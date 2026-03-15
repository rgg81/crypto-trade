from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class MeanReversionStrategy:
    """Extreme candle reversal: current body > K * avg body -> bet on pullback."""

    def __init__(self, lookback: int = 20, multiplier: float = 2.5) -> None:
        self.lookback = lookback
        self.multiplier = multiplier

    def compute_features(self, master: pd.DataFrame) -> None:
        o = master["open"]
        c = master["close"]
        body = (c - o).abs()
        avg_body = body.groupby(master["symbol"]).transform(
            lambda x: x.rolling(self.lookback, min_periods=self.lookback).mean()
        )
        is_bullish = c > o

        self._body = body.values
        self._avg_body = avg_body.values
        self._is_bullish = is_bullish.values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        avg = self._avg_body[i]
        if avg != avg:  # NaN check
            return NO_SIGNAL
        if avg == 0:
            return NO_SIGNAL
        if self._body[i] <= self.multiplier * avg:
            return NO_SIGNAL
        if self._is_bullish[i]:
            return Signal(direction=-1, weight=60)
        if self._body[i] > 0:  # bearish (body > 0 means c != o)
            return Signal(direction=1, weight=60)
        return NO_SIGNAL
