from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.backtest_models import Signal
from crypto_trade.kline_array import KlineArray
from crypto_trade.strategies.price_action.consecutive_reversal import (
    ConsecutiveReversalStrategy,
)
from crypto_trade.strategies.price_action.follow_leader import FollowLeaderStrategy
from crypto_trade.strategies.price_action.gap_fill import GapFillStrategy
from crypto_trade.strategies.price_action.inside_bar import InsideBarStrategy
from crypto_trade.strategies.price_action.mean_reversion import MeanReversionStrategy
from crypto_trade.strategies.price_action.momentum import MomentumStrategy
from crypto_trade.strategies.price_action.wick_rejection import WickRejectionStrategy


def _make_kline_array(**kwargs: list[float]) -> KlineArray:
    """Build a KlineArray from keyword lists.

    Accepted keys: open_time, open, high, low, close, volume, close_time.
    Missing fields get sensible defaults.
    """
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
# MomentumStrategy
# ---------------------------------------------------------------------------


class TestMomentumStrategy:
    def test_bullish_momentum(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=0.1)
        master = _make_master(
            open=[100.0, 102.0, 104.0],
            high=[103.0, 105.0, 107.0],
            low=[99.0, 101.0, 103.0],
            close=[102.0, 104.0, 106.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_bearish_momentum(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=0.1)
        master = _make_master(
            open=[106.0, 104.0, 102.0],
            high=[107.0, 105.0, 103.0],
            low=[103.0, 101.0, 99.0],
            close=[104.0, 102.0, 100.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_mixed_direction_no_signal(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=0.1)
        master = _make_master(
            open=[100.0, 102.0, 100.0],
            high=[103.0, 103.0, 103.0],
            low=[99.0, 99.0, 99.0],
            close=[102.0, 100.0, 102.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_small_body_no_signal(self) -> None:
        s = MomentumStrategy(n_candles=3, min_body_pct=0.1)
        master = _make_master(
            open=[100.0, 100.05, 100.1],
            high=[101.0, 101.0, 101.0],
            low=[99.0, 99.0, 99.0],
            close=[100.05, 100.1, 100.15],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = MomentumStrategy(n_candles=3)
        master = _make_master(open=[100.0], close=[102.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# MeanReversionStrategy
# ---------------------------------------------------------------------------


class TestMeanReversionStrategy:
    def test_big_bullish_candle_triggers_short(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=2.0)
        master = _make_master(
            open=[100.0, 100.0, 100.0, 100.0, 100.0],
            high=[101.0, 101.0, 101.0, 101.0, 115.0],
            low=[99.0, 99.0, 99.0, 99.0, 99.0],
            close=[101.0, 101.0, 101.0, 101.0, 110.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_big_bearish_candle_triggers_long(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=2.0)
        master = _make_master(
            open=[100.0, 100.0, 100.0, 100.0, 110.0],
            high=[101.0, 101.0, 101.0, 101.0, 111.0],
            low=[99.0, 99.0, 99.0, 99.0, 95.0],
            close=[99.0, 99.0, 99.0, 99.0, 100.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_normal_candle_no_signal(self) -> None:
        s = MeanReversionStrategy(lookback=5, multiplier=2.0)
        master = _make_master(
            open=[100.0] * 5,
            close=[101.0] * 5,
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = MeanReversionStrategy(lookback=20)
        master = _make_master(open=[100.0] * 5, close=[100.0] * 5)
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# WickRejectionStrategy
# ---------------------------------------------------------------------------


class TestWickRejectionStrategy:
    def test_lower_wick_rejection_bullish(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=2.0)
        master = _make_master(open=[100.0], high=[101.0], low=[94.0], close=[101.0])
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_upper_wick_rejection_bearish(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=2.0)
        master = _make_master(open=[101.0], high=[108.0], low=[100.0], close=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_no_wick_no_signal(self) -> None:
        s = WickRejectionStrategy(wick_body_ratio=2.0)
        master = _make_master(open=[100.0], high=[105.0], low=[100.0], close=[105.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_doji_no_signal(self) -> None:
        s = WickRejectionStrategy()
        master = _make_master(open=[100.0], high=[101.0], low=[99.0], close=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# InsideBarStrategy
# ---------------------------------------------------------------------------


class TestInsideBarStrategy:
    def test_inside_bar_bullish(self) -> None:
        s = InsideBarStrategy()
        master = _make_master(
            open=[95.0, 98.0],
            high=[110.0, 105.0],
            low=[90.0, 95.0],
            close=[105.0, 103.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_inside_bar_bearish(self) -> None:
        s = InsideBarStrategy()
        master = _make_master(
            open=[95.0, 102.0],
            high=[110.0, 105.0],
            low=[90.0, 95.0],
            close=[105.0, 97.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_not_inside_bar_no_signal(self) -> None:
        s = InsideBarStrategy()
        master = _make_master(
            open=[100.0, 103.0],
            high=[105.0, 108.0],
            low=[95.0, 96.0],
            close=[102.0, 106.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = InsideBarStrategy()
        master = _make_master(open=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# GapFillStrategy
# ---------------------------------------------------------------------------


class TestGapFillStrategy:
    def test_gap_up_triggers_short(self) -> None:
        s = GapFillStrategy()
        master = _make_master(
            open=[100.0, 102.0],
            close=[100.0, 101.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_gap_down_triggers_long(self) -> None:
        s = GapFillStrategy()
        master = _make_master(
            open=[100.0, 98.0],
            close=[100.0, 99.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_no_gap_no_signal(self) -> None:
        s = GapFillStrategy()
        master = _make_master(
            open=[100.0, 100.0],
            close=[100.0, 101.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_tiny_gap_ignored(self) -> None:
        s = GapFillStrategy()
        master = _make_master(
            open=[100.0, 100.05],
            close=[100.0, 100.1],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = GapFillStrategy()
        master = _make_master(open=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0


# ---------------------------------------------------------------------------
# ConsecutiveReversalStrategy
# ---------------------------------------------------------------------------


class TestConsecutiveReversalStrategy:
    def test_bullish_streak_triggers_short_reversal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        master = _make_master(
            open=[100.0, 102.0, 104.0, 106.0],
            close=[102.0, 104.0, 106.0, 108.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1

    def test_bearish_streak_triggers_long_reversal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        master = _make_master(
            open=[108.0, 106.0, 104.0, 102.0],
            close=[106.0, 104.0, 102.0, 100.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 1

    def test_mixed_no_signal(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        master = _make_master(
            open=[100.0, 102.0, 100.0, 102.0],
            close=[102.0, 100.0, 102.0, 104.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_insufficient_history(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=4)
        master = _make_master(
            open=[100.0, 100.0, 100.0],
            close=[102.0, 102.0, 102.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == 0

    def test_custom_n(self) -> None:
        s = ConsecutiveReversalStrategy(n_consecutive=2)
        master = _make_master(
            open=[100.0, 102.0],
            close=[102.0, 104.0],
        )
        result = _get_last_signal(s, master)
        assert result.direction == -1


# ---------------------------------------------------------------------------
# FollowLeaderStrategy
# ---------------------------------------------------------------------------


class TestFollowLeaderStrategy:
    def test_bullish_candle(self) -> None:
        s = FollowLeaderStrategy()
        master = _make_master(open=[100.0], close=[105.0])
        result = _get_last_signal(s, master)
        assert result.direction == 1
        assert result.weight == 50

    def test_bearish_candle(self) -> None:
        s = FollowLeaderStrategy()
        master = _make_master(open=[105.0], close=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == -1
        assert result.weight == 50

    def test_doji_no_signal(self) -> None:
        s = FollowLeaderStrategy()
        master = _make_master(open=[100.0], close=[100.0])
        result = _get_last_signal(s, master)
        assert result.direction == 0
