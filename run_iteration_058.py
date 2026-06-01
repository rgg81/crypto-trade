"""iter-v1/058 — BTC-only specialist: btc_oi_delta_5_z30 short-window OI feature.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/058 and verifies the features-base-hash
guard for the 49-column V1_FEATURE_COLUMNS_PRUNED (btc_oi_delta_5_z30 ADDED).

Axis:
    EXPLORATION (feature-family; cycle-7 EXPLORATION 2/N).
    Cohort: BTCUSDT only (BTC-only specialist head).
    CHANGE vs /057:
        - btc_oi_delta_5_z30: ADDED to V1_FEATURE_COLUMNS_PRUNED (48 → 49 cols).
          Computation: (open_interest[t] - open_interest[t-5]) / open_interest[t-5],
          z-scored over 30 bars (10-day window). Short-window companion to oi_delta_30_z90
          (5-bar delta at 40h vs 30-bar delta at 240h). Targets rapid BTC institutional
          positioning shifts not captured by the slower accumulation window.

BTC baseline:
    BTC IS Sharpe: −0.85 (pooled Model A; biggest IS-headroom in the bundle).
    BTC IS trades: 113 (smallest specialist cohort; higher per-seed variance expected).
    BTC OOS Sharpe: +3.41 (structurally positive OOS; IS is the weak link).

Mandate:
    /057 BASIN-LOTTERY (ltc_vs_btc_ret_ratio_30 max-min spread 0.67 > 0.50 threshold).
    Pivot to OI-delta family (axis-adjacent to existing oi_delta_30_z90; different
    frequency bin: 5-bar/40h vs 30-bar/240h).

Multi-seed design (built-in from start; per /056 + /057 basin-lottery lessons):
    --seeds 3 at ensemble_size=3, _OUTER_SEED_OFFSETS=(0,3,6)
    → 9 disjoint inner seeds: [42,123,456] / [789,1001,2002] / [3003,4004,5005]
    Verdict basis: MULTI-SEED MEAN (n=3 outer seeds).
    Single-seed=42 result is informational only — cannot determine verdict.

Verdict bands (brief Section 4; multi-seed MEAN IS Δ vs BTC baseline −0.85):
    Mean IS Δ ≥ +0.50 → MULTI-SEED-SPECIALIST-CANDIDATE; pre-register cycle-7 CONFIRMATION
    Mean IS Δ ∈ [+0.20, +0.50) → MULTI-SEED-PARTIAL-CONFIRMED; pre-register cycle-7 CONFIRMATION
    Mean IS Δ ∈ [+0.05, +0.20) → MULTI-SEED-WEAK; no CONFIRMATION; BTC stays pooled
    Mean IS Δ ∈ (-0.05, +0.05) → NEG-INERT; feature stays in pruned set (informational)
    Mean IS Δ < -0.05 → NEG-CLEAN; btc_oi_delta_5_z30 reverted from pruned set
    Max-min spread > 0.50 → BASIN-LOTTERY downgrade (overrides Sharpe band)

Stability gate: max-min IS Sharpe ≤ 0.50 = PASS; > 0.50 = BASIN-LOTTERY.

LM Master priors (lgbm_advisor.md Phase 4.5):
    NEG-INERT (25%, modal) + MULTI-SEED-WEAK (25%).
    Sister-IC with oi_delta_30_z90 at |IC| ≈ 0.30–0.55 may route splits to established 30-bar
    version; 5-bar starved. OR: frequency-bin diversity adds mid-table importance (PARTIAL/WEAK).

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, ...)  (first 3 per outer seed)

Parquet regeneration required before running:
    uv run crypto-trade features --symbols BTCUSDT --interval 8h \\
        --track v1 --format parquet --workers 4
    Verify: btc_oi_delta_5_z30 present in BTCUSDT parquet with valid non-NaN values
    after 35-bar burn-in.

Features-base-hash:
    49-col hash:
        653b55c87d8f98e98742a5d85b65cdd1ba9a2227fc52e2df09d7d98d8a0fbc8d (btc_oi_delta_5_z30 ADDED)
    48-col hash (OLD /057 closeout ref):
        b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3
    The hashes DIFFER (btc_oi_delta_5_z30 ADD changes the column set). This is expected.

Invocation:
    # Default (EXPLORATION mode, multi-seed n=3, n_trials=18, ensemble_size=3):
    uv run python run_iteration_058.py

    # Override n_trials:
    uv run python run_iteration_058.py --n-trials 20

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_058.py --check-hash

Output paths:
    reports-v1/iteration_v1-058/seed_42/
    reports-v1/iteration_v1-058/seed_offset3/
    reports-v1/iteration_v1-058/seed_offset6/
    reports-v1/iteration_v1-058/comparison_multi_seed.csv
    reports-v1/iteration_v1-058/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — fires the len==49 assertion
# in features_v1/__init__.py, confirming btc_oi_delta_5_z30 was ADDED.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

# Pre-registered 49-col hash (btc_oi_delta_5_z30 added; post-/058).
# Computed from: hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest()
# This hash DIFFERS from the /057 closeout 48-col hash (feature ADD → column set changed).
#
# To regenerate:
#   uv run python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   print(hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())
#   "
FEATURES_BASE_HASH_49COL: str = "653b55c87d8f98e98742a5d85b65cdd1ba9a2227fc52e2df09d7d98d8a0fbc8d"
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-058"
ITERATION_NUMBER: int = 58
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 3  # 3 outer seeds: offsets 0, 3, 6 (built-in multi-seed)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)

# _OUTER_SEED_OFFSETS monkey-patch (mirrors /057 + /053 + /051 pattern):
# Patched into run_baseline_v1._OUTER_SEED_OFFSETS BEFORE calling main().
# (0, 3, 6) → inner windows [42,123,456] / [789,1001,2002] / [3003,4004,5005]
# These are fully disjoint across all 3 outer seeds.
_OUTER_SEED_OFFSETS_PATCH: tuple[int, ...] = (0, 3, 6)

# Compute the live hash at import time (fires the len==49 assertion in __init__.py).
_LIVE_HASH = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _LIVE_HASH


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/058 EXPLORATION runner: "
            "BTC-only specialist (btc_oi_delta_5_z30 ADDED; "
            "V1_FEATURE_COLUMNS_PRUNED 48 → 49 cols; cycle-7 EXPLORATION 2/N; "
            "multi-seed built-in: --seeds 3)"
        )
    )
    p.add_argument(
        "--n-trials",
        type=int,
        default=N_TRIALS_DEFAULT,
        help=f"Optuna trial budget per cell (default {N_TRIALS_DEFAULT}; EXPLORATION standard).",
    )
    p.add_argument(
        "--seeds",
        type=int,
        default=SEEDS_DEFAULT,
        help=(
            f"Number of outer seeds (default {SEEDS_DEFAULT}). "
            "Uses _OUTER_SEED_OFFSETS=(0,3,6) → "
            "seed_42 / seed_offset3 / seed_offset6. "
            "Multi-seed is MANDATORY for verdict basis; single-seed=42 is informational only."
        ),
    )
    p.add_argument(
        "--features-base-hash",
        type=str,
        default=None,
        dest="features_base_hash",
        metavar="SHA256",
        help=(
            "Expected SHA-256 of V1_FEATURE_COLUMNS_PRUNED (sorted). "
            "If provided, the runner aborts if the live hash does not match. "
            "Defaults to the pre-registered 49-col hash for iter-v1/058."
        ),
    )
    p.add_argument(
        "--check-hash",
        action="store_true",
        default=False,
        help="Print the features-base-hash and exit (dry-run; no backtest launched).",
    )
    return p.parse_args()


def _verify_features_hash(expected: str) -> None:
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 49-col hash.

    Exits with a non-zero status if the hash does not match.
    Provides a specific diagnosis if the hash matches the OLD 48-col set (missing ADD).
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual == FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/058] FEATURES-BASE-HASH MISMATCH — 48-col hash detected!\n"
            f"  actual   : {actual} (matches 48-col /057-closeout hash)\n"
            f"  expected : {expected} (49-col /058 hash)\n"
            f"  DIAGNOSIS: btc_oi_delta_5_z30 was NOT added to V1_FEATURE_COLUMNS_PRUNED. "
            "Check src/crypto_trade/features_v1/__init__.py — the btc_oi_delta_5_z30 entry "
            "must be PRESENT (iter-v1/058 ADD).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/058] ABORT: V1_FEATURE_COLUMNS_PRUNED is still 48 cols "
            "(btc_oi_delta_5_z30 not added). The /058 feature-add did not take effect. "
            "Edit src/crypto_trade/features_v1/__init__.py to add "
            "btc_oi_delta_5_z30 to V1_FEATURE_COLUMNS_PRUNED."
        )
    if actual != expected:
        print(
            f"[iter-v1/058] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/058] ABORT: feature column set does not match pre-registered 49-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: uv run python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_49COL in run_iteration_058.py."
        )
    print(
        f"[iter-v1/058] features-base-hash PASS: {actual[:16]}... "
        f"(49 columns; btc_oi_delta_5_z30 ADDED)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/058] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  btc_oi_delta_5_z30 in pruned (must be TRUE):",
            "btc_oi_delta_5_z30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(f"  Seeds: {args.seeds} outer seeds (offsets 0,3,6; multi-seed built-in)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner)")
        print("  49-col hash:", FEATURES_BASE_HASH_49COL)
        print("  48-col hash (OLD /057-closeout ref):", FEATURES_BASE_HASH_48COL)
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "btc_oi_delta_5_z30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/058] PRE-FLIGHT FAIL: btc_oi_delta_5_z30 is NOT in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "The /058 feature-add was not applied. "
        "Check src/crypto_trade/features_v1/__init__.py — add "
        "the btc_oi_delta_5_z30 entry."
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 49, (
        f"[iter-v1/058] PRE-FLIGHT FAIL: expected 49 features (48 + 1 btc_oi_delta_5_z30), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 49 at iter-v1/058."
    )
    assert args.seeds >= 1, f"[iter-v1/058] PRE-FLIGHT FAIL: --seeds must be >= 1, got {args.seeds}"

    print("=" * 70)
    print("iter-v1/058 — BTC-only specialist (btc_oi_delta_5_z30 short-window OI feature)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(
        f"  outer seeds            : {args.seeds} "
        f"(offsets 0,3,6 ENSEMBLE_SEEDS; 3x3=9 disjoint inner seeds)"
    )
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; 48→49)")
    oi5_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_oi_delta_5_z30")
    print(f"  btc_oi_delta_5_z30     : index {oi5_idx} of {n_cols} (ADDED; BTC OI short-window)")
    print("  cohort                 : BTCUSDT only (V1_ITER058_UNIVERSE)")
    print("  model                  : A_BTC_specialist (R1=OFF, R2=OFF, R3=ON)")
    print("  verdict bands          :")
    print("    Mean IS Δ ≥ +0.50 → MULTI-SEED-SPECIALIST-CANDIDATE")
    print("    Mean IS Δ ∈ [+0.20, +0.50) → MULTI-SEED-PARTIAL-CONFIRMED")
    print("    Mean IS Δ ∈ [+0.05, +0.20) → MULTI-SEED-WEAK")
    print("    Mean IS Δ ∈ (-0.05, +0.05) → NEG-INERT")
    print("    Mean IS Δ < -0.05 → NEG-CLEAN; feature reverted")
    print("    Max-min spread > 0.50 → BASIN-LOTTERY downgrade")
    print("  trade-rate floor       : IS ≥ 50 per seed (mean), OOS ≥ 10 (mean)")
    print("  49-col hash            :", FEATURES_BASE_HASH_49COL[:32] + "...")
    print("  48-col hash (old ref)  :", FEATURES_BASE_HASH_48COL[:32] + "...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/058. The `--symbols BTCUSDT` argument
    # selects the BTC-only cohort (V1_ITER058_UNIVERSE).
    # `--seeds N` activates the multi-seed framework loop in run_baseline_v1.
    sys.argv = [
        "run_baseline_v1.py",
        "--exploration",
        "--iteration",
        str(ITERATION_NUMBER),
        "--n-trials",
        str(args.n_trials),
        "--ensemble-size",
        str(ENSEMBLE_SIZE),
        "--symbols",
        "BTCUSDT",
        "--pruned-features",
        "--seeds",
        str(args.seeds),
    ]

    # --- Apply _OUTER_SEED_OFFSETS monkey-patch ---
    # run_baseline_v1._OUTER_SEED_OFFSETS is (0,5,10,15,20) by default.
    # Patch it to (0,3,6) before calling main() — same as /057, /053, /051 pattern.
    # (0,3,6) → inner pools [42,123,456] / [789,1001,2002] / [3003,4004,5005]
    # fully disjoint from each other.
    import run_baseline_v1

    run_baseline_v1._OUTER_SEED_OFFSETS = _OUTER_SEED_OFFSETS_PATCH

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
