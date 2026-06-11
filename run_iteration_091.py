"""iter-v1/091 — ETHUSDT SPECIALIST (R-CONV ensemble-conviction trade gate).

Second machinery axis of cycle-7. Single-seat EXPLORATION: ETH/064 seat re-run
with the post-aggregator R-CONV gate (enable_r_conv_gate=True, r_conv_tau=0.06)
vs the frozen ETH/064 standalone baseline (IS +0.2383 / OOS +0.5171).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/091:

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
    - FAIL-FAST: fail_fast_is_years=2.0 ON (brief §2.5; guards over-filtering bug)

THE SINGLE CHANGE vs ETH/064:
    enable_r_conv_gate=True, r_conv_tau=0.06 (hardwired in LightGbmStrategy constructor)
    = post-aggregator RULE skip when _sp_confidence < 0.06 (net seed agreement ≤2/50)
    = same RULE-layer band as /074 AXIS-R + /084 R-FADE
    Default enable_r_conv_gate=False path is BYTE-IDENTICAL (no change for any other iteration).

R-CONV gate mechanics:
    _sp_confidence = |_final_signed| / 100  (net seed-agreement fraction, 0..1)
    tau=0.06 → skip candles where ≤3 of 50 seeds net-agree on direction
    IS effect (§2.3): drops 67 of 198 IS trades (34%); dropped bucket WR 37.3% / −5.43% sumPnL
    OOS projection: drops ~9 of 81 OOS trades (11%); see LM §6 for OOS-sign-flip caveat

LM §1 REQUIRED deliverable:
    specialist_dispersion.csv persisted (skipped candles excluded from dispersion stats).
    Phase 7.4 will split the r_conv_skip decision_log entries by ensemble_std to separate
    abstention (low std) from disagreement (high std) in the dropped set.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED — no feature changes).
    ETH parquet at data/features/ETHUSDT_8h_features.parquet must be fresh (≤16h).
    ETH parquet verified fresh at /090 closeout (2026-06-11 07:39 UTC, ~9.8h stale).

Features-base-hash (48 cols; UNCHANGED from /064 closeout):
    b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Wall-clock projection (brief §3):
    50 seeds × 30 trials × ~54 months ≈ same as /064 (~8h worst case).
    R-CONV adds negligible overhead (pure Python comparison per candle, post-training).
    fail_fast=2.0 bounds worst-case bad draw to ~3-4h.
    Use detached-bash launch per feedback_split_engineer_dispatch.md.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, ETH only, fail-fast enabled):
    uv run python run_iteration_091.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_091.py --check-hash

Output paths:
    reports-v1/iteration_v1-091/in_sample/
    reports-v1/iteration_v1-091/out_of_sample/
    reports-v1/iteration_v1-091/comparison.csv
    reports-v1/iteration_v1-091/in_sample/specialist_dispersion.csv  (LM §1 REQUIRED)
    reports-v1/iteration_v1-091/optuna_best_params.csv
    reports-v1/iteration_v1-091/run.log
    reports-v1/iteration_v1-091/fail_fast_report.csv  (written if BLOCKED-FAIL-FAST)
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER091_UNIVERSE
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 48-col hash (V1_FEATURE_COLUMNS_PRUNED, STOCK, NO new features).
# Computed: sha256("\n".join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_48COL: str = "b81176f893826500"

# Fail-fast IS window (years).  Guards over-filtering and catastrophic bugs.
# ON per brief §2.5 / §9.
FAIL_FAST_IS_YEARS: float = 2.0

# R-CONV gate parameters (pre-registered, IS-only basis).
R_CONV_TAU: float = 0.06

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-091"
ITERATION_NUMBER: int = 91


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_FEATURE_COLUMNS_PRUNED is 48 cols and compute its hash.

    iter-v1/091 uses the STOCK 48-col global PRUNED set WITHOUT any additions.
    Global V1_FEATURE_COLUMNS_PRUNED must stay at 48 — this is a risk-primitive
    axis (post-aggregator RULE gate), NOT a feature axis. Zero feature changes.
    """
    if len(V1_FEATURE_COLUMNS_PRUNED) != 48:
        print(
            f"[iter-v1/091] GLOBAL-PRUNED-COUNT MISMATCH\n"
            f"  expected : 48 (global, unchanged)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            "  V1_FEATURE_COLUMNS_PRUNED must stay at 48; "
            "iter-v1/091 adds ZERO new features (risk-primitive/post-aggregator axis).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/091] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 48 (global unchanged). "
            "iter-v1/091 adds ZERO new feature columns by design."
        )
    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual_hash[:16] != FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/091] HASH MISMATCH\n"
            f"  expected prefix : {FEATURES_BASE_HASH_48COL}\n"
            f"  actual prefix   : {actual_hash[:16]}\n"
            "  V1_FEATURE_COLUMNS_PRUNED has changed from the pre-registered 48-col STOCK set.",
            file=sys.stderr,
        )
        # Non-fatal: print warning but continue (hash is informational)
    print(
        f"[iter-v1/091] features-base-hash: {actual_hash[:16]}... "
        f"(48 columns; STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/091 SPECIALIST runner: "
            f"ETHUSDT 50-seed independent-Optuna bagging, R-CONV gate "
            f"(enable_r_conv_gate=True, r_conv_tau={R_CONV_TAU}), "
            f"STOCK 48-col stack, fail_fast_is_years={FAIL_FAST_IS_YEARS}. "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 ETH R-CONV SPECIALIST)"
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
            f"[iter-v1/091] --check-hash mode. "
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
        print("  cohort                    : ETHUSDT only (V1_ITER091_UNIVERSE)")
        print("  model                     : Model_A_ETH_specialist_091 (R-CONV)")
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
        print("  feature_count             : 48 (STOCK V1_FEATURE_COLUMNS_PRUNED; NO new)")
        print("  new_features              : NONE (zero additions by design)")
        print("  THE SINGLE CHANGE vs /064 : enable_r_conv_gate=True")
        print(f"                              r_conv_tau={R_CONV_TAU} (pre-registered IS-only)")
        print("                              = skip _sp_confidence < 0.06 (net agree ≤2/50)")
        print(
            "                              post-aggregator RULE layer (same band as AXIS-R+R-FADE)"
        )
        print("  lm_required_deliverable   : specialist_dispersion.csv persisted")
        print("                              r_conv_skip entries carry ensemble_std for 7.4 split")
        print(f"  features_hash_16char      : {actual_hash[:16]}")
        print(f"  V1_ITER091_UNIVERSE       : {V1_ITER091_UNIVERSE}")
        print(f"  fail_fast_is_years        : {FAIL_FAST_IS_YEARS}")
        print(
            "  fail_fast_semantics       : IS weighted_pnl ≤ 0 over first "
            f"{FAIL_FAST_IS_YEARS:.1f}yr → BLOCKED-FAIL-FAST"
        )
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/091] PRE-FLIGHT FAIL: global V1_FEATURE_COLUMNS_PRUNED expected 48, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The global pruned set must stay at 48; iter-v1/091 adds ZERO new features."
    )
    assert V1_ITER091_UNIVERSE == ("ETHUSDT",), (
        f"[iter-v1/091] PRE-FLIGHT FAIL: V1_ITER091_UNIVERSE must be ('ETHUSDT',); "
        f"got {V1_ITER091_UNIVERSE}."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/091] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/091] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/091] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/091 — ETHUSDT SPECIALIST R-CONV (conviction gate tau=0.06)")
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
    print("  cohort                     : ETHUSDT only (V1_ITER091_UNIVERSE)")
    print("  model                      : Model_A_ETH_specialist_091 (R-CONV)")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (Model A)  R2=OFF (Model A)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; matches /064 exactly)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  THE SINGLE CHANGE vs /064  : enable_r_conv_gate=True")
    print(f"                               r_conv_tau={R_CONV_TAU} (pre-registered IS-only)")
    print(
        "                               skip _sp_confidence < 0.06 → NO_SIGNAL "
        "(post-aggregator RULE)"
    )
    print(
        "  LM §1 REQUIRED             : specialist_dispersion.csv persisted; "
        "r_conv_skip carries ensemble_std"
    )
    print(f"  48-col hash prefix         : {actual_hash[:16]}...")
    print(f"  fail_fast_is_years         : {FAIL_FAST_IS_YEARS}")
    print(
        f"  fail_fast_semantics        : IS weighted_pnl ≤ 0 over first "
        f"{FAIL_FAST_IS_YEARS:.1f}yr IS test trades → BLOCKED-FAIL-FAST (saves remaining compute)"
    )
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # AXIS ISOLATION: do NOT pass --enable-r-conv-gate here. The gate parameters are
    # hardwired in the LightGbmStrategy constructor inside the v1-091 dispatch block.
    # This keeps the CLI surface minimal and avoids any cross-contamination with
    # global CLI flag parsing in run_baseline_v1.
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

    print(f"[iter-v1/091] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
