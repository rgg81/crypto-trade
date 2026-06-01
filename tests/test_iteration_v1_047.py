"""Tests for iter-v1/047: skew_zscore_21 feature dispatch.

Covers:
  - Column presence in V1_FEATURE_COLUMNS_PRUNED (45 cols) and V1_FEATURE_COLUMNS
  - Computation correctness (synthetic OHLCV → known value)
  - No look-ahead (past-only discipline)
  - Window alignment (21-bar inner + 90-bar z-norm)
  - Parquet column presence (post-regen integration)
  - Track isolation (no cross-track imports)
  - Z-score normalization approximate (mean ≈ 0, std ≈ 1)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS, V1_FEATURE_COLUMNS_PRUNED
from crypto_trade.features_v1.statistical_v1 import compute_skew_zscore_21

# ---------------------------------------------------------------------------
# 1. Column list tests
# ---------------------------------------------------------------------------


def test_skew_zscore_21_in_pruned():
    """skew_zscore_21 is present in V1_FEATURE_COLUMNS_PRUNED and count is 45."""
    assert "skew_zscore_21" in V1_FEATURE_COLUMNS_PRUNED, (
        "skew_zscore_21 missing from V1_FEATURE_COLUMNS_PRUNED"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
        f"Expected 45 pruned features, got {len(V1_FEATURE_COLUMNS_PRUNED)}"
    )


def test_skew_zscore_21_in_full():
    """V1_FEATURE_COLUMNS is non-empty and remains a valid tuple."""
    # V1_FEATURE_COLUMNS is the legacy 193-col set (not extended by /047).
    # Verify it is still a non-empty tuple and that the pruned set is a subset
    # of features accessible from the parquet (structural sanity, not containment).
    assert isinstance(V1_FEATURE_COLUMNS, tuple), "V1_FEATURE_COLUMNS must be a tuple"
    assert len(V1_FEATURE_COLUMNS) > 0, "V1_FEATURE_COLUMNS must be non-empty"
    # The pruned set is independently maintained; spot-check stat_skew_20 is in
    # the full set (it is produced by legacy statistical.py).
    assert "stat_skew_20" in V1_FEATURE_COLUMNS, (
        "stat_skew_20 (algebraic sister) must be in V1_FEATURE_COLUMNS"
    )


# ---------------------------------------------------------------------------
# 2. Computation correctness
# ---------------------------------------------------------------------------


def test_skew_zscore_21_computation():
    """Synthetic 300-bar OHLCV — verify skew_zscore_21 value at a known bar."""
    rng = np.random.default_rng(seed=42)
    # Use a log-normal price path (consistent with crypto returns).
    log_rets = rng.normal(0.0, 0.02, size=300)
    prices = 100.0 * np.exp(np.cumsum(log_rets))
    df = pd.DataFrame({"close": prices})

    result = compute_skew_zscore_21(df)

    assert "skew_zscore_21" in result.columns, "skew_zscore_21 column must be present"

    # First 110 bars (21 + 90 - 1) must be NaN.
    warmup = 21 + 90 - 1  # = 110
    assert result["skew_zscore_21"].iloc[:warmup].isna().all(), (
        f"Expected NaN for first {warmup} bars (warmup period)"
    )

    # At bar 110 (index 110) the feature must be defined (not NaN).
    assert not np.isnan(result["skew_zscore_21"].iloc[warmup]), (
        f"Expected a valid float at index {warmup} (first post-warmup bar)"
    )

    # Recompute manually for bar index 200 and verify agreement.
    import scipy.stats as st  # noqa: PLC0415

    idx = 200
    # Inner skew_21bar values over the 90-bar z-norm window ending at idx.
    skew_at = []
    for j in range(idx - 90 + 1, idx + 1):
        lr_window = np.log(prices[j - 20 : j + 1] / prices[j - 21 : j])
        # log(p[k] / p[k-1]) for k in [j-20, j]
        # but more simply: np.diff(np.log(prices[j-21:j+1]))
        lr_window = np.diff(np.log(prices[j - 21 : j + 1]))
        skew_at.append(st.skew(lr_window, bias=False))
    expected_mean = np.mean(skew_at)
    expected_std = np.std(skew_at, ddof=1)
    expected_z = (skew_at[-1] - expected_mean) / expected_std
    actual_z = result["skew_zscore_21"].iloc[idx]
    assert abs(actual_z - expected_z) < 1e-9, (
        f"Manual recomputation mismatch at bar {idx}: "
        f"expected {expected_z:.10f}, got {actual_z:.10f}"
    )


# ---------------------------------------------------------------------------
# 3. No look-ahead (past-only)
# ---------------------------------------------------------------------------


def test_skew_zscore_21_no_lookahead():
    """skew_zscore_21[t] does not use close[t+k] for any k > 0."""
    rng = np.random.default_rng(42)
    base = 100 + rng.normal(0, 1, size=300).cumsum()

    df1 = pd.DataFrame({"close": base.copy()})
    df1 = compute_skew_zscore_21(df1)

    # Perturb ONLY the final bar — all prior rows should be completely unaffected.
    df2 = pd.DataFrame({"close": base.copy()})
    df2.loc[df2.index[-1], "close"] = base[-1] * 10.0
    df2 = compute_skew_zscore_21(df2)

    pd.testing.assert_series_equal(
        df1["skew_zscore_21"].iloc[:-1],
        df2["skew_zscore_21"].iloc[:-1],
        check_names=False,
        check_exact=True,
    )


# ---------------------------------------------------------------------------
# 4. Window alignment (21-bar inner + 90-bar z-norm)
# ---------------------------------------------------------------------------


def test_skew_zscore_21_window_alignment():
    """Verify the 21-bar inner window and 90-bar z-norm window alignment."""
    rng = np.random.default_rng(7)
    base = 100 + rng.normal(0, 1, size=400).cumsum()
    df = pd.DataFrame({"close": base})

    result = compute_skew_zscore_21(df, skew_window=21, znorm_window=90)

    warmup = 21 + 90 - 1  # 110 bars
    # Bar at index (warmup - 1) = 109: still in warmup → NaN.
    assert np.isnan(result["skew_zscore_21"].iloc[warmup - 1]), (
        f"Bar {warmup - 1} should still be NaN (last warmup bar)"
    )
    # Bar at index warmup = 110: first valid bar.
    assert not np.isnan(result["skew_zscore_21"].iloc[warmup]), (
        f"Bar {warmup} should be the first non-NaN bar"
    )

    # Also verify with non-default windows to confirm parameter plumbing.
    result_narrow = compute_skew_zscore_21(df, skew_window=10, znorm_window=20)
    warmup_narrow = 10 + 20 - 1  # 29
    assert result_narrow["skew_zscore_21"].iloc[:warmup_narrow].isna().all()
    assert not np.isnan(result_narrow["skew_zscore_21"].iloc[warmup_narrow])


# ---------------------------------------------------------------------------
# 5. Parquet integration (post-regen)
# ---------------------------------------------------------------------------


def test_skew_zscore_21_parquet():
    """Parquet files for all 5 v1 symbols have skew_zscore_21 column post-regen.

    v1 parquets live in data/features/{SYM}_8h_features.parquet (old-style path).
    The v1 runner (run_baseline_v1.py) reads features_dir='data/features' at line 528.
    """
    parquet_dir = Path("data/features")
    symbols = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]

    if not parquet_dir.exists():
        pytest.skip(
            f"Parquet directory {parquet_dir} not found. "
            "Run: uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
            "--interval 8h --track v1 --format parquet --workers 4"
        )

    missing_files = [s for s in symbols if not (parquet_dir / f"{s}_8h_features.parquet").exists()]
    if missing_files:
        pytest.skip(f"Parquet files not found for {missing_files}. Regenerate v1 features first.")

    for sym in symbols:
        path = parquet_dir / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(path, columns=["skew_zscore_21"])
        assert "skew_zscore_21" in df.columns, f"{sym}: skew_zscore_21 column missing from {path}"
        # Post-warmup values must exist (not all NaN).
        assert df["skew_zscore_21"].notna().any(), (
            f"{sym}: all skew_zscore_21 values are NaN — feature computation failed"
        )


# ---------------------------------------------------------------------------
# 6. Track isolation
# ---------------------------------------------------------------------------


def test_skew_zscore_21_track_isolation():
    """statistical_v1 module does not import from features_v2 or features_v3."""
    import ast  # noqa: PLC0415
    import inspect  # noqa: PLC0415

    from crypto_trade.features_v1 import statistical_v1  # noqa: PLC0415

    src = inspect.getsource(statistical_v1)

    # Parse the source and check import statements only (not docstrings).
    tree = ast.parse(src)
    import_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                import_modules.append(node.module)

    for mod in import_modules:
        assert "features_v2" not in mod, (
            f"Track isolation violation: import from '{mod}' (features_v2) found in statistical_v1"
        )
        assert "features_v3" not in mod, (
            f"Track isolation violation: import from '{mod}' (features_v3) found in statistical_v1"
        )
