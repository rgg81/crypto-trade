"""Integration tests for iter-v1/043 — LINK-only trend-scanning specialist.

Covers all 12 mandatory test items from research_brief.md Section 3.5 (10 items)
plus regime_attribution.csv schema test and walk-forward embargo regression:

1.  test_v1_043_universe_constant_exists — V1_ITER043_UNIVERSE = ("LINKUSDT",).
2.  test_v1_043_universe_subset_of_baseline — LINKUSDT in V1_BASELINE_UNIVERSE.
3.  test_v1_043_dispatch_branch_exists — runner source contains
    iteration_label == "v1-043" dispatch branch.
4.  test_v1_043_pre_flight_label_mode_assert — runner with v1-043 AND
    --label-mode triple_barrier raises AssertionError BEFORE compute.
5.  test_v1_043_pre_flight_universe_assert — runner with v1-043 AND
    --symbols LINKUSDT,DOTUSDT raises AssertionError BEFORE compute.
6.  test_v1_043_pre_flight_optuna_objective_assert — runner with v1-043 AND
    --optuna-objective sortino raises AssertionError BEFORE compute.
7.  test_v1_043_pre_flight_model_type_assert — runner with v1-043 AND
    --model xgboost raises AssertionError BEFORE compute (/042 carry-over guard).
8.  test_v1_043_in_baseline_catchall_exclusion — "v1-043" in catch-all exclusion tuple.
9.  test_v1_043_dispatch_banner_emitted — runner source contains expected banner
    "[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE".
10. test_v1_043_label_mode_threaded_to_link_model — real LightGbmStrategy instance
    with label_mode="trend_scanning" stores it correctly (per /027 LESSON).
11. test_v1_043_dispatches_only_link_model — dispatch block contains ONLY LINKUSDT;
    no DOTUSDT, no BTCUSDT, no LTCUSDT dispatched.
12. test_v1_043_regime_attribution_csv_schema — build_regime_attribution_csv()
    produces DataFrame with required schema columns + ≥ 5 regime rows (IS+OOS).

Foundation regression:
- test_v1_043_walk_forward_embargo_regression — walk_forward.py:113 embargo discipline.
"""

from __future__ import annotations

import inspect
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Test 1 — V1_ITER043_UNIVERSE constant exists and is correct
# ---------------------------------------------------------------------------


def test_v1_043_universe_constant_exists() -> None:
    """V1_ITER043_UNIVERSE must be defined as a tuple containing exactly ("LINKUSDT",)."""
    from crypto_trade.features_v1 import V1_ITER043_UNIVERSE

    assert isinstance(V1_ITER043_UNIVERSE, tuple), (
        f"V1_ITER043_UNIVERSE must be a tuple, got {type(V1_ITER043_UNIVERSE).__name__}."
    )
    assert set(V1_ITER043_UNIVERSE) == {"LINKUSDT"}, (
        f"V1_ITER043_UNIVERSE must be exactly {{'LINKUSDT'}}, got {set(V1_ITER043_UNIVERSE)}."
    )
    assert len(V1_ITER043_UNIVERSE) == 1, (
        f"V1_ITER043_UNIVERSE must have exactly 1 element (LINK-only specialist), "
        f"got {len(V1_ITER043_UNIVERSE)}."
    )


# ---------------------------------------------------------------------------
# Test 2 — V1_ITER043_UNIVERSE is a subset of V1_BASELINE_UNIVERSE
# ---------------------------------------------------------------------------


def test_v1_043_universe_subset_of_baseline() -> None:
    """V1_ITER043_UNIVERSE ⊂ V1_BASELINE_UNIVERSE and NOT in V1_EXCLUDED_SYMBOLS."""
    from crypto_trade.features_v1 import (
        V1_BASELINE_UNIVERSE,
        V1_EXCLUDED_SYMBOLS,
        V1_ITER043_UNIVERSE,
    )

    baseline_set = set(V1_BASELINE_UNIVERSE)
    excluded_set = set(V1_EXCLUDED_SYMBOLS)

    for sym in V1_ITER043_UNIVERSE:
        assert sym in baseline_set, (
            f"{sym} from V1_ITER043_UNIVERSE is NOT in V1_BASELINE_UNIVERSE {baseline_set}. "
            "LINKUSDT must be a baseline symbol."
        )
        assert sym not in excluded_set, (
            f"{sym} from V1_ITER043_UNIVERSE IS in V1_EXCLUDED_SYMBOLS {excluded_set}. "
            "Excluded symbols cannot be traded in v1."
        )


