from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class WickRejectionStrategy:
    """Wick > K * body -> trade rejection direction."""

    def __init__(self, wick_body_ratio: Decimal = Decimal("2.0")) -> None:
        self.wick_body_ratio = wick_body_ratio

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        o = Decimal(kline.open)
        c = Decimal(kline.close)
        h = Decimal(kline.high)
        lo = Decimal(kline.low)

        body = abs(c - o)
        if body == 0:
            return NO_SIGNAL

        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - lo

        # Long lower wick -> bullish rejection (price rejected lows)
        if lower_wick > self.wick_body_ratio * body and lower_wick > upper_wick:
            return Signal(direction=1, weight=65)

        # Long upper wick -> bearish rejection (price rejected highs)
        if upper_wick > self.wick_body_ratio * body and upper_wick > lower_wick:
            return Signal(direction=-1, weight=65)

        return NO_SIGNAL
