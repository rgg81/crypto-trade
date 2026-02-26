from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies.filters.range_spike_filter import RangeSpikeFilter
from crypto_trade.strategies.filters.volume_filter import VolumeFilter


def _kline(
    open: str = "100",
    high: str = "101",
    low: str = "99",
    close: str = "100",
    volume: str = "1000",
    open_time: int = 0,
) -> Kline:
    return Kline(
        open_time=open_time,
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
        close_time=open_time + 299999,
        quote_volume="100000",
        trades=50,
        taker_buy_volume="500",
        taker_buy_quote_volume="50000",
    )


class AlwaysBuy:
    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        return Signal(direction=1, weight=100)


# ---------------------------------------------------------------------------
# RangeSpikeFilter
# ---------------------------------------------------------------------------


class TestRangeSpikeFilter:
    def test_insufficient_history_returns_no_signal(self) -> None:
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=5)
        history = [_kline()] * 4
        result = f.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_normal_candles_blocked(self) -> None:
        """Uniform candles => range_spike=1.0 < threshold => blocked."""
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=Decimal("2.0"))
        history = [_kline(open="100", high="102", low="98", close="100")] * 10
        result = f.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_spike_candle_passes(self) -> None:
        """One huge candle at the end, preceded by tiny candles => passes."""
        tiny = _kline(open="100", high="100.01", low="99.99", close="100")
        huge = _kline(open="100", high="120", low="80", close="100")
        history = [tiny] * 9 + [huge]
        f = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=Decimal("2.0"))
        result = f.on_kline("TEST", huge, history)
        assert result.direction == 1
        assert result.weight == 100

    def test_no_inner_returns_no_signal(self) -> None:
        """Filter with no inner strategy returns NO_SIGNAL even if spike passes."""
        tiny = _kline(open="100", high="100.01", low="99.99", close="100")
        huge = _kline(open="100", high="120", low="80", close="100")
        history = [tiny] * 9 + [huge]
        f = RangeSpikeFilter(inner=None, window=10, threshold=Decimal("2.0"))
        result = f.on_kline("TEST", huge, history)
        assert result.direction == 0

    def test_default_params(self) -> None:
        f = RangeSpikeFilter()
        assert f.window == 48
        assert f.threshold == Decimal("5.85")


# ---------------------------------------------------------------------------
# VolumeFilter
# ---------------------------------------------------------------------------


class TestVolumeFilter:
    def test_insufficient_history_returns_no_signal(self) -> None:
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5)
        history = [_kline()] * 4
        result = f.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_normal_volume_blocked(self) -> None:
        """Same volume throughout => current <= multiplier*avg => blocked."""
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5, multiplier=Decimal("1.5"))
        history = [_kline(volume="1000")] * 5
        result = f.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_high_volume_passes(self) -> None:
        """Last candle volume >> average => passes."""
        normal = _kline(volume="100")
        spike = _kline(volume="500")
        history = [normal] * 4 + [spike]
        f = VolumeFilter(inner=AlwaysBuy(), lookback=5, multiplier=Decimal("1.5"))
        result = f.on_kline("TEST", spike, history)
        assert result.direction == 1

    def test_no_inner_returns_no_signal(self) -> None:
        normal = _kline(volume="100")
        spike = _kline(volume="500")
        history = [normal] * 4 + [spike]
        f = VolumeFilter(inner=None, lookback=5, multiplier=Decimal("1.5"))
        result = f.on_kline("TEST", spike, history)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# Stacking
# ---------------------------------------------------------------------------


class TestFilterStacking:
    def test_volume_wraps_range_spike(self) -> None:
        """VolumeFilter(RangeSpikeFilter(AlwaysBuy)): both must pass."""
        tiny = _kline(open="100", high="100.01", low="99.99", close="100", volume="100")
        huge = _kline(open="100", high="120", low="80", close="100", volume="500")
        history = [tiny] * 9 + [huge]

        inner = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=Decimal("2.0"))
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=Decimal("1.5"))
        result = stacked.on_kline("TEST", huge, history)
        assert result.direction == 1

    def test_volume_blocks_even_with_spike(self) -> None:
        """Range spike passes but volume is normal => blocked."""
        tiny = _kline(open="100", high="100.01", low="99.99", close="100", volume="100")
        spike_no_vol = _kline(open="100", high="120", low="80", close="100", volume="100")
        history = [tiny] * 9 + [spike_no_vol]

        inner = RangeSpikeFilter(inner=AlwaysBuy(), window=10, threshold=Decimal("2.0"))
        stacked = VolumeFilter(inner=inner, lookback=10, multiplier=Decimal("1.5"))
        result = stacked.on_kline("TEST", spike_no_vol, history)
        assert result.direction == 0
