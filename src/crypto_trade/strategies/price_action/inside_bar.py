from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class InsideBarStrategy:
    """Inside bar breakout: current range inside previous range -> trade breakout direction."""

    def __init__(self, weight: int = 70) -> None:
        self.weight = weight

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < 2:
            return NO_SIGNAL

        prev = history[-2]
        curr = history[-1]

        prev_high = Decimal(prev.high)
        prev_low = Decimal(prev.low)
        curr_high = Decimal(curr.high)
        curr_low = Decimal(curr.low)
        curr_close = Decimal(curr.close)

        # Check if current bar is inside previous bar
        if curr_high > prev_high or curr_low < prev_low:
            return NO_SIGNAL

        # Inside bar detected — trade breakout direction based on close
        mid = (prev_high + prev_low) / 2
        if curr_close > mid:
            return Signal(direction=1, weight=self.weight)
        elif curr_close < mid:
            return Signal(direction=-1, weight=self.weight)
        return NO_SIGNAL
