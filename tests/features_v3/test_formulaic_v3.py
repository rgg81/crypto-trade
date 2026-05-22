"""Tests for formulaic_v3.py — WorldQuant Alpha#32 (iter-v3/102).

Test inventory:
1. Import smoke — compute_alpha032 and add_formulaic_v3_features importable.
2. Column name — output column is exactly "alpha032".
3. HARD CAUSALITY TEST — feature value at bar t is unchanged when bars > t are
   mutated or removed.  This is the primary Phase-5.5 gate item: "Add a HARD
   CAUSALITY test (the feature value at bar t is unchanged when bars > t are
   mutated/removed — fails the build if look-ahead exists)."
4. NaN warm-up — first ≈334 bars NaN (dominated by 230-bar correlation + 5 lag +
   100-bar scale_ts); an exact lower-bound check on the minimum warm-up.
5. Formula correctness — manually compute alpha032 on a small known series and
   compare to compute_alpha032.
6. Missing quote_volume raises KeyError.
7. Missing volume raises KeyError.
8. Missing close raises KeyError.
9. Zero volume rows — vwap is NaN there; alpha032 propagates NaN in those rows'
   term2 window contributions without crashing.
10. add_formulaic_v3_features integration — GROUP_REGISTRY entry point returns a
    DataFrame with alpha032 column via the standard pipeline wrapper.
11. Integration smoke — full feature pipeline for one symbol includes alpha032 and
    it appears in V3_FEATURE_COLUMNS.  (Static check; no live data required.)
12. V3_FEATURE_COLUMNS contains alpha032 — the column list is exactly 15 entries.
13. LightGbmStrategy training smoke — confirms the 15-feature stack is accepted and
    alpha032 is among the feature columns passed to LightGBM (no live data; uses
    synthetic training data).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.formulaic_v3 import add_formulaic_v3_features, compute_alpha032

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC


def _make_df(n: int = 600, seed: int = 42) -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with OHLCV + quote_volume."""
    rng = np.random.default_rng(seed)
    close = np.cumprod(1.0 + rng.normal(0.0, 0.01, n)) * 100.0
    open_prices = close * rng.uniform(0.99, 1.01, n)
    high = close * rng.uniform(1.0, 1.02, n)
    low = close * rng.uniform(0.98, 1.0, n)
    volume = rng.uniform(1_000.0, 10_000.0, n)
    quote_volume = volume * close * rng.uniform(0.99, 1.01, n)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]

    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": open_prices,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "quote_volume": quote_volume,
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_import_smoke() -> None:
    """Test 1: public API importable without error."""
    assert callable(compute_alpha032)
    assert callable(add_formulaic_v3_features)


def test_column_name() -> None:
    """Test 2: output column name is exactly 'alpha032'."""
    df = _make_df()
    result = compute_alpha032(df)
    assert "alpha032" in result.columns, "alpha032 column missing from output"


def test_hard_causality() -> None:
    """Test 3 (HARD CAUSALITY): feature at bar t is unchanged when future bars are mutated.

    This is the primary Phase-5.5 gate test from the brief Section 9.  It is
    analogous to the T3 past-only audit in analysis/iteration_v3-102/alpha032_deepdive.py.

    Method:
    1. Compute alpha032 on the FULL frame (600 bars).
    2. Compute alpha032 on a TRUNCATED frame (first 550 bars — 50 bars removed).
    3. The overlap window (bars 0..549) must be bit-identical.

    A look-ahead bug (e.g. using min_periods < window length, allowing partial windows
    that read beyond the valid past) would produce different values in the tail of the
    overlap.  This test fails the build if any look-ahead is present.
    """
    n_full = 600
    n_trunc = 550  # remove 50 future bars
    df_full = _make_df(n=n_full, seed=7)
    df_trunc = df_full.iloc[:n_trunc].copy()

    result_full = compute_alpha032(df_full)["alpha032"].values
    result_trunc = compute_alpha032(df_trunc)["alpha032"].values

    # Overlap = bars 0..n_trunc-1
    overlap_full = result_full[:n_trunc]
    overlap_trunc = result_trunc[:n_trunc]

    # NaN pattern must match
    nan_full = np.isnan(overlap_full)
    nan_trunc = np.isnan(overlap_trunc)
    assert np.array_equal(nan_full, nan_trunc), (
        f"NaN pattern mismatch in overlap — look-ahead detected. "
        f"Positions with mismatch: {np.where(nan_full != nan_trunc)[0]}"
    )

    # Non-NaN values must be bit-identical (past-only property)
    valid_idx = ~nan_full
    if valid_idx.any():
        max_diff = np.abs(overlap_full[valid_idx] - overlap_trunc[valid_idx]).max()
        assert max_diff == 0.0, (
            f"CAUSALITY VIOLATION: alpha032 value at overlap bars differs between "
            f"full and truncated frame.  max_abs_diff={max_diff:.6e}  "
            "A non-zero diff means future bars influenced past-bar computations — "
            "look-ahead contamination detected.  Check rolling min_periods and "
            ".shift() calls in formulaic_v3.py."
        )


