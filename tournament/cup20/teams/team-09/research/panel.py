"""Build a dense numpy panel from the team-09 data root, for offline research only.

Nothing here scores anything the organiser recognises. It exists so the design space can be
mapped for free before a trial is spent. The organiser's own commands remain the only source of
a number this team is entitled to act on.

Panel conventions
-----------------
``times[i]`` is a bar open time and also a decision boundary. A decision made at ``times[i]``
may read bars whose close time is <= ``times[i]``, i.e. panel rows ``0 .. i-1``. The position
taken at ``times[i]`` is filled at ``open[i]`` and earns ``open[i+1] / open[i] - 1``.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[5]
DATA = REPO / "data" / "cup20" / "is"
# The cache is a large binary. It lives OUTSIDE the team workspace on purpose: the organiser's
# integrity review scans every file in the workspace and reports any it cannot read, and an
# unreadable blob sitting in a research tree is exactly the sort of thing an honest team should not
# leave behind. Everything here is regenerable from the data root in seconds.
CACHE = Path(os.environ.get("TEAM09_CACHE", "/tmp/team09-cup20-cache")) / "_panel.npz"

_cfg = tomllib.loads((REPO / "tournament" / "cup20" / "config.toml").read_text())
IS_END = pd.Timestamp(_cfg["splits"]["is_end"])
INTERVAL_H = int(_cfg["execution"]["interval_hours"])
EXEC = _cfg["execution"]
RISK_UNIT = _cfg["risk_unit"]

FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
)


def _build() -> dict[str, np.ndarray]:
    bars = pd.read_parquet(DATA / "bars.parquet")
    membership = pd.read_parquet(DATA / "membership.parquet")
    funding = pd.read_parquet(DATA / "funding.parquet")

    counts = membership.groupby("reconstitution_time").size().sort_index()
    is_start = pd.Timestamp(counts[counts >= 20].index[0]).tz_convert("UTC")

    symbols = sorted(bars["symbol"].unique())
    sym_ix = {s: j for j, s in enumerate(symbols)}

    # Full bar grid, then restrict decisions to [is_start, IS_END).
    all_times = pd.DatetimeIndex(sorted(bars["open_time"].unique()))
    out: dict[str, np.ndarray] = {}
    for field in FIELDS:
        wide = bars.pivot(index="open_time", columns="symbol", values=field)
        wide = wide.reindex(index=all_times, columns=symbols)
        out[field] = wide.to_numpy(dtype=float)

    # Weekly membership forward-filled onto the bar grid, then intersected with "has an open".
    recon = pd.DatetimeIndex(sorted(membership["reconstitution_time"].unique()))
    member = np.zeros((len(recon), len(symbols)), dtype=bool)
    for r, sym in zip(membership["reconstitution_time"], membership["symbol"], strict=True):
        member[recon.get_loc(pd.Timestamp(r)), sym_ix[sym]] = True
    slot = np.searchsorted(recon.asi8, all_times.asi8, side="right") - 1
    memb = np.zeros((len(all_times), len(symbols)), dtype=bool)
    valid = slot >= 0
    memb[valid] = member[slot[valid]]
    eligible = memb & np.isfinite(out["open"])

    # Funding attributed to the holding interval (open[t], open[t+1]]. Settlements exactly at a
    # boundary belong to the position carried INTO it (charged at index of that boundary);
    # settlements strictly inside belong to the post-rebalance book of the preceding boundary.
    # We fold both into one per-(bar, symbol) rate charged against the book held over the bar,
    # which is exact for the 8h grid and off by one sub-interval for 4h settlers.
    fund = funding.copy()
    fund["settlement_time"] = pd.to_datetime(fund["settlement_time"], utc=True)
    edges = all_times.asi8
    pos = np.searchsorted(edges, fund["settlement_time"].to_numpy().astype("datetime64[ns]").view("int64"), side="left")
    # settlement at edges[k] -> belongs to interval ending at k, i.e. bar k-1
    bar_ix = pos - 1
    keep = (bar_ix >= 0) & (bar_ix < len(all_times)) & fund["symbol"].isin(sym_ix).to_numpy()
    fpay = np.zeros((len(all_times), len(symbols)), dtype=float)
    cols = fund.loc[keep, "symbol"].map(sym_ix).to_numpy(dtype=int)
    rows = bar_ix[keep]
    vals = (fund.loc[keep, "funding_rate"] * fund.loc[keep, "mark_price"]).to_numpy(dtype=float)
    mk = fund.loc[keep, "mark_price"].to_numpy(dtype=float)
    np.add.at(fpay, (rows, cols), vals)
    fmark = np.zeros_like(fpay)
    np.add.at(fmark, (rows, cols), mk)

    out["funding_per_unit"] = fpay  # USD paid per unit of long quantity over the bar
    out["eligible"] = eligible.astype(np.uint8)
    out["times"] = all_times.asi8
    out["symbols"] = np.array(symbols, dtype=object)
    out["is_start"] = np.array([pd.Timestamp(is_start).value])
    out["is_end"] = np.array([pd.Timestamp(IS_END).value])
    del fmark
    return out


def load() -> dict:
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        return {k: z[k] for k in z.files}
    data = _build()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **data)
    return data


class Panel:
    """Decision-grid view: rows are boundaries in ``[is_start, IS_END)``."""

    def __init__(self) -> None:
        raw = load()
        times = pd.DatetimeIndex(raw["times"]).tz_localize("UTC")
        start = pd.Timestamp(int(raw["is_start"][0])).tz_localize("UTC")
        end = pd.Timestamp(int(raw["is_end"][0])).tz_localize("UTC")
        self.symbols = list(raw["symbols"])
        # Decisions run over [start, end); we keep one extra row past the last decision when it
        # exists so the final bar has a next open.  It does not, so the last decision's return is
        # the organiser's terminal close-out; we drop that single boundary offline.
        mask = (times >= start) & (times < end)
        self.d0 = int(np.argmax(mask))
        self.dn = int(len(times) - np.argmax(mask[::-1]))
        self.all_times = times
        self.times = times[self.d0 : self.dn]
        for f in FIELDS:
            setattr(self, f, raw[f])
        self.funding_per_unit = raw["funding_per_unit"]
        self.eligible = raw["eligible"].astype(bool)
        self.n_all = len(times)
        self.n_sym = len(self.symbols)

    def slice_decisions(self, arr: np.ndarray) -> np.ndarray:
        return arr[self.d0 : self.dn]


if __name__ == "__main__":
    p = Panel()
    print("symbols", p.n_sym, "decisions", len(p.times))
    print("first", p.times[0], "last", p.times[-1])
    print("members per boundary", p.eligible[p.d0 : p.dn].sum(axis=1).min(),
          p.eligible[p.d0 : p.dn].sum(axis=1).max())
