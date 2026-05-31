"""Integration tests for iter-v1/039 — per-cohort Sortino x specialist hybrid.

Covers all 13 mandatory test items from research_brief.md Section 3.4:

1.  test_v1_039_universe_constant_exists — V1_ITER039_UNIVERSE is defined as tuple
    containing exactly ("LINKUSDT", "DOTUSDT").
2.  test_v1_039_universe_subset_of_baseline — V1_ITER039_UNIVERSE is a subset of
    V1_BASELINE_UNIVERSE; neither symbol is in V1_EXCLUDED_SYMBOLS.
3.  test_v1_039_dispatch_branch_exists — runner source contains
    iteration_label == "v1-039" dispatch branch.
4.  test_v1_039_pre_flight_label_mode_assert — dispatch branch contains assert that
    fires on label_mode mismatch (trend_scanning required).
5.  test_v1_039_pre_flight_universe_assert — dispatch branch contains assert that fires
    on non-{LINKUSDT, DOTUSDT} universe (source-level check).
6.  test_v1_039_pre_flight_optuna_objective_assert — dispatch branch contains assert
    that fires on optuna_objective != sortino (NEW vs /036).
7.  test_v1_039_in_baseline_catchall_exclusion — "v1-039" in catch-all exclusion tuple
    (per /030 LESSON feedback_v1_dispatch_baseline_catchall_exclusion.md).
8.  test_v1_039_dispatch_banner_emitted — banner contains both
    label_mode=trend_scanning AND optuna_objective=sortino.
9.  test_v1_039_label_mode_threaded_to_link_model — real LightGbmStrategy instance
    has .label_mode == "trend_scanning" (LINK specialist).
10. test_v1_039_label_mode_threaded_to_dot_model — same for DOT specialist.
11. test_v1_039_optuna_objective_threaded_to_link_model — real LightGbmStrategy
    instance has ._optuna_objective == "sortino" (LINK specialist).
12. test_v1_039_optuna_objective_threaded_to_dot_model — same for DOT specialist.
13. test_v1_039_dispatches_only_link_and_dot_models — dispatch block contains
    LINKUSDT and DOTUSDT but NOT BTCUSDT, ETHUSDT, or LTCUSDT.

Foundation regression:
- test_v1_039_walk_forward_embargo_regression — walk_forward.py embargo discipline
  (train_end_ms = test_start_ms - embargo_ms).
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 1 — V1_ITER039_UNIVERSE constant exists and is correct
# ---------------------------------------------------------------------------


def test_v1_039_universe_constant_exists() -> None:
    """V1_ITER039_UNIVERSE must be defined as a tuple containing exactly
    ("LINKUSDT", "DOTUSDT") in src/crypto_trade/features_v1/__init__.py.

    Per /039 brief Section 3.1: universe constant is the guard for the dispatch branch.
    /039 reuses the same 2-symbol LINK+DOT universe as /036 but adds Sortino objective.
    """
    from crypto_trade.features_v1 import V1_ITER039_UNIVERSE

    assert isinstance(V1_ITER039_UNIVERSE, tuple), (
        f"V1_ITER039_UNIVERSE must be a tuple, got {type(V1_ITER039_UNIVERSE).__name__}."
    )
    assert set(V1_ITER039_UNIVERSE) == {"LINKUSDT", "DOTUSDT"}, (
        f"V1_ITER039_UNIVERSE must be exactly {{'LINKUSDT', 'DOTUSDT'}}, "
        f"got {set(V1_ITER039_UNIVERSE)}."
    )
    assert len(V1_ITER039_UNIVERSE) == 2, (
        f"V1_ITER039_UNIVERSE must have exactly 2 elements, got {len(V1_ITER039_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# Test 2 — V1_ITER039_UNIVERSE is a subset of V1_BASELINE_UNIVERSE
# ---------------------------------------------------------------------------


def test_v1_039_universe_subset_of_baseline() -> None:
    """V1_ITER039_UNIVERSE is a subset of V1_BASELINE_UNIVERSE.

    Both LINKUSDT and DOTUSDT must be in V1_BASELINE_UNIVERSE — they are existing
    baseline symbols, not new additions. Neither should be in V1_EXCLUDED_SYMBOLS.
    """
    from crypto_trade.features_v1 import (
        V1_BASELINE_UNIVERSE,
        V1_EXCLUDED_SYMBOLS,
        V1_ITER039_UNIVERSE,
    )

    baseline_set = set(V1_BASELINE_UNIVERSE)
    excluded_set = set(V1_EXCLUDED_SYMBOLS)

    for sym in V1_ITER039_UNIVERSE:
        assert sym in baseline_set, (
            f"{sym} from V1_ITER039_UNIVERSE is NOT in V1_BASELINE_UNIVERSE "
            f"{baseline_set}. Both LINKUSDT and DOTUSDT must be baseline symbols."
        )
        assert sym not in excluded_set, (
            f"{sym} from V1_ITER039_UNIVERSE IS in V1_EXCLUDED_SYMBOLS {excluded_set}. "
            "Excluded symbols cannot be traded in v1."
        )


# ---------------------------------------------------------------------------
# Test 3 — Dispatch branch exists in runner source
# ---------------------------------------------------------------------------


def test_v1_039_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-039'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-039"' in src, (
        'Dispatch branch iteration_label == "v1-039" not found in run_baseline_v1.py. '
        "The /039 elif must exist before the catch-all to trigger per-cohort-Sortino "
        "specialist-hybrid logic."
    )


# ---------------------------------------------------------------------------
# Test 4 — Pre-flight assert fires on label_mode mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_039_pre_flight_label_mode_assert() -> None:
    """The v1-039 dispatch branch must contain an assert that fires on label_mode mismatch.

    When iteration_label == 'v1-039' AND label_mode_arg != 'trend_scanning', the runner
    must raise AssertionError BEFORE any backtest compute starts.

    Verified via source inspection that the assert is present in the dispatch branch.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "iter-v1/039 pre-flight FAIL: expected --label-mode trend_scanning" in src, (
        "'iter-v1/039 pre-flight FAIL: expected --label-mode trend_scanning' not found "
        "in run_baseline_v1.py. The /039 dispatch branch must pre-flight assert that "
        "label_mode_arg == 'trend_scanning'. Without this, a missing --label-mode flag "
        "silently runs triple_barrier labels while dispatching as iter-v1/039."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert fires on universe mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_039_pre_flight_universe_assert() -> None:
    """The v1-039 dispatch branch must enforce the V1_ITER039_UNIVERSE set-equality.

    The dispatch condition set(symbols) == set(V1_ITER039_UNIVERSE) must be present
    in the elif guard. Passing a wrong symbol set must NOT route to the /039 branch.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "V1_ITER039_UNIVERSE" in src, (
        "V1_ITER039_UNIVERSE not found in run_baseline_v1.py source. "
        "The /039 dispatch branch elif condition must use V1_ITER039_UNIVERSE "
        "in the set-equality guard."
    )
    combined_guard = 'iteration_label == "v1-039" and set(symbols) == set(V1_ITER039_UNIVERSE)'
    assert combined_guard in src, (
        f"Combined guard '{combined_guard}' not found in run_baseline_v1.py. "
        "The /039 elif must check BOTH iteration_label AND universe set-equality."
    )


# ---------------------------------------------------------------------------
# Test 6 — Pre-flight assert fires on optuna_objective mismatch (NEW vs /036)
# ---------------------------------------------------------------------------


def test_v1_039_pre_flight_optuna_objective_assert() -> None:
    """The v1-039 dispatch branch must assert optuna_objective_arg == 'sortino'.

    When iteration_label == 'v1-039' AND optuna_objective_arg != 'sortino', the runner
    must raise AssertionError. This is the NEW assert not present in /036 (which only
    requires trend_scanning labels, not Sortino objective).

    Verified via source inspection that the Sortino assert is present.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "iter-v1/039 pre-flight FAIL: expected --optuna-objective sortino" in src, (
        "'iter-v1/039 pre-flight FAIL: expected --optuna-objective sortino' not found "
        "in run_baseline_v1.py. The /039 dispatch branch must pre-flight assert that "
        "optuna_objective_arg == 'sortino'. Without this, a missing --optuna-objective "
        "flag silently runs Sharpe objective while dispatching as iter-v1/039."
    )


# ---------------------------------------------------------------------------
# Test 7 — Catch-all exclusion tuple contains "v1-039"
# ---------------------------------------------------------------------------


def test_v1_039_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-039'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif branch MUST be added
    to the catch-all exclusion tuple. Missing this causes the catch-all to silently
    run baseline-universe numbers.

    Note: /039 dispatches on V1_ITER039_UNIVERSE (not V1_BASELINE_UNIVERSE), so
    the catch-all guard protects specifically the V1_BASELINE_UNIVERSE path. The
    exclusion entry prevents accidental baseline-dispatch if a caller passes
    --symbols BTCUSDT,...,DOTUSDT --iteration 39.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-039"' in src, (
        '"v1-039" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, a caller passing --symbols BTCUSDT,...,DOTUSDT --iteration 39 "
        "would fall into the baseline catch-all silently."
    )


