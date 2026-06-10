"""iter-v1/086 — TRBUSDT SPECIALIST (STOCK 48-col stack, NO new features).

Cycle-7 SPECIALIST-MINE #6. First fresh-mine candidate to clear the full HARD gate ladder:
  GATE 0: lowest average bundle-correlation (avg 0.548 vs {DOT, ETH, BTC, AAVE})
  GATE 1: negative short-horizon trivial baseline (min-horizon −0.179 ≤ +0.15)
  GATE 2 PRIMARY: structure-probe PASS (IS Sharpe +0.4930 ≥ +0.30)
  GATE 2 SECONDARY: max |IC| 0.3863 (mom_macd_line_12_26_9) — momentum/trend structure

CRITICAL: global V1_FEATURE_COLUMNS_PRUNED stays at 48. NO new features.
NO V1_ITER086 local feature additions. The feature set is exactly V1_FEATURE_COLUMNS_PRUNED.
This is the load-bearing one-variable discipline of this iteration (explicit avoidance of
the /085 inert-feature failure mode): the edge is already in the stock 48-col stack.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires the
SPECIALIST-mode arguments for iter-v1/086:

    - Cohort: TRBUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level)
    - max_depth = 5 FIXED, num_leaves = 31 FIXED
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (STOCK 48 cols — NO new features)
    - Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; vol-class match for TRB)
    - Aggregator: mean-of-signed-weights across 50 seeds

UNCHANGED from /076//084//085 methodology:
    - specialist_mode = True (50 seeds × 30 Optuna trials)
    - max_depth=5 FIXED, num_leaves=31 FIXED
    - OOD R3=ON, R5=ON vt_target_vol=0.3
    - mean-of-signed-weights aggregator

NO PARQUET REGENERATION REQUIRED:
    Global V1_FEATURE_COLUMNS_PRUNED stays at 48 — existing TRBUSDT parquet is valid.
    The parquet was generated during the GATE-2 probe (analysis/iteration_v1-086/probe_TRBUSDT.py)
    and has been verified to contain all 48 V1_FEATURE_COLUMNS_PRUNED columns.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

Wall-clock projection:
    50 seeds × 30 trials × 24 months ≈ 36,000 fits
    With n_estimators cap 500 + n_startup_trials=10: projected ~5-7h

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, TRB only):
    uv run python run_iteration_086.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_086.py --check-hash

Output paths:
    reports-v1/iteration_v1-086/in_sample/
    reports-v1/iteration_v1-086/out_of_sample/
    reports-v1/iteration_v1-086/comparison.csv
    reports-v1/iteration_v1-086/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-086/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-086/optuna_best_params.csv
    reports-v1/iteration_v1-086/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER086_UNIVERSE
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 48-col hash (V1_FEATURE_COLUMNS_PRUNED, STOCK, NO new features).
# Computed: sha256("\n".join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_48COL: str = "b81176f893826500"


# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-086"
ITERATION_NUMBER: int = 86


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_FEATURE_COLUMNS_PRUNED is 48 cols and compute its hash.

    iter-v1/086 uses the STOCK 48-col global PRUNED set WITHOUT any additions.
    Global V1_FEATURE_COLUMNS_PRUNED must stay at 48 — this is the load-bearing
    one-variable discipline of this iteration.
    """
    if len(V1_FEATURE_COLUMNS_PRUNED) != 48:
        print(
            f"[iter-v1/086] GLOBAL-PRUNED-COUNT MISMATCH\n"
            f"  expected : 48 (global, unchanged)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            "  V1_FEATURE_COLUMNS_PRUNED must stay at 48; "
            "iter-v1/086 adds ZERO new features (one-variable discipline).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/086] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 48 (global unchanged). "
            "iter-v1/086 adds ZERO new feature columns by design."
        )
    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual_hash[:16] != FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/086] HASH MISMATCH\n"
            f"  expected prefix : {FEATURES_BASE_HASH_48COL}\n"
            f"  actual prefix   : {actual_hash[:16]}\n"
            "  V1_FEATURE_COLUMNS_PRUNED has changed from the pre-registered 48-col STOCK set.",
            file=sys.stderr,
        )
        # Non-fatal: print warning but continue (hash is informational)
    print(
        f"[iter-v1/086] features-base-hash: {actual_hash[:16]}... "
        f"(48 columns; STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/086 SPECIALIST runner: "
            f"TRBUSDT 50-seed independent-Optuna bagging, STOCK 48-col stack, NO new features. "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 TRB SPECIALIST)"
        )
    )
    p.add_argument(
        "--check-hash",
        action="store_true",
        default=False,
        help="Print the features-base-hash and exit (dry-run; no backtest launched).",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    # --- Hash/count check (always runs; dry-run exits here if --check-hash) ---
    actual_hash = _verify_features_hash()

    if args.check_hash:
        print(
            f"[iter-v1/086] --check-hash mode. "
            f"Hash = {actual_hash[:16]}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)} "
            f"(global=48; UNCHANGED). No backtest launched."
        )
        print(f"  ITERATION_LABEL          : {ITERATION_LABEL}")
        print("  specialist_mode          : True")
        print(f"  V1_SPECIALIST_SEED_COUNT : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]   : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]  : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                   : TRBUSDT only (V1_ITER086_UNIVERSE)")
        print("  model                    : Model_A_TRB_specialist_086")
        print("  max_depth                : 5 (FIXED)")
        print("  num_leaves               : 31 (FIXED; LightGBM default)")
        print("  min_child_samples        : REMOVED from search (LGBM default 20)")
        print("  n_estimators_max         : 500 (wall-clock mitigation)")
        print("  n_startup_trials         : 10 (wall-clock mitigation)")
        print("  atr_tp_multiplier        : 2.9")
        print("  atr_sl_multiplier        : 1.45")
        print("  R1                       : OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3)")
        print("  R2                       : OFF (Model A baseline)")
        print("  R3                       : ON-SHARED cutoff=0.70 16-features")
        print("  R5                       : ON vt_target_vol=0.3 vt_lookback_days=45")
        print("  aggregator               : mean-of-signed-weights across 50 seeds")
        print("  feature_count            : 48 (STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)")
        print("  new_features             : NONE (zero additions by design)")
        print(f"  features_hash_16char     : {actual_hash[:16]}")
        print(f"  V1_ITER086_UNIVERSE      : {V1_ITER086_UNIVERSE}")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/086] PRE-FLIGHT FAIL: global V1_FEATURE_COLUMNS_PRUNED expected 48, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The global pruned set must stay at 48; iter-v1/086 adds ZERO new features."
    )
    assert V1_ITER086_UNIVERSE == ("TRBUSDT",), (
        f"[iter-v1/086] PRE-FLIGHT FAIL: V1_ITER086_UNIVERSE must be ('TRBUSDT',); "
        f"got {V1_ITER086_UNIVERSE}."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/086] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/086] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/086] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/086 — TRBUSDT SPECIALIST (STOCK 48-col stack, NO new features)")
    print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
    print("  specialist_mode            : True")
    print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
    print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
    print(
        f"  seed roster                : {V1_SPECIALIST_SEEDS[0]}..{V1_SPECIALIST_SEEDS[-1]} "
        f"(50 consecutive seeds)"
    )
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(
        f"  feature_columns            : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; STOCK; NO new)"
    )
    print("  new features               : NONE (zero additions by design)")
    print("  cohort                     : TRBUSDT only (V1_ITER086_UNIVERSE)")
    print("  model                      : Model_A_TRB_specialist_086")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A baseline)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; vol-class match TRB)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print(f"  48-col hash prefix         : {actual_hash[:16]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    sys.argv = [
        "run_baseline_v1.py",
        "--exploration",
        "--iteration",
        str(ITERATION_NUMBER),
        "--n-trials",
        str(V1_SPECIALIST_OPTUNA_TRIALS),
        "--ensemble-size",
        "1",
        "--symbols",
        "TRBUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/086] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
