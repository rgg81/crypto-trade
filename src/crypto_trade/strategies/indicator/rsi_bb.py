from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.indicators import rsi_series
from crypto_trade.strategies import NO_SIGNAL


class RsiBbStrategy:
    """RSI + Bollinger Bands mean reversion during volatile moments.

    Long: RSI < oversold AND close < lower BB.
    Short: RSI > overbought AND close > upper BB.
    """

    def __init__(
        self,
        rsi_period: int = 14,
        bb_period: int = 20,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
    ) -> None:
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def compute_features(self, master: pd.DataFrame) -> None:
        sym = master["symbol"]
        closes = master["close"]

        rsi_vals = closes.groupby(sym).transform(lambda x: rsi_series(x, self.rsi_period))

        bb_middle = closes.groupby(sym).transform(
            lambda x: x.rolling(self.bb_period, min_periods=self.bb_period).mean()
        )
        bb_std = closes.groupby(sym).transform(
            lambda x: x.rolling(self.bb_period, min_periods=self.bb_period).std(ddof=0)
        )
        bb_upper = bb_middle + 2.0 * bb_std
        bb_lower = bb_middle - 2.0 * bb_std

        self._rsi = rsi_vals.values
        self._bb_upper = bb_upper.values
        self._bb_lower = bb_lower.values
        self._close = closes.values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        rsi_val = self._rsi[i]
        if rsi_val != rsi_val:  # NaN
            return NO_SIGNAL
        bb_u = self._bb_upper[i]
        if bb_u != bb_u:  # NaN
            return NO_SIGNAL

        c = self._close[i]
        if rsi_val < self.rsi_oversold and c < self._bb_lower[i]:
            return Signal(direction=1, weight=75)
        if rsi_val > self.rsi_overbought and c > bb_u:
            return Signal(direction=-1, weight=75)
        return NO_SIGNAL
