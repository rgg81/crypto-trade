"""Role checks: how the nominee and each sleeve behave in up, down and chop markets, plus the
long / short decomposition. Offline; the replica agrees with the organiser evaluator to ~1e-5."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO, fastsim as FS
from sleevegen import sleeve_matrix

p = Panel(); n = len(p.times)
mats = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}
W, _ = CO.combine(p, mats, bars=270)
books = {"ENSEMBLE": W, **{f"sleeve-{s}": mats[s] for s in CO.SLEEVES}}

# market state: 30-day trailing return of the equal-weight eligible basket, classified per month
elig = p.eligible[p.t0:p.t0+n]
cl = p.close[p.t0:p.t0+n]
prev = p.close[p.t0-1:p.t0+n-1]
r = np.where(elig & np.isfinite(cl) & np.isfinite(prev), cl / prev - 1.0, np.nan)
with np.errstate(invalid="ignore"):
    basket = np.nanmean(r, axis=1)
bs = pd.Series(np.nan_to_num(basket), index=p.times)
bd = (1 + bs).groupby(p.times.normalize()).prod() - 1.0
month = pd.DatetimeIndex(bd.index).tz_convert("UTC").tz_localize(None).to_period("M")
mret = (1 + bd).groupby(month).prod() - 1.0
lo, hi = mret.quantile(1/3), mret.quantile(2/3)
state = pd.Series(np.where(mret > hi, "up", np.where(mret < lo, "down", "chop")), index=mret.index)
print("market months:", state.value_counts().to_dict())

rows = []
for name, B in books.items():
    rb = CO.rebalance(n, 6, 3, B)
    res = FS.run_book(B, rb, p)["results"][1]
    d = FS.daily(res["net_return"], p.times)
    dm = pd.DatetimeIndex(d.index).tz_convert("UTC").tz_localize(None).to_period("M")
    out = {"book": name}
    for s in ("up", "chop", "down"):
        sel = d[pd.Index(dm).map(state).to_numpy() == s]
        out[f"{s}_sharpe"] = round(FS.sharpe(sel), 3)
        out[f"{s}_ret"] = round(float((1 + sel).prod() - 1.0), 4)
    lp = float(res["long_price_pnl"].sum() + res["long_funding_pnl"].sum())
    sp = float(res["short_price_pnl"].sum() + res["short_funding_pnl"].sum())
    out["long_gross"] = round(lp, 4); out["short_gross"] = round(sp, 4)
    # average net exposure
    rows.append(out)
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== net exposure of each book (executed, mean and sd of gross-normalised net) ===")
for name, B in books.items():
    g = np.abs(B).sum(axis=1)
    net = B.sum(axis=1) / np.where(g > 0, g, 1.0)
    nz = net[g > 0]
    print(f"  {name:16s} mean_net={nz.mean():+.3f} sd={nz.std():.3f} "
          f"p05={np.percentile(nz,5):+.3f} p95={np.percentile(nz,95):+.3f}")
