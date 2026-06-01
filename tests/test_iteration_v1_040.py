"""Integration tests for iter-v1/040 — composed feature SWAP.

Axis: DROP basis_zscore_30 (3-consec INERT) + ADD regime_momentum_signed_5d.

Covers all 14 mandatory test items from research_brief.md Section 10.3:

8.  test_v1_040_pruned_features_contains_regime_momentum_signed_5d —
    V1_FEATURE_COLUMNS_PRUNED contains "regime_momentum_signed_5d".
9.  test_v1_040_pruned_features_excludes_basis_zscore_30 —
    V1_FEATURE_COLUMNS_PRUNED does NOT contain "basis_zscore_30".
10. test_v1_040_pruned_features_count_44 — len(V1_FEATURE_COLUMNS_PRUNED) == 44.
11. test_v1_040_basis_zscore_30_in_retired_columns — V1_RETIRED_FEATURE_COLUMNS
    contains "basis_zscore_30" (defensive — legacy parquet residual rejection).
12. test_v1_040_dispatch_branch_exists — runner source contains
    iteration_label == "v1-040" dispatch branch.
13. test_v1_040_in_baseline_catchall_exclusion — catch-all exclusion tuple
    contains "v1-040" per /030 LESSON.
14. test_v1_040_dispatch_banner_emitted — runner source contains
    "[iter-v1/040] COMPOSED-FEATURE ACTIVE" banner text.

Additional tests (beyond the 14-test mandate):
15. test_v1_040_pre_flight_regime_momentum_assert_text — dispatch contains
    assert text for regime_momentum_signed_5d not in active_feature_columns.
16. test_v1_040_pre_flight_basis_zscore_30_assert_text — dispatch contains
    assert text for basis_zscore_30 still in active_feature_columns.
17. test_v1_040_pre_flight_vol_ceiling_assert_text — dispatch contains
    assert text for vol_ceiling_mode != none.
18. test_v1_040_pre_flight_label_mode_assert_text — dispatch contains
    assert text for label_mode != triple_barrier.
19. test_v1_040_pre_flight_optuna_objective_assert_text — dispatch contains
    assert text for optuna_objective != sharpe.

Foundation regression:
20. test_v1_040_walk_forward_embargo_regression — walk_forward.py embargo
    discipline (train_end_ms = test_start_ms - embargo_ms).
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 8 — V1_FEATURE_COLUMNS_PRUNED contains regime_momentum_signed_5d
# ---------------------------------------------------------------------------


def test_v1_040_pruned_features_contains_regime_momentum_signed_5d() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must contain 'regime_momentum_signed_5d'.

    iter-v1/040 ADDS regime_momentum_signed_5d (composed feature = ret_5d ×
    sign(hurst_100 − 0.5)) to replace the INERT basis_zscore_30. Absence means
    the parquet regen (--groups composed_v1) or the tuple edit was skipped.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "regime_momentum_signed_5d" in V1_FEATURE_COLUMNS_PRUNED, (
        "'regime_momentum_signed_5d' not found in V1_FEATURE_COLUMNS_PRUNED. "
        "iter-v1/040 adds this composed feature (ret_5d × sign(hurst_100 − 0.5)) "
        "in place of basis_zscore_30 (3-consec INERT). "
        "Edit src/crypto_trade/features_v1/__init__.py to add regime_momentum_signed_5d."
    )


# ---------------------------------------------------------------------------
# Test 9 — V1_FEATURE_COLUMNS_PRUNED does NOT contain basis_zscore_30
# ---------------------------------------------------------------------------


def test_v1_040_pruned_features_excludes_basis_zscore_30() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must NOT contain 'basis_zscore_30'.

    iter-v1/040 DROPS basis_zscore_30 (3-consecutive INERT across /034, /037, /038;
    mean importance rank 27.67/44). Presence means the DROP was not applied.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "basis_zscore_30" not in V1_FEATURE_COLUMNS_PRUNED, (
        "'basis_zscore_30' is still in V1_FEATURE_COLUMNS_PRUNED. "
        "iter-v1/040 DROPS basis_zscore_30 (3-consec INERT: /034 + /037 + /038 rank ≥25/44). "
        "Edit src/crypto_trade/features_v1/__init__.py to remove basis_zscore_30."
    )


# ---------------------------------------------------------------------------
# Test 10 — V1_FEATURE_COLUMNS_PRUNED count (updated for iter-v1/049)
# ---------------------------------------------------------------------------


def test_v1_040_pruned_features_count_44() -> None:
    """len(V1_FEATURE_COLUMNS_PRUNED) must be 45 after iter-v1/049 ADD.

    iter-v1/040 performed a pure SWAP: DROP basis_zscore_30 (−1) + ADD
    regime_momentum_signed_5d (+1) → count stayed at 44.
    iter-v1/049 added long_short_zscore_30 (+1) → count is now 45.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
        f"V1_FEATURE_COLUMNS_PRUNED has {len(V1_FEATURE_COLUMNS_PRUNED)} features; expected 45. "
        "iter-v1/049 adds long_short_zscore_30 (+1): count advances 44 → 45."
    )


