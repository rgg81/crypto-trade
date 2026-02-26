from __future__ import annotations

from decimal import Decimal

from crypto_trade.backtest_models import Signal
from crypto_trade.indicators import bollinger_bands
from crypto_trade.models import Kline
from crypto_trade.strategies import NO_SIGNAL, closes, volumes


class BbSqueezeStrategy:
    """Bollinger Band squeeze breakout.

    When BB bandwidth has been below threshold for N periods and then expands
    with a volume spike, trade the breakout direction.
    """

    def __init__(
        self,
        bb_period: int = 20,
        squeeze_threshold: Decimal = Decimal("0.02"),
        squeeze_lookback: int = 10,
        vol_multiplier: Decimal = Decimal("1.5"),
    ) -> None:
        self.bb_period = bb_period
        self.squeeze_threshold = squeeze_threshold
        self.squeeze_lookback = squeeze_lookback
        self.vol_multiplier = vol_multiplier

    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal:
        min_len = self.bb_period + self.squeeze_lookback
        if len(history) < min_len:
            return NO_SIGNAL

        # Compute current BB
        close_vals = closes(history)
        bb_now = bollinger_bands(close_vals, self.bb_period)
        if bb_now is None:
            return NO_SIGNAL

        # Compute BB for the lookback window (excluding current candle)
        prev_closes = closes(history[:-1])
        bb_prev = bollinger_bands(prev_closes, self.bb_period)
        if bb_prev is None:
            return NO_SIGNAL

        # Check squeeze: previous bandwidth was below threshold
        if bb_prev.bandwidth >= self.squeeze_threshold:
            return NO_SIGNAL

        # Check expansion: current bandwidth exceeds threshold
        if bb_now.bandwidth <= self.squeeze_threshold:
            return NO_SIGNAL

        # Volume confirmation
        vol_vals = volumes(history)
        if len(vol_vals) < self.squeeze_lookback:
            return NO_SIGNAL
        avg_vol = sum(vol_vals[-self.squeeze_lookback - 1 : -1]) / Decimal(self.squeeze_lookback)
        current_vol = vol_vals[-1]
        if avg_vol > 0 and current_vol <= self.vol_multiplier * avg_vol:
            return NO_SIGNAL

        # Breakout direction: close vs BB middle
        current_close = close_vals[-1]
        if current_close > bb_now.middle:
            return Signal(direction=1, weight=80)
        elif current_close < bb_now.middle:
            return Signal(direction=-1, weight=80)

        return NO_SIGNAL
