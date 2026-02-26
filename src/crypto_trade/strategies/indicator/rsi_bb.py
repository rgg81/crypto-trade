from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.indicators import bollinger_bands, rsi
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL, closes


class RsiBbStrategy:
    """RSI + Bollinger Bands mean reversion during volatile moments.

    Long: RSI < oversold AND close < lower BB.
    Short: RSI > overbought AND close > upper BB.
    """

    def __init__(
        self,
        rsi_period: int = 14,
        bb_period: int = 20,
        rsi_oversold: Decimal = Decimal("30"),
        rsi_overbought: Decimal = Decimal("70"),
    ) -> None:
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        close_vals = closes(history)
        min_len = max(self.rsi_period + 1, self.bb_period)
        if len(close_vals) < min_len:
            return NO_SIGNAL

        rsi_val = rsi(close_vals, self.rsi_period)
        bb = bollinger_bands(close_vals, self.bb_period)
        if rsi_val is None or bb is None:
            return NO_SIGNAL

        current_close = close_vals[-1]

        if rsi_val < self.rsi_oversold and current_close < bb.lower:
            return Signal(direction=1, weight=75)

        if rsi_val > self.rsi_overbought and current_close > bb.upper:
            return Signal(direction=-1, weight=75)

        return NO_SIGNAL
