"""Adversarial tests for ensemble seed propagation in OOF return parquets.

iter-v3/005 Section 3.5 sub-fix #2 — spec from brief:
  Assert df.groupby([trial_id, candle_open_time_ms])["oof_return"].nunique() > 1
  for at least 50% of groups.

Three tests:
  (A) test_seed_propagation_synthetic_variable  — synthetic parquet where 80%
      of (trial_id, candle_open_time_ms) groups have nunique(oof_return) > 1
      and 20% are constant.  Asserts PASS (≥50% variable).

  (B) test_seed_propagation_synthetic_constant  — synthetic parquet where ALL
      groups have nunique(oof_return) == 1 (degenerate seed dimension).
      Asserts FAIL on the ≥50% threshold (i.e., the test itself FAILS, which
      is what we want to document — a constant parquet triggers the test
      assertion).  Implemented by checking the fraction is < 50% and asserting
      that. (The test checks that the failing condition would be detected.)

  (C) test_seed_propagation_real_parquet  — loads
      reports-v3/iteration_v3-003/trial_oof_returns.parquet and asserts
      ≥50% of natural-key groups have nunique(oof_return) > 1.
      Per Section 2.1 Phase-5 evidence: empirical fraction = 76.55% > 50%.
      Expected to PASS.

Natural key is (symbol, train_month, trial_id, fold_idx, candle_open_time_ms)
per brief Section 2.1, consistent with the dedup key in recompute_metrics.py.
For the test assertion, the brief specifies groupby([trial_id, candle_open_time_ms])
which is a superset projection — we use the full natural key to be consistent
with the Section 2.1 audit results.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Natural-key columns (must match optimization.py writer and brief Section 2.1)
# ---------------------------------------------------------------------------
NATURAL_KEY = ["symbol", "train_month", "trial_id", "fold_idx", "candle_open_time_ms"]

# ---------------------------------------------------------------------------
# Path to iter-v3/003 parquet (Section 3.5 sub-fix #3)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_PARQUET = REPO_ROOT / "reports-v3" / "iteration_v3-003" / "trial_oof_returns.parquet"

# ---------------------------------------------------------------------------
# Threshold from brief Section 2.1: at least 50% of groups must have
# nunique(oof_return) > 1 for the ensemble seed dimension to carry signal.
# ---------------------------------------------------------------------------
MIN_VARIABLE_FRACTION = 0.50


# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _make_synthetic_parquet(
    n_groups: int,
    variable_fraction: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Build a synthetic parquet-like DataFrame.

    Each group represents a unique (symbol, train_month, trial_id, fold_idx,
    candle_open_time_ms) tuple with 5 rows (one per inner ensemble seed).

    For ``variable_fraction`` of groups, the 5 rows have distinct oof_return
    values (drawn IID from N(0, 1)).  For the remaining (1 - variable_fraction)
    groups, all 5 rows share the same oof_return (degenerate seed dimension).

    Parameters
    ----------
    n_groups       : Total natural-key groups to create.
    variable_fraction : Fraction of groups with nunique(oof_return) > 1.
    rng            : Random generator for reproducible synthetic data.
    """
    n_variable = int(n_groups * variable_fraction)

    rows = []
    for g in range(n_groups):
        sym = f"SYM{g % 4:02d}USDT"
        month = f"2023-{(g % 12) + 1:02d}"
        trial_id = g % 50
        fold_idx = g % 5
        candle_ts = 1_000_000 + g * 28800_000  # 8h spacing

        if g < n_variable:
            # Variable: each of 5 seeds produces a different oof_return
            values = rng.standard_normal(5).tolist()
        else:
            # Constant: all 5 seeds produce the same oof_return
            v = float(rng.standard_normal())
            values = [v] * 5

        for val in values:
            rows.append(
                {
                    "symbol": sym,
                    "train_month": month,
                    "trial_id": trial_id,
                    "fold_idx": fold_idx,
                    "candle_open_time_ms": candle_ts,
                    "oof_return": val,
                }
            )

    return pd.DataFrame(rows)


def _compute_variable_fraction(df: pd.DataFrame) -> float:
    """Compute the fraction of natural-key groups with nunique(oof_return) > 1."""
    nunique_per_group = df.groupby(NATURAL_KEY)["oof_return"].nunique()
    variable_mask = nunique_per_group > 1
    return float(variable_mask.mean())


# ---------------------------------------------------------------------------
# (A) Synthetic variable: 80% groups variable — expect PASS
# ---------------------------------------------------------------------------


