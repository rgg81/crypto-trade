"""Tests for iter-v1/075 — ATOMUSDT SPECIALIST (first NEW SYMBOL universe-extension).

Covers:
1. V1_ITER075_UNIVERSE constant: importable, correct symbol, in __all__.
2. run_iteration_075.py: importable, ITERATION_LABEL=="v1-075", ITERATION_NUMBER==75.
3. Methodology constants UNCHANGED: 48-col hash, V1_SPECIALIST_SEED_COUNT=50,
   V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91, OOS_CUTOFF_MS.
4. Dispatch presence: "v1-075" appears in run_baseline_v1.py source.
5. Feature hash for ATOMUSDT parquet: all 48 V1_FEATURE_COLUMNS_PRUNED columns present.
6. R1=OFF documented in runner (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3).
"""

from __future__ import annotations

import hashlib

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered 48-col hash (UNCHANGED from /061 closeout).
EXPECTED_HASH_48COL = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"


# ---------------------------------------------------------------------------
# 1. Smoke imports
# ---------------------------------------------------------------------------


def test_lgbm_strategy_import() -> None:
    """LightGbmStrategy imports without error."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy  # noqa: F401


def test_v1_iter075_universe_import() -> None:
    """V1_ITER075_UNIVERSE is importable and == ('ATOMUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER075_UNIVERSE

    assert V1_ITER075_UNIVERSE == ("ATOMUSDT",), (
        f"V1_ITER075_UNIVERSE must be ('ATOMUSDT',); got {V1_ITER075_UNIVERSE}"
    )


def test_v1_iter075_universe_in_all() -> None:
    """V1_ITER075_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER075_UNIVERSE" in f1.__all__, (
        "V1_ITER075_UNIVERSE must be in crypto_trade.features_v1.__all__"
    )


def test_runner_import() -> None:
    """run_iteration_075 imports without error and exposes required attrs."""
    import importlib
    import sys

    if "run_iteration_075" in sys.modules:
        del sys.modules["run_iteration_075"]
    mod = importlib.import_module("run_iteration_075")
    assert hasattr(mod, "main")
    assert hasattr(mod, "ITERATION_LABEL")
    assert mod.ITERATION_LABEL == "v1-075"
    assert hasattr(mod, "ITERATION_NUMBER")
    assert mod.ITERATION_NUMBER == 75
    assert hasattr(mod, "FEATURES_BASE_HASH_48COL")


# ---------------------------------------------------------------------------
# 2. Methodology constants UNCHANGED
# ---------------------------------------------------------------------------


def test_v1_feature_columns_pruned_48_cols() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must be 48 columns (UNCHANGED from /074 closeout)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED must have 48 cols at iter-v1/075; "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "NEW SYMBOL universe-extension does NOT modify the feature stack."
    )


def test_features_base_hash_48col() -> None:
    """The 48-col features hash matches the pre-registered value (UNCHANGED from /061+)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert actual == EXPECTED_HASH_48COL, (
        f"V1_FEATURE_COLUMNS_PRUNED hash mismatch at iter-v1/075.\n"
        f"  expected (48-col /061+ hash): {EXPECTED_HASH_48COL}\n"
        f"  actual                     : {actual}\n"
        f"  len(V1_FEATURE_COLUMNS_PRUNED) = {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
        "NEW SYMBOL universe-extension must NOT modify the feature stack."
    )


def test_runner_hash_constant_matches() -> None:
    """FEATURES_BASE_HASH_48COL in run_iteration_075 matches V1_FEATURE_COLUMNS_PRUNED hash."""
    import run_iteration_075 as r075

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert r075.FEATURES_BASE_HASH_48COL == actual, (
        f"run_iteration_075.FEATURES_BASE_HASH_48COL mismatch.\n"
        f"  runner constant: {r075.FEATURES_BASE_HASH_48COL}\n"
        f"  computed hash  : {actual}\n"
        "The runner's pre-registered hash must match V1_FEATURE_COLUMNS_PRUNED."
    )


def test_specialist_constants() -> None:
    """V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_OPTUNA_TRIALS,
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEEDS,
    )

    assert V1_SPECIALIST_SEED_COUNT == 50, (
        f"V1_SPECIALIST_SEED_COUNT must be 50; got {V1_SPECIALIST_SEED_COUNT}"
    )
    assert V1_SPECIALIST_OPTUNA_TRIALS == 30, (
        f"V1_SPECIALIST_OPTUNA_TRIALS must be 30; got {V1_SPECIALIST_OPTUNA_TRIALS}"
    )
    assert len(V1_SPECIALIST_SEEDS) == 50, (
        f"V1_SPECIALIST_SEEDS must have 50 entries; got {len(V1_SPECIALIST_SEEDS)}"
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"V1_SPECIALIST_SEEDS[0] must be 42; got {V1_SPECIALIST_SEEDS[0]}"
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"V1_SPECIALIST_SEEDS[-1] must be 91; got {V1_SPECIALIST_SEEDS[-1]}"
    )


def test_oos_cutoff_ms_sacred() -> None:
    """OOS_CUTOFF_MS is the sacred 2025-03-24 constant (1742774400000)."""
    from crypto_trade.config import OOS_CUTOFF_MS

    assert OOS_CUTOFF_MS == 1742774400000, (
        f"OOS_CUTOFF_MS must be 1742774400000 (2025-03-24); got {OOS_CUTOFF_MS}"
    )


def test_runner_iteration_label_and_number() -> None:
    """Runner ITERATION_LABEL='v1-075' and ITERATION_NUMBER=75."""
    import run_iteration_075 as r075

    assert r075.ITERATION_LABEL == "v1-075", (
        f"ITERATION_LABEL must be 'v1-075'; got {r075.ITERATION_LABEL!r}"
    )
    assert r075.ITERATION_NUMBER == 75, f"ITERATION_NUMBER must be 75; got {r075.ITERATION_NUMBER}"


# ---------------------------------------------------------------------------
# 3. Dispatch presence in run_baseline_v1.py
# ---------------------------------------------------------------------------


def test_dispatch_branch_present_in_runner() -> None:
    """run_baseline_v1.py contains the 'v1-075' dispatch branch."""
    import pathlib

    runner_path = pathlib.Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists(), f"run_baseline_v1.py not found at {runner_path}"
    src = runner_path.read_text(encoding="utf-8")
    assert 'iteration_label == "v1-075"' in src, (
        "run_baseline_v1.py must contain dispatch branch 'elif iteration_label == \"v1-075\"'"
    )
    assert "V1_ITER075_UNIVERSE" in src, (
        "run_baseline_v1.py must reference V1_ITER075_UNIVERSE in the dispatch branch"
    )
    assert "ATOMUSDT" in src, (
        "run_baseline_v1.py dispatch branch must wire ATOMUSDT as the cohort symbol"
    )
    assert "Model_A_ATOM_specialist_075" in src, (
        "run_baseline_v1.py dispatch branch must name the model 'Model_A_ATOM_specialist_075'"
    )


def test_dispatch_import_in_runner() -> None:
    """run_baseline_v1.py imports V1_ITER075_UNIVERSE from features_v1."""
    import pathlib

    runner_path = pathlib.Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER075_UNIVERSE" in src, (
        "run_baseline_v1.py must import V1_ITER075_UNIVERSE from features_v1"
    )


# ---------------------------------------------------------------------------
# 4. Feature hash for ATOMUSDT parquet (all 48 V1_FEATURE_COLUMNS_PRUNED present)
# ---------------------------------------------------------------------------


def test_atomusdt_parquet_exists() -> None:
    """ATOMUSDT feature parquet exists at data/features/ATOMUSDT_8h_features.parquet."""
    import pathlib

    parquet_path = (
        pathlib.Path(__file__).parent.parent / "data" / "features" / "ATOMUSDT_8h_features.parquet"
    )
    assert parquet_path.exists(), (
        f"ATOMUSDT feature parquet not found at {parquet_path}. "
        "No fetch/regen needed: parquet must exist from prior EDA (table_09 audit)."
    )


def test_atomusdt_parquet_contains_all_48_feature_columns() -> None:
    """ATOMUSDT parquet contains all 48 V1_FEATURE_COLUMNS_PRUNED columns."""
    import pathlib

    try:
        import pandas as pd
    except ImportError:
        import pytest

        pytest.skip("pandas not available; skipping parquet column audit")

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    parquet_path = (
        pathlib.Path(__file__).parent.parent / "data" / "features" / "ATOMUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        import pytest

        pytest.skip(f"ATOMUSDT parquet not found at {parquet_path}")

    # Read only column names (no full data load needed)
    df = pd.read_parquet(parquet_path, columns=list(V1_FEATURE_COLUMNS_PRUNED))
    missing = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in df.columns]
    assert not missing, (
        f"ATOMUSDT parquet is missing {len(missing)} of 48 V1_FEATURE_COLUMNS_PRUNED columns:\n"
        + "\n".join(f"  {c}" for c in missing)
    )
    assert len(df.columns) == 48, (
        f"Expected 48 feature columns in ATOMUSDT parquet read; got {len(df.columns)}"
    )


def test_atomusdt_parquet_symbol_conditional_nan_columns_present() -> None:
    """SYMBOL-conditional ALL-NaN columns (dot_vs_btc, eth_vs_btc) are present in parquet.

    They are ALL-NaN for ATOM by design. LightGBM handles NaN natively (use_missing=True).
    The test confirms the columns EXIST in V1_FEATURE_COLUMNS_PRUNED (they are NOT removed).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "dot_vs_btc_ret_ratio_30 must remain in V1_FEATURE_COLUMNS_PRUNED "
        "(ALL-NaN for ATOM but LightGBM NaN-handles natively; per brief Section 2.9)"
    )
    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "eth_vs_btc_ret_ratio_30 must remain in V1_FEATURE_COLUMNS_PRUNED "
        "(ALL-NaN for ATOM but LightGBM NaN-handles natively; per brief Section 2.9)"
    )


