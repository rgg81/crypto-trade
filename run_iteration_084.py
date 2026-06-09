"""iter-v1/084 — CRVUSDT SPECIALIST (OI-price divergence + R-FADE gate).

Cycle-7 SPECIALIST-MINE N/N. Symbol selected via REFORMED SELECTION RULE:
prefer symbols with the MOST NEGATIVE trivial-momentum Sharpe (IS-only).
CRV trivial-momentum IS Sharpe: negative → ML has room to add edge.

TWO-CHANGE iteration (NEW FEATURE + NEW RISK — both scoped to CRVUSDT specialist):
    (a) NEW feature oi_price_divergence_30 added to V1_FEATURE_COLUMNS_PRUNED (48 → 49).
        Re-aimed from /083 rank-7/11 OI family toward NEGATIVE-baseline CRVUSDT.
        Compute (all components past-only via .shift(1)):
            oi_delta_30 = sum_open_interest.pct_change(30)
            ret_30 = log(close).diff(30)
            div_raw = sign(oi_delta_30) - sign(ret_30)   ∈ {-2, 0, +2}
            oi_price_divergence_30 = z90(div_raw).shift(1)
        NON_FEATURE intermediates: oi_delta_30, ret_30, div_raw NOT passed as model columns.
    (b) NEW risk enable_oi_divergence_fade_gate=True — post-aggregator stateless gate:
        VETO entry when sign(signal) OPPOSES sign(oi_price_divergence_30) AND
        |oi_price_divergence_30| > fade_z=2.0 (IS-calibrated, pre-registered threshold).
        Reuses the proven AXIS-R /074 gate pattern (post-aggregator, state-free, parity-clean).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires the
SPECIALIST-mode arguments for iter-v1/084:

    - Cohort: CRVUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level, NOT inner ensemble)
    - max_depth = 5 FIXED (removed from Optuna search; set in lgbm.py specialist path)
    - num_leaves = 31 FIXED (LightGBM default; removed from Optuna search)
    - min_child_samples REMOVED from search space (uses LGBM default 20)
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (49 cols: 48 base + oi_price_divergence_30)
    - Risk config: R1=OFF (CATALOG-CLOSED; f81cafc3), R2=OFF, R3=ON-SHARED cutoff=0.70,
                   R5=ON vt_target_vol=0.3, R-FADE=ON fade_z=2.0
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; vol-class match for CRV ~100-130% IS vol)
    - Aggregator: mean-of-signed-weights across 50 seeds

UNCHANGED from /076 methodology (single-bit family per mandate):
    - specialist_mode = True (50 seeds × 30 Optuna trials)
    - max_depth=5 FIXED, num_leaves=31 FIXED
    - OOD R3=ON, R5=ON vt_target_vol=0.3
    - mean-of-signed-weights aggregator

PARQUET REGENERATION REQUIRED:
    V1_FEATURE_COLUMNS_PRUNED extended 48 → 49 (NEW: oi_price_divergence_30).
    Pre-feature hash (old 48-col parquet): e0292892e28a0f51
    Post-feature hash (new 49-col parquet): 274348d5eb93f9d6

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))
    oi_divergence_fade_z = 2.0  (IS-calibrated pre-registered; anti-tuning FROZEN at brief commit)

Wall-clock projection:
    50 seeds × 30 trials × 24 months ≈ 36,000 fits
    With n_estimators cap 500 + n_startup_trials=10: projected ~5.5-8h
    No kill-switch. Overrun documented in engineering report.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, CRV only):
    uv run python run_iteration_084.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_084.py --check-hash

Output paths:
    reports-v1/iteration_v1-084/in_sample/
    reports-v1/iteration_v1-084/out_of_sample/
    reports-v1/iteration_v1-084/comparison.csv
    reports-v1/iteration_v1-084/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-084/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-084/optuna_best_params.csv
    reports-v1/iteration_v1-084/run.log
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

# Pre-registered 49-col hash (V1_FEATURE_COLUMNS_PRUNED after adding oi_price_divergence_30).
# Computed: sha256("\n".join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode("utf-8")).hexdigest()
FEATURES_BASE_HASH_49COL: str = "expected_hash_computed_at_import"

# Pre-feature parquet hash (CRVUSDT_8h_features.parquet before oi_price_divergence_30 added).
# Used as a baseline fingerprint for audit trail only (not a runtime assertion).
PRE_FEATURE_PARQUET_HASH_16: str = "e0292892e28a0f51"

# Post-feature parquet hash (CRVUSDT_8h_features.parquet after oi_price_divergence_30 regen).
POST_FEATURE_PARQUET_HASH_16: str = "274348d5eb93f9d6"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-084"
ITERATION_NUMBER: int = 84

# R-FADE gate: pre-registered IS-calibrated threshold (FROZEN at brief authoring; anti-tuning).
OI_DIVERGENCE_FADE_Z: float = 2.0
OI_DIVERGENCE_FADE_COLUMN: str = "oi_price_divergence_30"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash() -> str:
    """Assert V1_FEATURE_COLUMNS_PRUNED is 49 cols and compute its hash."""
    if len(V1_FEATURE_COLUMNS_PRUNED) != 49:
        print(
            f"[iter-v1/084] FEATURES-COUNT MISMATCH\n"
            f"  expected : 49 (48 base + oi_price_divergence_30)\n"
            f"  actual   : {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/084] ABORT: V1_FEATURE_COLUMNS_PRUNED must be 49 at iter-v1/084. "
            "Expected 48 base + oi_price_divergence_30 = 49."
        )
    if "oi_price_divergence_30" not in V1_FEATURE_COLUMNS_PRUNED:
        sys.exit(
            "[iter-v1/084] ABORT: oi_price_divergence_30 not found in V1_FEATURE_COLUMNS_PRUNED. "
            "This feature must be added before running /084."
        )
    actual_hash = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    print(
        f"[iter-v1/084] features-base-hash: {actual_hash[:16]}... "
        f"(49 columns; 48 base + oi_price_divergence_30)"
    )
    return actual_hash


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/084 SPECIALIST runner: "
            f"CRVUSDT 50-seed independent-Optuna bagging + oi_price_divergence_30 feature "
            f"+ R-FADE gate (fade_z={OI_DIVERGENCE_FADE_Z}) "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 SPECIALIST N/N)"
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
            f"[iter-v1/084] --check-hash mode. "
            f"Hash = {actual_hash[:16]}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(f"  ITERATION_LABEL          : {ITERATION_LABEL}")
        print("  specialist_mode          : True")
        print(f"  V1_SPECIALIST_SEED_COUNT : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]   : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]  : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                   : CRVUSDT only (V1_ITER084_UNIVERSE)")
        print("  model                    : Model_A_CRV_specialist_084")
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
        print(
            f"  R-FADE                   : ON fade_z={OI_DIVERGENCE_FADE_Z}"
            f" col={OI_DIVERGENCE_FADE_COLUMN}"
        )
        print("  aggregator               : mean-of-signed-weights across 50 seeds")
        print("  feature_count            : 49 (48 base + oi_price_divergence_30)")
        print(f"  pre_feature_hash         : {PRE_FEATURE_PARQUET_HASH_16}")
        print(f"  post_feature_hash        : {POST_FEATURE_PARQUET_HASH_16}")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 49, (
        f"[iter-v1/084] PRE-FLIGHT FAIL: expected 49 features, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 49 at iter-v1/084 "
        "(48 base + oi_price_divergence_30)."
    )
    assert "oi_price_divergence_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/084] PRE-FLIGHT FAIL: oi_price_divergence_30 not in V1_FEATURE_COLUMNS_PRUNED."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/084] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/084] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/084] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )
    # R-FADE threshold assertion (anti-tuning; pre-registered threshold FROZEN at brief authoring)
    assert OI_DIVERGENCE_FADE_Z == 2.0, (
        f"[iter-v1/084] PRE-FLIGHT FAIL: OI_DIVERGENCE_FADE_Z must be 2.0 (pre-registered); "
        f"got {OI_DIVERGENCE_FADE_Z}. Threshold is FROZEN at brief authoring."
    )

    print("=" * 70)
    print("iter-v1/084 — CRVUSDT SPECIALIST (OI-price divergence + R-FADE gate)")
    print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
    print("  specialist_mode            : True")
    print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
    print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
    print(
        f"  seed roster                : {V1_SPECIALIST_SEEDS[0]}..{V1_SPECIALIST_SEEDS[-1]} "
        f"(50 consecutive seeds)"
    )
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns            : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED + oi_div_30)")
    print("  cohort                     : CRVUSDT only (V1_ITER084_UNIVERSE)")
    print("  model                      : Model_A_CRV_specialist_084")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A baseline)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print(
        f"  R-FADE=ON fade_z={OI_DIVERGENCE_FADE_Z} col={OI_DIVERGENCE_FADE_COLUMN}"
        " (IS-cal; FROZEN)"
    )
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell; vol-class CRV ~100-130% IS vol)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print(f"  49-col hash prefix         : {actual_hash[:16]}...")
    print(f"  pre-feature parquet hash   : {PRE_FEATURE_PARQUET_HASH_16} (e0292892...)")
    print(f"  post-feature parquet hash  : {POST_FEATURE_PARQUET_HASH_16} (274348d5...)")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # specialist-mode is signaled via iteration_label "v1-084" + symbols "CRVUSDT" dispatch.
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (49 cols).
    # --specialist-mode is NOT a CLI flag on run_baseline_v1; the dispatch branch fires
    # from iteration_label=="v1-084" and wires specialist_mode=True + R-FADE to LightGbmStrategy.
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
        "CRVUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/084] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
