from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.indicators import (
    BollingerBands,
    atr,
    bollinger_bands,
    ema,
    rsi,
    rsi_series,
    sma,
    stddev,
    true_range,
)


class TestSma:
    def test_basic(self) -> None:
        vals = np.array([10, 20, 30, 40, 50], dtype=np.float64)
        assert sma(vals, 3) == pytest.approx(40)

    def test_full_window(self) -> None:
        vals = np.array([2, 4, 6], dtype=np.float64)
        assert sma(vals, 3) == pytest.approx(4)

    def test_insufficient_data(self) -> None:
        assert sma(np.array([1.0]), 3) is None

    def test_empty(self) -> None:
        assert sma(np.array([], dtype=np.float64), 1) is None

    def test_period_zero(self) -> None:
        assert sma(np.array([1.0]), 0) is None

    def test_single_value(self) -> None:
        assert sma(np.array([42.0]), 1) == pytest.approx(42)


class TestEma:
    def test_basic(self) -> None:
        vals = np.array([10, 20, 30, 40, 50], dtype=np.float64)
        result = ema(vals, 3)
        assert result is not None
        assert result == pytest.approx(40)

    def test_insufficient_data(self) -> None:
        assert ema(np.array([1.0]), 3) is None

    def test_exact_period(self) -> None:
        vals = np.array([10, 20, 30], dtype=np.float64)
        result = ema(vals, 3)
        assert result == pytest.approx(20)


class TestStddev:
    def test_basic(self) -> None:
        vals = np.array([2, 4, 4, 4, 5, 5, 7, 9], dtype=np.float64)
        result = stddev(vals, 8)
        assert result is not None
        assert result == pytest.approx(2, abs=0.01)

    def test_constant_values(self) -> None:
        vals = np.array([5.0] * 5)
        assert stddev(vals, 5) == pytest.approx(0)

    def test_insufficient_data(self) -> None:
        assert stddev(np.array([1.0]), 3) is None


class TestBollingerBands:
    def test_basic(self) -> None:
        vals = np.arange(1, 21, dtype=np.float64)
        result = bollinger_bands(vals, period=20)
        assert result is not None
        assert isinstance(result, BollingerBands)
        assert result.middle == pytest.approx(10.5)
        assert result.upper > result.middle
        assert result.lower < result.middle
        assert result.bandwidth > 0

    def test_insufficient_data(self) -> None:
        assert bollinger_bands(np.array([1.0] * 5), period=20) is None

    def test_constant_prices(self) -> None:
        vals = np.array([100.0] * 20)
        result = bollinger_bands(vals, period=20)
        assert result is not None
        assert result.upper == pytest.approx(100)
        assert result.lower == pytest.approx(100)
        assert result.bandwidth == pytest.approx(0)


class TestTrueRange:
    def test_high_low_dominant(self) -> None:
        result = true_range(105.0, 100.0, 102.0)
        assert result == pytest.approx(5)

    def test_gap_up(self) -> None:
        result = true_range(107.0, 102.0, 100.0)
        assert result == pytest.approx(7)

    def test_gap_down(self) -> None:
        result = true_range(97.0, 92.0, 100.0)
        assert result == pytest.approx(8)


class TestAtr:
    def test_basic(self) -> None:
        highs = np.array([11, 12, 13, 14, 15], dtype=np.float64)
        lows = np.array([9, 10, 11, 12, 13], dtype=np.float64)
        closes = np.array([10, 11, 12, 13, 14], dtype=np.float64)
        result = atr(highs, lows, closes, period=3)
        assert result is not None
        assert result == pytest.approx(2)

    def test_insufficient_data(self) -> None:
        assert atr(np.array([10.0]), np.array([9.0]), np.array([10.0]), period=3) is None

    def test_needs_period_plus_one(self) -> None:
        highs = np.array([11, 12, 13], dtype=np.float64)
        lows = np.array([9, 10, 11], dtype=np.float64)
        closes = np.array([10, 11, 12], dtype=np.float64)
        assert atr(highs, lows, closes, period=3) is None


class TestRsi:
    def test_all_gains(self) -> None:
        closes = np.arange(100, 116, dtype=np.float64)
        result = rsi(closes, period=14)
        assert result is not None
        assert result == pytest.approx(100)

    def test_all_losses(self) -> None:
        closes = np.arange(115, 99, -1, dtype=np.float64)
        result = rsi(closes, period=14)
        assert result is not None
        assert result == pytest.approx(0)

    def test_mixed(self) -> None:
        vals = [100.0]
        for i in range(15):
            if i % 2 == 0:
                vals.append(vals[-1] + 1)
            else:
                vals.append(vals[-1] - 1)
        closes = np.array(vals)
        result = rsi(closes, period=14)
        assert result is not None
        assert 0 < result < 100

    def test_insufficient_data(self) -> None:
        assert rsi(np.array([100.0] * 10), period=14) is None

    def test_period_1(self) -> None:
        closes = np.array([100.0, 105.0])
        result = rsi(closes, period=1)
        assert result is not None
        assert result == pytest.approx(100)


class TestRsiSeries:
    def test_all_gains(self) -> None:
        closes = pd.Series(np.arange(100, 116, dtype=np.float64))
        result = rsi_series(closes, period=14)
        assert result.iloc[-1] == pytest.approx(100)

    def test_all_losses(self) -> None:
        closes = pd.Series(np.arange(115, 99, -1, dtype=np.float64))
        result = rsi_series(closes, period=14)
        assert result.iloc[-1] == pytest.approx(0)

    def test_mixed_in_range(self) -> None:
        vals = [100.0]
        for i in range(15):
            if i % 2 == 0:
                vals.append(vals[-1] + 1)
            else:
                vals.append(vals[-1] - 1)
        closes = pd.Series(vals)
        result = rsi_series(closes, period=14)
        last = result.iloc[-1]
        assert 0 < last < 100

    def test_insufficient_data_nan(self) -> None:
        closes = pd.Series([100.0] * 10)
        result = rsi_series(closes, period=14)
        assert result.isna().all()

    def test_returns_series_same_length(self) -> None:
        closes = pd.Series(np.arange(100, 130, dtype=np.float64))
        result = rsi_series(closes, period=14)
        assert len(result) == len(closes)
