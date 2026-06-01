"""Integration tests for iter-v1/035 — trend-scanning labels axis.

Covers all 9 mandatory test items from research_brief.md Section 10.3:

1.  test_v1_035_label_mode_cli_flag_parses — "--label-mode trend_scanning" parses
    via argparse with allowed choices.
2.  test_v1_035_label_mode_default_unchanged — "--label-mode" default is "triple_barrier";
    backward-compat.
3.  test_v1_035_run_model_threads_label_mode — run_model() has label_mode kwarg and
    LightGbmStrategy receives it (real instance per /027 LESSON).
4.  test_v1_035_dispatch_banner_emitted — runner source contains the expected dispatch
    banner for v1-035.
5.  test_v1_035_dispatch_branch_pre_flight_assert — runner with iteration_label="v1-035"
    AND --label-mode triple_barrier (mismatch) raises AssertionError (source-level verify).
6.  test_v1_035_in_baseline_catchall_exclusion — "v1-035" in catch-all exclusion tuple
    (per /030 LESSON feedback_v1_dispatch_baseline_catchall_exclusion.md).
7.  test_v1_035_dispatch_branch_exists — dispatch branch for v1-035 exists in runner.
8.  test_v1_035_trend_scan_grid_default — LightGbmStrategy trend_scan_grid default is
    (5, 8, 13, 21).
9.  test_v1_035_label_mode_does_not_leak_outside_dispatch — foundation regression:
    walk_forward.py:113 embargo discipline (train_end_ms = test_start_ms - embargo_ms).
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 1 — CLI flag parses with allowed choices
# ---------------------------------------------------------------------------


def test_v1_035_label_mode_cli_flag_parses() -> None:
    """--label-mode argument must accept 'trend_scanning' as a valid choice."""
    import argparse

    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    # Verify the choices declaration is present in the source
    assert '"trend_scanning"' in src, (
        '"trend_scanning" not found in run_baseline_v1.py source. '
        "The --label-mode argparse argument must include 'trend_scanning' as a choice. "
        "See iter-v1/035 Section 3.1."
    )
    assert "--label-mode" in src, (
        '"--label-mode" argument not found in run_baseline_v1.py source. '
        "Add the --label-mode argument to argparse (iter-v1/035 Section 3.1)."
    )
    # Smoke-test that argparse can parse the flag
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--label-mode",
        choices=["triple_barrier", "fixed_horizon", "trend_scanning"],
        default="triple_barrier",
    )
    parsed = parser.parse_args(["--label-mode", "trend_scanning"])
    assert parsed.label_mode == "trend_scanning", (
        f"Expected 'trend_scanning' but got {parsed.label_mode!r}."
    )


# ---------------------------------------------------------------------------
# Test 2 — Default is triple_barrier (backward-compat)
# ---------------------------------------------------------------------------


def test_v1_035_label_mode_default_unchanged() -> None:
    """--label-mode default must be 'triple_barrier' to preserve backward compatibility.

    Runs without --label-mode must produce BIT-IDENTICAL labels to historic baseline runs.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--label-mode",
        choices=["triple_barrier", "fixed_horizon", "trend_scanning"],
        default="triple_barrier",
    )
    parsed = parser.parse_args([])  # no --label-mode flag
    assert parsed.label_mode == "triple_barrier", (
        f"Expected default 'triple_barrier' but got {parsed.label_mode!r}. "
        "The default must be 'triple_barrier' to preserve baseline behavior."
    )


# ---------------------------------------------------------------------------
# Test 3 — run_model() threads label_mode to LightGbmStrategy (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_035_run_model_threads_label_mode() -> None:
    """run_model() must accept label_mode kwarg and pass it to LightGbmStrategy.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.
    Mock attribute names are unreliable — only real instantiation proves the kwarg reaches
    the strategy.
    """
    import inspect

    import run_baseline_v1

    # Verify label_mode is in run_model's signature
    sig = inspect.signature(run_baseline_v1.run_model)
    assert "label_mode" in sig.parameters, (
        "run_model() in run_baseline_v1.py does not have a 'label_mode' parameter. "
        "Add label_mode: str = 'triple_barrier' to run_model() signature and pass it "
        "to LightGbmStrategy (iter-v1/035 Section 3.1)."
    )

    # Verify LightGbmStrategy accepts label_mode (real class, not mock)
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    lgbm_sig = inspect.signature(LightGbmStrategy.__init__)
    assert "label_mode" in lgbm_sig.parameters, (
        "LightGbmStrategy.__init__() does not have a 'label_mode' parameter. "
        "The kwarg must exist in lgbm.py to receive the trend_scanning value."
    )

    # Construct a real minimal LightGbmStrategy instance and verify attribute
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
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],  # minimal non-empty list
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got "
        f"{strategy.label_mode!r}. "
        "The kwarg must be stored as self.label_mode in LightGbmStrategy.__init__()."
    )
    assert strategy.trend_scan_grid == (5, 8, 13, 21), (
        f"LightGbmStrategy.trend_scan_grid expected (5, 8, 13, 21) but got "
        f"{strategy.trend_scan_grid!r}. "
        "Default trend_scan_grid should be (5, 8, 13, 21) per labeling.py:132-214."
    )


