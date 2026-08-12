"""EDA 5 — cross-sectional conditioning + variance decomposition of the carry price leg."""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel

p = build_panel()
g=p["grid"]; op=p["open"]; cl=p["close"]; el=p["eligible"]; fr=p["funding"]
qv=p["quote_volume"]; tbq=p["taker_buy_quote"]
start = el.sum(axis=1).ge(20).idxmax(); m = g>=start
g=g[m]; op=op.loc[g]; cl=cl.loc[g]; el=el.loc[g]; fr=fr.loc[g]; qv=qv.loc[g]; tbq=tbq.loc[g]
fund_raw = pd.read_parquet("data/cup20/is/funding.parquet")
mk = fund_raw.assign(b=fund_raw.funding_time.dt.floor("8h")).groupby(["b","symbol"])["mark_price"].last()
mk = mk.unstack("symbol").reindex(g).reindex(columns=op.columns)

H = 9; L = 63
fwd = op.shift(-H)/op - 1.0
ok = el & fwd.notna()
r8 = op.pct_change()

sig  = fr.rolling(L, min_periods=L//2).mean().shift(1)
states = {
 "own_vol":    r8.rolling(L).std().shift(1),
 "own_mom":    (op.shift(1)/op.shift(1+L) - 1.0),
 "fund_persist": fr.gt(0.0001).rolling(L).mean().shift(1),
 "fund_stretch": (fr.rolling(9).mean() - fr.rolling(189).mean()).shift(1),
 "basis":      (cl/mk - 1.0).rolling(L).mean().shift(1),
 "taker":      (tbq/qv - 0.5).rolling(L).mean().shift(1),
 "turnover":   (qv/qv.rolling(189).mean()).rolling(L).mean().shift(1),
}

def spread_ret(sig_, ok_, fwd_, sub_mask=None):
    """dollar-neutral carry spread forward return per boundary, restricted to sub_mask names"""
    s = sig_.where(ok_ if sub_mask is None else (ok_ & sub_mask))
    r = s.rank(axis=1, pct=True)
    w = -(r.sub(r.mean(axis=1), axis=0))
    w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0)
    return (w * fwd_).sum(axis=1, min_count=1), s.notna().sum(axis=1)

base, n = spread_ret(sig, ok, fwd)
valid = n.ge(15)
print(f"baseline carry spread fwd{H} price leg: mean={base[valid].mean()*1e4:+.1f}bps "
      f"t={base[valid].mean()/base[valid].std()*np.sqrt(valid.sum()/H):+.2f}")
print()
for nm, X in states.items():
    Xr = X.where(ok).rank(axis=1, pct=True)
    for lab, lo, hi in (("low", 0.0, 0.34), ("mid", 0.34, 0.67), ("high", 0.67, 1.01)):
        sub = (Xr >= lo) & (Xr < hi)
        r, nn = spread_ret(sig, ok, fwd, sub)
        v = nn.ge(5)
        t = r[v].mean()/r[v].std()*np.sqrt(v.sum()/H)
        print(f"  {nm:14s} {lab:5s}  mean={r[v].mean()*1e4:+7.1f}bps  t={t:+5.2f}  n={v.sum()}")
    print()

# ---- variance decomposition of the price leg -------------------------------
mkt = op.where(ok).pct_change().mean(axis=1)
r = sig.where(ok).rank(axis=1, pct=True)
w = -(r.sub(r.mean(axis=1), axis=0)); w = w.div(w.abs().sum(axis=1), axis=0)
leg = (w.shift(0) * op.pct_change().shift(-1)).sum(axis=1)      # 1-boundary price leg
d = pd.concat([leg.rename("leg"), mkt.shift(-1).rename("mkt")], axis=1).dropna()
b = np.polyfit(d.mkt, d.leg, 1)
resid = d.leg - (b[0]*d.mkt + b[1])
print(f"price-leg beta to equal-weight universe: {b[0]:+.3f}")
print(f"  leg vol {d.leg.std()*np.sqrt(3*365):.1%}  residual vol {resid.std()*np.sqrt(3*365):.1%} "
      f"-> beta explains {1-(resid.var()/d.leg.var()):.1%} of variance")
# per fold
for a_,b_ in [("2020-08-17","2021-08-01"),("2021-08-01","2022-08-01"),("2022-08-01","2023-08-01"),("2023-08-01","2024-08-01")]:
    seg = d[(d.index>=pd.Timestamp(a_,tz="UTC")) & (d.index<pd.Timestamp(b_,tz="UTC"))]
    bb = np.polyfit(seg.mkt, seg.leg, 1)[0]
    print(f"   {a_}: beta={bb:+.3f}  mkt ann ret={seg.mkt.mean()*3*365:+.1%}  leg sum={seg.leg.sum():+.3f}")
