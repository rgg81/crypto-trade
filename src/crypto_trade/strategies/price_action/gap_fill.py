from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class GapFillStrategy:
    """Gap / imbalance fill: gap between candles -> trade the fill direction."""

    def __init__(self, weight: int = 60) -> None:
        self.weight = weight

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < 2:
            return NO_SIGNAL

        prev = history[-2]
        curr = history[-1]

        prev_close = Decimal(prev.close)
        curr_open = Decimal(curr.open)

        # Gap up: current open > previous close -> expect fill down (short)
        if curr_open > prev_close:
            gap = curr_open - prev_close
            if prev_close != 0 and gap / prev_close > Decimal("0.001"):
                return Signal(direction=-1, weight=self.weight)

        # Gap down: current open < previous close -> expect fill up (long)
        if curr_open < prev_close:
            gap = prev_close - curr_open
            if prev_close != 0 and gap / prev_close > Decimal("0.001"):
                return Signal(direction=1, weight=self.weight)

        return NO_SIGNAL
