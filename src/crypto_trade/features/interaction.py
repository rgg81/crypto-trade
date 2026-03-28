"""Interaction features: products of momentum, volatility, and trend indicators."""

from __future__ import annotations

import pandas as pd
import pandas_ta as ta


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction feature columns (products of base indicators)."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    cols: dict[str, pd.Series] = {}

    # Base indicators (compute inline to avoid dependency on other modules)
    rsi_14 = ta.rsi(close, length=14)
    adx_df = ta.adx(high, low, close, length=14)
    adx_14 = adx_df.iloc[:, 0] if adx_df is not None else pd.Series(0, index=df.index)

    atr_14 = ta.atr(high, low, close, length=14)
    natr_14 = atr_14 / close * 100 if atr_14 is not None else pd.Series(0, index=df.index)

    # Stochastic %K
    stoch_df = ta.stoch(high, low, close, k=14, d=3, smooth_k=3)
    stoch_k = stoch_df.iloc[:, 0] if stoch_df is not None else pd.Series(50, index=df.index)

    # Returns
    ret_1 = close.pct_change(1) * 100
    ret_3 = close.pct_change(3) * 100

    # --- Interaction products (all scale-invariant) ---

    # Momentum × Trend strength: strong trend + extreme RSI = stronger signal
    cols["interact_rsi_x_adx"] = (rsi_14 - 50) * adx_14 / 100  # centered RSI × ADX
    cols["interact_stoch_x_adx"] = (stoch_k - 50) * adx_14 / 100

    # Volatility × Trend: volatile + trending = directional move
    cols["interact_natr_x_adx"] = natr_14 * adx_14

    # Momentum × Volatility: extreme momentum in volatile market
    cols["interact_rsi_x_natr"] = (rsi_14 - 50) * natr_14 / 100
    cols["interact_ret1_x_natr"] = ret_1 * natr_14

    # Return persistence: current return × recent return (momentum confirmation)
    cols["interact_ret1_x_ret3"] = ret_1 * ret_3

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
