"""iter-v1/075 — ATOMUSDT SPECIALIST (first NEW SYMBOL universe-extension; autopilot mining).

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/075:

    - Cohort: ATOMUSDT only (single-symbol SPECIALIST per skill mandate)
    - specialist_mode=True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level, NOT inner ensemble)
    - max_depth = 5 FIXED (bounds_profile="v1_specialist")
    - num_leaves = 31 FIXED (LightGBM default; removed from Optuna search)
    - n_estimators upper bound = 500 (wall-clock mitigation)
    - n_startup_trials = 10 (TPE warmup reduction)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED)

Risk config (matched to Model A ETH/BTC baseline cell — /064 + /065 pattern):
    R1=OFF  apply_r1=False — CATALOG-CLOSED for SPECIALIST_mode (f81cafc3)
    R2=OFF  apply_r2=False — Model A baseline has no R2 (R2 is Model E DOT-only)
    R3=ON   Mahalanobis OOD gate, cutoff=0.70, 16 scale-invariant features;
            applied at AGGREGATOR level (NOT per-seed) per SPECIALIST methodology
    R5=ON   vt_target_vol=0.3, vt_lookback_days=45 (baseline vol targeting)
    atr_tp=2.9, atr_sl=1.45 (Model A ETH cell — vol-class match for ATOM 80% IS realized vol)
    Aggregator: mean-of-signed-weights across 50 seeds

Single-bit changes vs /063 dispatch:
    (a) SYMBOLS=("ATOMUSDT",) instead of ("DOTUSDT",)
    (b) ITERATION_LABEL="v1-075" instead of "v1-063"
    (c) ATR cell (2.9, 1.45) instead of /063's (3.5, 1.75) — ETH-class vol match
    (d) Model A wrapper (R1=OFF, R2=OFF) matching /064+/065 pattern, NOT /063 DOT's Model E

LOAD-BEARING: specialist_dispersion.csv persistence (matching /065+/074 pattern).
    After the ATOM specialist backtest completes, the runner persists:
      1. specialist_dispersion.csv → reports-v1/iteration_v1-075/in_sample/
      2. specialist_dispersion_mean scalar appended to comparison.csv
    Critic 7.5 BLOCKS /075 closeout if specialist_dispersion.csv is absent.

SPECIALIST + BUNDLE methodology design (skill commit ee5910e):
    Each seed_i (i ∈ {0..49}) runs:
      1. Its own Optuna TPESampler(seed=42+i) study with n_trials=30
      2. Stores best (HP_i, threshold_i, model_i) triple
      3. At inference: model_i.predict_proba(X) compared to threshold_i → (dir_i, weight_i)
    Aggregator at inference:
      signed_w_i = direction_i × weight_i ∈ [-100, +100]
      final_signed = mean(signed_w_i for i in range(50)) ∈ [-100, +100]
      Signal(direction=sign(final_signed), weight=abs(int(round(final_signed))))
    Risk wrappers (R3/R5) apply ONCE to aggregator output — NOT per-seed.
    R1/R2 are OFF per Model A ETH/BTC baseline cell pattern.

Verdict framework (brief Section 4 F-AXIS):
    F-AXIS #1 (mean IS Sharpe — NEW SYMBOL; bands vs BUNDLE-001 member distribution):
        IS Sharpe >= +0.50 → SPECIALIST-PROMISING-CLEAN (ATOM enters BUNDLE-002 at HIGH confidence)
        IS Sharpe in [+0.20, +0.50) → SPECIALIST-PROMISING-TENTATIVE (basin-lottery audit required)
        IS Sharpe < +0.20 OR IS trades < 50 → SPECIALIST-NEGATIVE (ATOM dropped; one-attempt rule)
    F-AXIS #2 (sigma_pop = cross-seed std at N=50; LOAD-BEARING gate):
        <= 0.20 → METHODOLOGY-VALIDATED-STRONG
        (0.20, 0.30] → METHODOLOGY-VALIDATED (LM modal prediction)
        (0.30, 0.40] → METHODOLOGY-PARTIAL (basin-lottery vigilance triggers)
        > 0.40 → METHODOLOGY-NEGATIVE
    F-AXIS #3 (OOS Sharpe): INFORMATIONAL ONLY.
    F-AXIS-FALSIFIER #1: per-direction Sharpe + WR + trade count MANDATORY in Phase 7.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED from /061 closeout; verified at /063-/065+/074).
    data/features/ATOMUSDT_8h_features.parquet exists (6933 x 230 cols;
    all 48 V1_FEATURE_COLUMNS_PRUNED present;
    parquet-file hash 0865537dc50a8d11 per LM Master Phase 4.5 verification).

NaN notes (table_09 audit — NOT a methodology break):
    dot_vs_btc_ret_ratio_30  — ALL-NaN for ATOM (SYMBOL-conditional; DOT-only feature)
    eth_vs_btc_ret_ratio_30  — ALL-NaN for ATOM (SYMBOL-conditional; ETH-only feature)
    LightGBM handles NaN natively (use_missing=True default). 2/48 = 4.2% wasted slots.
    long_short_zscore_30 ~50% NaN in IS (ATOM data starts mid-window).
    oi_delta_30_z90 ~41% NaN in IS (ATOM OI data starts mid-window).

Features-base-hash (48 cols; UNCHANGED):
    b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Wall-clock projection (brief Section 0.5):
    ATOM single cell × 50 seeds × 30 trials × 24 months ≈ 36,000 fits
    Based on /063 (DOT ≈ 1.4h) and /064 (ETH ≈ 1.5h) precedents: projected ~50-90 min.
    Hard cap: 2h EXPLORATION budget per feedback_v1_confirmation_walltime_9h.md.

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, ATOM only):
    uv run python run_iteration_075.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_075.py --check-hash

Output paths:
    reports-v1/iteration_v1-075/in_sample/
    reports-v1/iteration_v1-075/in_sample/specialist_dispersion.csv  [LOAD-BEARING]
    reports-v1/iteration_v1-075/out_of_sample/
    reports-v1/iteration_v1-075/comparison.csv  (includes specialist_dispersion_mean row)
    reports-v1/iteration_v1-075/run.log
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

# Pre-registered 48-col hash (UNCHANGED from /061 closeout; verified at /063, /064, /065, /074).
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-075"
ITERATION_NUMBER: int = 75


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 48-col hash."""
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/075] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected} (48-col; UNCHANGED from /061 closeout)\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/075] ABORT: feature column set does not match pre-registered 48-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/075 (no feature add/drop)."
        )
    print(
        f"[iter-v1/075] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; UNCHANGED from /061 closeout)"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/075 SPECIALIST runner: "
            f"ATOMUSDT 50-seed independent-Optuna bagging "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; cycle-7 NEW SYMBOL mine 1/N). "
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
    _verify_features_hash(FEATURES_BASE_HASH_48COL)

    if args.check_hash:
        print(
            f"[iter-v1/075] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_48COL}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(f"  ITERATION_LABEL          : {ITERATION_LABEL}")
        print("  specialist_mode          : True")
        print(f"  V1_SPECIALIST_SEED_COUNT : {V1_SPECIALIST_SEED_COUNT}")
        print(f"  V1_SPECIALIST_OPTUNA_TRIALS: {V1_SPECIALIST_OPTUNA_TRIALS}")
        print(f"  V1_SPECIALIST_SEEDS[0]   : {V1_SPECIALIST_SEEDS[0]}")
        print(f"  V1_SPECIALIST_SEEDS[-1]  : {V1_SPECIALIST_SEEDS[-1]}")
        print("  cohort                   : ATOMUSDT only (V1_ITER075_UNIVERSE)")
        print("  model                    : Model_A_ATOM_specialist_075")
        print("  max_depth                : 5 (FIXED via bounds_profile=v1_specialist)")
        print("  num_leaves               : 31 (FIXED; LightGBM default)")
        print("  n_estimators_max         : 500 (wall-clock mitigation)")
        print("  n_startup_trials         : 10 (wall-clock mitigation; TPE warmup reduction)")
        print("  atr_tp_multiplier        : 2.9  (Model A ETH cell — vol-class match for ATOM)")
        print("  atr_sl_multiplier        : 1.45 (Model A ETH cell — vol-class match for ATOM)")
        print("  R1                       : OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3)")
        print("  R2                       : OFF (apply_r2=False; Model A has no R2)")
        print("  R3                       : ON  (aggregator-level, cutoff=0.70, 16 features)")
        print("  R5                       : ON  (vt_target_vol=0.3, vt_lookback_days=45)")
        print("  aggregator               : mean-of-signed-weights across 50 seeds")
        print("  NaN notes (table_09)     : dot_vs_btc_ret_ratio_30 ALL-NaN (SYMBOL-conditional)")
        print("                             eth_vs_btc_ret_ratio_30 ALL-NaN (SYMBOL-conditional)")
        print("                             LightGBM NaN-handles natively (use_missing=True)")
        print("  LOAD-BEARING patch       : specialist_dispersion.csv WILL BE persisted")
        print("  verdict framework        :")
        print("    F-AXIS #1 (mean IS Sharpe >= +0.50): SPECIALIST-PROMISING-CLEAN")
        print("    F-AXIS #1 (mean IS Sharpe [+0.20, +0.50)): SPECIALIST-PROMISING-TENTATIVE")
        print("    F-AXIS #1 (< +0.20 OR < 50 IS trades): SPECIALIST-NEGATIVE (one-attempt rule)")
        print("    F-AXIS #2 (sigma_pop <= 0.30): METHODOLOGY-VALIDATED (load-bearing gate)")
        print("    F-AXIS #3 (OOS Sharpe)      : INFORMATIONAL ONLY")
        print(f"  48-col hash              : {FEATURES_BASE_HASH_48COL[:32]}...")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/075] PRE-FLIGHT FAIL: expected 48 features (UNCHANGED), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/075 (no feature add/drop). "
        "The 2 ALL-NaN-IS SYMBOL-conditional columns (dot_vs_btc_ret_ratio_30, "
        "eth_vs_btc_ret_ratio_30) are RETAINED; LightGBM NaN-handles natively."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/075] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/075] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/075] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )

    print("=" * 70)
    print("iter-v1/075 — ATOMUSDT SPECIALIST (NEW SYMBOL mine 1/N; autopilot 2026-06-06)")
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
    print("  cohort                     : ATOMUSDT only (V1_ITER075_UNIVERSE)")
    print("  model                      : Model_A_ATOM_specialist_075")
    print("  max_depth                  : 5 (FIXED via bounds_profile=v1_specialist)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A has no R2)")
    print("  R3=ON-AGGREGATOR-LEVEL cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45  (Model A ETH cell; vol-class match for ATOM ~80% IS vol)")
    print("  NaN (table_09): dot_vs_btc_ret_ratio_30 + eth_vs_btc_ret_ratio_30 ALL-NaN (OK)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  LOAD-BEARING dispersion CSV: specialist_dispersion.csv WILL be persisted to")
    print("    reports-v1/iteration_v1-075/in_sample/specialist_dispersion.csv")
    print("    specialist_dispersion_mean appended to comparison.csv")
    print("  IS BTC return corr         : 0.617 (highest idiosyncratic diversity in eligible set)")
    print("  IS realized vol            : ~80% ann. (ETH-class; ATR cell justified)")
    print("  F-AXIS #1                  : PROMISING-CLEAN >= +0.50 / TENTATIVE [+0.20, +0.50)")
    print("  F-AXIS #1 NEGATIVE         : < +0.20 OR < 50 IS trades (one-attempt-and-eliminate)")
    print(f"  48-col hash                : {FEATURES_BASE_HASH_48COL[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # specialist-mode is signaled via iteration_label "v1-075" + symbols "ATOMUSDT" dispatch.
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (48 cols).
    # --specialist-mode is NOT a CLI flag on run_baseline_v1; the dispatch branch fires
    # from iteration_label=="v1-075" and wires specialist_mode=True to LightGbmStrategy.
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
        "ATOMUSDT",
        "--pruned-features",
        "--seeds",
        "1",
    ]

    print(f"[iter-v1/075] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
