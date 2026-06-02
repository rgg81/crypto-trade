"""iter-v1/063 — DOTUSDT SPECIALIST (first under SPECIALIST + BUNDLE methodology).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/063:

    - Cohort: DOTUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level, NOT inner ensemble)
    - max_depth = 5 FIXED (removed from Optuna search; set in lgbm.py specialist path)
    - num_leaves = 31 FIXED (LightGBM default; removed from Optuna search)
    - min_child_samples REMOVED from search space (uses LGBM default 20)
    - n_estimators upper bound = 500 (wall-clock mitigation, per brief Section 3.6)
    - n_startup_trials = 10 (TPE warmup reduction; per brief Section 3.6)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED)
    - Risk config: R1=ON K=3/C=27, R2=ON trigger=7%/anchor=15%/floor=0.33,
                   R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BASELINE_V1 Model E DOT)
    - Aggregator: mean-of-signed-weights across 50 seeds

SPECIALIST + BUNDLE methodology design (skill commit ee5910e):
    Each seed_i (i ∈ {0..49}) runs:
      1. Its own Optuna TPESampler(seed=42+i) study with n_trials=30
      2. Stores best (HP_i, threshold_i, model_i) triple
      3. At inference: model_i.predict_proba(X) compared to threshold_i → (dir_i, weight_i)
    Aggregator at inference:
      signed_w_i = direction_i × weight_i ∈ [-100, +100]
      final_signed = mean(signed_w_i for i in range(50)) ∈ [-100, +100]
      Signal(direction=sign(final_signed), weight=abs(int(round(final_signed))))
    Risk wrappers (R1/R2/R3/R5) apply ONCE to aggregator output — NOT per-seed.
    R3 OOD is SHARED (one Mahalanobis distance per candle, NOT 50).

Verdict framework (brief Section 4 F-AXIS):
    F-AXIS #1 (mean IS Sharpe, LM 60% modal band [+0.18, +0.32]):
        ≥ +0.32 → SPECIALIST-PROMISING-STRONG
        [+0.18, +0.32] → SPECIALIST-PROMISING (first roster entry for BUNDLE-001)
        [-0.10, +0.18] → SPECIALIST-PROMISING-WEAK
        [-0.20, -0.10] → SPECIALIST-NEUTRAL
        < -0.20 → SPECIALIST-NEGATIVE (DOT axis closed; /064 advances to ETH)
    F-AXIS #2 (σ_pop = cross-seed std at N=50; LOAD-BEARING gate):
        ≤ 0.20 → METHODOLOGY-VALIDATED-STRONG
        (0.20, 0.30] → METHODOLOGY-VALIDATED (LM modal prediction)
        (0.30, 0.40] → METHODOLOGY-PARTIAL
        > 0.40 → METHODOLOGY-NEGATIVE (bagging redesign at /064)
    F-AXIS #3 (OOS Sharpe): INFORMATIONAL ONLY.
    F-AXIS #4 (falsifier): methodology FALSIFIED only if σ_pop>0.40 AND mean IS<-0.20 BOTH.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED from /061 closeout).

Features-base-hash (48 cols; UNCHANGED):
    b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Wall-clock projection (brief Section 3.6):
    50 seeds × 30 trials × 24 months ≈ 36,000 fits
    With n_estimators cap 500 + n_startup_trials=10: projected ~5.5h
    No kill-switch (per 2026-05-30 directive). Overrun documented in engineering report.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, DOT only):
    uv run python run_iteration_063.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_063.py --check-hash

Output paths:
    reports-v1/iteration_v1-063/in_sample/
    reports-v1/iteration_v1-063/out_of_sample/
    reports-v1/iteration_v1-063/comparison.csv
    reports-v1/iteration_v1-063/per_seed_sharpe.csv    (F-AXIS #2 σ_pop diagnostic)
    reports-v1/iteration_v1-063/optuna_best_params.csv  (per-seed HP persistence)
    reports-v1/iteration_v1-063/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 48-col hash (UNCHANGED from /061 closeout).
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-063"
ITERATION_NUMBER: int = 63


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 48-col hash."""
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/063] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected} (48-col; UNCHANGED from /061 closeout)\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/063] ABORT: feature column set does not match pre-registered 48-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/063 (no feature add/drop)."
        )
    print(
        f"[iter-v1/063] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; UNCHANGED from /061 closeout)"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/063 SPECIALIST runner: "
            f"DOTUSDT 50-seed independent-Optuna bagging "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 SPECIALIST 1/10)"
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

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    _verify_features_hash(FEATURES_BASE_HASH_48COL)

    if args.check_hash:
        print(
            f"[iter-v1/063] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_48COL}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
        print("  specialist_mode        : True")
        print(f"  V1_SPECIALIST_SEED_COUNT : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0] : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]: {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                 : DOTUSDT only (V1_ITER063_UNIVERSE)")
        print("  model                  : Model_E_DOT_specialist (R1=ON, R2=ON, R3=ON-SHARED)")
        print("  max_depth              : 5 (FIXED)")
        print("  num_leaves             : 31 (FIXED; LightGBM default)")
        print("  min_child_samples      : REMOVED from search (LGBM default 20)")
        print("  n_estimators_max       : 500 (wall-clock mitigation)")
        print("  n_startup_trials       : 10 (wall-clock mitigation)")
        print("  atr_tp_multiplier      : 3.5")
        print("  atr_sl_multiplier      : 1.75")
        print("  R1                     : ON K=3 C=27")
        print("  R2                     : ON trigger=7% anchor=15% floor=0.33")
        print("  R3                     : ON-SHARED cutoff=0.70 16-features")
        print("  R5                     : ON vt_target_vol=0.3 vt_lookback_days=45")
        print("  aggregator             : mean-of-signed-weights across 50 seeds")
        print("  verdict framework      :")
        print("    F-AXIS #1 (mean IS Sharpe): [+0.18, +0.32] = SPECIALIST-PROMISING")
        print("    F-AXIS #2 (σ_pop ≤ 0.30) : METHODOLOGY-VALIDATED (load-bearing gate)")
        print("    F-AXIS #3 (OOS Sharpe)   : INFORMATIONAL ONLY")
        print(f"  48-col hash            : {FEATURES_BASE_HASH_48COL[:32]}...")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/063] PRE-FLIGHT FAIL: expected 48 features (UNCHANGED), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/063."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/063] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/063] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/063] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/063 — DOTUSDT SPECIALIST (SPECIALIST+BUNDLE methodology)")
    print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
    print("  specialist_mode            : True")
    print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
    print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
    print(
        f"  seed roster                : {V1_SPECIALIST_SEEDS[0]}..{V1_SPECIALIST_SEEDS[-1]} "
        f"(50 consecutive seeds)"
    )
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns            : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; UNCHANGED)")
    print("  cohort                     : DOTUSDT only (V1_ITER063_UNIVERSE)")
    print("  model                      : Model_E_DOT_specialist")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=ON K=3/C=27  R2=ON trigger=7%/anchor=15%/floor=0.33")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  verdict primary gate       : F-AXIS #2 σ_pop ≤ 0.30 (METHODOLOGY-WIN)")
    print(f"  48-col hash                : {FEATURES_BASE_HASH_48COL[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # specialist-mode is signaled via iteration_label "v1-063" + symbols "DOTUSDT" dispatch.
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (48 cols).
    # --specialist-mode is NOT a CLI flag on run_baseline_v1; the dispatch branch fires
    # from iteration_label=="v1-063" and wires specialist_mode=True to LightGbmStrategy.
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
        "DOTUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/063] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
