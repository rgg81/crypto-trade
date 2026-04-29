"""v2 tail-risk features — rolling skew/kurt + realized vol + max drawdown."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _rolling_max_dd(close: pd.Series, window: int) -> pd.Series:
    """Rolling max drawdown of close over *window*, expressed as fraction (negative)."""
    rolling_max = close.rolling(window, min_periods=max(5, window // 4)).max()
    return (close / rolling_max - 1.0).rolling(window, min_periods=max(5, window // 4)).min()


def _range_realized_vol(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    """Realized vol estimator via log high/low range (Garman-Klass intermediate)."""
    hl = np.log(high.clip(lower=1e-12) / low.clip(lower=1e-12))
    return np.sqrt((hl**2).rolling(window, min_periods=window // 2).mean() / (4.0 * np.log(2.0)))


def add_tail_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 tail-risk features to *df*.

    Requires columns: high, low, close.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    log_returns = np.log(close.clip(lower=1e-12)).diff()

    df["ret_skew_50"] = log_returns.rolling(50, min_periods=25).skew()
    df["ret_skew_100"] = log_returns.rolling(100, min_periods=50).skew()
    df["ret_skew_200"] = log_returns.rolling(200, min_periods=100).skew()

    df["ret_kurt_50"] = log_returns.rolling(50, min_periods=25).kurt()
    df["ret_kurt_200"] = log_returns.rolling(200, min_periods=100).kurt()

    df["range_realized_vol_50"] = _range_realized_vol(high, low, 50)
    df["max_dd_window_50"] = _rolling_max_dd(close, 50)

    return df
