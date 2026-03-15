from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class FollowLeaderStrategy:
    """Trade in the same direction as the current candle (bullish -> buy, bearish -> sell)."""

    def compute_features(self, master: pd.DataFrame) -> None:
        o = master["open"]
        c = master["close"]
        self._bull = (c > o).values
        self._bear = (c < o).values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        if self._bull[i]:
            return Signal(direction=1, weight=50)
        if self._bear[i]:
            return Signal(direction=-1, weight=50)
        return NO_SIGNAL
