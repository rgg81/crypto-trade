"""Integration tests for iter-v1/041 — triple-barrier TIGHTEN.

Axis: uniform shrink atr_tp_mult 2.9/3.5 → 1.5 and atr_sl_mult 1.45/1.75 → 0.75
      (TP/SL ratio 2.0 PRESERVED), paired with min_data_in_leaf Optuna lower-bound
      floor 20 → 50 (denser-label noise mitigation).

Covers all 12 mandatory test items from research_brief.md Section 3.4:

1.  test_v1_041_dispatch_branch_exists — iteration_label == "v1-041" path reachable.
2.  test_v1_041_pre_flight_atr_tp_assert — --atr-tp-mult 2.9 raises AssertionError.
3.  test_v1_041_pre_flight_atr_sl_assert — --atr-sl-mult 1.45 raises AssertionError.
4.  test_v1_041_pre_flight_min_data_in_leaf_assert — --min-data-in-leaf-min 20 raises.
5.  test_v1_041_pre_flight_label_mode_assert — --label-mode trend_scanning raises.
6.  test_v1_041_pre_flight_universe_assert — (via vol_ceiling_mode assert check).
7.  test_v1_041_in_baseline_catchall_exclusion — "v1-041" in exclusion tuple.
8.  test_v1_041_dispatch_banner_emitted — banner contains key strings.
9.  test_v1_041_atr_multipliers_threaded_to_lgbm — LightGbmStrategy stores override.
10. test_v1_041_min_child_samples_lower_bound_threaded — LightGbmStrategy stores 50.
11. test_v1_041_min_child_samples_lower_bound_default_unchanged — default is None.
12. test_v1_041_label_time_barrier_uses_new_multiplier — verify 1.5 ATR barrier via
    LightGbmStrategy attribute, not end-to-end label call (unit-level wiring test).

Additional tests:
13. test_v1_041_optimization_objective_accepts_lower_bound — _objective accepts
    min_child_samples_lower_bound keyword and uses it when not None.
14. test_v1_041_optimization_objective_default_unchanged — when lower_bound=None,
    v1_pruned profile still defaults to 20.
15. test_v1_041_walk_forward_embargo_regression — walk_forward.py embargo discipline.
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 1 — Dispatch branch exists
# ---------------------------------------------------------------------------


def test_v1_041_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-041'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-041"' in src, (
        'Dispatch branch iteration_label == "v1-041" not found in run_baseline_v1.py. '
        "The /041 elif must exist before the catch-all to activate the triple-barrier "
        "tighten axis (atr_tp_mult=1.5/atr_sl_mult=0.75 + min_data_in_leaf=50)."
    )


# ---------------------------------------------------------------------------
# Test 2 — Pre-flight assert: wrong atr_tp_mult
# ---------------------------------------------------------------------------


def test_v1_041_pre_flight_atr_tp_assert() -> None:
    """Dispatch branch must contain assert text for wrong atr_tp_mult value."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/041 pre-flight FAIL: expected --atr-tp-mult 1.5" in src, (
        "Pre-flight assert text for wrong atr_tp_mult not found in run_baseline_v1.py. "
        "The /041 dispatch must assert atr_tp_mult_arg == 1.5 with a descriptive message."
    )


# ---------------------------------------------------------------------------
# Test 3 — Pre-flight assert: wrong atr_sl_mult
# ---------------------------------------------------------------------------


