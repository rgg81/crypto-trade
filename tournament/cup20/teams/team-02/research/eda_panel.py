"""Build a point-in-time 8h panel for team-02 EDA (IS snapshot only).

Everything here is read-only research over data/cup20/is/. No trial is consumed by this file;
it never touches the organiser scorer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"


def load_panel() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bars = pd.read_parquet(f"{IS_ROOT}/bars.parquet")
    membership = pd.read_parquet(f"{IS_ROOT}/membership.parquet")
    funding = pd.read_parquet(f"{IS_ROOT}/funding.parquet")
    return bars, membership, funding


def wide(bars: pd.DataFrame, column: str) -> pd.DataFrame:
    return bars.pivot(index="open_time", columns="symbol", values=column).sort_index()


def eligibility_mask(membership: pd.DataFrame, index: pd.DatetimeIndex,
                     columns: pd.Index) -> pd.DataFrame:
    """True where the symbol is a point-in-time member at that 8h boundary."""
    memb = membership.copy()
    memb["one"] = True
    weekly = memb.pivot_table(
        index="reconstitution_time", columns="symbol", values="one", aggfunc="first"
    )
    weekly = weekly.reindex(columns=columns).fillna(False).astype(bool)
    # membership row at time R governs decisions at t >= R (point-in-time, already causal)
    mask = weekly.reindex(weekly.index.union(index)).ffill().reindex(index)
    return mask.fillna(False).astype(bool)


def true_range(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    prev = close.shift(1)
    a = high - low
    b = (high - prev).abs()
    c = (low - prev).abs()
    return pd.concat([a, b, c]).groupby(level=0).max()


def channel_position(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame,
                     n: int) -> pd.DataFrame:
    """Donchian %-position of the last close inside the trailing n-bar high/low channel.

    The channel is formed from bars strictly before the current one plus the current one's own
    close, i.e. only information available at the decision.
    """
    hh = high.rolling(n, min_periods=n).max()
    ll = low.rolling(n, min_periods=n).min()
    width = hh - ll
    pos = (close - ll) / width.where(width > 0)
    return pos.clip(0.0, 1.0)


def summarise_ic(score: pd.DataFrame, fwd: pd.DataFrame, mask: pd.DataFrame,
                 label: str, min_names: int = 8) -> dict:
    s = score.where(mask)
    f = fwd.where(mask)
    both = s.notna() & f.notna()
    s = s.where(both)
    f = f.where(both)
    counts = both.sum(axis=1)
    ok = counts >= min_names
    s, f = s[ok], f[ok]
    rs = s.rank(axis=1)
    rf = f.rank(axis=1)
    rs = rs.sub(rs.mean(axis=1), axis=0)
    rf = rf.sub(rf.mean(axis=1), axis=0)
    num = (rs * rf).sum(axis=1)
    den = np.sqrt((rs**2).sum(axis=1) * (rf**2).sum(axis=1))
    ic = num / den.where(den > 0)
    ic = ic.dropna()
    return {
        "label": label,
        "n_obs": int(len(ic)),
        "ic_mean": float(ic.mean()),
        "ic_std": float(ic.std()),
        "ic_t": float(ic.mean() / ic.std() * np.sqrt(len(ic))) if len(ic) > 2 else np.nan,
        "ic_pos_frac": float((ic > 0).mean()),
    }
