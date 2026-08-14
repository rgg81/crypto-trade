"""Team-11 offline research panel.

Builds dense (boundary x symbol) numpy matrices from the IS snapshot so that thousands of
full-window simulations can run without re-reading parquet. Nothing here is scored; every
scored number comes from the organiser's own harness under a journaled trial.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"
IS_END = pd.Timestamp("2024-08-01T00:00:00Z")


def _eligible_matrix(membership: pd.DataFrame, times: pd.DatetimeIndex, symbols: list[str]):
    """Point-in-time membership as a boolean matrix, replicating ``universe.eligible_at``."""
    recon = pd.to_datetime(membership["reconstitution_time"], utc=True)
    m = membership.assign(reconstitution_time=recon)
    boundaries = np.sort(m["reconstitution_time"].unique())
    sym_index = {s: i for i, s in enumerate(symbols)}
    out = np.zeros((len(times), len(symbols)), dtype=bool)
    # index of the latest reconstitution at or before each decision time
    pos = np.searchsorted(boundaries, times.to_numpy(), side="right") - 1
    groups: dict[int, np.ndarray] = {}
    for i, b in enumerate(boundaries):
        members = m.loc[m["reconstitution_time"] == b, "symbol"].astype(str)
        idx = np.array([sym_index[s] for s in members if s in sym_index], dtype=int)
        groups[i] = idx
    for row, p in enumerate(pos):
        if p >= 0:
            out[row, groups[p]] = True
    return out


class Panel:
    def __init__(self, root: str = IS_ROOT):
        bars = pd.read_parquet(f"{root}/bars.parquet")
        bars["open_time"] = pd.to_datetime(bars["open_time"], utc=True)
        funding = pd.read_parquet(f"{root}/funding.parquet")
        funding["settlement_time"] = pd.to_datetime(funding["settlement_time"], utc=True)
        marks = pd.read_parquet(f"{root}/mark_prices.parquet")
        marks["mark_time"] = pd.to_datetime(marks["mark_time"], utc=True)
        membership = pd.read_parquet(f"{root}/membership.parquet")

        self.times = pd.DatetimeIndex(np.sort(bars["open_time"].unique()))
        self.symbols = sorted(bars["symbol"].astype(str).unique())
        self.si = {s: i for i, s in enumerate(self.symbols)}

        def piv(col, frame=bars, index="open_time"):
            p = frame.pivot(index=index, columns="symbol", values=col)
            p = p.reindex(index=self.times, columns=self.symbols)
            return p.to_numpy(dtype=float)

        self.open = piv("open")
        self.high = piv("high")
        self.low = piv("low")
        self.close = piv("close")
        self.quote_volume = piv("quote_volume")
        self.taker_buy_quote = piv("taker_buy_quote_volume")
        self.trade_count = piv("trade_count")
        self.mark = piv("mark_price", marks, "mark_time")

        # funding: sum of rates settling exactly at each boundary, and in (t, t+8h).
        # The evaluator's cashflow is -q * mark_price * funding_rate using the FUNDING ROW's own
        # mark, not the boundary mark, so the per-unit cash term is pre-aggregated here.
        f = funding.copy()
        f["symbol"] = f["symbol"].astype(str)
        f["cash"] = f["funding_rate"] * f["mark_price"]
        on_grid = f[f["settlement_time"].isin(self.times)]
        agg = on_grid.groupby(["settlement_time", "symbol"])["funding_rate"].sum().unstack()
        self.funding_at = (
            agg.reindex(index=self.times, columns=self.symbols).to_numpy(dtype=float)
        )
        aggc = on_grid.groupby(["settlement_time", "symbol"])["cash"].sum().unstack()
        self.fund_at_cash = np.nan_to_num(
            aggc.reindex(index=self.times, columns=self.symbols).to_numpy(dtype=float)
        )
        self.has_settlement = ~np.isnan(self.funding_at)
        self.funding_at_f = np.nan_to_num(self.funding_at)

        # off-grid settlements land strictly inside a bar
        off = f[~f["settlement_time"].isin(self.times)].copy()
        if len(off):
            bucket = off["settlement_time"].dt.floor("8h")
            off = off.assign(bucket=bucket)
            agg2 = off.groupby(["bucket", "symbol"])["funding_rate"].sum().unstack()
            self.funding_mid = np.nan_to_num(
                agg2.reindex(index=self.times, columns=self.symbols).to_numpy(dtype=float)
            )
            agg2c = off.groupby(["bucket", "symbol"])["cash"].sum().unstack()
            self.fund_mid_cash = np.nan_to_num(
                agg2c.reindex(index=self.times, columns=self.symbols).to_numpy(dtype=float)
            )
            cnt = off.groupby(["bucket", "symbol"]).size().unstack()
            self.mid_settlements = np.nan_to_num(
                cnt.reindex(index=self.times, columns=self.symbols).to_numpy(dtype=float)
            )
        else:  # pragma: no cover
            self.funding_mid = np.zeros_like(self.open)
            self.fund_mid_cash = np.zeros_like(self.open)
            self.mid_settlements = np.zeros_like(self.open)

        fi = f.groupby(["settlement_time", "symbol"])["funding_interval_hours"].min().unstack()
        self.funding_interval = fi.reindex(
            index=self.times, columns=self.symbols
        ).to_numpy(dtype=float)

        self.eligible = _eligible_matrix(membership, self.times, self.symbols)
        # An eligible symbol must also have an executable open at the boundary.
        self.eligible &= ~np.isnan(self.open)

        self.hour = self.times.hour.to_numpy()
        self.slot = (self.hour // 8).astype(int)  # 0 -> 00:00, 1 -> 08:00, 2 -> 16:00
        self.dow = self.times.dayofweek.to_numpy()  # Monday = 0

        # open-to-open transaction return, aligned so row t is the return earned by exposure
        # taken at boundary t (fills at open[t], marked to open[t+1]).
        nxt = np.vstack([self.open[1:], np.full((1, self.open.shape[1]), np.nan)])
        self.oo_ret = nxt / self.open - 1.0
        # close-to-close within the bar, for formation features that must not use open[t+1]
        self.bar_ret = self.close / self.open - 1.0


def load(root: str = IS_ROOT) -> Panel:
    return Panel(root)