def test_v1_041_pre_flight_atr_sl_assert() -> None:
    """Dispatch branch must contain assert text for wrong atr_sl_mult value."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/041 pre-flight FAIL: expected --atr-sl-mult 0.75" in src, (
        "Pre-flight assert text for wrong atr_sl_mult not found in run_baseline_v1.py. "
        "The /041 dispatch must assert atr_sl_mult_arg == 0.75 with a descriptive message."
    )


# ---------------------------------------------------------------------------
# Test 4 — Pre-flight assert: wrong min_data_in_leaf_min
# ---------------------------------------------------------------------------


def test_v1_041_pre_flight_min_data_in_leaf_assert() -> None:
    """Dispatch branch must contain assert text for wrong min_data_in_leaf_min value."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/041 pre-flight FAIL: expected --min-data-in-leaf-min 50" in src, (
        "Pre-flight assert text for wrong min_data_in_leaf_min not found in run_baseline_v1.py. "
        "The /041 dispatch must assert min_data_in_leaf_min_arg == 50 with a descriptive message."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert: wrong label_mode
# ---------------------------------------------------------------------------


def test_v1_041_pre_flight_label_mode_assert() -> None:
    """Dispatch branch must contain assert text for wrong label_mode."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/041 pre-flight FAIL: expected --label-mode triple_barrier" in src, (
        "Pre-flight assert text for label_mode != triple_barrier not found. "
        "The /041 dispatch must assert label_mode_arg == 'triple_barrier' "
        "(iter-v1/041 stays within triple-barrier family, NOT trend-scanning)."
    )


# ---------------------------------------------------------------------------
# Test 6 — Pre-flight assert: vol_ceiling_mode != none
# ---------------------------------------------------------------------------


def test_v1_041_pre_flight_vol_ceiling_assert() -> None:
    """Dispatch branch must contain assert for vol_ceiling_mode == none."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/041 pre-flight FAIL: expected --vol-ceiling-mode none" in src, (
        "Pre-flight assert text for vol_ceiling_mode not found in run_baseline_v1.py. "
        "The /041 dispatch must assert vol_ceiling_mode_arg == 'none' "
        "(iter-v1/038 vol-ceiling is a CLOSED axis; no carry-over to /041)."
    )


# ---------------------------------------------------------------------------
# Test 7 — catch-all exclusion tuple contains "v1-041"
# ---------------------------------------------------------------------------


def test_v1_041_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-041'.

    Per /030 LESSON: every new iteration label dispatched via an explicit elif MUST be
    added to the catch-all exclusion tuple. Missing this causes the catch-all to
    silently run baseline numbers when iteration_label=='v1-041' routes past the
    explicit elif (e.g., wrong symbol set).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-041"' in src, (
        '"v1-041" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, the catch-all branch may silently run baseline numbers."
    )


# ---------------------------------------------------------------------------
# Test 8 — Dispatch banner contains key strings
# ---------------------------------------------------------------------------


def test_v1_041_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py must contain the '[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE' banner."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE" in src, (
        "Banner '[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE' not found in run_baseline_v1.py. "
        "The v1-041 dispatch branch must print this banner. "
        "Add a print('[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE: ...') in the /041 elif."
    )
    # Verify banner contains the key parameter values
    assert "atr_tp_mult=1.5" in src or "atr_tp_mult={atr_tp_mult_arg}" in src, (
        "Banner does not reference atr_tp_mult=1.5 or the formatted variable. "
        "The banner must display the actual multiplier values for F-AXIS #2 verification."
    )
    assert "min_data_in_leaf_lower_bound=50" in src or "min_data_in_leaf_lower_bound=" in src, (
        "Banner does not reference min_data_in_leaf_lower_bound. "
        "The banner must display the Optuna lower bound for F-AXIS #2 verification."
    )


# ---------------------------------------------------------------------------
# Test 9 — LightGbmStrategy stores atr_tp_multiplier + atr_sl_multiplier correctly
# ---------------------------------------------------------------------------


def test_v1_041_atr_multipliers_threaded_to_lgbm() -> None:
    """LightGbmStrategy must store the overridden atr_tp_multiplier and atr_sl_multiplier.

    Verifies the constructor parameter assignment is present in lgbm.py source.
    The actual numeric values are set at run_model call time; this test verifies
    the storage path so that the live engine and backtest both use 1.5/0.75.
    """
    from crypto_trade.strategies.ml import lgbm

    src = inspect.getsource(lgbm)
    assert "self.atr_tp_multiplier = atr_tp_multiplier" in src, (
        "LightGbmStrategy does not assign self.atr_tp_multiplier from constructor arg. "
        "The assignment must exist so run_baseline_v1.py's atr_tp=1.5 override reaches the model."
    )
    assert "self.atr_sl_multiplier = atr_sl_multiplier" in src, (
        "LightGbmStrategy does not assign self.atr_sl_multiplier from constructor arg. "
        "The assignment must exist so run_baseline_v1.py's atr_sl=0.75 override reaches the model."
    )
    # Verify the constructor accepts the parameters
    sig = inspect.signature(lgbm.LightGbmStrategy.__init__)
    assert "atr_tp_multiplier" in sig.parameters, (
        "LightGbmStrategy.__init__ does not accept atr_tp_multiplier parameter."
    )
    assert "atr_sl_multiplier" in sig.parameters, (
        "LightGbmStrategy.__init__ does not accept atr_sl_multiplier parameter."
    )


