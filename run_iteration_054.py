"""iter-v1/054 — BTC-only impulse-drop test: spread-alone IS attribution.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/054 and verifies the features-base-hash
guard for the 47-column V1_FEATURE_COLUMNS_PRUNED (btc_funding_rate_8h_impulse DROPPED).

Axis:
    EXPLORATION (feature-pruning sub-axis; cycle-6 EXPLORATION 9/10).
    Cohort: BTCUSDT only (BTC-only specialist head; unchanged from /052-/053).
    CHANGE vs /052-/053:
        - btc_funding_rate_8h_impulse: DROPPED from V1_FEATURE_COLUMNS_PRUNED (48 → 47).
          Computation code preserved in funding_v1.py (restore path for /055 if needed).
        - btc_funding_spread_30_90: RETAINED (rank 4-10/48 STABLE in 3/3 seeds at /053).
    V1_FEATURE_COLUMNS_PRUNED reduced 48 → 47 cols.

Triggering mandate:
    /053 PARTIAL-CONFIRMED (mean IS Δ +0.8102; impulse rank >30/48 in 3/3 seeds;
    spread rank 4-10/48 in 3/3 seeds). LM Master Rec 1 conditional FIRES:
    impulse-drop revaluation at /054 is MANDATORY, not discretionary.

Pre-registered verdict bands (brief Section 4, F-AXIS #1):
    Spread IS ≥ +0.16 (within ±0.05 of /052's both-feature IS +0.1609)
        → IMPULSE-DROP-CONFIRMED: impulse permanently removed; 47-col stack.
    Spread IS ∈ [0, +0.16)
        → IMPULSE-DROP-MARGINAL: retain both; /055 CONFIRMATION at 48 cols.
    Spread IS < 0
        → IMPULSE-DROP-DEGRADES: restore impulse; /055 CONFIRMATION at 48 cols.
    IS trades < 50
        → NEGATIVE-INSUFFICIENT-TRADES (regardless of IS Sharpe).

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, ...)  (first 3 used for single-seed=42 inner pool)

Parquet regeneration required before running (BTCUSDT only):
    uv run crypto-trade features --symbols BTCUSDT --interval 8h \\
        --track v1 --format parquet --workers 4
    Verify: btc_funding_spread_30_90 present; btc_funding_rate_8h_impulse may still
    appear as a parquet column (the runner does not pass it to LightGBM feature_columns).

Features-base-hash:
    47-col hash: f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56
    48-col hash: 106003ea8f1779b3ac3e1c051ee4c7097847f52f33e4820010951453570e6660
    The hashes DIFFER (impulse-drop changes the column set). This is expected.

Invocation:
    # Default (EXPLORATION mode, single-seed=42, n_trials=18, ensemble_size=3):
    uv run python run_iteration_054.py

    # Override n_trials:
    uv run python run_iteration_054.py --n-trials 35

    # Verify features-base-hash only (dry-run, no backtest):
    uv run python run_iteration_054.py --check-hash

Output paths:
    reports-v1/iteration_v1-054/in_sample/
    reports-v1/iteration_v1-054/out_of_sample/
    reports-v1/iteration_v1-054/comparison.csv
    reports-v1/iteration_v1-054/run.log
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED at startup — fires the len==47 assertion
# in features_v1/__init__.py, confirming btc_funding_rate_8h_impulse was DROPPED.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

# Pre-registered 47-col hash (btc_funding_rate_8h_impulse removed; btc_funding_spread_30_90 kept).
# Computed from: hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest()
# This hash DIFFERS from the /052-/053 48-col hash (impulse dropped → column set changed).
#
# To regenerate:
#   uv run python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   print(hashlib.sha256('\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())
#   "
FEATURES_BASE_HASH_47COL: str = "f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56"
FEATURES_BASE_HASH_48COL: str = "106003ea8f1779b3ac3e1c051ee4c7097847f52f33e4820010951453570e6660"


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-054"
ITERATION_NUMBER: int = 54
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 1  # single-seed=42 (EXPLORATION budget; F-AXIS #1 vs /052 anchor)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)

# Compute the live hash at import time (fires the len==47 assertion in __init__.py).
_LIVE_HASH = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _LIVE_HASH


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/054 EXPLORATION runner: "
            "BTC-only impulse-drop test (btc_funding_rate_8h_impulse DROPPED; "
            "btc_funding_spread_30_90 RETAINED; V1_FEATURE_COLUMNS_PRUNED 48 → 47 cols)"
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
            "Defaults to the pre-registered 47-col hash for iter-v1/054."
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
    """Assert V1_FEATURE_COLUMNS_PRUNED matches the pre-registered 47-col hash.

    Exits with a non-zero status if the hash does not match.
    Provides a specific diagnosis if the hash matches the OLD 48-col set (accidental revert).
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual == FEATURES_BASE_HASH_48COL:
        print(
            f"[iter-v1/054] FEATURES-BASE-HASH MISMATCH — 48-col hash detected!\n"
            f"  actual   : {actual} (matches 48-col /052-/053 hash)\n"
            f"  expected : {expected} (47-col /054 hash)\n"
            f"  DIAGNOSIS: btc_funding_rate_8h_impulse was NOT dropped from "
            "V1_FEATURE_COLUMNS_PRUNED. "
            "Check src/crypto_trade/features_v1/__init__.py — the impulse entry must be "
            "COMMENTED OUT (iter-v1/054 DROP).",
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/054] ABORT: V1_FEATURE_COLUMNS_PRUNED is still 48 cols "
            "(impulse not dropped). The /054 feature-drop did not take effect. "
            "Edit src/crypto_trade/features_v1/__init__.py to remove "
            "btc_funding_rate_8h_impulse from V1_FEATURE_COLUMNS_PRUNED."
        )
    if actual != expected:
        print(
            f"[iter-v1/054] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/054] ABORT: feature column set does not match pre-registered 47-col hash. "
            "V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: uv run python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_47COL in run_iteration_054.py."
        )
    print(
        f"[iter-v1/054] features-base-hash PASS: {actual[:16]}... "
        f"(47 columns; btc_funding_rate_8h_impulse DROPPED; btc_funding_spread_30_90 RETAINED)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here if --check-hash) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/054] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  btc_funding_rate_8h_impulse in pruned (must be FALSE):",
            "btc_funding_rate_8h_impulse" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(
            "  btc_funding_spread_30_90 in pruned (must be TRUE):",
            "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(f"  Seeds: {SEEDS_DEFAULT} (single-seed=42; EXPLORATION cadence)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner)")
        print("  47-col hash:", FEATURES_BASE_HASH_47COL)
        print("  48-col hash (OLD /052-/053 ref):", FEATURES_BASE_HASH_48COL)
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "btc_funding_rate_8h_impulse" not in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/054] PRE-FLIGHT FAIL: btc_funding_rate_8h_impulse is STILL in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "The /054 impulse-drop was not applied. "
        "Check src/crypto_trade/features_v1/__init__.py — remove or comment out "
        "the btc_funding_rate_8h_impulse entry."
    )
    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/054] PRE-FLIGHT FAIL: btc_funding_spread_30_90 NOT in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "The spread must be RETAINED at /054 per the both-or-neither rule variant: "
        "impulse-drop test ONLY drops impulse; spread stays."
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 47, (
        f"[iter-v1/054] PRE-FLIGHT FAIL: expected 47 features (48 - 1 impulse-drop), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 47 at iter-v1/054."
    )

    print("=" * 70)
    print("iter-v1/054 — BTC-only impulse-drop test (spread-alone IS attribution)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {SEEDS_DEFAULT} (single-seed=42; EXPLORATION cadence)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; 48→47)")
    spr_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_funding_spread_30_90")
    print(
        f"  btc_funding_spread_30_90   : index {spr_idx} of {n_cols} (RETAINED; rank 4-10 STABLE)"
    )
    print("  btc_funding_rate_8h_impulse: DROPPED (rank >30/48 INERT multi-seed confirmed)")
    print("  cohort                 : BTCUSDT only (V1_ITER054_UNIVERSE)")
    print("  model                  : A_BTC_specialist (R3=ON, R1=OFF, R2=OFF)")
    print("  verdict bands          :")
    print("    Spread IS >= +0.16 → IMPULSE-DROP-CONFIRMED (47-col stack permanent)")
    print("    Spread IS ∈ [0, +0.16) → IMPULSE-DROP-MARGINAL (/055 CONFIRMATION at 48 cols)")
    print("    Spread IS < 0 → IMPULSE-DROP-DEGRADES (restore impulse; /055 at 48 cols)")
    print("  trade-rate floor       : IS ≥ 50 AND OOS ≥ 10")
    print("  47-col hash            :", FEATURES_BASE_HASH_47COL[:32] + "...")
    print("  48-col hash (old ref)  :", FEATURES_BASE_HASH_48COL[:32] + "...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/054. The `--symbols BTCUSDT` argument
    # selects the BTC-only cohort (V1_ITER054_UNIVERSE).
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
        "BTCUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    # No _OUTER_SEED_OFFSETS patch needed — single-seed=42 uses the default offset (0).
    run_baseline_v1.main()


if __name__ == "__main__":
    main()
