from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.kline_array import KlineArray
from crypto_trade.strategies.filters.range_spike_filter import RangeSpikeFilter
from crypto_trade.strategies.filters.volume_filter import VolumeFilter


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
        else open_time + 899999
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
        self._n = len(master)

    def skip(self) -> None:
        self._pos += 1

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


# ---------------------------------------------------------------------------
# RangeSpikeFilter
# ---------------------------------------------------------------------------


class TestRangeSpikeFilter:
    def test_insufficient_history_returns_no_signal(self) -> None:
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=5)
        master = _make_master(open=[100.0] * 4, high=[101.0] * 4, low=[99.0] * 4)
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_normal_candles_blocked(self) -> None:
        """Uniform candles => range_spike=1.0 < threshold => blocked."""
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=2.0)
        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
            close=[100.0] * 10,
        )
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_spike_candle_passes(self) -> None:
        """One huge candle at the end, preceded by tiny candles => passes."""
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        master = _make_master(open=opens, high=highs, low=lows, close=closes)
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=2.0)
        result = _get_last_signal(f, master)
        assert result.direction == 1
        assert result.weight == 100

    def test_no_inner_returns_no_signal(self) -> None:
        """Filter with no inner strategy returns NO_SIGNAL even if spike passes."""
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        master = _make_master(open=opens, high=highs, low=lows, close=closes)
        f = RangeSpikeFilter(inner=None, window=10, threshold=2.0)
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_default_params(self) -> None:
        f = RangeSpikeFilter()
        assert f.window == 16
        assert f.threshold == 5.85


# ---------------------------------------------------------------------------
# VolumeFilter
# ---------------------------------------------------------------------------


class TestVolumeFilter:
    def test_insufficient_history_returns_no_signal(self) -> None:
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5)
        master = _make_master(volume=[1000.0] * 4)
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_normal_volume_blocked(self) -> None:
        """Same volume throughout => current <= multiplier*avg => blocked."""
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5, multiplier=1.5)
        master = _make_master(volume=[1000.0] * 5)
        result = _get_last_signal(f, master)
        assert result.direction == 0

    def test_high_volume_passes(self) -> None:
        """Last candle volume >> average => passes."""
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5, multiplier=1.5)
        master = _make_master(volume=[100.0] * 4 + [500.0])
        result = _get_last_signal(f, master)
        assert result.direction == 1

    def test_no_inner_returns_no_signal(self) -> None:
        f = VolumeFilter(inner=None, lookback=5, multiplier=1.5)
        master = _make_master(volume=[100.0] * 4 + [500.0])
        result = _get_last_signal(f, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# Stacking
# ---------------------------------------------------------------------------


class TestFilterStacking:
    def test_volume_wraps_range_spike(self) -> None:
        """VolumeFilter(RangeSpikeFilter(AlwaysBuy)): both must pass."""
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        volumes = [100.0] * 9 + [500.0]
        master = _make_master(open=opens, high=highs, low=lows, close=closes, volume=volumes)

        inner = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=2.0)
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=1.5)
        result = _get_last_signal(stacked, master)
        assert result.direction == 1

    def test_volume_blocks_even_with_spike(self) -> None:
        """Range spike passes but volume is normal => blocked."""
        opens = [100.0] * 10
        highs = [100.01] * 9 + [120.0]
        lows = [99.99] * 9 + [80.0]
        closes = [100.0] * 10
        volumes = [100.0] * 10  # no volume spike
        master = _make_master(open=opens, high=highs, low=lows, close=closes, volume=volumes)

        inner = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=2.0)
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=1.5)
        result = _get_last_signal(stacked, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# Skip
# ---------------------------------------------------------------------------


class TestSkip:
    def test_skip_increments_pos_on_filter_and_inner(self) -> None:
        """skip() advances _pos on both the filter and the inner strategy."""
        leaf = AlwaysBuy()
        f = RangeSpikeFilter(inner=leaf, window=10, threshold=2.0)
        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
        )
        f.compute_features(master)
        assert f._pos == 0
        assert leaf._pos == 0

        f.skip()
        assert f._pos == 1
        assert leaf._pos == 1

        f.skip()
        assert f._pos == 2
        assert leaf._pos == 2

    def test_nested_skip_propagates(self) -> None:
        """skip() propagates through nested filters to the leaf."""
        leaf = AlwaysBuy()
        inner_filter = RangeSpikeFilter(inner=leaf, window=10, threshold=2.0)
        outer_filter = VolumeFilter(inner=inner_filter, lookback=5, multiplier=1.5)

        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
            volume=[1000.0] * 10,
        )
        outer_filter.compute_features(master)

        outer_filter.skip()
        assert outer_filter._pos == 1
        assert inner_filter._pos == 1
        assert leaf._pos == 1

    def test_blocked_candles_call_skip_not_get_signal(self) -> None:
        """When filter blocks, inner _pos advances via skip() without side effects."""
        leaf = AlwaysBuy()
        # All uniform candles → range_spike=1.0 < threshold=2.0 → all blocked
        f = RangeSpikeFilter(inner=leaf, window=10, threshold=2.0)
        master = _make_master(
            open=[100.0] * 10,
            high=[102.0] * 10,
            low=[98.0] * 10,
        )
        f.compute_features(master)

        # Walk through all candles — all should be blocked
        syms = master["symbol"].values
        ots = master["open_time"].values
        for i in range(len(master)):
            sig = f.get_signal(str(syms[i]), int(ots[i]))
            assert sig.direction == 0

        # Both filter and leaf _pos should have advanced to len(master)
        assert f._pos == len(master)
        assert leaf._pos == len(master)
