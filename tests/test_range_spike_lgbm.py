"""Tests for the RangeSpikeLightGbmStrategy and its components."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.labeling import label_trades
from crypto_trade.strategies.ml.optimization import (
    build_feature_column_map,
    classes_to_labels,
    compute_sharpe,
    labels_to_classes,
    select_feature_columns,
)
from crypto_trade.strategies.ml.walk_forward import (
    generate_monthly_splits,
    select_training_samples,
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

    return pd.DataFrame({
        "symbol": symbol,
        "open_time": open_times,
        "close_time": close_times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })


def _make_label_master(prices: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    """Build master from explicit (open, high, low, close) tuples at 15m intervals."""
    n = len(prices)
    start_ms = 1_704_067_200_000
    interval_ms = 900_000
    open_times = np.arange(start_ms, start_ms + n * interval_ms, interval_ms)
    close_times = open_times + interval_ms - 1

    return pd.DataFrame({
        "symbol": "BTCUSDT",
        "open_time": open_times,
        "close_time": close_times,
        "open": [p[0] for p in prices],
        "high": [p[1] for p in prices],
        "low": [p[2] for p in prices],
        "close": [p[3] for p in prices],
    })


# ---------------------------------------------------------------------------
# Labeling tests
# ---------------------------------------------------------------------------


class TestLabeling:
    def test_label_long_tp(self):
        """Long TP hits when price goes up, short SL hits first."""
        # Entry at close of candle 0 = 100
        # tp_pct=3 → long TP at 103, long SL at 98
        # short TP at 97, short SL at 103
        prices = [
            (99.0, 101.0, 99.0, 100.0),   # entry candle
            (100.0, 101.0, 99.5, 100.5),   # small move up
            (100.5, 103.5, 100.0, 103.0),  # long TP hit (high=103.5 >= 103)
        ]
        master = _make_label_master(prices)
        labels = label_trades(master, np.array([0]), tp_pct=3.0, sl_pct=2.0, timeout_minutes=60)
        assert labels[0] == 1  # long

    def test_label_short_tp(self):
        """Short TP hits when price drops, long SL hits first."""
        prices = [
            (101.0, 101.0, 99.0, 100.0),   # entry candle, close=100
            (100.0, 100.5, 99.0, 99.5),     # small move down
            (99.5, 100.0, 96.5, 97.0),      # short TP hit (low=96.5 <= 97)
        ]
        master = _make_label_master(prices)
        labels = label_trades(master, np.array([0]), tp_pct=3.0, sl_pct=2.0, timeout_minutes=60)
        assert labels[0] == -1  # short

    def test_label_both_fail_timeout(self):
        """Both directions fail when price stays flat and times out."""
        prices = [
            (100.0, 100.5, 99.5, 100.0),  # entry candle
            (100.0, 100.3, 99.7, 100.1),  # flat
            (100.1, 100.4, 99.8, 100.0),  # flat
        ]
        master = _make_label_master(prices)
        # timeout_minutes=15 means only 1 candle forward (15m interval)
        labels = label_trades(master, np.array([0]), tp_pct=3.0, sl_pct=2.0, timeout_minutes=15)
        assert labels[0] == 0  # skip

    def test_label_empty_candidates(self):
        """Empty candidates returns empty labels."""
        master = _make_label_master([(100.0, 101.0, 99.0, 100.0)])
        labels = label_trades(
            master, np.array([], dtype=np.intp),
            tp_pct=3.0, sl_pct=2.0, timeout_minutes=60,
        )
        assert len(labels) == 0

    def test_label_long_tp_first_when_both_hit(self):
        """When both TP hit, but long hits on an earlier candle, label is 1."""
        prices = [
            (100.0, 100.5, 99.5, 100.0),  # entry, close=100
            (100.0, 103.5, 99.5, 101.0),  # long TP hits, short SL hits
            (101.0, 101.5, 96.5, 97.0),   # short TP hits (96.5 <= 97)
        ]
        master = _make_label_master(prices)
        labels = label_trades(master, np.array([0]), tp_pct=3.0, sl_pct=2.0, timeout_minutes=60)
        assert labels[0] == 1  # long hit first


# ---------------------------------------------------------------------------
# Walk-forward split tests
# ---------------------------------------------------------------------------


class TestMonthSplits:
    def test_basic_splits(self):
        """3 months of data with training_months=2 should yield 1 split."""
        # Jan, Feb, Mar 2024
        master = _make_master(n=100, start_ms=1_704_067_200_000)  # starts Jan 1 2024
        # Add Feb and Mar data
        feb = _make_master(n=100, start_ms=1_706_745_600_000)  # Feb 1 2024
        mar = _make_master(n=100, start_ms=1_709_251_200_000)  # Mar 1 2024
        combined_times = np.concatenate([
            master["open_time"].values, feb["open_time"].values, mar["open_time"].values,
        ])
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

        # 4 months → 2 splits with training_months=2
        jan = _make_master(n=50, start_ms=1_704_067_200_000)
        feb = _make_master(n=50, start_ms=1_706_745_600_000)
        mar = _make_master(n=50, start_ms=1_709_251_200_000)
        apr = _make_master(n=50, start_ms=1_711_929_600_000)
        combined_times = np.concatenate([
            jan["open_time"].values, feb["open_time"].values,
            mar["open_time"].values, apr["open_time"].values,
        ])
        splits = generate_monthly_splits(combined_times, training_months=2)
        assert len(splits) == 2

        # First split: train=Jan+Feb, test=Mar
        s0 = splits[0]
        assert s0.test_month == "2024-03"
        # train_start = Jan 1
        assert datetime.datetime.fromtimestamp(
            s0.train_start_ms / 1000, tz=datetime.UTC
        ).month == 1
        # test_start = Mar 1
        assert datetime.datetime.fromtimestamp(
            s0.test_start_ms / 1000, tz=datetime.UTC
        ).month == 3


# ---------------------------------------------------------------------------
# Sample selection tests
# ---------------------------------------------------------------------------


class TestSampleSelection:
    def test_selects_top_spikes(self):
        """Selected samples should have high range_spike values."""
        n = 1000
        open_times = np.arange(0, n * 900_000, 900_000, dtype=np.int64)
        rng = np.random.default_rng(42)
        range_spike = rng.uniform(0, 10, n)

        indices = select_training_samples(
            open_times, range_spike,
            train_start_ms=0, train_end_ms=n * 900_000,
            n_samples=50,
        )
        assert len(indices) == 50
        # Mean spike of selected should be higher than overall mean
        assert range_spike[indices].mean() > range_spike.mean()

    def test_returns_all_if_less_than_n_samples(self):
        """If window has fewer candles than n_samples, return all."""
        n = 20
        open_times = np.arange(0, n * 900_000, 900_000, dtype=np.int64)
        range_spike = np.ones(n)

        indices = select_training_samples(
            open_times, range_spike,
            train_start_ms=0, train_end_ms=n * 900_000,
            n_samples=100,
        )
        assert len(indices) == n

    def test_empty_window(self):
        """Empty time window returns empty array."""
        open_times = np.array([1_000_000, 2_000_000], dtype=np.int64)
        range_spike = np.array([5.0, 6.0])

        indices = select_training_samples(
            open_times, range_spike,
            train_start_ms=10_000_000, train_end_ms=20_000_000,
            n_samples=10,
        )
        assert len(indices) == 0


# ---------------------------------------------------------------------------
# Sharpe computation tests
# ---------------------------------------------------------------------------


class TestSharpe:
    def test_positive_sharpe(self):
        """Mostly correct predictions → positive Sharpe."""
        y_true = np.array([1, 1, 1, -1, -1, 1, 1, -1, 1, 1])
        y_pred = np.array([1, 1, 1, -1, -1, 1, 1, -1, 1, 1])  # all correct
        sharpe = compute_sharpe(y_true, y_pred, tp_pct=3.0, sl_pct=2.0, fee_pct=0.1)
        assert sharpe > 0

    def test_negative_sharpe(self):
        """Mostly wrong predictions → negative Sharpe."""
        y_true = np.array([1, 1, 1, -1, -1])
        y_pred = np.array([-1, -1, -1, 1, 1])  # all wrong
        sharpe = compute_sharpe(y_true, y_pred, tp_pct=3.0, sl_pct=2.0, fee_pct=0.1)
        assert sharpe < 0

    def test_empty_predictions(self):
        """All skip predictions → penalty Sharpe."""
        y_true = np.array([1, -1, 0])
        y_pred = np.array([0, 0, 0])  # all skip
        sharpe = compute_sharpe(y_true, y_pred, tp_pct=3.0, sl_pct=2.0, fee_pct=0.1)
        assert sharpe == -10.0

    def test_single_trade(self):
        """Single trade → penalty (< 2 trades)."""
        y_true = np.array([1, 0])
        y_pred = np.array([1, 0])
        sharpe = compute_sharpe(y_true, y_pred, tp_pct=3.0, sl_pct=2.0, fee_pct=0.1)
        assert sharpe == -10.0


# ---------------------------------------------------------------------------
# Feature column map tests
# ---------------------------------------------------------------------------


class TestFeatureColumnMap:
    def test_basic_mapping(self):
        """Columns are mapped to correct groups and periods."""
        cols = [
            "mom_rsi_14", "mom_rsi_21",
            "vol_atr_14", "vol_bb_bandwidth_20",
            "trend_adx_14", "trend_psar_af",
            "vol_obv", "vol_cmf_14",
            "mr_zscore_20",
            "stat_return_5",
        ]
        col_map = build_feature_column_map(cols)

        assert "momentum" in col_map
        assert 14 in col_map["momentum"]
        assert "mom_rsi_14" in col_map["momentum"][14]

        assert "volatility" in col_map
        assert 14 in col_map["volatility"]
        assert "vol_atr_14" in col_map["volatility"][14]

        assert "volume" in col_map
        assert None in col_map["volume"]  # vol_obv has no period
        assert "vol_obv" in col_map["volume"][None]
        assert 14 in col_map["volume"]
        assert "vol_cmf_14" in col_map["volume"][14]

        assert "trend" in col_map
        assert None in col_map["trend"]
        assert "trend_psar_af" in col_map["trend"][None]

    def test_macd_uses_slow_period(self):
        """MACD columns use the slow EMA period."""
        cols = ["mom_macd_line_8_21_5", "mom_macd_hist_12_26_9"]
        col_map = build_feature_column_map(cols)
        assert 21 in col_map["momentum"]
        assert "mom_macd_line_8_21_5" in col_map["momentum"][21]
        assert 26 in col_map["momentum"]
        assert "mom_macd_hist_12_26_9" in col_map["momentum"][26]

    def test_select_by_period_range(self):
        """Period range filtering works correctly."""
        cols = ["mom_rsi_5", "mom_rsi_14", "mom_rsi_30", "vol_obv"]
        col_map = build_feature_column_map(cols)

        selected = select_feature_columns(
            col_map,
            use_groups={"momentum": True, "volume": True, "volatility": False,
                        "trend": False, "mean_reversion": False, "statistical": False},
            min_period=10, max_period=20,
        )
        assert "mom_rsi_14" in selected
        assert "mom_rsi_5" not in selected
        assert "mom_rsi_30" not in selected
        assert "vol_obv" in selected  # no-period always included


# ---------------------------------------------------------------------------
# Label encoding tests
# ---------------------------------------------------------------------------


class TestLabelEncoding:
    def test_roundtrip(self):
        """Labels survive encode → decode roundtrip."""
        labels = np.array([-1, 0, 1, -1, 1, 0])
        classes = labels_to_classes(labels)
        assert list(classes) == [0, 1, 2, 0, 2, 1]
        recovered = classes_to_labels(classes)
        np.testing.assert_array_equal(recovered, labels)


# ---------------------------------------------------------------------------
# Strategy registration tests
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_strategy_registered(self):
        from crypto_trade.strategies import list_strategies
        assert "range_spike_lgbm" in list_strategies()

    def test_get_strategy_string_params(self):
        from crypto_trade.strategies import get_strategy
        # features_dir is a string param that should pass through without int/float conversion
        strategy = get_strategy(
            "range_spike_lgbm",
            {"features_dir": "data/features", "n_trials": "10"},
        )
        assert strategy.features_dir == "data/features"
        assert strategy.n_trials == 10

    def test_spike_threshold_not_accepted(self):
        """spike_threshold was removed; passing it should raise TypeError."""
        import pytest

        from crypto_trade.strategies import get_strategy

        with pytest.raises(TypeError):
            get_strategy("range_spike_lgbm", {"spike_threshold": "5.85"})


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
        from crypto_trade.strategies.ml.range_spike_lgbm import RangeSpikeLightGbmStrategy

        master = self._make_multi_month_master()
        strategy = RangeSpikeLightGbmStrategy(
            training_months=2, features_dir="/nonexistent"
        )
        strategy.compute_features(master)

        # No model trained yet
        assert strategy._model is None
        assert strategy._current_month is None
        # But splits should be generated
        assert len(strategy._splits) > 0
        assert len(strategy._split_map) > 0

    def test_get_signal_triggers_training(self):
        """First get_signal call for a month triggers _train_for_month."""
        from crypto_trade.strategies.ml.range_spike_lgbm import RangeSpikeLightGbmStrategy

        master = self._make_multi_month_master()
        strategy = RangeSpikeLightGbmStrategy(
            training_months=2, features_dir="/nonexistent"
        )
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        # First candle is Jan 2024
        first_ot = int(master["open_time"].iloc[0])
        first_sym = master["symbol"].iloc[0]
        strategy.get_signal(first_sym, first_ot)

        assert len(train_calls) == 1
        assert train_calls[0] == "2024-01"

    def test_same_month_no_retrain(self):
        """Multiple get_signal calls in same month should not retrain."""
        from crypto_trade.strategies.ml.range_spike_lgbm import RangeSpikeLightGbmStrategy

        master = self._make_multi_month_master()
        strategy = RangeSpikeLightGbmStrategy(
            training_months=2, features_dir="/nonexistent"
        )
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        # Call get_signal for first two candles (both in Jan)
        for i in range(2):
            ot = int(master["open_time"].iloc[i])
            sym = master["symbol"].iloc[i]
            strategy.get_signal(sym, ot)

        # Only one train call despite two get_signal calls
        assert len(train_calls) == 1

    def test_month_change_triggers_retrain(self):
        """Crossing a month boundary triggers a new training call."""
        from crypto_trade.strategies.ml.range_spike_lgbm import RangeSpikeLightGbmStrategy

        master = self._make_multi_month_master()
        strategy = RangeSpikeLightGbmStrategy(
            training_months=2, features_dir="/nonexistent"
        )
        strategy.compute_features(master)

        train_calls = []
        original_train = strategy._train_for_month

        def mock_train(month_str):
            train_calls.append(month_str)
            original_train(month_str)

        strategy._train_for_month = mock_train

        # Call for Jan candle, then Feb candle
        jan_ot = int(master["open_time"].iloc[0])
        jan_sym = master["symbol"].iloc[0]
        strategy.get_signal(jan_sym, jan_ot)

        # Find first Feb candle (index 200 since each month has 200 candles)
        feb_ot = int(master["open_time"].iloc[200])
        feb_sym = master["symbol"].iloc[200]
        strategy._pos = 200  # align pos
        strategy.get_signal(feb_sym, feb_ot)

        assert len(train_calls) == 2
        assert train_calls[0] == "2024-01"
        assert train_calls[1] == "2024-02"

    def test_get_signal_returns_no_signal_without_model(self):
        """When no model can be trained, get_signal returns NO_SIGNAL."""
        from crypto_trade.strategies import NO_SIGNAL
        from crypto_trade.strategies.ml.range_spike_lgbm import RangeSpikeLightGbmStrategy

        master = self._make_multi_month_master()
        strategy = RangeSpikeLightGbmStrategy(
            training_months=2, features_dir="/nonexistent"
        )
        strategy.compute_features(master)

        signal = strategy.get_signal("BTCUSDT", int(master["open_time"].iloc[0]))
        assert signal == NO_SIGNAL