def test_seed_propagation_synthetic_variable() -> None:
    """80% variable groups: assert ≥50% threshold PASSES by construction.

    This test verifies that the propagation rule correctly identifies a parquet
    with meaningful cross-seed variance.  It should always PASS regardless of
    the real parquet content.
    """
    rng = np.random.default_rng(42)
    df = _make_synthetic_parquet(n_groups=1000, variable_fraction=0.80, rng=rng)
    frac = _compute_variable_fraction(df)

    assert frac >= MIN_VARIABLE_FRACTION, (
        f"Expected ≥{MIN_VARIABLE_FRACTION:.0%} variable groups. "
        f"Got {frac:.4f} ({frac * 100:.2f}%). "
        f"Synthetic parquet was constructed with 80% variable groups — "
        f"this test should always PASS."
    )


# ---------------------------------------------------------------------------
# (B) Synthetic constant: 0% variable — detect the degenerate case
# ---------------------------------------------------------------------------


def test_seed_propagation_synthetic_constant() -> None:
    """All groups constant: assert the degenerate case is correctly DETECTED.

    A parquet where all 5 inner ensemble seeds produce identical oof_return
    values per natural key has 0% variable groups — the seed dimension carries
    no signal.  This test asserts that the fraction is BELOW the ≥50% threshold,
    confirming the detection logic works.  The test PASSES (the assertion below
    is TRUE) — it is testing that a degenerate parquet would FAIL the main
    propagation check.
    """
    rng = np.random.default_rng(99)
    df = _make_synthetic_parquet(n_groups=1000, variable_fraction=0.0, rng=rng)
    frac = _compute_variable_fraction(df)

    # The fraction should be 0 (all groups are constant)
    assert frac < MIN_VARIABLE_FRACTION, (
        f"Expected <{MIN_VARIABLE_FRACTION:.0%} variable groups (degenerate parquet). "
        f"Got {frac:.4f}. Synthetic parquet was constructed with 0% variable groups."
    )

    # Also assert it is effectively 0 (not just below threshold by chance)
    assert frac < 0.01, (
        f"Expected near-zero variable fraction for a fully-constant parquet. Got {frac:.4f}."
    )


# ---------------------------------------------------------------------------
# (C) Real parquet: iter-v3/003 — expect PASS at ≥76.55%
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not REAL_PARQUET.exists(),
    reason="iter-v3/003 trial_oof_returns.parquet not found — skip in CI without data",
)
def test_seed_propagation_real_parquet() -> None:
    """Load iter-v3/003 parquet and assert ≥50% of groups have nunique > 1.

    Per brief Section 2.1 Phase-5 evidence (analysis/iteration_v3-005/seed_audit_demo.py):
      - Total natural-key groups (raw pre-dedup): 15,747,500
      - Variable groups (nunique > 1): 12,054,773 (76.55%)
      - Degenerate groups (nunique == 1): 3,692,727 (23.45%)

    The nunique check must be computed on the RAW parquet (pre-dedup, 78.7M rows)
    because the writer appends 5 rows per natural key (one per inner ensemble seed)
    without a seed column.  After dedup each group trivially has nunique==1.
    The audit asks: "of the 15.7M unique natural-key groups, how many had at
    least 2 distinct oof_return values across the 5 seed-appended rows?"

    Expected outcome: PASS at ~76.55% >> 50% threshold.

    The result of this test (PASS fraction) is documented in the engineering
    report per brief Section 3.5 sub-fix #3 and reconciliation row 12.
    """
    df = pd.read_parquet(REAL_PARQUET)
    n_raw = len(df)

    # Compute nunique ON THE RAW parquet (pre-dedup).
    # The writer appends 5 rows per natural key (one per inner seed).
    # nunique(oof_return) > 1 iff at least 2 of those 5 seed rows differ.
    frac = _compute_variable_fraction(df)
    n_groups = df.groupby(NATURAL_KEY).ngroups
    n_variable = int(frac * n_groups)

    print("\n[test_seed_propagation_real_parquet]")
    print(f"  Raw rows: {n_raw:,}")
    print(f"  Natural-key groups: {n_groups:,}")
    print(f"  Variable groups (nunique>1): {n_variable:,} ({frac * 100:.2f}%)")
    print(f"  Degenerate groups (nunique==1): {n_groups - n_variable:,} ({(1 - frac) * 100:.2f}%)")
    print(f"  Threshold: {MIN_VARIABLE_FRACTION * 100:.0f}%")
    print(f"  Result: {'PASS' if frac >= MIN_VARIABLE_FRACTION else 'FAIL'}")

    assert frac >= MIN_VARIABLE_FRACTION, (
        f"test_ensemble_seed_propagation FAIL: only {frac * 100:.2f}% of natural-key "
        f"groups have nunique(oof_return) > 1 (across 5 ensemble-seed rows). "
        f"Threshold is {MIN_VARIABLE_FRACTION * 100:.0f}%. "
        f"This means the iter-v3/003 ensemble seed dimension is structurally "
        f"degenerate — all 5 inner seeds produce identical OOF returns per group. "
        f"iter-v3/006 recommendation: investigate whether the seed parameter is "
        f"actually propagated through optimize_and_train() in optimization.py."
    )
