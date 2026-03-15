from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.kline_array import KlineArray
from crypto_trade.strategies.filters.adaptive_range_spike_filter import (
    AdaptiveRangeSpikeFilter,
    count_signals_per_month,
    find_best_threshold,
)
from crypto_trade.strategies.filters.volume_filter import VolumeFilter

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_kline_array(**kwargs: list[float]) -> KlineArray:
    """Build a KlineArray from keyword lists."""
    n = 0
    for v in kwargs.values():
        n = len(v)
        break
    if n == 0:
        n = 1

    def _arr(key: str, default: float | int = 0, dtype=np.float64) -> np.ndarray:
        if key in kwargs:
            return np.array(kwargs[key], dtype=dtype)
        return np.full(n, default, dtype=dtype)

    open_time = _arr("open_time", 0, np.int64)
    close_time = (
        np.array(kwargs["close_time"], dtype=np.int64)
        if "close_time" in kwargs
        else open_time + 299999
    )

    return KlineArray.from_arrays(
        open_time=open_time,
        open=_arr("open", 100.0),
        high=_arr("high", 101.0),
        low=_arr("low", 99.0),
        close=_arr("close", 100.0),
        volume=_arr("volume", 1000.0),
        close_time=close_time,
        quote_volume=np.full(n, 100000.0),
        trades=np.full(n, 50, dtype=np.int64),
        taker_buy_volume=np.full(n, 500.0),
        taker_buy_quote_volume=np.full(n, 50000.0),
    )


def _make_master(symbol: str = "TEST", **kwargs) -> pd.DataFrame:
    """Build a master DF from keyword lists."""
    ka = _make_kline_array(**kwargs)
    df = ka.df.reset_index(drop=True)
    df["symbol"] = symbol
    return df


class AlwaysBuy:
    def compute_features(self, master: pd.DataFrame) -> None:
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        self._pos += 1
        return Signal(direction=1, weight=100)


def _get_last_signal(strategy, master: pd.DataFrame) -> Signal:
    """Compute features and return the last signal."""
    strategy.compute_features(master)
    syms = master["symbol"].values
    ots = master["open_time"].values
    signal = Signal(direction=0, weight=0)
    for i in range(len(master)):
        signal = strategy.get_signal(str(syms[i]), int(ots[i]))
    return signal


def _generate_kline_array(
    n: int,
    base_range: float = 0.02,
    spike_indices: list[int] | None = None,
    spike_range: float = 0.40,
    base_open: float = 100.0,
    interval_ms: int = 300_000,
    start_time: int = 0,
) -> KlineArray:
    """Generate a KlineArray with controllable range."""
    spike_set = set(spike_indices or [])
    opens = np.full(n, base_open)
    highs = np.empty(n, dtype=np.float64)
    lows = np.empty(n, dtype=np.float64)
    closes = np.full(n, base_open)
    volumes = np.full(n, 1000.0)
    open_times = np.arange(start_time, start_time + n * interval_ms, interval_ms, dtype=np.int64)
    close_times = open_times + interval_ms - 1

    for i in range(n):
        r = spike_range if i in spike_set else base_range
        highs[i] = base_open * (1 + r / 2)
        lows[i] = base_open * (1 - r / 2)

    return KlineArray.from_arrays(
        open_time=open_times,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes,
        close_time=close_times,
        quote_volume=np.full(n, 100000.0),
        trades=np.full(n, 50, dtype=np.int64),
        taker_buy_volume=np.full(n, 500.0),
        taker_buy_quote_volume=np.full(n, 50000.0),
    )


def _generate_master(symbol: str = "SYM1", **kwargs) -> pd.DataFrame:
    """Generate a master DF using _generate_kline_array."""
    ka = _generate_kline_array(**kwargs)
    df = ka.df.reset_index(drop=True)
    df["symbol"] = symbol
    return df


# ---------------------------------------------------------------------------
# TestCountSignalsPerMonth
# ---------------------------------------------------------------------------