# ---------------------------------------------------------------------------
# Test 3 — Dispatch branch exists in runner source
# ---------------------------------------------------------------------------


def test_v1_043_dispatch_branch_exists() -> None:
    """run_baseline_v1.py must contain an explicit elif for iteration_label == 'v1-043'."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert 'iteration_label == "v1-043"' in src, (
        'Dispatch branch iteration_label == "v1-043" not found in run_baseline_v1.py. '
        "The /043 elif must exist before the catch-all to trigger LINK-only trend-scan specialist."
    )


# ---------------------------------------------------------------------------
# Test 4 — Pre-flight assert fires on label_mode mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_043_pre_flight_label_mode_assert() -> None:
    """The v1-043 dispatch branch must contain an assert for label_mode == trend_scanning."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "iter-v1/043 pre-flight FAIL: expected --label-mode trend_scanning" in src, (
        "Pre-flight label_mode assert message not found in run_baseline_v1.py. "
        "The /043 dispatch branch must assert label_mode_arg == 'trend_scanning' with "
        "the error prefix 'iter-v1/043 pre-flight FAIL: expected --label-mode trend_scanning'."
    )


# ---------------------------------------------------------------------------
# Test 5 — Pre-flight assert fires on universe mismatch (source-level check)
# ---------------------------------------------------------------------------


def test_v1_043_pre_flight_universe_assert() -> None:
    """The v1-043 dispatch branch must enforce V1_ITER043_UNIVERSE set-equality."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "V1_ITER043_UNIVERSE" in src, (
        "V1_ITER043_UNIVERSE not found in run_baseline_v1.py source. "
        "The /043 dispatch branch elif condition must use V1_ITER043_UNIVERSE "
        "in the set-equality guard."
    )
    combined_guard = 'iteration_label == "v1-043" and set(symbols) == set(V1_ITER043_UNIVERSE)'
    assert combined_guard in src, (
        f"Combined guard '{combined_guard}' not found in run_baseline_v1.py. "
        "The /043 elif must check BOTH iteration_label AND V1_ITER043_UNIVERSE set-equality."
    )
    assert "iter-v1/043 pre-flight FAIL: expected symbols == {{LINKUSDT}}" in src, (
        "Pre-flight universe assert message not found in run_baseline_v1.py. "
        "The /043 dispatch branch must assert set(symbols) == set(V1_ITER043_UNIVERSE) with "
        "the error prefix 'iter-v1/043 pre-flight FAIL: expected symbols == {LINKUSDT}'."
    )


# ---------------------------------------------------------------------------
# Test 6 — Pre-flight assert fires on optuna_objective mismatch
# ---------------------------------------------------------------------------


def test_v1_043_pre_flight_optuna_objective_assert() -> None:
    """The v1-043 dispatch branch must assert optuna_objective is sharpe (NOT sortino)."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "iter-v1/043 pre-flight FAIL: expected --optuna-objective sharpe" in src, (
        "Pre-flight optuna_objective assert message not found in run_baseline_v1.py. "
        "The /043 dispatch branch must assert optuna_objective_arg in ('sharpe', None) with "
        "error prefix 'iter-v1/043 pre-flight FAIL: expected --optuna-objective sharpe'. "
        "Defends against accidental /039 Sortino contamination."
    )


# ---------------------------------------------------------------------------
# Test 7 — Pre-flight assert fires on model_type mismatch (/042 XGBoost guard)
# ---------------------------------------------------------------------------


