from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BollingerBands:
    upper: Decimal
    middle: Decimal
    lower: Decimal
    bandwidth: Decimal


def sma(values: list[Decimal], period: int) -> Decimal | None:
    """Simple moving average over the last *period* values."""
    if len(values) < period or period <= 0:
        return None
    window = values[-period:]
    return sum(window) / Decimal(period)


def ema(values: list[Decimal], period: int) -> Decimal | None:
    """Exponential moving average over *values*.

    Uses the standard multiplier k = 2 / (period + 1).
    Seed is the SMA of the first *period* values.
    """
    if len(values) < period or period <= 0:
        return None
    k = Decimal(2) / Decimal(period + 1)
    result = sum(values[:period]) / Decimal(period)
    for v in values[period:]:
        result = v * k + result * (1 - k)
    return result


def stddev(values: list[Decimal], period: int) -> Decimal | None:
    """Population standard deviation over the last *period* values."""
    if len(values) < period or period <= 0:
        return None
    window = values[-period:]
    mean = sum(window) / Decimal(period)
    variance = sum((v - mean) ** 2 for v in window) / Decimal(period)
    return variance.sqrt()


def bollinger_bands(
    closes: list[Decimal], period: int = 20, num_std: Decimal = Decimal(2)
) -> BollingerBands | None:
    """Bollinger Bands: middle=SMA, upper/lower=middle +/- num_std*stddev."""
    middle = sma(closes, period)
    sd = stddev(closes, period)
    if middle is None or sd is None:
        return None
    upper = middle + num_std * sd
    lower = middle - num_std * sd
    bandwidth = (upper - lower) / middle if middle != 0 else Decimal(0)
    return BollingerBands(upper=upper, middle=middle, lower=lower, bandwidth=bandwidth)


def true_range(high: Decimal, low: Decimal, prev_close: Decimal) -> Decimal:
    """True range for a single bar."""
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(
    highs: list[Decimal], lows: list[Decimal], closes: list[Decimal], period: int = 14
) -> Decimal | None:
    """Average true range (SMA of true ranges over *period*)."""
    n = len(highs)
    if n < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return None
    trs: list[Decimal] = []
    for i in range(1, n):
        trs.append(true_range(highs[i], lows[i], closes[i - 1]))
    return sma(trs, period)


def rsi(closes: list[Decimal], period: int = 14) -> Decimal | None:
    """Relative Strength Index using Wilder's smoothing (EMA-style)."""
    if len(closes) < period + 1 or period <= 0:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [d if d > 0 else Decimal(0) for d in deltas[:period]]
    losses = [-d if d < 0 else Decimal(0) for d in deltas[:period]]
    avg_gain = sum(gains) / Decimal(period)
    avg_loss = sum(losses) / Decimal(period)

    for d in deltas[period:]:
        gain = d if d > 0 else Decimal(0)
        loss = -d if d < 0 else Decimal(0)
        avg_gain = (avg_gain * Decimal(period - 1) + gain) / Decimal(period)
        avg_loss = (avg_loss * Decimal(period - 1) + loss) / Decimal(period)

    if avg_loss == 0:
        return Decimal(100)
    rs = avg_gain / avg_loss
    return Decimal(100) - Decimal(100) / (1 + rs)
