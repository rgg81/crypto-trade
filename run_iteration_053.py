"""iter-v1/053 — BTC-only multi-seed re-validation of /052's funding-rate specialist.

This is a thin dispatch wrapper around ``run_baseline_v1.main()``.  It hardwires
the EXPLORATION-mode arguments for iter-v1/053 and verifies the features-base-hash
guard for the 48-column V1_FEATURE_COLUMNS_PRUNED (UNCHANGED from /052).

Axis:
    VALIDATION (multi-seed re-validation sub-type; cycle-6 EXPLORATION 8/10).
    Same BTC-only cohort + V1_FEATURE_COLUMNS_PRUNED (48 cols) as iter-v1/052.
    Changes vs /052:
        (1) --seeds 3: runs 3 outer seed draws (offsets 0, 3, 6 from
            ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]).
            Offsets satisfy run_baseline_v1.py constraint: offset+ensemble_size ≤ 10.
            Inner seed windows: offset 0 = [42, 123, 456];
                                offset 3 = [789, 1001, 2002];
                                offset 6 = [3003, 4004, 5005].
            All disjoint (no seed reuse across outer seeds).
            Outer seed IDs: seed_42 (offset=0), seed_offset3, seed_offset6.
        (2) No feature changes — V1_FEATURE_COLUMNS_PRUNED = 48 cols (UNCHANGED).
        (3) No parquet regeneration required — both funding features already present
            from /052 regen.

LM Master Rec 3 from /052 Phase 4.5 FIRES (PROMISING-SPECIALIST-CANDIDATE closeout).
/053 is MANDATORY, not discretionary.

Pre-registered verdict bands (brief Section 8):
    mean IS Δ ≥ +0.85 AND max-min ≤ 0.5 → SPECIALIST-CONFIRMED (BTC into /055 roster)
    mean IS Δ ∈ [+0.30, +0.85) → PARTIAL-CONFIRMED (consider impulse-drop at /054)
    mean IS Δ < +0.30 → NEG-CLEAN-MULTI-SEED (revert both features)

Basin-lottery threshold: max-min > 0.5 (TIGHTENED from /051's 1.0 due to concentrated
single-driver btc_funding_spread_30_90 at rank 4/48 at /052).

Trade-rate floor: mean IS ≥ 50 AND mean OOS ≥ 10.

Sacred constants (DO NOT CHANGE):
    OOS_CUTOFF_MS = 1742774400000  (2025-03-24 00:00 UTC)
    training_months = 24
    ENSEMBLE_SEEDS = (42, 123, 456, 789, 1001, ...)  (first 3 used per outer seed)

Invocation:
    # Default (EXPLORATION mode, n_trials=18, seeds=3, ensemble_size=3):
    uv run python run_iteration_053.py

    # Override n_trials (e.g. to 35 for sensitivity check — NOT default):
    uv run python run_iteration_053.py --n-trials 35

    # Override seeds count (e.g. 1 for quick smoke test — seed=42 reproduces /052):
    uv run python run_iteration_053.py --seeds 1

    # Verify features-base-hash only (dry-run):
    uv run python run_iteration_053.py --check-hash

Output paths:
    reports-v1/iteration_v1-053/seed_42/          (canonical outer seed, offset=0)
    reports-v1/iteration_v1-053/seed_offset3/     (outer seed, offset=3)
    reports-v1/iteration_v1-053/seed_offset6/     (outer seed, offset=6)
    reports-v1/iteration_v1-053/comparison_multi_seed.csv  (multi-seed aggregate)
    reports-v1/iteration_v1-053/run.log

Pre-flight checklist (parquets already regenerated at /052 — no regen needed):
    V1_FEATURE_COLUMNS_PRUNED is UNCHANGED (48 cols).
    btc_funding_rate_8h_impulse + btc_funding_spread_30_90 already in parquets from /052.
    Hash check passes automatically (same feature set as /052).
"""

from __future__ import annotations

import argparse
import hashlib
import sys

