"""iter-v2/039: microstructure transition features.

Four scale-invariant features focused on regime transitions and
market-structure quality — areas not covered by the existing v2 catalog.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_microstructure_v2_features(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"].to_numpy(dtype=np.float64)
    open_ = df["open"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    volume = df["volume"].to_numpy(dtype=np.float64)
    n = len(close)

    # 1. Candle efficiency: how much of the intra-bar range is directional
    # (close-open) / (high-low), clipped to [-1, 1]. Rolling mean over 20 bars.
    bar_range = high - low
    bar_range[bar_range == 0] = np.nan
    raw_eff = (close - open_) / bar_range
    raw_eff = np.clip(raw_eff, -1.0, 1.0)
    candle_eff = np.full(n, np.nan)
    for i in range(19, n):
        window = raw_eff[i - 19 : i + 1]
        valid = window[~np.isnan(window)]
        if len(valid) >= 10:
            candle_eff[i] = float(np.mean(valid))
    df["candle_efficiency_20"] = candle_eff

    # 2. Volatility transition slope: linear regression slope of
    # parkinson_vol_20 over the last 20 bars, normalized by its mean.
    if "parkinson_vol_20" in df.columns:
        pvol = df["parkinson_vol_20"].to_numpy(dtype=np.float64)
    else:
        hl_ratio = np.log(high / low)
        hl_ratio[hl_ratio == 0] = np.nan
        pvol_raw = hl_ratio**2 / (4 * np.log(2))
        pvol = np.full(n, np.nan)
        for i in range(19, n):
            window = pvol_raw[i - 19 : i + 1]
            valid = window[~np.isnan(window)]
            if len(valid) >= 10:
                pvol[i] = float(np.sqrt(np.mean(valid)))

    x = np.arange(20, dtype=np.float64)
    x_mean = x.mean()
    x_var = float(np.sum((x - x_mean) ** 2))
    vol_slope = np.full(n, np.nan)
    for i in range(19, n):
        window = pvol[i - 19 : i + 1]
        if np.any(np.isnan(window)):
            continue
        w_mean = float(np.mean(window))
        if w_mean == 0:
            continue
        slope = float(np.sum((x - x_mean) * (window - w_mean)) / x_var)
        vol_slope[i] = slope / w_mean
    df["vol_transition_slope_20"] = vol_slope

    # 3. Volume-return divergence: z-scored volume momentum vs z-scored
    # abs(return). When volume surges but return is small → distribution
    # event. When return is large on low volume → hollow move.
    log_ret = np.concatenate([[np.nan], np.diff(np.log(close))])
    abs_ret = np.abs(log_ret)

    vol_div = np.full(n, np.nan)
    window_size = 30
    for i in range(window_size - 1, n):
        vol_w = volume[i - window_size + 1 : i + 1]
        ret_w = abs_ret[i - window_size + 1 : i + 1]
        if np.any(np.isnan(ret_w)) or np.any(np.isnan(vol_w)):
            continue
        vol_std = float(np.std(vol_w))
        ret_std = float(np.std(ret_w))
        if vol_std == 0 or ret_std == 0:
            continue
        vol_z = (vol_w[-1] - float(np.mean(vol_w))) / vol_std
        ret_z = (ret_w[-1] - float(np.mean(ret_w))) / ret_std
        if ret_z == 0:
            continue
        vol_div[i] = vol_z / ret_z
    df["vol_return_divergence_30"] = np.clip(vol_div, -5.0, 5.0)

    # 4. Kurtosis ratio: short-term tail fatness / long-term.
    # Spike → short-term distribution sharpening.
    if "ret_kurt_50" in df.columns and "ret_kurt_200" in df.columns:
        k50 = df["ret_kurt_50"].to_numpy(dtype=np.float64)
        k200 = df["ret_kurt_200"].to_numpy(dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(np.abs(k200) > 0.1, k50 / k200, np.nan)
        df["kurt_ratio_50_200"] = np.clip(ratio, -10.0, 10.0)
    else:
        df["kurt_ratio_50_200"] = np.nan

    return df