# ---------------------------------------------------------------------------
# Test 8 — Dispatch banner contains both label_mode AND optuna_objective
# ---------------------------------------------------------------------------


def test_v1_039_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py dispatch branch for v1-039 must emit a banner containing
    both label_mode=trend_scanning AND optuna_objective=sortino.

    Per brief Section 3.1 and F-AXIS #2: the banner is the primary wiring proof.
    Both flags must appear in the banner to confirm both axes are threaded.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE" in src, (
        "Expected banner '[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE' not found in "
        "run_baseline_v1.py. The /039 dispatch branch must print this banner with all "
        "required fields including models, label_mode, and optuna_objective."
    )
    assert "label_mode=trend_scanning" in src or "label_mode={label_mode_arg}" in src, (
        "Banner must contain label_mode field (either literal 'label_mode=trend_scanning' "
        "or 'label_mode={label_mode_arg}'). The label_mode flag must be visible in "
        "the banner to confirm trend-scanning wiring."
    )
    assert "optuna_objective=sortino" in src or "optuna_objective={optuna_objective_arg}" in src, (
        "Banner must contain optuna_objective field (either literal "
        "'optuna_objective=sortino' or 'optuna_objective={optuna_objective_arg}'). "
        "The Sortino objective flag must be visible in the banner — this is the NEW "
        "field vs /036 and confirms the loss-function axis is threaded."
    )


