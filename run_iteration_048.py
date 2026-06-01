"""iter-v1/048 — trade_count_zscore_30 feature-family EXPLORATION runner.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/048 and adds the ``--features-base-hash``
guard recommended by LM Master Phase 4.5 Rec #1.

Feature axis:
    ADD ``trade_count_zscore_30`` (rolling-30bar z-score of the ``trades`` kline
    field = Binance ``number_of_trades`` kline primitive) to
    ``V1_FEATURE_COLUMNS_PRUNED``: 44 → 45 columns.

    Module: src/crypto_trade/features_v1/microstructure_v1.py (NEW at iter-v1/048)
    Kline column: ``trades`` (models.Kline.trades, kline field index 8)
    UNUSED-primitive defense: ``trades`` has zero descendants in V1_FEATURE_COLUMNS_PRUNED

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, ...)  (first 3 used at EXPLORATION)

Invocation:
    # Default (EXPLORATION mode, n_trials=18, seeds=1, ensemble_size=3):
    uv run python run_iteration_048.py

    # Override n_trials (e.g. to 35 for sensitivity check — NOT default):
    uv run python run_iteration_048.py --n-trials 35

    # Verify features-base-hash only (dry-run):
    uv run python run_iteration_048.py --check-hash

Output paths:
    reports-v1/iteration_v1-048/in_sample/
    reports-v1/iteration_v1-048/out_of_sample/
    reports-v1/iteration_v1-048/comparison.csv
    reports-v1/iteration_v1-048/feature_importance.csv
    reports-v1/iteration_v1-048/run.log

LM Master Phase 4.5 Rec #1 (ADOPTED):
    Pre-registered SHA-256 hash of V1_FEATURE_COLUMNS_PRUNED (45 cols after /048 change).
    Computed at module load: assert hash == FEATURES_BASE_HASH_EXPECTED at startup.
    Catches any accidental Optuna-search-space bound change that slipped in alongside
    the feature ADD.  The hash covers the sorted tuple bytes — column names + ordering.
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash (LM Master Rec #1)
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED to compute the hash at startup.
# The import also fires the len==45 assertion in features_v1/__init__.py.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered hash: computed once from V1_FEATURE_COLUMNS_PRUNED (45 cols)
# after the iter-v1/048 source change.  If this value changes, the Optuna search
# space has been inadvertently modified — BLOCK the backtest.
#
# To regenerate:
#   python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   payload = '\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()
#   print(hashlib.sha256(payload).hexdigest())
#   "
FEATURES_BASE_HASH_EXPECTED: str = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)

# ---------------------------------------------------------------------------
# EXPLORATION parameters (DO NOT CHANGE — single-axis isolation)
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-048"
ITERATION_NUMBER: int = 48
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 1  # single outer seed (EXPLORATION standard)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="iter-v1/048 EXPLORATION runner: trade_count_zscore_30 feature axis"
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
        help=f"Number of outer seeds (default {SEEDS_DEFAULT}; EXPLORATION standard).",
    )
    p.add_argument(
        "--features-base-hash",
        type=str,
        default=None,
        dest="features_base_hash",
        metavar="SHA256",
        help=(
            "Expected SHA-256 of V1_FEATURE_COLUMNS_PRUNED (sorted).  "
            "If provided, the runner aborts if the live hash does not match.  "
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

    Exits with a non-zero status if the hash does not match (feature list was
    modified without updating the pre-registered value).
    """
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    if actual != expected:
        print(
            f"[iter-v1/048] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/048] ABORT: feature column set does not match pre-registered hash.  "
            "This means V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed.  "
            'Re-run: python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_EXPECTED in run_iteration_048.py."
        )
    print(
        f"[iter-v1/048] features-base-hash PASS: {actual[:16]}... "
        f"(45 columns, trade_count_zscore_30 included)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/048] --check-hash mode.  "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}.  "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}.  "
            "No backtest launched."
        )
        print(
            "  trade_count_zscore_30 in pruned:",
            "trade_count_zscore_30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "trade_count_zscore_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/048] PRE-FLIGHT FAIL: trade_count_zscore_30 not in V1_FEATURE_COLUMNS_PRUNED.  "
        "Ensure src/crypto_trade/features_v1/__init__.py has been updated and parquets "
        "regenerated with: uv run crypto-trade features "
        "--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
        "--interval 8h --track v1 --format parquet --workers 4"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
        f"[iter-v1/048] PRE-FLIGHT FAIL: expected 45 features, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}."
    )

    print("=" * 60)
    print("iter-v1/048 — trade_count_zscore_30 EXPLORATION")
    print(f"  ITERATION_LABEL       : {ITERATION_LABEL}")
    print(f"  n_trials              : {args.n_trials}")
    print(f"  outer seeds           : {args.seeds}")
    print(f"  ensemble_size         : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns       : {n_cols} cols (pruned, V1_FEATURE_COLUMNS_PRUNED)")
    tc_idx = V1_FEATURE_COLUMNS_PRUNED.index("trade_count_zscore_30")
    print(f"  trade_count_zscore_30 : index {tc_idx} of {n_cols}")
    print("  kline primitive       : trades (Binance number_of_trades field 8)")
    print(f"  features-base-hash    : {FEATURES_BASE_HASH_EXPECTED[:32]}...")
    print("=" * 60)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv.  We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/048.  This is the standard dispatch
    # pattern for iteration-specific runners in this codebase.
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
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
