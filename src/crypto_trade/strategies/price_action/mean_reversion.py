from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class MeanReversionStrategy:
    """Extreme candle reversal: current body > K * avg body -> bet on pullback."""

    def __init__(self, lookback: int = 20, multiplier: Decimal = Decimal("2.5")) -> None:
        self.lookback = lookback
        self.multiplier = multiplier

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < self.lookback:
            return NO_SIGNAL

        bodies: list[Decimal] = []
        for k in history[-self.lookback :]:
            bodies.append(abs(Decimal(k.close) - Decimal(k.open)))

        avg_body = sum(bodies) / Decimal(len(bodies))
        if avg_body == 0:
            return NO_SIGNAL

        current_body = bodies[-1]
        if current_body <= self.multiplier * avg_body:
            return NO_SIGNAL

        o, c = Decimal(kline.open), Decimal(kline.close)
        if c > o:
            # Big bullish candle -> expect pullback (short)
            return Signal(direction=-1, weight=60)
        elif c < o:
            # Big bearish candle -> expect pullback (long)
            return Signal(direction=1, weight=60)
        return NO_SIGNAL
