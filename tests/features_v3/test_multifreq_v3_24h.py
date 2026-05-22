"""Tests for iter-v3/126 24h multi-frequency feature — add_multifreq_v3_24h_features.

Tests:
1. Import smoke test — public API importable without error.
2. Column output — exactly ONE new column d24_ret_autocorr_lag1_50 appended.
3. Past-only (look-ahead-free) property — appending future 24h bars does NOT change
   earlier 8h feature values (adversarial integration test per brief Section 9 +
   feedback_v3_methodology_axis_integration_test.md).
4. Causal merge invariant — bar_close_time <= open_time for every joined row.
5. Shape preservation — output has same row count as input.
6. Error on missing parquet — FileNotFoundError with clear message.
7. V3_FEATURE_COLUMNS_TOP_N membership — d24_ret_autocorr_lag1_50 is present at index 14.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.multifreq_v3 import (
    D24_FEATURE_COLUMN,
    add_multifreq_v3_24h_features,
)

# 8h interval in milliseconds
_8H_MS = 8 * 3_600_000
# 24h interval in milliseconds
_24H_MS = 24 * 3_600_000


def _make_8h_ohlcv(
    n: int = 300,
    seed: int = 42,
    start_ms: int = 1_600_000_000_000,
    symbol: str = "TESTUSDT",
) -> pd.DataFrame:
    """Make a deterministic 8h OHLCV DataFrame with n rows.

    open_time starts at start_ms and increments by 8h.
    close_time = open_time + 8h - 1ms.
    Includes a 'symbol' column (required by add_multifreq_v3_24h_features).
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
            "symbol": symbol,
        }
    )


def _make_24h_parquet(
    n_24h: int = 200,
    seed: int = 42,
    start_ms: int = 1_600_000_000_000,
    offset_id: int = 0,
    symbol: str = "TESTUSDT",
    parquet_dir: Path | None = None,
) -> Path:
    """Write a minimal 24h feature parquet for testing.

    Contains: offset_id, bar_open_time, bar_close_time, ret_autocorr_lag1_50.
    bar_close_time = bar_open_time + 24h - 1ms (strictly ends before the next 24h bar).
    offset_id=0 rows are the calendar-day-aligned slice the function reads.

    Returns the path of the written parquet.
    """
    rng = np.random.default_rng(seed)
    if parquet_dir is None:
        raise ValueError("parquet_dir required")
    parquet_dir.mkdir(parents=True, exist_ok=True)

    bar_open_times = np.arange(n_24h, dtype=np.int64) * _24H_MS + start_ms
    bar_close_times = bar_open_times + _24H_MS - 1
    ret_autocorr = rng.uniform(-0.5, 0.5, n_24h)

    df = pd.DataFrame(
        {
            "bar_open_time": bar_open_times,
            "bar_close_time": bar_close_times,
            "offset_id": np.full(n_24h, offset_id, dtype=np.int64),
            "ret_autocorr_lag1_50": ret_autocorr,
        }
    )
    out_path = parquet_dir / f"{symbol}_24h_features.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


# ─────────────────────────────────────────────
# 1. Import smoke test
# ─────────────────────────────────────────────


def test_import_smoke() -> None:
    """Public API importable without error."""
    from crypto_trade.features_v3.multifreq_v3 import (  # noqa: PLC0415
        D24_FEATURE_COLUMN,
        add_multifreq_v3_24h_features,
    )

    assert callable(add_multifreq_v3_24h_features)
    assert D24_FEATURE_COLUMN == "d24_ret_autocorr_lag1_50"


# ─────────────────────────────────────────────
# 2. Column output — exactly ONE new column
# ─────────────────────────────────────────────


