from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class ConsecutiveReversalStrategy:
    """N+ same-direction candles -> trade reversal."""

    def __init__(self, n_consecutive: int = 4) -> None:
        self.n_consecutive = n_consecutive

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < self.n_consecutive:
            return NO_SIGNAL

        recent = history[-self.n_consecutive :]
        bullish = 0
        bearish = 0
        for k in recent:
            o, c = Decimal(k.open), Decimal(k.close)
            if c > o:
                bullish += 1
            elif c < o:
                bearish += 1

        if bullish == self.n_consecutive:
            # N consecutive bullish -> expect reversal (short)
            return Signal(direction=-1, weight=60)
        if bearish == self.n_consecutive:
            # N consecutive bearish -> expect reversal (long)
            return Signal(direction=1, weight=60)
        return NO_SIGNAL
