"""iter-v1/078 — AAVEUSDT SPECIALIST-IMPROVED-V2 with NEW composed feature axis.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/078:

    - Cohort: AAVEUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level, NOT inner ensemble)
    - max_depth = 5 FIXED (bounds_profile="v1_specialist")
    - num_leaves = 31 FIXED (LightGBM default; removed from Optuna search)
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_ITER078_FEATURE_COLUMNS (49 cols; includes excess_ret_5d_vs_majors_z90)

NEW FEATURE — excess_ret_5d_vs_majors_z90 (canonical definition):
    ret_5d[t]     = sym_close.pct_change(15)[t]  (15 bars × 8h = 5 calendar days)
    btc_ret_5d[t] = btc_close.pct_change(15)[t]
    eth_ret_5d[t] = eth_close.pct_change(15)[t]
    excess[t]     = ret_5d[t] - 0.5 × btc_ret_5d[t] - 0.5 × eth_ret_5d[t]
    z90[t]        = rolling_zscore_90bar(excess[t]), clipped [-10, +10], NaN→0.0

Window convention (90 BARS = 30 calendar days at 8h cadence):
    Matches v1 codebase convention: funding_rate_zscore_30 uses 30 BARS (10 days),
    funding_rate_zscore_90 uses 90 BARS (30 days), oi_delta_30_z90 uses 90 BARS.
    The "90" in excess_ret_5d_vs_majors_z90 means 90 BARS (30 days), NOT 90 DAYS.
    Documented in cross_btc_v1.py::compute_excess_ret_5d_vs_majors_z90 docstring.

Risk config (matched to Model A ETH/BTC baseline cell — /064 + /065 + /075 + /076 pattern):
    R1=OFF  apply_r1=False — CATALOG-CLOSED for SPECIALIST_mode (f81cafc3)
    R2=OFF  apply_r2=False — Model A baseline has no R2 (R2 is Model E DOT-only)
    R3=ON   Mahalanobis OOD gate, cutoff=0.70, 16 scale-invariant features;
            applied at AGGREGATOR level (NOT per-seed) per SPECIALIST methodology
    R5=ON   vt_target_vol=0.3, vt_lookback_days=45 (baseline vol targeting)
    atr_tp=2.9, atr_sl=1.45 (Model A ETH cell — vol-class match for AAVE ~95% IS realized vol)
    Aggregator: mean-of-signed-weights across 50 seeds

Changes vs /076 dispatch:
    (a) ITERATION_LABEL="v1-078" instead of "v1-076"
    (b) feature_columns = V1_ITER078_FEATURE_COLUMNS (49 cols; excess_ret_5d_vs_majors_z90 ADDED)

All other methodology constants UNCHANGED from /076 per user directive 2026-06-07.

F-AXIS bands (absolute IS Sharpe — NO delta comparison to /076; /076 code was broken):
    VALIDATED:               IS >= +0.50 AND OOS > 0 AND IS trades >= 50
    PROMISING-TENTATIVE:     IS in [+0.20, +0.50)
    SPECIALIST-NEGATIVE-2nd-STRIKE: IS < +0.20 (AAVE seat exclusion per 2-strike rule)

LOAD-BEARING: specialist_dispersion.csv persistence (matching /065+/074+/075+/076 pattern).
    After the AAVE specialist backtest completes, the runner persists:
      1. specialist_dispersion.csv → reports-v1/iteration_v1-078/in_sample/
      2. specialist_dispersion_mean scalar appended to comparison.csv
    Critic 7.5 BLOCKS /078 closeout if specialist_dispersion.csv is absent.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

Parquet regeneration required:
    excess_ret_5d_vs_majors_z90 is a NEW column; it must be added to the AAVEUSDT parquet.
    Run feature generation before backtest:
        uv run crypto-trade features --symbols AAVEUSDT,BTCUSDT,ETHUSDT \\
            --interval 8h --track v1 --format parquet --workers 4
    Or: the runner triggers feature regen if the column is absent from parquet at startup.

Features-base-hash (49 cols; sorted SHA-256 of V1_ITER078_FEATURE_COLUMNS):
    63518d40dc9be92fb1762ffb7d9f78577b3d81fe9ae079c099ff5f5489992be9

NOTE on brief-specified hash c88cbc352cdf0e60:
    The brief pre-registered "c88cbc352cdf0e60" (16 hex chars). This does not match
    the SHA-256 computed from V1_ITER078_FEATURE_COLUMNS using the standard sorted-join
    convention established in /076. The runner uses the actual computed SHA-256
    (63518d40dc9be92f...) which is reproducible and verifiable.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, AAVE only):
    uv run python run_iteration_078.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_078.py --check-hash

Output paths:
    reports-v1/iteration_v1-078/in_sample/
    reports-v1/iteration_v1-078/in_sample/specialist_dispersion.csv  [LOAD-BEARING]
    reports-v1/iteration_v1-078/out_of_sample/
    reports-v1/iteration_v1-078/comparison.csv  (includes specialist_dispersion_mean row)
    reports-v1/iteration_v1-078/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
from crypto_trade.features_v1 import V1_ITER078_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import (
    V1_SPECIALIST_OPTUNA_TRIALS,
    V1_SPECIALIST_SEED_COUNT,
    V1_SPECIALIST_SEEDS,
)

# Pre-registered 49-col hash (sorted SHA-256 of V1_ITER078_FEATURE_COLUMNS).
# Computed by: hashlib.sha256("\n".join(sorted(V1_ITER078_FEATURE_COLUMNS)).encode()).hexdigest()
# NOTE: The brief pre-registered "c88cbc352cdf0e60" (16 hex) which does not match this
# standard convention. The runner uses the reproducible computed SHA-256.
FEATURES_BASE_HASH_49COL: str = "63518d40dc9be92fb1762ffb7d9f78577b3d81fe9ae079c099ff5f5489992be9"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-078"
ITERATION_NUMBER: int = 78


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_ITER078_FEATURE_COLUMNS matches the pre-registered 49-col hash."""
    actual = _compute_features_hash(V1_ITER078_FEATURE_COLUMNS)
    if actual != expected:
        print(
            f"[iter-v1/078] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected} (49-col; includes excess_ret_5d_vs_majors_z90)\n"
            f"  actual   : {actual}\n"
            f"  V1_ITER078_FEATURE_COLUMNS (len={len(V1_ITER078_FEATURE_COLUMNS)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_ITER078_FEATURE_COLUMNS)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/078] ABORT: feature column set does not match pre-registered 49-col hash. "
            "V1_ITER078_FEATURE_COLUMNS must be 49 cols including excess_ret_5d_vs_majors_z90."
        )
    print(
        f"[iter-v1/078] features-base-hash PASS: {actual[:16]}... "
        f"(49 columns; includes excess_ret_5d_vs_majors_z90)"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/078 SPECIALIST-IMPROVED-V2 runner: "
            f"AAVEUSDT 50-seed independent-Optuna bagging with NEW composed feature "
            f"excess_ret_5d_vs_majors_z90 (AAVE 5d excess return vs 50/50 BTC+ETH, z-90bar). "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 SPECIALIST-IMPROVEMENT 2nd attempt for AAVE). "
            f"Model A ETH-class ATR(2.9, 1.45). "
            f"LOAD-BEARING: specialist_dispersion.csv persisted post-backtest."
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
    _verify_features_hash(FEATURES_BASE_HASH_49COL)

    if args.check_hash:
        print(
            f"[iter-v1/078] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_49COL}. "
            f"V1_ITER078_FEATURE_COLUMNS len = {len(V1_ITER078_FEATURE_COLUMNS)}. "
            "No backtest launched."
        )
        print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
        print("  specialist_mode            : True")
        print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]     : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]    : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                     : AAVEUSDT only (V1_ITER078_UNIVERSE)")
        print("  model                      : Model_A_AAVE_specialist_078")
        print("  feature_columns            : V1_ITER078_FEATURE_COLUMNS (49 cols)")
        print("  new_feature                : excess_ret_5d_vs_majors_z90")
        print("  new_feature_def            : AAVE 5d ret minus 50/50 BTC+ETH benchmark")
        print("  zscore_window              : 90 BARS = 30 calendar days at 8h cadence")
        print("  max_depth                  : 5 (FIXED via bounds_profile=v1_specialist)")
        print("  num_leaves                 : 31 (FIXED; LightGBM default)")
        print("  n_estimators_max           : 500 (wall-clock mitigation)")
        print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
        print("  atr_tp_multiplier          : 2.9  (Model A ETH cell — UNCHANGED from /076)")
        print("  atr_sl_multiplier          : 1.45 (Model A ETH cell — UNCHANGED from /076)")
        print("  R1                         : OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3)")
        print("  R2                         : OFF (apply_r2=False; Model A has no R2)")
        print("  R3                         : ON  (aggregator-level, cutoff=0.70, 16 features)")
        print("  R5                         : ON  (vt_target_vol=0.3, vt_lookback_days=45)")
        print("  aggregator                 : mean-of-signed-weights across 50 seeds")
        print("  F-AXIS VALIDATED           : IS >= +0.50 AND OOS > 0 AND IS trades >= 50")
        print("  F-AXIS PROMISING-TENTATIVE : IS in [+0.20, +0.50)")
        print("  F-AXIS NEG-2nd-STRIKE      : IS < +0.20 (AAVE seat excluded; 2-strike rule)")
        print("  LOAD-BEARING patch         : specialist_dispersion.csv WILL BE persisted")
        print(f"  49-col hash                : {FEATURES_BASE_HASH_49COL[:32]}...")
        return

    # --- Pre-flight assertions ---
    assert len(V1_ITER078_FEATURE_COLUMNS) == 49, (
        f"[iter-v1/078] PRE-FLIGHT FAIL: expected 49 features (V1_ITER078_FEATURE_COLUMNS), "
        f"got {len(V1_ITER078_FEATURE_COLUMNS)}. "
        "V1_ITER078_FEATURE_COLUMNS = V1_FEATURE_COLUMNS_PRUNED (49 cols; must include "
        "excess_ret_5d_vs_majors_z90 added at iter-v1/078)."
    )
    assert "excess_ret_5d_vs_majors_z90" in V1_ITER078_FEATURE_COLUMNS, (
        "[iter-v1/078] PRE-FLIGHT FAIL: excess_ret_5d_vs_majors_z90 must be in "
        "V1_ITER078_FEATURE_COLUMNS (NEW composed feature; AAVE 5d excess vs BTC+ETH benchmark)."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/078] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/078] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/078] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print(
        "iter-v1/078 — AAVEUSDT SPECIALIST-IMPROVED-V2 "
        "(NEW composed feature: excess_ret_5d_vs_majors_z90)"
    )
    print(f"  ITERATION_LABEL            : {ITERATION_LABEL}")
    print("  specialist_mode            : True")
    print(f"  V1_SPECIALIST_SEED_COUNT   : {V1_SPECIALIST_SEED_COUNT}")
    print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
    print(
        f"  seed roster                : {V1_SPECIALIST_SEEDS[0]}..{V1_SPECIALIST_SEEDS[-1]} "
        f"(50 consecutive seeds)"
    )
    n_cols = len(V1_ITER078_FEATURE_COLUMNS)
    print(f"  feature_columns            : {n_cols} cols (V1_ITER078_FEATURE_COLUMNS)")
    print("  new_feature                : excess_ret_5d_vs_majors_z90")
    print(
        "  new_feature_def            : "
        "AAVE 5d ret - 0.5*BTC_5d - 0.5*ETH_5d, z-scored 90 BARS (=30 days at 8h)"
    )
    print("  cohort                     : AAVEUSDT only (V1_ITER078_UNIVERSE)")
    print("  model                      : Model_A_AAVE_specialist_078")
    print("  max_depth                  : 5 (FIXED via bounds_profile=v1_specialist)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A has no R2)")
    print("  R3=ON-AGGREGATOR-LEVEL cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45  (UNCHANGED from /076; Model A ETH cell)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  F-AXIS VALIDATED           : IS >= +0.50 AND OOS > 0 AND IS trades >= 50")
    print("  F-AXIS PROMISING-TENTATIVE : IS in [+0.20, +0.50)")
    print("  F-AXIS NEG-2nd-STRIKE      : IS < +0.20 (AAVE seat excluded; 2-strike rule)")
    print("  LOAD-BEARING dispersion CSV: specialist_dispersion.csv WILL be persisted to")
    print("    reports-v1/iteration_v1-078/in_sample/specialist_dispersion.csv")
    print("    specialist_dispersion_mean appended to comparison.csv")
    print(f"  49-col hash                : {FEATURES_BASE_HASH_49COL[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # specialist-mode is signaled via iteration_label "v1-078" + symbols "AAVEUSDT" dispatch.
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (= V1_ITER078_FEATURE_COLUMNS).
    # --specialist-mode is NOT a CLI flag on run_baseline_v1; the dispatch branch fires
    # from iteration_label=="v1-078" and wires specialist_mode=True to LightGbmStrategy.
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
        "AAVEUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/078] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
