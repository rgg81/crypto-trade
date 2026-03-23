from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal, Strategy
from crypto_trade.strategies import NO_SIGNAL


class VolumeFilter:
    """Pass-through filter: only forwards inner strategy signals when volume > multiplier * avg."""

    def __init__(
        self,
        inner: Strategy | None = None,
        lookback: int = 20,
        multiplier: float = 1.5,
    ) -> None:
        self.inner = inner
        self.lookback = lookback
        self.multiplier = multiplier

    def compute_features(self, master: pd.DataFrame) -> None:
        if self.inner is not None:
            self.inner.compute_features(master)

        vol = master["volume"]
        vol_avg = vol.groupby(master["symbol"]).transform(
            lambda x: x.rolling(self.lookback, min_periods=self.lookback).mean()
        )
        self._passes = (vol > self.multiplier * vol_avg).values
        self._pos = 0

    def skip(self) -> None:
        self._pos += 1
        if self.inner is not None:
            self.inner.skip()

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        if not self._passes[i]:
            if self.inner is not None:
                self.inner.skip()
            return NO_SIGNAL
        if self.inner is not None:
            return self.inner.get_signal(symbol, open_time)
        return NO_SIGNAL
