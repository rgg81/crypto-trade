"""Statistical features: returns, log returns, autocorrelation, skewness, kurtosis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_statistical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ~25 statistical feature columns to *df*."""
    close = df["close"]
    cols: dict[str, pd.Series] = {}

    # Returns (pct_change)
    for p in (1, 2, 3, 5, 10, 15, 20, 30):
        cols[f"stat_return_{p}"] = close.pct_change(p)

    # Log returns
    for p in (1, 3, 5, 10, 20):
        cols[f"stat_log_return_{p}"] = np.log(close / close.shift(p))

    # Autocorrelation (rolling)
    window = 50
    for lag in (1, 5, 10):
        cols[f"stat_autocorr_lag{lag}"] = (
            close.pct_change().rolling(window).apply(lambda x: x.autocorr(lag=lag), raw=False)
        )

    # Rolling skewness
    for p in (10, 20, 30, 50):
        cols[f"stat_skew_{p}"] = close.pct_change().rolling(p).skew()

    # Rolling kurtosis
    for p in (10, 20, 30, 50):
        cols[f"stat_kurtosis_{p}"] = close.pct_change().rolling(p).kurt()

    return pd.concat([df, pd.DataFrame(cols, index=df.index)], axis=1)
