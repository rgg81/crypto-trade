"""Team-07 research panel builder (EDA only; never a scorer).

Builds an 8h-grid panel from data/cup20/is/ that mirrors the organiser's execution shape closely
enough to reason about mechanism: open-to-open returns, per-boundary funding bucketed to the 8h
grid, and point-in-time membership. It is NOT the tournament scorer and no number produced here
is treated as a result.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

IS_ROOT = "data/cup20/is"
GRID = pd.Timedelta(hours=8)


def load():
    bars = pd.read_parquet(f"{IS_ROOT}/bars.parquet")
    funding = pd.read_parquet(f"{IS_ROOT}/funding.parquet")
    membership = pd.read_parquet(f"{IS_ROOT}/membership.parquet")
    return bars, funding, membership


def build_panel():
    bars, funding, membership = load()
    bars = bars.sort_values(["open_time", "symbol"])
    grid = pd.DatetimeIndex(sorted(bars["open_time"].unique()))

    def pivot(col):
        return bars.pivot(index="open_time", columns="symbol", values=col).reindex(grid)

    op = pivot("open")
    hi = pivot("high")
    lo = pivot("low")
    cl = pivot("close")
    vol = pivot("quote_volume")
    tbq = pivot("taker_buy_quote_volume")
    ntr = pivot("trade_count")

    # funding bucketed to the nominal 8h grid: an event at 07:59:59.95 or 08:00:00.005 is the
    # 08:00 settlement. Bucketing removes millisecond jitter from feature construction so that
    # what a symbol contributes never depends on which side of the boundary its clock landed.
    ft = funding["funding_time"]
    bucket = ft.dt.round("8h")
    fr = funding.assign(bucket=bucket).groupby(["bucket", "symbol"])["funding_rate"].sum()
    fr = fr.unstack("symbol").reindex(grid)

    # membership matrix: True where symbol is a PIT member at that boundary. A symbol absent from
    # a reconstitution row is NOT a member from that boundary on, so the boolean (not the rank) is
    # what gets forward-filled; forward-filling the rank would keep dropped names alive forever.
    rank_at_recon = membership.pivot(
        index="reconstitution_time", columns="symbol", values="liquidity_rank"
    )
    member_at_recon = rank_at_recon.notna()
    idx = member_at_recon.index.union(grid)
    is_member = member_at_recon.reindex(idx).ffill().reindex(grid).fillna(False).astype(bool)
    is_member = is_member.reindex(columns=op.columns, fill_value=False)
    mem = rank_at_recon.reindex(idx).ffill().reindex(grid).where(is_member)
    # eligible = PIT member AND has an executable open at this boundary
    eligible = is_member & op.notna()

    return dict(
        grid=grid, open=op, high=hi, low=lo, close=cl, quote_volume=vol,
        taker_buy_quote=tbq, trade_count=ntr, funding=fr.reindex(columns=op.columns),
        eligible=eligible, rank=mem.reindex(columns=op.columns),
    )


if __name__ == "__main__":
    p = build_panel()
    g = p["grid"]
    print("grid", len(g), g[0], "->", g[-1])
    print("symbols", p["open"].shape[1])
    print("eligible per boundary:", p["eligible"].sum(axis=1).describe())
    fr = p["funding"].where(p["eligible"])
    print("\nfunding coverage among eligible:", fr.notna().sum().sum() / p["eligible"].sum().sum())
    print("funding rate stats (eligible):")
    print(fr.stack().describe())
    ann = fr.stack() * 3 * 365
    print("\nannualised funding (eligible), pct:")
    print((ann * 100).describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]))