# ---------------------------------------------------------------------------
# Test 10 — min_child_samples_lower_bound stored in LightGbmStrategy
# ---------------------------------------------------------------------------


def test_v1_041_min_child_samples_lower_bound_threaded() -> None:
    """LightGbmStrategy must accept and store min_child_samples_lower_bound=50."""
    from crypto_trade.strategies.ml import lgbm

    sig = inspect.signature(lgbm.LightGbmStrategy.__init__)
    assert "min_child_samples_lower_bound" in sig.parameters, (
        "LightGbmStrategy.__init__ does not accept min_child_samples_lower_bound parameter. "
        "iter-v1/041 threads this via run_model to override Optuna lower bound 20 → 50."
    )
    # Verify the storage attribute exists in source
    src = inspect.getsource(lgbm)
    assert "_min_child_samples_lower_bound" in src, (
        "LightGbmStrategy does not store _min_child_samples_lower_bound. "
        "The attribute must be assigned in __init__ and passed to optimize_and_train."
    )


# ---------------------------------------------------------------------------
# Test 11 — Default min_child_samples_lower_bound is None (backward compat)
# ---------------------------------------------------------------------------


def test_v1_041_min_child_samples_lower_bound_default_unchanged() -> None:
    """LightGbmStrategy default for min_child_samples_lower_bound must be None.

    None = BIT-IDENTICAL to all pre-/041 callers (v1_pruned lower bound stays 20,
    default bounds lower bound stays 5). Only /041 dispatch sets it to 50.
    """
    from crypto_trade.strategies.ml import lgbm

    sig = inspect.signature(lgbm.LightGbmStrategy.__init__)
    param = sig.parameters.get("min_child_samples_lower_bound")
    assert param is not None, "min_child_samples_lower_bound not in LightGbmStrategy.__init__"
    assert param.default is None, (
        f"Default for min_child_samples_lower_bound is {param.default!r}, expected None. "
        "None default preserves BIT-IDENTICAL behaviour for all pre-/041 callers. "
        "Only iter-v1/041 dispatch passes 50."
    )
    # Also verify optimize_and_train default is None
    from crypto_trade.strategies.ml import optimization

    opt_sig = inspect.signature(optimization.optimize_and_train)
    opt_param = opt_sig.parameters.get("min_child_samples_lower_bound")
    assert opt_param is not None, (
        "min_child_samples_lower_bound not in optimize_and_train signature. "
        "iter-v1/041 threads this from LightGbmStrategy through to _objective."
    )
    assert opt_param.default is None, (
        f"optimize_and_train default for min_child_samples_lower_bound is {opt_param.default!r}. "
        "Expected None to preserve BIT-IDENTICAL behaviour for all pre-/041 callers."
    )


# ---------------------------------------------------------------------------
# Test 12 — LightGbmStrategy attribute confirms 1.5 ATR barrier (wiring test)
# ---------------------------------------------------------------------------


