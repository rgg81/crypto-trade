"""Shared EDA panel builder for team-04 (market-residual cross-sectional momentum).

Builds the exact past-only view the organiser's runner streams: 8h decision grid, weekly
point-in-time membership intersected with symbols that have an executable open at the decision.
Nothing here scores anything -- scoring is the organiser's command. This is EDA only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"


def load_panel():
    bars = pd.read_parquet(f"{IS_ROOT}/bars.parquet")
    membership = pd.read_parquet(f"{IS_ROOT}/membership.parquet")

    bars = bars.sort_values(["open_time", "symbol"])
    opens = bars.pivot(index="open_time", columns="symbol", values="open").sort_index()
    closes = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    qv = bars.pivot(index="open_time", columns="symbol", values="quote_volume").sort_index()

    grid = opens.index  # every 8h open_time present in the snapshot
    symbols = list(opens.columns)

    # membership: forward-fill the weekly constituent set onto the 8h grid
    memb = np.zeros((len(grid), len(symbols)), dtype=bool)
    recon_times = pd.DatetimeIndex(sorted(membership["reconstitution_time"].unique()))
    sym_index = {s: j for j, s in enumerate(symbols)}
    sets = {
        pd.Timestamp(t): [sym_index[s] for s in g["symbol"] if s in sym_index]
        for t, g in membership.groupby("reconstitution_time")
    }
    pos = recon_times.searchsorted(grid, side="right") - 1
    for i, p in enumerate(pos):
        if p < 0:
            continue
        memb[i, sets[pd.Timestamp(recon_times[p])]] = True

    has_open = opens.notna().to_numpy()
    eligible = memb & has_open

    is_start = pd.Timestamp(
        membership.groupby("reconstitution_time").size().pipe(lambda s: s[s >= 20].index[0])
    )
    return {
        "grid": grid,
        "symbols": symbols,
        "opens": opens,
        "closes": closes,
        "quote_volume": qv,
        "eligible": eligible,
        "is_start": is_start,
    }


def log_returns(closes: pd.DataFrame) -> np.ndarray:
    """Log return of the bar CLOSING at each grid stamp+8h, aligned to its open_time row.

    Row i holds log(close_i / close_{i-1}); at decision time t = open_time_i + 8h this row is the
    most recent fully closed bar, so a signal at decision i+1 may use rows <= i.
    """
    c = closes.to_numpy(dtype=float)
    out = np.full_like(c, np.nan)
    out[1:] = np.log(c[1:] / c[:-1])
    return out


def rolling_sum(x: np.ndarray, window: int) -> np.ndarray:
    """Trailing sum over `window` rows, NaN-aware (NaN treated as absent -> result NaN)."""
    filled = np.nan_to_num(x, nan=0.0)
    valid = (~np.isnan(x)).astype(float)
    cs = np.cumsum(filled, axis=0)
    cv = np.cumsum(valid, axis=0)
    out = np.full_like(x, np.nan)
    out[window - 1 :] = cs[window - 1 :] - np.vstack([np.zeros((1, x.shape[1])), cs[:-window]])
    cnt = np.full_like(x, np.nan)
    cnt[window - 1 :] = cv[window - 1 :] - np.vstack([np.zeros((1, x.shape[1])), cv[:-window]])
    out[cnt < window] = np.nan
    return out
