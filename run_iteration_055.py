"""iter-v1/055 — ETH-only specialist: eth_vs_btc_ret_ratio_30 cross-asset feature.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/055 and verifies the features-base-hash
guard for the 48-column V1_FEATURE_COLUMNS_PRUNED (eth_vs_btc_ret_ratio_30 ADDED).

Axis:
    EXPLORATION (feature-family; cycle-6 EXPLORATION 10/10 FINAL).
    Cohort: ETHUSDT only (ETH-only specialist head; BTC loaded for cross-asset feature only).
    CHANGE vs /054:
        - eth_vs_btc_ret_ratio_30: ADDED to V1_FEATURE_COLUMNS_PRUNED (47 → 48 cols).
          Computation in cross_btc_v1.py (direct mirror of /050 dot_vs_btc_ret_ratio_30).
    V1_FEATURE_COLUMNS_PRUNED extended 47 → 48 cols.

ETH baseline:
    ETH IS Sharpe: -0.61 (pooled Model A; second-worst of 5 symbols).
    ETH IS trades: 145 (larger corpus than DOT 93 → cleaner Optuna basin expected).
    ETH OOS Sharpe: +0.07 (informational; near-flat; does NOT gate verdict).

Verdict bands (brief Section 4, F-AXIS #1):
    IS >= 0.00 (Δ >= +0.61) → SPECIALIST-CANDIDATE; pre-register /057 ETH multi-seed
    IS ∈ [-0.31, 0.00) (Δ ∈ [+0.30, +0.61)) → PARTIAL; pre-register /057 ETH multi-seed
    IS ∈ [-0.56, -0.31) (Δ ∈ [+0.05, +0.30)) → WEAK; no multi-seed; ETH stays pooled
    IS ∈ (-0.66, -0.56) (Δ ∈ (-0.05, +0.05)) → NEG-INERT; no signal added
    IS < -0.66 (Δ < -0.05) → NEG-CLEAN; eth_vs_btc_ret_ratio_30 reverted from pruned set
    IS trades < 50 → NEGATIVE-INSUFFICIENT-TRADES (regardless of IS Sharpe)

LM Master priors (lgbm_advisor.md Phase 4.5):
    SPECIALIST-CANDIDATE 35% (modal) + PARTIAL 30% = 65% positive prior.
    Driven by larger ETH corpus (145 vs DOT 93 IS trades) + proven mechanism from /050.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, ...)  (first 3 used for single-seed=42 inner pool)

Parquet regeneration required before running (BOTH BTCUSDT and ETHUSDT):
    uv run crypto-trade features --symbols BTCUSDT,ETHUSDT --interval 8h \\
        --track v1 --format parquet --workers 4
    Verify: eth_vs_btc_ret_ratio_30 present in ETHUSDT parquet with valid non-NaN values.
    Verify: eth_vs_btc_ret_ratio_30 is NaN for BTCUSDT parquet (ETH-only feature).

Features-base-hash:
    48-col hash: b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3
    47-col hash: f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56
    The hashes DIFFER (eth_vs_btc_ret_ratio_30 ADD changes the column set). This is expected.

Invocation:
    # Default (EXPLORATION mode, single-seed=42, n_trials=18, ensemble_size=3):
    uv run python run_iteration_055.py

    # Override n_trials:
    uv run python run_iteration_055.py --n-trials 35

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_055.py --check-hash

Output paths:
    reports-v1/iteration_v1-055/in_sample/
    reports-v1/iteration_v1-055/out_of_sample/
    reports-v1/iteration_v1-055/comparison.csv
    reports-v1/iteration_v1-055/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — fires the len==48 assertion
# in features_v1/__init__.py, confirming eth_vs_btc_ret_ratio_30 was ADDED.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

# Pre-registered 48-col hash (eth_vs_btc_ret_ratio_30 added; post-/055).
# Computed from: hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest()
# This hash DIFFERS from the /054 47-col hash (feature ADD → column set changed).
#
# To regenerate:
#   uv run python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   print(hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())
#   "
FEATURES_BASE_HASH_48COL: str = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"
FEATURES_BASE_HASH_47COL: str = "f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-055"
ITERATION_NUMBER: int = 55
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 1  # single-seed=42 (EXPLORATION budget; F-AXIS #1 ETH IS Sharpe Δ)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)

# Compute the live hash at import time (fires the len==48 assertion in __init__.py).
_LIVE_HASH = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _LIVE_HASH


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/055 EXPLORATION runner: "
            "ETH-only specialist (eth_vs_btc_ret_ratio_30 ADDED; "
            "V1_FEATURE_COLUMNS_PRUNED 47 → 48 cols; cycle-6 EXPLORATION 10/10 FINAL)"
        )
    )
    p.add_argument(
        "--n-trials",
        type=int,
        default=N_TRIALS_DEFAULT,
        help=f"Optuna trial budget per cell (default {N_TRIALS_DEFAULT}; EXPLORATION standard).",
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
            "Defaults to the pre-registered 48-col hash for iter-v1/055."
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
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 48-col hash.

    Exits with a non-zero status if the hash does not match.
    Provides a specific diagnosis if the hash matches the OLD 47-col set (missing ADD).
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual == FEATURES_BASE_HASH_47COL:
        print(
            f"[iter-v1/055] FEATURES-BASE-HASH MISMATCH — 47-col hash detected!\n"
            f"  actual   : {actual} (matches 47-col /054 hash)\n"
            f"  expected : {expected} (48-col /055 hash)\n"
            f"  DIAGNOSIS: eth_vs_btc_ret_ratio_30 was NOT added to V1_FEATURE_COLUMNS_PRUNED. "
            "Check src/crypto_trade/features_v1/__init__.py — the eth entry must be "
            "PRESENT (iter-v1/055 ADD).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/055] ABORT: V1_FEATURE_COLUMNS_PRUNED is still 47 cols "
            "(eth_vs_btc_ret_ratio_30 not added). The /055 feature-add did not take effect. "
            "Edit src/crypto_trade/features_v1/__init__.py to add "
            "eth_vs_btc_ret_ratio_30 to V1_FEATURE_COLUMNS_PRUNED."
        )
    if actual != expected:
        print(
            f"[iter-v1/055] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/055] ABORT: feature column set does not match pre-registered 48-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: uv run python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_48COL in run_iteration_055.py."
        )
    print(
        f"[iter-v1/055] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; eth_vs_btc_ret_ratio_30 ADDED)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/055] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  eth_vs_btc_ret_ratio_30 in pruned (must be TRUE):",
            "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(f"  Seeds: {SEEDS_DEFAULT} (single-seed=42; EXPLORATION cadence)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner)")
        print("  48-col hash:", FEATURES_BASE_HASH_48COL)
        print("  47-col hash (OLD /054 ref):", FEATURES_BASE_HASH_47COL)
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "eth_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/055] PRE-FLIGHT FAIL: eth_vs_btc_ret_ratio_30 is NOT in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "The /055 feature-add was not applied. "
        "Check src/crypto_trade/features_v1/__init__.py — add "
        "the eth_vs_btc_ret_ratio_30 entry."
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/055] PRE-FLIGHT FAIL: expected 48 features (47 + 1 eth_vs_btc_ret_ratio_30), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/055."
    )

    print("=" * 70)
    print("iter-v1/055 — ETH-only specialist (eth_vs_btc_ret_ratio_30 cross-asset feature)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {SEEDS_DEFAULT} (single-seed=42; EXPLORATION cadence)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; 47→48)")
    eth_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("eth_vs_btc_ret_ratio_30")
    print(
        f"  eth_vs_btc_ret_ratio_30    : index {eth_idx} of {n_cols} (ADDED; ETH-only specialist)"
    )
    print("  cohort                 : ETHUSDT only (V1_ITER055_UNIVERSE)")
    print("  model                  : A_ETH_specialist (R3=ON, R1=OFF, R2=OFF)")
    print("  verdict bands          :")
    print("    IS >= 0.00 (Δ >= +0.61) → SPECIALIST-CANDIDATE; pre-register /057 ETH multi-seed")
    print("    IS ∈ [-0.31, 0.00) (Δ ∈ [+0.30, +0.61)) → PARTIAL; pre-register /057 multi-seed")
    print("    IS ∈ [-0.56, -0.31) (Δ ∈ [+0.05, +0.30)) → WEAK; no multi-seed")
    print("    IS ∈ (-0.66, -0.56) (Δ ∈ (-0.05, +0.05)) → NEG-INERT; no signal")
    print("    IS < -0.66 (Δ < -0.05) → NEG-CLEAN; feature reverted")
    print("  trade-rate floor       : IS ≥ 50 AND OOS ≥ 10")
    print("  48-col hash            :", FEATURES_BASE_HASH_48COL[:32] + "...")
    print("  47-col hash (old ref)  :", FEATURES_BASE_HASH_47COL[:32] + "...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/055. The `--symbols ETHUSDT` argument
    # selects the ETH-only cohort (V1_ITER055_UNIVERSE).
    # `--seeds 1` activates single-seed mode (seed=42 inner pool [42, 123, 456]).
    sys.argv = [
        "run_baseline_v1.py",
        "--exploration",
        "--iteration",
        str(ITERATION_NUMBER),
        "--n-trials",
        str(args.n_trials),
        "--seeds",
        str(SEEDS_DEFAULT),
        "--ensemble-size",
        str(ENSEMBLE_SIZE),
        "--pruned-features",
        "--symbols",
        "ETHUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    # No _OUTER_SEED_OFFSETS patch needed — single-seed=42 uses the default offset (0).
    run_baseline_v1.main()


if __name__ == "__main__":
    main()
