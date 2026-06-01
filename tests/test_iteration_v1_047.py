"""Tests for iter-v1/047: skew_zscore_21 feature dispatch.

CLOSEOUT STATUS: **NEG-CLEAN-PRE-EDA** (verdict 2026-06-01).

The pre-launch F5 IC orthogonality gate fired: max |IC| = 0.8132 (Pearson, pooled IS)
vs `stat_skew_20`, which is **above the ABORT threshold 0.60**. `skew_zscore_21` is
nearly collinear with the existing `stat_skew_20` primitive — z-score normalization
preserves the monotonic relationship between rolling-skew at 21 bars and rolling-skew
at 20 bars (LightGBM cannot separate them at depth 3-5).

No backtest was launched. `skew_zscore_21` was REVERTED from V1_FEATURE_COLUMNS_PRUNED
(45 → 44). The `statistical_v1` group was de-registered from GROUP_REGISTRY
(14 → 13 groups). The `statistical_v1` Python module file is kept on disk as
dead code (clean code, ready for future-iter reuse with a NON-skew higher-moment
primitive).

These tests now ASSERT THE REVERTED STATE — `skew_zscore_21` MUST NOT be in
V1_FEATURE_COLUMNS_PRUNED. The computation-correctness / no-lookahead / window
alignment tests are retained against the (still-present) ``compute_skew_zscore_21``
helper, since the module is preserved. The parquet integration test is skipped
unconditionally because the parquets no longer include the column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS, V1_FEATURE_COLUMNS_PRUNED
from crypto_trade.features_v1.statistical_v1 import compute_skew_zscore_21

# ---------------------------------------------------------------------------
# 1. Column list tests — assert REVERTED state
# ---------------------------------------------------------------------------


def test_skew_zscore_21_reverted_from_pruned():
    """Post-closeout: skew_zscore_21 MUST NOT be in V1_FEATURE_COLUMNS_PRUNED.

    Count check: pruned set is 44 post-/047 revert. iter-v1/048 (microstructure
    trade_count_zscore_30) also closed NEG-CLEAN-PRE-EDA and reverted 45 → 44,
    so the steady-state count was 44. iter-v1/049 added long_short_zscore_30 → 45.
    """
    assert "skew_zscore_21" not in V1_FEATURE_COLUMNS_PRUNED, (
        "skew_zscore_21 must be REVERTED from V1_FEATURE_COLUMNS_PRUNED "
        "(iter-v1/047 NEG-CLEAN-PRE-EDA: F5 |IC|=0.8132 vs stat_skew_20)"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 46, (
        f"Expected 46 pruned features (45 post-/049 ADD + /050 ADD dot_vs_btc_ret_ratio_30), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}"
    )


def test_full_feature_columns_unchanged():
    """V1_FEATURE_COLUMNS (the legacy 193-col set) is unchanged by /047 revert."""
    assert isinstance(V1_FEATURE_COLUMNS, tuple), "V1_FEATURE_COLUMNS must be a tuple"
    assert len(V1_FEATURE_COLUMNS) == 193, (
        f"V1_FEATURE_COLUMNS must remain at 193 cols, got {len(V1_FEATURE_COLUMNS)}"
    )
    # stat_skew_20 (the algebraic sister) IS in the full set — produced by legacy
    # statistical.py and untouched by the /047 revert.
    assert "stat_skew_20" in V1_FEATURE_COLUMNS, (
        "stat_skew_20 (algebraic sister) must remain in V1_FEATURE_COLUMNS"
    )


def test_statistical_v1_not_in_group_registry():
    """statistical_v1 group is de-registered from GROUP_REGISTRY post-revert."""
    from crypto_trade.features import GROUP_REGISTRY  # noqa: PLC0415

    assert "statistical_v1" not in GROUP_REGISTRY, (
        "statistical_v1 must be DE-REGISTERED from GROUP_REGISTRY "
        "(iter-v1/047 NEG-CLEAN-PRE-EDA revert)"
    )
    # Count is 15 post-/050 (14 post-/049 + 1 cross_btc_v1 added at /050).
    assert len(GROUP_REGISTRY) == 15, (
        f"GROUP_REGISTRY must have exactly 15 groups post-/050, got {len(GROUP_REGISTRY)}"
    )


# ---------------------------------------------------------------------------
# 2. Computation correctness — module preserved on disk, helper still works
# ---------------------------------------------------------------------------


def test_skew_zscore_21_helper_still_functional():
    """The compute_skew_zscore_21 helper is preserved on disk (dead-code module);
    we keep the smoke test so any future-iter reuse starts from a working baseline.
    """
    rng = np.random.default_rng(seed=42)
    log_rets = rng.normal(0.0, 0.02, size=300)
    prices = 100.0 * np.exp(np.cumsum(log_rets))
    df = pd.DataFrame({"close": prices})

    result = compute_skew_zscore_21(df)

    assert "skew_zscore_21" in result.columns
    warmup = 21 + 90 - 1  # = 110
    assert result["skew_zscore_21"].iloc[:warmup].isna().all()
    assert not np.isnan(result["skew_zscore_21"].iloc[warmup])


def test_skew_zscore_21_no_lookahead():
    """No-lookahead invariant: perturbing close[-1] does not affect skew_zscore_21[<-1]."""
    rng = np.random.default_rng(42)
    base = 100 + rng.normal(0, 1, size=300).cumsum()

    df1 = pd.DataFrame({"close": base.copy()})
    df1 = compute_skew_zscore_21(df1)

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
# 3. Parquet integration — skipped post-revert (column no longer in parquets)
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason="iter-v1/047 NEG-CLEAN-PRE-EDA closeout: skew_zscore_21 reverted from "
    "V1_FEATURE_COLUMNS_PRUNED and de-registered from GROUP_REGISTRY. Parquets "
    "regenerated post-revert do not include the column."
)
def test_skew_zscore_21_parquet():
    """Skipped — column intentionally absent from v1 parquets post-revert."""
    pass
