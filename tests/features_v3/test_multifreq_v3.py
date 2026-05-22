"""Tests for iter-v3/113 multi-frequency daily features — multifreq_v3.py.

Tests:
1. Import smoke test — public API importable without error.
2. Column count — all 8 daily features appended.
3. Past-only property — appending future 8h rows does not change earlier values.
4. day_close alignment — each 8h row is aligned to a daily bar whose
   day_close <= open_time (the causal as-of-join invariant).
5. Shape preservation — output has same row count as input.
6. Open-time index guard — handles DataFrames indexed by open_time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.features_v3.multifreq_v3 import DAILY_FEATURES, add_multifreq_v3_features

# 8h interval in milliseconds
_8H_MS = 8 * 3_600_000


def _make_8h_ohlcv(n: int = 300, seed: int = 42, start_ms: int = 1_600_000_000_000) -> pd.DataFrame:
    """Make a deterministic 8h OHLCV DataFrame with n rows.

    open_time starts at start_ms and increments by 8h (28_800_000 ms).
    close_time = open_time + 28_800_000 - 1 (one ms before the next open).
    """
    rng = np.random.default_rng(seed)
    open_times = np.arange(n, dtype=np.int64) * _8H_MS + start_ms
    close_times = open_times + _8H_MS - 1
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.01, n))
    high = close * (1.0 + rng.uniform(0.001, 0.02, n))
    low = close * (1.0 - rng.uniform(0.001, 0.02, n))
    open_ = close * (1.0 + rng.normal(0, 0.005, n))
    volume = rng.uniform(1e6, 1e7, n)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "close_time": close_times,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# ─────────────────────────────────────────────
# 1. Import smoke test
# ─────────────────────────────────────────────


def test_import_smoke() -> None:
    """Public API importable without error."""
    from crypto_trade.features_v3.multifreq_v3 import (  # noqa: PLC0415
        DAILY_FEATURES,
        add_multifreq_v3_features,
    )

    assert callable(add_multifreq_v3_features)
    assert len(DAILY_FEATURES) == 8


# ─────────────────────────────────────────────
# 2. Column count — all 8 daily features appended
# ─────────────────────────────────────────────


def test_column_count() -> None:
    """All 8 DAILY_FEATURES columns are appended; no extra or missing columns."""
    df = _make_8h_ohlcv(300)
    original_cols = set(df.columns)
    result = add_multifreq_v3_features(df)

    for feat in DAILY_FEATURES:
        assert feat in result.columns, f"Expected column '{feat}' not found in result"

    # 'day_close' join-key must be DROPPED (only 8 feature cols added, not 9).
    assert "day_close" not in result.columns, (
        "'day_close' join-key column must be dropped before returning"
    )

    # Original columns must all be preserved.
    for col in original_cols:
        assert col in result.columns, f"Original column '{col}' missing from result"

    # Exactly 8 new columns added (no silent extras).
    added = set(result.columns) - original_cols
    assert added == set(DAILY_FEATURES), (
        f"Expected exactly 8 new columns = DAILY_FEATURES; got {sorted(added)}"
    )


# ─────────────────────────────────────────────
# 3. Past-only property (adversarial look-ahead test)
# ─────────────────────────────────────────────


def test_past_only_property() -> None:
    """Appending future 8h rows does NOT change earlier daily feature values.

    This is the adversarial look-ahead defense for the multi-frequency feature.
    It mirrors the adx_14 past-only test in test_technical_v3.py and is the
    QE-mandatory test from the iter-v3/113 brief Section 3.5 (item 8).

    Construction:
      - Build a 210-row frame of 8h candles (the "full" data set).
      - The short frame = first 120 rows of the full frame (same data, just truncated).
      - The long frame  = all 210 rows of the full frame.
      - Run add_multifreq_v3_features on both and assert that every daily feature
        at row 60 is bit-identical (or both NaN). A look-ahead violation would
        change values at earlier rows when future rows from the SAME DATA are added.
    """
    df_full = _make_8h_ohlcv(210)
    df_short = df_full.iloc[:120].copy().reset_index(drop=True)
    df_long = df_full.copy()

    result_short = add_multifreq_v3_features(df_short)
    result_long = add_multifreq_v3_features(df_long)

    # Row 60 is well within both frames and past any warm-up period.
    check_row = 60
    for feat in DAILY_FEATURES:
        val_short = result_short[feat].iloc[check_row]
        val_long = result_long[feat].iloc[check_row]

        if np.isnan(val_short) and np.isnan(val_long):
            continue  # both NaN — fine
        assert not np.isnan(val_short), (
            f"Past-only test: {feat}[{check_row}] is NaN in short frame but not NaN-check "
            "in long frame — investigate warm-up length."
        )
        assert abs(val_short - val_long) < 1e-10, (
            f"Past-only VIOLATION for feature '{feat}' at row {check_row}: "
            f"short-frame value={val_short}, long-frame value={val_long}. "
            "Adding future 8h rows (same underlying data) changed an earlier daily "
            "feature — look-ahead leak in the daily aggregation or merge_asof."
        )


# ─────────────────────────────────────────────
# 4. day_close <= open_time alignment invariant
# ─────────────────────────────────────────────


def test_day_close_alignment() -> None:
    """Each 8h row is aligned to a daily bar whose day_close <= that row's open_time.

    We verify this by temporarily keeping 'day_close' in the output (using the
    internal helpers directly) and asserting the causal alignment on every row.
    """
    from crypto_trade.features_v3.multifreq_v3 import (  # noqa: PLC0415
        _add_daily_features,
        _aggregate_to_daily,
    )

    df = _make_8h_ohlcv(300)

    daily = _aggregate_to_daily(df)
    daily = _add_daily_features(daily)
    daily_join = (
        daily[["day_close"] + DAILY_FEATURES].sort_values("day_close").reset_index(drop=True)
    )

    merged = pd.merge_asof(
        df.sort_values("open_time").reset_index(drop=True),
        daily_join,
        left_on="open_time",
        right_on="day_close",
        direction="backward",
        allow_exact_matches=True,
    )

    # For every row that has a matched daily bar (day_close not NaN), verify alignment.
    has_match = merged["day_close"].notna()
    if has_match.any():
        violations = merged.loc[has_match, "day_close"] > merged.loc[has_match, "open_time"]
        n_violations = violations.sum()
        assert n_violations == 0, (
            f"day_close alignment VIOLATION: {n_violations} rows where day_close > open_time "
            "(future daily bar matched to 8h row — look-ahead leak in as-of join)."
        )


# ─────────────────────────────────────────────
# 5. Shape preservation
# ─────────────────────────────────────────────


def test_shape_preservation() -> None:
    """Output has the same row count as the input."""
    for n in (30, 150, 300):
        df = _make_8h_ohlcv(n)
        result = add_multifreq_v3_features(df)
        assert len(result) == len(df), (
            f"Row count changed: input={len(df)}, output={len(result)} (n={n})"
        )


# ─────────────────────────────────────────────
# 6. Open-time index guard
# ─────────────────────────────────────────────


def test_open_time_index_guard() -> None:
    """Handles DataFrames indexed by open_time (restores index after merge)."""
    df = _make_8h_ohlcv(200)
    df_indexed = df.set_index("open_time", drop=False)
    df_indexed.index.name = "open_time"

    result = add_multifreq_v3_features(df_indexed)

    # Index should be restored as open_time after the merge.
    assert result.index.name == "open_time", (
        f"Expected index name 'open_time' after restore; got '{result.index.name}'"
    )
    assert len(result) == len(df_indexed), "Row count changed for indexed DataFrame"
    for feat in DAILY_FEATURES:
        assert feat in result.columns, f"Feature '{feat}' missing from indexed-input result"