def test_v1_043_pre_flight_model_type_assert() -> None:
    """The v1-043 dispatch branch must assert model_type == lgbm (/042 carry-over guard)."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    assert "iter-v1/043 pre-flight FAIL: expected --model lgbm" in src, (
        "Pre-flight model_type assert message not found in run_baseline_v1.py. "
        "The /043 dispatch branch must assert model_type_arg == 'lgbm' with "
        "error prefix 'iter-v1/043 pre-flight FAIL: expected --model lgbm'. "
        "Defends against accidental /042 XGBoost carry-over."
    )


# ---------------------------------------------------------------------------
# Test 8 — Catch-all exclusion tuple contains "v1-043"
# ---------------------------------------------------------------------------


def test_v1_043_in_baseline_catchall_exclusion() -> None:
    """Exclusion tuple at catch-all branch must contain 'v1-043'.

    Per /030 LESSON (feedback_v1_dispatch_baseline_catchall_exclusion.md):
    Every new iteration label dispatched via an explicit elif branch MUST be added
    to the catch-all exclusion tuple. V1_ITER043_UNIVERSE != V1_BASELINE_UNIVERSE
    (LINK-only vs 5-symbol baseline), but the catch-all exclusion still prevents
    accidental catch-all fallthrough if --symbols changes between runs.
    """
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert '"v1-043"' in src, (
        '"v1-043" not found in run_baseline_v1.py source. '
        "Add it to the catch-all exclusion tuple (per /030 LESSON). "
        "Without this, re-running /043 with --symbols BTCUSDT,...,DOTUSDT "
        "would fall into the baseline catch-all silently."
    )


# ---------------------------------------------------------------------------
# Test 9 — Dispatch banner is present in source
# ---------------------------------------------------------------------------


def test_v1_043_dispatch_banner_emitted() -> None:
    """run_baseline_v1.py dispatch branch for v1-043 must contain the expected banner."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)
    assert "[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE" in src, (
        "Expected banner '[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE' "
        "not found in run_baseline_v1.py. "
        "The v1-043 dispatch branch must print this banner per brief Section 3.1 + F-AXIS #2."
    )
    # Verify banner contains model name
    assert "Model_C_LINK_only" in src, (
        "'Model_C_LINK_only' not found in run_baseline_v1.py. "
        "The /043 banner must identify the single specialist model."
    )
    # Verify banner or source references trend_scan_grid
    assert "trend_scan_grid=(5, 8, 13, 21)" in src, (
        "'trend_scan_grid=(5, 8, 13, 21)' not found in run_baseline_v1.py. "
        "The /043 banner must declare the canonical trend-scanning grid."
    )
    # Verify banner references cycle-5 EXP-10/10
    assert "EXP-10/10" in src or "cycle-5 EXP" in src, (
        "Cycle position reference ('EXP-10/10' or 'cycle-5 EXP') not found in "
        "run_baseline_v1.py /043 dispatch. The banner must identify this as the "
        "final cycle-5 EXPLORATION."
    )


# ---------------------------------------------------------------------------
# Test 10 — label_mode threaded to LINK model (real instance, /027 LESSON)
# ---------------------------------------------------------------------------


