from __future__ import annotations

from decimal import Decimal

from crypto_trade.models import Kline
from crypto_trade.strategies.price_action.consecutive_reversal import (
    ConsecutiveReversalStrategy,
)
from crypto_trade.strategies.price_action.gap_fill import GapFillStrategy
from crypto_trade.strategies.price_action.inside_bar import InsideBarStrategy
from crypto_trade.strategies.price_action.mean_reversion import MeanReversionStrategy
from crypto_trade.strategies.price_action.momentum import MomentumStrategy
from crypto_trade.strategies.price_action.wick_rejection import WickRejectionStrategy


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
# MomentumStrategy
# ---------------------------------------------------------------------------


class TestMomentumStrategy:
    def test_bullish_momentum(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=Decimal("0.1"))
        history = [
            _kline(open="100", high="103", low="99", close="102"),
            _kline(open="102", high="105", low="101", close="104"),
            _kline(open="104", high="107", low="103", close="106"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 1

    def test_bearish_momentum(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=Decimal("0.1"))
        history = [
            _kline(open="106", high="107", low="103", close="104"),
            _kline(open="104", high="105", low="101", close="102"),
            _kline(open="102", high="103", low="99", close="100"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == -1

    def test_mixed_direction_no_signal(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=Decimal("0.1"))
        history = [
            _kline(open="100", high="103", low="99", close="102"),
            _kline(open="102", high="103", low="99", close="100"),  # bearish
            _kline(open="100", high="103", low="99", close="102"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_small_body_no_signal(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=Decimal("0.1"))
        history = [
            _kline(open="100", high="101", low="99", close="100.05"),  # body < 0.1%
            _kline(open="100.05", high="101", low="99", close="100.1"),
            _kline(open="100.1", high="101", low="99", close="100.15"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = MomentumStrategy(n_candles=3)
        history = [_kline(open="100", close="102")]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# MeanReversionStrategy
# ---------------------------------------------------------------------------


class TestMeanReversionStrategy:
    def test_big_bullish_candle_triggers_short(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=Decimal("2.0"))
        # Small candles then a big bullish one
        small = [_kline(open="100", close="101")] * 4
        big = _kline(open="100", high="115", low="99", close="110")
        history = small + [big]
        result = s.on_kline("TEST", big, history)
        assert result.direction == -1

    def test_big_bearish_candle_triggers_long(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=Decimal("2.0"))
        small = [_kline(open="100", close="99")] * 4
        big = _kline(open="110", high="111", low="95", close="100")
        history = small + [big]
        result = s.on_kline("TEST", big, history)
        assert result.direction == 1

    def test_normal_candle_no_signal(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=Decimal("2.0"))
        history = [_kline(open="100", close="101")] * 5
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = MeanReversionStrategy(lookback=20)
        history = [_kline()] * 5
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# WickRejectionStrategy
# ---------------------------------------------------------------------------


class TestWickRejectionStrategy:
    def test_lower_wick_rejection_bullish(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=Decimal("2.0"))
        # Small bullish body, long lower wick
        k = _kline(open="100", high="101", low="94", close="101")
        result = s.on_kline("TEST", k, [k])
        assert result.direction == 1

    def test_upper_wick_rejection_bearish(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=Decimal("2.0"))
        # Small bearish body, long upper wick
        k = _kline(open="101", high="108", low="100", close="100")
        result = s.on_kline("TEST", k, [k])
        assert result.direction == -1

    def test_no_wick_no_signal(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=Decimal("2.0"))
        k = _kline(open="100", high="105", low="100", close="105")  # no wicks
        result = s.on_kline("TEST", k, [k])
        assert result.direction == 0

    def test_doji_no_signal(self) -> None:
        s = WickRejectionStrategy()
        k = _kline(open="100", high="101", low="99", close="100")  # body=0
        result = s.on_kline("TEST", k, [k])
        assert result.direction == 0


# ---------------------------------------------------------------------------
# InsideBarStrategy
# ---------------------------------------------------------------------------


class TestInsideBarStrategy:
    def test_inside_bar_bullish(self) -> None:
        s = InsideBarStrategy()
        prev = _kline(open="95", high="110", low="90", close="105")
        curr = _kline(open="98", high="105", low="95", close="103")  # close > mid(100)
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == 1

    def test_inside_bar_bearish(self) -> None:
        s = InsideBarStrategy()
        prev = _kline(open="95", high="110", low="90", close="105")
        curr = _kline(open="102", high="105", low="95", close="97")  # close < mid(100)
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == -1

    def test_not_inside_bar_no_signal(self) -> None:
        s = InsideBarStrategy()
        prev = _kline(open="100", high="105", low="95", close="102")
        curr = _kline(open="103", high="108", low="96", close="106")  # high exceeds
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = InsideBarStrategy()
        result = s.on_kline("TEST", _kline(), [_kline()])
        assert result.direction == 0


# ---------------------------------------------------------------------------
# GapFillStrategy
# ---------------------------------------------------------------------------


class TestGapFillStrategy:
    def test_gap_up_triggers_short(self) -> None:
        s = GapFillStrategy()
        prev = _kline(open="100", close="100")
        curr = _kline(open="102", close="101")  # gap up
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == -1

    def test_gap_down_triggers_long(self) -> None:
        s = GapFillStrategy()
        prev = _kline(open="100", close="100")
        curr = _kline(open="98", close="99")  # gap down
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == 1

    def test_no_gap_no_signal(self) -> None:
        s = GapFillStrategy()
        prev = _kline(open="100", close="100")
        curr = _kline(open="100", close="101")  # no gap
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == 0

    def test_tiny_gap_ignored(self) -> None:
        s = GapFillStrategy()
        prev = _kline(open="100", close="100")
        curr = _kline(open="100.05", close="100.1")  # gap < 0.1%
        result = s.on_kline("TEST", curr, [prev, curr])
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = GapFillStrategy()
        result = s.on_kline("TEST", _kline(), [_kline()])
        assert result.direction == 0


# ---------------------------------------------------------------------------
# ConsecutiveReversalStrategy
# ---------------------------------------------------------------------------


class TestConsecutiveReversalStrategy:
    def test_bullish_streak_triggers_short_reversal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        history = [
            _kline(open="100", close="102"),
            _kline(open="102", close="104"),
            _kline(open="104", close="106"),
            _kline(open="106", close="108"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == -1

    def test_bearish_streak_triggers_long_reversal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        history = [
            _kline(open="108", close="106"),
            _kline(open="106", close="104"),
            _kline(open="104", close="102"),
            _kline(open="102", close="100"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 1

    def test_mixed_no_signal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        history = [
            _kline(open="100", close="102"),
            _kline(open="102", close="100"),
            _kline(open="100", close="102"),
            _kline(open="102", close="104"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        history = [_kline(open="100", close="102")] * 3
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == 0

    def test_custom_n(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=2)
        history = [
            _kline(open="100", close="102"),
            _kline(open="102", close="104"),
        ]
        result = s.on_kline("TEST", history[-1], history)
        assert result.direction == -1
