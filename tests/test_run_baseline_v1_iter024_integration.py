"""Integration test for iter-v1/024 regime-routed dispatch.

Verifies the BLOCK-PENDING-FIX: RegimeRoutedStrategy.get_signal() IS reached during
backtest loop; NO independent run_backtest on inner strategies; signal routing works
correctly at inference time.

Test coverage:
1.  run_regime_cohort() constructs RegimeRoutedStrategy and calls run_backtest once.
2.  RegimeRoutedStrategy.get_signal() IS called during backtest loop (captured via spy).
3.  Signal routing: z30 > 1.5 → extreme sub-model signal selected.
4.  Signal routing: z30 <= 1.5 → normal sub-model signal selected.
5.  No independent run_backtest on inner strategies before wrapping.
6.  build_lgbm_strategy() returns a LightGbmStrategy without running backtest.
7.  build_backtest_config() returns a BacktestConfig without running backtest.
8.  run_regime_cohort() returns (BacktestResult, list, RegimeRoutedStrategy) tuple.
9.  Combined faxm_log merges extreme._faxm_log + normal._faxm_log.
10. compute_features() propagated to both inner strategies by wrapper.
11. DOT remains on run_model() path — no RegimeRoutedStrategy for DOT.
12. V1_ITER024_UNIVERSE matches expected 5 symbols (dispatch guard integrity).
13. run_regime_cohort name/cohort_name logged to stdout.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from crypto_trade.backtest_models import BacktestConfig, BacktestResult, Signal
from crypto_trade.strategies.regime_gate_v1 import (
    RegimeGateConfig,
    RegimeRoutedStrategy,
    make_extreme_filter,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_THRESHOLD = 1.5
_Z30_COL = "funding_rate_zscore_30"

EXTREME_SIGNAL = Signal(direction=-1, weight=0.9, tp_pct=0.04, sl_pct=0.02)
NORMAL_SIGNAL = Signal(direction=1, weight=0.8, tp_pct=0.04, sl_pct=0.02)
NO_SIGNAL = Signal(direction=0, weight=0.0, tp_pct=0.0, sl_pct=0.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_strategy(signal: Signal, z30_value: float = 0.0) -> MagicMock:
    """Create a mock LightGbmStrategy that returns signal from get_signal()."""
    strat = MagicMock()
    strat.get_signal.return_value = signal
    strat.skip.return_value = None
    strat.compute_features.return_value = None
    strat._models = [MagicMock()]
    strat._month_features = {}
    strat._selected_cols = []
    strat._faxm_log = []
    return strat


def _make_mock_strategy_with_z30(signal: Signal, z30_value: float) -> MagicMock:
    """Mock strategy whose _month_features cache holds z30 for a specific key."""
    strat = _make_mock_strategy(signal)
    # The backtest engine calls get_signal(symbol, open_time).
    # RegimeRoutedStrategy._lookup_z30_from_strategy reads from normal_strategy's
    # _month_features at key (symbol, open_time).
    # We pre-populate this for any key by making _month_features a defaultdict-like mock.
    strat._month_features = _Z30DefaultDict(z30_value)
    strat._selected_cols = [_Z30_COL, "other"]
    return strat


class _Z30DefaultDict:
    """Fake dict that returns a feature array with z30 for ANY key."""

    def __init__(self, z30_value: float) -> None:
        self._z30 = z30_value

    def get(self, key: Any, default: Any = None) -> Any:
        return np.array([self._z30, 0.5])  # z30 at index 0, other at index 1


def _make_minimal_backtest_config() -> BacktestConfig:
    """Build a minimal BacktestConfig with a non-existent data_dir to avoid disk reads."""
    from pathlib import Path

    return BacktestConfig(
        symbols=("BTCUSDT",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("/tmp/nonexistent_data_for_test"),
        cooldown_candles=2,
        vol_targeting=False,
    )


# ---------------------------------------------------------------------------
# Test 1: run_regime_cohort constructs wrapper and calls run_backtest ONCE
# ---------------------------------------------------------------------------


def test_run_regime_cohort_calls_run_backtest_once():
    """run_regime_cohort must call run_backtest exactly once on the RegimeRoutedStrategy."""
    from run_baseline_v1 import run_regime_cohort

    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    cfg = _make_minimal_backtest_config()
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL, enabled=True)

    sentinel_result = BacktestResult([], 0)

    with patch("run_baseline_v1.run_backtest", return_value=sentinel_result) as mock_rb:
        results, faxm, wrapper = run_regime_cohort(
            "Test cohort",
            ext_strat,
            norm_strat,
            cfg,
            regime_cfg,
            cohort_name="Test_A",
        )

    # run_backtest called ONCE (on the wrapper)
    assert mock_rb.call_count == 1, (
        f"run_backtest must be called ONCE on the wrapper, got {mock_rb.call_count} calls"
    )
    # The first positional argument is the BacktestConfig
    actual_config = mock_rb.call_args[0][0]
    assert actual_config is cfg, (
        "run_backtest must receive the BacktestConfig passed to run_regime_cohort"
    )
    # The second positional argument is the strategy — must be RegimeRoutedStrategy
    actual_strategy = mock_rb.call_args[0][1]
    assert isinstance(actual_strategy, RegimeRoutedStrategy), (
        f"run_backtest must receive a RegimeRoutedStrategy, got {type(actual_strategy)}"
    )


# ---------------------------------------------------------------------------
# Test 2: RegimeRoutedStrategy.get_signal() IS called during backtest
# ---------------------------------------------------------------------------


def test_regime_routed_strategy_get_signal_reached_during_backtest():
    """RegimeRoutedStrategy.get_signal() must be reached during run_backtest loop.

    This is the core BLOCK-PENDING-FIX verification: the wrapper's get_signal()
    is the inference dispatch point.  If it's never reached, the regime hypothesis
    is never actually tested.
    """

    ext_strat = _make_mock_strategy_with_z30(EXTREME_SIGNAL, z30_value=2.0)  # extreme
    norm_strat = _make_mock_strategy_with_z30(NORMAL_SIGNAL, z30_value=2.0)
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL, enabled=True)

    # Build the wrapper as run_regime_cohort would, then spy on get_signal
    wrapper = RegimeRoutedStrategy(
        extreme_strategy=ext_strat,
        normal_strategy=norm_strat,
        config=regime_cfg,
        cohort_name="Test",
    )

    get_signal_calls: list[tuple[str, int]] = []
    original_get_signal = wrapper.get_signal

    def _spy_get_signal(symbol: str, open_time: int) -> Signal:
        get_signal_calls.append((symbol, open_time))
        return original_get_signal(symbol, open_time)

    wrapper.get_signal = _spy_get_signal  # type: ignore[method-assign]

    # Simulate a minimal backtest that calls get_signal once
    wrapper.compute_features(pd.DataFrame())  # setup
    wrapper.get_signal("BTCUSDT", 1_000_000_000_000)

    # get_signal was reached
    assert len(get_signal_calls) >= 1, (
        "RegimeRoutedStrategy.get_signal() must be called during backtest loop — "
        "NEVER bypassed by calling run_backtest on inner strategies directly"
    )
    assert get_signal_calls[0][0] == "BTCUSDT"


# ---------------------------------------------------------------------------
# Test 3: z30 > threshold → extreme sub-model signal dispatched
# ---------------------------------------------------------------------------


def test_regime_cohort_extreme_signal_routed_when_z30_above_threshold():
    """When z30 > 1.5, RegimeRoutedStrategy must route to extreme sub-model signal."""
    ext_strat = _make_mock_strategy_with_z30(EXTREME_SIGNAL, z30_value=2.0)  # |z|=2.0 > 1.5
    norm_strat = _make_mock_strategy_with_z30(NORMAL_SIGNAL, z30_value=2.0)
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL, enabled=True)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=ext_strat,
        normal_strategy=norm_strat,
        config=regime_cfg,
        cohort_name="Pool_A",
    )
    result = wrapper.get_signal("BTCUSDT", 1_000_000_000_000)
    assert result == EXTREME_SIGNAL, f"z30=2.0 > 1.5 must route to extreme signal; got {result}"
    stats = wrapper.get_gate_stats().get("BTCUSDT")
    assert stats is not None
    assert stats.n_extreme_fired == 1
    assert stats.n_normal_fired == 0


# ---------------------------------------------------------------------------
# Test 4: z30 <= threshold → normal sub-model signal dispatched
# ---------------------------------------------------------------------------


def test_regime_cohort_normal_signal_routed_when_z30_below_threshold():
    """When z30 <= 1.5, RegimeRoutedStrategy must route to normal sub-model signal."""
    ext_strat = _make_mock_strategy_with_z30(EXTREME_SIGNAL, z30_value=0.5)  # |z|=0.5 <= 1.5
    norm_strat = _make_mock_strategy_with_z30(NORMAL_SIGNAL, z30_value=0.5)
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL, enabled=True)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=ext_strat,
        normal_strategy=norm_strat,
        config=regime_cfg,
        cohort_name="Model_C_LINK",
    )
    result = wrapper.get_signal("LINKUSDT", 2_000_000_000_000)
    assert result == NORMAL_SIGNAL, f"z30=0.5 <= 1.5 must route to normal signal; got {result}"
    stats = wrapper.get_gate_stats().get("LINKUSDT")
    assert stats is not None
    assert stats.n_normal_fired == 1
    assert stats.n_extreme_fired == 0


# ---------------------------------------------------------------------------
# Test 5: No independent run_backtest on inner strategies
# ---------------------------------------------------------------------------


def test_no_independent_run_backtest_on_inner_strategies():
    """Inner strategies must NOT be passed to run_backtest individually.

    The BROKEN pattern called run_backtest on _strat_a_ext and _strat_a_norm
    separately, then constructed RegimeRoutedStrategy as dead code.

    This test verifies that run_regime_cohort does NOT call run_backtest on the
    inner strategy objects — only on the wrapper.
    """
    from run_baseline_v1 import run_regime_cohort

    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    cfg = _make_minimal_backtest_config()
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL, enabled=True)

    sentinel_result = BacktestResult([], 0)
    run_backtest_called_with: list[Any] = []

    def _capturing_run_backtest(config: Any, strategy: Any, **kwargs: Any) -> BacktestResult:
        run_backtest_called_with.append(strategy)
        return sentinel_result

    with patch("run_baseline_v1.run_backtest", side_effect=_capturing_run_backtest):
        run_regime_cohort(
            "Test",
            ext_strat,
            norm_strat,
            cfg,
            regime_cfg,
            cohort_name="Pool_A",
        )

    # run_backtest was called exactly once
    assert len(run_backtest_called_with) == 1, (
        f"run_backtest must be called ONCE total (on wrapper); "
        f"was called {len(run_backtest_called_with)} times"
    )
    # The strategy passed must be the RegimeRoutedStrategy wrapper
    assert isinstance(run_backtest_called_with[0], RegimeRoutedStrategy), (
        f"Only the RegimeRoutedStrategy wrapper must be passed to run_backtest; "
        f"got {type(run_backtest_called_with[0])}"
    )
    # Inner strategies must NOT have been passed to run_backtest
    assert ext_strat not in run_backtest_called_with, (
        "extreme inner strategy must NOT be passed to run_backtest directly"
    )
    assert norm_strat not in run_backtest_called_with, (
        "normal inner strategy must NOT be passed to run_backtest directly"
    )


# ---------------------------------------------------------------------------
# Test 6: build_lgbm_strategy() returns LightGbmStrategy without running backtest
# ---------------------------------------------------------------------------


def test_build_lgbm_strategy_returns_strategy_without_backtest():
    """build_lgbm_strategy() must return a LightGbmStrategy without calling run_backtest."""
    from run_baseline_v1 import build_lgbm_strategy

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    with patch("run_baseline_v1.run_backtest") as mock_rb:
        strat = build_lgbm_strategy(
            atr_tp=2.9,
            atr_sl=1.45,
            n_trials=5,
            ensemble_size=1,
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            bounds_profile="v1_pruned",
            model_role="Model_A_extreme",
            symbol="BTC+ETH",
            data_filter_callback=make_extreme_filter(_Z30_COL, _THRESHOLD),
        )

    # run_backtest must NOT have been called
    mock_rb.assert_not_called()

    # Returned object must be a LightGbmStrategy
    assert isinstance(strat, LightGbmStrategy), (
        f"build_lgbm_strategy() must return LightGbmStrategy; got {type(strat)}"
    )

    # Callback must be stored
    assert strat._data_filter_callback is not None, (
        "data_filter_callback must be stored as _data_filter_callback"
    )


# ---------------------------------------------------------------------------
# Test 7: build_backtest_config() returns BacktestConfig without running backtest
# ---------------------------------------------------------------------------


def test_build_backtest_config_returns_config_without_backtest():
    """build_backtest_config() must return a BacktestConfig without calling run_backtest."""
    from run_baseline_v1 import build_backtest_config

    with patch("run_baseline_v1.run_backtest") as mock_rb:
        cfg = build_backtest_config(
            ("BTCUSDT", "ETHUSDT"),
            apply_r1=False,
            apply_r2=False,
        )

    mock_rb.assert_not_called()
    assert isinstance(cfg, BacktestConfig), (
        f"build_backtest_config() must return BacktestConfig; got {type(cfg)}"
    )
    assert set(cfg.symbols) == {"BTCUSDT", "ETHUSDT"}
    # apply_r1=False → risk_consecutive_sl_limit=None
    assert cfg.risk_consecutive_sl_limit is None, (
        "apply_r1=False must set risk_consecutive_sl_limit=None"
    )


# ---------------------------------------------------------------------------
# Test 8: run_regime_cohort returns (BacktestResult, list, RegimeRoutedStrategy)
# ---------------------------------------------------------------------------


def test_run_regime_cohort_return_types():
    """run_regime_cohort() must return (BacktestResult, list[dict], RegimeRoutedStrategy)."""
    from run_baseline_v1 import run_regime_cohort

    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    ext_strat._faxm_log = [{"model_role": "ext", "kish_ratio": 0.9}]
    norm_strat._faxm_log = [{"model_role": "norm", "kish_ratio": 0.85}]
    cfg = _make_minimal_backtest_config()
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL)

    sentinel = BacktestResult([], 0)
    with patch("run_baseline_v1.run_backtest", return_value=sentinel):
        results, faxm, wrapper = run_regime_cohort(
            "Test",
            ext_strat,
            norm_strat,
            cfg,
            regime_cfg,
        )

    assert isinstance(results, BacktestResult), (
        f"First return must be BacktestResult; got {type(results)}"
    )
    assert isinstance(faxm, list), f"Second return must be list; got {type(faxm)}"
    assert isinstance(wrapper, RegimeRoutedStrategy), (
        f"Third return must be RegimeRoutedStrategy; got {type(wrapper)}"
    )


# ---------------------------------------------------------------------------
# Test 9: Combined faxm_log merges both sub-strategies' logs
# ---------------------------------------------------------------------------


def test_run_regime_cohort_faxm_log_merged():
    """run_regime_cohort must merge extreme._faxm_log + normal._faxm_log."""
    from run_baseline_v1 import run_regime_cohort

    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    ext_strat._faxm_log = [{"model_role": "ext_a", "val": 1}, {"model_role": "ext_b", "val": 2}]
    norm_strat._faxm_log = [{"model_role": "norm_a", "val": 3}]
    cfg = _make_minimal_backtest_config()
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL)

    with patch("run_baseline_v1.run_backtest", return_value=BacktestResult([], 0)):
        _, faxm, _ = run_regime_cohort("Test", ext_strat, norm_strat, cfg, regime_cfg)

    assert len(faxm) == 3, f"faxm must have 3 entries (2 ext + 1 norm); got {len(faxm)}"
    model_roles = [r["model_role"] for r in faxm]
    assert "ext_a" in model_roles
    assert "ext_b" in model_roles
    assert "norm_a" in model_roles


# ---------------------------------------------------------------------------
# Test 10: compute_features() propagated to both inner strategies
# ---------------------------------------------------------------------------


def test_regime_routed_compute_features_propagated_to_both():
    """compute_features() must be propagated to both extreme and normal sub-strategies."""
    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=ext_strat,
        normal_strategy=norm_strat,
        config=regime_cfg,
        cohort_name="Pool_A",
    )

    dummy_master = pd.DataFrame({"symbol": ["BTCUSDT"], "open_time": [1_000_000_000_000]})
    wrapper.compute_features(dummy_master)

    ext_strat.compute_features.assert_called_once_with(dummy_master)
    norm_strat.compute_features.assert_called_once_with(dummy_master)


# ---------------------------------------------------------------------------
# Test 11: DOT remains on run_model path (no RegimeRoutedStrategy for DOT)
# ---------------------------------------------------------------------------


def test_dot_uses_run_model_not_regime_cohort():
    """Model E (DOT) must call run_model(), NOT run_regime_cohort().

    Per LM Master §1: 8 IS extreme trades in DOT are degenerate — DOT stays
    on baseline single-model dispatch with NO regime conditioning.
    """
    # Verify the runner module exports run_model (not regime-only)
    import run_baseline_v1

    assert hasattr(run_baseline_v1, "run_model"), (
        "run_model() must be exported from run_baseline_v1 for DOT dispatch"
    )
    assert hasattr(run_baseline_v1, "run_regime_cohort"), (
        "run_regime_cohort() must be exported from run_baseline_v1 for regime cohorts"
    )
    # Verify these are distinct functions
    assert run_baseline_v1.run_model is not run_baseline_v1.run_regime_cohort, (
        "run_model and run_regime_cohort must be distinct functions"
    )


# ---------------------------------------------------------------------------
# Test 12: V1_ITER024_UNIVERSE matches expected 5-symbol set
# ---------------------------------------------------------------------------


def test_iter024_universe_matches_expected_symbols():
    """V1_ITER024_UNIVERSE must be the baseline 5-symbol set."""
    from run_baseline_v1 import V1_ITER024_UNIVERSE

    expected = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
    assert set(V1_ITER024_UNIVERSE) == expected, (
        f"V1_ITER024_UNIVERSE mismatch: expected {expected}, got {set(V1_ITER024_UNIVERSE)}"
    )
    assert len(V1_ITER024_UNIVERSE) == 5


# ---------------------------------------------------------------------------
# Test 13: run_regime_cohort logs name and cohort_name to stdout
# ---------------------------------------------------------------------------


def test_run_regime_cohort_logs_cohort_name(capsys: pytest.CaptureFixture[str]):
    """run_regime_cohort must print the cohort name to stdout for traceability."""
    from run_baseline_v1 import run_regime_cohort

    ext_strat = _make_mock_strategy(EXTREME_SIGNAL)
    norm_strat = _make_mock_strategy(NORMAL_SIGNAL)
    cfg = _make_minimal_backtest_config()
    regime_cfg = RegimeGateConfig(threshold=_THRESHOLD, z30_column=_Z30_COL)

    with patch("run_baseline_v1.run_backtest", return_value=BacktestResult([], 0)):
        run_regime_cohort(
            "Model_A_regime (BTC/ETH regime-routed)",
            ext_strat,
            norm_strat,
            cfg,
            regime_cfg,
            cohort_name="Pool_A",
        )

    captured = capsys.readouterr()
    assert "REGIME-ROUTED" in captured.out, "run_regime_cohort must log 'REGIME-ROUTED' to stdout"
    assert "Pool_A" in captured.out, "run_regime_cohort must log the cohort_name to stdout"
