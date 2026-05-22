"""v3 microstructure transition features.

Track-isolated copy of v2's microstructure_v2.py. No imports from
crypto_trade.features or crypto_trade.features_v2 permitted in this file.

Features focused on regime transitions and market-structure quality:
    candle_efficiency_20    — directional fraction of intra-bar range
    vol_transition_slope_20 — linear slope of parkinson_vol_20 over 20 bars
    vol_return_divergence_30 — z-scored volume vs abs(return)
    kurt_ratio_50_200       — short-term tail fatness / long-term
    taker_buy_imbalance_20  — 20-bar rolling mean of (tbr - 0.5); iter-v3/063 NEW

References:
    Hasbrouck, J. (1991). Measuring the information content of stock trades.
        Journal of Finance, 46(1), 179-207. (Trade-direction inference.)
    Easley, D., & O'Hara, M. (1992). Time and the process of security price
        adjustment. Journal of Finance, 47(2), 577-605. (PIN / informed trading.)
    Brogaard, J., Hendershott, T., & Riordan, R. (2014). High-frequency trading
        and price discovery. Review of Financial Studies. (Toxic flow.)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_taker_buy_imbalance_20(df: pd.DataFrame) -> pd.DataFrame:
    """Taker-buy imbalance: 20-bar rolling mean of (tbr - 0.5).

    Encodes the Hasbrouck (1991) / Easley-O'Hara (1992) informed-trading proxy:
    when taker buys constitute more than 50% of volume over the trailing 20 bars,
    informed demand is present (positive imbalance); below 50% signals selling
    pressure.

    Construction:
    - ``tbr`` = taker_buy_ratio (taker_buy_base_volume / volume); range [0, 1].
      The raw column is ``tbr_raw`` in V3_NON_FEATURE_COLUMNS (helper column
      computed by add_microstructure_v3_features).
    - ``tbr_raw.shift(1)`` ensures bar t uses tbr at t-1 (past-only; no current bar).
    - ``rolling(20).mean()`` over the shifted series: 20-bar trailing average.
    - ``- 0.5``: centers the feature at 0 (net taker-buy excess; positive = buy
      pressure, negative = sell pressure).

    Output range: approximately [-0.5, +0.5].

    Past-only by construction:
    - ``tbr_raw.shift(1)`` uses bar t-1 (past-only).
    - Rolling mean of 20 bars ending at t-1 uses bars [t-20, t-1] (past-only).
    - Appending future bars does NOT alter the value at t.

    NaN warm-up: first 20 bars are NaN (20-bar rolling window + 1-bar shift = 21
    bars needed before first valid output; actually first bar of shift is NaN so
    effective warm-up is bars 0..20).

    Args:
        df: DataFrame with column ``tbr_raw`` (float, range [0, 1]).

    Returns:
        Copy of ``df`` with ``taker_buy_imbalance_20`` column appended.
        If ``tbr_raw`` is missing, the column is set to all-NaN without error.
    """
    df = df.copy()
    if "tbr_raw" not in df.columns:
        df["taker_buy_imbalance_20"] = np.nan
        return df

    tbr = df["tbr_raw"].astype(float)
    # shift(1): bar t uses tbr at t-1 (past-only; no look-ahead of current bar)
    tbr_lagged = tbr.shift(1)
    df["taker_buy_imbalance_20"] = tbr_lagged.rolling(20, min_periods=20).mean() - 0.5
    return df


def add_microstructure_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"].to_numpy(dtype=np.float64)
    open_ = df["open"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    volume = df["volume"].to_numpy(dtype=np.float64)
    n = len(close)

    # 1. Candle efficiency
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

    # 2. Volatility transition slope
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

    # 3. Volume-return divergence
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

    # 4. Kurtosis ratio
    if "ret_kurt_50" in df.columns and "ret_kurt_200" in df.columns:
        k50 = df["ret_kurt_50"].to_numpy(dtype=np.float64)
        k200 = df["ret_kurt_200"].to_numpy(dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(np.abs(k200) > 0.1, k50 / k200, np.nan)
        df["kurt_ratio_50_200"] = np.clip(ratio, -10.0, 10.0)
    else:
        df["kurt_ratio_50_200"] = np.nan

    # 5. Taker-buy imbalance (iter-v3/063 NEW)
    # Depends on tbr_raw which must be computed before microstructure group runs.
    # tbr_raw is produced by add_microstructure_v3_features itself (below in v2 implementation)
    # OR pre-existing in parquet for v3. For robustness, tbr_raw is computed here if missing.
    if "tbr_raw" not in df.columns:
        # Compute tbr_raw inline: taker_buy_base_volume / volume
        taker_vol = df.get("taker_buy_base_volume", pd.Series(dtype=float))
        vol_series = df.get("volume", pd.Series(dtype=float))
        if len(taker_vol) == n and len(vol_series) == n:
            taker_vol = taker_vol.astype(float).to_numpy()
            vol_np = vol_series.astype(float).to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                tbr_raw = np.where(vol_np > 0, taker_vol / vol_np, np.nan)
            df["tbr_raw"] = tbr_raw

    df = add_taker_buy_imbalance_20(df)

    return df
