"""Tests for v3 calendar features — iter-v3/063.

Tests:
1. Import smoke test — public API importable without error.
2. Cyclic encoding invariant — sin² + cos² = 1 for all bars.
3. DOW values are periodic — same DOW on two dates 7 days apart gives same encoding.
4. Shape — output has same length as input.
5. Missing open_time column — graceful all-NaN fallback.
6. add_calendar_v3_features integration — both columns added to DataFrame.
7. NaN warm-up — no warm-up (both columns valid from first bar).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3.calendar_v3 import add_calendar_v3_features

# Monday 2024-01-01 00:00:00 UTC in milliseconds
_MONDAY_2024_01_01_MS: int = 1704067200000
_8H_MS: int = 8 * 3600 * 1000


def _make_df(n: int = 50, start_ms: int = _MONDAY_2024_01_01_MS) -> pd.DataFrame:
    """Make a DataFrame with open_time at 8h intervals starting from start_ms."""
    open_times = start_ms + np.arange(n) * _8H_MS
    return pd.DataFrame({"open_time": open_times, "close": np.ones(n)})


def test_import_smoke():
    """Public API importable without error."""
    from crypto_trade.features_v3.calendar_v3 import add_calendar_v3_features  # noqa: PLC0415

    assert callable(add_calendar_v3_features)


def test_cyclic_encoding_unit_circle():
    """sin² + cos² must equal 1 for all bars (cyclic encoding invariant)."""
    df = _make_df(100)
    result = add_calendar_v3_features(df)
    sin_sq = result["candle_dow_sin"] ** 2
    cos_sq = result["candle_dow_cos"] ** 2
    unit_check = sin_sq + cos_sq
    np.testing.assert_allclose(unit_check, 1.0, atol=1e-12, err_msg="sin²+cos²≠1")


def test_dow_periodic():
    """Same DOW on dates 7 days apart must produce identical encoding."""
    df = _make_df(50)
    result = add_calendar_v3_features(df)
    # At 8h cadence, 3 candles per day. After 21 bars (7 days), DOW repeats.
    # Bar 0 (Monday 00:00) and bar 21 (Monday 00:00, next week) should match.
    val_0_sin = result["candle_dow_sin"].iloc[0]
    val_21_sin = result["candle_dow_sin"].iloc[21]
    val_0_cos = result["candle_dow_cos"].iloc[0]
    val_21_cos = result["candle_dow_cos"].iloc[21]
    assert abs(val_0_sin - val_21_sin) < 1e-12, (
        f"DOW sin not periodic: bar 0={val_0_sin}, bar 21={val_21_sin}"
    )
    assert abs(val_0_cos - val_21_cos) < 1e-12, (
        f"DOW cos not periodic: bar 0={val_0_cos}, bar 21={val_21_cos}"
    )


def test_shape():
    """Output has same length as input."""
    n = 77
    df = _make_df(n)
    result = add_calendar_v3_features(df)
    assert len(result["candle_dow_sin"]) == n
    assert len(result["candle_dow_cos"]) == n


def test_no_nan_warmup():
    """Both columns valid from first bar (no warm-up period)."""
    df = _make_df(50)
    result = add_calendar_v3_features(df)
    assert not result["candle_dow_sin"].isna().any(), "candle_dow_sin has unexpected NaN"
    assert not result["candle_dow_cos"].isna().any(), "candle_dow_cos has unexpected NaN"


def test_missing_open_time():
    """Graceful all-NaN fallback when open_time is missing."""
    df = pd.DataFrame({"close": np.ones(30)})
    result = add_calendar_v3_features(df)
    assert "candle_dow_sin" in result.columns
    assert "candle_dow_cos" in result.columns
    assert np.all(np.isnan(result["candle_dow_sin"]))
    assert np.all(np.isnan(result["candle_dow_cos"]))


def test_integration():
    """add_calendar_v3_features adds both columns to DataFrame."""
    df = _make_df(50)
    original_cols = set(df.columns)
    result = add_calendar_v3_features(df)
    assert "candle_dow_sin" in result.columns
    assert "candle_dow_cos" in result.columns
    assert "candle_dow_sin" not in original_cols
    assert "candle_dow_cos" not in original_cols
    # Original columns preserved
    for col in original_cols:
        assert col in result.columns


def test_encoding_distinct_days():
    """Different days of week must produce different (sin, cos) pairs."""
    # Create a 7-day span to cover all DOW values (21 bars at 8h cadence)
    df = _make_df(21)
    result = add_calendar_v3_features(df)
    # Take one candle per day (every 3rd bar)
    sin_vals = result["candle_dow_sin"].iloc[::3].tolist()
    cos_vals = result["candle_dow_cos"].iloc[::3].tolist()
    # All 7 (sin, cos) pairs should be distinct
    pairs = list(zip(sin_vals, cos_vals))
    assert len(set(pairs)) == 7, f"Expected 7 distinct DOW encodings, got {len(set(pairs))}"
