"""EDA 4 — does the funding->forward-price relationship depend on a crowding state?"""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel

p = build_panel()
g = p["grid"]; op = p["open"]; cl = p["close"]; el = p["eligible"]; fr = p["funding"]
qv = p["quote_volume"]; tbq = p["taker_buy_quote"]
start = el.sum(axis=1).ge(20).idxmax(); m = g >= start
g=g[m]; op=op.loc[g]; cl=cl.loc[g]; el=el.loc[g]; fr=fr.loc[g]; qv=qv.loc[g]; tbq=tbq.loc[g]

# mark price at each 8h boundary, from the funding rows
fund_raw = pd.read_parquet("data/cup20/is/funding.parquet")
mk = fund_raw.assign(b=fund_raw.funding_time.dt.floor("8h")).groupby(["b","symbol"])["mark_price"].last()
mk = mk.unstack("symbol").reindex(g).reindex(columns=op.columns)

ret8 = op.pct_change()
H = 9                                   # holding horizon in boundaries (3 days)
fwd = op.shift(-H) / op - 1.0
fwdf = fr.rolling(H).sum().shift(-H)     # funding paid over the holding interval
ok = el & fwd.notna() & mk.notna()

L = 63
sig = fr.rolling(L, min_periods=L//2).mean().shift(1)
srank = sig.where(ok).rank(axis=1, pct=True)
srank = srank.sub(srank.mean(axis=1), axis=0)          # centred cross-sectional carry rank

state = {}
state["agg_fund"]   = sig.where(ok).mean(axis=1)
state["disp_fund"]  = sig.where(ok).std(axis=1)
# persistence: fraction of last L settlements above the 0.01% baseline
state["agg_pers"]   = (fr.gt(0.0001)).rolling(L).mean().shift(1).where(ok).mean(axis=1)
basis = (cl / mk - 1.0)
state["agg_basis"]  = basis.rolling(L).mean().shift(1).where(ok).mean(axis=1)
state["agg_taker"]  = (tbq / qv - 0.5).rolling(L).mean().shift(1).where(ok).mean(axis=1)
mktret = (op.where(ok).pct_change().mean(axis=1))
state["mkt_mom"]    = mktret.rolling(L).sum().shift(1)
state["mkt_vol"]    = mktret.rolling(L).std().shift(1) * np.sqrt(3*365)

# The carry book's per-boundary forward price leg and funding leg (rank-weighted, unit gross)
w = -srank
w = w.div(w.abs().sum(axis=1), axis=0)
price_leg = (w * fwd).sum(axis=1)
fund_leg = -(w * fwdf).sum(axis=1)
sub = ok.sum(axis=1).ge(15)

print("full-sample per-decision means (H=9 overlapping):")
print(f"  price leg {price_leg[sub].mean():+.5f}  funding leg {fund_leg[sub].mean():+.5f}")
print()
for name, s in state.items():
    s = s[sub].dropna()
    pl = price_leg.reindex(s.index); fl = fund_leg.reindex(s.index)
    q = pd.qcut(s, 5, labels=False, duplicates="drop")
    tab = pd.DataFrame({"q": q, "price": pl, "fund": fl}).dropna().groupby("q").agg(
        price=("price", "mean"), fund=("fund", "mean"), n=("price", "size"))
    tab["total"] = tab.price + tab.fund
    print(f"--- {name} (quintiles of the state, low->high) ---")
    print((tab[["price","fund","total"]] * 1e4).round(1).assign(n=tab.n).to_string())
    print()
