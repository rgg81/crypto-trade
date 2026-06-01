"""iter-v1/051 — DOT-only multi-seed re-validation of /050's dot_vs_btc_ret_ratio_30.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/051 and verifies the features-base-hash
guard inherited from /050.

Axis:
    VALIDATION (multi-seed re-validation sub-type; cycle-6 EXPLORATION 6/10).
    Same DOT-only cohort + V1_FEATURE_COLUMNS_PRUNED (46 cols) as iter-v1/050.
    Changes vs /050:
        (1) Vol-spike regime gate DROPPED (was 0%% IS/OOS fire rate — INERT).
        (2) --seeds 3: runs 3 outer seed draws (offsets 0, 3, 6 from
            ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]).
            Offsets satisfy run_baseline_v1.py:7382 constraint: offset+ensemble_size ≤ 10.
            Inner seed windows: offset 0 = [42, 123, 456]; offset 3 = [789, 1001, 2002];
            offset 6 = [3003, 4004, 5005]. Fully disjoint (no seed reuse across outer seeds).
            Outer seed IDs: seed_42 (offset=0), seed_offset3, seed_offset6.

Pre-registered verdict bands (brief Section 8):
    mean IS Delta >= +1.23 → PROMISING-SPECIALIST-CONFIRMED
    +0.50 <= mean IS Delta < +1.23 → PROMISING-PARTIAL-CONFIRMED
    mean IS Delta < +0.50 → LOTTERY-CONFIRMED-NEGATIVE (revert feature)

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, ...)  (first 3 used per outer seed)

Invocation:
    # Default (EXPLORATION mode, n_trials=18, seeds=3, ensemble_size=3):
    uv run python run_iteration_051.py

    # Override n_trials (e.g. to 35 for sensitivity check — NOT default):
    uv run python run_iteration_051.py --n-trials 35

    # Override seeds count (e.g. 1 for quick smoke test):
    uv run python run_iteration_051.py --seeds 1

    # Verify features-base-hash only (dry-run):
    uv run python run_iteration_051.py --check-hash

Output paths:
    reports-v1/iteration_v1-051/seed_42/          (canonical outer seed, offset=0)
    reports-v1/iteration_v1-051/seed_offset3/     (outer seed, offset=3)
    reports-v1/iteration_v1-051/seed_offset6/     (outer seed, offset=6)
    reports-v1/iteration_v1-051/comparison_multi_seed.csv  (multi-seed aggregate)
    reports-v1/iteration_v1-051/run.log

Pre-flight checklist (parquets already regenerated at /050 — no regen needed):
    V1_FEATURE_COLUMNS_PRUNED is UNCHANGED (46 cols).
    dot_vs_btc_ret_ratio_30 already in parquets from iter-v1/050 parquet regen.
    Hash check passes automatically (same feature set as /050).
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED to compute the hash at startup.
# The import also fires the len==46 assertion in features_v1/__init__.py.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered hash: same as iter-v1/050 (V1_FEATURE_COLUMNS_PRUNED UNCHANGED at 46 cols).
# If this value changes, the Optuna search space has been inadvertently modified — BLOCK.
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

ITERATION_LABEL: str = "v1-051"
ITERATION_NUMBER: int = 51
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 3  # 3 outer seeds: offsets 0, 3, 6 (brief Section 3.2)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/051 EXPLORATION runner: "
            "DOT-only multi-seed re-validation of dot_vs_btc_ret_ratio_30 (no regime gate)"
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
            "Uses ENSEMBLE_SEEDS offsets [0, 3, 6] → "
            "seed_42 / seed_offset3 / seed_offset6. "
            "Offsets satisfy run_baseline_v1.py:7382: offset+ensemble_size ≤ 10."
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
            "Defaults to the hash pre-registered in this file."
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
            f"[iter-v1/051] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/051] ABORT: feature column set does not match pre-registered hash. "
            "This means V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_EXPECTED in run_iteration_051.py."
        )
    print(
        f"[iter-v1/051] features-base-hash PASS: {actual[:16]}... "
        f"(46 columns, dot_vs_btc_ret_ratio_30 included; UNCHANGED from /050)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/051] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  dot_vs_btc_ret_ratio_30 in pruned:",
            "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print("  Vol-spike regime gate: DROPPED (was 0%% fire rate / INERT at /050)")
        print(f"  Seeds: {args.seeds} outer seeds (offsets 0, 3, 6)")
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/051] PRE-FLIGHT FAIL: dot_vs_btc_ret_ratio_30 not in V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure src/crypto_trade/features_v1/__init__.py has the column (retained from /050). "
        "Run: uv run crypto-trade features "
        "--symbols BTCUSDT,DOTUSDT "
        "--interval 8h --track v1 --format parquet --workers 4"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 46, (
        f"[iter-v1/051] PRE-FLIGHT FAIL: expected 46 features, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 46 (post iter-v1/050 ADD; UNCHANGED at /051)."
    )
    assert args.seeds >= 1, f"[iter-v1/051] PRE-FLIGHT FAIL: --seeds must be >= 1, got {args.seeds}"

    print("=" * 70)
    print("iter-v1/051 — DOT-only multi-seed re-validation (no regime gate)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {args.seeds} (offsets 0,3,6 ENSEMBLE_SEEDS; 3x3=9 disjoint)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; from /050)")
    dbtc_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("dot_vs_btc_ret_ratio_30")
    print(f"  dot_vs_btc_ret_ratio_30: index {dbtc_idx} of {n_cols} (retained from /050)")
    print("  regime_gate            : DROPPED (was 0% fire rate / INERT at /050)")
    print("  cohort                 : DOTUSDT only (V1_ITER051_UNIVERSE)")
    print("  verdict bands          : mean IS Delta >= +1.23 SPECIALIST-CONFIRMED")
    print("                           +0.50 <= mean IS Delta < +1.23 PARTIAL-CONFIRMED")
    print("                           mean IS Delta < +0.50 LOTTERY-CONFIRMED-NEGATIVE (revert)")
    print(f"  features-base-hash     : {FEATURES_BASE_HASH_EXPECTED[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/051. The `--symbols DOTUSDT` argument
    # selects the DOT-only cohort (V1_ITER051_UNIVERSE).
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
        "DOTUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
