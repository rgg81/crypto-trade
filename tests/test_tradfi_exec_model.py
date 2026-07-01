"""Tests for the TradFi paper engine's LIVE-track EXECUTION MODEL (lot quantization + funding).

The conceptual split under test:
  * PARITY = THE SIGNAL — the CONTINUOUS ideal book (``tradfi_held_w`` + the parity equity track).
    It must match the backtest bit-for-bit; quantization is an EXECUTION effect and must NEVER touch
    it (or the monitor's PARITY check would false-drift).
  * LIVE = THE REAL TRADE — the deployed weights QUANTIZED to the official Binance perp filters
    (lot-step rounding + sub-min-notional drops) at each day's perp price, funding booked on the
    quantized legs, and turnover charged at ``ct.COST_SIDE`` (the SAME taker+slippage the backtest
    owns — slippage is NOT double-counted; optional ``live_extra_slippage_side`` stress knob = 0).

Pure-unit: synthetic perp/funding frames in tmp dirs + monkeypatch; NO network, NO on-disk data, and
NO touching of the live ``data/tradfi_paper.db`` / ``data/tradfi_equity.csv``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_TF = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
_SRC = Path(__file__).resolve().parents[1] / "src"
for _p in (str(_TF), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import core_tradfi as ct  # noqa: E402
import live_tradfi as lt  # noqa: E402
import sizing_min_notional as sizing  # noqa: E402

DAY_MS = 86_400_000
# SECTOR_MAP keys that resolve to themselves in the static perp snapshot (key == perp symbol).
A = "AAPLUSDT"  # normal-sized leg
TINY = "GMEUSDT"  # used as a sub-min-notional leg


# ------------------------------------------------------------------ fixtures / helpers -----------
@pytest.fixture(autouse=True)
def _no_network_filters(monkeypatch):
    """Default: stub the live exchangeInfo fetch to an EMPTY dict so engine init is network-free and
    every filter lookup resolves to the verified-uniform ``_DEFAULT_FILT``. Individual tests may
    override this (e.g. to raise, exercising the fetch-failure fallback path)."""
    monkeypatch.setattr("sizing_min_notional._filters", lambda: {})


def _days(n: int) -> pd.DatetimeIndex:
    return pd.to_datetime([i * DAY_MS for i in range(n)], unit="ms")


def _write_perp(live_dir: Path, sym: str, idx: pd.DatetimeIndex, opens: list[float]) -> None:
    d = live_dir / sym
    d.mkdir(parents=True, exist_ok=True)
    ot = (idx.astype("datetime64[ms]").astype("int64")).to_numpy()
    pd.DataFrame(
        {
            "open_time": ot,
            "open": opens,
            "high": opens,
            "low": opens,
            "close": opens,
            "volume": [0.0] * len(opens),
        }
    ).to_csv(d / "1d.csv", index=False)


def _write_funding(fund_dir: Path, sym: str, idx: pd.DatetimeIndex, rates: list[float]) -> None:
    fr = fund_dir / "funding_rates"
    fr.mkdir(parents=True, exist_ok=True)
    ft = (idx.astype("datetime64[ms]").astype("int64")).to_numpy()
    pd.DataFrame({"funding_time": ft, "funding_rate": rates}).to_csv(fr / f"{sym}.csv", index=False)


def _engine(tmp_path: Path, **cfg_kw) -> lt.TradfiPaperEngine:
    cfg = lt.TradfiPaperConfig(
        db_path=str(tmp_path / "paper.db"),
        live_data_dir=str(tmp_path / "live"),
        funding_dir=str(tmp_path / "fund"),
        data_dir=str(tmp_path / "data"),
        equity_csv=str(tmp_path / "eq.csv"),
        **cfg_kw,
    )
    return lt.TradfiPaperEngine(cfg)


# ============================================================ 1. LIVE quantized, PARITY/held not ==
def test_live_track_is_quantized_but_parity_style_track_is_not(tmp_path):
    """The quantized LIVE track differs from the continuous ``_live_returns`` whenever the lot/min-
    notional rounding bites — proving quantization is applied to LIVE. Prices 100,101,102,… make the
    0.5 weight round to 0.49995 on the off-$100 bars, so the two live tracks must diverge."""
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    idx = _days(5)
    _write_perp(live_dir, A, idx, [100.0, 101.0, 102.0, 103.0, 104.0])
    _write_funding(fund_dir, A, idx, [0.0] * 5)

    dw = pd.DataFrame({A: [0.5] * 5}, index=idx)  # CONTINUOUS ideal weight (the signal)
    live_q, _ = eng._live_returns_quantized(dw)  # quantized (real) live track
    live_c, _ = eng._live_returns(dw)  # continuous live track (no quantization)

    # Off-$100 bars round 0.5 → 0.49995, so the quantized track must diverge from the continuous.
    assert not np.allclose(live_q.iloc[:-1].to_numpy(), live_c.iloc[:-1].to_numpy())
    # And the quantized weight itself is NOT the ideal 0.5 on those bars (it IS on the $100 bar).
    q_w = eng._quantize_book(dw, pd.DataFrame({A: [100.0, 101.0, 102.0, 103.0, 104.0]}, index=idx))
    assert q_w[A].iloc[0] == pytest.approx(0.5)  # 0.5*10000/100 = 50.00 lots, clean → exactly 0.5
    assert q_w[A].iloc[1] != pytest.approx(
        0.5
    )  # 101 → 49.5 lots → 0.49995, quantized away from 0.5


def test_held_book_and_parity_stay_continuous_through_run_once(tmp_path, monkeypatch):
    """After ``run_once``, ``tradfi_held_w`` is the CONTINUOUS ideal book (both legs, exact weights)
    and the parity equity is the continuous net compounding — neither is quantized. eq_live diverges
    from eq_parity (real vs signal)."""
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    idx = _days(5)
    _write_perp(live_dir, A, idx, [100.0, 101.0, 102.0, 103.0, 104.0])
    _write_perp(live_dir, TINY, idx, [50.0] * 5)
    _write_funding(fund_dir, A, idx, [0.0] * 5)
    _write_funding(fund_dir, TINY, idx, [0.0] * 5)

    deployed_w = pd.DataFrame({A: [0.5] * 5, TINY: [0.0003] * 5}, index=idx)
    net = pd.Series([0.001] * 5, index=idx)  # parity net (Yahoo backtest), unaffected by quant
    as_of = idx[-1]

    # back-date launch so parity compounds over idx[0..as_of); else run_once starts flat at launch
    eng.store.set_state("tradfi_launch_candle", str(int(idx[0].value // 1_000_000)))
    monkeypatch.setattr(eng, "_settled_book", lambda: (net, deployed_w, as_of))
    monkeypatch.setattr(
        lt.lw,
        "deployed_target_weights",
        lambda a, data_dir: {A: 0.5, TINY: 0.0003, "_meta": {"gross": 0.5003, "as_of": as_of}},
    )

    res = eng.run_once(refresh=False)

    held = json.loads(eng.store.get_state("tradfi_held_w"))
    assert set(held) == {
        A,
        TINY,
    }  # continuous ideal book — TINY present, NOT dropped, NOT quantized
    assert held[A] == pytest.approx(0.5)
    assert held[TINY] == pytest.approx(0.0003)
    # parity = pure continuous net compounding over the realized (launch..as_of) bars → quant-free
    expected_parity = 10_000.0 * float(
        (1.0 + net[(net.index >= idx[0]) & (net.index < as_of)]).prod()
    )
    assert res["equity_parity"] == pytest.approx(expected_parity)
    # real vs signal: eq_live (quantized perp book) diverges from eq_parity (ideal signal)
    assert res["equity_live"] != pytest.approx(res["equity_parity"])


# ==================================== 2. sub-min-notional leg dropped from LIVE only ==
def test_sub_min_notional_leg_dropped_from_live_but_present_in_held(tmp_path, monkeypatch):
    """A leg whose notional at $10k is < the $5 min-notional floor quantizes to 0 in the LIVE book
    (not placed), yet stays in ``tradfi_held_w`` at its exact ideal weight — so the PARITY check
    (which compares held vs the recomputed ideal target) does NOT drift on it."""
    eng = _engine(tmp_path)
    idx = _days(5)

    # TINY: |w|=0.0003 → $3 notional at $10k, below the $5 min-notional → dropped from live book.
    w = pd.DataFrame({TINY: [0.0003] * 5}, index=idx)
    opens = pd.DataFrame({TINY: [50.0] * 5}, index=idx)
    q_w = eng._quantize_book(w, opens)
    assert (q_w[TINY] == 0.0).all()  # DROPPED from the executed live book
    # sanity: the scalar rule agrees it is untradeable at $10k
    _rw, ok = sizing.quantize_weight(0.0003, 50.0, lt._DEFAULT_FILT, 10_000.0)
    assert ok is False

    # but the ideal held book (what PARITY compares to) still carries it
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    _write_perp(live_dir, TINY, idx, [50.0] * 5)
    _write_funding(fund_dir, TINY, idx, [0.0] * 5)
    net = pd.Series([0.0] * 5, index=idx)
    as_of = idx[-1]
    eng.store.set_state("tradfi_launch_candle", str(int(idx[0].value // 1_000_000)))
    monkeypatch.setattr(eng, "_settled_book", lambda: (net, w, as_of))
    monkeypatch.setattr(
        lt.lw,
        "deployed_target_weights",
        lambda a, data_dir: {TINY: 0.0003, "_meta": {"gross": 0.0003, "as_of": as_of}},
    )
    eng.run_once(refresh=False)
    held = json.loads(eng.store.get_state("tradfi_held_w"))
    assert TINY in held and held[TINY] == pytest.approx(0.0003)  # present in the SIGNAL book


# ==================================== 3. cost on QUANTIZED turnover at COST_SIDE ===
def test_cost_charged_on_quantized_turnover_default_is_cost_side(tmp_path):
    """Turnover cost is charged on the QUANTIZED weight changes at ``ct.COST_SIDE`` by default — the
    SAME taker+slippage the backtest/parity own, so slippage is NOT double-counted. The optional
    ``live_extra_slippage_side`` knob adds stress cost ABOVE that."""
    idx = _days(5)
    # flat perp @ $100 (zero perp return, clean lots) + zero funding ⇒ live_ret == −turnover cost.
    dw = pd.DataFrame({A: [0.3, 0.6, 0.6, 0.6, 0.6]}, index=idx)  # Δ|q_w| = 0.3 at bar 1

    eng = _engine(tmp_path)  # default live_extra_slippage_side = 0.0
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    _write_perp(live_dir, A, idx, [100.0] * 5)
    _write_funding(fund_dir, A, idx, [0.0] * 5)
    live_ret, _ = eng._live_returns_quantized(dw)
    # q_w: 0.3→0.6 (both clean at $100) → |Δ| = 0.3 ; cost = COST_SIDE * 0.3
    assert live_ret.iloc[1] == pytest.approx(-ct.COST_SIDE * 0.3)
    assert ct.COST_SIDE == pytest.approx(0.0006)  # documents: parity uses this same taker+slippage

    # stress knob: extra slippage ABOVE the backtest assumption stacks on COST_SIDE
    eng2 = _engine(tmp_path / "x", live_extra_slippage_side=0.0005)
    ld2, fd2 = Path(eng2.cfg.live_data_dir), Path(eng2.cfg.funding_dir)
    _write_perp(ld2, A, idx, [100.0] * 5)
    _write_funding(fd2, A, idx, [0.0] * 5)
    live_ret2, _ = eng2._live_returns_quantized(dw)
    assert live_ret2.iloc[1] == pytest.approx(-(ct.COST_SIDE + 0.0005) * 0.3)
    assert live_ret2.iloc[1] < live_ret.iloc[1]  # extra slippage is strictly more drag


# ==================================== 4. funding booked on QUANTIZED legs ==
def test_funding_booked_on_quantized_legs_correct_sign(tmp_path):
    """Funding P&L is computed on the QUANTIZED weight (what you actually hold), not the continuous
    ideal — and keeps the −w·f sign (long pays when f>0, short earns)."""
    idx = _days(4)
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    # flat perp @ $101 (perp return 0) so live_ret is funding-only; price 101 makes 0.5 quantize.
    _write_perp(live_dir, A, idx, [101.0] * 4)
    _write_funding(fund_dir, A, idx, [0.001] * 4)  # f>0

    q_expected, ok = sizing.quantize_weight(0.5, 101.0, lt._DEFAULT_FILT, 10_000.0)
    assert ok and q_expected != pytest.approx(0.5)  # 0.5 → 0.49995 (the quantization bites)

    # LONG leg: funding NEGATIVE, on the QUANTIZED weight (−q_w·f), NOT the continuous 0.5.
    dw_long = pd.DataFrame({A: [0.5] * 4}, index=idx)
    _, fund_long = eng._live_returns_quantized(dw_long)
    assert fund_long.iloc[1] == pytest.approx(-q_expected * 0.001)
    assert fund_long.iloc[1] != pytest.approx(
        -0.5 * 0.001
    )  # would be wrong if booked on continuous

    # SHORT leg: funding POSITIVE, on the quantized (−0.49995) weight.
    dw_short = pd.DataFrame({A: [-0.5] * 4}, index=idx)
    _, fund_short = eng._live_returns_quantized(dw_short)
    assert fund_short.iloc[1] == pytest.approx(q_expected * 0.001)


# ==================================== 5. filter-fetch failure → uniform default, no raise
def test_filter_fetch_failure_falls_back_to_uniform_default(tmp_path, monkeypatch):
    """A live exchangeInfo outage at engine init must NOT raise — the filter cache falls back to {}
    and every lookup resolves to the verified-uniform ``_DEFAULT_FILT``, so quantization keeps
    running."""

    def _boom():
        raise RuntimeError("exchangeInfo unreachable")

    monkeypatch.setattr("sizing_min_notional._filters", _boom)
    eng = _engine(tmp_path)  # must construct cleanly despite the fetch failure
    assert eng._perp_filters == {}

    idx = _days(4)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    _write_perp(live_dir, A, idx, [100.0] * 4)
    _write_funding(fund_dir, A, idx, [0.0] * 4)
    dw = pd.DataFrame({A: [0.5] * 4}, index=idx)
    q_w = eng._quantize_book(dw, pd.DataFrame({A: [100.0] * 4}, index=idx))
    assert q_w[A].iloc[0] == pytest.approx(0.5)  # uniform-default filter still quantizes cleanly
    live_ret, _ = eng._live_returns_quantized(dw)
    assert not live_ret.isna().any()  # runs without raising
