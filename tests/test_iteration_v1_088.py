"""Tests for iter-v1/088 — XRPUSDT SPECIALIST (STOCK 48-col stack, fail-fast gate).

Mirrors test_iteration_v1_086.py (TRB) / test_iteration_v1_087.py structure with
XRP-specific assertions and cross-track-overlap verification.

Covers:
1. V1_ITER088_UNIVERSE constant: importable, correct symbol, in __all__.
2. Global V1_FEATURE_COLUMNS_PRUNED stays at 48 (unchanged — no new features).
3. run_iteration_088.py: importable, ITERATION_LABEL=="v1-088", ITERATION_NUMBER==88.
4. Methodology constants: V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30,
   seeds 42..91, OOS_CUTOFF_MS.
5. Feature hash: 48-col PRUNED hash prefix == b81176f893826500.
6. Dispatch presence: "v1-088" dispatches XRPUSDT in run_baseline_v1.py source.
7. Zero new features: V1_ITER088 does NOT introduce any new column constant.
8. Track isolation: no features_v2/features_v3 imports leak.
9. Symbol eligibility: XRPUSDT not in V1_EXCLUDED_SYMBOLS; assert_v1_universe passes.
10. Cross-track overlap flag: V1_EXCLUDED_SYMBOLS comment or __init__ documents the flag.
11. XRPUSDT parquet: has all 48 V1_FEATURE_COLUMNS_PRUNED columns (if parquet exists).
12. Fail-fast infra unchanged: FAIL_FAST_IS_YEARS == 2.0; fail-fast code not re-introduced.
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


def test_v1_iter088_universe_import() -> None:
    """V1_ITER088_UNIVERSE is importable and == ('XRPUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER088_UNIVERSE

    assert V1_ITER088_UNIVERSE == ("XRPUSDT",), (
        f"V1_ITER088_UNIVERSE must be ('XRPUSDT',); got {V1_ITER088_UNIVERSE}"
    )


def test_v1_iter088_universe_in_all() -> None:
    """V1_ITER088_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER088_UNIVERSE" in f1.__all__


# ---------------------------------------------------------------------------
# 2. Global PRUNED stays at 48 — NO new features
# ---------------------------------------------------------------------------


def test_global_pruned_unchanged_at_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED is exactly 48 (unchanged; iter-v1/088 adds ZERO features)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"CRITICAL: V1_FEATURE_COLUMNS_PRUNED must be 48 (unchanged at iter-v1/088); "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "iter-v1/088 adds ZERO new features — one-variable discipline (universe axis only)."
    )


def test_no_v1_iter088_feature_columns_constant() -> None:
    """iter-v1/088 introduces NO V1_ITER088_FEATURE_COLUMNS constant (zero new features)."""
    import crypto_trade.features_v1 as f1

    assert not hasattr(f1, "V1_ITER088_FEATURE_COLUMNS"), (
        "V1_ITER088_FEATURE_COLUMNS must NOT exist — iter-v1/088 adds zero new features. "
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
    """run_iteration_088 imports without error and has ITERATION_LABEL='v1-088'."""
    import importlib
    import sys

    if "run_iteration_088" in sys.modules:
        del sys.modules["run_iteration_088"]
    mod = importlib.import_module("run_iteration_088")
    assert hasattr(mod, "main")
    assert mod.ITERATION_LABEL == "v1-088"
    assert mod.ITERATION_NUMBER == 88
    assert hasattr(mod, "FEATURES_BASE_HASH_48COL")


def test_runner_hash_constant() -> None:
    """FEATURES_BASE_HASH_48COL in runner matches computed hash of V1_FEATURE_COLUMNS_PRUNED."""
    import run_iteration_088 as r088

    assert r088.FEATURES_BASE_HASH_48COL == "b81176f893826500", (
        f"Runner FEATURES_BASE_HASH_48COL mismatch: {r088.FEATURES_BASE_HASH_48COL!r}"
    )


def test_fail_fast_is_years_constant() -> None:
    """FAIL_FAST_IS_YEARS in runner is 2.0 (matches /087 — infra unchanged)."""
    import run_iteration_088 as r088

    assert r088.FAIL_FAST_IS_YEARS == 2.0, (
        f"FAIL_FAST_IS_YEARS must be 2.0 (unchanged from /087); got {r088.FAIL_FAST_IS_YEARS!r}"
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
    """run_baseline_v1.py contains 'v1-088' dispatch with correct symbol and model name."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists()
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER088_UNIVERSE" in src
    assert "XRPUSDT" in src
    assert "Model_A_XRP_specialist_088" in src


def test_dispatch_import_in_runner() -> None:
    """run_baseline_v1.py imports V1_ITER088_UNIVERSE."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER088_UNIVERSE" in src


def test_dispatch_no_feature_override() -> None:
    """run_baseline_v1.py v1-088 dispatch does NOT override active_feature_columns with a local
    feature set (no V1_ITER088_FEATURE_COLUMNS override in the dispatch block)."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER088_FEATURE_COLUMNS" not in src, (
        "run_baseline_v1.py must NOT reference V1_ITER088_FEATURE_COLUMNS — "
        "iter-v1/088 uses the global 48-col PRUNED set unchanged."
    )


def test_dispatch_fail_fast_wired() -> None:
    """run_baseline_v1.py v1-088 dispatch uses fail_fast_is_years=_ff_years_088."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "_ff_years_088" in src, (
        "run_baseline_v1.py must wire _ff_years_088 for the /088 dispatch block. "
        "Fail-fast is the structure gate of this iteration."
    )
    assert "fail_fast_is_years=_ff_years_088" in src, (
        "run_baseline_v1.py /088 dispatch must pass fail_fast_is_years=_ff_years_088 "
        "to run_backtest()."
    )


# ---------------------------------------------------------------------------
# 6. XRPUSDT parquet audit (skipped if not present)
# ---------------------------------------------------------------------------


def test_xrpusdt_parquet_has_all_48_pruned_columns() -> None:
    """XRPUSDT parquet contains all 48 V1_FEATURE_COLUMNS_PRUNED columns."""
    import pandas as pd

    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "XRPUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"XRPUSDT parquet not found at {parquet_path}")

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    df = pd.read_parquet(parquet_path, columns=list(V1_FEATURE_COLUMNS_PRUNED))
    missing = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in df.columns]
    assert not missing, (
        f"XRPUSDT parquet is missing {len(missing)} of 48 V1_FEATURE_COLUMNS_PRUNED:\n"
        + "\n".join(f"  {c}" for c in missing)
    )
    assert len(df.columns) == 48


# ---------------------------------------------------------------------------
# 7. Symbol eligibility + cross-track flag
# ---------------------------------------------------------------------------


def test_xrp_not_in_v1_excluded_symbols() -> None:
    """XRPUSDT is NOT in V1_EXCLUDED_SYMBOLS (un-reserved at iter-v1/088)."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    assert "XRPUSDT" not in V1_EXCLUDED_SYMBOLS, (
        "XRPUSDT must not be in V1_EXCLUDED_SYMBOLS — it is the iter-v1/088 cohort. "
        "Un-reserved per user directive 2026-06-10 (cross-track v2 overlap accepted)."
    )


