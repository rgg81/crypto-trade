"""Tests for v3 technical indicator features — iter-v3/063.

Tests:
1. Import smoke test — public API importable without error.
2. adx_14 shape — output has same length as input.
3. adx_14 range — values in [0, 100] (or NaN).
4. adx_14 NaN warm-up — first ~27 bars are NaN.
5. adx_14 past-only — appending future bars does not alter bar t's value.
6. adx_14 missing columns — graceful all-NaN fallback, no error.
7. add_technical_v3_features integration — column added to DataFrame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3.technical_v3 import add_technical_v3_features


def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Make a deterministic OHLCV DataFrame with n rows."""
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.01, n))
    high = close * (1.0 + rng.uniform(0.001, 0.02, n))
    low = close * (1.0 - rng.uniform(0.001, 0.02, n))
    open_ = close * (1.0 + rng.normal(0, 0.005, n))
    volume = rng.uniform(1e6, 1e7, n)
    return pd.DataFrame(
        {
            "open_time": np.arange(n) * 3_600_000 * 8,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_import_smoke():
    """Public API importable without error."""
    from crypto_trade.features_v3.technical_v3 import add_technical_v3_features  # noqa: PLC0415

    assert callable(add_technical_v3_features)


def test_adx_14_shape():
    """adx_14 output has same length as input."""
    df = _make_ohlcv(200)
    result = add_technical_v3_features(df)
    assert "adx_14" in result.columns
    assert len(result["adx_14"]) == len(df)


def test_adx_14_range():
    """adx_14 values are in [0, 100] for non-NaN entries."""
    df = _make_ohlcv(300)
    result = add_technical_v3_features(df)
    adx = result["adx_14"].dropna()
    assert len(adx) > 0, "Expected some non-NaN values after warm-up"
    assert adx.min() >= 0.0, f"ADX below 0: {adx.min()}"
    assert adx.max() <= 100.0, f"ADX above 100: {adx.max()}"


def test_adx_14_nan_warmup():
    """First ~27 bars should be NaN (warm-up period for Wilder smoothing)."""
    df = _make_ohlcv(200)
    result = add_technical_v3_features(df)
    adx = result["adx_14"].to_numpy()
    # The first (period - 1) + (period - 1) = 26 bars should be NaN
    # (14 bars for DX seed + 14 bars for ADX seed; first bar at bar 27)
    # We check that at least the first 25 bars are NaN
    assert np.all(np.isnan(adx[:25])), "Expected NaN warm-up for first 25 bars"
    # And there's eventually a valid value
    valid = adx[~np.isnan(adx)]
    assert len(valid) > 100, "Expected many valid ADX values after warm-up"


def test_adx_14_past_only():
    """Appending future bars does not alter bar t's adx_14 value."""
    df = _make_ohlcv(200)
    result_short = add_technical_v3_features(df.iloc[:150].copy())
    result_long = add_technical_v3_features(df.copy())

    # Bar 100 in both should be identical (past-only)
    val_short = result_short["adx_14"].iloc[100]
    val_long = result_long["adx_14"].iloc[100]

    if np.isnan(val_short) and np.isnan(val_long):
        pass  # both NaN is fine
    else:
        assert abs(val_short - val_long) < 1e-10, (
            f"Past-only violation: adx_14[100] differs after appending future bars. "
            f"Short: {val_short}, Long: {val_long}"
        )


def test_adx_14_missing_columns():
    """Graceful all-NaN fallback when required columns are missing."""
    df = pd.DataFrame({"open_time": np.arange(50), "close": np.ones(50)})
    # No high/low columns
    result = add_technical_v3_features(df)
    assert "adx_14" in result.columns
    assert np.all(np.isnan(result["adx_14"]))


def test_add_technical_v3_features_integration():
    """add_technical_v3_features adds adx_14 column to DataFrame."""
    df = _make_ohlcv(200)
    original_cols = set(df.columns)
    result = add_technical_v3_features(df)
    assert "adx_14" in result.columns
    assert "adx_14" not in original_cols  # new column added
    # Original columns preserved
    for col in original_cols:
        assert col in result.columns
