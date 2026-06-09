"""iter-v1/085 — UNIUSDT SPECIALIST (4-feature mean-reversion set).

Cycle-7 SPECIALIST-MINE. Per user directive 2026-06-09: "get one coin and focus on it.
start with 4 features, 10. grind a bit."

4-FEATURE SET (LOCAL; V1_FEATURE_COLUMNS_PRUNED global stays at 48):
    (a) rev_extension_z_3     — sign-flipped 3-bar return z-score (reversion signal).
        UNI ac_lag3 = -0.0843 — strongest measured autocorr structure.
        Warmup: 3 + 50 + 1 = 54 bars NaN.
    (b) vol_state_z_natr_30   — z-normalized 30-bar NATR volatility state conditioner.
        Stationarized version of natr_30 (|IC|≈0.0386 with label in prescreen).
        Warmup: 30 + 90 + 1 = 121 bars NaN.
    (c) rev_halflife_50       — z-normalized rolling AR(1) mean-reversion half-life.
        Measures how FAST UNI reverts — fast = phi ≈ -1 = half-life ≈ 0 bars.
        Warmup: 50 + 90 + 1 = 141 bars NaN.
    (d) rev_vol_gate_signed   — rev_extension_z_3 × soft vol-regime gate (composed).
        Gates reversion signal OFF in vol-expansion regimes (vol_state_z_natr_30 > 1.0).
        Mechanically correlated with rev_extension_z_3 by construction (Category-2).
        Warmup: same as rev_extension_z_3 ≈ 54 bars (inherits shift(1) from inputs).

CRITICAL: global V1_FEATURE_COLUMNS_PRUNED stays at 48 (the /084 bug lesson applied).
V1_ITER085_FEATURE_COLUMNS = V1_FEATURE_COLUMNS_PRUNED + 4 new = 52 cols LOCAL.
All 4 features go LOCAL — NEVER modify global V1_FEATURE_COLUMNS_PRUNED.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires the
SPECIALIST-mode arguments for iter-v1/085:

    - Cohort: UNIUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level)
    - max_depth = 5 FIXED, num_leaves = 31 FIXED
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_ITER085_FEATURE_COLUMNS (LOCAL; 52 cols)
    - Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; vol-class match for UNI ~80-100% IS vol)
    - Aggregator: mean-of-signed-weights across 50 seeds

UNCHANGED from /076//084 methodology:
    - specialist_mode = True (50 seeds × 30 Optuna trials)
    - max_depth=5 FIXED, num_leaves=31 FIXED
    - OOD R3=ON, R5=ON vt_target_vol=0.3
    - mean-of-signed-weights aggregator

PARQUET REGENERATION REQUIRED (UNIUSDT only; other symbols unchanged):
    V1_ITER085_FEATURE_COLUMNS (LOCAL 52 cols) used for UNIUSDT specialist cell.
    Global V1_FEATURE_COLUMNS_PRUNED stays 48 — other specialists UNCHANGED.
    Post-feature hash (new 52-col UNIUSDT parquet): c8b8e0a87abb280a

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

Wall-clock projection:
    50 seeds × 30 trials × 24 months ≈ 36,000 fits
    With n_estimators cap 500 + n_startup_trials=10: projected ~5-8h

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, UNI only):
    uv run python run_iteration_085.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_085.py --check-hash

Output paths:
    reports-v1/iteration_v1-085/in_sample/
    reports-v1/iteration_v1-085/out_of_sample/
    reports-v1/iteration_v1-085/comparison.csv
    reports-v1/iteration_v1-085/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-085/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-085/optuna_best_params.csv
    reports-v1/iteration_v1-085/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER085_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 52-col hash (V1_FEATURE_COLUMNS_PRUNED + 4 new UNI-specialist features).
# Computed: sha256("\n".join(sorted(V1_ITER085_FEATURE_COLUMNS)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_52COL: str = "c8b8e0a87abb280a"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-085"
ITERATION_NUMBER: int = 85

# New features in /085 (LOCAL — not in global PRUNED)
ITER085_NEW_FEATURES: tuple[str, ...] = (
    "rev_extension_z_3",
    "vol_state_z_natr_30",
    "rev_halflife_50",
    "rev_vol_gate_signed",
)


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_ITER085_FEATURE_COLUMNS is 52 cols and compute its hash.

    V1_FEATURE_COLUMNS_PRUNED (global) stays at 48. The /085-local constant
    V1_ITER085_FEATURE_COLUMNS = PRUNED(48) + (4 new features) = 52.
    """
    if len(V1_FEATURE_COLUMNS_PRUNED) != 48:
        print(
            f"[iter-v1/085] GLOBAL-PRUNED-COUNT MISMATCH\n"
            f"  expected : 48 (global, unchanged)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            "  V1_FEATURE_COLUMNS_PRUNED must stay at 48; "
            "the 4 new features are LOCAL-ONLY in V1_ITER085_FEATURE_COLUMNS.",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/085] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 48 (global unchanged). "
            "4 new features live in V1_ITER085_FEATURE_COLUMNS only."
        )
    if len(V1_ITER085_FEATURE_COLUMNS) != 52:
        print(
            f"[iter-v1/085] ITER085-FEATURE-COUNT MISMATCH\n"
            f"  expected : 52 (48 base + 4 new UNI-specialist features)\n"
            f"  actual   : {len(V1_ITER085_FEATURE_COLUMNS)}\n"
            f"  V1_ITER085_FEATURE_COLUMNS (len={len(V1_ITER085_FEATURE_COLUMNS)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_ITER085_FEATURE_COLUMNS)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/085] ABORT: V1_ITER085_FEATURE_COLUMNS must be 52 at iter-v1/085. "
            "Expected 48 base + 4 new features = 52."
        )
    for feat in ITER085_NEW_FEATURES:
        if feat not in V1_ITER085_FEATURE_COLUMNS:
            sys.exit(
                f"[iter-v1/085] ABORT: {feat} not found in V1_ITER085_FEATURE_COLUMNS. "
                "All 4 new features must be in the /085 local constant."
            )
    actual_hash = _compute_features_hash(V1_ITER085_FEATURE_COLUMNS)
    if actual_hash[:16] != FEATURES_BASE_HASH_52COL:
        print(
            f"[iter-v1/085] HASH MISMATCH\n"
            f"  expected prefix : {FEATURES_BASE_HASH_52COL}\n"
            f"  actual prefix   : {actual_hash[:16]}\n"
            "  V1_ITER085_FEATURE_COLUMNS has changed from the pre-registered 52-col set.",
            file=sys.stderr,
        )
        # Non-fatal: print warning but continue (hash is informational)
    print(
        f"[iter-v1/085] features-base-hash: {actual_hash[:16]}... "
        f"(52 columns; 48 base + {len(ITER085_NEW_FEATURES)} new UNI-specialist features)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/085 SPECIALIST runner: "
            f"UNIUSDT 50-seed independent-Optuna bagging + 4-feature mean-reversion set "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 UNI SPECIALIST)"
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
            f"[iter-v1/085] --check-hash mode. "
            f"Hash = {actual_hash[:16]}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)} (global=48). "
            f"V1_ITER085_FEATURE_COLUMNS len = {len(V1_ITER085_FEATURE_COLUMNS)} (local=52). "
            "No backtest launched."
        )
        print(f"  ITERATION_LABEL          : {ITERATION_LABEL}")
        print("  specialist_mode          : True")
        print(f"  V1_SPECIALIST_SEED_COUNT : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]   : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]  : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                   : UNIUSDT only (V1_ITER085_UNIVERSE)")
        print("  model                    : Model_A_UNI_specialist_085")
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
        print("  feature_count            : 52 (48 base + 4 new UNI-specialist)")
        print(f"  new_features             : {list(ITER085_NEW_FEATURES)}")
        print(f"  features_hash_16char     : {actual_hash[:16]}")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/085] PRE-FLIGHT FAIL: global V1_FEATURE_COLUMNS_PRUNED expected 48, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The global pruned set must stay at 48; 4 new features are LOCAL-ONLY in "
        "V1_ITER085_FEATURE_COLUMNS."
    )
    assert len(V1_ITER085_FEATURE_COLUMNS) == 52, (
        f"[iter-v1/085] PRE-FLIGHT FAIL: V1_ITER085_FEATURE_COLUMNS expected 52, "
        f"got {len(V1_ITER085_FEATURE_COLUMNS)}. "
        "Must be V1_FEATURE_COLUMNS_PRUNED(48) + 4 new UNI-specialist features = 52."
    )
    for feat in ITER085_NEW_FEATURES:
        assert feat in V1_ITER085_FEATURE_COLUMNS, (
            f"[iter-v1/085] PRE-FLIGHT FAIL: {feat} not in V1_ITER085_FEATURE_COLUMNS."
        )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/085] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/085] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/085] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/085 — UNIUSDT SPECIALIST (4-feature mean-reversion set)")
    print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
    print("  specialist_mode            : True")
    print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
    print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
    print(
        f"  seed roster                : {V1_SPECIALIST_SEEDS[0]}..{V1_SPECIALIST_SEEDS[-1]} "
        f"(50 consecutive seeds)"
    )
    n_cols = len(V1_ITER085_FEATURE_COLUMNS)
    print(f"  feature_columns            : {n_cols} cols (V1_ITER085_FEATURE_COLUMNS)")
    print(f"  new features               : {list(ITER085_NEW_FEATURES)}")
    print("  cohort                     : UNIUSDT only (V1_ITER085_UNIVERSE)")
    print("  model                      : Model_A_UNI_specialist_085")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A baseline)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; vol-class match UNI ~80-100% IS vol)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print(f"  52-col hash prefix         : {actual_hash[:16]}...")
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
        "UNIUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/085] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
