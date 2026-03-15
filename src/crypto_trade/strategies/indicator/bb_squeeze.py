from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class BbSqueezeStrategy:
    """Bollinger Band squeeze breakout.

    When BB bandwidth has been below threshold for N periods and then expands
    with a volume spike, trade the breakout direction.
    """

    def __init__(
        self,
        bb_period: int = 20,
        squeeze_threshold: float = 0.02,
        squeeze_lookback: int = 10,
        vol_multiplier: float = 1.5,
    ) -> None:
        self.bb_period = bb_period
        self.squeeze_threshold = squeeze_threshold
        self.squeeze_lookback = squeeze_lookback
        self.vol_multiplier = vol_multiplier

    def compute_features(self, master: pd.DataFrame) -> None:
        sym = master["symbol"]
        closes = master["close"]

        bb_middle = closes.groupby(sym).transform(
            lambda x: x.rolling(self.bb_period, min_periods=self.bb_period).mean()
        )
        bb_std = closes.groupby(sym).transform(
            lambda x: x.rolling(self.bb_period, min_periods=self.bb_period).std(ddof=0)
        )
        bb_upper = bb_middle + 2.0 * bb_std
        bb_lower = bb_middle - 2.0 * bb_std
        bandwidth = ((bb_upper - bb_lower) / bb_middle).fillna(0)
        prev_bw = bandwidth.groupby(sym).shift(1)

        vol_avg = (
            master["volume"]
            .groupby(sym)
            .transform(
                lambda x: x.rolling(self.squeeze_lookback, min_periods=self.squeeze_lookback).mean()
            )
        )
        vol_spike = master["volume"] > self.vol_multiplier * vol_avg

        self._bandwidth = bandwidth.values
        self._prev_bw = prev_bw.values
        self._vol_spike = vol_spike.values
        self._close = closes.values
        self._bb_middle = bb_middle.values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        prev = self._prev_bw[i]
        if prev != prev:  # NaN
            return NO_SIGNAL
        # Previous bandwidth must be below squeeze threshold
        if prev >= self.squeeze_threshold:
            return NO_SIGNAL
        # Current bandwidth must exceed threshold (expansion)
        if self._bandwidth[i] <= self.squeeze_threshold:
            return NO_SIGNAL
        # Volume confirmation
        if not self._vol_spike[i]:
            return NO_SIGNAL
        # Breakout direction
        if self._close[i] > self._bb_middle[i]:
            return Signal(direction=1, weight=80)
        elif self._close[i] < self._bb_middle[i]:
            return Signal(direction=-1, weight=80)
        return NO_SIGNAL