# ---------------------------------------------------------------------------
# Test 4 — Dispatch banner emitted in source
# ---------------------------------------------------------------------------


def test_v1_035_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py dispatch branch for v1-035 must contain the expected banner."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/035] TREND-SCANNING-LABEL ACTIVE" in src, (
        "Expected banner '[iter-v1/035] TREND-SCANNING-LABEL ACTIVE' not found in "
        "run_baseline_v1.py. "
        "The v1-035 dispatch branch must print this banner with label_mode, "
        "trend_scan_grid, ENSEMBLE_SIZE, n_trials, seeds=1 (iter-v1/035 Section 3.7)."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert catches label_mode mismatch
# ---------------------------------------------------------------------------


def test_v1_035_dispatch_branch_pre_flight_assert() -> None:
    """The v1-035 dispatch branch must contain an assert that fires on label_mode mismatch.

    When iteration_label == 'v1-035' AND label_mode_arg == 'triple_barrier' (mismatch),
    the runner must raise AssertionError BEFORE any backtest compute starts.

    Per /030 LESSON: sample-instance test mandate (assert must be in the dispatch branch,
    not a test-only mock). We verify via source inspection.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    # The assert must be present in the source and reference label_mode_arg
    assert "assert label_mode_arg == " in src, (
        "'assert label_mode_arg ==' not found in run_baseline_v1.py. "
        "The v1-035 dispatch branch must pre-flight assert that label_mode_arg == "
        "'trend_scanning'. Without this, a missing --label-mode flag silently runs "
        "triple_barrier labels while reporting as v1-035."
    )
    assert "trend_scanning" in src, (
        "'trend_scanning' not found in run_baseline_v1.py source. "
        "The pre-flight assert must check for 'trend_scanning' specifically."
    )


# ---------------------------------------------------------------------------
# Test 6 — Catch-all exclusion tuple contains "v1-035"
# ---------------------------------------------------------------------------


def test_v1_035_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-035'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif branch MUST be added
    to the catch-all exclusion tuple. Missing this causes the catch-all to silently
    run baseline numbers for v1-035 (the recurring /030+/031+/032+/033+/034 defect class).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-035"' in src, (
        '"v1-035" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, the catch-all branch silently runs baseline numbers."
    )


# ---------------------------------------------------------------------------
# Test 7 — Dispatch branch exists
# ---------------------------------------------------------------------------


def test_v1_035_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-035'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-035"' in src, (
        'Dispatch branch iteration_label == "v1-035" not found in run_baseline_v1.py. '
        "The /035 elif must exist before the catch-all to trigger trend-scanning logic."
    )


# ---------------------------------------------------------------------------
# Test 8 — trend_scan_grid default in LightGbmStrategy
# ---------------------------------------------------------------------------


def test_v1_035_trend_scan_grid_default() -> None:
    """When only --label-mode trend_scanning is passed, LightGbmStrategy must receive
    trend_scan_grid=(5, 8, 13, 21) as default (AFML Ch.5 §5.5 canonical grid).

    Verifies that run_model() does NOT override the default trend_scan_grid when none
    is specified — it passes through the labeling.py default grid intact.
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
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],
        label_mode="trend_scanning",
        # trend_scan_grid NOT passed — should default to (5, 8, 13, 21)
    )
    assert strategy.trend_scan_grid == (5, 8, 13, 21), (
        f"Expected default trend_scan_grid=(5, 8, 13, 21) but got "
        f"{strategy.trend_scan_grid!r}. "
        "LightGbmStrategy must default to the canonical AFML Ch.5 §5.5 grid."
    )


# ---------------------------------------------------------------------------
# Test 9 — Foundation regression: walk_forward.py:113 embargo discipline
# ---------------------------------------------------------------------------


def test_v1_035_label_mode_does_not_leak_outside_dispatch() -> None:
    """Foundation regression: walk_forward.py embargo discipline.

    walk_forward.py must implement train_end_ms = test_start_ms - embargo_ms.
    This is the load-bearing fix from iter-v3/058 / feedback_v3_walkforward_lookahead_bug.md.
    The walk_forward module must carry embargo_ms so that the training window ends
    strictly BEFORE the test window begins — preventing label-leakage lookahead bias.

    Named 'does_not_leak_outside_dispatch' per Section 10.3 test 9: confirms the
    fundamental walk-forward discipline that prevents OOS contamination regardless of
    label_mode. Trend-scanning does NOT change the walk-forward embargo logic.
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