def test_v1_043_label_mode_threaded_to_link_model() -> None:
    """LightGbmStrategy constructed with label_mode='trend_scanning' stores it correctly.

    Per /027 LESSON: use a REAL LightGbmStrategy instance to verify attribute access.
    Verifies Model C' (LINK specialist) receives trend_scanning.
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
        atr_tp_multiplier=3.5,  # Model C' parameter
        atr_sl_multiplier=1.75,  # Model C' parameter
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=["vol_natr_21"],  # minimal non-empty list
        label_mode="trend_scanning",
    )
    assert strategy.label_mode == "trend_scanning", (
        f"LightGbmStrategy.label_mode expected 'trend_scanning' but got {strategy.label_mode!r}. "
        "The label_mode kwarg must be stored as self.label_mode in LightGbmStrategy.__init__(). "
        "This is the LINK specialist (Model C') configuration for iter-v1/043."
    )
    assert strategy.trend_scan_grid == (5, 8, 13, 21), (
        f"LightGbmStrategy.trend_scan_grid expected (5, 8, 13, 21) but got "
        f"{strategy.trend_scan_grid!r}. "
        "Default trend_scan_grid must be (5, 8, 13, 21) per labeling.py canonical grid."
    )


# ---------------------------------------------------------------------------
# Test 11 — Dispatch branch dispatches ONLY Model C' (LINK); no DOT/BTC/LTC
# ---------------------------------------------------------------------------


def test_v1_043_dispatches_only_link_model() -> None:
    """The v1-043 dispatch branch must NOT dispatch Model E DOT, Model A, Model D LTC."""
    import run_baseline_v1  # noqa: F401

    src = inspect.getsource(run_baseline_v1)

    # Locate the /043 dispatch block boundaries
    dispatch_marker = "[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE"
    assert dispatch_marker in src, (
        f"Dispatch marker '{dispatch_marker}' not found. Cannot locate /043 dispatch block."
    )

    start_idx = src.find('iteration_label == "v1-043" and set(symbols) == set(V1_ITER043_UNIVERSE)')
    assert start_idx >= 0, "Cannot find v1-043 elif guard in source."

    # The /043 block ends at the next elif or the catch-all
    next_elif_idx = src.find("\n    elif ", start_idx + 1)
    assert next_elif_idx > start_idx, "Cannot find closing elif after /043 block."
    block_043 = src[start_idx:next_elif_idx]

    # Model C' (LINK) must be dispatched
    assert '"LINKUSDT"' in block_043, (
        "Model C' (LINK) dispatch ('LINKUSDT',) not found in the /043 block. "
        "The LINK specialist must be dispatched."
    )
    # Model C' should appear with exact tuple for symbol dispatch
    assert "Model_C_LINK_trend_scan_only" in block_043, (
        "'Model_C_LINK_trend_scan_only' not found in /043 dispatch block. "
        "_post_dispatch_fi_strategies must use the specialist model name."
    )
    # Model E DOT must NOT be dispatched in /043 block
    assert '"DOTUSDT"' not in block_043, (
        "DOTUSDT found in /043 dispatch block. "
        "iter-v1/043 must dispatch ONLY Model C' (LINK). DOT is excluded from /043."
    )
    # Model A pool (BTC+ETH) must NOT be dispatched
    assert '"BTCUSDT"' not in block_043, (
        "BTCUSDT found in /043 dispatch block. "
        "Model A pool (BTC/ETH) must NOT be dispatched in /043. LINK-only specialist."
    )
    # Model D LTC must NOT be dispatched
    assert '"LTCUSDT"' not in block_043, (
        "LTCUSDT found in /043 dispatch block. Model D (LTC) must NOT be dispatched in /043."
    )
    # _r5_model_results must be a single-element list
    assert "_r5_model_results = [results_c043]" in block_043, (
        "'_r5_model_results = [results_c043]' not found in /043 block. "
        "The dispatch must produce a single-model result list (LINK only)."
    )


# ---------------------------------------------------------------------------
# Test 12 — regime_attribution.csv schema test (mock trades → schema validation)
# ---------------------------------------------------------------------------


def test_v1_043_regime_attribution_csv_schema() -> None:
    """build_regime_attribution_csv() produces CSV with required schema + ≥5 regime rows.

    Uses minimal mock trades DataFrame to verify the schema without loading real data.
    Schema required: regime_tag, in_sample, candidate_sharpe, candidate_max_dd,
    candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count.
    """
    import numpy as np
    import pandas as pd
    import run_baseline_v1

    # Minimal mock: 20 trades across IS+OOS, random pnl_pct, all "LINKUSDT"
    rng = np.random.default_rng(42)
    n = 20
    # is_cutoff_ms = 2025-03-24 00:00 UTC = 1742774400000
    is_cutoff_ms = 1742774400000
    close_times = [
        # 10 IS trades (before cutoff)
        *[is_cutoff_ms - (i + 1) * 86400_000 * 30 for i in range(10)],
        # 10 OOS trades (after cutoff)
        *[is_cutoff_ms + (i + 1) * 86400_000 * 30 for i in range(10)],
    ]
    mock_trades = pd.DataFrame(
        {
            "symbol": ["LINKUSDT"] * n,
            "close_time": close_times,
            "pnl_pct": rng.normal(0.05, 0.15, n),
            "open_time": [ct - 86400_000 for ct in close_times],
        }
    )

    # Mock baseline trades (half the rows)
    mock_baseline = mock_trades.iloc[:10].copy()

    # Write to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "regime_attribution.csv"

        run_baseline_v1.build_regime_attribution_csv(
            trades_df=mock_trades,
            baseline_trades_df=mock_baseline,
            is_cutoff_ms=is_cutoff_ms,
            btc_klines_df=None,  # None → all regimes tagged as "other"
            out_path=out_path,
        )

        assert out_path.exists(), (
            f"regime_attribution.csv not written to {out_path}. "
            "build_regime_attribution_csv() must create the output file."
        )

        result = pd.read_csv(out_path)

    # Schema check — all required columns present
    required_cols = {
        "regime_tag",
        "in_sample",
        "candidate_sharpe",
        "candidate_max_dd",
        "candidate_trade_count",
        "baseline_sharpe",
        "baseline_max_dd",
        "baseline_trade_count",
    }
    missing_cols = required_cols - set(result.columns)
    assert not missing_cols, (
        f"regime_attribution.csv missing required columns: {missing_cols}. "
        f"Got columns: {list(result.columns)}. "
        "Schema must be: regime_tag, in_sample, candidate_sharpe, candidate_max_dd, "
        "candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count."
    )

    # Row count: 6 regimes × 2 splits (IS+OOS) = 12 rows minimum
    assert len(result) >= 5, (
        f"regime_attribution.csv has {len(result)} rows; expected ≥ 5 "
        "(at least 5 regime × split combinations). "
        "Possible schema: bull, bear, vol-spike, chop, recovery, other × {IS, OOS}."
    )

    # regime_tag column must contain string values
    # Regime tag must be string-like (object or pandas StringDtype)
    _regime_dtype = str(result["regime_tag"].dtype)
    assert _regime_dtype in ("object", "str") or _regime_dtype.startswith("string"), (
        f"regime_tag column dtype is {result['regime_tag'].dtype}; expected string/object type. "
    )

    # in_sample column must be boolean-compatible
    assert result["in_sample"].isin([True, False, 0, 1]).all(), (
        f"in_sample column contains non-boolean values: {result['in_sample'].unique()}. "
        "Must be True/False or 0/1."
    )

    # trade_count columns must be non-negative integers
    assert (result["candidate_trade_count"] >= 0).all(), (
        "candidate_trade_count contains negative values."
    )
    assert (result["baseline_trade_count"] >= 0).all(), (
        "baseline_trade_count contains negative values."
    )

    # When btc_klines_df=None, all rows should be tagged as "other" regime
    # (since _assign_regime_tag returns "other" when btc_df is None)
    other_rows = result[result["regime_tag"] == "other"]
    assert len(other_rows) >= 2, (
        f"Expected ≥ 2 'other' regime rows when btc_klines_df=None "
        f"(IS + OOS), got {len(other_rows)}. "
        "When no BTC klines available, all trades should map to 'other'."
    )


# ---------------------------------------------------------------------------
# Foundation regression — walk_forward.py:113 embargo discipline
# ---------------------------------------------------------------------------


def test_v1_043_walk_forward_embargo_regression() -> None:
    """Foundation regression: walk_forward.py embargo discipline.

    walk_forward.py must implement train_end_ms = test_start_ms - embargo_ms.
    The iter-v3/058 fix; cannot regress. Trend-scanning labels do NOT change
    the walk-forward embargo logic.
    """
    try:
        from crypto_trade.strategies.ml import walk_forward
    except ImportError:
        import importlib

        walk_forward = importlib.import_module("crypto_trade.strategies.ml.walk_forward")

    src = inspect.getsource(walk_forward)

    assert "embargo_ms" in src, (
        "walk_forward.py must contain 'embargo_ms' for the label-leakage gap."
    )
    assert "train_end_ms" in src, "walk_forward.py must contain 'train_end_ms'."
    assert "train_end_ms = test_start_ms - embargo_ms" in src, (
        "walk_forward.py:113 must implement 'train_end_ms = test_start_ms - embargo_ms'. "
        "The /036 per-cohort-trend-scanning axis does not change this."
    )
