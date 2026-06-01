"""Tests for iter-v1/048: trade_count_zscore_30 feature dispatch.

CLOSEOUT STATUS: **NEG-CLEAN-PRE-EDA** (verdict 2026-06-01).

The pre-launch F5 IC orthogonality gate fired: max |IC| = 0.9063 (Pearson, pooled IS)
vs ``vol_volume_rel_20``, which is **above the ABORT threshold 0.60**. The "UNUSED
kline primitive" defense post-/047 is REFUTED — ``number_of_trades`` is empirically
tied to the volume cluster despite the theoretical primitive-orthogonality argument
(rank-1 ``vol_volume_rel_20`` 0.9063, rank-2 ``vol_range_spike_24`` 0.7908, rank-3
``vol_range_spike_72`` 0.7322 — three concurrent ABORT-triggers).

No backtest was launched. ``trade_count_zscore_30`` was REVERTED from
V1_FEATURE_COLUMNS_PRUNED (45 → 44). The ``microstructure_v1`` group was
de-registered from GROUP_REGISTRY (14 → 13 groups). The ``microstructure_v1``
Python module file is kept on disk as dead code (clean code, ready for future-iter
reuse with a non-kline microstructure primitive — funding-rate momentum,
OI-velocity, basis delta).

These tests now ASSERT THE REVERTED STATE — ``trade_count_zscore_30`` MUST NOT be
in V1_FEATURE_COLUMNS_PRUNED. The computation-correctness / no-lookahead / window
alignment tests are retained against the (still-present)
``compute_trade_count_zscore_30`` helper, since the module is preserved. The
parquet integration test is skipped unconditionally because the parquets no longer
include the column.
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import (
    V1_FEATURE_COLUMNS,
    V1_FEATURE_COLUMNS_PRUNED,
    microstructure_v1,
)
from crypto_trade.features_v1.microstructure_v1 import compute_trade_count_zscore_30

# ---------------------------------------------------------------------------
# 1. Column list tests — assert REVERTED state
# ---------------------------------------------------------------------------


def test_trade_count_zscore_30_reverted_from_pruned():
    """Post-closeout: trade_count_zscore_30 MUST NOT be in V1_FEATURE_COLUMNS_PRUNED."""
    assert "trade_count_zscore_30" not in V1_FEATURE_COLUMNS_PRUNED, (
        "trade_count_zscore_30 must be REVERTED from V1_FEATURE_COLUMNS_PRUNED "
        "(iter-v1/048 NEG-CLEAN-PRE-EDA: F5 |IC|=0.9063 vs vol_volume_rel_20)"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 49, (
        f"Expected 49 pruned features (post iter-v1/058 ADD btc_oi_delta_5_z30), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}"
    )


def test_full_feature_columns_unchanged():
    """V1_FEATURE_COLUMNS (the legacy 193-col set) is unchanged by /048 revert."""
    assert isinstance(V1_FEATURE_COLUMNS, tuple), "V1_FEATURE_COLUMNS must be a tuple"
    assert len(V1_FEATURE_COLUMNS) == 193, (
        f"V1_FEATURE_COLUMNS must remain at 193 cols, got {len(V1_FEATURE_COLUMNS)}"
    )
    assert "trade_count_zscore_30" not in V1_FEATURE_COLUMNS, (
        "trade_count_zscore_30 must NOT appear in V1_FEATURE_COLUMNS (was never in BASELINE_FEATURE_COLUMNS)"  # noqa: E501
    )
    # vol_volume_rel_20 (the empirical volume-cluster anchor for F5 failure) IS in
    # the full set — produced by legacy volume.py and untouched by the /048 revert.
    assert "vol_volume_rel_20" in V1_FEATURE_COLUMNS, (
        "vol_volume_rel_20 (rank-1 F5 collinearity anchor) must remain in V1_FEATURE_COLUMNS"
    )


def test_microstructure_v1_not_in_group_registry():
    """microstructure_v1 group is de-registered from GROUP_REGISTRY post-revert."""
    from crypto_trade.features import GROUP_REGISTRY  # noqa: PLC0415

    assert "microstructure_v1" not in GROUP_REGISTRY, (
        "microstructure_v1 must be DE-REGISTERED from GROUP_REGISTRY "
        "(iter-v1/048 NEG-CLEAN-PRE-EDA revert)"
    )
    # Count is 15 post-/050 (14 post-/049 + 1 cross_btc_v1 added at /050).
    assert len(GROUP_REGISTRY) == 15, (
        f"GROUP_REGISTRY must have exactly 15 groups post-/050, got {len(GROUP_REGISTRY)}"
    )


# ---------------------------------------------------------------------------
# 2. Computation correctness — module preserved on disk, helper still works
# ---------------------------------------------------------------------------


def test_trade_count_zscore_30_helper_still_functional():
    """The compute_trade_count_zscore_30 helper is preserved on disk (dead-code module);
    we keep the smoke test so any future-iter reuse starts from a working baseline.
    """
    rng = np.random.default_rng(seed=42)
    base = rng.integers(10_000, 100_000, size=300).astype(float)
    df = pd.DataFrame({"trades": base})

    result = compute_trade_count_zscore_30(df)

    assert "trade_count_zscore_30" in result.columns
    # window=30, min_periods=30 => first 29 bars NaN
    assert result["trade_count_zscore_30"].iloc[:29].isna().all()
    assert not np.isnan(result["trade_count_zscore_30"].iloc[40])


def test_trade_count_zscore_30_no_lookahead():
    """No-lookahead invariant: perturbing trades[-1] does not affect z-score[<-1]."""
    rng = np.random.default_rng(42)
    base = rng.integers(10_000, 100_000, size=300).astype(float)

    df1 = pd.DataFrame({"trades": base.copy()})
    df1 = compute_trade_count_zscore_30(df1)

    df2 = pd.DataFrame({"trades": base.copy()})
    df2.loc[df2.index[-1], "trades"] = base[-1] * 100
    df2 = compute_trade_count_zscore_30(df2)

    pd.testing.assert_series_equal(
        df1["trade_count_zscore_30"].iloc[:-1],
        df2["trade_count_zscore_30"].iloc[:-1],
        check_names=False,
    )


def test_track_isolation():
    """microstructure_v1 must not import from features_v2 or features_v3.

    Checks actual import statements via AST, not docstring mentions.
    """
    import ast  # noqa: PLC0415

    src = inspect.getsource(microstructure_v1)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "features_v2" not in alias.name, (
                    f"microstructure_v1 imports from features_v2: {alias.name}"
                )
                assert "features_v3" not in alias.name, (
                    f"microstructure_v1 imports from features_v3: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "features_v2" not in module, (
                f"microstructure_v1 imports from features_v2: {module}"
            )
            assert "features_v3" not in module, (
                f"microstructure_v1 imports from features_v3: {module}"
            )


# ---------------------------------------------------------------------------
# 3. Parquet integration — skipped post-revert (column no longer in parquets)
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason="iter-v1/048 NEG-CLEAN-PRE-EDA closeout: trade_count_zscore_30 reverted from "
    "V1_FEATURE_COLUMNS_PRUNED and microstructure_v1 de-registered from GROUP_REGISTRY. "
    "Parquets regenerated post-revert do not include the column."
)
def test_trade_count_zscore_30_parquet():
    """Skipped — column intentionally absent from v1 parquets post-revert."""
    pass
