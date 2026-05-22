"""Smoke tests for XgboostStrategy (iter-v3/016).

Tests verify:
1. Constructor accepts valid arguments and raises on invalid ones.
2. Parity with LightGbmStrategy: raises ValueError on None/empty feature_columns.
3. Parity with LightGbmStrategy: raises ValueError on None/empty ensemble_seeds.
4. Import path is correct (xgb.py parallel to lgbm.py).
5. XgboostStrategy and LightGbmStrategy are distinct classes.
"""

from __future__ import annotations

import pytest


def test_xgboost_strategy_import():
    """XgboostStrategy is importable from the correct module path."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    assert XgboostStrategy is not None


def test_xgboost_strategy_constructor_smoke():
    """XgboostStrategy constructs without error with minimal valid args."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    strat = XgboostStrategy(
        training_months=24,
        n_trials=10,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        ensemble_seeds=[42],
        feature_columns=["hurst_100"],
        use_atr_labeling=True,
        atr_tp_multiplier=2.0,
        atr_sl_multiplier=1.0,
    )
    assert strat.training_months == 24
    assert strat.n_trials == 10
    assert strat.ensemble_seeds == [42]
    assert strat.feature_columns == ["hurst_100"]
    assert strat._fast_mode is False


def test_xgboost_strategy_raises_on_none_feature_columns():
    """XgboostStrategy must raise ValueError when feature_columns=None."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        XgboostStrategy(
            training_months=24,
            n_trials=10,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[42],
            feature_columns=None,
        )


def test_xgboost_strategy_raises_on_empty_feature_columns():
    """XgboostStrategy must raise ValueError when feature_columns=[]."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        XgboostStrategy(
            training_months=24,
            n_trials=10,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[42],
            feature_columns=[],
        )


def test_xgboost_strategy_raises_on_none_ensemble_seeds():
    """XgboostStrategy must raise ValueError when ensemble_seeds=None."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="ensemble_seeds must be a non-empty list"):
        XgboostStrategy(
            training_months=24,
            n_trials=10,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=None,
            feature_columns=["hurst_100"],
        )


def test_xgboost_strategy_raises_on_empty_ensemble_seeds():
    """XgboostStrategy must raise ValueError when ensemble_seeds=[]."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="ensemble_seeds must be a non-empty list"):
        XgboostStrategy(
            training_months=24,
            n_trials=10,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[],
            feature_columns=["hurst_100"],
        )


def test_xgboost_strategy_raises_on_ood_without_features():
    """XgboostStrategy must raise ValueError when ood_enabled=True but ood_features=None."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    with pytest.raises(ValueError, match="ood_features must be specified"):
        XgboostStrategy(
            training_months=24,
            n_trials=10,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[42],
            feature_columns=["hurst_100"],
            ood_enabled=True,
            ood_features=None,
        )


def test_xgboost_strategy_distinct_from_lgbm():
    """XgboostStrategy and LightGbmStrategy are distinct classes."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    assert XgboostStrategy is not LightGbmStrategy


def test_xgboost_strategy_fast_mode():
    """XgboostStrategy stores fast_mode correctly."""
    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    strat = XgboostStrategy(
        training_months=24,
        n_trials=10,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        ensemble_seeds=[42],
        feature_columns=["hurst_100"],
        fast_mode=True,
    )
    assert strat._fast_mode is True


def test_optimization_xgb_import():
    """optimize_and_train_xgb is importable from optimization_xgb."""
    from crypto_trade.strategies.ml.optimization_xgb import optimize_and_train_xgb

    assert callable(optimize_and_train_xgb)


def test_xgboost_strategy_compute_features_smoke():
    """compute_features() runs without TypeError on a small master frame.

    Regression guard for the lookahead-bias fix on main (commit 5566a69):
    ``generate_monthly_splits`` requires ``label_timeout_minutes`` and
    ``interval_minutes`` as kwargs. xgb.py:219's call to that helper was
    initially missing those args — silently disabling the embargo and
    re-introducing the exact bug the fix was added to prevent. This test
    invokes the call site so a future regression would TypeError here.

    Construction-only tests above never exercised this path — that's how
    the bug sat undetected.
    """
    import numpy as np
    import pandas as pd

    from crypto_trade.strategies.ml.xgb import XgboostStrategy

    # 18 months of synthetic 8h candles for one symbol. 18 > training_months=24's
    # warmup is intentionally insufficient (would produce 0 splits) — we only
    # need the call site to fire. generate_monthly_splits gracefully returns
    # an empty list when there's no test month, no TypeError expected.
    n_bars = 18 * 30 * 3  # ~18 months * 30 days * 3 8h candles/day
    interval_ms = 8 * 3600 * 1000
    start_ms = 1_577_836_800_000  # 2020-01-01 UTC
    open_times = np.arange(start_ms, start_ms + n_bars * interval_ms, interval_ms)
    master = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"] * n_bars,
            "open_time": open_times,
            "close_time": open_times + interval_ms - 1,
            "close": np.linspace(20000.0, 30000.0, n_bars),
        }
    )

    strategy = XgboostStrategy(
        training_months=24,
        n_trials=10,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        ensemble_seeds=[42],
        feature_columns=["hurst_100"],
        # use_atr_labeling defaults to False → skips ATR loading path
        # so the smoke focuses on the splits-generation call site (xgb.py:219).
    )
    # Will TypeError on the missing-kwargs regression — that's the guard.
    strategy.compute_features(master)
    # splits may be empty (training_months>data months) — that's fine
    assert isinstance(strategy._splits, list)
    assert strategy._interval == "8h"
    assert strategy._current_month is None


def test_optimization_xgb_reexports_label_helpers():
    """optimization_xgb re-exports label conversion helpers from optimization."""
    from crypto_trade.strategies.ml.optimization_xgb import (
        classes_to_labels,
        labels_to_classes,
    )

    import numpy as np

    labels = np.array([-1, 1, 1, -1])
    classes = labels_to_classes(labels)
    assert list(classes) == [0, 1, 1, 0]
    recovered = classes_to_labels(classes)
    assert list(recovered) == [-1, 1, 1, -1]
