"""Volume features: OBV, CMF, MFI, A/D, VWAP, taker buy ratio, volume momentum."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_ta as ta


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~25 volume feature columns to *df*."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    cols: dict[str, pd.Series] = {}

    # OBV
    obv = ta.obv(close, volume)
    if obv is not None:
        cols["vol_obv"] = obv

    # CMF (Chaikin Money Flow)
    for p in (10, 14, 20):
        cmf = ta.cmf(high, low, close, volume, length=p)
        if cmf is not None:
            cols[f"vol_cmf_{p}"] = cmf

    # MFI (Money Flow Index)
    for p in (7, 10, 14, 21):
        mfi = ta.mfi(high, low, close, volume, length=p)
        if mfi is not None:
            cols[f"vol_mfi_{p}"] = mfi

    # Accumulation/Distribution
    ad = ta.ad(high, low, close, volume)
    if ad is not None:
        cols["vol_ad"] = ad

    # VWAP (cumulative approximation)
    typical_price = (high + low + close) / 3
    cols["vol_vwap"] = (typical_price * volume).cumsum() / volume.cumsum().replace(0.0, np.nan)

    # Taker buy ratio
    if "taker_buy_volume" in df.columns:
        taker_ratio = df["taker_buy_volume"] / volume.replace(0.0, np.nan)
        cols["vol_taker_buy_ratio"] = taker_ratio

        # Taker buy ratio SMAs
        for p in (5, 10, 20, 50):
            cols[f"vol_taker_buy_ratio_sma_{p}"] = taker_ratio.rolling(p, min_periods=p).mean()

    # Volume pct_change
    for p in (3, 5, 10, 15, 20, 30):
        cols[f"vol_volume_pctchg_{p}"] = volume.pct_change(p)

    # Volume relative (volume / rolling mean)
    for p in (5, 10, 20, 50):
        rolling_vol = volume.rolling(p, min_periods=p).mean()
        cols[f"vol_volume_rel_{p}"] = volume / rolling_vol.replace(0.0, np.nan)

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