class TestCountSignalsPerMonth:
    def test_known_count(self) -> None:
        """Signals spread across 2 months → average per month."""
        # 2 months of data: Jan 2024 and Feb 2024
        # 50 signals in each month = 50 avg
        jan_start = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
        feb_start = int(pd.Timestamp("2024-02-01", tz="UTC").timestamp() * 1000)
        interval_ms = 300_000  # 5 min

        n_jan = 8640  # ~30 days of 5m candles
        n_feb = 8064  # ~28 days of 5m candles

        times_jan = np.arange(jan_start, jan_start + n_jan * interval_ms, interval_ms)
        times_feb = np.arange(feb_start, feb_start + n_feb * interval_ms, interval_ms)
        open_times = np.concatenate([times_jan, times_feb])

        # Low spikes everywhere, high spikes at specific positions
        spikes = np.full(len(open_times), 1.0)
        spikes[100:150] = 6.0  # 50 signals in Jan
        spikes[n_jan + 100 : n_jan + 150] = 6.0  # 50 signals in Feb

        result = count_signals_per_month(spikes, open_times, threshold=5.0)
        assert result == 50.0

    def test_empty_arrays(self) -> None:
        spikes = np.array([], dtype=float)
        open_times = np.array([], dtype=np.int64)
        result = count_signals_per_month(spikes, open_times, threshold=5.0)
        assert result == 0.0

    def test_no_signals_above_threshold(self) -> None:
        jan_start = int(pd.Timestamp("2024-01-15", tz="UTC").timestamp() * 1000)
        open_times = np.arange(jan_start, jan_start + 100 * 300_000, 300_000)
        spikes = np.full(100, 1.0)
        result = count_signals_per_month(spikes, open_times, threshold=5.0)
        assert result == 0.0

    def test_single_month(self) -> None:
        """All data in one month."""
        jan_start = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
        open_times = np.arange(jan_start, jan_start + 1000 * 300_000, 300_000)
        spikes = np.full(1000, 1.0)
        spikes[0:20] = 6.0  # 20 signals
        result = count_signals_per_month(spikes, open_times, threshold=5.0)
        assert result == 20.0


# ---------------------------------------------------------------------------
# TestFindBestThreshold
# ---------------------------------------------------------------------------


class TestFindBestThreshold:
    def test_finds_threshold_near_target(self) -> None:
        rng = np.random.default_rng(42)
        n = 8640 * 3  # ~3 months of 5m data
        jan_start = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
        open_times = np.arange(jan_start, jan_start + n * 300_000, 300_000, dtype=np.int64)
        spikes = rng.uniform(0, 10, size=n)
        target = 200.0

        threshold = find_best_threshold(
            spikes,
            open_times,
            target_signals_month=target,
            threshold_lo=0.0,
            threshold_hi=10.0,
        )

        actual = count_signals_per_month(spikes, open_times, threshold)
        assert abs(actual - target) < 10  # binary search is very precise

    def test_respects_bounds(self) -> None:
        jan_start = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)
        open_times = np.arange(jan_start, jan_start + 100 * 300_000, 300_000, dtype=np.int64)
        spikes = np.full(100, 5.0)

        threshold = find_best_threshold(
            spikes,
            open_times,
            target_signals_month=50,
            threshold_lo=3.0,
            threshold_hi=8.0,
        )
        assert 3.0 <= threshold <= 8.0


# ---------------------------------------------------------------------------
# TestAdaptiveBasic
# ---------------------------------------------------------------------------


