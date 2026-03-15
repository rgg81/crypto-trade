from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class ConsecutiveContinuationStrategy:
    """N+ same-direction candles -> trade continuation (with the trend)."""

    def __init__(self, n_consecutive: int = 6) -> None:
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
        self._sym = master["symbol"].values
        self._open_time = master["open_time"].values
        self._open = master["open"].values
        self._high = master["high"].values
        self._low = master["low"].values
        self._close = master["close"].values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1

        bull = self._bull[i]
        bear = self._bear[i]
        if bull == 1:
            signal = Signal(direction=1, weight=60)
        elif bear == 1:
            signal = Signal(direction=-1, weight=60)
        else:
            signal = NO_SIGNAL

        if i % 50000 == 0:
            dt = datetime.fromtimestamp(int(self._open_time[i]) / 1000, tz=UTC)
            direction = {1: "LONG", -1: "SHORT", 0: "-"}[signal.direction]
            print(
                f"[cc] #{i} {self._sym[i]} {dt:%Y-%m-%d %H:%M}"
                f" | O={self._open[i]:.2f} H={self._high[i]:.2f}"
                f" L={self._low[i]:.2f} C={self._close[i]:.2f}"
                f" | bull={bull:.0f} bear={bear:.0f}"
                f" | signal={direction}"
            )

        return signal
