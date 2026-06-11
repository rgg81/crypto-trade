"""iter-v1/090 — ETHUSDT SPECIALIST (W-DECAY sample-weighting axis).

Cycle-7 SPECIALIST — first machinery / sample-weighting EXPLORATION.
Single-seat EXPLORATION: ETH/064 seat re-run with abs_pnl_timedecay (half_life=12mo)
vs the frozen ETH/064 standalone baseline (IS +0.2383 / OOS +0.5171).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/090:

    - Cohort: ETHUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level)
    - max_depth = 5 FIXED, num_leaves = 31 FIXED
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (STOCK 48 cols — NO new features)
    - Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; matches /064)
    - Aggregator: mean-of-signed-weights across 50 seeds
    - FAIL-FAST: fail_fast_is_years=2.0 ON (QR call: brief §3; guards implementation bug)

THE SINGLE CHANGE vs ETH/064:
    sample_weight_mode="abs_pnl_timedecay" (hardwired in LightGbmStrategy constructor)
    = abs_pnl weights × exp(-ln2/12 · age_months)
    = López de Prado AFML Ch.4 exponential time-decay, half_life=12mo (pre-registered).
    Default abs_pnl path is BYTE-IDENTICAL (no change for any other iteration/seat).

Axis Isolation design:
    The mode is hardwired in the dispatch block's LightGbmStrategy constructor, NOT
    passed via --sample-weight-mode CLI flag. This bypasses the /016 _disable_r5 logic
    (which targets pooled-model runs, not per-seat specialist W-DECAY). R5 stays ON as
    per ETH/064 config. See run_baseline_v1.py iter-v1/090 dispatch block comment.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED — no feature changes).
    ETH parquet at data/features/ETHUSDT_8h_features.parquet must be fresh (≤16h).

Features-base-hash (48 cols; UNCHANGED from /064 closeout):
    b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Wall-clock projection (brief Section 3):
    50 seeds × 30 trials × ~54 months ≈ same as /064 (~1.5h)
    W-DECAY decay multiply overhead: negligible (O(n_train) per cell).
    Projected ~1.5–2.0h, inside the 2h SPECIALIST cap.
    Use detached-bash launch per feedback_split_engineer_dispatch.md.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, ETH only, fail-fast enabled):
    uv run python run_iteration_090.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_090.py --check-hash

Output paths:
    reports-v1/iteration_v1-090/in_sample/
    reports-v1/iteration_v1-090/out_of_sample/
    reports-v1/iteration_v1-090/comparison.csv
    reports-v1/iteration_v1-090/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-090/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-090/optuna_best_params.csv
    reports-v1/iteration_v1-090/run.log
    reports-v1/iteration_v1-090/fail_fast_report.csv  (written if BLOCKED-FAIL-FAST)
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER090_UNIVERSE
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 48-col hash (V1_FEATURE_COLUMNS_PRUNED, STOCK, NO new features).
# Computed: sha256("\n".join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_48COL: str = "b81176f893826500"

# Fail-fast IS window (years).  Guards catastrophic implementation bugs.
# ON per brief §3 ("fail-fast: ON (QR call)").
FAIL_FAST_IS_YEARS: float = 2.0

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-090"
ITERATION_NUMBER: int = 90


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_FEATURE_COLUMNS_PRUNED is 48 cols and compute its hash.

    iter-v1/090 uses the STOCK 48-col global PRUNED set WITHOUT any additions.
    Global V1_FEATURE_COLUMNS_PRUNED must stay at 48 — this is a sample-weighting
    axis, NOT a feature axis. Zero feature changes by design.
    """
    if len(V1_FEATURE_COLUMNS_PRUNED) != 48:
        print(
            f"[iter-v1/090] GLOBAL-PRUNED-COUNT MISMATCH\n"
            f"  expected : 48 (global, unchanged)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            "  V1_FEATURE_COLUMNS_PRUNED must stay at 48; "
            "iter-v1/090 adds ZERO new features (sample-weighting axis only).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/090] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 48 (global unchanged). "
            "iter-v1/090 adds ZERO new feature columns by design."
        )
    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual_hash[:16] != FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/090] HASH MISMATCH\n"
            f"  expected prefix : {FEATURES_BASE_HASH_48COL}\n"
            f"  actual prefix   : {actual_hash[:16]}\n"
            "  V1_FEATURE_COLUMNS_PRUNED has changed from the pre-registered 48-col STOCK set.",
            file=sys.stderr,
        )
        # Non-fatal: print warning but continue (hash is informational)
    print(
        f"[iter-v1/090] features-base-hash: {actual_hash[:16]}... "
        f"(48 columns; STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/090 SPECIALIST runner: "
            f"ETHUSDT 50-seed independent-Optuna bagging, W-DECAY abs_pnl_timedecay, "
            f"STOCK 48-col stack, fail_fast_is_years={FAIL_FAST_IS_YEARS}. "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 ETH W-DECAY SPECIALIST)"
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
            f"[iter-v1/090] --check-hash mode. "
            f"Hash = {actual_hash[:16]}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)} "
            f"(global=48; UNCHANGED). No backtest launched."
        )
        print(f"  ITERATION_LABEL           : {ITERATION_LABEL}")
        print("  specialist_mode           : True")
        print(f"  V1_SPECIALIST_SEED_COUNT  : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]    : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]   : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                    : ETHUSDT only (V1_ITER090_UNIVERSE)")
        print("  model                     : Model_A_ETH_specialist_090 (W-DECAY)")
        print("  max_depth                 : 5 (FIXED)")
        print("  num_leaves                : 31 (FIXED; LightGBM default)")
        print("  min_child_samples         : REMOVED from search (LGBM default 20)")
        print("  n_estimators_max          : 500 (wall-clock mitigation)")
        print("  n_startup_trials          : 10 (wall-clock mitigation)")
        print("  atr_tp_multiplier         : 2.9 (Model A ETH cell; matches /064)")
        print("  atr_sl_multiplier         : 1.45 (Model A ETH cell; matches /064)")
        print("  R1                        : OFF (Model A baseline)")
        print("  R2                        : OFF (Model A baseline)")
        print("  R3                        : ON-SHARED cutoff=0.70 16-features")
        print("  R5                        : ON vt_target_vol=0.3 vt_lookback_days=45")
        print("  aggregator                : mean-of-signed-weights across 50 seeds")
        print("  feature_count             : 48 (STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)")
        print("  new_features              : NONE (zero additions by design)")
        print("  THE SINGLE CHANGE vs /064 : sample_weight_mode=abs_pnl_timedecay")
        print("                              = abs_pnl × exp(-ln2/12 · age_months)")
        print(
            "                              half_life=12mo (pre-registered; hardwired in dispatch)"
        )  # noqa: E501
        print("  axis_isolation            : mode hardwired in constructor (NOT CLI flag)")
        print("                              → /016 R5-disable bypassed; R5 stays ON")
        print(f"  features_hash_16char      : {actual_hash[:16]}")
        print(f"  V1_ITER090_UNIVERSE       : {V1_ITER090_UNIVERSE}")
        print(f"  fail_fast_is_years        : {FAIL_FAST_IS_YEARS}")
        print(
            "  fail_fast_semantics       : IS weighted_pnl ≤ 0 over first "
            f"{FAIL_FAST_IS_YEARS:.1f}yr → BLOCKED-FAIL-FAST"
        )
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/090] PRE-FLIGHT FAIL: global V1_FEATURE_COLUMNS_PRUNED expected 48, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The global pruned set must stay at 48; iter-v1/090 adds ZERO new features."
    )
    assert V1_ITER090_UNIVERSE == ("ETHUSDT",), (
        f"[iter-v1/090] PRE-FLIGHT FAIL: V1_ITER090_UNIVERSE must be ('ETHUSDT',); "
        f"got {V1_ITER090_UNIVERSE}."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/090] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/090] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/090] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/090 — ETHUSDT SPECIALIST W-DECAY (abs_pnl_timedecay half_life=12mo)")
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
    print("  cohort                     : ETHUSDT only (V1_ITER090_UNIVERSE)")
    print("  model                      : Model_A_ETH_specialist_090 (W-DECAY)")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (Model A)  R2=OFF (Model A)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; matches /064 exactly)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  THE SINGLE CHANGE vs /064  : sample_weight_mode=abs_pnl_timedecay")
    print("                               (hardwired in dispatch constructor; NOT CLI flag)")
    print("                               abs_pnl × exp(-ln2/12 · age_months), half_life=12mo")
    print(f"  48-col hash prefix         : {actual_hash[:16]}...")
    print(f"  fail_fast_is_years         : {FAIL_FAST_IS_YEARS}")
    print(
        f"  fail_fast_semantics        : IS weighted_pnl ≤ 0 over first "
        f"{FAIL_FAST_IS_YEARS:.1f}yr IS test trades → BLOCKED-FAIL-FAST (saves remaining compute)"
    )
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # AXIS ISOLATION: do NOT pass --sample-weight-mode here. The mode is hardwired
    # in the LightGbmStrategy constructor inside the v1-090 dispatch block.
    # This prevents the /016-era _disable_r5_for_sample_weighting flag from firing.
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
        "ETHUSDT",
        "--pruned-features",
        "--seeds",
        "1",
        "--fail-fast-is-years",
        str(FAIL_FAST_IS_YEARS),
    ]

    print(f"[iter-v1/090] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
