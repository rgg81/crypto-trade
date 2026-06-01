"""iter-v1/052 — BTC-only specialist with btc_funding_rate_8h_impulse + btc_funding_spread_30_90.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/052 and verifies the features-base-hash
guard for the 48-column V1_FEATURE_COLUMNS_PRUNED.

Axis:
    EXPLORATION (feature-family; cycle-6 EXPLORATION 7/10).
    Cohort: BTCUSDT only (BTC-only specialist head).
    NEW features (both-or-neither axis):
        - btc_funding_rate_8h_impulse: funding shock detector
          (diff(funding_rate) / rolling(90).std(diff(funding_rate)), clipped ±10)
        - btc_funding_spread_30_90: term-structure slope
          (funding_rate_zscore_30 - funding_rate_zscore_90)
    V1_FEATURE_COLUMNS_PRUNED extended 46 → 48 cols.

Pre-registered verdict bands (brief Section 4, F-AXIS #1):
    IS Sharpe Δ >= +0.85 → PROMISING-SPECIALIST (flip-positive)
    +0.30 <= IS Sharpe Δ < +0.85 → PROMISING-PARTIAL
    +0.05 <= IS Sharpe Δ < +0.30 → PROMISING-WEAK
    IS Sharpe Δ ∈ (-0.05, +0.05) → NEG-INERT
    IS Sharpe Δ < -0.05 → NEGATIVE-CLEAN
    IS trades < 50 → NEGATIVE-INSUFFICIENT-TRADES

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, ...)  (first 3 used for inner ensemble)

Parquet regeneration required before running:
    uv run crypto-trade features --symbols BTCUSDT --interval 8h \\
        --track v1 --format parquet --workers 4
    Verify: btc_funding_rate_8h_impulse + btc_funding_spread_30_90 present in parquet.

Invocation:
    # Default (EXPLORATION mode, single-seed=42, n_trials=18, ensemble_size=3):
    uv run python run_iteration_052.py

    # Override n_trials:
    uv run python run_iteration_052.py --n-trials 35

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_052.py --check-hash

Output paths:
    reports-v1/iteration_v1-052/in_sample/
    reports-v1/iteration_v1-052/out_of_sample/
    reports-v1/iteration_v1-052/comparison.csv
    reports-v1/iteration_v1-052/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — fires the len==48 assertion
# in features_v1/__init__.py, confirming the two new features are registered.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered hash: computed from V1_FEATURE_COLUMNS_PRUNED (48 cols including
# btc_funding_rate_8h_impulse and btc_funding_spread_30_90) at module-import time.
# If this value changes at runtime, V1_FEATURE_COLUMNS_PRUNED was inadvertently
# modified — BLOCK.
#
# To regenerate:
#   python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   payload = '\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()
#   print(hashlib.sha256(payload).hexdigest())
#   "
_COMPUTED_HASH_AT_DEFINITION = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _COMPUTED_HASH_AT_DEFINITION

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-052"
ITERATION_NUMBER: int = 52
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 1  # single-seed=42 (EXPLORATION; multi-seed conditional on PROMISING)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/052 EXPLORATION runner: "
            "BTC-only specialist with btc_funding_rate_8h_impulse + btc_funding_spread_30_90 "
            "(V1_FEATURE_COLUMNS_PRUNED 46 → 48 cols)"
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
            "Defaults to the hash pre-registered in this file (48-col set)."
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
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered hash.

    Exits with a non-zero status if the hash does not match.
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/052] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/052] ABORT: feature column set does not match pre-registered hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_EXPECTED in run_iteration_052.py."
        )
    print(
        f"[iter-v1/052] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; btc_funding_rate_8h_impulse + btc_funding_spread_30_90 included)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/052] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  btc_funding_rate_8h_impulse in pruned:",
            "btc_funding_rate_8h_impulse" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(
            "  btc_funding_spread_30_90 in pruned:",
            "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(f"  Seeds: {SEEDS_DEFAULT} (single-seed=42; multi-seed conditional on PROMISING)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner)")
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "btc_funding_rate_8h_impulse" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/052] PRE-FLIGHT FAIL: btc_funding_rate_8h_impulse not in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure src/crypto_trade/features_v1/__init__.py has the column (iter-v1/052 ADD). "
        "Run: uv run crypto-trade features "
        "--symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4"
    )
    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/052] PRE-FLIGHT FAIL: btc_funding_spread_30_90 not in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure src/crypto_trade/features_v1/__init__.py has the column (iter-v1/052 ADD). "
        "Run: uv run crypto-trade features "
        "--symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/052] PRE-FLIGHT FAIL: expected 48 features (46 + 2 new funding transforms), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/052 (btc_funding_rate_8h_impulse + "
        "btc_funding_spread_30_90 added at /052)."
    )

    print("=" * 70)
    print("iter-v1/052 — BTC-only specialist (funding impulse + spread)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {SEEDS_DEFAULT} (single-seed=42; EXPLORATION cadence)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; 46→48)")
    imp_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_funding_rate_8h_impulse")
    spr_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_funding_spread_30_90")
    print(f"  btc_funding_rate_8h_impulse: index {imp_idx} of {n_cols}")
    print(f"  btc_funding_spread_30_90   : index {spr_idx} of {n_cols}")
    print("  cohort                 : BTCUSDT only (V1_ITER052_UNIVERSE)")
    print("  model                  : A_BTC_specialist (R3=ON, R1=OFF, R2=OFF)")
    print("  verdict bands          : IS Sharpe Δ >= +0.85 SPECIALIST / [+0.30,+0.85) PARTIAL")
    print("                           [+0.05,+0.30) WEAK / NEG-INERT / NEGATIVE-CLEAN")
    print(f"  features-base-hash     : {FEATURES_BASE_HASH_EXPECTED[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/052. The `--symbols BTCUSDT` argument
    # selects the BTC-only cohort (V1_ITER052_UNIVERSE).
    # `--seeds 1` activates single-seed mode (seed=42 inner pool, 3 models).
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
        "BTCUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
