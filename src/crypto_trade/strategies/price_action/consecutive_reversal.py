from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class ConsecutiveReversalStrategy:
    """N+ same-direction candles -> trade reversal."""

    def __init__(self, n_consecutive: int = 4) -> None:
        self.n_consecutive = n_consecutive

    def compute_features(self, master: pd.DataFrame) -> None:
        n = self.n_consecutive
        is_bull = (master["close"] > master["open"]).astype(int)
        is_bear = (master["close"] < master["open"]).astype(int)

        bull_streak = (
            is_bull.groupby(master["symbol"])
            .transform(lambda x: x.rolling(n, min_periods=n).min())
            .fillna(0)
        )
        bear_streak = (
            is_bear.groupby(master["symbol"])
            .transform(lambda x: x.rolling(n, min_periods=n).min())
            .fillna(0)
        )

        self._bull = bull_streak.values
        self._bear = bear_streak.values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        if self._bull[i] == 1:
            return Signal(direction=-1, weight=60)  # reversal
        if self._bear[i] == 1:
            return Signal(direction=1, weight=60)  # reversal
        return NO_SIGNAL
