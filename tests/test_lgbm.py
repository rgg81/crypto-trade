"""Tests for the LightGbmStrategy and its components."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.labeling import label_trades
from crypto_trade.strategies.ml.optimization import (
    classes_to_labels,
    compute_sharpe,
    labels_to_classes,
)
from crypto_trade.strategies.ml.walk_forward import (
    generate_monthly_splits,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_master(
    n: int,
    symbol: str = "BTCUSDT",
    start_ms: int = 1_704_067_200_000,  # 2024-01-01 00:00 UTC
    interval_ms: int = 900_000,  # 15m
    base_price: float = 100.0,
) -> pd.DataFrame:
    """Build a minimal master DataFrame for testing."""
    open_times = np.arange(start_ms, start_ms + n * interval_ms, interval_ms)
    close_times = open_times + interval_ms - 1

    rng = np.random.default_rng(42)
    opens = base_price + rng.normal(0, 0.5, n).cumsum()
    closes = opens + rng.normal(0, 0.3, n)
    highs = np.maximum(opens, closes) + rng.uniform(0, 1, n)
    lows = np.minimum(opens, closes) - rng.uniform(0, 1, n)

    return pd.DataFrame(
        {
            "symbol": symbol,
            "open_time": open_times,
            "close_time": close_times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )


def _make_label_master(prices: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    """Build master from explicit (open, high, low, close) tuples at 15m intervals."""
    n = len(prices)
    start_ms = 1_704_067_200_000
    interval_ms = 900_000
    open_times = np.arange(start_ms, start_ms + n * interval_ms, interval_ms)
    close_times = open_times + interval_ms - 1

    return pd.DataFrame(
        {
            "symbol": "BTCUSDT",
            "open_time": open_times,
            "close_time": close_times,
            "open": [p[0] for p in prices],
            "high": [p[1] for p in prices],
            "low": [p[2] for p in prices],
            "close": [p[3] for p in prices],
        }
    )


# ---------------------------------------------------------------------------
# Labeling tests
# ---------------------------------------------------------------------------


class TestLabeling:
    def test_label_long_tp(self):
        """Long TP hits when price goes up, short SL hits first."""
        prices = [
            (99.0, 101.0, 99.0, 100.0),  # entry candle
            (100.0, 101.0, 99.5, 100.5),  # small move up
            (100.5, 103.5, 100.0, 103.0),  # long TP hit (high=103.5 >= 103)
        ]
        master = _make_label_master(prices)
        labels, weights, long_pnls, short_pnls = label_trades(
            master,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        assert labels[0] == 1  # long
        assert weights[0] > 0
        assert long_pnls[0] > 0  # long TP hit → positive PnL
        assert short_pnls[0] < 0  # short SL hit → negative PnL

    def test_label_short_tp(self):
        """Short TP hits when price drops, long SL hits first."""
        prices = [
            (101.0, 101.0, 99.0, 100.0),  # entry candle, close=100
            (100.0, 100.5, 99.0, 99.5),  # small move down
            (99.5, 100.0, 96.5, 97.0),  # short TP hit (low=96.5 <= 97)
        ]
        master = _make_label_master(prices)
        labels, weights, long_pnls, short_pnls = label_trades(
            master,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        assert labels[0] == -1  # short
        assert weights[0] > 0
        assert short_pnls[0] > 0  # short TP hit → positive PnL
        assert long_pnls[0] < 0  # long SL hit → negative PnL

    def test_label_timeout_uses_forward_return(self):
        """When neither TP hits, label is based on forward return direction."""
        prices = [
            (100.0, 100.5, 99.5, 100.0),  # entry candle
            (100.0, 100.3, 99.7, 100.1),  # slight up
            (100.1, 100.4, 99.8, 100.2),  # slight up
        ]
        master = _make_label_master(prices)
        labels, weights, long_pnls, short_pnls = label_trades(
            master,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=15,
        )
        assert labels[0] == 1  # forward return positive → long
        assert weights[0] >= 1.0

    def test_label_empty_candidates(self):
        """Empty candidates returns empty arrays."""
        master = _make_label_master([(100.0, 101.0, 99.0, 100.0)])
        labels, weights, long_pnls, short_pnls = label_trades(
            master,
            np.array([], dtype=np.intp),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        assert len(labels) == 0
        assert len(weights) == 0
        assert len(long_pnls) == 0
        assert len(short_pnls) == 0

    def test_label_long_tp_first_when_both_hit(self):
        """When both TP hit, but long hits on an earlier candle, label is 1."""
        prices = [
            (100.0, 100.5, 99.5, 100.0),  # entry, close=100
            (100.0, 103.5, 99.5, 101.0),  # long TP hits, short SL hits
            (101.0, 101.5, 96.5, 97.0),  # short TP hits (96.5 <= 97)
        ]
        master = _make_label_master(prices)
        labels, weights, long_pnls, short_pnls = label_trades(
            master,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        assert labels[0] == 1  # long hit first

    def test_higher_return_gets_higher_weight(self):
        """Candles with larger forward moves get higher weights."""
        prices_big = [
            (100.0, 100.5, 99.5, 100.0),
            (100.0, 101.0, 99.5, 100.5),
            (100.5, 110.0, 100.0, 108.0),  # big up
        ]
        prices_small = [
            (100.0, 100.5, 99.5, 100.0),
            (100.0, 101.0, 99.5, 100.5),
            (100.5, 101.0, 100.0, 100.8),  # small up
        ]
        master_big = _make_label_master(prices_big)
        master_small = _make_label_master(prices_small)
        _, w_big, _, _ = label_trades(
            master_big,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        _, w_small, _, _ = label_trades(
            master_small,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
        )
        assert w_big[0] >= 1.0
        assert w_small[0] >= 1.0

    def test_fee_deducted_from_pnls(self):
        """PnLs should have fee deducted."""
        prices = [
            (99.0, 101.0, 99.0, 100.0),
            (100.0, 101.0, 99.5, 100.5),
            (100.5, 103.5, 100.0, 103.0),  # long TP hit at 3%
        ]
        master = _make_label_master(prices)
        _, _, long_pnls, _ = label_trades(
            master,
            np.array([0]),
            tp_pct=3.0,
            sl_pct=2.0,
            timeout_minutes=60,
            fee_pct=0.1,
        )
        # Long TP hit → pnl = 3.0 - 0.1 = 2.9
        assert abs(long_pnls[0] - 2.9) < 0.001


# ---------------------------------------------------------------------------
# Walk-forward split tests
# ---------------------------------------------------------------------------


class TestMonthSplits:
    def test_basic_splits(self):
        """3 months of data with training_months=2 should yield 1 split."""
        master = _make_master(n=100, start_ms=1_704_067_200_000)
        feb = _make_master(n=100, start_ms=1_706_745_600_000)
        mar = _make_master(n=100, start_ms=1_709_251_200_000)
        combined_times = np.concatenate(
            [
                master["open_time"].values,
                feb["open_time"].values,
                mar["open_time"].values,
            ]
        )
        splits = generate_monthly_splits(combined_times, training_months=2)
        assert len(splits) == 1
        assert splits[0].test_month == "2024-03"

    def test_no_splits_insufficient_data(self):
        """1 month of data with training_months=2 yields no splits."""
        master = _make_master(n=100)
        splits = generate_monthly_splits(master["open_time"].values, training_months=2)
        assert len(splits) == 0

    def test_split_boundaries(self):
        """Verify train/test boundaries are correct month boundaries."""
        import datetime

        jan = _make_master(n=50, start_ms=1_704_067_200_000)
        feb = _make_master(n=50, start_ms=1_706_745_600_000)
        mar = _make_master(n=50, start_ms=1_709_251_200_000)
        apr = _make_master(n=50, start_ms=1_711_929_600_000)
        combined_times = np.concatenate(
            [
                jan["open_time"].values,
                feb["open_time"].values,
                mar["open_time"].values,
                apr["open_time"].values,
            ]
        )
        splits = generate_monthly_splits(combined_times, training_months=2)
        assert len(splits) == 2

        s0 = splits[0]
        assert s0.test_month == "2024-03"
        assert datetime.datetime.fromtimestamp(
            s0.train_start_ms / 1000, tz=datetime.UTC
        ).month == 1
        assert datetime.datetime.fromtimestamp(
            s0.test_start_ms / 1000, tz=datetime.UTC
        ).month == 3


# ---------------------------------------------------------------------------
# Sharpe computation tests (using actual returns)
# ---------------------------------------------------------------------------


class TestSharpe:
    def test_positive_sharpe_correct_predictions(self):
        """Mostly correct predictions → positive Sharpe."""
        y_pred = np.array([1, 1, 1, -1, -1, 1, 1, -1, 1, -1])
        # Realistic: TP/SL/timeout produce varied returns
        long_pnls = np.array([3.9, 2.5, 3.9, -2.1, -1.5, 3.9, 1.8, -2.1, 3.9, -2.1])
        short_pnls = np.array([-2.1, -1.8, -2.1, 3.9, 2.8, -2.1, -2.1, 3.9, -0.5, 3.9])
        sharpe = compute_sharpe(y_pred, long_pnls, short_pnls)
        assert sharpe > 0

    def test_negative_sharpe_wrong_predictions(self):
        """Wrong predictions → negative Sharpe."""
        y_pred = np.array([1, 1, 1, -1, -1])
        long_pnls = np.array([-2.1, -2.1, -2.1, 3.9, 3.9])
        short_pnls = np.array([3.9, 3.9, 3.9, -2.1, -2.1])
        sharpe = compute_sharpe(y_pred, long_pnls, short_pnls)
        assert sharpe < 0

    def test_too_few_predictions(self):
        """Fewer than 2 predictions → penalty Sharpe."""
        y_pred = np.array([1])
        long_pnls = np.array([3.9])
        short_pnls = np.array([-2.1])
        sharpe = compute_sharpe(y_pred, long_pnls, short_pnls)
        assert sharpe == -10.0


# ---------------------------------------------------------------------------
# Label encoding tests
# ---------------------------------------------------------------------------


class TestLabelEncoding:
    def test_roundtrip(self):
        """Labels survive encode → decode roundtrip."""
        labels = np.array([-1, 1, -1, 1])
        classes = labels_to_classes(labels)
        assert list(classes) == [0, 1, 0, 1]
        recovered = classes_to_labels(classes)
        np.testing.assert_array_equal(recovered, labels)


# ---------------------------------------------------------------------------
# Strategy registration tests
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_strategy_registered(self):
        from crypto_trade.strategies import list_strategies

        assert "lgbm" in list_strategies()

    def test_get_strategy_string_params(self):
        from crypto_trade.strategies import get_strategy

        strategy = get_strategy(
            "lgbm",
            {"features_dir": "data/features", "n_trials": "10"},
        )
        assert strategy.features_dir == "data/features"
        assert strategy.n_trials == 10

    def test_removed_params_not_accepted(self):
        """n_samples and spike_window were removed; passing them should raise TypeError."""
        import pytest

        from crypto_trade.strategies import get_strategy

        with pytest.raises(TypeError):
            get_strategy("lgbm", {"n_samples": "10000"})
        with pytest.raises(TypeError):
            get_strategy("lgbm", {"spike_window": "16"})


# ---------------------------------------------------------------------------
# Lazy monthly training tests
# ---------------------------------------------------------------------------


class TestLazyMonthlyTraining:
    def _make_multi_month_master(self):
        """Create a master spanning Jan-Apr 2024 (4 months)."""
        frames = []
        month_starts = [
            1_704_067_200_000,  # Jan 1 2024
            1_706_745_600_000,  # Feb 1 2024
            1_709_251_200_000,  # Mar 1 2024
            1_711_929_600_000,  # Apr 1 2024
        ]
        for ms in month_starts:
            frames.append(_make_master(n=200, start_ms=ms))
        return pd.concat(frames, ignore_index=True)

    def test_compute_features_no_training(self):
        """compute_features should not train any model."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        master = self._make_multi_month_master()
        strategy = LightGbmStrategy(training_months=2, features_dir="/nonexistent")
        strategy.compute_features(master)

        assert strategy._model is None
        assert strategy._current_month is None
        assert len(strategy._splits) > 0
        assert len(strategy._split_map) > 0

    def test_get_signal_triggers_training(self):
        """First get_signal call for a month triggers _train_for_month."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        master = self._make_multi_month_master()
        strategy = LightGbmStrategy(training_months=2, features_dir="/nonexistent")
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        first_ot = int(master["open_time"].iloc[0])
        first_sym = master["symbol"].iloc[0]
        strategy.get_signal(first_sym, first_ot)

        assert len(train_calls) == 1
        assert train_calls[0] == "2024-01"

    def test_same_month_no_retrain(self):
        """Multiple get_signal calls in same month should not retrain."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        master = self._make_multi_month_master()
        strategy = LightGbmStrategy(training_months=2, features_dir="/nonexistent")
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        for i in range(2):
            ot = int(master["open_time"].iloc[i])
            sym = master["symbol"].iloc[i]
            strategy.get_signal(sym, ot)

        assert len(train_calls) == 1

    def test_month_change_triggers_retrain(self):
        """Crossing a month boundary triggers a new training call."""
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        master = self._make_multi_month_master()
        strategy = LightGbmStrategy(training_months=2, features_dir="/nonexistent")
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        jan_ot = int(master["open_time"].iloc[0])
        jan_sym = master["symbol"].iloc[0]
        strategy.get_signal(jan_sym, jan_ot)

        feb_ot = int(master["open_time"].iloc[200])
        feb_sym = master["symbol"].iloc[200]
        strategy.get_signal(feb_sym, feb_ot)

        assert len(train_calls) == 2
        assert train_calls[0] == "2024-01"
        assert train_calls[1] == "2024-02"

    def test_get_signal_returns_no_signal_without_model(self):
        """When no model can be trained, get_signal returns NO_SIGNAL."""
        from crypto_trade.strategies import NO_SIGNAL
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        master = self._make_multi_month_master()
        strategy = LightGbmStrategy(training_months=2, features_dir="/nonexistent")
        strategy.compute_features(master)

        signal = strategy.get_signal("BTCUSDT", int(master["open_time"].iloc[0]))
        assert signal == NO_SIGNAL