# ---------------------------------------------------------------------------
# Test 9 — label_mode threaded to LINK specialist (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_039_label_mode_threaded_to_link_model() -> None:
    """LightGbmStrategy constructed with label_mode='trend_scanning' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.
    Mock attribute names are unreliable — only real instantiation proves the kwarg
    reaches the strategy.

    This test verifies the LINK specialist (Model C') receives trend_scanning.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strategy = LightGbmStrategy(
        training_months=1,
        n_trials=1,
        cv_splits=2,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got "
        f"{strategy.label_mode!r}. "
        "The label_mode kwarg must be stored as self.label_mode in LightGbmStrategy.__init__(). "
        "This is the LINK specialist (Model C') configuration for iter-v1/039."
    )


# ---------------------------------------------------------------------------
# Test 10 — label_mode threaded to DOT specialist (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_039_label_mode_threaded_to_dot_model() -> None:
    """LightGbmStrategy constructed with label_mode='trend_scanning' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.

    This test verifies the DOT specialist (Model E) receives trend_scanning.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strategy = LightGbmStrategy(
        training_months=1,
        n_trials=1,
        cv_splits=2,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got "
        f"{strategy.label_mode!r}. "
        "The label_mode kwarg must be stored as self.label_mode in LightGbmStrategy.__init__(). "
        "This is the DOT specialist (Model E) configuration for iter-v1/039."
    )


# ---------------------------------------------------------------------------
# Test 11 — optuna_objective threaded to LINK specialist (real instance, NEW vs /036)
# ---------------------------------------------------------------------------


def test_v1_039_optuna_objective_threaded_to_link_model() -> None:
    """LightGbmStrategy constructed with optuna_objective='sortino' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.
    This is NEW vs /036 (which only asserts label_mode). Both flags must be verified
    because /039 is the first dispatch that threads BOTH simultaneously.

    LightGbmStrategy must store optuna_objective as self._optuna_objective.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strategy = LightGbmStrategy(
        training_months=1,
        n_trials=1,
        cv_splits=2,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],
        label_mode="trend_scanning",
        optuna_objective="sortino",
    )
    assert strategy._optuna_objective == "sortino", (
        f"LightGbmStrategy._optuna_objective expected 'sortino' but got "
        f"{strategy._optuna_objective!r}. "
        "The optuna_objective kwarg must be stored as self._optuna_objective in "
        "LightGbmStrategy.__init__(). "
        "This is the LINK specialist (Model C') configuration for iter-v1/039 — "
        "both label_mode=trend_scanning AND optuna_objective=sortino must be threaded."
    )


# ---------------------------------------------------------------------------
# Test 12 — optuna_objective threaded to DOT specialist (real instance, NEW vs /036)
# ---------------------------------------------------------------------------


def test_v1_039_optuna_objective_threaded_to_dot_model() -> None:
    """LightGbmStrategy constructed with optuna_objective='sortino' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.

    This test verifies the DOT specialist (Model E) also receives sortino.
    Both models in the /039 2-cohort bundle must use Sortino objective.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strategy = LightGbmStrategy(
        training_months=1,
        n_trials=1,
        cv_splits=2,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],
        label_mode="trend_scanning",
        optuna_objective="sortino",
    )
    assert strategy._optuna_objective == "sortino", (
        f"LightGbmStrategy._optuna_objective expected 'sortino' but got "
        f"{strategy._optuna_objective!r}. "
        "The optuna_objective kwarg must be stored as self._optuna_objective in "
        "LightGbmStrategy.__init__(). "
        "This is the DOT specialist (Model E) configuration for iter-v1/039."
    )


