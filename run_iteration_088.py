"""iter-v1/088 — XRPUSDT SPECIALIST (STOCK 48-col stack, fail-fast gate).

Cycle-7 SPECIALIST-MINE #8. XRPUSDT un-reserved per user directive 2026-06-10:
  "XRP stays in the v2 universe too — user accepted cross-track double-exposure
  (Option 3). v1 and v2 both trade XRP independently."
  CROSS-TRACK-OVERLAP FLAG: XRPUSDT is traded independently in BOTH v1 (this
  specialist) AND v2 (live). Concentration and parity MUST be checked across
  both tracks at any future bundle assembly or live deployment. This is
  intentional double-exposure per the user directive; not a methodology violation.
  GATE 0 (INFORMATIONAL): avg corr with {DOT, ETH, BTC, AAVE} — NOTED not blocking
  GATE 1 (INFORMATIONAL): trivial short-horizon baseline — NOTED not blocking
  FAIL-FAST GATE: fail_fast_is_years=2.0 — the structure gate of this iteration.
    If cumulative IS weighted_pnl ≤ 0 over first 730 days of IS test trades →
    BLOCKED-FAIL-FAST (run aborts, minimal report written, remaining compute saved).
    If > 0 → continues to full run.

CRITICAL: global V1_FEATURE_COLUMNS_PRUNED stays at 48. NO new features.
NO V1_ITER088 local feature additions. The feature set is exactly V1_FEATURE_COLUMNS_PRUNED.
One-variable discipline: the variable being tested is UNIVERSE (XRP whitelist),
and the fail-fast mechanism is the structure gate (unchanged from /087).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires the
SPECIALIST-mode arguments for iter-v1/088:

    - Cohort: XRPUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level)
    - max_depth = 5 FIXED, num_leaves = 31 FIXED
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (STOCK 48 cols — NO new features)
    - Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; vol-class match for XRP)
    - Aggregator: mean-of-signed-weights across 50 seeds
    - FAIL-FAST: fail_fast_is_years=2.0 enabled (UNCHANGED from /087)

UNCHANGED from /087 methodology:
    - specialist_mode = True (50 seeds × 30 Optuna trials)
    - max_depth=5 FIXED, num_leaves=31 FIXED
    - OOD R3=ON, R5=ON vt_target_vol=0.3
    - mean-of-signed-weights aggregator
    - fail_fast_is_years=2.0 (REUSED infra; no new infrastructure)

NO PARQUET REGENERATION REQUIRED beyond the standard feature regen:
    Global V1_FEATURE_COLUMNS_PRUNED stays at 48 — existing XRP parquet structure
    is valid after running:
    uv run crypto-trade fetch --symbols XRPUSDT --intervals 8h
    uv run crypto-trade fetch-oi --symbols XRPUSDT
    uv run crypto-trade features \
        --symbols XRPUSDT --interval 8h --track v1 --format parquet --workers 4

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

Fail-fast semantics (UNCHANGED from /087):
    Once IS test trades span 2.0 years (730 days) from the first IS trade's close_time,
    evaluate cumulative weighted_pnl of all IS test trades. If ≤ 0:
      - EarlyStopError raised with "BLOCKED-FAIL-FAST: ..." prefix
      - Runner catches it, writes minimal report to reports-v1/iteration_v1-088/
      - Exit code 0 (clean abort, not crash)
      - Compute saved: all remaining IS months + full OOS run
    If > 0: print checkpoint PASSED, continue to full run.
    Default OFF: existing runs unaffected (fail_fast_is_years=None is the default).

Wall-clock projection:
    Full run: 50 seeds × 30 trials × ~37 months ≈ 55,500 fits → ~6-8h
    Aborted at 2yr IS boundary: saves 40-60% of full-run compute.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, XRP only, fail-fast enabled):
    uv run python run_iteration_088.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_088.py --check-hash

Output paths:
    reports-v1/iteration_v1-088/in_sample/
    reports-v1/iteration_v1-088/out_of_sample/
    reports-v1/iteration_v1-088/comparison.csv
    reports-v1/iteration_v1-088/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-088/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-088/optuna_best_params.csv
    reports-v1/iteration_v1-088/run.log
    reports-v1/iteration_v1-088/fail_fast_report.csv  (written if BLOCKED-FAIL-FAST)
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER088_UNIVERSE
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 48-col hash (V1_FEATURE_COLUMNS_PRUNED, STOCK, NO new features).
# Computed: sha256("\n".join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_48COL: str = "b81176f893826500"

# Fail-fast IS window (years).  The real backtest's structure gate.
# UNCHANGED from /087 — same infra, same threshold, same semantics.
FAIL_FAST_IS_YEARS: float = 2.0

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-088"
ITERATION_NUMBER: int = 88


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_FEATURE_COLUMNS_PRUNED is 48 cols and compute its hash.

    iter-v1/088 uses the STOCK 48-col global PRUNED set WITHOUT any additions.
    Global V1_FEATURE_COLUMNS_PRUNED must stay at 48 — this is the load-bearing
    one-variable discipline of this iteration (universe axis, not feature axis).
    """
    if len(V1_FEATURE_COLUMNS_PRUNED) != 48:
        print(
            f"[iter-v1/088] GLOBAL-PRUNED-COUNT MISMATCH\n"
            f"  expected : 48 (global, unchanged)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            "  V1_FEATURE_COLUMNS_PRUNED must stay at 48; "
            "iter-v1/088 adds ZERO new features (one-variable discipline).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/088] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 48 (global unchanged). "
            "iter-v1/088 adds ZERO new feature columns by design."
        )
    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual_hash[:16] != FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/088] HASH MISMATCH\n"
            f"  expected prefix : {FEATURES_BASE_HASH_48COL}\n"
            f"  actual prefix   : {actual_hash[:16]}\n"
            "  V1_FEATURE_COLUMNS_PRUNED has changed from the pre-registered 48-col STOCK set.",
            file=sys.stderr,
        )
        # Non-fatal: print warning but continue (hash is informational)
    print(
        f"[iter-v1/088] features-base-hash: {actual_hash[:16]}... "
        f"(48 columns; STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/088 SPECIALIST runner: "
            f"XRPUSDT 50-seed independent-Optuna bagging, STOCK 48-col stack, "
            f"fail_fast_is_years={FAIL_FAST_IS_YEARS}. "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 XRP SPECIALIST)"
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
            f"[iter-v1/088] --check-hash mode. "
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
        print("  cohort                    : XRPUSDT only (V1_ITER088_UNIVERSE)")
        print("  model                     : Model_A_XRP_specialist_088")
        print("  max_depth                 : 5 (FIXED)")
        print("  num_leaves                : 31 (FIXED; LightGBM default)")
        print("  min_child_samples         : REMOVED from search (LGBM default 20)")
        print("  n_estimators_max          : 500 (wall-clock mitigation)")
        print("  n_startup_trials          : 10 (wall-clock mitigation)")
        print("  atr_tp_multiplier         : 2.9")
        print("  atr_sl_multiplier         : 1.45")
        print("  R1                        : OFF (CATALOG-CLOSED for SPECIALIST_mode)")
        print("  R2                        : OFF (Model A baseline)")
        print("  R3                        : ON-SHARED cutoff=0.70 16-features")
        print("  R5                        : ON vt_target_vol=0.3 vt_lookback_days=45")
        print("  aggregator                : mean-of-signed-weights across 50 seeds")
        print("  feature_count             : 48 (STOCK V1_FEATURE_COLUMNS_PRUNED; NO new features)")
        print("  new_features              : NONE (zero additions by design)")
        print(f"  features_hash_16char      : {actual_hash[:16]}")
        print(f"  V1_ITER088_UNIVERSE       : {V1_ITER088_UNIVERSE}")
        print(f"  fail_fast_is_years        : {FAIL_FAST_IS_YEARS}")
        print(
            "  fail_fast_semantics       : IS weighted_pnl ≤ 0 over first "
            f"{FAIL_FAST_IS_YEARS:.1f}yr → BLOCKED-FAIL-FAST"
        )
        print(
            "  cross_track_flag          : XRPUSDT also traded by v2 live (user-accepted Option 3)"
        )
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/088] PRE-FLIGHT FAIL: global V1_FEATURE_COLUMNS_PRUNED expected 48, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The global pruned set must stay at 48; iter-v1/088 adds ZERO new features."
    )
    assert V1_ITER088_UNIVERSE == ("XRPUSDT",), (
        f"[iter-v1/088] PRE-FLIGHT FAIL: V1_ITER088_UNIVERSE must be ('XRPUSDT',); "
        f"got {V1_ITER088_UNIVERSE}."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/088] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/088] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/088] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/088 — XRPUSDT SPECIALIST (STOCK 48-col stack, fail-fast gate)")
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
    print("  cohort                     : XRPUSDT only (V1_ITER088_UNIVERSE)")
    print("  model                      : Model_A_XRP_specialist_088")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED)  R2=OFF (Model A baseline)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; vol-class match XRP)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print(f"  48-col hash prefix         : {actual_hash[:16]}...")
    print(f"  fail_fast_is_years         : {FAIL_FAST_IS_YEARS}")
    print(
        f"  fail_fast_semantics        : IS weighted_pnl ≤ 0 over first "
        f"{FAIL_FAST_IS_YEARS:.1f}yr IS test trades → BLOCKED-FAIL-FAST (saves remaining compute)"
    )
    print("  cross_track_flag           : XRPUSDT also traded by v2 live (user-accepted Option 3)")
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
        "XRPUSDT",
        "--pruned-features",
        "--seeds",
        "1",
        "--fail-fast-is-years",
        str(FAIL_FAST_IS_YEARS),
    ]

    print(f"[iter-v1/088] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
