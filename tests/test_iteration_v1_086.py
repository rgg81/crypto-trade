"""Tests for iter-v1/086 — TRBUSDT SPECIALIST (STOCK 48-col stack, NO new features).

Covers:
1. V1_ITER086_UNIVERSE constant: importable, correct symbol, in __all__.
2. Global V1_FEATURE_COLUMNS_PRUNED stays at 48 (unchanged — no new features).
3. run_iteration_086.py: importable, ITERATION_LABEL=="v1-086", ITERATION_NUMBER==86.
4. Methodology constants: V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30,
   seeds 42..91, OOS_CUTOFF_MS.
5. Feature hash: 48-col PRUNED hash prefix == b81176f893826500.
6. Dispatch presence: "v1-086" appears in run_baseline_v1.py source.
7. TRBUSDT parquet: has all 48 V1_FEATURE_COLUMNS_PRUNED columns.
8. Zero new features: V1_ITER086 does NOT introduce any new column constant.
9. Track isolation: no features_v2/features_v3 imports leak.
10. Symbol eligibility: TRBUSDT not in V1_EXCLUDED_SYMBOLS; assert_v1_universe passes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. Universe constant
# ---------------------------------------------------------------------------


def test_v1_iter086_universe_import() -> None:
    """V1_ITER086_UNIVERSE is importable and == ('TRBUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER086_UNIVERSE

    assert V1_ITER086_UNIVERSE == ("TRBUSDT",), (
        f"V1_ITER086_UNIVERSE must be ('TRBUSDT',); got {V1_ITER086_UNIVERSE}"
    )


def test_v1_iter086_universe_in_all() -> None:
    """V1_ITER086_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER086_UNIVERSE" in f1.__all__


# ---------------------------------------------------------------------------
# 2. Global PRUNED stays at 48 — NO new features
# ---------------------------------------------------------------------------


def test_global_pruned_unchanged_at_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED is exactly 48 (unchanged; iter-v1/086 adds ZERO features)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"CRITICAL: V1_FEATURE_COLUMNS_PRUNED must be 48 (unchanged at iter-v1/086); "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "iter-v1/086 adds ZERO new features — the edge is in the stock 48-col stack."
    )


def test_no_v1_iter086_feature_columns_constant() -> None:
    """iter-v1/086 introduces NO V1_ITER086_FEATURE_COLUMNS constant (zero new features)."""
    import crypto_trade.features_v1 as f1

    assert not hasattr(f1, "V1_ITER086_FEATURE_COLUMNS"), (
        "V1_ITER086_FEATURE_COLUMNS must NOT exist — iter-v1/086 adds zero new features. "
        "The global V1_FEATURE_COLUMNS_PRUNED (48 cols) is the feature set."
    )


# ---------------------------------------------------------------------------
# 3. Feature hash
# ---------------------------------------------------------------------------


def test_features_hash_48col() -> None:
    """48-col PRUNED feature hash matches pre-registered b81176f893826500."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert actual_hash[:16] == "b81176f893826500", (
        f"48-col PRUNED feature hash prefix mismatch. "
        f"Expected: b81176f893826500, Got: {actual_hash[:16]}. "
        "V1_FEATURE_COLUMNS_PRUNED has changed from the pre-registered 48-col STOCK set."
    )


# ---------------------------------------------------------------------------
# 4. Runner constants
# ---------------------------------------------------------------------------


def test_runner_import() -> None:
    """run_iteration_086 imports without error and has ITERATION_LABEL='v1-086'."""
    import importlib
    import sys

    if "run_iteration_086" in sys.modules:
        del sys.modules["run_iteration_086"]
    mod = importlib.import_module("run_iteration_086")
    assert hasattr(mod, "main")
    assert mod.ITERATION_LABEL == "v1-086"
    assert mod.ITERATION_NUMBER == 86
    assert hasattr(mod, "FEATURES_BASE_HASH_48COL")


def test_runner_hash_constant() -> None:
    """FEATURES_BASE_HASH_48COL in runner matches computed hash of V1_FEATURE_COLUMNS_PRUNED."""
    import run_iteration_086 as r086

    assert r086.FEATURES_BASE_HASH_48COL == "b81176f893826500", (
        f"Runner FEATURES_BASE_HASH_48COL mismatch: {r086.FEATURES_BASE_HASH_48COL!r}"
    )