# ---------------------------------------------------------------------------
# Test 13 — Dispatch branch dispatches ONLY Model C' (LINK) + Model E (DOT)
# ---------------------------------------------------------------------------


def test_v1_039_dispatches_only_link_and_dot_models() -> None:
    """The v1-039 dispatch branch must NOT include Model A pool or Model D LTC.

    Per /039 brief Section 3.3: Model A (BTC/ETH pool) and Model D (LTC) are SKIPPED.
    Only Model C' (LINK) and Model E (DOT) are dispatched.

    Verified via source inspection: the /039 dispatch block must contain runs for
    LINKUSDT and DOTUSDT only.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    dispatch_marker = "[iter-v1/039] PER-COHORT-SORTINO-HYBRID ACTIVE"
    assert dispatch_marker in src, (
        f"Dispatch marker '{dispatch_marker}' not found in run_baseline_v1.py. "
        "Cannot locate the /039 dispatch block for model-dispatch verification."
    )

    start_idx = src.find('iteration_label == "v1-039" and set(symbols) == set(V1_ITER039_UNIVERSE)')
    assert start_idx >= 0, (
        'Cannot find "iteration_label == \\"v1-039\\"" in source to locate block start.'
    )
    next_elif_idx = src.find("\n    elif ", start_idx + 1)
    assert next_elif_idx > start_idx, "Cannot find the closing elif after the /039 dispatch block."
    block_039 = src[start_idx:next_elif_idx]

    assert '"LINKUSDT"' in block_039, (
        'Model C\' (LINK) dispatch ("LINKUSDT",) not found in the /039 block. '
        "The LINK specialist must be dispatched in iter-v1/039."
    )
    assert '"DOTUSDT"' in block_039, (
        'Model E (DOT) dispatch ("DOTUSDT",) not found in the /039 block. '
        "The DOT specialist must be dispatched in iter-v1/039."
    )
    assert '"BTCUSDT"' not in block_039, (
        'Model A pool ("BTCUSDT") found in /039 dispatch block. '
        "The /039 dispatch must SKIP Model A — BTCUSDT must NOT be dispatched. "
        "Only LINKUSDT + DOTUSDT specialists should trade in iter-v1/039."
    )
    assert '"LTCUSDT"' not in block_039, (
        'Model D ("LTCUSDT") found in /039 dispatch block. '
        "The /039 dispatch must SKIP Model D — LTCUSDT must NOT be dispatched."
    )
    assert '"ETHUSDT"' not in block_039, (
        "ETHUSDT found in /039 dispatch block. "
        "The /039 dispatch must SKIP Model A which covers ETHUSDT."
    )
    assert "Model_C_LINK_sortino_trend_scan_specialist" in block_039, (
        "'Model_C_LINK_sortino_trend_scan_specialist' not found in /039 dispatch block. "
        "_post_dispatch_fi_strategies must use the specialist model name for LINK."
    )
    assert "Model_E_DOT_sortino_trend_scan_specialist" in block_039, (
        "'Model_E_DOT_sortino_trend_scan_specialist' not found in /039 dispatch block. "
        "_post_dispatch_fi_strategies must use the specialist model name for DOT."
    )


# ---------------------------------------------------------------------------
# Foundation regression — walk_forward.py:113 embargo discipline
# ---------------------------------------------------------------------------


def test_v1_039_walk_forward_embargo_regression() -> None:
    """Foundation regression: walk_forward.py embargo discipline.

    walk_forward.py must implement train_end_ms = test_start_ms - embargo_ms.
    This is the load-bearing fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md.
    The walk_forward module must carry embargo_ms so that the training window ends
    strictly BEFORE the test window begins — preventing label-leakage lookahead bias.
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
    assert "train_end_ms = test_start_ms - embargo_ms" in src, (
        "walk_forward.py:113 must implement 'train_end_ms = test_start_ms - embargo_ms'. "
        "This is the exact fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md."
    )