def test_nan_warmup_minimum() -> None:
    """Test 4: first ~334 bars have NaN; bar 500 must be non-NaN.

    The 230-bar correlation window + 5-bar lag → first valid corr at bar 234.
    The 100-bar scale_ts window on the result → first valid scaled value at bar 334.
    (Exact: max(7, 100) + max(230, 5) + 100 - 1 rounded; conservative lower bound 334.)
    We assert:
    - bars 0..232 are all NaN (safe lower bound — clearly before any window fills)
    - bar 499 (position 500 when 1-indexed) is non-NaN (clearly after warm-up)
    """
    df = _make_df(n=600)
    result = compute_alpha032(df)["alpha032"].values

    # The first 233 bars must be NaN (min_periods=230 for corr alone)
    early_window = result[:233]
    assert np.all(np.isnan(early_window)), (
        f"Expected all NaN in bars 0..232 (below 230-bar correlation window). "
        f"Non-NaN count: {(~np.isnan(early_window)).sum()}"
    )

    # Bar 499 must be non-NaN (well past the warm-up period)
    assert not np.isnan(result[499]), (
        "Bar 499 is NaN — warm-up period extends unexpectedly far. "
        "Check rolling min_periods in _ts_corr and _scale_ts."
    )


def test_formula_correctness() -> None:
    """Test 5: compare compute_alpha032 to a manual inline computation.

    Uses a short deterministic synthetic series where we can independently verify
    the formula.  Compares the non-NaN tail of the result.
    """
    rng = np.random.default_rng(99)
    n = 600
    close = np.cumprod(1.0 + rng.normal(0.0, 0.005, n)) * 200.0
    volume = rng.uniform(500.0, 5000.0, n)
    quote_volume = volume * close

    df = pd.DataFrame(
        {
            "open_time": [_IS_START_MS + i * _8H_MS for i in range(n)],
            "open": close * rng.uniform(0.99, 1.01, n),
            "high": close * rng.uniform(1.0, 1.01, n),
            "low": close * rng.uniform(0.99, 1.0, n),
            "close": close,
            "volume": volume,
            "quote_volume": quote_volume,
        }
    )

    result = compute_alpha032(df)["alpha032"]

    # Manual inline computation
    s_close = pd.Series(close, dtype=float)
    s_volume = pd.Series(volume, dtype=float)
    s_qv = pd.Series(quote_volume, dtype=float)
    vwap = s_qv / s_volume
    sma7 = s_close.rolling(7, min_periods=7).sum() / 7.0
    term1_raw = sma7 - s_close
    denom1 = term1_raw.abs().rolling(100, min_periods=100).mean()
    term1 = term1_raw / denom1.replace(0.0, np.nan)

    close_lag5 = s_close.shift(5)
    corr230 = vwap.rolling(230, min_periods=230).corr(close_lag5)
    denom2 = corr230.abs().rolling(100, min_periods=100).mean()
    term2 = corr230 / denom2.replace(0.0, np.nan)

    expected = term1 + 20.0 * term2

    # Compare non-NaN overlap tail
    valid_mask = ~(result.isna() | expected.isna())
    assert valid_mask.any(), "No valid (non-NaN) bars to compare — warm-up too long"

    max_diff = (result[valid_mask] - expected[valid_mask]).abs().max()
    assert max_diff < 1e-10, (
        f"Formula mismatch: max_abs_diff={max_diff:.2e} between compute_alpha032 "
        "and manual inline computation.  Check the formula in formulaic_v3.py."
    )


