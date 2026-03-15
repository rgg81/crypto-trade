from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal, Strategy
from crypto_trade.strategies import NO_SIGNAL


class RangeSpikeFilter:
    """Pass-through filter: only forwards inner strategy signals when range_spike >= threshold.

    range_ratio = (high - low) / open
    rolling_mean = mean(range_ratio for last *window* candles)
    range_spike = range_ratio / rolling_mean
    """

    def __init__(
        self,
        inner: Strategy | None = None,
        window: int = 48,
        threshold: float = 5.85,
    ) -> None:
        self.inner = inner
        self.window = window
        self.threshold = threshold

    def compute_features(self, master: pd.DataFrame) -> None:
        if self.inner is not None:
            self.inner.compute_features(master)

        range_ratio = (master["high"] - master["low"]) / master["open"]
        rolling_mean = range_ratio.groupby(master["symbol"]).transform(
            lambda x: x.rolling(self.window, min_periods=self.window).mean()
        )
        range_spike = range_ratio / rolling_mean.replace(0.0, float("nan"))

        self._passes = (range_spike >= self.threshold).values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        if not self._passes[i]:
            if self.inner is not None:
                self.inner.get_signal(symbol, open_time)
            return NO_SIGNAL
        if self.inner is not None:
            return self.inner.get_signal(symbol, open_time)
        return NO_SIGNAL
