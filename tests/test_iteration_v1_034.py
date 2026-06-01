"""Integration tests for iter-v1/034 — basis_zscore_30 feature.

Covers:
7.  test_v1_034_dispatch_banner — runner with iteration_label="v1-034" prints
    "[iter-v1/034] BASIS-Z30 ACTIVE" line.
8.  test_v1_034_in_baseline_catchall_exclusion — exclusion tuple contains "v1-034"
    (catch-all guard per /030 LESSON feedback_v1_dispatch_baseline_catchall_exclusion.md).
9.  test_v1_034_dispatch_branch_exists — runner source contains "v1-034" dispatch branch
    (existence check via inspect.getsource).
10. test_v1_034_basis_zscore_30_in_pruned_features — basis_zscore_30 was added at /034
    but DROPPED at /040 (3-consec INERT). Now checks V1_RETIRED_FEATURE_COLUMNS.
11. test_v1_034_pruned_features_length_44 — V1_FEATURE_COLUMNS_PRUNED has 44 columns.
12. test_v1_034_foundation_regression_walk_forward_embargo — walk_forward.py:113 carry
    embargo discipline (train_end_ms < test_start_ms).
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 7 — Dispatch banner
# ---------------------------------------------------------------------------


def test_v1_034_dispatch_banner() -> None:
    """run_baseline_v1.py dispatch branch for v1-034 contains the expected banner print."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/034] BASIS-Z30 ACTIVE" in src, (
        "Expected banner '[iter-v1/034] BASIS-Z30 ACTIVE' not found in run_baseline_v1.py. "
        "The v1-034 dispatch branch must print this banner to confirm feature wiring."
    )


# ---------------------------------------------------------------------------
# Test 8 — Catch-all exclusion tuple
# ---------------------------------------------------------------------------


def test_v1_034_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-034'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif branch MUST be added
    to the catch-all exclusion tuple that guards the generic baseline dispatch.
    Missing this causes the catch-all to silently run baseline numbers for v1-034.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    # The exclusion tuple must contain "v1-034" as a literal string
    assert '"v1-034"' in src, (
        '"v1-034" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, the catch-all branch silently runs baseline numbers."
    )


# ---------------------------------------------------------------------------
# Test 9 — Dispatch branch exists
# ---------------------------------------------------------------------------


def test_v1_034_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-034'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-034"' in src, (
        'Dispatch branch iteration_label == "v1-034" not found in run_baseline_v1.py. '
        "The /034 elif must exist before the catch-all to trigger basis_zscore_30 logic."
    )


# ---------------------------------------------------------------------------
# Test 10 — basis_zscore_30 in V1_FEATURE_COLUMNS_PRUNED
# ---------------------------------------------------------------------------


def test_v1_034_basis_zscore_30_in_pruned_features() -> None:
    """basis_zscore_30 was added at /034 but DROPPED at /040 (3-consec INERT).

    After iter-v1/040, basis_zscore_30 is in V1_RETIRED_FEATURE_COLUMNS (not in
    V1_FEATURE_COLUMNS_PRUNED). This test now verifies the retired state.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_RETIRED_FEATURE_COLUMNS

    # After /040: basis_zscore_30 MUST be in RETIRED, NOT in PRUNED.
    assert "basis_zscore_30" not in V1_FEATURE_COLUMNS_PRUNED, (
        "basis_zscore_30 is still in V1_FEATURE_COLUMNS_PRUNED. "
        "iter-v1/040 dropped basis_zscore_30 (3-consec INERT across /034, /037, /038). "
        "It should now be in V1_RETIRED_FEATURE_COLUMNS only."
    )
    assert "basis_zscore_30" in V1_RETIRED_FEATURE_COLUMNS, (
        "basis_zscore_30 not found in V1_RETIRED_FEATURE_COLUMNS. "
        "iter-v1/040 retired basis_zscore_30; add it to V1_RETIRED_FEATURE_COLUMNS."
    )


# ---------------------------------------------------------------------------
# Test 11 — V1_FEATURE_COLUMNS_PRUNED has 44 columns
# ---------------------------------------------------------------------------


def test_v1_034_pruned_features_length_44() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 45 features after /049 ADD.

    History: /034 added basis_zscore_30 (43→44); /040 swapped to regime_momentum (44);
    /049 added long_short_zscore_30 (44→45).
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    n = len(V1_FEATURE_COLUMNS_PRUNED)
    assert n == 45, (
        f"V1_FEATURE_COLUMNS_PRUNED should have 45 features after iter-v1/049 adds "
        f"long_short_zscore_30 (44 → 45). Got {n}."
    )


# ---------------------------------------------------------------------------
# Test 12 — Foundation regression: walk_forward.py:113 embargo discipline
# ---------------------------------------------------------------------------


def test_v1_034_foundation_regression_walk_forward_embargo() -> None:
    """walk_forward.py must implement train_end_ms < test_start_ms (embargo gap).

    This is the load-bearing fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md.
    The walk_forward module must carry embargo_ms so that the training window ends
    strictly BEFORE the test window begins.

    We verify by reading the source: 'train_end_ms' and 'embargo_ms' must both appear,
    and 'train_end_ms = test_start_ms - embargo_ms' must be present (no lookahead).
    """
    try:
        from crypto_trade.strategies.ml import walk_forward
    except ImportError:
        import importlib

        walk_forward = importlib.import_module("crypto_trade.strategies.ml.walk_forward")

    src = inspect.getsource(walk_forward)

    assert "embargo_ms" in src, (
        "walk_forward.py must contain 'embargo_ms' for the label-leakage gap. "
        "Missing embargo_ms means walk_forward has a lookahead bias."
    )
    assert "train_end_ms" in src, (
        "walk_forward.py must contain 'train_end_ms'. "
        "This is the load-bearing embargo implementation point."
    )
    # The canonical embargo line (from iter-v3/058 fix)
    assert "train_end_ms = test_start_ms - embargo_ms" in src, (
        "walk_forward.py:113 must implement 'train_end_ms = test_start_ms - embargo_ms'. "
        "This is the exact fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md. "
        "If this assertion fails, the walk-forward has a label-leakage lookahead bug."
    )
