"""v2 momentum-acceleration features — acceleration, EMA spread, autocorrelation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _momentum(close: pd.Series, n: int) -> pd.Series:
    """Log momentum over *n* bars."""
    return np.log(close.clip(lower=1e-12) / close.shift(n).clip(lower=1e-12))


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _rolling_autocorr(series: pd.Series, window: int, lag: int) -> pd.Series:
    """Rolling Pearson autocorrelation at lag *lag* over trailing *window* bars."""
    shifted = series.shift(lag)
    return series.rolling(window, min_periods=window // 2).corr(shifted)


def add_momentum_accel_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 momentum-acceleration features to *df*.

    Requires columns: high, low, close.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    log_returns = np.log(close.clip(lower=1e-12)).diff()

    mom5 = _momentum(close, 5)
    mom20 = _momentum(close, 20)
    mom100 = _momentum(close, 100)

    # Acceleration vs baseline momentum (denominator clipped to avoid division by zero)
    df["mom_accel_5_20"] = (mom5 - mom20) / mom20.abs().clip(lower=1e-6)
    df["mom_accel_20_100"] = (mom20 - mom100) / mom100.abs().clip(lower=1e-6)

    # EMA spread normalized by ATR (vol-scaled trend strength)
    ema10 = close.ewm(span=10, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    atr20 = _atr(high, low, close, period=20)
    df["ema_spread_atr_20"] = (ema10 - ema50) / atr20.replace(0, np.nan)

    # Return autocorrelation
    df["ret_autocorr_lag1_50"] = _rolling_autocorr(log_returns, window=50, lag=1)
    df["ret_autocorr_lag5_50"] = _rolling_autocorr(log_returns, window=50, lag=5)

    return df
