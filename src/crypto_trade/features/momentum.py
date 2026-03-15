"""Momentum features: RSI, MACD, Stochastic, Williams %R, ROC, MOM."""

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~30 momentum feature columns to *df*."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    cols: dict[str, pd.Series] = {}

    # RSI
    for p in (5, 7, 9, 14, 21, 30):
        cols[f"mom_rsi_{p}"] = ta.rsi(close, length=p)

    # MACD (line, histogram, signal)
    for fast, slow, signal in ((8, 21, 5), (12, 26, 9), (5, 13, 3)):
        macd_df = ta.macd(close, fast=fast, slow=slow, signal=signal)
        if macd_df is not None:
            for col in macd_df.columns:
                if col.startswith("MACD_"):
                    cols[f"mom_macd_line_{fast}_{slow}_{signal}"] = macd_df[col]
                elif col.startswith("MACDh_"):
                    cols[f"mom_macd_hist_{fast}_{slow}_{signal}"] = macd_df[col]
                elif col.startswith("MACDs_"):
                    cols[f"mom_macd_signal_{fast}_{slow}_{signal}"] = macd_df[col]

    # Stochastic %K, %D
    for k in (5, 9, 14, 21):
        stoch_df = ta.stoch(high, low, close, k=k, d=3, smooth_k=3)
        if stoch_df is not None:
            stoch_cols = list(stoch_df.columns)
            if len(stoch_cols) >= 2:
                cols[f"mom_stoch_k_{k}"] = stoch_df[stoch_cols[0]]
                cols[f"mom_stoch_d_{k}"] = stoch_df[stoch_cols[1]]

    # Williams %R
    for p in (7, 14, 21):
        cols[f"mom_willr_{p}"] = ta.willr(high, low, close, length=p)

    # Rate of Change
    for p in (3, 5, 10, 15, 20, 30):
        cols[f"mom_roc_{p}"] = ta.roc(close, length=p)

    # Momentum
    for p in (5, 10, 15, 20):
        cols[f"mom_mom_{p}"] = ta.mom(close, length=p)

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
