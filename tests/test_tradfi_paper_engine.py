"""Tests for the TradFi PAPER-TRADING engine (analysis/portfolio/tradfi/live_tradfi.py).

Pure-unit: tiny synthetic perp/funding frames written to tmp dirs — no network, no on-disk data.
Guards the four load-bearing behaviors of the dual-P&L engine:
  1. PAYP is dropped from the held book and NOT re-normalized (surviving weights unchanged).
  2. Funding P&L sign: a long leg with positive funding => NEGATIVE P&L; a short leg => POSITIVE.
  3. Coverage-aware: a name with no perp/funding contributes 0 to live_ret (no NaN poison).
  4. Live weight-lag alignment == parity net alignment (deployed_w[t] pairs with forward-return[t],
     no extra shift).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_TF = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
_SRC = Path(__file__).resolve().parents[1] / "src"
for _p in (str(_TF), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import live_tradfi as lt  # noqa: E402

DAY_MS = 86_400_000
# Two SECTOR_MAP keys that resolve to themselves in the static perp snapshot (key == perp symbol).
A, B = "AAPLUSDT", "MSFTUSDT"


# ------------------------------------------------------------------ synthetic-data helpers -------
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


def _engine(tmp_path: Path) -> lt.TradfiPaperEngine:
    cfg = lt.TradfiPaperConfig(
        db_path=str(tmp_path / "paper.db"),
        live_data_dir=str(tmp_path / "live"),
        funding_dir=str(tmp_path / "fund"),
        data_dir=str(tmp_path / "data"),
        equity_csv=str(tmp_path / "eq.csv"),
    )
    return lt.TradfiPaperEngine(cfg)


# ------------------------------------------------------------------ 1. PAYP exclusion ------------
def test_payp_dropped_not_renormalized():
    raw = {A: 0.5, B: -0.3, "PAYPUSDT": 0.11}
    held = lt.TradfiPaperEngine._drop_excluded(raw)
    assert "PAYPUSDT" not in held
    # every surviving leg keeps its EXACT weight — no re-normalization
    assert held == {A: 0.5, B: -0.3}
    assert sum(abs(v) for v in held.values()) == 0.8  # 0.8, NOT re-scaled back to (0.8+0.11)


# ------------------------------------------------------------------ 2. funding sign --------------
def test_funding_sign_long_pays_short_earns(tmp_path):
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    idx = _days(4)
    _write_perp(live_dir, A, idx, [100.0, 100.0, 100.0, 100.0])  # flat perp -> perp_ret 0
    _write_funding(fund_dir, A, idx, [0.001, 0.001, 0.001, 0.001])  # f>0

    # LONG leg: funding P&L must be NEGATIVE (long pays when f>0)
    dw_long = pd.DataFrame({A: [0.5, 0.5, 0.5, 0.5]}, index=idx)
    _, fund_long = eng._live_returns(dw_long)
    assert fund_long.iloc[1] < 0
    assert np.isclose(fund_long.iloc[1], -0.5 * 0.001)

    # SHORT leg: funding P&L must be POSITIVE (short earns when f>0)
    dw_short = pd.DataFrame({A: [-0.5, -0.5, -0.5, -0.5]}, index=idx)
    _, fund_short = eng._live_returns(dw_short)
    assert fund_short.iloc[1] > 0
    assert np.isclose(fund_short.iloc[1], 0.5 * 0.001)


# ------------------------------------------------------------------ 3. coverage-aware ------------
def test_coverage_missing_name_contributes_zero_no_nan(tmp_path):
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    idx = _days(4)
    # Only A has a perp + funding; B has NEITHER (not yet onboarded) -> B contributes 0, no NaN.
    _write_perp(live_dir, A, idx, [100.0, 101.0, 102.0, 103.0])
    _write_funding(fund_dir, A, idx, [0.0, 0.0, 0.0, 0.0])
    dw = pd.DataFrame({A: [0.5, 0.5, 0.5, 0.5], B: [0.5, 0.5, 0.5, 0.5]}, index=idx)

    live_ret, _ = eng._live_returns(dw)
    assert not live_ret.isna().any()  # B's absence must NOT NaN-poison the sum
    # On REALIZED bars (all but the last, whose fwd return is NaN) live_ret == A-only contribution:
    # 0.5 * perp_ret_a (funding 0, cost 0 for constant weights). The last bar carries the frontier
    # unwind cost (A coverage-masked once its fwd return is NaN); run_once drops it (index < as_of).
    perp_ret_a = pd.Series([101 / 100 - 1, 102 / 101 - 1, 103 / 102 - 1], index=idx[:-1])
    assert np.allclose(live_ret.iloc[:-1].to_numpy(), (0.5 * perp_ret_a).to_numpy())


# ------------------------------------------------------------------ 4. lag alignment -------------
def test_live_lag_matches_parity_shift(tmp_path):
    """live_ret (funding=0, cost=0) == Σ deployed_w[t]·perp_rf[t] — deployed_w is already .shift(1)-
    lagged (banded_book_freq), so pairing it with the forward return on the SAME index t is exactly
    the parity net alignment. Any spurious extra shift in the live track breaks this equality."""
    eng = _engine(tmp_path)
    live_dir, fund_dir = Path(eng.cfg.live_data_dir), Path(eng.cfg.funding_dir)
    idx = _days(5)
    opens_a = [100.0, 110.0, 121.0, 133.1, 146.41]  # +10%/day
    opens_b = [50.0, 49.0, 48.02, 47.06, 46.12]  # ~-2%/day
    _write_perp(live_dir, A, idx, opens_a)
    _write_perp(live_dir, B, idx, opens_b)
    _write_funding(fund_dir, A, idx, [0.0] * 5)
    _write_funding(fund_dir, B, idx, [0.0] * 5)

    # CONSTANT weights -> zero turnover cost -> live_ret is pure Σ w·perp_rf
    dw = pd.DataFrame({A: [0.6] * 5, B: [-0.4] * 5}, index=idx)
    live_ret, _ = eng._live_returns(dw)

    # parity-style pnl using the SAME forward-return convention, weights paired on the same index t
    perp_rf = pd.DataFrame(
        {
            A: pd.Series(opens_a, index=idx).shift(-1) / pd.Series(opens_a, index=idx) - 1,
            B: pd.Series(opens_b, index=idx).shift(-1) / pd.Series(opens_b, index=idx) - 1,
        }
    )
    parity_pnl = (dw * perp_rf.fillna(0.0)).sum(axis=1)
    # Compare REALIZED bars (all but the last, whose fwd return is NaN → coverage-masked frontier).
    # Equality here proves the live track pairs deployed_w[t] with forward-return[t] on the SAME
    # index t — bit-identical to the parity net's shift; any spurious extra .shift() would break it.
    assert np.allclose(live_ret.iloc[:-1].to_numpy(), parity_pnl.iloc[:-1].to_numpy())
    # sanity: the forward return realizes on bar t (open[t+1]/open[t]), so bar 0 is non-zero
    assert abs(live_ret.iloc[0]) > 0