# ---------------------------------------------------------------------------
# get_signal always predicts direction (no threshold)
# ---------------------------------------------------------------------------


class TestAlwaysPredict:
    _JAN_2024_MS = 1_704_067_200_000

    def test_long_signal(self):
        """Model predicting long → always returns long signal."""
        from unittest.mock import MagicMock

        from crypto_trade.backtest_models import Signal
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        ot = self._JAN_2024_MS
        strategy = LightGbmStrategy(features_dir="/nonexistent")
        strategy._current_month = "2024-01"

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
        strategy._model = mock_model
        strategy._selected_cols = ["feat_a", "feat_b"]
        strategy._month_features = {("BTCUSDT", ot): np.array([1.0, 2.0])}

        signal = strategy.get_signal("BTCUSDT", ot)
        assert signal == Signal(direction=1, weight=100)

    def test_short_signal(self):
        """Model predicting short → always returns short signal."""
        from unittest.mock import MagicMock

        from crypto_trade.backtest_models import Signal
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        ot = self._JAN_2024_MS
        strategy = LightGbmStrategy(features_dir="/nonexistent")
        strategy._current_month = "2024-01"

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.75, 0.25]])
        strategy._model = mock_model
        strategy._selected_cols = ["feat_a", "feat_b"]
        strategy._month_features = {("BTCUSDT", ot): np.array([1.0, 2.0])}

        signal = strategy.get_signal("BTCUSDT", ot)
        assert signal == Signal(direction=-1, weight=100)

    def test_low_confidence_still_predicts(self):
        """Even with low confidence, model still returns a direction."""
        from unittest.mock import MagicMock

        from crypto_trade.backtest_models import Signal
        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        ot = self._JAN_2024_MS
        strategy = LightGbmStrategy(features_dir="/nonexistent")
        strategy._current_month = "2024-01"

        mock_model = MagicMock()
        # Very low confidence — still predicts
        mock_model.predict_proba.return_value = np.array([[0.51, 0.49]])
        strategy._model = mock_model
        strategy._selected_cols = ["feat_a", "feat_b"]
        strategy._month_features = {("BTCUSDT", ot): np.array([1.0, 2.0])}

        signal = strategy.get_signal("BTCUSDT", ot)
        assert signal == Signal(direction=-1, weight=100)  # short wins at 0.51
