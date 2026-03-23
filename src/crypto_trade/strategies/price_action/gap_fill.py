from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class GapFillStrategy:
    """Gap / imbalance fill: gap between candles -> trade the fill direction."""

    def __init__(self, weight: int = 60) -> None:
        self.weight = weight

    def compute_features(self, master: pd.DataFrame) -> None:
        sym = master["symbol"]
        prev_close = master["close"].groupby(sym).shift(1)

        self._prev_close = prev_close.values
        self._open = master["open"].values
        self._pos = 0

    def skip(self) -> None:
        self._pos += 1

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        pc = self._prev_close[i]
        if pc != pc:  # NaN
            return NO_SIGNAL

        curr_open = self._open[i]

        if curr_open > pc:
            gap = curr_open - pc
            if pc != 0 and gap / pc > 0.001:
                return Signal(direction=-1, weight=self.weight)

        if curr_open < pc:
            gap = pc - curr_open
            if pc != 0 and gap / pc > 0.001:
                return Signal(direction=1, weight=self.weight)

        return NO_SIGNAL
