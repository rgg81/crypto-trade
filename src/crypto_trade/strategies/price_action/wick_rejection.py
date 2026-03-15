from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class WickRejectionStrategy:
    """Wick > K * body -> trade rejection direction."""

    def __init__(self, wick_body_ratio: float = 2.0) -> None:
        self.wick_body_ratio = wick_body_ratio

    def compute_features(self, master: pd.DataFrame) -> None:
        o = master["open"].values
        c = master["close"].values
        h = master["high"].values
        lo = master["low"].values

        body = np.abs(c - o)
        upper_wick = h - np.maximum(o, c)
        lower_wick = np.minimum(o, c) - lo

        self._body = body
        self._upper_wick = upper_wick
        self._lower_wick = lower_wick
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        body = self._body[i]
        if body == 0:
            return NO_SIGNAL

        upper = self._upper_wick[i]
        lower = self._lower_wick[i]
        k = self.wick_body_ratio

        if lower > k * body and lower > upper:
            return Signal(direction=1, weight=65)
        if upper > k * body and upper > lower:
            return Signal(direction=-1, weight=65)
        return NO_SIGNAL
