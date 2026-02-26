from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class MomentumStrategy:
    """Trend continuation: last N candles same direction with min body size -> continue."""

    def __init__(self, n_candles: int = 3, min_body_pct: Decimal = Decimal("0.1")) -> None:
        self.n_candles = n_candles
        self.min_body_pct = min_body_pct / Decimal(100)

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < self.n_candles:
            return NO_SIGNAL

        recent = history[-self.n_candles :]
        bullish = 0
        bearish = 0
        for k in recent:
            o, c = Decimal(k.open), Decimal(k.close)
            if o == 0:
                return NO_SIGNAL
            body_pct = abs(c - o) / o
            if body_pct < self.min_body_pct:
                return NO_SIGNAL
            if c > o:
                bullish += 1
            elif c < o:
                bearish += 1
            else:
                return NO_SIGNAL

        if bullish == self.n_candles:
            return Signal(direction=1, weight=70)
        if bearish == self.n_candles:
            return Signal(direction=-1, weight=70)
        return NO_SIGNAL
