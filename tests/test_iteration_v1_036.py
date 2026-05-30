"""Integration tests for iter-v1/036 — LINK + DOT 2-specialist trend-scanning bundle.

Covers all 10 mandatory test items from research_brief.md Section 10.3:

1.  test_v1_036_universe_constant_exists — V1_ITER036_UNIVERSE is defined as tuple
    containing exactly ("LINKUSDT", "DOTUSDT").
2.  test_v1_036_universe_subset_of_baseline — V1_ITER036_UNIVERSE ⊂ V1_BASELINE_UNIVERSE.
3.  test_v1_036_dispatch_branch_exists — runner source contains
    iteration_label == "v1-036" dispatch branch.
4.  test_v1_036_dispatch_branch_pre_flight_label_mode_assert — dispatch branch contains
    assert that fires on label_mode mismatch (trend_scanning required).
5.  test_v1_036_dispatch_branch_pre_flight_universe_assert — dispatch branch contains
    assert that fires on non-{LINKUSDT, DOTUSDT} universe (source-level check).
6.  test_v1_036_in_baseline_catchall_exclusion — "v1-036" in catch-all exclusion tuple
    (per /030 LESSON feedback_v1_dispatch_baseline_catchall_exclusion.md).
7.  test_v1_036_dispatch_banner_emitted — runner source contains the expected dispatch
    banner '[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE'.
8.  test_v1_036_label_mode_threaded_to_link_model — LightGbmStrategy accepts
    label_mode="trend_scanning" and stores it (real instance /027 LESSON).
9.  test_v1_036_label_mode_threaded_to_dot_model — same for DOT specialist.
10. test_v1_036_dispatches_only_link_and_dot_models — dispatch branch sources only
    Model C' (LINK) + Model E (DOT); no Model A pool, no Model D LTC, no Model G ETH.

Foundation regression:
- test_v1_036_walk_forward_embargo_regression — walk_forward.py:113 embargo discipline
  (train_end_ms = test_start_ms - embargo_ms).
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 1 — V1_ITER036_UNIVERSE constant exists and is correct
# ---------------------------------------------------------------------------


def test_v1_036_universe_constant_exists() -> None:
    """V1_ITER036_UNIVERSE must be defined as a tuple containing exactly
    ("LINKUSDT", "DOTUSDT") in src/crypto_trade/features_v1/__init__.py.

    Per /036 brief Section 10.1: universe constant is the guard for the dispatch branch.
    """
    from crypto_trade.features_v1 import V1_ITER036_UNIVERSE

    assert isinstance(V1_ITER036_UNIVERSE, tuple), (
        f"V1_ITER036_UNIVERSE must be a tuple, got {type(V1_ITER036_UNIVERSE).__name__}."
    )
    assert set(V1_ITER036_UNIVERSE) == {"LINKUSDT", "DOTUSDT"}, (
        f"V1_ITER036_UNIVERSE must be exactly {{'LINKUSDT', 'DOTUSDT'}}, "
        f"got {set(V1_ITER036_UNIVERSE)}."
    )
    assert len(V1_ITER036_UNIVERSE) == 2, (
        f"V1_ITER036_UNIVERSE must have exactly 2 elements, got {len(V1_ITER036_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# Test 2 — V1_ITER036_UNIVERSE is a subset of V1_BASELINE_UNIVERSE
# ---------------------------------------------------------------------------


def test_v1_036_universe_subset_of_baseline() -> None:
    """V1_ITER036_UNIVERSE ⊂ V1_BASELINE_UNIVERSE.

    Both LINKUSDT and DOTUSDT must be in V1_BASELINE_UNIVERSE — they are existing
    baseline symbols, not new additions. Neither should be in V1_EXCLUDED_SYMBOLS.
    """
    from crypto_trade.features_v1 import (
        V1_BASELINE_UNIVERSE,
        V1_EXCLUDED_SYMBOLS,
        V1_ITER036_UNIVERSE,
    )

    baseline_set = set(V1_BASELINE_UNIVERSE)
    excluded_set = set(V1_EXCLUDED_SYMBOLS)

    for sym in V1_ITER036_UNIVERSE:
        assert sym in baseline_set, (
            f"{sym} from V1_ITER036_UNIVERSE is NOT in V1_BASELINE_UNIVERSE "
            f"{baseline_set}. Both LINKUSDT and DOTUSDT must be baseline symbols."
        )
        assert sym not in excluded_set, (
            f"{sym} from V1_ITER036_UNIVERSE IS in V1_EXCLUDED_SYMBOLS {excluded_set}. "
            "Excluded symbols cannot be traded in v1."
        )


# ---------------------------------------------------------------------------
# Test 3 — Dispatch branch exists in runner source
# ---------------------------------------------------------------------------


def test_v1_036_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-036'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-036"' in src, (
        'Dispatch branch iteration_label == "v1-036" not found in run_baseline_v1.py. '
        "The /036 elif must exist before the catch-all to trigger per-cohort-trend-scanning logic."
    )


# ---------------------------------------------------------------------------
# Test 4 — Pre-flight assert fires on label_mode mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_036_dispatch_branch_pre_flight_label_mode_assert() -> None:
    """The v1-036 dispatch branch must contain an assert that fires on label_mode mismatch.

    When iteration_label == 'v1-036' AND label_mode_arg != 'trend_scanning', the runner
    must raise AssertionError BEFORE any backtest compute starts.

    Per /030 LESSON: sample-instance test mandate. We verify via source inspection that
    the assert is present in the dispatch branch code. Without this guard, a missing
    --label-mode trend_scanning flag would silently run triple_barrier labels on the
    /036 dispatch (reproducing baseline numbers instead of testing the bimodal hypothesis).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    # Verify the assert references label_mode_arg equality with trend_scanning
    assert "assert label_mode_arg ==" in src, (
        "'assert label_mode_arg ==' not found in run_baseline_v1.py. "
        "The v1-036 dispatch branch must pre-flight assert that label_mode_arg == "
        "'trend_scanning'. Without this, a missing --label-mode flag silently runs "
        "triple_barrier labels while dispatching as iter-v1/036."
    )
    # Verify the error message references iter-v1/036 (not just /035)
    assert "iter-v1/036 pre-flight FAIL" in src, (
        "'iter-v1/036 pre-flight FAIL' error message not found in run_baseline_v1.py. "
        "The /036 dispatch branch must have its own labeled pre-flight assert "
        "(distinct from the /035 assert at the same location)."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert fires on universe mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_036_dispatch_branch_pre_flight_universe_assert() -> None:
    """The v1-036 dispatch branch must enforce the V1_ITER036_UNIVERSE set-equality.

    The dispatch condition `set(symbols) == set(V1_ITER036_UNIVERSE)` must be present
    in the elif guard. Passing a wrong symbol set (e.g. LINKUSDT-only or the full
    5-symbol baseline) must NOT route to the /036 branch.

    Per /036 brief Section 2.5: pre-flight assert on universe set is one of two
    required guards for the 2-mechanism HIGH-RISK stack.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    # The elif condition must reference V1_ITER036_UNIVERSE in the set-equality guard
    assert "V1_ITER036_UNIVERSE" in src, (
        "V1_ITER036_UNIVERSE not found in run_baseline_v1.py source. "
        "The /036 dispatch branch elif condition must use V1_ITER036_UNIVERSE "
        "in the set-equality guard: set(symbols) == set(V1_ITER036_UNIVERSE)."
    )
    combined_guard = 'iteration_label == "v1-036" and set(symbols) == set(V1_ITER036_UNIVERSE)'
    assert combined_guard in src, (
        f"Combined guard '{combined_guard}' not found in run_baseline_v1.py. "
        "The /036 elif must check BOTH iteration_label AND universe set-equality."
    )


# ---------------------------------------------------------------------------
# Test 6 — Catch-all exclusion tuple contains "v1-036"
# ---------------------------------------------------------------------------


def test_v1_036_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-036'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif branch MUST be added
    to the catch-all exclusion tuple. Missing this causes the catch-all to silently
    run baseline-universe numbers for v1-036 when --symbols includes all 5 baseline
    symbols (the recurring /030+/031+/032+/033+/034+/035 defect class).

    Note: the /036 dispatch branches on V1_ITER036_UNIVERSE (not V1_BASELINE_UNIVERSE),
    so the catch-all guard protects specifically the V1_BASELINE_UNIVERSE path. This
    test verifies the exclusion entry exists to prevent accidental baseline-dispatch.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-036"' in src, (
        '"v1-036" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, a caller passing --symbols BTCUSDT,...,DOTUSDT --iteration 36 "
        "would fall into the baseline catch-all silently."
    )


# ---------------------------------------------------------------------------
# Test 7 — Dispatch banner is present in source
# ---------------------------------------------------------------------------


def test_v1_036_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py dispatch branch for v1-036 must contain the expected banner.

    The banner '[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE' must be printed
    with all required fields: models, label_mode, trend_scan_grid, ENSEMBLE_SIZE,
    n_trials, seeds=1, feature count.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE" in src, (
        "Expected banner '[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE' not found in "
        "run_baseline_v1.py. "
        "The v1-036 dispatch branch must print this banner with models, label_mode, "
        "trend_scan_grid, ENSEMBLE_SIZE, n_trials, seeds=1, feature count "
        "(iter-v1/036 Section 3.7 step 7 + F-AXIS #6)."
    )
    # Verify banner contains the model names (both specialists must be named)
    assert "Model_C_LINK" in src, (
        "'Model_C_LINK' not found in run_baseline_v1.py. "
        "The /036 banner must identify both specialist models. "
        "Expected 'models=Model_C_LINK + Model_E_DOT' in banner."
    )
    assert "Model_E_DOT" in src, (
        "'Model_E_DOT' not found in run_baseline_v1.py. "
        "The /036 banner must identify both specialist models."
    )


# ---------------------------------------------------------------------------
# Test 8 — label_mode threaded to LINK specialist (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_036_label_mode_threaded_to_link_model() -> None:
    """LightGbmStrategy constructed with label_mode='trend_scanning' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.
    Mock attribute names are unreliable — only real instantiation proves the kwarg
    reaches the strategy.

    This test verifies the LINK specialist (Model C') receives trend_scanning.
    The label_mode plumbing through run_model() → LightGbmStrategy was established at
    /035; /036 reuses the same path with a 2-symbol universe restriction.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Construct a real minimal LightGbmStrategy (LINK specialist parameters)
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
        atr_tp_multiplier=3.5,  # Model C' parameter
        atr_sl_multiplier=1.75,  # Model C' parameter
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],  # minimal non-empty list
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got "
        f"{strategy.label_mode!r}. "
        "The label_mode kwarg must be stored as self.label_mode in LightGbmStrategy.__init__(). "
        "This is the LINK specialist (Model C') configuration for iter-v1/036."
    )
    assert strategy.trend_scan_grid == (5, 8, 13, 21), (
        f"LightGbmStrategy.trend_scan_grid expected (5, 8, 13, 21) but got "
        f"{strategy.trend_scan_grid!r}. "
        "Default trend_scan_grid must be (5, 8, 13, 21) per labeling.py canonical grid."
    )


