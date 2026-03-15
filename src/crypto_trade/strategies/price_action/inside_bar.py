from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class InsideBarStrategy:
    """Inside bar breakout: current range inside previous range -> trade breakout direction."""

    def __init__(self, weight: int = 70) -> None:
        self.weight = weight

    def compute_features(self, master: pd.DataFrame) -> None:
        sym = master["symbol"]
        prev_high = master["high"].groupby(sym).shift(1)
        prev_low = master["low"].groupby(sym).shift(1)
        mid = (prev_high + prev_low) / 2

        self._prev_high = prev_high.values
        self._prev_low = prev_low.values
        self._mid = mid.values
        self._high = master["high"].values
        self._low = master["low"].values
        self._close = master["close"].values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        ph = self._prev_high[i]
        pl = self._prev_low[i]
        if ph != ph:  # NaN (first candle per symbol)
            return NO_SIGNAL

        curr_high = self._high[i]
        curr_low = self._low[i]

        if curr_high > ph or curr_low < pl:
            return NO_SIGNAL

        mid = self._mid[i]
        curr_close = self._close[i]
        if curr_close > mid:
            return Signal(direction=1, weight=self.weight)
        elif curr_close < mid:
            return Signal(direction=-1, weight=self.weight)
        return NO_SIGNAL