# ---------------------------------------------------------------------------
# features-base-hash guard
# ---------------------------------------------------------------------------
# Import V1_FEATURE_COLUMNS_PRUNED to compute the hash at startup.
# The import also fires the len==48 assertion in features_v1/__init__.py,
# confirming the two /052 funding features are still registered.
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    """Compute SHA-256 of the sorted feature-column tuple (deterministic)."""
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Pre-registered hash: same as iter-v1/052 (V1_FEATURE_COLUMNS_PRUNED UNCHANGED at 48 cols).
# If this value changes, V1_FEATURE_COLUMNS_PRUNED was inadvertently modified — BLOCK.
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

ITERATION_LABEL: str = "v1-053"
ITERATION_NUMBER: int = 53
N_TRIALS_DEFAULT: int = 18  # EXPLORATION standard (brief Section 0.5)
SEEDS_DEFAULT: int = 3  # 3 outer seeds: offsets 0, 3, 6 (brief Section 3.2)
ENSEMBLE_SIZE: int = 3  # EXPLORATION inner-ensemble size (brief Section 0.5)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "iter-v1/053 EXPLORATION runner: "
            "BTC-only multi-seed re-validation of /052 "
            "(btc_funding_rate_8h_impulse + btc_funding_spread_30_90; "
            "V1_FEATURE_COLUMNS_PRUNED 48 cols UNCHANGED)"
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
            "Offsets satisfy run_baseline_v1.py constraint: offset+ensemble_size ≤ 10. "
            "Use --seeds 1 to reproduce /052 single-seed=42 result exactly."
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
            "Defaults to the hash pre-registered in this file (same as /052 — 48 cols)."
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
            f"[iter-v1/053] FEATURES-BASE-HASH MISMATCH\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            f"  V1_FEATURE_COLUMNS_PRUNED (len={len(V1_FEATURE_COLUMNS_PRUNED)}):\n"
            + "\n".join(f"    {i:03d}: {c}" for i, c in enumerate(V1_FEATURE_COLUMNS_PRUNED)),
            file=sys.stderr,
        )
        sys.exit(
            "[iter-v1/053] ABORT: feature column set does not match pre-registered hash. "
            "This means V1_FEATURE_COLUMNS_PRUNED was modified after the hash was computed. "
            "The hash at /053 MUST equal the /052 hash (48 cols; no feature changes). "
            'Re-run: python -c "import hashlib; from crypto_trade.features_v1 import '
            "V1_FEATURE_COLUMNS_PRUNED; "
            "print(hashlib.sha256('\\n'.join(sorted(V1_FEATURE_COLUMNS_PRUNED)).encode()).hexdigest())\""
            " and update FEATURES_BASE_HASH_EXPECTED in run_iteration_053.py."
        )
    print(
        f"[iter-v1/053] features-base-hash PASS: {actual[:16]}... "
        f"(48 columns; btc_funding_rate_8h_impulse + btc_funding_spread_30_90 UNCHANGED from /052)"
    )


