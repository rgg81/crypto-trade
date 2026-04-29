"""v2 volume-microstructure features — VWAP deviation, volume CV, OBV slope, range ratios."""

from __future__ import annotations

import numpy as np
import pandas as pd


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


def _rolling_vwap(close: pd.Series, volume: pd.Series, window: int) -> pd.Series:
    typical = close
    vol_x_price = (typical * volume).rolling(window, min_periods=window // 2).sum()
    vol_sum = volume.rolling(window, min_periods=window // 2).sum()
    return vol_x_price / vol_sum.replace(0, np.nan)


def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
    """Rolling OLS slope (per-bar) over *window*, using the linear regression of y vs index."""
    x = np.arange(window, dtype=np.float64)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()

    def _fit(y: np.ndarray) -> float:
        # y length is always *window* because we require min_periods == window
        y_mean = y.mean()
        cov = ((x - x_mean) * (y - y_mean)).sum()
        return cov / x_var if x_var > 0 else np.nan

    return series.rolling(window, min_periods=window).apply(_fit, raw=True)


def add_volume_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v2 volume-microstructure features to *df*.

    Requires columns: open, high, low, close, volume.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    atr20 = _atr(high, low, close, period=20).replace(0, np.nan)

    # VWAP deviation in volatility units
    vwap20 = _rolling_vwap(close, volume, 20)
    vwap50 = _rolling_vwap(close, volume, 50)
    df["vwap_dev_20"] = (close - vwap20) / atr20
    df["vwap_dev_50"] = (close - vwap50) / atr20

    # Volume momentum ratio: short/long volume mean
    vol10 = volume.rolling(10, min_periods=5).mean()
    vol50 = volume.rolling(50, min_periods=25).mean()
    df["volume_mom_ratio_20"] = vol10 / vol50.replace(0, np.nan)

    # Volume coefficient of variation (activity consistency)
    vol_mean50 = volume.rolling(50, min_periods=25).mean()
    vol_std50 = volume.rolling(50, min_periods=25).std()
    df["volume_cv_50"] = vol_std50 / vol_mean50.replace(0, np.nan)

    # OBV slope, normalized by mean absolute OBV
    signed_vol = np.sign(close.diff()).fillna(0) * volume
    obv = signed_vol.cumsum()
    obv_slope = _rolling_slope(obv, 50)
    df["obv_slope_50"] = obv_slope / obv.abs().rolling(50, min_periods=25).mean().replace(
        0, np.nan
    )

    # Intrabar dispersion relative to rolling mean (stationary ratio)
    hl = high - low
    df["hl_range_ratio_20"] = hl / hl.rolling(20, min_periods=10).mean().replace(0, np.nan)

    # Close position within the rolling bar range (0 = at low, 1 = at high)
    high20 = high.rolling(20, min_periods=10).max()
    low20 = low.rolling(20, min_periods=10).min()
    df["close_pos_in_range_20"] = (close - low20) / (high20 - low20).replace(0, np.nan)
    high50 = high.rolling(50, min_periods=25).max()
    low50 = low.rolling(50, min_periods=25).min()
    df["close_pos_in_range_50"] = (close - low50) / (high50 - low50).replace(0, np.nan)

    return df
