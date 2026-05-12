"""iter-v3/057 — adversarial past-only audit for parkinson_gk_ratio_20.

The feature is computed by `add_price_efficient_vol_v3_features` in
`src/crypto_trade/features_v3/price_efficient_vol_v3.py`:

    parkinson_vol_20 = sqrt(sum((log(H/L))**2) / (4*ln(2))) / 20  (20-bar trailing)
    garman_klass_vol_20 = sqrt(GK estimator from OHLC)             (20-bar trailing)
    parkinson_gk_ratio_20 = parkinson_vol_20 / garman_klass_vol_20

Both factors are 20-bar trailing rolling means terminating at bar t. The ratio
at bar t uses only OHLC data from bars [t-19, t]. The current bar's close is
observable at bar close (8h boundary); v3's trading convention is to act on
bar t+1's open, so observing close[t] at bar t-close is consistent with the
post-bar-close decision discipline (zero leakage from t+1+).

Test 1 — past_only discipline: appending future bars t+1, t+2, ... does NOT alter the
         value at bar t. The 20-bar trailing window is causal by construction.
Test 2 — within_expected_range: ratio median in [0.5, 2.0]; 95% of bars in [0.3, 2.5].
Test 3 — in_v3_feature_columns_top_n: parkinson_gk_ratio_20 MUST be in V3_FEATURE_COLUMNS_TOP_N.
Test 4 — ret_skew_50_absent: ret_skew_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N (SWAPPED OUT).
Test 5 — feature_count_14: V3_FEATURE_COLUMNS_TOP_N must have exactly 14 elements.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N
from crypto_trade.features_v3.price_efficient_vol_v3 import (
    add_price_efficient_vol_v3_features,
)


def _make_synthetic_klines(n: int, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV with realistic high-low range."""
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))
    open_ = close * np.exp(rng.normal(0.0, 0.003, n))
    high = np.maximum(open_, close) * np.exp(np.abs(rng.normal(0.0, 0.005, n)))
    low = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0.0, 0.005, n)))
    volume = rng.uniform(100, 10000, n)
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# ---------------------------------------------------------------------------
# Test 1 — past-only discipline
# ---------------------------------------------------------------------------


def test_parkinson_gk_ratio_20_past_only_discipline() -> None:
    """Appending future bars t+1, t+2, ... must NOT alter the value at bar t.

    Compute the feature on a 500-bar series. Then compute again on a 600-bar
    series (appending 100 future bars). The first 500 values must match
    within float tolerance (rtol=1e-9, atol=1e-12).
    """
    # Generate the 600-bar series; derive the 500-bar prefix from it to guarantee
    # that both share an IDENTICAL OHLCV prefix (bit-for-bit).
    longer = _make_synthetic_klines(600, seed=42)
    short = longer.iloc[:500].copy()

    short_feat = add_price_efficient_vol_v3_features(short.copy())
    longer_feat = add_price_efficient_vol_v3_features(longer.copy())

    assert "parkinson_gk_ratio_20" in short_feat.columns, (
        "parkinson_gk_ratio_20 not found in output of add_price_efficient_vol_v3_features. "
        "Check price_efficient_vol_v3.py."
    )

    s_vals = short_feat["parkinson_gk_ratio_20"].values
    l_vals = longer_feat["parkinson_gk_ratio_20"].iloc[:500].values

    # Both warmups: first 19 bars NaN expected (20-bar window min_periods=10; may
    # produce values before bar 19, but bars 0-9 should be NaN given min_periods=10).
    # Stricter check: values beyond bar 19 must be non-NaN and match.
    s_valid = s_vals[19:]
    l_valid = l_vals[19:]

    s_nan_mask = np.isnan(s_valid)
    l_nan_mask = np.isnan(l_valid)
    assert np.array_equal(s_nan_mask, l_nan_mask), (
        "NaN pattern diverges between 500-bar and 600-bar computations — "
        "parkinson_gk_ratio_20 warmup is NOT deterministic on identical prefixes. "
        "This indicates look-ahead bias or non-deterministic initialization."
    )

    s_clean = s_valid[~s_nan_mask]
    l_clean = l_valid[~l_nan_mask]
    assert len(s_clean) == len(l_clean), (
        f"n_valid mismatch: short={len(s_clean)} vs longer-first-500={len(l_clean)}. "
        "parkinson_gk_ratio_20 warmup is inconsistent between 500-bar and 600-bar series."
    )
    np.testing.assert_allclose(
        s_clean,
        l_clean,
        rtol=1e-9,
        atol=1e-12,
        err_msg=(
            "parkinson_gk_ratio_20 values diverge between 500-bar and 600-bar "
            "computations — LOOK-AHEAD BIAS DETECTED. "
            "The 20-bar rolling window must not use future bars."
        ),
    )