def test_xrp_not_in_v1_baseline_universe() -> None:
    """XRPUSDT is NOT in V1_BASELINE_UNIVERSE (it is a fresh-mine candidate, not incumbent)."""
    from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE

    assert "XRPUSDT" not in V1_BASELINE_UNIVERSE, (
        "XRPUSDT must not be in V1_BASELINE_UNIVERSE — it is a fresh-mine SPECIALIST candidate."
    )


def test_assert_v1_universe_passes_for_xrp() -> None:
    """assert_v1_universe(['XRPUSDT']) must pass (XRP is no longer excluded)."""
    from crypto_trade.features_v1 import assert_v1_universe

    assert_v1_universe(["XRPUSDT"])


def test_cross_track_flag_documented_in_source() -> None:
    """V1_EXCLUDED_SYMBOLS comment in __init__.py must document the cross-track overlap."""
    init_path = (
        Path(__file__).parent.parent / "src" / "crypto_trade" / "features_v1" / "__init__.py"
    )
    src = init_path.read_text(encoding="utf-8")
    assert "cross-track" in src.lower() or "CROSS-TRACK" in src, (
        "features_v1/__init__.py must document the cross-track overlap flag for XRPUSDT "
        "(v1 and v2 both trade XRP independently). Missing cross-track annotation."
    )
    assert "XRPUSDT" in src, "features_v1/__init__.py must reference XRPUSDT un-reservation."


def test_other_v2_v3_symbols_still_excluded() -> None:
    """After XRP un-reservation, DOGE/NEAR/BCH/LDO/TRX must still be excluded."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    for sym in ("DOGEUSDT", "NEARUSDT", "BCHUSDT", "LDOUSDT", "TRXUSDT"):
        assert sym in V1_EXCLUDED_SYMBOLS, (
            f"{sym} must remain in V1_EXCLUDED_SYMBOLS (v2/v3 live track). "
            "Only XRPUSDT was un-reserved at iter-v1/088."
        )


# ---------------------------------------------------------------------------
# 8. Track isolation
# ---------------------------------------------------------------------------


def test_run_iteration_088_no_v2_v3_imports() -> None:
    """run_iteration_088.py has no features_v2/v3 import statements (track isolation)."""
    module_path = Path(__file__).parent.parent / "run_iteration_088.py"
    src = module_path.read_text(encoding="utf-8")
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text
    assert "from crypto_trade.features_v3" not in import_text
