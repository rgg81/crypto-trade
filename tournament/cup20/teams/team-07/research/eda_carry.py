"""EDA 1 — does a cross-sectional funding-carry book earn, and how persistent is funding?"""
from __future__ import annotations
import numpy as np, pandas as pd
import sys
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel

p = build_panel()
g = p["grid"]; op = p["open"]; el = p["eligible"]; fr = p["funding"]

# restrict to the scored IS window: first boundary where 20 members exist
start = el.sum(axis=1).ge(20).idxmax()
print("first 20-member boundary:", start)
mask = g >= start
g = g[mask]; op = op.loc[g]; el = el.loc[g]; fr = fr.loc[g]

# forward open-to-open return over ONE holding interval
fwd = op.shift(-1) / op - 1.0
# funding settled during the holding interval (t, t+8h] == the t+8h bucket
fwd_fund = fr.shift(-1)
# most recent SAFELY visible funding bucket at decision t
f_prev = fr.shift(1)

E = el & fwd.notna() & fwd_fund.notna() & f_prev.notna()
print("usable symbol-boundaries:", int(E.sum().sum()))

# --- persistence -------------------------------------------------------------
def xs_corr(a, b, m):
    A = a.where(m); B = b.where(m)
    out = []
    for t in A.index:
        x = A.loc[t].dropna(); y = B.loc[t].dropna()
        j = x.index.intersection(y.index)
        if len(j) >= 8:
            xr = x[j].rank(); yr = y[j].rank()
            if xr.std() > 0 and yr.std() > 0:
                out.append(np.corrcoef(xr, yr)[0, 1])
    return np.mean(out), len(out)

for lag in (1, 2, 3, 6, 9, 21, 63):
    c, n = xs_corr(fr.shift(1), fr.shift(1 - lag), E)
    print(f"XS rank corr  f[t-1] vs f[t-1+{lag}] : {c:+.3f}  (n={n})")

# --- carry vs forward return --------------------------------------------------
print()
for lb in (1, 3, 6, 9, 21, 42, 63):
    sig = fr.rolling(lb).mean().shift(1)          # trailing mean funding, visible at t
    c, n = xs_corr(sig, fwd, E)
    cf, _ = xs_corr(sig, -fwd_fund, E)
    print(f"lookback {lb:3d} boundaries: XS rank corr(sig, fwd_price)={c:+.4f}   "
          f"corr(sig, -fwd_funding)={cf:+.4f}")