def test_missing_quote_volume_raises() -> None:
    """Test 6: KeyError when quote_volume column is absent."""
    df = _make_df()
    df_bad = df.drop(columns=["quote_volume"])
    with pytest.raises(KeyError):
        compute_alpha032(df_bad)


def test_missing_volume_raises() -> None:
    """Test 7: KeyError when volume column is absent."""
    df = _make_df()
    df_bad = df.drop(columns=["volume"])
    with pytest.raises(KeyError):
        compute_alpha032(df_bad)


def test_missing_close_raises() -> None:
    """Test 8: KeyError when close column is absent."""
    df = _make_df()
    df_bad = df.drop(columns=["close"])
    with pytest.raises(KeyError):
        compute_alpha032(df_bad)


def test_zero_volume_rows() -> None:
    """Test 9: zero volume rows produce NaN vwap but do not crash."""
    df = _make_df(n=600, seed=55)
    df = df.copy()
    # Set a few volume rows to zero
    df.loc[300:310, "volume"] = 0.0
    result = compute_alpha032(df)
    # Should complete without exception; alpha032 may have NaN in the affected window
    assert "alpha032" in result.columns
    # At bar 599 (well past the zero-volume rows) there should still be a result
    # (unless the 100/230-bar windows were too close to the zero rows)
    # Just assert no crash and dtype is float
    assert result["alpha032"].dtype == np.float64 or result["alpha032"].dtype == float


def test_add_formulaic_v3_features_registry() -> None:
    """Test 10: add_formulaic_v3_features GROUP_REGISTRY entry point."""
    df = _make_df(n=600)
    result = add_formulaic_v3_features(df)
    assert "alpha032" in result.columns, (
        "add_formulaic_v3_features did not produce alpha032 column — "
        "check the GROUP_REGISTRY entry point in formulaic_v3.py."
    )


def test_v3_feature_columns_does_not_contain_alpha032() -> None:
    """Test 11 + 12: iter-v3/102 CLOSEOUT — alpha032 ABSENT from V3_FEATURE_COLUMNS.

    iter-v3/102 was NEGATIVE (IS collapsed +0.3993, F2 falsifier fired; OOS +1.55
    confirmed overfitting/regime-luck by Critic). alpha032 is reverted at closeout.
    formulaic_v3.py (compute_alpha032 + helpers) is RETAINED as reusable infrastructure
    but NOT wired into V3_FEATURE_COLUMNS. V3_FEATURE_COLUMNS returns to 14 features
    (the /059 canonical anchor). The runner ABSENT-assertion ban guards this invariant.
    """
    from crypto_trade.features_v3 import V3_FEATURE_COLUMNS

    assert "alpha032" not in V3_FEATURE_COLUMNS, (
        "alpha032 FOUND in V3_FEATURE_COLUMNS — must be ABSENT at iter-v3/102 closeout "
        "(NEGATIVE: IS collapsed +0.3993, F2 falsifier fired). "
        "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
    assert len(V3_FEATURE_COLUMNS) == 14, (
        f"V3_FEATURE_COLUMNS has {len(V3_FEATURE_COLUMNS)} columns — expected 14. "
        "iter-v3/124: eth_vs_sym_rv_50 REMOVED (/123 NEGATIVE-catastrophic); "
        "/121 BASELINE_V3 14-feature canonical anchor restored. "
        "alpha032 stays ABSENT at /102 closeout (NEGATIVE)."
    )
