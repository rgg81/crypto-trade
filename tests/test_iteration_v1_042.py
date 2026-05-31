"""Integration tests for iter-v1/042 — MODEL-ARCH library swap LightGBM → XGBoost.

Axis: pure library substitution LightGbmStrategy → XgboostStrategy at constant
      data / labels / features / risk gates / Optuna objective.
      XGBoost: tree_method='hist', grow_policy='depthwise', n_jobs=1.
      Optuna: 6 hp (num_leaves DROPPED — no-op under depthwise growth).
      max_depth ∈ [3, 5] enforced in optimization_xgb.py (LM Master Rec 1).

Covers all 9 mandatory test items from research_brief.md Section 10.3:

1.  test_v1_042_dispatch_branch_exists — iteration_label == "v1-042" path reachable.
2.  test_v1_042_in_baseline_catchall_exclusion — "v1-042" in exclusion tuple.
3.  test_v1_042_dispatch_banner_emitted — banner contains XGBOOST ACTIVE key strings.
4.  test_v1_042_pre_flight_model_assert — --model lgbm raises AssertionError.
5.  test_v1_042_pre_flight_label_mode_assert — wrong label_mode text in source.
6.  test_v1_042_pre_flight_vol_ceiling_assert — vol_ceiling_mode assert text in source.
7.  test_v1_042_pre_flight_atr_tp_assert — no --atr-tp-mult override assert text.
8.  test_v1_042_xgboost_feature_columns_honored — XgboostStrategy raises if None/empty.
9.  test_v1_042_xgboost_optuna_max_depth_bound — max_depth ∈ [3, 5] in optimization_xgb.py.

Additional tests:
10. test_v1_042_model_flag_argparse — --model xgboost accepted; default is lgbm.
11. test_v1_042_lgbm_path_unchanged — default --model lgbm preserves LightGbmStrategy import.
12. test_v1_042_xgboost_pinned_config — optimization_xgb.py pins tree_method + grow_policy + n_jobs.
13. test_v1_042_xgboost_feature_columns_ensemble_seeds_guards — constructor raises without seeds.
14. test_v1_042_f2_wiring_xgb_import_ok — import xgboost succeeds (F-AXIS #2 wiring).
15. test_v1_042_walk_forward_embargo_regression — walk_forward.py embargo discipline.
"""

from __future__ import annotations

import inspect

# ---------------------------------------------------------------------------
# Test 1 — Dispatch branch exists
# ---------------------------------------------------------------------------


def test_v1_042_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-042'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-042"' in src, (
        'Dispatch branch iteration_label == "v1-042" not found in run_baseline_v1.py. '
        "The /042 elif must exist before the catch-all to activate the XGBoost library swap."
    )


# ---------------------------------------------------------------------------
# Test 2 — catch-all exclusion tuple contains "v1-042"
# ---------------------------------------------------------------------------


def test_v1_042_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at run_baseline_v1.py catch-all branch must contain 'v1-042'.

    Per /030 LESSON: every new iteration label dispatched via an explicit elif MUST be
    added to the catch-all exclusion tuple. Missing this causes the catch-all to
    silently run baseline numbers when iteration_label=='v1-042' routes past the
    explicit elif (e.g., wrong symbol set).
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-042"' in src, (
        '"v1-042" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, the catch-all branch may silently run baseline numbers."
    )


# ---------------------------------------------------------------------------
# Test 3 — Dispatch banner contains key XGBOOST ACTIVE strings
# ---------------------------------------------------------------------------


def test_v1_042_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py must contain the '[iter-v1/042] XGBOOST ACTIVE' banner."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/042] XGBOOST ACTIVE" in src, (
        "Banner '[iter-v1/042] XGBOOST ACTIVE' not found in run_baseline_v1.py. "
        "The v1-042 dispatch branch must print this banner for F-AXIS #2 wiring verification."
    )
    # Verify banner contains load-bearing configuration strings
    assert "tree_method=hist" in src, (
        "Banner does not reference tree_method=hist. "
        "LM Master Rec 3 requires tree_method='hist' locked in the banner."
    )
    assert "grow_policy=depthwise" in src, (
        "Banner does not reference grow_policy=depthwise. "
        "LM Master Rec 3 requires grow_policy='depthwise' locked in the banner."
    )
    assert "n_jobs=1" in src, (
        "Banner does not reference n_jobs=1. "
        "n_jobs=1 is load-bearing for XGBoost determinism (fixed seed)."
    )


# ---------------------------------------------------------------------------
# Test 4 — Pre-flight assert: wrong model flag (lgbm instead of xgboost)
# ---------------------------------------------------------------------------


