"""Panel builder: 8h grid matrices for the IS snapshot.

Nothing here scores anything. It converts the organiser's long frames into aligned
numpy matrices so sleeve signals can be explored offline without spending trials.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.cup20.config import IS_END
from crypto_trade.cup20.runner import decision_grid
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.tournament.data import eligible_at

IS_ROOT = "data/cup20/is"


class Panel:
    def __init__(self, root: str = IS_ROOT) -> None:
        snap = load_snapshot(root)
        self.snapshot = snap
        bars = snap.bars.copy()
        bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True)
        self.is_start = resolve_is_start(snap.membership)
        self.times = pd.DatetimeIndex(decision_grid(self.is_start, IS_END, interval_hours=8))
        # full bar grid, including warm-up before is_start
        full_times = pd.DatetimeIndex(sorted(bars["open_time"].unique()))
        self.full_times = full_times
        syms = sorted(bars["symbol"].unique())
        self.symbols = syms
        self.sidx = {s: i for i, s in enumerate(syms)}

        def pivot(col: str) -> np.ndarray:
            p = bars.pivot(index="open_time", columns="symbol", values=col)
            p = p.reindex(index=full_times, columns=syms)
            return p.to_numpy(dtype=float)

        self.open = pivot("open")
        self.high = pivot("high")
        self.low = pivot("low")
        self.close = pivot("close")
        self.volume = pivot("volume")
        self.quote_volume = pivot("quote_volume")
        self.trade_count = pivot("trade_count")
        self.taker_buy_quote = pivot("taker_buy_quote_volume")

        marks = snap.mark_prices.copy()
        marks["mark_time"] = pd.to_datetime(marks["mark_time"], utc=True)
        mp = marks.pivot(index="mark_time", columns="symbol", values="mark_price")
        mp = mp.reindex(index=full_times, columns=syms)
        self.mark = mp.to_numpy(dtype=float)

        # funding: settlement-time keyed, summed rate per (settlement bucket, symbol)
        f = snap.funding.copy()
        f["settlement_time"] = pd.to_datetime(f["funding_time"], utc=True).dt.floor("h")
        f["mark_time"] = pd.to_datetime(f["mark_time"], utc=True)
        # bucket each settlement into the 8h bar it falls in: [t, t+8h)
        bucket = f["settlement_time"].dt.floor("8h")
        f["bucket"] = bucket
        f["at_boundary"] = f["settlement_time"] == bucket
        f["cash_per_unit"] = f["mark_price"] * f["funding_rate"]
        # rate paid on the boundary itself (charged to the carried book, before rebalance)
        at = f[f["at_boundary"]].pivot_table(
            index="bucket", columns="symbol", values="cash_per_unit", aggfunc="sum"
        ).reindex(index=full_times, columns=syms).fillna(0.0)
        af = f[~f["at_boundary"]].pivot_table(
            index="bucket", columns="symbol", values="cash_per_unit", aggfunc="sum"
        ).reindex(index=full_times, columns=syms).fillna(0.0)
        self.fund_at = at.to_numpy(dtype=float)      # per-unit-quantity cash OUTFLOW basis
        self.fund_after = af.to_numpy(dtype=float)
        rate = f.pivot_table(
            index="bucket", columns="symbol", values="funding_rate", aggfunc="sum"
        ).reindex(index=full_times, columns=syms).fillna(0.0)
        self.funding_rate_bar = rate.to_numpy(dtype=float)
        pres = f.pivot_table(
            index="bucket", columns="symbol", values="funding_rate", aggfunc="count"
        ).reindex(index=full_times, columns=syms).fillna(0.0)
        self.funding_present = pres.to_numpy(dtype=float) > 0

        # membership eligibility on the decision grid, intersected with a fillable open
        elig = np.zeros((len(full_times), len(syms)), dtype=bool)
        mem = snap.membership.copy()
        mem["reconstitution_time"] = pd.to_datetime(mem["reconstitution_time"], utc=True)
        cache: dict[pd.Timestamp, tuple[str, ...]] = {}
        recon = pd.DatetimeIndex(sorted(mem["reconstitution_time"].unique()))
        for i, t in enumerate(full_times):
            pos = recon.searchsorted(t, side="right") - 1
            if pos < 0:
                continue
            key = recon[pos]
            if key not in cache:
                cache[key] = eligible_at(snap.membership, key)
            for s in cache[key]:
                j = self.sidx.get(s)
                if j is not None and np.isfinite(self.open[i, j]):
                    elig[i, j] = True
        self.eligible = elig
        self.t0 = int(full_times.searchsorted(self.times[0]))
        assert full_times[self.t0] == self.times[0]

    def slice_grid(self, arr: np.ndarray) -> np.ndarray:
        return arr[self.t0 : self.t0 + len(self.times)]


if __name__ == "__main__":
    p = Panel()
    print("grid", len(p.times), p.times[0], p.times[-1])
    print("symbols", len(p.symbols))
    e = p.slice_grid(p.eligible)
    print("eligible per boundary: min", e.sum(axis=1).min(), "max", e.sum(axis=1).max(),
          "mean", e.sum(axis=1).mean())
    o = p.slice_grid(p.open)
    print("NaN open among eligible:", int((e & ~np.isfinite(o)).sum()))
    m = p.slice_grid(p.mark)
    print("NaN mark among eligible:", int((e & ~np.isfinite(m)).sum()))
    print("mark/open median abs dev:",
          float(np.nanmedian(np.abs(m[e] / o[e] - 1.0))))