def test_specialist_constants() -> None:
    """V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_OPTUNA_TRIALS,
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEEDS,
    )

    assert V1_SPECIALIST_SEED_COUNT == 50
    assert V1_SPECIALIST_OPTUNA_TRIALS == 30
    assert len(V1_SPECIALIST_SEEDS) == 50
    assert V1_SPECIALIST_SEEDS[0] == 42
    assert V1_SPECIALIST_SEEDS[-1] == 91


def test_oos_cutoff_ms_sacred() -> None:
    """OOS_CUTOFF_MS must be 1742774400000 (2025-03-24, unchanged)."""
    from crypto_trade.config import OOS_CUTOFF_MS

    assert OOS_CUTOFF_MS == 1742774400000


# ---------------------------------------------------------------------------
# 5. Dispatch in run_baseline_v1.py
# ---------------------------------------------------------------------------


def test_dispatch_branch_present() -> None:
    """run_baseline_v1.py contains 'v1-086' dispatch with correct model name."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists()
    src = runner_path.read_text(encoding="utf-8")
    assert 'iteration_label == "v1-086"' in src
    assert "V1_ITER086_UNIVERSE" in src
    assert "TRBUSDT" in src
    assert "Model_A_TRB_specialist_086" in src


def test_dispatch_import_in_runner() -> None:
    """run_baseline_v1.py imports V1_ITER086_UNIVERSE."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER086_UNIVERSE" in src


def test_dispatch_no_feature_override() -> None:
    """run_baseline_v1.py v1-086 dispatch does NOT override active_feature_columns with a local
    feature set (no V1_ITER086_FEATURE_COLUMNS override in the dispatch block)."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    # The /086 block should NOT reference V1_ITER086_FEATURE_COLUMNS
    assert "V1_ITER086_FEATURE_COLUMNS" not in src, (
        "run_baseline_v1.py must NOT reference V1_ITER086_FEATURE_COLUMNS — "
        "iter-v1/086 uses the global 48-col PRUNED set unchanged."
    )


# ---------------------------------------------------------------------------
# 6. TRBUSDT parquet audit
# ---------------------------------------------------------------------------


def test_trbusdt_parquet_has_all_48_pruned_columns() -> None:
    """TRBUSDT parquet contains all 48 V1_FEATURE_COLUMNS_PRUNED columns."""
    import pandas as pd

    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "TRBUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"TRBUSDT parquet not found at {parquet_path}")

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    df = pd.read_parquet(parquet_path, columns=list(V1_FEATURE_COLUMNS_PRUNED))
    missing = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in df.columns]
    assert not missing, (
        f"TRBUSDT parquet is missing {len(missing)} of 48 V1_FEATURE_COLUMNS_PRUNED:\n"
        + "\n".join(f"  {c}" for c in missing)
    )
    assert len(df.columns) == 48


# ---------------------------------------------------------------------------
# 7. Symbol eligibility
# ---------------------------------------------------------------------------


def test_trb_not_in_v1_excluded_symbols() -> None:
    """TRBUSDT is NOT in V1_EXCLUDED_SYMBOLS."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    assert "TRBUSDT" not in V1_EXCLUDED_SYMBOLS, (
        "TRBUSDT must not be in V1_EXCLUDED_SYMBOLS — it is the iter-v1/086 cohort."
    )


def test_trb_not_in_v1_baseline_universe() -> None:
    """TRBUSDT is NOT in V1_BASELINE_UNIVERSE (it is a fresh-mine candidate, not an incumbent)."""
    from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE

    assert "TRBUSDT" not in V1_BASELINE_UNIVERSE, (
        "TRBUSDT must not be in V1_BASELINE_UNIVERSE — it is a fresh-mine SPECIALIST candidate."
    )


def test_assert_v1_universe_passes_for_trb() -> None:
    """assert_v1_universe(['TRBUSDT']) must pass."""
    from crypto_trade.features_v1 import assert_v1_universe

    assert_v1_universe(["TRBUSDT"])


# ---------------------------------------------------------------------------
# 8. Track isolation
# ---------------------------------------------------------------------------


def test_run_iteration_086_no_v2_v3_imports() -> None:
    """run_iteration_086.py has no features_v2/v3 import statements (track isolation)."""
    module_path = Path(__file__).parent.parent / "run_iteration_086.py"
    src = module_path.read_text(encoding="utf-8")
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text
    assert "from crypto_trade.features_v3" not in import_text
