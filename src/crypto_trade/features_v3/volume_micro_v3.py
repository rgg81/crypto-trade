"""v3 volume-microstructure features — VWAP deviation, volume CV, OBV slope, range ratios.

Track-isolated copy of v2's volume_micro.py. No imports from
crypto_trade.features or crypto_trade.features_v2 permitted in this file.
"""

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
    """Rolling OLS slope (per-bar) over *window*."""
    x = np.arange(window, dtype=np.float64)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()

    def _fit(y: np.ndarray) -> float:
        y_mean = y.mean()
        cov = ((x - x_mean) * (y - y_mean)).sum()
        return cov / x_var if x_var > 0 else np.nan

    return series.rolling(window, min_periods=window).apply(_fit, raw=True)


def add_volume_micro_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add v3 volume-microstructure features to *df*.

    Requires columns: open, high, low, close, volume.
    """
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    atr20 = _atr(high, low, close, period=20).replace(0, np.nan)

    vwap20 = _rolling_vwap(close, volume, 20)
    vwap50 = _rolling_vwap(close, volume, 50)
    df["vwap_dev_20"] = (close - vwap20) / atr20
    df["vwap_dev_50"] = (close - vwap50) / atr20

    vol10 = volume.rolling(10, min_periods=5).mean()
    vol50 = volume.rolling(50, min_periods=25).mean()
    df["volume_mom_ratio_20"] = vol10 / vol50.replace(0, np.nan)

    vol_mean50 = volume.rolling(50, min_periods=25).mean()
    vol_std50 = volume.rolling(50, min_periods=25).std()
    df["volume_cv_50"] = vol_std50 / vol_mean50.replace(0, np.nan)

    signed_vol = np.sign(close.diff()).fillna(0) * volume
    obv = signed_vol.cumsum()
    obv_slope = _rolling_slope(obv, 50)
    df["obv_slope_50"] = obv_slope / obv.abs().rolling(50, min_periods=25).mean().replace(0, np.nan)

    hl = high - low
    df["hl_range_ratio_20"] = hl / hl.rolling(20, min_periods=10).mean().replace(0, np.nan)

    # close_pos_in_range columns computed but not in V3_FEATURE_COLUMNS (dropped in v2/069)
    high20 = high.rolling(20, min_periods=10).max()
    low20 = low.rolling(20, min_periods=10).min()
    df["close_pos_in_range_20"] = (close - low20) / (high20 - low20).replace(0, np.nan)
    high50 = high.rolling(50, min_periods=25).max()
    low50 = low.rolling(50, min_periods=25).min()
    df["close_pos_in_range_50"] = (close - low50) / (high50 - low50).replace(0, np.nan)

    # Taker-buy ratio z-score — iter-v3/015 NEW microstructure feature family
    df = compute_tbr_zscore(df, window=30)

    return df


def compute_tbr_zscore(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Compute taker-buy ratio z-score over a rolling window (past-only).

    ``tbr_zscore_30`` = z-score of (taker_buy_quote_volume / quote_volume)
    over a rolling ``window``-bar window.  All ops are strictly past-only:
    the z-score at bar t uses bars t-window...t-1 via ``.shift(1)`` before
    rolling stats, so the bar's own taker volume is excluded.

    Mirrors the reference implementation in
    ``analysis/iteration_v3-015/tbr_zscore_eda.py`` (SHA fcf6b06).

    Parameters
    ----------
    df:
        DataFrame with columns ``taker_buy_quote_volume`` and ``quote_volume``.
    window:
        Rolling window in bars (default 30 = ~10 days at 8h cadence).

    Returns
    -------
    pd.DataFrame
        Input df with ``tbr_zscore_30`` column appended.  ``tbr_raw`` is also
        written as an intermediate (not in V3_FEATURE_COLUMNS).
    """
    qv = df["quote_volume"].astype(float)
    tbqv = df["taker_buy_quote_volume"].astype(float)

    # Raw ratio in [0, 1]; NaN where quote_volume == 0 (rare edge)
    tbr_raw = np.where(qv > 0, tbqv / qv, np.nan)
    df["tbr_raw"] = tbr_raw

    # Rolling stats shifted by 1 — bar t uses bars t-window...t-1 only
    s = pd.Series(tbr_raw, index=df.index)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    df["tbr_zscore_30"] = (s_shifted - rmean) / rstd.replace(0, np.nan)

    return df