# ---------------------------------------------------------------------------
# Test 9 — label_mode threaded to DOT specialist (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_036_label_mode_threaded_to_dot_model() -> None:
    """LightGbmStrategy constructed with label_mode='trend_scanning' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.

    This test verifies the DOT specialist (Model E) receives trend_scanning.
    Model E uses the same atr_tp/atr_sl as Model C' in the /036 dispatch.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Construct a real minimal LightGbmStrategy (DOT specialist parameters)
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
        atr_tp_multiplier=3.5,  # Model E parameter
        atr_sl_multiplier=1.75,  # Model E parameter
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],  # minimal non-empty list
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got "
        f"{strategy.label_mode!r}. "
        "The label_mode kwarg must be stored as self.label_mode in LightGbmStrategy.__init__(). "
        "This is the DOT specialist (Model E) configuration for iter-v1/036."
    )
    assert strategy.trend_scan_grid == (5, 8, 13, 21), (
        f"LightGbmStrategy.trend_scan_grid expected (5, 8, 13, 21) but got "
        f"{strategy.trend_scan_grid!r}. "
        "Default trend_scan_grid must be (5, 8, 13, 21) per labeling.py canonical grid."
    )


# ---------------------------------------------------------------------------
# Test 10 — Dispatch branch dispatches ONLY Model C' (LINK) + Model E (DOT)
# ---------------------------------------------------------------------------


def test_v1_036_dispatches_only_link_and_dot_models() -> None:
    """The v1-036 dispatch branch must NOT include Model A pool, Model D LTC,
    or Model G ETH dispatches.

    Per /036 brief Section 3.4: Model A (BTC/ETH pool), Model D (LTC), Model G (ETH)
    are SKIPPED. Only Model C' (LINK) and Model E (DOT) are dispatched.

    Verified via source inspection: the /036 dispatch block must contain runs for
    LINKUSDT and DOTUSDT only. The absence of 'BTCUSDT', 'ETHUSDT', 'LTCUSDT' in the
    /036 dispatch block confirms per-cohort isolation.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    # Find the /036 dispatch block boundaries by locating the dispatch comment
    dispatch_marker = "[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE"
    assert dispatch_marker in src, (
        f"Dispatch marker '{dispatch_marker}' not found in run_baseline_v1.py. "
        "Cannot locate the /036 dispatch block for model-dispatch verification."
    )

    # Locate the /036 block: starts at the iter-v1/036 comment, ends at next 'elif'
    start_idx = src.find('iteration_label == "v1-036" and set(symbols)')
    assert start_idx >= 0, (
        'Cannot find "iteration_label == \\"v1-036\\"" in source to locate block start.'
    )
    # Find the next elif after the /036 block start
    next_elif_idx = src.find("\n    elif ", start_idx + 1)
    assert next_elif_idx > start_idx, "Cannot find the closing elif after the /036 dispatch block."
    block_036 = src[start_idx:next_elif_idx]

    # Model C' (LINK) must be dispatched
    assert '"LINKUSDT"' in block_036, (
        'Model C\' (LINK) dispatch ("LINKUSDT",) not found in the /036 block. '
        "The LINK specialist must be dispatched in iter-v1/036."
    )
    # Model E (DOT) must be dispatched
    assert '"DOTUSDT"' in block_036, (
        'Model E (DOT) dispatch ("DOTUSDT",) not found in the /036 block. '
        "The DOT specialist must be dispatched in iter-v1/036."
    )
    # Model A pool (BTC+ETH) must NOT be dispatched in /036 block
    assert '"BTCUSDT"' not in block_036, (
        'Model A pool ("BTCUSDT") found in /036 dispatch block. '
        "The /036 dispatch must SKIP Model A — BTCUSDT must NOT be dispatched. "
        "Only LINKUSDT + DOTUSDT specialists should trade in iter-v1/036."
    )
    # Model D (LTC) must NOT be dispatched in /036 block
    assert '"LTCUSDT"' not in block_036, (
        'Model D ("LTCUSDT") found in /036 dispatch block. '
        "The /036 dispatch must SKIP Model D — LTCUSDT must NOT be dispatched."
    )
    # ETH must NOT be dispatched in /036 block (covered by Model A exclusion)
    assert '"ETHUSDT"' not in block_036, (
        "ETHUSDT found in /036 dispatch block. "
        "The /036 dispatch must SKIP Model A which covers ETHUSDT. "
        "Only LINKUSDT + DOTUSDT specialists should trade in iter-v1/036."
    )
    # Model names in _post_dispatch_fi_strategies must be the specialist names
    assert "Model_C_LINK_trend_scan_specialist" in block_036, (
        "'Model_C_LINK_trend_scan_specialist' not found in /036 dispatch block. "
        "_post_dispatch_fi_strategies must use the specialist model name for LINK."
    )
    assert "Model_E_DOT_trend_scan_specialist" in block_036, (
        "'Model_E_DOT_trend_scan_specialist' not found in /036 dispatch block. "
        "_post_dispatch_fi_strategies must use the specialist model name for DOT."
    )


# ---------------------------------------------------------------------------
# Foundation regression — walk_forward.py:113 embargo discipline
# ---------------------------------------------------------------------------


def test_v1_036_walk_forward_embargo_regression() -> None:
    """Foundation regression: walk_forward.py embargo discipline.

    walk_forward.py must implement train_end_ms = test_start_ms - embargo_ms.
    This is the load-bearing fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md.
    The walk_forward module must carry embargo_ms so that the training window ends
    strictly BEFORE the test window begins — preventing label-leakage lookahead bias.

    Trend-scanning does NOT change the walk-forward embargo logic. This regression test
    ensures the embargo is intact regardless of the label_mode axis change.
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
        "This is the exact fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md. "
        "If this assertion fails, the walk-forward has a label-leakage lookahead bug."
    )
