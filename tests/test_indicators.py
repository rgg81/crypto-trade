from __future__ import annotations

from decimal import Decimal

from crypto_trade.indicators import (
    BollingerBands,
    atr,
    bollinger_bands,
    ema,
    rsi,
    sma,
    stddev,
    true_range,
)


class TestSma:
    def test_basic(self) -> None:
        vals = [Decimal(i) for i in [10, 20, 30, 40, 50]]
        assert sma(vals, 3) == Decimal(40)  # (30+40+50)/3

    def test_full_window(self) -> None:
        vals = [Decimal(i) for i in [2, 4, 6]]
        assert sma(vals, 3) == Decimal(4)

    def test_insufficient_data(self) -> None:
        assert sma([Decimal(1)], 3) is None

    def test_empty(self) -> None:
        assert sma([], 1) is None

    def test_period_zero(self) -> None:
        assert sma([Decimal(1)], 0) is None

    def test_single_value(self) -> None:
        assert sma([Decimal(42)], 1) == Decimal(42)


class TestEma:
    def test_basic(self) -> None:
        vals = [Decimal(i) for i in [10, 20, 30, 40, 50]]
        result = ema(vals, 3)
        assert result is not None
        # Seed = sma(10,20,30) = 20, k=0.5
        # step 4: 40*0.5 + 20*0.5 = 30
        # step 5: 50*0.5 + 30*0.5 = 40
        assert result == Decimal(40)

    def test_insufficient_data(self) -> None:
        assert ema([Decimal(1)], 3) is None

    def test_exact_period(self) -> None:
        vals = [Decimal(i) for i in [10, 20, 30]]
        result = ema(vals, 3)
        assert result == Decimal(20)  # just the seed SMA


class TestStddev:
    def test_basic(self) -> None:
        vals = [Decimal(i) for i in [2, 4, 4, 4, 5, 5, 7, 9]]
        result = stddev(vals, 8)
        assert result is not None
        assert abs(result - Decimal(2)) < Decimal("0.01")

    def test_constant_values(self) -> None:
        vals = [Decimal(5)] * 5
        assert stddev(vals, 5) == Decimal(0)

    def test_insufficient_data(self) -> None:
        assert stddev([Decimal(1)], 3) is None


class TestBollingerBands:
    def test_basic(self) -> None:
        vals = [Decimal(i) for i in range(1, 21)]  # 1..20
        result = bollinger_bands(vals, period=20)
        assert result is not None
        assert isinstance(result, BollingerBands)
        assert result.middle == Decimal("10.5")
        assert result.upper > result.middle
        assert result.lower < result.middle
        assert result.bandwidth > 0

    def test_insufficient_data(self) -> None:
        assert bollinger_bands([Decimal(1)] * 5, period=20) is None

    def test_constant_prices(self) -> None:
        vals = [Decimal(100)] * 20
        result = bollinger_bands(vals, period=20)
        assert result is not None
        assert result.upper == Decimal(100)
        assert result.lower == Decimal(100)
        assert result.bandwidth == Decimal(0)


class TestTrueRange:
    def test_high_low_dominant(self) -> None:
        # high-low=5 > |high-prev_close|=3 > |low-prev_close|=2
        result = true_range(Decimal(105), Decimal(100), Decimal(102))
        assert result == Decimal(5)

    def test_gap_up(self) -> None:
        # |high-prev_close|=7, high-low=5, |low-prev_close|=2
        result = true_range(Decimal(107), Decimal(102), Decimal(100))
        assert result == Decimal(7)

    def test_gap_down(self) -> None:
        # |low-prev_close|=8, high-low=5, |high-prev_close|=3
        result = true_range(Decimal(97), Decimal(92), Decimal(100))
        assert result == Decimal(8)


class TestAtr:
    def test_basic(self) -> None:
        highs = [Decimal(h) for h in [11, 12, 13, 14, 15]]
        lows = [Decimal(v) for v in [9, 10, 11, 12, 13]]
        closes = [Decimal(c) for c in [10, 11, 12, 13, 14]]
        result = atr(highs, lows, closes, period=3)
        assert result is not None
        # Each TR = max(high-low, |high-prev_close|, |low-prev_close|) = 2
        assert result == Decimal(2)

    def test_insufficient_data(self) -> None:
        assert atr([Decimal(10)], [Decimal(9)], [Decimal(10)], period=3) is None

    def test_needs_period_plus_one(self) -> None:
        # period=3 needs 4 bars (3 TRs need prev_close from bar 0)
        highs = [Decimal(h) for h in [11, 12, 13]]
        lows = [Decimal(v) for v in [9, 10, 11]]
        closes = [Decimal(c) for c in [10, 11, 12]]
        assert atr(highs, lows, closes, period=3) is None


class TestRsi:
    def test_all_gains(self) -> None:
        closes = [Decimal(i) for i in range(100, 116)]  # 16 values, 15 deltas
        result = rsi(closes, period=14)
        assert result is not None
        assert result == Decimal(100)

    def test_all_losses(self) -> None:
        closes = [Decimal(i) for i in range(115, 99, -1)]  # 16 values descending
        result = rsi(closes, period=14)
        assert result is not None
        assert result == Decimal(0)

    def test_mixed(self) -> None:
        closes = [Decimal(100)]
        for i in range(15):
            if i % 2 == 0:
                closes.append(closes[-1] + Decimal(1))
            else:
                closes.append(closes[-1] - Decimal(1))
        result = rsi(closes, period=14)
        assert result is not None
        assert Decimal(0) < result < Decimal(100)

    def test_insufficient_data(self) -> None:
        assert rsi([Decimal(100)] * 10, period=14) is None

    def test_period_1(self) -> None:
        closes = [Decimal(100), Decimal(105)]
        result = rsi(closes, period=1)
        assert result is not None
        assert result == Decimal(100)  # one gain, no loss