class TestAdaptiveBasic:
    def test_default_params(self) -> None:
        f = AdaptiveRangeSpikeFilter()
        assert f.window == 48
        assert f.threshold == 5.85
        assert f.target_signals_month == 400
        assert f.recalibrate_days == 30
        assert f.min_history_days == 30

    def test_insufficient_history_returns_no_signal(self) -> None:
        f = AdaptiveRangeSpikeFilter(inner=AlwaysBuy(), window=5)
        master = _make_master(open=[100.0] * 4)
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_initial_threshold_used_before_calibration(self) -> None:
        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=5,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
            close=[100.0] * 10,
        )
        result = _get_last_signal(f, master)
        assert result.direction == 0
        assert f.threshold == 2.0

    def test_spike_passes_with_initial_threshold(self) -> None:
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        master = _make_master(open=opens, high=highs, low=lows, close=[100.0] * 10)
        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        result = _get_last_signal(f, master)
        assert result.direction == 1
        assert result.weight == 100

    def test_no_inner_returns_no_signal(self) -> None:
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        master = _make_master(open=opens, high=highs, low=lows, close=[100.0] * 10)
        f = AdaptiveRangeSpikeFilter(
            inner=None,
            window=10,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_normal_candles_blocked(self) -> None:
        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
            close=[100.0] * 10,
        )
        result = _get_last_signal(f, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# TestRecalibration
# ---------------------------------------------------------------------------


class TestRecalibration:
    def test_calibration_triggers_after_min_history(self) -> None:
        n = 350
        master = _generate_master(
            n=n,
            base_range=0.02,
            spike_indices=list(range(300, 350)),
            spike_range=0.40,
        )

        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            min_history_days=1,
            recalibrate_days=0,
            initial_threshold=5.85,
        )

        _get_last_signal(f, master)
        assert len(f._calibration_log) > 0

    def test_threshold_changes_after_calibration(self) -> None:
        n = 400
        spike_indices = list(range(50, 400, 3))
        master = _generate_master(
            n=n,
            base_range=0.02,
            spike_indices=spike_indices,
            spike_range=0.40,
        )

        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            min_history_days=1,
            recalibrate_days=0,
            target_signals_month=50,
            initial_threshold=5.85,
        )

        _get_last_signal(f, master)
        assert len(f._calibration_log) > 0
        last = f._calibration_log[-1]
        assert isinstance(last.threshold, float)
        assert last.signals_per_month > 0

    def test_recalibration_interval_respected(self) -> None:
        n = 600
        master = _generate_master(n=n, base_range=0.02)

        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            min_history_days=1,
            recalibrate_days=2,
        )

        _get_last_signal(f, master)
        # 600 candles * 5min = 3000min = ~2.08 days. With 2-day interval:
        # first trigger at min_history, then at most 1 more.
        assert len(f._calibration_log) <= 2

    def test_multi_symbol_calibration(self) -> None:
        n = 350
        ka1 = _generate_kline_array(
            n,
            base_range=0.02,
            spike_indices=[300],
            spike_range=0.40,
        )
        ka2 = _generate_kline_array(
            n,
            base_range=0.03,
            spike_indices=[310],
            spike_range=0.50,
            base_open=200.0,
        )

        df1 = ka1.df.copy()
        df1["symbol"] = "SYM1"
        df2 = ka2.df.copy()
        df2["symbol"] = "SYM2"
        master = pd.concat([df1, df2], ignore_index=True)
        master = master.sort_values(["open_time", "symbol"], kind="mergesort", ignore_index=True)

        f = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            min_history_days=1,
            recalibrate_days=0,
        )

        _get_last_signal(f, master)
        assert len(f._calibration_log) > 0


# ---------------------------------------------------------------------------
# TestStacking
# ---------------------------------------------------------------------------


class TestStacking:
    def test_volume_wraps_adaptive_range_spike(self) -> None:
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        volumes = [100.0] * 9 + [500.0]
        master = _make_master(open=opens, high=highs, low=lows, close=closes, volume=volumes)

        inner = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=1.5)
        result = _get_last_signal(stacked, master)
        assert result.direction == 1

    def test_volume_blocks_even_with_adaptive_spike(self) -> None:
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        volumes = [100.0] * 10
        master = _make_master(open=opens, high=highs, low=lows, close=closes, volume=volumes)

        inner = AdaptiveRangeSpikeFilter(
            inner=AlwaysBuy(),
            window=10,
            initial_threshold=2.0,
            min_history_days=9999,
        )
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=1.5)
        result = _get_last_signal(stacked, master)
        assert result.direction == 0