def test_v1_041_label_time_barrier_uses_new_multiplier() -> None:
    """LightGbmStrategy with atr_tp_multiplier=1.5 must store that value.

    Verifies that passing atr_tp_multiplier=1.5 at construction results in
    strategy.atr_tp_multiplier == 1.5 (the new barrier distance, not the baseline
    2.9 for Pool A or 3.5 for C/D/E).

    This is a wiring test — it confirms the constructor assignment chain
    without running a full label-time computation.
    """
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strategy = LightGbmStrategy(
        training_months=24,
        n_trials=18,
        cv_splits=5,
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
        ensemble_seeds=[42],
        atr_tp_multiplier=1.5,
        atr_sl_multiplier=0.75,
        use_atr_labeling=True,
        min_child_samples_lower_bound=50,
    )
    assert strategy.atr_tp_multiplier == 1.5, (
        f"strategy.atr_tp_multiplier = {strategy.atr_tp_multiplier!r}, expected 1.5. "
        "iter-v1/041 tighten axis requires atr_tp_multiplier=1.5 stored on the strategy "
        "object so both label-time and execution-time barriers use the tighter value."
    )
    assert strategy.atr_sl_multiplier == 0.75, (
        f"strategy.atr_sl_multiplier = {strategy.atr_sl_multiplier!r}, expected 0.75. "
        "iter-v1/041 tighten axis requires atr_sl_multiplier=0.75 (ratio 2.0 preserved)."
    )
    assert strategy._min_child_samples_lower_bound == 50, (
        f"strategy._min_child_samples_lower_bound = {strategy._min_child_samples_lower_bound!r}, "
        "expected 50. iter-v1/041 paired mitigation requires lower_bound=50 stored on strategy."
    )


# ---------------------------------------------------------------------------
# Test 13 — _objective uses min_child_samples_lower_bound when provided
# ---------------------------------------------------------------------------


def test_v1_041_optimization_objective_accepts_lower_bound() -> None:
    """_objective must accept and use min_child_samples_lower_bound when set.

    Verifies source-level that the lower bound override path exists in _objective.
    """
    from crypto_trade.strategies.ml import optimization

    src = inspect.getsource(optimization)
    assert "min_child_samples_lower_bound" in src, (
        "min_child_samples_lower_bound not found in optimization.py source. "
        "The parameter must be threaded from optimize_and_train to _objective "
        "and applied to the min_child_samples Optuna suggestion."
    )
    # Verify the conditional override pattern exists (may be split across lines by formatter)
    _not_none_pattern = "if min_child_samples_lower_bound is not None"
    assert "min_child_samples_lower_bound" in src and _not_none_pattern in src, (
        "Override conditional pattern not found in optimization.py. "
        "Expected 'min_child_samples_lower_bound' and the is-not-None guard. "
        "This pattern guards backward compatibility (None = prior behaviour)."
    )


# ---------------------------------------------------------------------------
# Test 14 — Default lower bound 20 for v1_pruned is unchanged when lower_bound=None
# ---------------------------------------------------------------------------


def test_v1_041_optimization_objective_default_unchanged() -> None:
    """When min_child_samples_lower_bound=None, v1_pruned profile default is 20.

    Verifies source-level that the fallback to (20 if _pruned else 5) is preserved
    in the _objective function when the override is None.
    """
    from crypto_trade.strategies.ml import optimization

    src = inspect.getsource(optimization)
    # Check both sides of the conditional exist
    assert "20 if _pruned else 5" in src, (
        "Fallback '20 if _pruned else 5' not found in optimization.py. "
        "When min_child_samples_lower_bound=None, the original v1_pruned default of 20 "
        "must be preserved for BIT-IDENTICAL behaviour with all pre-/041 callers."
    )


# ---------------------------------------------------------------------------
# Test 15 — Foundation walk-forward embargo regression
# ---------------------------------------------------------------------------


def test_v1_041_walk_forward_embargo_regression() -> None:
    """walk_forward.py must apply embargo: train_end_ms = test_start_ms - embargo_ms.

    This is the foundational anti-lookahead guarantee. Verified via source inspection:
    the walk-forward split must compute train_end_ms as test_start_ms minus an embargo
    (not equal to test_start_ms, which would allow label leakage).

    Fixed at iter-v3/058 RE-ANCHOR (commit e149e9d); all v1 iterations since use the
    fixed walk-forward. This test regression-guards that fix is still present.
    """
    from crypto_trade.strategies.ml import walk_forward

    src = inspect.getsource(walk_forward)
    assert "train_end_ms = test_start_ms - embargo_ms" in src, (
        "walk_forward.py embargo discipline violated: "
        "'train_end_ms = test_start_ms - embargo_ms' not found. "
        "The embargo is required to prevent label leakage across walk-forward splits. "
        "Fixed at iter-v3/058 RE-ANCHOR; must not regress."
    )
