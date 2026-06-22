"""Fast synthetic-panel unit tests for the v2 portfolio engine (TDD — written first).

These tests NEVER load real data and NEVER run the full walk-forward backtest. They build small
synthetic pandas panels and exercise the leak-safe primitives directly:

  - universe_v2.eligibility(...)      — rank band + PIT seasoning, past-only.
  - engine_v2.build_panel(...)        — opens/close/qv/fund DataFrames from a coins dict.
  - engine_v2.fixed_lambda_book(...)  — the per-coin lagged weight book + net for one λ (the
                                        deterministic building block of run_book; small-panel safe).

The slow full-universe parity gate lives in analysis/portfolio_v2/parity_check.py (run separately).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "analysis"))

from portfolio_v2 import engine_v2, universe_v2  # noqa: E402

STEP_MS = 8 * 60 * 60 * 1000  # one 8h candle


def _ms_index(n: int, start: int = 1_577_836_800_000) -> list[int]:
    """n consecutive 8h open_time stamps in ms (Jan 2020 onward, like the real data)."""
    return [start + i * STEP_MS for i in range(n)]


def _coin(idx_ms, *, opens, closes=None, qv, fund=None) -> pd.DataFrame:
    """Build a single synthetic coin frame indexed by ms open_time (v1 on-disk layout).

    `opens`/`closes`/`qv` may be scalars (broadcast) or arrays. NaN entries model a coin that is
    not yet listed (leading NaN) or delisted (trailing NaN).
    """
    n = len(idx_ms)

    def _col(v):
        if np.isscalar(v):
            return np.full(n, float(v))
        return np.asarray(v, dtype=float)

    closes = opens if closes is None else closes
    df = pd.DataFrame(
        {
            "open": _col(opens),
            "close": _col(closes),
            "quote_volume": _col(qv),
        },
        index=pd.Index(idx_ms, name="open_time"),
    )
    if fund is not None:
        df["funding"] = _col(fund)
    return df


# ---------------------------------------------------------------------------------------------
# 1. rank band selects rank 21–40 vs top-20
# ---------------------------------------------------------------------------------------------
def test_rank_band_selects_2140():
    """50 coins with constant, distinct liquidity ranks: (20,40] selects exactly ranks 21–40 and
    (0,20] selects exactly the top-20."""
    n = 120
    idx = _ms_index(n)
    # coin k has liquidity proportional to (50 - k): coin0 highest (rank 1) ... coin49 lowest.
    coins = {
        f"C{k:02d}USDT": _coin(idx, opens=100.0, qv=float(50 - k) * 1_000_000.0) for k in range(50)
    }
    elig_top20 = universe_v2.eligibility(coins, rank_lo=0, rank_hi=20, season=None, liq_win=3)
    elig_2140 = universe_v2.eligibility(coins, rank_lo=20, rank_hi=40, season=None, liq_win=3)

    # use a late candle where the trailing-mean liquidity rank is well-defined
    t = idx[-1]
    row20 = elig_top20.loc[pd.to_datetime(t, unit="ms")]
    row2140 = elig_2140.loc[pd.to_datetime(t, unit="ms")]

    top20_syms = {f"C{k:02d}USDT" for k in range(20)}  # ranks 1..20
    band_syms = {f"C{k:02d}USDT" for k in range(20, 40)}  # ranks 21..40

    assert set(row20[row20].index) == top20_syms
    assert set(row2140[row2140].index) == band_syms
    assert int(row20.sum()) == 20
    assert int(row2140.sum()) == 20
    # disjoint bands
    assert not (set(row20[row20].index) & set(row2140[row2140].index))


# ---------------------------------------------------------------------------------------------
# 2. seasoning gates a young coin out of BOTH the traded set and the rank denominator
# ---------------------------------------------------------------------------------------------
def test_seasoning_gates_young_coin():
    """A coin with < season trailing closes is ineligible AND excluded from the rank denominator,
    so the marginal in-band coin keeps its slot until the young coin seasons and displaces it."""
    season = 5
    n = 30
    idx = _ms_index(n)
    # 3 always-on coins. Ranked AAA(1) > BBB(2) > CCC(3) -> top-3 = {AAA,BBB,CCC} while YNG gated.
    coins = {
        "AAAUSDT": _coin(idx, opens=100.0, qv=9_000_000.0),
        "BBBUSDT": _coin(idx, opens=100.0, qv=8_000_000.0),
        "CCCUSDT": _coin(idx, opens=100.0, qv=7_000_000.0),
    }
    # YOUNG coin: HIGHEST liquidity but only listed from candle `start_at` (leading NaN closes).
    # Once seasoned it becomes rank-1 and pushes CCC (the marginal in-band coin) out of the top-3.
    start_at = 10
    young_close = np.full(n, np.nan)
    young_close[start_at:] = 100.0
    young_open = young_close.copy()
    young_qv = np.where(np.isnan(young_close), np.nan, 99_000_000.0)
    coins["YNGUSDT"] = _coin(idx, opens=young_open, closes=young_close, qv=young_qv)

    elig = universe_v2.eligibility(coins, rank_lo=0, rank_hi=3, season=season, liq_win=3)
    dt = pd.to_datetime(idx, unit="ms")

    # Pre-seasoning: young has < season trailing non-NaN closes -> ineligible AND absent from the
    # rank denominator, so CCC (the marginal coin) still holds the 3rd slot.
    t_pre = dt[start_at + 2]  # only 2 trailing closes (shifted) -> not seasoned at season=5
    assert not bool(elig.loc[t_pre, "YNGUSDT"])
    assert bool(elig.loc[t_pre, "CCCUSDT"])  # young excluded from denominator -> CCC keeps top-3

    # Post-seasoning: young has >= season trailing closes -> eligible; being the most liquid it
    # enters the top-3 and displaces CCC.
    t_post = dt[start_at + season + 2]
    assert bool(elig.loc[t_post, "YNGUSDT"])
    assert not bool(elig.loc[t_post, "CCCUSDT"])


# ---------------------------------------------------------------------------------------------
# 3. PIT pool keeps a delisted coin through its last candle, then closes the position
# ---------------------------------------------------------------------------------------------
def test_pit_pool_keeps_delisted_through_last_candle():
    """A coin that ends mid-sample is eligible (seasoned + ranked) during its life and
    ineligible after its last candle; no forward fill resurrects it."""
    season = 3
    n = 30
    idx = _ms_index(n)
    last_at = 18  # coin trades through candle 18, then delists (trailing NaN)
    dl_close = np.full(n, 100.0)
    dl_close[last_at + 1 :] = np.nan
    dl_open = dl_close.copy()
    dl_qv = np.where(np.isnan(dl_close), np.nan, 9_000_000.0)
    coins = {
        "AAAUSDT": _coin(idx, opens=100.0, qv=8_000_000.0),
        "BBBUSDT": _coin(idx, opens=100.0, qv=7_000_000.0),
        "DELUSDT": _coin(idx, opens=dl_open, closes=dl_close, qv=dl_qv),
    }
    elig = universe_v2.eligibility(coins, rank_lo=0, rank_hi=3, season=season, liq_win=3)
    dt = pd.to_datetime(idx, unit="ms")

    # Alive + seasoned mid-life -> eligible.
    assert bool(elig.loc[dt[last_at], "DELUSDT"])
    # Well after the last candle -> NaN close -> not seasoned -> ineligible (no forward fill).
    assert not bool(elig.loc[dt[last_at + 5], "DELUSDT"])

    # And the PIT pool loader keeps the delisted coin's full on-disk history (its terminal candle is
    # present, not dropped by any lifetime filter). Verified on the eligibility frame's columns.
    assert "DELUSDT" in elig.columns


# ---------------------------------------------------------------------------------------------
# 4. slippage zero reduces to taker cost bit-for-bit
# ---------------------------------------------------------------------------------------------
def test_slippage_zero_reduces_to_taker():
    """With slip=0 the engine cost per candle equals COST_SIDE · Σ|Δw| exactly (v1 cost)."""
    rng = np.random.default_rng(0)
    n = 40
    idx = _ms_index(n)
    coins = {}
    for k in range(6):
        px = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.02, n))
        coins[f"C{k}USDT"] = _coin(
            idx, opens=px, closes=px, qv=float(6 - k) * 1_000_000.0, fund=0.0
        )

    book_zero = engine_v2.fixed_lambda_book(
        coins,
        lam=0.0,
        rank_lo=0,
        rank_hi=4,
        season=None,
        slip_bps_fn=engine_v2.zero_slip,
        liq_win=3,
    )
    w = book_zero["w"]
    expected_cost = engine_v2.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    got_cost = book_zero["cost"]
    aligned_e, aligned_g = expected_cost.align(got_cost, join="inner")
    assert float((aligned_e - aligned_g).abs().max()) < 1e-15


# ---------------------------------------------------------------------------------------------
# 5. slippage is monotone in turnover and thin coins pay strictly more per unit; capped
# ---------------------------------------------------------------------------------------------
def test_slippage_monotone_and_thin_pays_more():
    """Per-unit slip bps strictly decreases with dollar-volume (thin pays more), is floored and
    capped, and total slip cost rises with turnover."""
    f = engine_v2.default_slip_bps
    thin = f(5.0)  # $5M daily $-vol
    mid = f(40.0)  # $40M
    thick = f(200.0)  # $200M
    assert thin > mid > thick  # thinner coin -> strictly higher per-unit bps
    # floor / cap
    assert f(1e9) == pytest.approx(engine_v2.SLIP_FLOOR)  # ultra-deep clamps to floor
    assert f(1e-9) == pytest.approx(engine_v2.SLIP_CAP)  # ultra-thin clamps to cap
    # sanity on the brief's anchor points
    assert thick == pytest.approx(1.1, abs=0.05)
    assert mid == pytest.approx(1.5, abs=0.05)
    assert f(5.0) == pytest.approx(5.0, abs=0.05)

    # total slip cost rises with turnover: scale Σ|Δw| by 2x -> slip cost doubles for a fixed coin.
    dvol_m = pd.Series([40.0, 40.0])
    dwt = pd.Series([0.10, 0.20])
    slip_side = engine_v2.default_slip_bps(dvol_m) / 1e4
    cost_small = float((dwt.iloc[:1] * slip_side.iloc[:1]).sum())
    cost_big = float((dwt.iloc[1:] * slip_side.iloc[1:]).sum())
    assert cost_big == pytest.approx(2.0 * cost_small, rel=1e-9)


# ---------------------------------------------------------------------------------------------
# 6. leak safety — perturbing future inputs does not change past target_w or net
# ---------------------------------------------------------------------------------------------
def test_leak_safety_future_perturbation():
    """Corrupt ALL inputs (open/close/qv/funding) at candles >= cutoff; target_w AND net BEFORE the
    cutoff are bit-identical (mirrors iter_021's corruption gate)."""
    n = 60
    idx = _ms_index(n)

    def _make(seed_shift: float, cutoff: int | None):
        coins = {}
        for k in range(6):
            base_px = 100.0 * np.cumprod(1.0 + rng_for(k).normal(0, 0.02, n))
            opens = base_px.copy()
            closes = base_px.copy()
            qv = np.full(n, float(6 - k) * 1_000_000.0)
            fund = np.full(n, 0.0001)
            if cutoff is not None:
                # garbage everything from `cutoff` onward
                opens[cutoff:] = base_px[cutoff:] * (1.0 + seed_shift)
                closes[cutoff:] = base_px[cutoff:] * (1.0 - seed_shift)
                qv[cutoff:] = qv[cutoff:] * 1000.0
                fund[cutoff:] = -0.05
            coins[f"C{k}USDT"] = _coin(idx, opens=opens, closes=closes, qv=qv, fund=fund)
        return coins

    # deterministic per-coin RNG so clean and corrupted panels share identical pre-cutoff data
    _streams = {k: np.random.default_rng(100 + k) for k in range(6)}

    def rng_for(k):
        return _streams[k]

    cutoff_i = 45
    # reset streams, build clean
    _streams = {k: np.random.default_rng(100 + k) for k in range(6)}
    clean = engine_v2.fixed_lambda_book(
        _make(0.0, None), lam=0.0, rank_lo=0, rank_hi=4, season=None, liq_win=3
    )
    _streams = {k: np.random.default_rng(100 + k) for k in range(6)}
    dirty = engine_v2.fixed_lambda_book(
        _make(0.3, cutoff_i), lam=0.0, rank_lo=0, rank_hi=4, season=None, liq_win=3
    )

    cutoff_dt = pd.to_datetime(idx[cutoff_i], unit="ms")
    w_clean = clean["w"]
    w_dirty = dirty["w"].reindex(index=w_clean.index, columns=w_clean.columns)
    pre = w_clean.index < cutoff_dt
    dw = (w_clean[pre] - w_dirty[pre]).abs().to_numpy()
    assert np.nanmax(dw) == 0.0

    net_clean = clean["net"]
    net_dirty = dirty["net"].reindex(net_clean.index)
    pre_n = net_clean.index < cutoff_dt
    assert float((net_clean[pre_n] - net_dirty[pre_n]).abs().max()) == 0.0


# ---------------------------------------------------------------------------------------------
# 7. dollar neutrality on a sign-balanced synthetic trend
# ---------------------------------------------------------------------------------------------
def test_dollar_neutrality_balanced_signal():
    """With a sign-balanced set of trends (4 up MIRRORED by 4 down), per-candle gross long == gross
    short before vol-target. The down-coins are the exact return-mirror of the up-coins, so their
    realized vol (std of pct_change) is identical -> inverse-vol sizing is symmetric -> the book is
    dollar-neutral by construction."""
    rng = np.random.default_rng(11)
    n = 260
    idx = _ms_index(n)
    coins = {}
    # 4 independent up-trends; each has a positive drift + small symmetric noise.
    up_rets = [0.004 + rng.normal(0, 0.001, n) for _ in range(4)]
    for k, r in enumerate(up_rets):
        up_px = 100.0 * np.cumprod(1.0 + r)
        coins[f"U{k}USDT"] = _coin(idx, opens=up_px, closes=up_px, qv=1_000_000.0, fund=0.0)
        # the MIRROR coin: returns negated -> exact down-trend, identical |pct_change| series.
        dn_px = 100.0 * np.cumprod(1.0 - r)
        coins[f"D{k}USDT"] = _coin(idx, opens=dn_px, closes=dn_px, qv=1_000_000.0, fund=0.0)

    book = engine_v2.fixed_lambda_book(coins, lam=0.0, rank_lo=0, rank_hi=8, season=None)
    w = book["w"]
    # evaluate on a late candle where all horizons + rvol are warm and weights are non-zero
    late = w.iloc[-3]
    gross_long = late[late > 0].sum()
    gross_short = -late[late < 0].sum()
    assert gross_long > 0 and gross_short > 0
    assert gross_long == pytest.approx(gross_short, abs=1e-9)


# ---------------------------------------------------------------------------------------------
# 8. eligibility is strictly past-only (shift(1))
# ---------------------------------------------------------------------------------------------
def test_eligibility_is_past_only():
    """elig[t] depends only on data <= t-1; perturbing close/qv at exactly t does not change
    elig[t]."""
    season = 4
    n = 30
    idx = _ms_index(n)

    def _panel(spike_at: int | None):
        coins = {
            "AAAUSDT": _coin(idx, opens=100.0, qv=5_000_000.0),
            "BBBUSDT": _coin(idx, opens=100.0, qv=4_000_000.0),
            "CCCUSDT": _coin(idx, opens=100.0, qv=3_000_000.0),
            "DDDUSDT": _coin(idx, opens=100.0, qv=2_000_000.0),
        }
        if spike_at is not None:
            # blow up DDD's qv at exactly t -> would make it rank 1 IF the engine peeked at t.
            qv = np.full(n, 2_000_000.0)
            qv[spike_at] = 1_000_000_000.0
            coins["DDDUSDT"] = _coin(idx, opens=100.0, qv=qv)
        return coins

    t_i = 20
    elig_clean = universe_v2.eligibility(
        _panel(None), rank_lo=0, rank_hi=2, season=season, liq_win=3
    )
    elig_spike = universe_v2.eligibility(
        _panel(t_i), rank_lo=0, rank_hi=2, season=season, liq_win=3
    )
    dt = pd.to_datetime(idx, unit="ms")
    # elig at exactly t is unchanged by a same-candle qv spike (uses .shift(1))
    pd.testing.assert_series_equal(
        elig_clean.loc[dt[t_i]], elig_spike.loc[dt[t_i]], check_names=False
    )
    # but the NEXT candle DOES see the spike (sanity: the perturbation is real)
    assert bool(elig_spike.loc[dt[t_i + 1], "DDDUSDT"])


# ---------------------------------------------------------------------------------------------
# 9. leak safety at the run_book LEVEL — covers the walk-forward stitch + band/eligexit overlay
#    that test #6 (fixed_lambda_book) does NOT exercise. (Critic gap-fix.)
# ---------------------------------------------------------------------------------------------
def test_leak_safety_run_book_walkforward():
    """Corrupt ALL inputs from a cutoff forward and confirm the full run_book DECISIONS (target_w +
    held_w) before the cutoff are bit-identical, and the booked net is identical up to the candle
    whose forward-return legitimately reaches the cutoff. Panel spans > TRAIN_MONTHS so the
    walk-forward λ-stitch + band/eligexit overlay (untouched by test #6) are actually exercised."""
    # ~26 months of 8h candles so _canonical_book produces covered candles (needs 24m train + test).
    n = 2400
    idx = _ms_index(n)
    cutoff_i = 2360  # well inside the walk-forward-covered region, leaves a vol-warmed pre-window

    streams = {k: np.random.default_rng(200 + k) for k in range(6)}

    def _make(shift: float, cut: int | None):
        coins = {}
        for k in range(6):
            base_px = 100.0 * np.cumprod(1.0 + streams[k].normal(0, 0.02, n))
            opens, closes = base_px.copy(), base_px.copy()
            qv = np.full(n, float(6 - k) * 1_000_000.0)
            fund = np.full(n, 0.0001)
            if cut is not None:
                opens[cut:] = base_px[cut:] * (1.0 + shift)
                closes[cut:] = base_px[cut:] * (1.0 - shift)
                qv[cut:] *= 1000.0
                fund[cut:] = -0.05
            coins[f"C{k}USDT"] = _coin(idx, opens=opens, closes=closes, qv=qv, fund=fund)
        return coins

    streams = {k: np.random.default_rng(200 + k) for k in range(6)}
    clean = engine_v2.run_book(_make(0.0, None), rank_lo=0, rank_hi=4, season=None)
    streams = {k: np.random.default_rng(200 + k) for k in range(6)}
    dirty = engine_v2.run_book(_make(0.3, cutoff_i), rank_lo=0, rank_hi=4, season=None)

    cutoff_dt = pd.to_datetime(idx[cutoff_i], unit="ms")

    # there MUST be covered pre-cutoff candles, else the test is vacuous
    pre_cov = clean["target_w"].index[clean["target_w"].index < cutoff_dt]
    assert len(pre_cov) > 90, "walk-forward produced too few pre-cutoff candles"

    # DECISIONS (the leak surface): target_w + held_w bit-identical for every pre-cutoff candle.
    for key in ("target_w", "held_w"):
        a = clean[key].reindex(index=clean[key].index)
        b = dirty[key].reindex(index=a.index, columns=a.columns)
        pre = a.index < cutoff_dt
        diff = (a[pre] - b[pre]).abs().to_numpy()
        assert np.nanmax(diff) == 0.0, f"{key} leaked future info before cutoff"

    # BOOKED net: identical up to the candle whose ret_fwd reaches the cutoff (drop the 2 boundary
    # candles whose forward-return legitimately reads the corrupted open).
    nc, nd = clean["net"], dirty["net"].reindex(clean["net"].index)
    safe = nc.index < (cutoff_dt - pd.Timedelta(milliseconds=2 * STEP_MS))
    assert float((nc[safe] - nd[safe]).abs().max()) == 0.0
    assert bool((nc[safe].abs() > 0).any()), "net is trivially zero — vol-target not warmed"