# ---------------------------------------------------------------------------
# Test 2 — within expected range
# ---------------------------------------------------------------------------


def test_parkinson_gk_ratio_20_within_expected_range() -> None:
    """The ratio should be in a reasonable band [0.5, 2.0] for most bars.

    Both Parkinson and Garman-Klass estimators measure the same underlying vol;
    their ratio should be near 1.0. Pathological values indicate a bug.
    """
    df = _make_synthetic_klines(2000, seed=1234)
    feat = add_price_efficient_vol_v3_features(df.copy())
    vals = feat["parkinson_gk_ratio_20"].dropna()

    assert len(vals) >= 100, (
        f"Only {len(vals)} non-NaN values in parkinson_gk_ratio_20 — "
        "expected >= 100 for a 2000-bar series."
    )

    median = float(np.median(vals))
    assert 0.5 <= median <= 2.0, (
        f"parkinson_gk_ratio_20 median={median:.4f} outside expected [0.5, 2.0] band. "
        "Possible numerical instability in Parkinson or Garman-Klass estimator. "
        "Check price_efficient_vol_v3.py."
    )

    q025 = float(np.percentile(vals, 2.5))
    q975 = float(np.percentile(vals, 97.5))
    assert q025 >= 0.3 and q975 <= 2.5, (
        f"parkinson_gk_ratio_20 2.5%-97.5% range [{q025:.4f}, {q975:.4f}] "
        "outside expected [0.3, 2.5] band. "
        "Check price_efficient_vol_v3.py for numerical instability."
    )


# ---------------------------------------------------------------------------
# Test 3 — parkinson_gk_ratio_20 in V3_FEATURE_COLUMNS_TOP_N
# ---------------------------------------------------------------------------


def test_parkinson_gk_ratio_20_in_v3_feature_columns_top_n() -> None:
    """parkinson_gk_ratio_20 MUST be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/057.

    A4 base-stack SWAP: parkinson_gk_ratio_20 SWAPPED IN for ret_skew_50 as
    the price_efficient_vol FIRST-IN-CATEGORY entry (EDA SHA `8160e3a`).
    """
    assert "parkinson_gk_ratio_20" in V3_FEATURE_COLUMNS_TOP_N, (
        "parkinson_gk_ratio_20 NOT FOUND in V3_FEATURE_COLUMNS_TOP_N. "
        "iter-v3/057: A4 base-stack SWAP requires parkinson_gk_ratio_20 PRESENT. "
        "Add 'parkinson_gk_ratio_20' to V3_FEATURE_COLUMNS_TOP_N in "
        "src/crypto_trade/features_v3/__init__.py."
    )


# ---------------------------------------------------------------------------
# Test 4 — ret_skew_50 absent from V3_FEATURE_COLUMNS_TOP_N
# ---------------------------------------------------------------------------


def test_ret_skew_50_absent_from_v3_feature_columns_top_n() -> None:
    """ret_skew_50 MUST NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/057.

    A4 base-stack SWAP: ret_skew_50 SWAPPED OUT (rank 12/14 portfolio importance;
    bottom-3 BCH+TRX per analysis/iteration_v3-057/a4_drop_ranking.csv SHA `8160e3a`).
    """
    assert "ret_skew_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "ret_skew_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT at iter-v3/057. "
        "A4 base-stack SWAP: ret_skew_50 SWAPPED OUT for parkinson_gk_ratio_20 "
        "(EDA SHA `8160e3a`; rank 12/14 bottom-3 BCH+TRX). "
        "Remove 'ret_skew_50' from V3_FEATURE_COLUMNS_TOP_N in "
        "src/crypto_trade/features_v3/__init__.py."
    )


# ---------------------------------------------------------------------------
# Test 5 — feature count remains 14 (1-for-1 SWAP)
# ---------------------------------------------------------------------------


def test_v3_feature_columns_top_n_count_14_after_swap() -> None:
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 elements after the A4 SWAP.

    iter-v3/057: 1-for-1 SWAP at base-stack level (ret_skew_50 OUT,
    parkinson_gk_ratio_20 IN). Net count must remain 14.
    """
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} elements — expected exactly 14 after "
        "iter-v3/057 A4 base-stack SWAP (ret_skew_50 OUT, parkinson_gk_ratio_20 IN). "
        "Net count must be 14 (1-for-1 SWAP). "
        "Check V3_FEATURE_COLUMNS_TOP_N in src/crypto_trade/features_v3/__init__.py."
    )
