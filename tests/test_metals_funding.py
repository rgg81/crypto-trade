"""Tests for the metals paper-desk funding leg (analysis/portfolio/metals/metals_funding.py).

Guards the three properties that make funding a SAFE realism add-on:
  1. NO LOOK-AHEAD — corrupting funding rates from a cutoff forward leaves every earlier candle's
     funding PnL bit-identical (a candle only ever uses settlements floored into its own window).
  2. SIGN — a long charged when fundingRate>0 (pays); a short receives.
  3. BOUNDARY — candle t sums exactly the {t, t+4h} settlements; the t+8h settlement rolls to the
     NEXT candle (no double-count, no gap).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_METALS = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "metals"
if str(_METALS) not in sys.path:
    sys.path.insert(0, str(_METALS))

import metals_funding as mf  # noqa: E402

H4 = 4 * 60 * 60 * 1000
STEP = mf.STEP_MS  # 8h


def _deployed(weights):
    """4 candles on the 8h grid, one symbol 'A', given signed weights."""
    idx = [0, STEP, 2 * STEP, 3 * STEP]
    return pd.DataFrame({"A": weights}, index=idx)


def _funding(rates_by_time):
    return {"A": pd.Series(rates_by_time).sort_index()}


def test_sign_long_pays_short_receives():
    dep = _deployed([1.0, -1.0, 1.0, 1.0])
    fr = _funding({t: 0.001 for t in range(0, 8 * H4, H4)})  # every 4h, +0.001
    fn = mf.funding_net_8h(dep, fr)
    # candle 0: long, +funding -> pays -> negative; candle 1: short -> receives -> positive
    assert fn.loc[0] < 0 and abs(fn.loc[0] - (-(0.001 + 0.001))) < 1e-15
    assert fn.loc[STEP] > 0 and abs(fn.loc[STEP] - (0.001 + 0.001)) < 1e-15


def test_boundary_partition_no_double_count():
    dep = _deployed([1.0, 1.0, 1.0, 1.0])
    # settlement at t+8h (=STEP) must belong to candle 1, NOT candle 0
    fr = _funding({0: 0.001, H4: 0.002, STEP: 99.0})
    fn = mf.funding_net_8h(dep, fr)
    assert abs(fn.loc[0] - (-(0.001 + 0.002))) < 1e-15  # candle 0 = {0, +4h} only
    assert abs(fn.loc[STEP] - (-99.0)) < 1e-12  # the +8h settlement rolled into candle 1


def test_no_look_ahead_future_funding_corruption():
    dep = _deployed([1.0, -1.0, 1.0, -1.0])
    base_rates = {t: 0.0005 * (1 + i) for i, t in enumerate(range(0, 8 * H4, H4))}
    fn0 = mf.funding_net_8h(dep, _funding(base_rates))
    # corrupt every settlement at fundingTime >= 2*STEP (candle 2 onward)
    corrupt = {t: (9.9 if t >= 2 * STEP else r) for t, r in base_rates.items()}
    fn1 = mf.funding_net_8h(dep, _funding(corrupt))
    # candles 0 and 1 use only settlements < 2*STEP -> must be bit-identical
    assert fn1.loc[0] == fn0.loc[0]
    assert fn1.loc[STEP] == fn0.loc[STEP]
    # candle 2 DID change (proves the corruption was real, not a no-op)
    assert fn1.loc[2 * STEP] != fn0.loc[2 * STEP]


def test_datetime64_index_aligns_like_int_index():
    """Regression: the live deployed book is datetime64[ms] while funding keys are int-ms. The two
    must produce identical funding — a dtype mismatch must never silently zero funding out."""
    weights = [1.0, -1.0, 1.0, 1.0]
    dep_int = _deployed(weights)
    dep_dt = dep_int.copy()
    dep_dt.index = pd.to_datetime(dep_int.index, unit="ms")  # datetime64[ns]
    fr = _funding({t: 0.001 for t in range(0, 8 * H4, H4)})
    fn_int = mf.funding_net_8h(dep_int, fr)
    fn_dt = mf.funding_net_8h(dep_dt, fr)
    assert list(fn_int.to_numpy()) == list(fn_dt.to_numpy())
    assert fn_dt.iloc[0] != 0.0  # non-trivial: would be 0 under the old int-only reindex bug


def test_missing_symbol_contributes_zero_and_no_mutation():
    dep = _deployed([1.0, 1.0, 1.0, 1.0])
    before = dep.copy()
    fn = mf.funding_net_8h(dep, {"A": pd.Series(dtype=float)})  # empty funding
    assert (fn == 0.0).all()
    pd.testing.assert_frame_equal(dep, before)  # deployed book untouched


def test_multi_symbol_summation_and_absent_symbol():
    """Per-symbol funding sums; a symbol present in the book but absent from funding adds 0 and
    does NOT zero the others."""
    idx = [0, STEP, 2 * STEP, 3 * STEP]
    dep = pd.DataFrame({"A": [1.0] * 4, "B": [-1.0] * 4}, index=idx)
    fr = {
        "A": pd.Series({t: 0.001 for t in range(0, 8 * H4, H4)}),
        "B": pd.Series({t: 0.002 for t in range(0, 8 * H4, H4)}),
    }
    exp0 = -1.0 * (0.001 + 0.001) + 1.0 * (0.002 + 0.002)  # A pays, B earns -> +0.002
    assert abs(mf.funding_net_8h(dep, fr).loc[0] - exp0) < 1e-15
    dep2 = dep.copy()
    dep2["C"] = 1.0  # C in the book but not in the funding dict
    assert abs(mf.funding_net_8h(dep2, fr).loc[0] - exp0) < 1e-15  # A,B intact; C adds 0


def test_reindex_onto_price_net_subset_datetime64():
    """Integration seam: fnet is reindexed onto price_net.index — a datetime64 SUBSET of the
    deployed index. Alignment must survive + stay non-zero (where the int-vs-datetime bug hid)."""
    opens = pd.to_datetime([0, STEP, 2 * STEP, 3 * STEP], unit="ms").astype("datetime64[ms]")
    dep = pd.DataFrame({"A": [1.0, -1.0, 1.0, 1.0]}, index=opens)
    fr = _funding({t: 0.001 for t in range(0, 8 * H4, H4)})
    fnet = mf.funding_net_8h(dep, fr)
    price_idx = opens[1:]  # price_net.index is a datetime64 subset (last-3 candles)
    aligned = fnet.reindex(price_idx)
    assert not aligned.isna().any()  # every price candle got its funding
    assert (aligned != 0.0).any()  # non-trivial (would be 0 under the old int-only reindex bug)
    assert list(aligned.index) == list(price_idx)
