from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal, Strategy
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL


class VolumeFilter:
    """Pass-through filter: only forwards inner strategy signals when volume > multiplier * avg."""

    def __init__(
        self,
        inner: Strategy | None = None,
        lookback: int = 20,
        multiplier: Decimal = Decimal("1.5"),
    ) -> None:
        self.inner = inner
        self.lookback = lookback
        self.multiplier = multiplier

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        if len(history) < self.lookback:
            return NO_SIGNAL

        vols = [Decimal(k.volume) for k in history[-self.lookback :]]
        avg_vol = sum(vols) / Decimal(len(vols))
        current_vol = Decimal(kline.volume)

        if current_vol <= self.multiplier * avg_vol:
            return NO_SIGNAL

        if self.inner is not None:
            return self.inner.on_kline(symbol, kline, history)

        return NO_SIGNAL