def main() -> None:
    args = _parse_args()

    # --- Hash check (always runs; dry-run exits here) ---
    expected_hash = args.features_base_hash or FEATURES_BASE_HASH_EXPECTED
    _verify_features_hash(expected_hash)

    if args.check_hash:
        print(
            f"[iter-v1/053] --check-hash mode. "
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
        print(f"  Seeds: {args.seeds} outer seeds (offsets 0,3,6 → 3 disjoint inner pools)")
        print(f"  Ensemble size: {ENSEMBLE_SIZE} (inner; UNCHANGED from /052)")
        print("  No parquet regen required — features already present from /052.")
        print("  Column list:")
        for i, col in enumerate(V1_FEATURE_COLUMNS_PRUNED):
            print(f"    {i:02d}: {col}")
        return

    # --- Pre-flight assertions ---
    assert "btc_funding_rate_8h_impulse" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/053] PRE-FLIGHT FAIL: btc_funding_rate_8h_impulse not in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "Both features must be retained from /052 per both-or-neither rule. "
        "Check src/crypto_trade/features_v1/__init__.py has not been modified."
    )
    assert "btc_funding_spread_30_90" in V1_FEATURE_COLUMNS_PRUNED, (
        "[iter-v1/053] PRE-FLIGHT FAIL: btc_funding_spread_30_90 not in "
        "V1_FEATURE_COLUMNS_PRUNED. "
        "Both features must be retained from /052 per both-or-neither rule. "
        "Check src/crypto_trade/features_v1/__init__.py has not been modified."
    )
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"[iter-v1/053] PRE-FLIGHT FAIL: expected 48 features (UNCHANGED from /052), "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "V1_FEATURE_COLUMNS_PRUNED must be 48 at iter-v1/053 (no feature changes vs /052)."
    )
    assert args.seeds >= 1, f"[iter-v1/053] PRE-FLIGHT FAIL: --seeds must be >= 1, got {args.seeds}"

    print("=" * 70)
    print("iter-v1/053 — BTC-only multi-seed re-validation (/052 PROMISING mandate)")
    print(f"  ITERATION_LABEL        : {ITERATION_LABEL}")
    print(f"  n_trials               : {args.n_trials}")
    print(f"  outer seeds            : {args.seeds} (offsets 0,3,6 ENSEMBLE_SEEDS; 3x3=9 disjoint)")
    print(f"  ensemble_size          : {ENSEMBLE_SIZE} (inner; UNCHANGED from /052)")
    n_cols = len(V1_FEATURE_COLUMNS_PRUNED)
    print(
        f"  feature_columns        : {n_cols} cols (V1_FEATURE_COLUMNS_PRUNED; UNCHANGED from /052)"
    )
    imp_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_funding_rate_8h_impulse")
    spr_idx = list(V1_FEATURE_COLUMNS_PRUNED).index("btc_funding_spread_30_90")
    print(f"  btc_funding_rate_8h_impulse: index {imp_idx} of {n_cols} (rank38@/052 INERT)")
    print(
        f"  btc_funding_spread_30_90   : index {spr_idx} of {n_cols} (rank4@/052 STRONGLY-LEARNED)"
    )
    print("  parquet_regen          : NOT REQUIRED (features already in parquet from /052)")
    print("  cohort                 : BTCUSDT only (V1_ITER053_UNIVERSE)")
    print("  model                  : A_BTC_specialist (R3=ON, R1=OFF, R2=OFF)")
    print("  verdict bands          :")
    print("    mean IS Δ ≥ +0.85 + max-min ≤ 0.5 → SPECIALIST-CONFIRMED")
    print("    mean IS Δ ∈ [+0.30, +0.85) → PARTIAL-CONFIRMED")
    print("    mean IS Δ < +0.30 → NEG-CLEAN-MULTI-SEED (revert both features)")
    print("  basin-lottery          : max-min > 0.5 FLAG (TIGHTENED from /051 threshold 1.0)")
    print("  trade-rate floor       : mean IS ≥ 50 AND mean OOS ≥ 10")
    print("  seed=42 sanity         : offset=0 must reproduce /052 IS Sharpe ±0.0005")
    print(f"  features-base-hash     : {FEATURES_BASE_HASH_EXPECTED[:32]}...")
    print("=" * 70)

    # --- Inject argv for run_baseline_v1.main() ---
    # run_baseline_v1.main() reads sys.argv. We replace it with the hardwired
    # EXPLORATION arguments for iter-v1/053. The `--symbols BTCUSDT` argument
    # selects the BTC-only cohort (V1_ITER053_UNIVERSE).
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
        "BTCUSDT",
    ]

    # Import and invoke the v1 runner.
    import run_baseline_v1  # noqa: PLC0415  (local import to defer argv replacement)

    # iter-v1/053 scope-limited offset override: disjoint outer seeds at ENSEMBLE_SIZE=3.
    # Framework default (0,5,10,15,20) silently skips offset 10 because 10+3>10 (len=10);
    # (0,3,6) gives three fully-disjoint windows: [42,123,456], [789,1001,2002], [3003,4004,5005].
    # Arithmetic check: max(offset)+ENSEMBLE_SIZE = 6+3 = 9 ≤ 10 ✓
    # DO NOT change run_baseline_v1._OUTER_SEED_OFFSETS in the framework file — this patch
    # is scope-limited to this runner module only (per /051 precedent).
    run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)

    run_baseline_v1.main()


if __name__ == "__main__":
    main()
