"""iter-v1/074 — ETH-IMPROVED-V3 SPECIALIST (AXIS-R Mid-Bull SHORT VETO).

THIRD improvement attempt for the ETH /064 BUNDLE-001 seat.
Anchor: /064 (IS Sharpe +0.2383, OOS Sharpe +0.5171, 198 IS / 81 OOS trades).
/073 is NOT the anchor — /073 IMPROVEMENT-FAIL (IS Δ −0.25 vs /064; discarded).

AXIS-R — Mid-Bull SHORT VETO rule layer:
    Skip direction=−1 entries when ret_270b ∈ [0.20, 0.50].
    ret_270b = (close[t] / close[t − 270]) − 1.0 on 8h candles = 90-day trailing return.
    Pre-registered band edges [0.20, 0.50] frozen at brief authoring commit.
    Post-aggregator filter (NOT per-seed): applied AFTER mean-of-signed-weights aggregator
    emits Signal(direction, weight) and BEFORE R3 OOD / R5 vol-target call-sites.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``. It hardwires
the SPECIALIST-mode arguments for iter-v1/074 — a SINGLE-BIT deviation from /064:

    - ITERATION_LABEL = "v1-074"  (vs "v1-064" at /064)
    - enable_mid_bull_short_veto = True  (NEW — the only change vs /064)
    - mid_bull_short_veto_lo = 0.20     (NEW — pre-registered band edge LOW)
    - mid_bull_short_veto_hi = 0.50     (NEW — pre-registered band edge HIGH)
    - mid_bull_short_veto_lookback = 270 (NEW — 270 8h candles = 90 calendar days)

UNCHANGED from /064 (HARD — single-bit discipline):
    - Cohort: ETHUSDT only (V1_ITER074_UNIVERSE)
    - specialist_mode = True → 50 independent Optuna studies (one per seed)
    - V1_SPECIALIST_SEED_COUNT = 50  (seeds 42..91)
    - V1_SPECIALIST_OPTUNA_TRIALS = 30  (n_trials per study)
    - ENSEMBLE_SIZE = 1 (per study; bagging at seed level, NOT inner ensemble)
    - max_depth = 5 FIXED (removed from Optuna search; set in lgbm.py specialist path)
    - num_leaves = 31 FIXED (LightGBM default; removed from Optuna search)
    - min_child_samples REMOVED from search space (uses LGBM default 20)
    - n_estimators upper bound = 500 (wall-clock mitigation, per brief Section 3.6)
    - n_startup_trials = 10 (TPE warmup reduction; per brief Section 3.6)
    - Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED)
    - Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    - atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; UNCHANGED from /064)
    - Aggregator: mean-of-signed-weights across 50 seeds
    - FEATURES_BASE_HASH_48COL = same as /064 (48-col hash; NO parquet regeneration)

Axis wiring (brief Section 3.1):
    (a) This runner: clone of run_iteration_064.py with ITERATION_LABEL='v1-074'
        + four new kwargs to LightGbmStrategy.
    (b) Dispatch branch: 'elif iteration_label == "v1-074"' in run_baseline_v1.py,
        identical to 'v1-064' except for the four new veto kwargs.
    (c) Implementation: LightGbmStrategy.get_signal → _apply_mid_bull_short_veto()
        applied after aggregator, before R3 OOD / R5 vol-target.
    (d) Engine parity: engine.py:_tick mirrors the veto at the same call-site
        (byte-equivalent ret_270b computation; same band edges; per Critic Check 15).

R1 EXCLUDED per catalog rule (skill commit f81cafc3):
    R1 streak-cooldown is CATALOG-CLOSED for SPECIALIST_mode.
    AXIS-R is at a different layer (post-aggregator direction veto; NOT streak-conditional).

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    V1_SPECIALIST_SEED_COUNT = 50
    V1_SPECIALIST_OPTUNA_TRIALS = 30
    V1_SPECIALIST_SEEDS = tuple(range(42, 92))
    AXIS-R band edges: [0.20, 0.50] (pre-registered; NOT re-fittable post-hoc)
    AXIS-R lookback: 270 8h candles (= 90 calendar days)

No parquet regeneration required:
    V1_FEATURE_COLUMNS_PRUNED is 48 cols (UNCHANGED from /061 closeout).
    AXIS-R veto is post-aggregator; does NOT touch features or training distribution.

Features-base-hash (48 cols; UNCHANGED from /064):
    b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3

Wall-clock projection (brief Section 0.5):
    AXIS-R adds zero training-time overhead (post-aggregator deterministic filter).
    Expected wall-clock ≈ /064's wall-clock (~8-9h).
    2h hard cap per feedback_v1_confirmation_walltime_9h.md EXPLORATION default.
    Kill-switch: abort if wall-clock > 2.5h OR IS trade count diverges by >10%
                 from expected (198 − 32 veto = ~166 ± 17, so 149-183).

Invocation:
    # Default SPECIALIST run (50 seeds × 30 trials, ETH only):
    uv run python run_iteration_074.py

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_074.py --check-hash

Output paths:
    reports-v1/iteration_v1-074/in_sample/
    reports-v1/iteration_v1-074/out_of_sample/
    reports-v1/iteration_v1-074/comparison.csv
    reports-v1/iteration_v1-074/in_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-074/out_of_sample/specialist_dispersion.csv
    reports-v1/iteration_v1-074/optuna_best_params.csv
    reports-v1/iteration_v1-074/run.log

F-AXIS verdict framework (brief Section 4):
    F-AXIS #1 (IS Δ vs /064 anchor IS +0.2383):
        IS ≥ +0.37 (Δ ≥ +0.13) → SPECIALIST-PROMISING (ETH-IMPROVED-V3 enters BUNDLE-002 roster)
        +0.29 ≤ IS < +0.37 (+0.05 ≤ Δ < +0.13) → PROMISING-MARGINAL (TENTATIVE-POSITIVE)
        +0.19 ≤ IS < +0.29 (−0.05 ≤ Δ < +0.05) → INERT (strike NOT consumed)
        IS < +0.19 (Δ < −0.05) → NEG-1st-STRIKE (ETH STRIKE-1 fires)
        IS < −0.10 (Δ < −0.34) → Catastrophic + MULTI-SEED MANDATE TRIGGER
    F-AXIS #2 (cross-seed dispersion; UNCHANGED from /064 expected; INFORMATIONAL)
    F-AXIS #3 (OOS Sharpe; INFORMATIONAL ONLY)
    F-AXIS-BEHAVIORAL (IS trade count; expected ~166 ± 17)
    F-AXIS-FALSIFIER (per-trade Sharpe lift ≥ +0.10 AND no single month >40% of lift)
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

# Pre-registered 48-col hash (UNCHANGED from /061 closeout / /064).
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-074"
ITERATION_NUMBER: int = 74

# Pre-registered AXIS-R band edges (HARD — anti-tuning; brief commit SHA is freeze ref).
AXIS_R_VETO_LO: float = 0.20  # mid_bull_short_veto_lo (FROZEN at brief authoring)
AXIS_R_VETO_HI: float = 0.50  # mid_bull_short_veto_hi (FROZEN at brief authoring)
AXIS_R_VETO_LOOKBACK: int = 270  # 270 8h candles = 90 calendar days (FROZEN)


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 48-col hash."""
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/074] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected} (48-col; UNCHANGED from /061 closeout / /064)\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/074] ABORT: feature column set does not match pre-registered 48-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/074 (no feature add/drop). "
            "AXIS-R is a post-aggregator rule-layer only — it does NOT change the feature stack."
        )
    print(
        f"[iter-v1/074] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; UNCHANGED from /061 closeout / /064)"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/074 SPECIALIST-IMPROVEMENT-V3 runner: "
            f"ETHUSDT 50-seed independent-Optuna bagging + AXIS-R Mid-Bull SHORT VETO "
            f"(V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}, "
            f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}, "
            f"specialist_mode=True; SINGLE-BIT deviation from /064; "
            f"enable_mid_bull_short_veto=True lo={AXIS_R_VETO_LO} hi={AXIS_R_VETO_HI} "
            f"lookback={AXIS_R_VETO_LOOKBACK})"
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
            f"[iter-v1/074] --check-hash mode. "
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
        print("  cohort                 : ETHUSDT only (V1_ITER074_UNIVERSE)")
        print("  model                  : Model_A_ETH_specialist_074 (R1=OFF, R2=OFF, R3=ON-SHD)")
        print("  max_depth              : 5 (FIXED)")
        print("  num_leaves             : 31 (FIXED; LightGBM default)")
        print("  min_child_samples      : REMOVED from search (LGBM default 20)")
        print("  n_estimators_max       : 500 (wall-clock mitigation)")
        print("  n_startup_trials       : 10 (wall-clock mitigation)")
        print("  atr_tp_multiplier      : 2.9 (Model A ETH cell — UNCHANGED from /064)")
        print("  atr_sl_multiplier      : 1.45 (Model A ETH cell — UNCHANGED from /064)")
        print("  R1                     : OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3)")
        print("  R2                     : OFF (Model A baseline)")
        print("  R3                     : ON-SHARED cutoff=0.70 (UNCHANGED from /064)")
        print("  R5                     : ON vt_target_vol=0.3 vt_lookback_days=45")
        print("  aggregator             : mean-of-signed-weights across 50 seeds")
        print("  AXIS-R veto            : ENABLED (single-bit add over /064)")
        print(f"  AXIS-R band            : ret_270b ∈ [{AXIS_R_VETO_LO}, {AXIS_R_VETO_HI}]")
        print(f"  AXIS-R lookback        : {AXIS_R_VETO_LOOKBACK} 8h candles (= 90 calendar days)")
        print("  verdict framework      :")
        print("    F-AXIS #1 (IS Δ vs /064 IS +0.2383) — anchor /064 (NOT /073)")
        print("    F-AXIS #2 (σ_pop)      : INFORMATIONAL (expected ≈ /064 ± 10%)")
        print("    F-AXIS #3 (OOS Sharpe) : INFORMATIONAL ONLY")
        print(f"  48-col hash            : {FEATURES_BASE_HASH_48COL[:32]}...")
        return

    # --- Pre-flight assertions ---
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: expected 48 features (UNCHANGED from /064), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/074 (no feature add/drop). "
        "AXIS-R is post-aggregator only — it does NOT modify the feature stack."
    )
    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS length "
        f"{len(V1_SPECIALIST_SEEDS)} != V1_SPECIALIST_SEED_COUNT {V1_SPECIALIST_SEED_COUNT}."
    )
    assert V1_SPECIALIST_SEEDS[0] == 42, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[0] must be 42; "
        f"got {V1_SPECIALIST_SEEDS[0]}."
    )
    assert V1_SPECIALIST_SEEDS[-1] == 91, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: V1_SPECIALIST_SEEDS[-1] must be 91; "
        f"got {V1_SPECIALIST_SEEDS[-1]}."
    )
    # AXIS-R band-edge assertion (anti-tuning; edges must match brief pre-registration)
    assert AXIS_R_VETO_LO == 0.20, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: AXIS_R_VETO_LO must be 0.20 (pre-registered); "
        f"got {AXIS_R_VETO_LO}. Band edges are FROZEN at brief authoring."
    )
    assert AXIS_R_VETO_HI == 0.50, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: AXIS_R_VETO_HI must be 0.50 (pre-registered); "
        f"got {AXIS_R_VETO_HI}. Band edges are FROZEN at brief authoring."
    )
    assert AXIS_R_VETO_LOOKBACK == 270, (
        f"[iter-v1/074] PRE-FLIGHT FAIL: AXIS_R_VETO_LOOKBACK must be 270 (pre-registered); "
        f"got {AXIS_R_VETO_LOOKBACK}. Lookback is FROZEN at brief authoring."
    )

    print("=" * 70)
    print("iter-v1/074 — ETH-IMPROVED-V3 SPECIALIST (AXIS-R Mid-Bull SHORT VETO)")
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
    print("  cohort                     : ETHUSDT only (V1_ITER074_UNIVERSE)")
    print("  model                      : Model_A_ETH_specialist_074")
    print("  max_depth                  : 5 (FIXED — removed from Optuna search)")
    print("  num_leaves                 : 31 (FIXED — LightGBM default; removed from search)")
    print("  min_child_samples          : REMOVED from search space (LGBM default 20)")
    print("  n_estimators_max           : 500 (wall-clock mitigation)")
    print("  n_startup_trials           : 10 (wall-clock mitigation; TPE warmup reduction)")
    print("  R1=OFF (CATALOG-CLOSED; f81cafc3)  R2=OFF (Model A baseline)")
    print("  R3=ON-SHARED cutoff=0.70  R5=ON vt_target_vol=0.3")
    print("  atr_tp=2.9  atr_sl=1.45 (Model A ETH cell — UNCHANGED from /064)")
    print("  aggregator                 : mean-of-signed-weights across 50 seeds")
    print("  AXIS-R veto                : ENABLED (single-bit add over /064)")
    print(
        f"  AXIS-R band                : ret_270b ∈ [{AXIS_R_VETO_LO}, {AXIS_R_VETO_HI}] "
        f"(pre-registered; FROZEN at brief authoring)"
    )
    print(f"  AXIS-R lookback            : {AXIS_R_VETO_LOOKBACK} bars (270 × 8h = 90 days)")
    print("  anchor                     : /064 IS Sharpe +0.2383 (NOT /073)")
    print("  verdict F-AXIS #1          : IS Δ ≥ +0.13 (IS ≥ +0.37) = SPECIALIST-PROMISING")
    print("  verdict F-AXIS #2          : σ_pop INFORMATIONAL (expected ≈ /064 ± 10%)")
    print(f"  48-col hash                : {FEATURES_BASE_HASH_48COL[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # specialist-mode is signaled via iteration_label "v1-074" + symbols "ETHUSDT" dispatch.
    # The --pruned-features flag selects V1_FEATURE_COLUMNS_PRUNED (48 cols).
    # --specialist-mode is NOT a CLI flag on run_baseline_v1; the dispatch branch fires
    # from iteration_label=="v1-074" and wires specialist_mode=True to LightGbmStrategy.
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
    ]

    print(f"[iter-v1/074] sys.argv set: {sys.argv}")

    import run_baseline_v1 as _rbv1  # module at repo root

    _rbv1.main()


if __name__ == "__main__":
    main()
