from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BollingerBands:
    upper: float
    middle: float
    lower: float
    bandwidth: float


def sma(values: np.ndarray, period: int) -> float | None:
    """Simple moving average over the last *period* values."""
    if len(values) < period or period <= 0:
        return None
    return float(values[-period:].mean())


def ema(values: np.ndarray, period: int) -> float | None:
    """Exponential moving average over *values*.

    Uses the standard multiplier k = 2 / (period + 1).
    Seed is the SMA of the first *period* values.
    """
    if len(values) < period or period <= 0:
        return None
    k = 2.0 / (period + 1)
    result = float(values[:period].mean())
    for v in values[period:]:
        result = float(v) * k + result * (1.0 - k)
    return result


def stddev(values: np.ndarray, period: int) -> float | None:
    """Population standard deviation over the last *period* values."""
    if len(values) < period or period <= 0:
        return None
    return float(values[-period:].std(ddof=0))


def bollinger_bands(
    closes: np.ndarray, period: int = 20, num_std: float = 2.0
) -> BollingerBands | None:
    """Bollinger Bands: middle=SMA, upper/lower=middle +/- num_std*stddev."""
    middle = sma(closes, period)
    sd = stddev(closes, period)
    if middle is None or sd is None:
        return None
    upper = middle + num_std * sd
    lower = middle - num_std * sd
    bandwidth = (upper - lower) / middle if middle != 0 else 0.0
    return BollingerBands(upper=upper, middle=middle, lower=lower, bandwidth=bandwidth)


def true_range(high: float, low: float, prev_close: float) -> float:
    """True range for a single bar."""
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float | None:
    """Average true range (SMA of true ranges over *period*)."""
    n = len(highs)
    if n < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return None
    # Vectorized true range: max(high-low, |high-prev_close|, |low-prev_close|)
    h = highs[1:]
    lo = lows[1:]
    pc = closes[:-1]
    tr = np.maximum(h - lo, np.maximum(np.abs(h - pc), np.abs(lo - pc)))
    return sma(tr, period)


def rsi(closes: np.ndarray, period: int = 14) -> float | None:
    """Relative Strength Index using Wilder's smoothing (EMA-style)."""
    if len(closes) < period + 1 or period <= 0:
        return None
    deltas = np.diff(closes)

    gains = np.where(deltas[:period] > 0, deltas[:period], 0.0)
    losses = np.where(deltas[:period] < 0, -deltas[:period], 0.0)
    avg_gain = float(gains.mean())
    avg_loss = float(losses.mean())

    for d in deltas[period:]:
        d = float(d)
        gain = d if d > 0 else 0.0
        loss = -d if d < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def rsi_series(closes: pd.Series, period: int = 14) -> pd.Series:
    """Vectorized RSI using pandas ewm for Wilder's smoothing."""
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)
