"""iter-v1/057 — LTC-only specialist: ltc_vs_btc_ret_ratio_30 cross-asset feature.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/057 and verifies the features-base-hash
guard for the 49-column V1_FEATURE_COLUMNS_PRUNED (ltc_vs_btc_ret_ratio_30 ADDED).

Axis:
    EXPLORATION (feature-family; cycle-7 EXPLORATION 1/N).
    Cohort: LTCUSDT only (LTC-only specialist head; BTC loaded for cross-asset feature only).
    CHANGE vs /056:
        - ltc_vs_btc_ret_ratio_30: ADDED to V1_FEATURE_COLUMNS_PRUNED (48 → 49 cols).
          Computation in cross_btc_v1.py (direct mirror of /055 eth_vs_btc_ret_ratio_30).
    V1_FEATURE_COLUMNS_PRUNED extended 48 → 49 cols.

LTC baseline:
    LTC IS Sharpe: +0.17 (pooled Model D; biggest IS/OOS divergence).
    LTC IS trades: 124 (smaller than ETH 145; higher per-seed variance expected).
    LTC OOS Sharpe: -4.27 (catastrophic; largest OOS drag in the bundle).

Multi-seed design (built-in from start; per /056 Phase 7.4 Rec A):
    --seeds 3 at ensemble_size=3, _OUTER_SEED_OFFSETS=(0,3,6)
    → 9 disjoint inner seeds: [42,123,456] / [789,1001,2002] / [3003,4004,5005]
    Verdict basis: MULTI-SEED MEAN (n=3 outer seeds).
    Single-seed=42 result is informational only — cannot determine verdict.

Verdict bands (brief Section 4, F-AXIS #1; MULTI-SEED MEAN):
    Mean IS Δ ≥ +0.50 → MULTI-SEED-SPECIALIST-CANDIDATE; pre-register cycle-7 CONFIRMATION
    Mean IS Δ ∈ [+0.20, +0.50) → MULTI-SEED-PARTIAL-CONFIRMED; pre-register cycle-7 CONFIRMATION
    Mean IS Δ ∈ [+0.05, +0.20) → MULTI-SEED-WEAK; no CONFIRMATION; LTC stays pooled
    Mean IS Δ ∈ (-0.05, +0.05) → NEG-INERT; no signal; feature stays in pruned
    Mean IS Δ < -0.05 → NEG-CLEAN; ltc_vs_btc_ret_ratio_30 reverted from pruned set
    Max-min spread > 0.50 → BASIN-LOTTERY downgrade (even if mean meets band)

LM Master priors (lgbm_advisor.md Phase 4.5):
    MULTI-SEED-PARTIAL-CONFIRMED 25% (modal) + NEG-INERT 25%.
    Bimodal: mechanism is sound but LTC's smaller IS cohort (124 trades) introduces noise.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, ...)  (first 3 per outer seed)

Parquet regeneration required before running (BOTH BTCUSDT and LTCUSDT):
    uv run crypto-trade features --symbols BTCUSDT,LTCUSDT --interval 8h \\
        --track v1 --format parquet --workers 4
    Verify: ltc_vs_btc_ret_ratio_30 present in LTCUSDT parquet with valid non-NaN values.
    Verify: ltc_vs_btc_ret_ratio_30 is NaN for BTCUSDT parquet (LTC-only feature).

Features-base-hash:
    49-col hash: 921227a877c7287baf423cefbe5155a342428ce7813ac82d5a7d7f01ab3ff035
    48-col hash: b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3
    The hashes DIFFER (ltc_vs_btc_ret_ratio_30 ADD changes the column set). This is expected.

Invocation:
    # Default (EXPLORATION mode, multi-seed n=3, n_trials=18, ensemble_size=3):
    uv run python run_iteration_057.py

    # Override n_trials:
    uv run python run_iteration_057.py --n-trials 20

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_057.py --check-hash

Output paths:
    reports-v1/iteration_v1-057/seed_42/
    reports-v1/iteration_v1-057/seed_offset3/
    reports-v1/iteration_v1-057/seed_offset6/
    reports-v1/iteration_v1-057/comparison_multi_seed.csv
    reports-v1/iteration_v1-057/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — fires the len==49 assertion
# in features_v1/__init__.py, confirming ltc_vs_btc_ret_ratio_30 was ADDED.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

# Pre-registered 49-col hash (ltc_vs_btc_ret_ratio_30 added; post-/057).
# Computed from: hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest()
# This hash DIFFERS from the /056 48-col hash (feature ADD → column set changed).
#
# To regenerate:
#   uv run python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   print(hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())
#   "
FEATURES_BASE_HASH_49COL: str = "921227a877c7287baf423cefbe5155a342428ce7813ac82d5a7d7f01ab3ff035"
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-057"
ITERATION_NUMBER: int = 57
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 3  # 3 outer seeds: offsets 0, 3, 6 (built-in multi-seed)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)

# _OUTER_SEED_OFFSETS monkey-patch (mirrors /051 pattern):
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
            "iter-v1/057 EXPLORATION runner: "
            "LTC-only specialist (ltc_vs_btc_ret_ratio_30 ADDED; "
            "V1_FEATURE_COLUMNS_PRUNED 48 → 49 cols; cycle-7 EXPLORATION 1/N; "
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
            "Defaults to the pre-registered 49-col hash for iter-v1/057."
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
            f"[iter-v1/057] FEATURES-BASE-HASH MISMATCH — 48-col hash detected!\n"
            f"  actual   : {actual} (matches 48-col /056 hash)\n"
            f"  expected : {expected} (49-col /057 hash)\n"
            f"  DIAGNOSIS: ltc_vs_btc_ret_ratio_30 was NOT added to V1_FEATURE_COLUMNS_PRUNED. "
            "Check src/crypto_trade/features_v1/__init__.py — the ltc entry must be "
            "PRESENT (iter-v1/057 ADD).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/057] ABORT: V1_FEATURE_COLUMNS_PRUNED is still 48 cols "
            "(ltc_vs_btc_ret_ratio_30 not added). The /057 feature-add did not take effect. "
            "Edit src/crypto_trade/features_v1/__init__.py to add "
            "ltc_vs_btc_ret_ratio_30 to V1_FEATURE_COLUMNS_PRUNED."
        )
    if actual != expected:
        print(
            f"[iter-v1/057] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/057] ABORT: feature column set does not match pre-registered 49-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: uv run python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_49COL in run_iteration_057.py."
        )
    print(
        f"[iter-v1/057] features-base-hash PASS: {actual[:16]}... "
        f"(49 columns; ltc_vs_btc_ret_ratio_30 ADDED)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/057] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  ltc_vs_btc_ret_ratio_30 in pruned (must be TRUE):",
            "ltc_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(f"  Seeds: {args.seeds} outer seeds (offsets 0,3,6; multi-seed built-in)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner)")
        print("  49-col hash:", FEATURES_BASE_HASH_49COL)
        print("  48-col hash (OLD /056 ref):", FEATURES_BASE_HASH_48COL)
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "ltc_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/057] PRE-FLIGHT FAIL: ltc_vs_btc_ret_ratio_30 is NOT in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "The /057 feature-add was not applied. "
        "Check src/crypto_trade/features_v1/__init__.py — add "
        "the ltc_vs_btc_ret_ratio_30 entry."
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 49, (
        f"[iter-v1/057] PRE-FLIGHT FAIL: expected 49 features (48 + 1 ltc_vs_btc_ret_ratio_30), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 49 at iter-v1/057."
    )
    assert args.seeds >= 1, f"[iter-v1/057] PRE-FLIGHT FAIL: --seeds must be >= 1, got {args.seeds}"

    print("=" * 70)
    print("iter-v1/057 — LTC-only specialist (ltc_vs_btc_ret_ratio_30 cross-asset feature)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(
        f"  outer seeds            : {args.seeds} "
        f"(offsets 0,3,6 ENSEMBLE_SEEDS; 3x3=9 disjoint inner seeds)"
    )
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; 48→49)")
    ltc_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("ltc_vs_btc_ret_ratio_30")
    print(f"  ltc_vs_btc_ret_ratio_30: index {ltc_idx} of {n_cols} (ADDED; LTC-only specialist)")
    print("  cohort                 : LTCUSDT only (V1_ITER057_UNIVERSE)")
    print("  model                  : D_LTC_specialist (R1=ON K=3/C=27, R2=OFF, R3=ON)")
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
    # EXPLORATION arguments for iter-v1/057. The `--symbols LTCUSDT` argument
    # selects the LTC-only cohort (V1_ITER057_UNIVERSE).
    # `--seeds N` activates the multi-seed framework loop in run_baseline_v1.
    sys.argv = [
        "run_baseline_v1.py",
        "--exploration",
        "--iteration",
        str(ITERATION_NUMBER),
        "--n-trials",
        str(args.n_trials),
        "--seeds",
        str(args.seeds),
        "--ensemble-size",
        str(ENSEMBLE_SIZE),
        "--pruned-features",
        "--symbols",
        "LTCUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    # iter-v1/057 scope-limited offset override: disjoint outer seeds at ENSEMBLE_SIZE=3.
    # Framework default (0,5,10,15,20) silently skips offset 10 because 10+3>10 (len=10);
    # (0,3,6) gives three fully-disjoint windows: [42,123,456], [789,1001,2002], [3003,4004,5005].
    # DO NOT change run_baseline_v1._OUTER_SEED_OFFSETS in the framework file — this patch
    # is scope-limited to this runner module only.
    # Mirrors the /051 pattern exactly (same offsets, same ensemble_size=3).
    run_baseline_v1._OUTER_SEED_OFFSETS = _OUTER_SEED_OFFSETS_PATCH

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
