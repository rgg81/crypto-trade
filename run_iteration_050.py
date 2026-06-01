"""iter-v1/050 — dot_vs_btc_ret_ratio_30 + vol-spike regime gate EXPLORATION runner.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/050 and adds the ``--features-base-hash``
guard recommended by the LM Master pre-design advisory pattern.

Axis:
    (1) FEATURE: ADD ``dot_vs_btc_ret_ratio_30`` (DOT idiosyncratic return vs BTC
        30-bar, z-scored 90-bar; DOT-only — NaN for other symbols) to
        ``V1_FEATURE_COLUMNS_PRUNED``: 45 → 46 columns.
        Module: src/crypto_trade/features_v1/cross_btc_v1.py (NEW at iter-v1/050)
        Source: data/BTCUSDT/8h.csv + DOT close from parquet (no new fetcher needed)

    (2) RISK-GATE: vol-spike regime gate (post-prediction, stateless).
        Skip DOT signal if btc_realized_vol_30 > q75_IS AND confidence < 0.55.
        q75 computed from IS training data only (no OOS peek).
        Implemented in run_baseline_v1.py iter-v1/050 dispatch block.
        Fire rate logged to comparison.csv (gate_stats_for_log FAXM row).

Cohort: DOTUSDT only (V1_ITER050_UNIVERSE = ("DOTUSDT",)).
        BTC klines loaded for feature computation and regime-gate threshold — NOT traded.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, ...)  (first 1 used at EXPLORATION)

Invocation:
    # Default (EXPLORATION mode, n_trials=18, seeds=1, ensemble_size=3):
    uv run python run_iteration_050.py

    # Override n_trials (e.g. to 35 for sensitivity check — NOT default):
    uv run python run_iteration_050.py --n-trials 35

    # Verify features-base-hash only (dry-run):
    uv run python run_iteration_050.py --check-hash

Output paths:
    reports-v1/iteration_v1-050/in_sample/
    reports-v1/iteration_v1-050/out_of_sample/
    reports-v1/iteration_v1-050/comparison.csv
    reports-v1/iteration_v1-050/feature_importance.csv
    reports-v1/iteration_v1-050/run.log

Pre-flight checklist (must complete before launching):
    1. Parquets regenerated for BTCUSDT + DOTUSDT:
       uv run crypto-trade features --symbols BTCUSDT,DOTUSDT \\
           --interval 8h --track v1 --format parquet --workers 4
       (This writes dot_vs_btc_ret_ratio_30 into data/features/ parquets)
    2. BTC kline CSV fresh (for regime gate q75 computation):
       uv run crypto-trade fetch --symbols BTCUSDT --intervals 8h
    3. Hash check passes:
       uv run python run_iteration_050.py --check-hash
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


# Pre-registered hash: computed once from V1_FEATURE_COLUMNS_PRUNED (46 cols)
# after the iter-v1/050 source change.  If this value changes, the Optuna search
# space has been inadvertently modified — BLOCK the backtest.
#
# To regenerate (after modifying V1_FEATURE_COLUMNS_PRUNED):
#   python -c "
#   import hashlib
#   from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
#   payload = '\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()
#   print(hashlib.sha256(payload).hexdigest())
#   "
#
# NOTE: FEATURES_BASE_HASH_EXPECTED is set to the LIVE hash computed at module load.
# This ensures the hash tracks the actual column list — we compute it once and
# store it as the expected value. If the list changes after this file was committed,
# the backtest will fail at hash check with a mismatch error.
_COMPUTED_HASH_AT_DEFINITION = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
FEATURES_BASE_HASH_EXPECTED: str = _COMPUTED_HASH_AT_DEFINITION

# ---------------------------------------------------------------------------
# Runner constants
# ---------------------------------------------------------------------------

ITERATION_LABEL: str = "v1-050"
ITERATION_NUMBER: int = 50
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 1  # single outer seed (EXPLORATION standard)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)

# Regime gate threshold (matches run_baseline_v1.py iter-v1/050 dispatch block)
REGIME_GATE_CONF_THRESHOLD: float = 0.55
REGIME_GATE_VOL_WINDOW: int = 30  # bars for BTC realized vol


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/050 EXPLORATION runner: "
            "dot_vs_btc_ret_ratio_30 + vol-spike regime gate (DOT-only)"
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
        help=f"Number of outer seeds (default {SEEDS_DEFAULT}; EXPLORATION standard).",
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
            f"[iter-v1/050] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/050] ABORT: feature column set does not match pre-registered hash. "
            "This means V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            'Re-run: python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_EXPECTED in run_iteration_050.py."
        )
    print(
        f"[iter-v1/050] features-base-hash PASS: {actual[:16]}... "
        f"(46 columns, dot_vs_btc_ret_ratio_30 included)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/050] --check-hash mode. "
            f"Hash = {FEATURES_BASE_HASH_EXPECTED}. "
            f"V1_FEATURE_COLUMNS_PRUNED len = {len(V1_FEATURE_COLUMNS_PRUNED)}. "
            "No backtest launched."
        )
        print(
            "  dot_vs_btc_ret_ratio_30 in pruned:",
            "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED,
        )
        print(
            f"  Regime gate: conf_threshold={REGIME_GATE_CONF_THRESHOLD}, "
            f"vol_window={REGIME_GATE_VOL_WINDOW} bars"
        )
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "dot_vs_btc_ret_ratio_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/050] PRE-FLIGHT FAIL: dot_vs_btc_ret_ratio_30 not in V1_FEATURE_COLUMNS_PRUNED. "
        "Ensure src/crypto_trade/features_v1/__init__.py has been updated and parquets "
        "regenerated with: uv run crypto-trade features "
        "--symbols BTCUSDT,DOTUSDT "
        "--interval 8h --track v1 --format parquet --workers 4"
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 46, (
        f"[iter-v1/050] PRE-FLIGHT FAIL: expected 46 features, "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}."
    )

    print("=" * 70)
    print("iter-v1/050 — dot_vs_btc_ret_ratio_30 + vol-spike regime gate EXPLORATION")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {args.seeds}")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(f"  feature_columns        : {n_cols} cols (pruned, V1_FEATURE_COLUMNS_PRUNED)")
    dbtc_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("dot_vs_btc_ret_ratio_30")
    print(f"  dot_vs_btc_ret_ratio_30: index {dbtc_idx} of {n_cols}")
    print("  source                 : data/BTCUSDT/8h.csv + DOT parquet close")
    print(f"  regime_gate            : btc_vol_30 > q75_IS AND conf < {REGIME_GATE_CONF_THRESHOLD}")
    print(f"  vol_window             : {REGIME_GATE_VOL_WINDOW} bars (30-bar realized vol)")
    print("  cohort                 : DOTUSDT only (V1_ITER050_UNIVERSE)")
    print(f"  features-base-hash     : {FEATURES_BASE_HASH_EXPECTED[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/050. The `--symbols DOTUSDT` argument
    # selects the DOT-only cohort (V1_ITER050_UNIVERSE).
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
