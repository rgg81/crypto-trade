"""v2 regime features — Hurst, ATR percentile rank, BB width rank, CUSUM reset count.

Also exports a ``natr_21_raw`` helper column used by the shared labeling code
(``LightGbmStrategy.atr_column``) to compute ATR-scaled triple barriers. That
column is NOT in the v2 feature catalog — it is only a labeling input — and
must be excluded from the LightGBM feature columns list.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    tr = _true_range(high, low, close)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _hurst_rs(window: np.ndarray) -> float:
    """Rescaled-range Hurst exponent for a single 1D window of log prices."""
    n = len(window)
    if n < 20:
        return np.nan
    lags = [5, 10, 20, 30, 50, 80]
    lags = [lag for lag in lags if lag < n]
    if len(lags) < 3:
        return np.nan
    rs_values: list[float] = []
    log_lags: list[float] = []
    for lag in lags:
        chunks = n // lag
        if chunks < 1:
            continue
        r_list: list[float] = []
        for i in range(chunks):
            chunk = window[i * lag : (i + 1) * lag]
            mean = chunk.mean()
            devs = chunk - mean
            cumdev = np.cumsum(devs)
            r = cumdev.max() - cumdev.min()
            s = chunk.std(ddof=1)
            if s > 0 and np.isfinite(r):
                r_list.append(r / s)
        if r_list:
            rs_values.append(np.mean(r_list))
            log_lags.append(np.log(lag))
    if len(rs_values) < 3:
        return np.nan
    log_rs = np.log(rs_values)
    slope, _ = np.polyfit(log_lags, log_rs, 1)
    return float(slope)


def _rolling_hurst(log_close: pd.Series, window: int) -> pd.Series:
    """Rolling Hurst exponent via rescaled range. Returns NaN until window filled."""
    values = log_close.to_numpy()
    out = np.full(len(values), np.nan, dtype=np.float64)
    for i in range(window, len(values) + 1):
        out[i - 1] = _hurst_rs(values[i - window : i])
    return pd.Series(out, index=log_close.index)


def _pct_rank(series: pd.Series, window: int) -> pd.Series:
    """Rolling percentile rank — current value vs last *window* observations. 0-1 scale."""
    return series.rolling(window, min_periods=max(20, window // 5)).apply(
        lambda x: (x < x[-1]).sum() / (len(x) - 1) if len(x) > 1 else 0.5,
        raw=True,
    )


def _cusum_reset_count(log_returns: pd.Series, window: int, threshold: float = 2.0) -> pd.Series:
    """Count CUSUM resets in the trailing *window* bars, divided by window.

    A reset occurs whenever the positive or negative CUSUM exceeds *threshold*
    standard deviations of the rolling mean-zero return series, at which point
    the corresponding accumulator returns to zero.
    """
    std = log_returns.rolling(window).std()
    mean = log_returns.rolling(window).mean()
    z = (log_returns - mean) / std

    s_pos = 0.0
    s_neg = 0.0
    reset_flag = np.zeros(len(log_returns), dtype=np.float64)
    z_arr = z.to_numpy()
    for i, zi in enumerate(z_arr):
        if not np.isfinite(zi):
            s_pos = 0.0
            s_neg = 0.0
            continue
        s_pos = max(0.0, s_pos + zi - 0.5)
        s_neg = max(0.0, s_neg - zi - 0.5)
        if s_pos > threshold or s_neg > threshold:
            reset_flag[i] = 1.0
            s_pos = 0.0
            s_neg = 0.0

    flags = pd.Series(reset_flag, index=log_returns.index)
    return flags.rolling(window, min_periods=window // 2).sum() / window


def add_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 regime features to *df*.

    Requires columns: open, high, low, close.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    log_returns = log_close.diff()

    # Rolling Hurst
    df["hurst_100"] = _rolling_hurst(log_close, 100)
    df["hurst_200"] = _rolling_hurst(log_close, 200)
    df["hurst_diff_100_50"] = df["hurst_100"] - _rolling_hurst(log_close, 50)

    # ATR percentile ranks (raw ATR is a helper only)
    atr14 = _atr(high, low, close, period=14)
    df["atr_pct_rank_200"] = _pct_rank(atr14, 200)
    df["atr_pct_rank_500"] = _pct_rank(atr14, 500)
    df["atr_pct_rank_1000"] = _pct_rank(atr14, 1000)

    # Helper column for labeling (NOT a feature — excluded from feature_columns).
    # Expressed in PERCENTAGE units to match v1's ``vol_natr_21`` convention so
    # LightGbmStrategy._load_atr_for_master can reuse its close * natr / 100 math.
    df["natr_21_raw"] = 100.0 * _atr(high, low, close, period=21) / close.clip(lower=1e-12)

    # Bollinger Band width percentile
    mid20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_width = (2.0 * 2.0 * std20) / mid20.replace(0, np.nan)
    df["bb_width_pct_rank_100"] = _pct_rank(bb_width, 100)

    # CUSUM reset count
    df["cusum_reset_count_200"] = _cusum_reset_count(log_returns, 200, threshold=2.0)

    return df
