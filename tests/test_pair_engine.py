"""Tests for the realistic market-neutral pair engine (analysis/pair_engine.py).

Foundation verification (user: "solid foundation without errors", "reproduce real scenarios"):
  - NO-LOOKAHEAD: the weight at t depends ONLY on data <= close[t]; corrupting future rows must not
    change any past weight.
  - FLAT MARKET: constant prices + zero funding => net P&L is EXACTLY the negative turnover cost.
  - PURE FUNDING: constant prices + constant funding diff => funding income == analytic value,
    price P&L == zero.
  - COST CONVENTION: per-side cost matches the live engine (fee 0.1% round-trip + 2bps/side slip).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
import pair_engine as pe  # noqa: E402


def _synth(n=400, seed=0, open_a=None, open_b=None, fa=0.0, fb=0.0):
    rng = np.random.default_rng(seed)
    ot = np.arange(n, dtype=np.int64) * (8 * 60 * 60 * 1000) + 1_600_000_000_000
    ca = 100 * np.cumprod(1 + rng.normal(0, 0.02, n)) if open_a is None else np.full(n, open_a)
    cb = 100 * np.cumprod(1 + rng.normal(0, 0.02, n)) if open_b is None else np.full(n, open_b)
    df = pd.DataFrame(
        {
            "open_a": ca, "close_a": ca, "funding_rate_a": np.full(n, fa), "quote_volume_a": 1e9,
            "open_b": cb, "close_b": cb, "funding_rate_b": np.full(n, fb), "quote_volume_b": 1e9,
        },
        index=ot,
    )
    return df


def test_no_lookahead():
    """Corrupting every row at/after k must not change any weight before k."""
    df = _synth(n=400, seed=1)
    w_clean = pe.signal_weights(df, "rev+carry")
    k = 250
    corrupt = df.copy()
    corrupt.iloc[k:, :] = 1e9  # garbage in the entire future (all columns, incl. funding)
    w_corrupt = pe.signal_weights(corrupt, "rev+carry")
    assert np.array_equal(w_clean[:k], w_corrupt[:k]), "look-ahead: a past weight changed"


def test_no_lookahead_all_configs():
    df = _synth(n=350, seed=2)
    k = 200
    corrupt = df.copy()
    corrupt.iloc[k:, :] = np.nan
    for cfg in pe.CONFIGS:
        wc = pe.signal_weights(df, cfg)
        wk = pe.signal_weights(corrupt, cfg)
        assert np.array_equal(wc[:k], wk[:k]), f"look-ahead in config {cfg}"


def test_flat_market_net_is_negative_cost():
    """Constant prices + zero funding => net == -turnover cost exactly; price and funding == 0."""
    df = _synth(n=200, open_a=100.0, open_b=100.0, fa=0.0, fb=0.0)
    w = np.tile([1.0, -1.0], len(df) // 2)  # flip every candle => steady turnover
    bt = pe.run(df, w)
    assert np.allclose(bt["price"], 0.0, atol=1e-12), "price P&L must be 0 in a flat market"
    assert np.allclose(bt["funding"], 0.0, atol=1e-12), "funding must be 0 with zero funding rates"
    # net must equal -cost, and cost = 2 * cost_side * |Δw_a|
    assert np.allclose(bt["net"], -bt["cost"], atol=1e-12), "flat-market net must equal -cost"
    assert (bt["net"] <= 1e-12).all(), "flat-market net cannot be positive"


def test_pure_funding_income_matches_analytic():
    """Constant prices + constant funding diff + steady short on the high-funding leg => funding
    income == (fa - fb) per candle; price == 0."""
    fa, fb = 0.01, 0.0
    df = _synth(n=200, open_a=100.0, open_b=100.0, fa=fa, fb=fb)
    w = np.full(len(df), -1.0)  # short A (high funding) / long B, never flips after entry
    bt = pe.run(df, w)
    assert np.allclose(bt["price"], 0.0, atol=1e-12), "price must be 0 with constant prices"
    # funding = -(wa*fa - wa*fb) = -(-1)*(fa - fb) = +(fa - fb)
    assert np.allclose(bt["funding"], fa - fb, atol=1e-12), "funding income != analytic (fa - fb)"
    # only the first candle has turnover (entry); the rest have zero cost
    assert np.allclose(bt["cost"].iloc[1:], 0.0, atol=1e-12), "no turnover cost once steady"


def test_cost_side_matches_live_engine_convention():
    """0.07%/side = fee 0.1% round-trip + 2bps/side slippage (the deployed-strategy convention)."""
    expected = pe.FEE_PCT / 100 / 2 + pe.SLIP_BPS / 1e4
    assert abs(pe.COST_SIDE - expected) < 1e-12
    assert abs(pe.COST_SIDE - 0.0007) < 1e-9, "per-side cost must be 0.07%"


def test_run_indexing_drops_unfillable_tail():
    """The hold needs open[t+2], so the backtest length is n-2 (no fabricated last fills)."""
    df = _synth(n=123, seed=3)
    bt = pe.run(df, pe.signal_weights(df, "carry"))
    assert len(bt) == len(df) - 2