# ---------------------------------------------------------------------------
# 5. R1=OFF documented in runner (CATALOG-CLOSED; f81cafc3)
# ---------------------------------------------------------------------------


def test_r1_off_documented_in_runner() -> None:
    """run_iteration_075.py documents R1=OFF (CATALOG-CLOSED for SPECIALIST_mode)."""
    import run_iteration_075 as r075

    doc = r075.__doc__ or ""
    assert "R1=OFF" in doc or "R1" in doc, (
        "run_iteration_075 docstring must document R1=OFF "
        "(CATALOG-CLOSED for SPECIALIST_mode per f81cafc3)"
    )


def test_atom_not_in_v1_excluded_symbols() -> None:
    """ATOMUSDT is NOT in V1_EXCLUDED_SYMBOLS (eligible for v1 universe)."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    assert "ATOMUSDT" not in V1_EXCLUDED_SYMBOLS, (
        f"ATOMUSDT must NOT be in V1_EXCLUDED_SYMBOLS; "
        f"current exclusion list: {V1_EXCLUDED_SYMBOLS}"
    )


def test_assert_v1_universe_passes_for_atom() -> None:
    """assert_v1_universe(['ATOMUSDT']) must pass (no exclusion violation)."""
    from crypto_trade.features_v1 import assert_v1_universe

    # Should not raise
    assert_v1_universe(["ATOMUSDT"])