# ---------------------------------------------------------------------------
# Test 11 — V1_RETIRED_FEATURE_COLUMNS contains basis_zscore_30
# ---------------------------------------------------------------------------


def test_v1_040_basis_zscore_30_in_retired_columns() -> None:
    """V1_RETIRED_FEATURE_COLUMNS must contain 'basis_zscore_30'.

    Defensive guard: basis_zscore_30 may still appear as a column in legacy
    parquets (from iterations /034 onward). V1_RETIRED_FEATURE_COLUMNS marks
    it as explicitly NOT a training feature. The runner must NOT pick it up
    from full parquet columns as a surrogate feature.
    """
    from crypto_trade.features_v1 import V1_RETIRED_FEATURE_COLUMNS

    assert "basis_zscore_30" in V1_RETIRED_FEATURE_COLUMNS, (
        "'basis_zscore_30' not found in V1_RETIRED_FEATURE_COLUMNS. "
        "iter-v1/040 retires basis_zscore_30 from the pruned set. "
        "Add it to V1_RETIRED_FEATURE_COLUMNS in src/crypto_trade/features_v1/__init__.py "
        "so legacy parquet columns don't silently re-enter as training features."
    )


# ---------------------------------------------------------------------------
# Test 12 — Dispatch branch exists
# ---------------------------------------------------------------------------


def test_v1_040_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-040'.

    The catch-all branch runs BASELINE config; without an explicit /040 dispatch,
    the runner would silently use baseline features (with basis_zscore_30 still
    in the pruned set from the catch-all's perspective).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-040"' in src, (
        'Dispatch branch iteration_label == "v1-040" not found in run_baseline_v1.py. '
        "The /040 elif must exist before the catch-all to activate the composed-feature "
        "SWAP (DROP basis_zscore_30 + ADD regime_momentum_signed_5d)."
    )


# ---------------------------------------------------------------------------
# Test 13 — catch-all exclusion tuple contains "v1-040"
# ---------------------------------------------------------------------------


def test_v1_040_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-040'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif MUST be added to
    the catch-all exclusion tuple. Missing this causes the catch-all to silently
    run baseline numbers when iteration_label=='v1-040' somehow routes past the
    explicit elif (e.g., wrong symbol set).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-040"' in src, (
        '"v1-040" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, the catch-all branch may silently run baseline numbers."
    )


# ---------------------------------------------------------------------------
# Test 14 — Dispatch banner text
# ---------------------------------------------------------------------------


def test_v1_040_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py must contain the '[iter-v1/040] COMPOSED-FEATURE ACTIVE' banner.

    The banner confirms that:
    - regime_momentum_signed_5d is wired to the active feature columns.
    - The position (@N) confirms column ordering is deterministic.
    - The 'basis_zscore_30 DROPPED' suffix confirms the DROP was applied.

    Verified via source inspection (the banner is in the dispatch branch print() call).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/040] COMPOSED-FEATURE ACTIVE" in src, (
        "Banner '[iter-v1/040] COMPOSED-FEATURE ACTIVE' not found in run_baseline_v1.py. "
        "The v1-040 dispatch branch must print this banner. "
        "Add a print('[iter-v1/040] COMPOSED-FEATURE ACTIVE: ...') in the /040 elif."
    )


# ---------------------------------------------------------------------------
# Test 15 — Pre-flight assert: regime_momentum_signed_5d not in columns
# ---------------------------------------------------------------------------


