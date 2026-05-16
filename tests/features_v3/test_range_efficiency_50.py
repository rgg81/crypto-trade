"""Adversarial tests for compute_range_efficiency_50 — iter-v3/076.

range_efficiency_50 is the cycle-2 EXPLORATION #6 axis: a sign-invariant
Kaufman-style 50-bar path-efficiency feature, a feature-internal IS-regime
discriminator the LightGBM model learns. It uses the same Kaufman path-efficiency
MATH as the dead-code compute_efficiency_ratio_50 (re-evaluation per
feedback_v3_walkforward_lookahead_bug.md; brief Section 10.2) under a new name
and a new role.

6 tests per brief Section 3.1 #7:

1. test_range_efficiency_50_appends_column_in_unit_range — output column in [0,1].
2. test_range_efficiency_50_past_only — appending a future bar does not change
   any prior bar's value (the .shift(1) past-only contract).
3. test_range_efficiency_50_warmup_is_zero — first 51 bars are 0.0 (the
   .fillna(0.0) neutral warm-up fill).
4. test_range_efficiency_50_clean_trend_high_chop_low — a clean monotone ramp
   yields a high value; a sawtooth chop yields a low value (the discrimination
   mechanism the EDA T2 measures).
5. test_range_efficiency_50_sign_invariant — a clean UP ramp and a clean DOWN
   ramp yield the SAME value (the SIGN-INVARIANT property — the load-bearing
   reason the feature escapes the /075 IS-up/OOS-down trap).
6. test_add_engineered_v3_features_dispatches_range_efficiency_50 — the
   GROUP_REGISTRY entry point dispatches the feature (integration-style).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3.engineered_v3 import (
    add_engineered_v3_features,
    compute_range_efficiency_50,
)

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC


def _make_df(close_values: np.ndarray) -> pd.DataFrame:
    """Minimal DataFrame with open_time + close for compute_range_efficiency_50."""
    n = len(close_values)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    return pd.DataFrame({"open_time": open_times, "close": np.asarray(close_values, dtype=float)})


# ---------------------------------------------------------------------------
# Test 1: output column exists and is in [0, 1]
# ---------------------------------------------------------------------------
def test_range_efficiency_50_appends_column_in_unit_range() -> None:
    """compute_range_efficiency_50 appends range_efficiency_50 with values in [0,1]."""
    rng = np.random.default_rng(42)
    close = np.cumprod(1.0 + rng.normal(0.0, 0.02, 300)) * 100.0
    out = compute_range_efficiency_50(_make_df(close))

    assert "range_efficiency_50" in out.columns, (
        "compute_range_efficiency_50 must append a 'range_efficiency_50' column."
    )
    vals = out["range_efficiency_50"].to_numpy()
    assert np.isfinite(vals).all(), "range_efficiency_50 must have no NaN/inf (fillna 0.0)."
    assert (vals >= 0.0).all() and (vals <= 1.0).all(), (
        f"range_efficiency_50 must be bounded to [0, 1]; observed [{vals.min()}, {vals.max()}]."
    )


# ---------------------------------------------------------------------------
# Test 2: past-only discipline
# ---------------------------------------------------------------------------
def test_range_efficiency_50_past_only() -> None:
    """Appending a future bar must NOT alter the value at any existing bar t.

    The 50-bar rolling window + .shift(1) make bar t use close[t-51..t-1] only —
    appending close[n], close[n+1], ... cannot change the value at bars 0..n-1.
    """
    n = 200
    rng = np.random.default_rng(77)
    close = np.cumprod(1.0 + rng.normal(0.0, 0.02, n)) * 100.0

    short = compute_range_efficiency_50(_make_df(close))["range_efficiency_50"].to_numpy()
    # append a wildly different future bar
    close_long = np.append(close, 1e9)
    long = compute_range_efficiency_50(_make_df(close_long))["range_efficiency_50"].to_numpy()

    for i in range(n):
        assert np.isclose(short[i], long[i], rtol=1e-10, atol=1e-12), (
            f"Bar {i}: past-only violation. short={short[i]}, long={long[i]}. "
            "Appending a future bar must not alter prior bar values."
        )


# ---------------------------------------------------------------------------
# Test 3: warm-up bars are 0.0
# ---------------------------------------------------------------------------
def test_range_efficiency_50_warmup_is_zero() -> None:
    """First 51 bars must be 0.0 (50-bar rolling window + shift(1), fillna 0.0)."""
    rng = np.random.default_rng(13)
    close = np.cumprod(1.0 + rng.normal(0.0, 0.02, 200)) * 100.0
    vals = compute_range_efficiency_50(_make_df(close))["range_efficiency_50"].to_numpy()

    assert np.allclose(vals[:51], 0.0), (
        f"First 51 bars must be 0.0 (neutral warm-up fill). Got: {vals[:51]}"
    )
    # bar 51 onward should be genuine (not all zero — a random walk has some efficiency)
    assert not np.allclose(vals[51:], 0.0), (
        "Bars 51+ must carry genuine efficiency values, not all 0.0."
    )


# ---------------------------------------------------------------------------
# Test 4: clean trend -> high efficiency, chop -> low efficiency
# ---------------------------------------------------------------------------
def test_range_efficiency_50_clean_trend_high_chop_low() -> None:
    """A clean monotone ramp yields a HIGH efficiency; a sawtooth chop yields LOW.

    This is the discrimination mechanism the EDA T2 measures (AUC 0.657 separating
    winning vs losing IS-bear/chop trades).
    """
    n = 120
    # clean monotone ramp: every bar moves the same direction -> efficiency ~= 1.0
    clean = 100.0 + np.arange(n, dtype=float)
    clean_eff = compute_range_efficiency_50(_make_df(clean))["range_efficiency_50"].to_numpy()

    # sawtooth chop: alternating up/down, near-zero net displacement -> efficiency ~= 0
    chop = 100.0 + np.array([(i % 2) for i in range(n)], dtype=float)
    chop_eff = compute_range_efficiency_50(_make_df(chop))["range_efficiency_50"].to_numpy()

    # evaluate at a post-warmup bar
    t = 100
    assert clean_eff[t] > 0.9, (
        f"A clean monotone ramp must yield high efficiency at bar {t}; got {clean_eff[t]}."
    )
    assert chop_eff[t] < 0.2, (
        f"A sawtooth chop must yield low efficiency at bar {t}; got {chop_eff[t]}."
    )
    assert clean_eff[t] > chop_eff[t], (
        "Clean trend efficiency must exceed choppy-grind efficiency — the discrimination mechanism."
    )


# ---------------------------------------------------------------------------
# Test 5: sign-invariance (the load-bearing /076 property)
# ---------------------------------------------------------------------------
def test_range_efficiency_50_sign_invariant() -> None:
    """A clean UP ramp and a clean DOWN ramp yield the SAME efficiency value.

    range_efficiency_50 measures HOW price moves (clean vs choppy), NOT WHICH WAY.
    This SIGN-INVARIANCE is the load-bearing property: it makes the feature
    regime-orthogonal (it is not a directional-regime proxy), which is what lets
    it escape the /075 IS-up/OOS-down structural tension (brief Section 2.3).
    """
    n = 120
    up = 100.0 + np.arange(n, dtype=float)  # clean monotone up
    down = 100.0 + (n - 1) - np.arange(n, dtype=float)  # clean monotone down (mirror)

    up_eff = compute_range_efficiency_50(_make_df(up))["range_efficiency_50"].to_numpy()
    down_eff = compute_range_efficiency_50(_make_df(down))["range_efficiency_50"].to_numpy()

    # post-warmup: the up ramp and the down ramp must produce identical efficiency
    for t in range(51, n):
        assert np.isclose(up_eff[t], down_eff[t], rtol=1e-9, atol=1e-9), (
            f"Bar {t}: sign-invariance violation. up={up_eff[t]}, down={down_eff[t]}. "
            "range_efficiency_50 must be identical for a clean up-trend and a clean "
            "down-trend — the SIGN-INVARIANT property (brief Section 2.3)."
        )


# ---------------------------------------------------------------------------
# Test 6: GROUP_REGISTRY dispatch (integration-style)
# ---------------------------------------------------------------------------
def test_add_engineered_v3_features_dispatches_range_efficiency_50() -> None:
    """add_engineered_v3_features must dispatch compute_range_efficiency_50.

    Exercises the GROUP_REGISTRY entry-point path, not just the math function in
    isolation. The synthetic frame carries the columns the other engineered
    features need so the full dispatch chain runs.
    """
    n = 300
    rng = np.random.default_rng(5)
    close = np.cumprod(1.0 + rng.normal(0.0, 0.02, n)) * 100.0
    df = pd.DataFrame(
        {
            "open_time": [_IS_START_MS + i * _8H_MS for i in range(n)],
            "close": close,
            # columns other engineered features may read (graceful if absent,
            # but provided here so the dispatch chain exercises cleanly)
            "hurst_100": rng.uniform(0.3, 0.7, n),
        }
    )
    out = add_engineered_v3_features(df)

    assert "range_efficiency_50" in out.columns, (
        "add_engineered_v3_features must dispatch compute_range_efficiency_50 "
        "(the iter-v3/076 EXPLORATION #6 axis)."
    )
    vals = out["range_efficiency_50"].to_numpy()
    assert np.isfinite(vals).all() and (vals >= 0.0).all() and (vals <= 1.0).all(), (
        "range_efficiency_50 from the dispatch path must be finite and in [0, 1]."
    )
