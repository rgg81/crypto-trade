"""Panel builder for team-10 offline research.

Loads the IS snapshot once and materialises aligned (time x symbol) matrices on the 8h decision
grid, plus the causal eligibility mask. Everything downstream reads these arrays; nothing
downstream re-reads parquet.

Nothing here decides anything. It is arithmetic on the rows the organiser handed us.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd

IS_ROOT = Path("data/cup20/is")
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
INTERVAL_HOURS = 8


@dataclasses.dataclass(frozen=True)
class Panel:
    times: pd.DatetimeIndex  # decision grid, length T
    symbols: tuple[str, ...]  # length S
    open: np.ndarray  # (T, S) open at the boundary; NaN if no bar
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    mark: np.ndarray  # (T, S) boundary mark price
    quote_volume: np.ndarray  # (T, S)
    trade_count: np.ndarray
    taker_buy_quote: np.ndarray
    fund_at: np.ndarray  # (T, S) sum(mark*rate) settling exactly at the boundary
    fund_in: np.ndarray  # (T, S) sum(mark*rate) settling strictly inside (t, t+1)
    member: np.ndarray  # (T, S) bool: weekly membership at t (point-in-time)
    eligible: np.ndarray  # (T, S) bool: member AND has an executable open at t


def _grid(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq=f"{INTERVAL_HOURS}h", inclusive="left")


def build_panel(root: Path = IS_ROOT) -> Panel:
    bars = pd.read_parquet(root / "bars.parquet")
    funding = pd.read_parquet(root / "funding.parquet")
    marks = pd.read_parquet(root / "mark_prices.parquet")
    membership = pd.read_parquet(root / "membership.parquet")

    for frame, col in ((bars, "open_time"), (marks, "mark_time"), (membership, "reconstitution_time")):
        frame[col] = pd.to_datetime(frame[col], utc=True)
    funding["funding_time"] = pd.to_datetime(funding["funding_time"], utc=True)
    # The organiser floors funding_time to the hour to get the settlement instant; funding_time
    # itself lands milliseconds after it on many rows, so selecting on funding_time is wrong.
    funding["settlement_time"] = funding["funding_time"].dt.floor("h")

    # IS_START is computed, not chosen: the first reconstitution boundary reaching 20 names.
    counts = membership.groupby("reconstitution_time").size().sort_index()
    is_start = pd.Timestamp(counts[counts >= 20].index[0])
    times = _grid(is_start, IS_END)
    symbols = tuple(sorted(bars["symbol"].unique()))
    t_index = {t: i for i, t in enumerate(times)}
    s_index = {s: i for i, s in enumerate(symbols)}
    shape = (len(times), len(symbols))

    def pivot(frame: pd.DataFrame, time_col: str, value_col: str, fill: float) -> np.ndarray:
        out = np.full(shape, fill, dtype=float)
        ti = frame[time_col].map(t_index)
        si = frame[value_col + "__sym"] if False else frame["symbol"].map(s_index)
        keep = ti.notna() & si.notna()
        out[ti[keep].to_numpy(dtype=int), si[keep].to_numpy(dtype=int)] = (
            frame.loc[keep, value_col].to_numpy(dtype=float)
        )
        return out

    op = pivot(bars, "open_time", "open", np.nan)
    hi = pivot(bars, "open_time", "high", np.nan)
    lo = pivot(bars, "open_time", "low", np.nan)
    cl = pivot(bars, "open_time", "close", np.nan)
    qv = pivot(bars, "open_time", "quote_volume", 0.0)
    tc = pivot(bars, "open_time", "trade_count", 0.0)
    tbq = pivot(bars, "open_time", "taker_buy_quote_volume", 0.0)
    mk = pivot(marks, "mark_time", "mark_price", np.nan)

    funding = funding.copy()
    funding["unit"] = funding["mark_price"].to_numpy(float) * funding["funding_rate"].to_numpy(float)
    # Bucket each settlement into the bar that owns it: exactly-on-boundary vs strictly inside.
    offset = (funding["settlement_time"] - times[0]) / pd.Timedelta(hours=INTERVAL_HOURS)
    bar_pos = np.floor(offset.to_numpy(dtype=float))
    on_boundary = np.isclose(offset.to_numpy(dtype=float), bar_pos)
    valid = (bar_pos >= 0) & (bar_pos < len(times))
    si = funding["symbol"].map(s_index).to_numpy(dtype=float)
    valid &= ~np.isnan(si)
    fund_at = np.zeros(shape)
    fund_in = np.zeros(shape)
    bp = bar_pos[valid].astype(int)
    sp = si[valid].astype(int)
    unit = funding["unit"].to_numpy(float)[valid]
    ob = on_boundary[valid]
    np.add.at(fund_at, (bp[ob], sp[ob]), unit[ob])
    np.add.at(fund_in, (bp[~ob], sp[~ob]), unit[~ob])

    member = np.zeros(shape, dtype=bool)
    recon_times = np.sort(membership["reconstitution_time"].unique())
    grid_vals = times.to_numpy()
    # For each boundary, the most recent reconstitution at or before it.
    slot = np.searchsorted(recon_times, grid_vals, side="right") - 1
    by_recon: dict[pd.Timestamp, np.ndarray] = {}
    for rt, group in membership.groupby("reconstitution_time"):
        by_recon[rt] = group["symbol"].map(s_index).dropna().to_numpy(dtype=int)
    for i in range(len(times)):
        k = slot[i]
        if k < 0:
            continue
        member[i, by_recon[pd.Timestamp(recon_times[k])]] = True

    eligible = member & ~np.isnan(op) & ~np.isnan(mk)
    return Panel(
        times=times,
        symbols=symbols,
        open=op,
        high=hi,
        low=lo,
        close=cl,
        mark=mk,
        quote_volume=qv,
        trade_count=tc,
        taker_buy_quote=tbq,
        fund_at=fund_at,
        fund_in=fund_in,
        member=member,
        eligible=eligible,
    )


_CACHE: Panel | None = None


def panel() -> Panel:
    global _CACHE
    if _CACHE is None:
        _CACHE = build_panel()
    return _CACHE
