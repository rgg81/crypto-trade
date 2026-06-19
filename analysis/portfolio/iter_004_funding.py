"""portfolio-iteration EXPLORATION-004 — add real funding P&L + a carry tilt to the TS-trend base.

The iter-002 baseline ignores funding. Held perp legs actually pay/earn funding each 8h (a LONG pays
when funding>0; a SHORT earns). Two things to test, one change at a time:
  A) baseline trend, NO funding (reference)
  B) baseline trend + REAL funding P&L (just more realistic — does it help or hurt?)
  C) trend + a CARRY TILT: blend the trend signal with a carry signal (-trailing funding: short
     high-funding / long low-funding) at weight lambda, then book the real funding P&L.
Keep a tilt only if net Sharpe rises. Realistic cost, vol-targeted, leak-safe.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402

M_FUND = 9   # trailing-funding window for the carry signal


def load_funding(index_ms, syms) -> pd.DataFrame:
    cols = {}
    for s in syms:
        p = f"data/funding_rates/{s}.csv"
        if not os.path.exists(p):
            cols[s] = pd.Series(0.0, index=index_ms)
            continue
        f = pd.read_csv(p).drop_duplicates(subset="funding_time", keep="last")
        f = f.set_index("funding_time")["funding_rate"].astype(float)
        cols[s] = f.reindex(index_ms).fillna(0.0)
    return pd.DataFrame(cols)


def build(coins: dict, lam: float, use_funding: bool):
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(M_FUND).mean())          # short high-funding / long low-funding
    sig = (1 - lam) * trend + lam * carry                       # blended directional signal
    raw = (sig / rvol).where(elig)
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    fund_pnl = -(w * fund.shift(-1).reindex(columns=w.columns)).sum(axis=1) if use_funding else 0.0
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = (pnl + fund_pnl - cost).dropna()
    return base.vol_target(net)


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-004: funding P&L + carry tilt on TS-trend — {len(coins)} candidates")
    base.line("A trend (no fund)", build(coins, 0.0, False))
    base.line("B trend + fundPnL", build(coins, 0.0, True))
    base.line("C tilt 0.25 +fund", build(coins, 0.25, True))
    base.line("D tilt 0.50 +fund", build(coins, 0.50, True))


if __name__ == "__main__":
    main()
