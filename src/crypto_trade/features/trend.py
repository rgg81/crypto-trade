"""Trend features: ADX, Aroon, EMA/SMA, crossovers, Supertrend, PSAR."""

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def add_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~30 trend feature columns to *df*."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    cols: dict[str, pd.Series] = {}

    # ADX (ADX, +DI, -DI)
    for p in (7, 14, 21):
        adx_df = ta.adx(high, low, close, length=p)
        if adx_df is not None:
            for col in adx_df.columns:
                if col.startswith("ADX_"):
                    cols[f"trend_adx_{p}"] = adx_df[col]
                elif col.startswith("DMP_"):
                    cols[f"trend_plus_di_{p}"] = adx_df[col]
                elif col.startswith("DMN_"):
                    cols[f"trend_minus_di_{p}"] = adx_df[col]

    # Aroon (up, down, oscillator)
    for p in (14, 25, 50):
        aroon_df = ta.aroon(high, low, length=p)
        if aroon_df is not None:
            for col in aroon_df.columns:
                if col.startswith("AROONU_"):
                    cols[f"trend_aroon_up_{p}"] = aroon_df[col]
                elif col.startswith("AROOND_"):
                    cols[f"trend_aroon_down_{p}"] = aroon_df[col]
                elif col.startswith("AROONOSC_"):
                    cols[f"trend_aroon_osc_{p}"] = aroon_df[col]

    # EMA
    emas: dict[int, pd.Series] = {}
    for p in (5, 9, 12, 21, 50, 100):
        result = ta.ema(close, length=p)
        if result is not None:
            emas[p] = result
            cols[f"trend_ema_{p}"] = result

    # SMA
    smas: dict[int, pd.Series] = {}
    for p in (10, 20, 50, 100):
        result = ta.sma(close, length=p)
        if result is not None:
            smas[p] = result
            cols[f"trend_sma_{p}"] = result

    # EMA cross signals (fast - slow, normalized by close)
    for fast, slow in ((5, 12), (9, 21), (12, 50)):
        ema_fast = emas.get(fast, ta.ema(close, length=fast))
        ema_slow = emas.get(slow, ta.ema(close, length=slow))
        if ema_fast is not None and ema_slow is not None:
            cols[f"trend_ema_cross_{fast}_{slow}"] = (ema_fast - ema_slow) / close

    # SMA cross signals
    for fast, slow in ((10, 50), (20, 50), (20, 100)):
        sma_fast = smas.get(fast, ta.sma(close, length=fast))
        sma_slow = smas.get(slow, ta.sma(close, length=slow))
        if sma_fast is not None and sma_slow is not None:
            cols[f"trend_sma_cross_{fast}_{slow}"] = (sma_fast - sma_slow) / close

    # Supertrend direction
    for length, mult in ((7, 3.0), (10, 2.0), (14, 3.0)):
        st = ta.supertrend(high, low, close, length=length, multiplier=mult)
        if st is not None:
            for col in st.columns:
                if col.startswith("SUPERTd_"):
                    cols[f"trend_supertrend_{length}_{mult:.0f}"] = st[col]

    # Parabolic SAR direction (1 = bullish, -1 = bearish)
    psar = ta.psar(high, low, close)
    if psar is not None:
        for col in psar.columns:
            if col.startswith("PSARaf_"):
                cols["trend_psar_af"] = psar[col]
        psar_long = None
        for col in psar.columns:
            if col.startswith("PSARl_"):
                psar_long = psar[col]
        if psar_long is not None:
            cols["trend_psar_dir"] = psar_long.notna().astype(int) * 2 - 1

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
