from __future__ import annotations

import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.strategies import NO_SIGNAL


class MomentumStrategy:
    """Trend continuation: last N candles same direction with min body size -> continue."""

    def __init__(self, n_candles: int = 3, min_body_pct: float = 0.1) -> None:
        self.n_candles = n_candles
        self.min_body_pct = min_body_pct / 100.0

    def compute_features(self, master: pd.DataFrame) -> None:
        n = self.n_candles
        o = master["open"]
        c = master["close"]
        body_pct = ((c - o) / o).abs()
        body_ok = body_pct >= self.min_body_pct
        is_bull = (c > o).astype(int)
        is_bear = (c < o).astype(int)

        all_bull = (
            (body_ok & is_bull.astype(bool))
            .astype(int)
            .groupby(master["symbol"])
            .transform(lambda x: x.rolling(n, min_periods=n).min())
            .fillna(0)
        )

        all_bear = (
            (body_ok & is_bear.astype(bool))
            .astype(int)
            .groupby(master["symbol"])
            .transform(lambda x: x.rolling(n, min_periods=n).min())
            .fillna(0)
        )

        self._bull = all_bull.values
        self._bear = all_bear.values
        self._pos = 0

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        i = self._pos
        self._pos += 1
        if self._bull[i] == 1:
            return Signal(direction=1, weight=70)
        if self._bear[i] == 1:
            return Signal(direction=-1, weight=70)
        return NO_SIGNAL