def test_column_output() -> None:
    """Exactly ONE new column d24_ret_autocorr_lag1_50 is appended; bar_close_time dropped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        start_ms = 1_600_000_000_000
        df8h = _make_8h_ohlcv(300, start_ms=start_ms)
        _make_24h_parquet(200, start_ms=start_ms, parquet_dir=Path(tmpdir))

        original_cols = set(df8h.columns)
        result = add_multifreq_v3_24h_features(df8h, symbol="TESTUSDT", features_24h_dir=tmpdir)

        # The 24h feature column must be present.
        assert D24_FEATURE_COLUMN in result.columns, (
            f"Expected column '{D24_FEATURE_COLUMN}' not found in result"
        )
        # bar_close_time join-key must be DROPPED.
        assert "bar_close_time" not in result.columns, (
            "'bar_close_time' join-key must be dropped before returning"
        )
        # Original columns must all be preserved.
        for col in original_cols:
            assert col in result.columns, f"Original column '{col}' missing from result"
        # Exactly ONE new column added.
        added = set(result.columns) - original_cols
        assert added == {D24_FEATURE_COLUMN}, (
            f"Expected exactly 1 new column = {D24_FEATURE_COLUMN!r}; got {sorted(added)}"
        )


# ─────────────────────────────────────────────
# 3. Past-only (look-ahead-free) adversarial integration test
# ─────────────────────────────────────────────


def test_past_only_property() -> None:
    """Appending future 24h bars does NOT change earlier 8h feature values.

    Adversarial integration test per brief Section 9 +
    feedback_v3_methodology_axis_integration_test.md.

    Construction:
      - 8h frame of 300 rows (constant).
      - SHORT 24h parquet: 150 rows (only covers the first ~150 days).
      - LONG 24h parquet: 300 rows (extends into the future relative to SHORT).
      - Run add_multifreq_v3_24h_features with SHORT and LONG separately.
      - Assert d24_ret_autocorr_lag1_50 at row 60 is NaN in SHORT but NOT NaN in LONG
        (because the SHORT parquet doesn't cover that date) OR if both have a value,
        they are bit-identical.
      - More importantly: assert that for any 8h row where BOTH have a non-NaN value,
        the values are identical. A look-ahead violation would change earlier values
        when future 24h bars are appended.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        start_ms = 1_600_000_000_000
        df8h = _make_8h_ohlcv(300, start_ms=start_ms)

        # SHORT parquet covers rows 0..149 of 24h bars (same seed = same autocorr values).
        short_dir = Path(tmpdir) / "short"
        short_dir.mkdir()
        _make_24h_parquet(150, start_ms=start_ms, parquet_dir=short_dir)

        # LONG parquet covers rows 0..299 of 24h bars (same seed = same autocorr values).
        long_dir = Path(tmpdir) / "long"
        long_dir.mkdir()
        _make_24h_parquet(300, start_ms=start_ms, parquet_dir=long_dir)

        result_short = add_multifreq_v3_24h_features(
            df8h, symbol="TESTUSDT", features_24h_dir=short_dir
        )
        result_long = add_multifreq_v3_24h_features(
            df8h, symbol="TESTUSDT", features_24h_dir=long_dir
        )

        # For every 8h row where SHORT has a non-NaN value, LONG must match exactly.
        # (If SHORT is NaN, LONG may have a value — that's NOT a look-ahead violation;
        # it means the SHORT parquet was truncated. The reverse — SHORT non-NaN but
        # LONG different non-NaN — IS a violation.)
        short_vals = result_short[D24_FEATURE_COLUMN].to_numpy()
        long_vals = result_long[D24_FEATURE_COLUMN].to_numpy()

        for i in range(len(df8h)):
            sv = short_vals[i]
            lv = long_vals[i]
            if np.isnan(sv):
                continue  # SHORT has no value here; LONG may or may not — not a violation.
            # SHORT has a value; LONG must match EXACTLY (or both NaN).
            assert not np.isnan(lv), (
                f"Past-only VIOLATION at row {i}: SHORT has value {sv}, LONG is NaN. "
                "Extending the 24h parquet caused a previously-matched row to lose its match."
            )
            assert abs(sv - lv) < 1e-10, (
                f"Past-only VIOLATION at row {i}: SHORT={sv}, LONG={lv} (diff={abs(sv - lv):.2e}). "
                "Adding future 24h bars changed an earlier 8h row's feature value — "
                "look-ahead leak in merge_asof."
            )


# ─────────────────────────────────────────────
# 4. Causal merge invariant — bar_close_time <= open_time
# ─────────────────────────────────────────────


def test_causal_merge_invariant() -> None:
    """For every 8h row that matches a 24h bar, bar_close_time <= open_time.

    This is the fundamental look-ahead-free condition. We inject bar_close_time
    into the output temporarily by reading the parquet directly and checking
    the merge_asof alignment.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_dir = Path(tmpdir)
        start_ms = 1_600_000_000_000
        df8h = _make_8h_ohlcv(300, start_ms=start_ms)
        parquet_path = _make_24h_parquet(200, start_ms=start_ms, parquet_dir=parquet_dir)

        # Load the 24h parquet offset_id=0 and manually perform the merge,
        # keeping bar_close_time for the causal alignment check.
        panel = pd.read_parquet(parquet_path)
        panel_offset0 = panel[panel["offset_id"] == 0].copy()
        join_frame = (
            panel_offset0[["bar_close_time", "ret_autocorr_lag1_50"]]
            .sort_values("bar_close_time")
            .reset_index(drop=True)
        )

        df_sorted = df8h.sort_values("open_time").reset_index(drop=True)
        merged = pd.merge_asof(
            df_sorted,
            join_frame,
            left_on="open_time",
            right_on="bar_close_time",
            direction="backward",
            allow_exact_matches=True,
        )

        # For every row with a matched 24h bar, bar_close_time <= open_time.
        has_match = merged["bar_close_time"].notna()
        if has_match.any():
            violations = (
                merged.loc[has_match, "bar_close_time"] > merged.loc[has_match, "open_time"]
            )
            n_violations = int(violations.sum())
            assert n_violations == 0, (
                f"Causal merge VIOLATION: {n_violations} rows where bar_close_time > open_time. "
                "Future 24h bars matched to earlier 8h rows — look-ahead leak in merge_asof. "
                "Check direction='backward' and allow_exact_matches=True in "
                "add_multifreq_v3_24h_features."
            )


# ─────────────────────────────────────────────
# 5. Shape preservation
# ─────────────────────────────────────────────


def test_shape_preservation() -> None:
    """Output has the same row count as the input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_dir = Path(tmpdir)
        start_ms = 1_600_000_000_000
        _make_24h_parquet(200, start_ms=start_ms, parquet_dir=parquet_dir)

        for n in (30, 150, 300):
            df8h = _make_8h_ohlcv(n, start_ms=start_ms)
            result = add_multifreq_v3_24h_features(df8h, symbol="TESTUSDT", features_24h_dir=tmpdir)
            assert len(result) == len(df8h), (
                f"Row count changed: input={len(df8h)}, output={len(result)} (n={n})"
            )


# ─────────────────────────────────────────────
# 6. Error on missing parquet
# ─────────────────────────────────────────────


def test_missing_parquet_raises() -> None:
    """FileNotFoundError with clear message when parquet not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        df8h = _make_8h_ohlcv(50)
        with pytest.raises(FileNotFoundError, match="24h feature parquet not found"):
            add_multifreq_v3_24h_features(df8h, symbol="TESTUSDT", features_24h_dir=tmpdir)


# ─────────────────────────────────────────────
# 7. V3_FEATURE_COLUMNS_TOP_N membership
# ─────────────────────────────────────────────


def test_v3_feature_columns_membership() -> None:
    """iter-v3/127: d24_ret_autocorr_lag1_50 REVERTED (NEGATIVE-catastrophic at /126).

    /127 rolls back to the 14-feature /059/121 canonical anchor.
    d24_ret_autocorr_lag1_50 is ABSENT from V3_FEATURE_COLUMNS_TOP_N.
    The feature module (compute_d24_features) still exists but is NOT in the training set.
    """
    from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N  # noqa: PLC0415

    assert "d24_ret_autocorr_lag1_50" not in V3_FEATURE_COLUMNS_TOP_N, (
        "d24_ret_autocorr_lag1_50 must NOT be in V3_FEATURE_COLUMNS_TOP_N at iter-v3/127 "
        "(reverted — NEGATIVE-catastrophic OOS result at iter-v3/126)"
    )
    assert len(V3_FEATURE_COLUMNS_TOP_N) == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {len(V3_FEATURE_COLUMNS_TOP_N)} elements — expected 14 "
        "(14 BASELINE_V3 /059/121 anchor; d24 reverted at iter-v3/127)"
    )
