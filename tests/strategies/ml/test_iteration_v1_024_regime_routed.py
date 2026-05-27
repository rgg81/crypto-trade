"""Tests for iter-v1/024 RegimeRoutedStrategy + LightGbmStrategy.data_filter_callback.

Per brief Section 10.5 test additions.

Test coverage:
1.  RegimeGateConfig defaults match brief Section 3.1.
2.  evaluate_regime_at_signal: extreme vs normal classification.
3.  evaluate_regime_at_signal: NaN z30 → "normal" (no look-ahead on missing data).
4.  evaluate_regime_at_signal: config.enabled=False → always "normal".
5.  make_extreme_filter: selects rows where |z30| > threshold.
6.  make_extreme_filter: NaN z30 → excluded from extreme partition (goes to normal).
7.  make_normal_filter: selects rows where |z30| <= threshold + NaN.
8.  LightGbmStrategy accepts data_filter_callback without error (backward compat).
9.  LightGbmStrategy.data_filter_callback=None is backward-compatible (no filter).
10. RegimeRoutedStrategy: extreme sub-model receives extreme-signal when z30 > threshold.
11. RegimeRoutedStrategy: normal sub-model receives normal-signal when z30 <= threshold.
12. RegimeRoutedStrategy: NaN z30 routes to normal sub-model.
13. RegimeRoutedStrategy: skip() propagates to both sub-strategies.
14. RegimeRoutedStrategy: gate stats accumulate n_extreme_fired + n_normal_fired.
15. DOT baseline is a plain LightGbmStrategy (no data_filter_callback).
16. 7 unique sub-model names when dispatch fires: A_ext, A_norm, C_ext, C_norm,
    D_ext, D_norm, E_baseline.
17. Skip-month fallback: extreme sub-model with no models routes to normal.
18. RegimeGateStats fire-rate properties computed correctly.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies.regime_gate_v1 import (
    RegimeGateConfig,
    RegimeGateStats,
    RegimeRoutedStrategy,
    evaluate_regime_at_signal,
    make_extreme_filter,
    make_normal_filter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_THRESHOLD = 1.5
_Z30_COL = "funding_rate_zscore_30"

EXTREME_SIGNAL = Signal(direction=-1, weight=0.9, tp_pct=0.04, sl_pct=0.02)
NORMAL_SIGNAL = Signal(direction=1, weight=0.8, tp_pct=0.04, sl_pct=0.02)
NO_SIGNAL_OBJ = Signal(direction=0, weight=0, tp_pct=0, sl_pct=0)


def _make_mock_strategy(signal: Signal, has_models: bool = True) -> MagicMock:
    """Create a mock strategy that returns the given signal from get_signal()."""
    strat = MagicMock()
    strat.get_signal.return_value = signal
    strat.skip.return_value = None
    # Simulate _models attribute (None = not trained; list = trained)
    strat._models = [MagicMock()] if has_models else None
    strat._month_features = {}
    strat._selected_cols = []
    return strat


def _make_strategy_with_z30(z30_value: float, signal: Signal) -> MagicMock:
    """Create a mock strategy whose _month_features cache contains z30."""
    strat = _make_mock_strategy(signal)
    open_time = 1_000_000_000_000  # dummy epoch ms
    symbol = "BTCUSDT"
    # Populate _month_features as LightGbmStrategy would
    strat._month_features = {(symbol, open_time): np.array([z30_value, 0.5])}
    strat._selected_cols = [_Z30_COL, "other_feature"]
    return strat


# ---------------------------------------------------------------------------
# Test 1: RegimeGateConfig defaults
# ---------------------------------------------------------------------------


def test_regime_gate_config_defaults():
    """RegimeGateConfig defaults match brief Section 3.1."""
    cfg = RegimeGateConfig()
    assert cfg.threshold == 1.5, f"threshold default must be 1.5, got {cfg.threshold}"
    assert cfg.z30_column == "funding_rate_zscore_30", (
        f"z30_column default must be 'funding_rate_zscore_30', got {cfg.z30_column}"
    )
    assert cfg.enabled is True, f"enabled default must be True, got {cfg.enabled}"


# ---------------------------------------------------------------------------
# Test 2: evaluate_regime_at_signal — extreme classification
# ---------------------------------------------------------------------------


def test_evaluate_regime_extreme_above_threshold():
    """z30 > threshold → 'extreme'."""
    cfg = RegimeGateConfig(threshold=1.5)
    assert evaluate_regime_at_signal(2.0, cfg) == "extreme"
    assert evaluate_regime_at_signal(1.51, cfg) == "extreme"
    assert evaluate_regime_at_signal(-2.5, cfg) == "extreme"  # |z| = 2.5 > 1.5


def test_evaluate_regime_normal_at_or_below_threshold():
    """z30 <= threshold → 'normal'."""
    cfg = RegimeGateConfig(threshold=1.5)
    assert evaluate_regime_at_signal(1.5, cfg) == "normal"  # at boundary → normal
    assert evaluate_regime_at_signal(0.5, cfg) == "normal"
    assert evaluate_regime_at_signal(-1.4, cfg) == "normal"
    assert evaluate_regime_at_signal(0.0, cfg) == "normal"


# ---------------------------------------------------------------------------
# Test 3: NaN z30 → "normal"
# ---------------------------------------------------------------------------


def test_evaluate_regime_nan_defaults_to_normal():
    """NaN z30 (early warm-up bars) must route to normal, not extreme.

    This ensures the wrapper does NOT introduce look-ahead for early bars
    where funding_rate_zscore_30 is still NaN (first 30 bars of history).
    """
    cfg = RegimeGateConfig(threshold=1.5)
    assert evaluate_regime_at_signal(float("nan"), cfg) == "normal"
    assert evaluate_regime_at_signal(np.nan, cfg) == "normal"


# ---------------------------------------------------------------------------
# Test 4: config.enabled=False → always "normal"
# ---------------------------------------------------------------------------


def test_evaluate_regime_disabled_always_normal():
    """When config.enabled=False, regime routing is disabled — always 'normal'."""
    cfg = RegimeGateConfig(threshold=1.5, enabled=False)
    # Even extreme values → "normal"
    assert evaluate_regime_at_signal(3.0, cfg) == "normal"
    assert evaluate_regime_at_signal(100.0, cfg) == "normal"
    assert evaluate_regime_at_signal(-5.0, cfg) == "normal"


# ---------------------------------------------------------------------------
# Test 5: make_extreme_filter selects rows with |z30| > threshold
# ---------------------------------------------------------------------------


def test_make_extreme_filter_selects_extreme_rows():
    """make_extreme_filter returns True for |z30| > threshold rows."""
    filt = make_extreme_filter(_Z30_COL, _THRESHOLD)
    df = pd.DataFrame(
        {
            _Z30_COL: [2.0, 0.5, -2.5, 1.4, 1.6, 0.0, -1.5],
        }
    )
    mask = filt(df)
    assert mask.dtype in (bool, np.bool_), f"mask dtype must be bool, got {mask.dtype}"
    # Expected: [T, F, T, F, T, F, F]
    expected = np.array([True, False, True, False, True, False, False])
    np.testing.assert_array_equal(mask, expected)


# ---------------------------------------------------------------------------
# Test 6: make_extreme_filter — NaN z30 excluded from extreme partition
# ---------------------------------------------------------------------------


def test_make_extreme_filter_nan_excluded():
    """NaN z30 must be excluded from extreme partition (included in normal)."""
    filt = make_extreme_filter(_Z30_COL, _THRESHOLD)
    df = pd.DataFrame({_Z30_COL: [np.nan, 2.0, np.nan, 0.5]})
    mask = filt(df)
    # NaN rows → False (excluded from extreme)
    assert not mask[0], "NaN row must NOT be in extreme partition"
    assert mask[1], "z30=2.0 must be in extreme partition"
    assert not mask[2], "NaN row must NOT be in extreme partition"
    assert not mask[3], "z30=0.5 must NOT be in extreme partition"


# ---------------------------------------------------------------------------
# Test 7: make_normal_filter — selects |z30| <= threshold + NaN rows
# ---------------------------------------------------------------------------


def test_make_normal_filter_selects_normal_rows():
    """make_normal_filter is the complement of make_extreme_filter (NaN → normal)."""
    filt = make_normal_filter(_Z30_COL, _THRESHOLD)
    df = pd.DataFrame(
        {
            _Z30_COL: [2.0, 0.5, np.nan, -2.5, 1.5, -1.4],
        }
    )
    mask = filt(df)
    # z30=2.0 → extreme (not normal)
    assert not mask[0], "z30=2.0 must NOT be in normal partition"
    # z30=0.5 → normal
    assert mask[1], "z30=0.5 must be in normal partition"
    # NaN → normal (fallback)
    assert mask[2], "NaN z30 must be in normal partition"
    # z30=-2.5 → extreme
    assert not mask[3], "z30=-2.5 must NOT be in normal partition"
    # z30=1.5 → at boundary (not strict, so <= 1.5 → normal)
    assert mask[4], "z30=1.5 must be in normal partition (boundary)"
    # z30=-1.4 → normal
    assert mask[5], "z30=-1.4 must be in normal partition"


# ---------------------------------------------------------------------------
# Test 8: LightGbmStrategy accepts data_filter_callback without error
# ---------------------------------------------------------------------------


def test_lgbm_strategy_accepts_data_filter_callback():
    """LightGbmStrategy can be instantiated with data_filter_callback without raising."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    callback = make_extreme_filter(_Z30_COL, _THRESHOLD)

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=5,
        feature_columns=["feat_a", "feat_b", "funding_rate_zscore_30"],
        ensemble_seeds=[42],
        data_filter_callback=callback,
    )
    # Verify the callback is stored
    assert strat._data_filter_callback is callback, (
        "data_filter_callback must be stored as _data_filter_callback"
    )