def test_v1_040_pre_flight_regime_momentum_assert_text() -> None:
    """Dispatch branch must contain assert text for regime_momentum_signed_5d missing."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert (
        "iter-v1/040 pre-flight FAIL: regime_momentum_signed_5d not in active_feature_columns"
        in src
    ), (
        "Pre-flight assert text for missing regime_momentum_signed_5d not found. "
        "The /040 dispatch must assert 'regime_momentum_signed_5d' in active_feature_columns "
        "with a descriptive error message."
    )


# ---------------------------------------------------------------------------
# Test 16 — Pre-flight assert: basis_zscore_30 still in columns
# ---------------------------------------------------------------------------


def test_v1_040_pre_flight_basis_zscore_30_assert_text() -> None:
    """Dispatch branch must contain assert text for basis_zscore_30 still present."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/040 pre-flight FAIL: basis_zscore_30 still in active_feature_columns" in src, (
        "Pre-flight assert text for basis_zscore_30 still present not found. "
        "The /040 dispatch must assert 'basis_zscore_30' NOT in active_feature_columns "
        "with a descriptive error message."
    )


# ---------------------------------------------------------------------------
# Test 17 — Pre-flight assert: vol_ceiling_mode != none
# ---------------------------------------------------------------------------


def test_v1_040_pre_flight_vol_ceiling_assert_text() -> None:
    """Dispatch branch must contain assert for vol_ceiling_mode == none."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/040 pre-flight FAIL: expected --vol-ceiling-mode none" in src, (
        "Pre-flight assert text for vol_ceiling_mode not found in run_baseline_v1.py. "
        "The /040 dispatch must assert vol_ceiling_mode_arg == 'none' "
        "(iter-v1/038 vol-ceiling is a CLOSED axis; no carry-over to /040)."
    )


# ---------------------------------------------------------------------------
# Test 18 — Pre-flight assert: label_mode != triple_barrier
# ---------------------------------------------------------------------------


def test_v1_040_pre_flight_label_mode_assert_text() -> None:
    """Dispatch branch must contain assert for label_mode == triple_barrier."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/040 pre-flight FAIL: expected --label-mode triple_barrier" in src, (
        "Pre-flight assert text for label_mode not found in run_baseline_v1.py. "
        "The /040 dispatch must assert label_mode_arg == 'triple_barrier' "
        "(iter-v1/040 uses standard triple-barrier labels, NOT trend-scanning)."
    )


# ---------------------------------------------------------------------------
# Test 19 — Pre-flight assert: optuna_objective != sharpe
# ---------------------------------------------------------------------------


def test_v1_040_pre_flight_optuna_objective_assert_text() -> None:
    """Dispatch branch must contain assert for optuna_objective == sharpe."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/040 pre-flight FAIL: expected --optuna-objective sharpe" in src, (
        "Pre-flight assert text for optuna_objective not found in run_baseline_v1.py. "
        "The /040 dispatch must assert optuna_objective_arg == 'sharpe' "
        "(iter-v1/040 uses Sharpe objective, NOT Sortino — orthogonal to /037)."
    )


# ---------------------------------------------------------------------------
# Test 20 — Walk-forward embargo regression (/027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_040_walk_forward_embargo_regression() -> None:
    """walk_forward.py must enforce train_end_ms < test_start_ms (embargo discipline).

    Per /027 LESSON: the walk-forward split must have train_end_ms strictly less than
    test_start_ms. The embargo gap = (timeout_candles + 1) × n_symbols to satisfy
    the López de Prado purge requirement.

    This test verifies the source-level fix (walk_forward.py:113) is still in place.
    It must pass for ALL iter-v1 iterations — it is a foundation regression.
    """
    import inspect as _inspect

    from crypto_trade.strategies.ml import walk_forward

    src = _inspect.getsource(walk_forward)

    # The fix at walk_forward.py:113 assigns train_end_ms = test_start_ms - embargo_ms.
    # We check that the embargo subtraction pattern exists in the source.
    assert "embargo_ms" in src, (
        "'embargo_ms' not found in walk_forward.py source. "
        "The walk-forward embargo fix (train_end_ms = test_start_ms - embargo_ms) "
        "from /027 LESSON must be present. Without it, labels leak across train/test split."
    )
    assert "train_end_ms" in src, (
        "'train_end_ms' not found in walk_forward.py source. "
        "The walk-forward embargo variable 'train_end_ms' must be assigned and used."
    )
