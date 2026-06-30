"""Equity-native neutralizers for the tradfi book: dollar / beta / sector.

All are leak-safe row-wise transforms on a raw-weight panel (index = daily DatetimeIndex,
columns = tickers). rolling_beta uses only past returns (no .shift into the future).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def dollar_neutralize(raw: pd.DataFrame) -> pd.DataFrame:
    """Subtract each row's cross-sectional mean so longs$ == shorts$ (net dollar = 0)."""
    return raw.sub(raw.mean(axis=1), axis=0)


def rolling_beta(ret: pd.DataFrame, mkt: pd.Series, win: int = 63) -> pd.DataFrame:
    """Past-only rolling beta of each column's returns to the market proxy `mkt`.

    beta = Cov(asset, mkt) / Var(mkt) over a trailing `win` window. The final window ends at
    the current bar (no forward leak); callers .shift(1) before USING betas to size bar t+1.
    """
    var = mkt.rolling(win).var()
    out = {}
    for c in ret.columns:
        out[c] = ret[c].rolling(win).cov(mkt) / var
    return pd.DataFrame(out, index=ret.index)


def beta_neutralize(raw: pd.DataFrame, betas: pd.DataFrame) -> pd.DataFrame:
    """Remove each row's net market-beta exposure: raw - (Σ w·β / Σ β²)·β.

    Projects the weight vector off the beta vector per row (least-squares hedge of the market
    factor). betas must be past-only and aligned to raw; rows with no beta are left unchanged.
    """
    b = betas.reindex_like(raw)
    num = (raw * b).sum(axis=1)
    den = (b * b).sum(axis=1).replace(0, np.nan)
    k = (num / den).fillna(0.0)
    return raw.sub(b.mul(k, axis=0), axis=0)


def sector_neutralize(raw: pd.DataFrame, sector_map: dict[str, str]) -> pd.DataFrame:
    """Demean weights WITHIN each sector bucket so every sector is net-zero dollar.

    Columns absent from sector_map are treated as their own singleton sector (-> forced to 0,
    which is the safe default: an unmapped name takes no position).
    """
    out = raw.copy()
    sectors: dict[str, list[str]] = {}
    for c in raw.columns:
        sectors.setdefault(sector_map.get(c, f"__{c}"), []).append(c)
    for cols in sectors.values():
        block = raw[cols]
        out[cols] = block.sub(block.mean(axis=1), axis=0)
    return out