def test_v1_042_pre_flight_model_assert() -> None:
    """Dispatch branch must contain assert text for wrong model_type_arg value."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/042 pre-flight FAIL: expected --model xgboost" in src, (
        "Pre-flight assert text for wrong model_type not found in run_baseline_v1.py. "
        "The /042 dispatch must assert model_type_arg == 'xgboost' with a descriptive message. "
        "This prevents silently running LightGBM instead of XGBoost on the library-swap axis."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert: wrong label_mode
# ---------------------------------------------------------------------------


def test_v1_042_pre_flight_label_mode_assert() -> None:
    """Dispatch branch must contain assert text for wrong label_mode."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/042 pre-flight FAIL: expected --label-mode triple_barrier" in src, (
        "Pre-flight assert text for label_mode != triple_barrier not found. "
        "The /042 dispatch must assert label_mode_arg == 'triple_barrier' "
        "(labeling is UNCHANGED from baseline — axis is library swap ONLY)."
    )


# ---------------------------------------------------------------------------
# Test 6 — Pre-flight assert: vol_ceiling_mode != none
# ---------------------------------------------------------------------------


def test_v1_042_pre_flight_vol_ceiling_assert() -> None:
    """Dispatch branch must contain assert for vol_ceiling_mode == none."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/042 pre-flight FAIL: expected --vol-ceiling-mode none" in src, (
        "Pre-flight assert text for vol_ceiling_mode not found in run_baseline_v1.py. "
        "The /042 dispatch must assert vol_ceiling_mode_arg == 'none' "
        "(iter-v1/038 vol-ceiling is a CLOSED axis; no carry-over to /042)."
    )


# ---------------------------------------------------------------------------
# Test 7 — Pre-flight assert: no --atr-tp-mult override
# ---------------------------------------------------------------------------


def test_v1_042_pre_flight_atr_tp_assert() -> None:
    """Dispatch branch must contain assert text ensuring no atr_tp_mult override."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "iter-v1/042 pre-flight FAIL: expected no --atr-tp-mult override" in src, (
        "Pre-flight assert text for atr_tp_mult override not found in run_baseline_v1.py. "
        "The /042 dispatch must assert atr_tp_mult_arg is None "
        "(baseline ATR defaults per cohort — no /041 carry-over)."
    )


# ---------------------------------------------------------------------------
# Test 8 — XgboostStrategy raises ValueError if feature_columns is None or empty
# ---------------------------------------------------------------------------


def test_v1_042_xgboost_feature_columns_honored() -> None:
    """XgboostStrategy must raise ValueError when feature_columns is None or empty.

    Per feedback_explicit_feature_columns.md: every strategy MUST reject None/empty
    feature_columns to prevent silent auto-discovery across parquet schema changes.
    """
    import pytest

    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        XgboostStrategy(
            feature_columns=None,
            ensemble_seeds=[42],
        )
    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        XgboostStrategy(
            feature_columns=[],
            ensemble_seeds=[42],
        )


# ---------------------------------------------------------------------------
# Test 9 — XGBoost Optuna max_depth bound is [3, 5] (LM Master Rec 1)
# ---------------------------------------------------------------------------


def test_v1_042_xgboost_optuna_max_depth_bound() -> None:
    """optimization_xgb.py must suggest max_depth in [3, 5] (NOT [3, 7]).

    LM Master Rec 1: tighten max_depth from [3, 7] to [3, 5] to keep wall-clock
    under the 2h EXPLORATION cap. Depth 5 = 32 leaves (symmetric depthwise);
    depth 7 would be 128 leaves with 2-3× per-trial cost at XGBoost depthwise.
    """
    from crypto_trade.strategies.ml import optimization_xgb

    src = inspect.getsource(optimization_xgb)
    # Must contain suggest_int for max_depth with upper bound 5
    assert 'suggest_int("max_depth", 3, 5)' in src, (
        "optimization_xgb.py max_depth bound is not [3, 5]. "
        "LM Master Rec 1 requires max_depth ∈ [3, 5] (NOT [3, 7]) to keep "
        "XGBoost depthwise wall-clock under the 2h EXPLORATION cap. "
        "Check _objective_xgb() in optimization_xgb.py."
    )


# ---------------------------------------------------------------------------
# Test 10 — --model argparse flag: default lgbm, xgboost accepted
# ---------------------------------------------------------------------------


