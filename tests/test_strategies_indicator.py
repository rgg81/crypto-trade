from __future__ import annotations

from decimal import Decimal

from crypto_trade.models import Kline
from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy
from crypto_trade.strategies.indicator.rsi_bb import RsiBbStrategy


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


# ---------------------------------------------------------------------------
# RsiBbStrategy
# ---------------------------------------------------------------------------


class TestRsiBbStrategy:
    def test_oversold_triggers_long(self) -> None:
        s = RsiBbStrategy(rsi_period=5, bb_period=10)
        # Flat period (BB tightens), then small drops, then huge crash
        klines: list[Kline] = []
        for i in range(15):
            klines.append(
                _kline(close="100", open="100", high="101", low="99", open_time=i * 300000)
            )
        # Small declines
        for i, c in enumerate(["98", "96"]):
            klines.append(
                _kline(close=c, open="100", high="100", low=c, open_time=(15 + i) * 300000)
            )
        # Huge crash
        klines.append(_kline(close="70", open="96", high="96", low="70", open_time=17 * 300000))
        result = s.on_kline("TEST", klines[-1], klines)
        assert result.direction == 1

    def test_overbought_triggers_short(self) -> None:
        s = RsiBbStrategy(rsi_period=5, bb_period=10)
        # Flat period, then small rises, then huge pump
        klines: list[Kline] = []
        for i in range(15):
            klines.append(
                _kline(close="100", open="100", high="101", low="99", open_time=i * 300000)
            )
        for i, c in enumerate(["102", "104"]):
            klines.append(
                _kline(close=c, open="100", high=c, low="100", open_time=(15 + i) * 300000)
            )
        klines.append(_kline(close="130", open="104", high="130", low="104", open_time=17 * 300000))
        result = s.on_kline("TEST", klines[-1], klines)
        assert result.direction == -1

    def test_neutral_no_signal(self) -> None:
        s = RsiBbStrategy(rsi_period=14, bb_period=20)
        # Flat prices -> RSI ~50, close near middle BB
        history = [_kline(close="100", open_time=i * 300000) for i in range(25)]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = RsiBbStrategy(rsi_period=14, bb_period=20)
        history = [_kline()] * 10
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# BbSqueezeStrategy
# ---------------------------------------------------------------------------


class TestBbSqueezeStrategy:
    def test_insufficient_history(self) -> None:
        s = BbSqueezeStrategy(bb_period=20, squeeze_lookback=10)
        history = [_kline()] * 10
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_no_squeeze_no_signal(self) -> None:
        """No squeeze (volatile prices throughout) -> no signal."""
        s = BbSqueezeStrategy(bb_period=5, squeeze_lookback=3, squeeze_threshold=Decimal("0.02"))
        # Volatile prices throughout
        klines: list[Kline] = []
        for i in range(15):
            p = 100 + (i % 2) * 10
            klines.append(
                _kline(
                    open=str(p),
                    high=str(p + 5),
                    low=str(p - 5),
                    close=str(p),
                    volume="1000",
                    open_time=i * 300000,
                )
            )
        result = s.on_kline("TEST", klines[-1], klines)
        assert result.direction == 0

    def test_squeeze_then_expansion_bullish(self) -> None:
        """Tight BB then sudden expansion up with volume -> long."""
        s = BbSqueezeStrategy(
            bb_period=5,
            squeeze_lookback=3,
            squeeze_threshold=Decimal("0.05"),
            vol_multiplier=Decimal("1.5"),
        )
        # Tight range for initial candles
        klines: list[Kline] = []
        for i in range(10):
            klines.append(
                _kline(
                    open="100.00",
                    high="100.01",
                    low="99.99",
                    close="100.00",
                    volume="100",
                    open_time=i * 300000,
                )
            )
        # Breakout candle: big move up with high volume
        klines.append(
            _kline(
                open="100",
                high="115",
                low="99",
                close="112",
                volume="5000",
                open_time=10 * 300000,
            )
        )
        result = s.on_kline("TEST", klines[-1], klines)
        # Should be long (close > middle)
        assert result.direction == 1

    def test_squeeze_then_expansion_bearish(self) -> None:
        """Tight BB then sudden expansion down with volume -> short."""
        s = BbSqueezeStrategy(
            bb_period=5,
            squeeze_lookback=3,
            squeeze_threshold=Decimal("0.05"),
            vol_multiplier=Decimal("1.5"),
        )
        klines: list[Kline] = []
        for i in range(10):
            klines.append(
                _kline(
                    open="100.00",
                    high="100.01",
                    low="99.99",
                    close="100.00",
                    volume="100",
                    open_time=i * 300000,
                )
            )
        # Breakout candle: big move down with high volume
        klines.append(
            _kline(
                open="100",
                high="101",
                low="85",
                close="88",
                volume="5000",
                open_time=10 * 300000,
            )
        )
        result = s.on_kline("TEST", klines[-1], klines)
        assert result.direction == -1
