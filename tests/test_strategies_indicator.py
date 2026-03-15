from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.kline_array import KlineArray
from crypto_trade.strategies.indicator.bb_squeeze import BbSqueezeStrategy
from crypto_trade.strategies.indicator.rsi_bb import RsiBbStrategy


def _make_kline_array(**kwargs: list[float]) -> KlineArray:
    """Build a KlineArray from keyword lists."""
    n = 0
    for v in kwargs.values():
        n = len(v)
        break
    if n == 0:
        n = 1

    def _arr(key: str, default: float | int = 0, dtype=np.float64) -> np.ndarray:
        if key in kwargs:
            return np.array(kwargs[key], dtype=dtype)
        return np.full(n, default, dtype=dtype)

    open_time = _arr("open_time", 0, np.int64)
    close_time = (
        np.array(kwargs["close_time"], dtype=np.int64)
        if "close_time" in kwargs
        else open_time + 299999
    )

    return KlineArray.from_arrays(
        open_time=open_time,
        open=_arr("open", 100.0),
        high=_arr("high", 101.0),
        low=_arr("low", 99.0),
        close=_arr("close", 100.0),
        volume=_arr("volume", 1000.0),
        close_time=close_time,
        quote_volume=np.full(n, 100000.0),
        trades=np.full(n, 50, dtype=np.int64),
        taker_buy_volume=np.full(n, 500.0),
        taker_buy_quote_volume=np.full(n, 50000.0),
    )


def _make_master(symbol: str = "TEST", **kwargs) -> pd.DataFrame:
    """Build a master DF from keyword lists."""
    ka = _make_kline_array(**kwargs)
    df = ka.df.reset_index(drop=True)
    df["symbol"] = symbol
    return df


def _get_last_signal(strategy, master: pd.DataFrame) -> Signal:
    """Compute features and return the last signal."""
    strategy.compute_features(master)
    syms = master["symbol"].values
    ots = master["open_time"].values
    signal = Signal(direction=0, weight=0)
    for i in range(len(master)):
        signal = strategy.get_signal(str(syms[i]), int(ots[i]))
    return signal


# ---------------------------------------------------------------------------
# RsiBbStrategy
# ---------------------------------------------------------------------------


class TestRsiBbStrategy:
    def test_oversold_triggers_long(self) -> None:
        s = RsiBbStrategy(rsi_period=5, bb_period=10)
        # Flat period (BB tightens), then small drops, then huge crash
        closes = [100.0] * 15 + [98.0, 96.0, 70.0]
        opens = [100.0] * 15 + [100.0, 100.0, 96.0]
        highs = [101.0] * 15 + [100.0, 100.0, 96.0]
        lows = [99.0] * 15 + [98.0, 96.0, 70.0]
        open_times = [i * 300000 for i in range(18)]
        master = _make_master(close=closes, open=opens, high=highs, low=lows, open_time=open_times)
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_overbought_triggers_short(self) -> None:
        s = RsiBbStrategy(rsi_period=5, bb_period=10)
        closes = [100.0] * 15 + [102.0, 104.0, 130.0]
        opens = [100.0] * 15 + [100.0, 100.0, 104.0]
        highs = [101.0] * 15 + [102.0, 104.0, 130.0]
        lows = [99.0] * 15 + [100.0, 100.0, 104.0]
        open_times = [i * 300000 for i in range(18)]
        master = _make_master(close=closes, open=opens, high=highs, low=lows, open_time=open_times)
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_neutral_no_signal(self) -> None:
        s = RsiBbStrategy(rsi_period=14, bb_period=20)
        n = 25
        master = _make_master(
            close=[100.0] * n,
            open_time=[i * 300000 for i in range(n)],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = RsiBbStrategy(rsi_period=14, bb_period=20)
        master = _make_master(close=[100.0] * 10)
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# BbSqueezeStrategy
# ---------------------------------------------------------------------------


class TestBbSqueezeStrategy:
    def test_insufficient_history(self) -> None:
        s = BbSqueezeStrategy(bb_period=20, squeeze_lookback=10)
        master = _make_master(close=[100.0] * 10)
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_no_squeeze_no_signal(self) -> None:
        """No squeeze (volatile prices throughout) -> no signal."""
        s = BbSqueezeStrategy(bb_period=5, squeeze_lookback=3, squeeze_threshold=0.02)
        n = 15
        closes = [100.0 + (i % 2) * 10 for i in range(n)]
        opens = closes[:]
        highs = [c + 5 for c in closes]
        lows = [c - 5 for c in closes]
        master = _make_master(
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=[1000.0] * n,
            open_time=[i * 300000 for i in range(n)],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_squeeze_then_expansion_bullish(self) -> None:
        """Tight BB then sudden expansion up with volume -> long."""
        s = BbSqueezeStrategy(
            bb_period=5,
            squeeze_lookback=3,
            squeeze_threshold=0.05,
            vol_multiplier=1.5,
        )
        n = 11
        opens = [100.0] * 10 + [100.0]
        highs = [100.01] * 10 + [115.0]
        lows = [99.99] * 10 + [99.0]
        closes = [100.0] * 10 + [112.0]
        volumes = [100.0] * 10 + [5000.0]
        master = _make_master(
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
            open_time=[i * 300000 for i in range(n)],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_squeeze_then_expansion_bearish(self) -> None:
        """Tight BB then sudden expansion down with volume -> short."""
        s = BbSqueezeStrategy(
            bb_period=5,
            squeeze_lookback=3,
            squeeze_threshold=0.05,
            vol_multiplier=1.5,
        )
        n = 11
        opens = [100.0] * 10 + [100.0]
        highs = [100.01] * 10 + [101.0]
        lows = [99.99] * 10 + [85.0]
        closes = [100.0] * 10 + [88.0]
        volumes = [100.0] * 10 + [5000.0]
        master = _make_master(
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            volume=volumes,
            open_time=[i * 300000 for i in range(n)],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1