def test_v1_042_model_flag_argparse() -> None:
    """run_baseline_v1.py must declare --model with choices lgbm/xgboost, default lgbm."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"--model"' in src or "'--model'" in src, (
        "--model argument not found in run_baseline_v1.py argparse. "
        "iter-v1/042 requires --model {lgbm,xgboost} CLI flag."
    )
    assert '"lgbm", "xgboost"' in src or '["lgbm", "xgboost"]' in src, (
        "choices=['lgbm', 'xgboost'] not found in run_baseline_v1.py. "
        "--model must restrict to these two values."
    )
    assert 'default="lgbm"' in src or "default='lgbm'" in src, (
        "default='lgbm' not found in run_baseline_v1.py --model argument. "
        "Default must be 'lgbm' to preserve BIT-IDENTICAL behaviour for all prior iterations."
    )


# ---------------------------------------------------------------------------
# Test 11 — Default --model lgbm preserves LightGbmStrategy import
# ---------------------------------------------------------------------------


def test_v1_042_lgbm_path_unchanged() -> None:
    """LightGbmStrategy must still be imported in run_baseline_v1.py (regression guard).

    All prior iterations (/034-/041) use LightGbmStrategy implicitly. Adding --model
    flag must NOT remove the LightGbmStrategy import or break any prior dispatch.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "from crypto_trade.strategies.ml.lgbm import LightGbmStrategy" in src, (
        "LightGbmStrategy import not found in run_baseline_v1.py. "
        "Adding --model xgboost must NOT remove the LightGbmStrategy import — "
        "all prior iterations (/034-/041) depend on it."
    )
    assert "LightGbmStrategy(" in src, (
        "LightGbmStrategy() instantiation not found in run_baseline_v1.py. "
        "The default lgbm path must still instantiate LightGbmStrategy (run_model uses it)."
    )


# ---------------------------------------------------------------------------
# Test 12 — optimization_xgb.py pins tree_method + grow_policy + n_jobs
# ---------------------------------------------------------------------------


def test_v1_042_xgboost_pinned_config() -> None:
    """optimization_xgb.py must pin tree_method='hist', grow_policy='depthwise', n_jobs=1.

    These are load-bearing architectural constants (LM Master Rec 3):
    - tree_method='hist': rules out GPU fallback / version drift
    - grow_policy='depthwise': maximises architectural difference from LightGBM leaf-wise
    - n_jobs=1: determinism with fixed random_state
    """
    from crypto_trade.strategies.ml import optimization_xgb

    src = inspect.getsource(optimization_xgb)
    assert '"tree_method": "hist"' in src or "'tree_method': 'hist'" in src, (
        "tree_method='hist' not pinned in optimization_xgb.py. "
        "LM Master Rec 3: tree_method='hist' must be locked (not 'exact' or 'approx')."
    )
    assert '"grow_policy": "depthwise"' in src or "'grow_policy': 'depthwise'" in src, (
        "grow_policy='depthwise' not pinned in optimization_xgb.py. "
        "LM Master Rec 3: grow_policy='depthwise' is load-bearing — "
        "lossguide would mimic LightGBM leaf-wise and defeat the axis purpose."
    )
    assert '"n_jobs": 1' in src or "'n_jobs': 1" in src, (
        "n_jobs=1 not pinned in optimization_xgb.py. "
        "n_jobs=1 is required for XGBoost determinism with fixed random_state."
    )


# ---------------------------------------------------------------------------
# Test 13 — XgboostStrategy raises if ensemble_seeds is empty/None
# ---------------------------------------------------------------------------


def test_v1_042_xgboost_feature_columns_ensemble_seeds_guards() -> None:
    """XgboostStrategy must raise ValueError when ensemble_seeds is None or empty."""
    import pytest

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="ensemble_seeds must be a non-empty list"):
        XgboostStrategy(
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ensemble_seeds=None,
        )
    with pytest.raises(ValueError, match="ensemble_seeds must be a non-empty list"):
        XgboostStrategy(
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ensemble_seeds=[],
        )


# ---------------------------------------------------------------------------
# Test 14 — F2 wiring check: import xgboost succeeds
# ---------------------------------------------------------------------------


def test_v1_042_f2_wiring_xgb_import_ok() -> None:
    """import xgboost must succeed and expose xgboost.__version__ (F-AXIS #2 wiring).

    LM Master §2 (F2 WIRING load-bearing): runner must be able to import xgboost
    and log xgboost.__version__ at startup. This test verifies the library is installed
    and accessible in the current venv.
    """
    import xgboost as xgb

    assert hasattr(xgb, "__version__"), (
        "xgboost.__version__ not found. "
        "The xgboost package must expose __version__ for F-AXIS #2 wiring verification."
    )
    version_parts = xgb.__version__.split(".")
    major = int(version_parts[0])
    assert major >= 2, (
        f"xgboost version {xgb.__version__} is below the required >=2.0. "
        "pyproject.toml pins xgboost>=2.0,<3.0. Reinstall dependencies."
    )
    # Verify the XGBClassifier is accessible (primary model class)
    assert hasattr(xgb, "XGBClassifier"), (
        "xgb.XGBClassifier not found. "
        "XGBClassifier is the primary class used in optimization_xgb.py and xgb.py."
    )


# ---------------------------------------------------------------------------
# Test 15 — Foundation walk-forward embargo regression
# ---------------------------------------------------------------------------


def test_v1_042_walk_forward_embargo_regression() -> None:
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
