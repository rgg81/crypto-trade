from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal, Strategy
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class RangeSpikeFilter:
    """Pass-through filter: only forwards inner strategy signals when range_spike >= threshold.

    range_ratio = (high - low) / open
    rolling_mean = mean(range_ratio for last *window* candles)
    range_spike = range_ratio / rolling_mean
    """

    def __init__(
        self,
        inner: Strategy | None = None,
        window: int = 48,
        threshold: Decimal = Decimal("5.85"),
    ) -> None:
        self.inner = inner
        self.window = window
        self.threshold = threshold

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < self.window:
            return NO_SIGNAL

        ratios: list[Decimal] = []
        for k in history[-self.window :]:
            o = Decimal(k.open)
            if o == 0:
                return NO_SIGNAL
            ratios.append((Decimal(k.high) - Decimal(k.low)) / o)

        rolling_mean = sum(ratios) / Decimal(len(ratios))
        if rolling_mean == 0:
            return NO_SIGNAL

        current_ratio = ratios[-1]
        range_spike = current_ratio / rolling_mean

        if range_spike < self.threshold:
            return NO_SIGNAL

        if self.inner is not None:
            return self.inner.on_kline(symbol, kline, history)

        # No inner strategy — just signal that the filter passed (direction=0 means no trade)
        return NO_SIGNAL