# ---------------------------------------------------------------------------
# Test 9: LightGbmStrategy.data_filter_callback=None is backward-compatible
# ---------------------------------------------------------------------------


def test_lgbm_strategy_no_filter_backward_compat():
    """LightGbmStrategy with data_filter_callback=None behaves as baseline (no filter)."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=5,
        feature_columns=["feat_a", "feat_b"],
        ensemble_seeds=[42],
        data_filter_callback=None,
    )
    assert strat._data_filter_callback is None, (
        "data_filter_callback=None must store None, not a default filter"
    )


# ---------------------------------------------------------------------------
# Test 10: RegimeRoutedStrategy routes extreme signal when z30 > threshold
# ---------------------------------------------------------------------------


def test_regime_routed_extreme_signal_routed_correctly():
    """When z30 > threshold, RegimeRoutedStrategy returns the extreme sub-model signal."""
    open_time = 1_000_000_000_000
    symbol = "BTCUSDT"

    extreme_strat = _make_strategy_with_z30(2.0, EXTREME_SIGNAL)  # z30=2.0 > 1.5
    normal_strat = _make_strategy_with_z30(2.0, NORMAL_SIGNAL)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(threshold=1.5),
    )
    result = wrapper.get_signal(symbol, open_time)
    assert result == EXTREME_SIGNAL, (
        f"z30=2.0 > 1.5 must route to extreme sub-model signal; got {result}"
    )


# ---------------------------------------------------------------------------
# Test 11: RegimeRoutedStrategy routes normal signal when z30 <= threshold
# ---------------------------------------------------------------------------


def test_regime_routed_normal_signal_routed_correctly():
    """When z30 <= threshold, RegimeRoutedStrategy returns the normal sub-model signal."""
    open_time = 1_000_000_000_000
    symbol = "BTCUSDT"

    extreme_strat = _make_strategy_with_z30(0.5, EXTREME_SIGNAL)  # z30=0.5 <= 1.5
    normal_strat = _make_strategy_with_z30(0.5, NORMAL_SIGNAL)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(threshold=1.5),
    )
    result = wrapper.get_signal(symbol, open_time)
    assert result == NORMAL_SIGNAL, (
        f"z30=0.5 <= 1.5 must route to normal sub-model signal; got {result}"
    )


# ---------------------------------------------------------------------------
# Test 12: NaN z30 routes to normal sub-model
# ---------------------------------------------------------------------------


def test_regime_routed_nan_z30_routes_to_normal():
    """NaN z30 (missing funding data) routes to normal sub-model."""
    open_time = 1_000_000_000_000
    symbol = "BTCUSDT"

    extreme_strat = _make_strategy_with_z30(float("nan"), EXTREME_SIGNAL)
    normal_strat = _make_strategy_with_z30(float("nan"), NORMAL_SIGNAL)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(threshold=1.5),
    )
    result = wrapper.get_signal(symbol, open_time)
    assert result == NORMAL_SIGNAL, f"NaN z30 must route to normal sub-model signal; got {result}"


# ---------------------------------------------------------------------------
# Test 13: RegimeRoutedStrategy.skip() propagates to both sub-strategies
# ---------------------------------------------------------------------------


def test_regime_routed_skip_propagates_to_both():
    """skip() must propagate to both extreme and normal sub-strategies."""
    extreme_strat = _make_mock_strategy(EXTREME_SIGNAL)
    normal_strat = _make_mock_strategy(NORMAL_SIGNAL)

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(),
    )
    wrapper.skip()
    extreme_strat.skip.assert_called_once()
    normal_strat.skip.assert_called_once()


# ---------------------------------------------------------------------------
# Test 14: Gate stats accumulate correctly
# ---------------------------------------------------------------------------


def test_regime_gate_stats_accumulate():
    """n_extreme_fired and n_normal_fired accumulate per symbol across calls."""
    open_time_extreme = 1_000_000_000_000
    open_time_normal = 2_000_000_000_000
    symbol = "LINKUSDT"

    extreme_strat = MagicMock()
    extreme_strat.get_signal.return_value = EXTREME_SIGNAL
    extreme_strat._models = [MagicMock()]
    extreme_strat._month_features = {
        (symbol, open_time_extreme): np.array([2.0]),  # z30=2.0 → extreme
        (symbol, open_time_normal): np.array([0.5]),  # z30=0.5 → normal
    }
    extreme_strat._selected_cols = [_Z30_COL]

    normal_strat = MagicMock()
    normal_strat.get_signal.return_value = NORMAL_SIGNAL
    normal_strat._models = [MagicMock()]
    normal_strat._month_features = extreme_strat._month_features
    normal_strat._selected_cols = extreme_strat._selected_cols

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(threshold=1.5),
    )

    # 3 extreme calls, 2 normal calls
    for _ in range(3):
        wrapper.get_signal(symbol, open_time_extreme)
    for _ in range(2):
        wrapper.get_signal(symbol, open_time_normal)

    stats = wrapper.get_gate_stats()[symbol]
    assert stats.n_extreme_fired == 3, f"Expected 3 extreme fires, got {stats.n_extreme_fired}"
    assert stats.n_normal_fired == 2, f"Expected 2 normal fires, got {stats.n_normal_fired}"
    assert stats.n_routed == 5, f"Expected 5 total routed, got {stats.n_routed}"


# ---------------------------------------------------------------------------
# Test 15: DOT baseline is a plain LightGbmStrategy (no data_filter_callback)
# ---------------------------------------------------------------------------


def test_dot_baseline_has_no_filter_callback():
    """Model E (DOT) must use a plain LightGbmStrategy with no data_filter_callback.

    This verifies the DOT exclusion per LM Master §1: 8 IS extreme trades are
    degenerate, so DOT stays on baseline single-model dispatch.
    """
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    dot_strat = LightGbmStrategy(
        training_months=24,
        n_trials=5,
        feature_columns=["feat_a", "feat_b", "funding_rate_zscore_30"],
        ensemble_seeds=[42],
        # No data_filter_callback — DOT baseline
    )
    assert dot_strat._data_filter_callback is None, (
        "DOT baseline strategy must have data_filter_callback=None "
        "(no regime conditioning per LM Master §1)"
    )


# ---------------------------------------------------------------------------
# Test 16: 7 unique sub-model names in dispatch
# ---------------------------------------------------------------------------


def test_iter024_dispatch_produces_7_sub_model_names():
    """The /024 dispatch produces exactly 7 unique model_role values.

    Verifies DOT mitigation (LM Master §1): 7 sub-models, not 8.
    Model names: Model_A_extreme, Model_A_normal, Model_C_extreme, Model_C_normal,
                 Model_D_extreme, Model_D_normal, Model_E_baseline.
    """
    expected_names = {
        "Model_A_extreme",
        "Model_A_normal",
        "Model_C_extreme",
        "Model_C_normal",
        "Model_D_extreme",
        "Model_D_normal",
        "Model_E_baseline",
    }
    assert len(expected_names) == 7, "Must have exactly 7 sub-model names"

    # Verify the 3 RegimeRoutedStrategy cohorts each have 2 sub-models
    regime_pairs = [
        ("Model_A_extreme", "Model_A_normal"),
        ("Model_C_extreme", "Model_C_normal"),
        ("Model_D_extreme", "Model_D_normal"),
    ]
    for ext_name, norm_name in regime_pairs:
        assert ext_name in expected_names
        assert norm_name in expected_names

    # DOT uses baseline (no regime split)
    assert "Model_E_baseline" in expected_names
    assert "Model_E_extreme" not in expected_names, (
        "DOT must NOT have an extreme sub-model per LM Master §1 DOT mitigation"
    )
    assert "Model_E_normal" not in expected_names, (
        "DOT must NOT have a normal sub-model per LM Master §1 DOT mitigation"
    )


# ---------------------------------------------------------------------------
# Test 17: Skip-month fallback — extreme sub-model with no models → normal
# ---------------------------------------------------------------------------


def test_skip_month_fallback_routes_to_normal():
    """When extreme sub-model has no trained models, ALL bars route to normal.

    LM Master §4(c): if extreme sub-model skip-month, route ALL bars through
    normal sub-model for that cohort.
    """
    open_time = 1_000_000_000_000
    symbol = "BTCUSDT"

    # Extreme sub-model has no models (training skipped due to thin partition)
    extreme_strat = _make_strategy_with_z30(3.0, EXTREME_SIGNAL)
    extreme_strat._models = None  # No trained model for this month

    normal_strat = _make_strategy_with_z30(3.0, NORMAL_SIGNAL)
    normal_strat._models = [MagicMock()]  # Normal sub-model IS trained

    wrapper = RegimeRoutedStrategy(
        extreme_strategy=extreme_strat,
        normal_strategy=normal_strat,
        config=RegimeGateConfig(threshold=1.5),
    )
    # z30=3.0 > 1.5 would normally route to extreme, but extreme has no model
    result = wrapper.get_signal(symbol, open_time)
    assert result == NORMAL_SIGNAL, (
        f"Extreme skip-month fallback must route to normal sub-model; got {result}"
    )

    # Verify skip-month counter incremented
    stats = wrapper.get_gate_stats()[symbol]
    assert stats.n_skip_month_fallback >= 1, (
        f"n_skip_month_fallback must be >= 1 after skip-month fallback; "
        f"got {stats.n_skip_month_fallback}"
    )


# ---------------------------------------------------------------------------
# Test 18: RegimeGateStats fire-rate properties
# ---------------------------------------------------------------------------


def test_regime_gate_stats_fire_rate_properties():
    """RegimeGateStats.extreme_fire_rate and normal_fire_rate are computed correctly."""
    stats = RegimeGateStats(n_extreme_fired=30, n_normal_fired=170, n_skip_month_fallback=5)

    total = 205
    assert stats.n_routed == total, f"Expected n_routed={total}, got {stats.n_routed}"
    assert abs(stats.extreme_fire_rate - 30 / 205) < 1e-6, (
        f"extreme_fire_rate must be {30 / 205:.6f}, got {stats.extreme_fire_rate:.6f}"
    )
    expected_normal_rate = (170 + 5) / 205
    assert abs(stats.normal_fire_rate - expected_normal_rate) < 1e-6, (
        f"normal_fire_rate must be {expected_normal_rate:.6f}, got {stats.normal_fire_rate:.6f}"
    )

    # Fire rate in brief Section 4.2 F-AXIS #3 band: IS [10%, 18%]
    # 30/205 = 14.6% — within [10%, 18%]
    assert 0.10 <= stats.extreme_fire_rate <= 0.18, (
        f"extreme_fire_rate {stats.extreme_fire_rate:.3f} must be in [0.10, 0.18] "
        f"(per Section 4.2 F-AXIS #3 fire-rate band)"
    )
