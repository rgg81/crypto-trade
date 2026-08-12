import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from book import targets
from strat import data
from sim2 import simulate, reference_scalars, metrics, G

p = data()
tl = targets(cadence=6, phase=0, n_side=7)
ref, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
sc = reference_scalars(ref, p["grid"])
r2, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
eq = (1 + r2["net"]).cumprod(); dd = 1 - eq / eq.cummax()
print("2x maxDD", dd.max(), "at", dd.idxmax())

# top drawdown episodes
d = dd.copy(); eps = []
peak_idx = (eq / eq.cummax()).eq(1.0)
cur_peak = None
for t in dd.index:
    if peak_idx.loc[t]:
        cur_peak = t
for _ in range(6):
    end = d.idxmax()
    if d.loc[end] < 0.03: break
    startseg = d.loc[:end]
    st = startseg[startseg == 0].index[-1] if (startseg == 0).any() else startseg.index[0]
    rec = d.loc[end:]
    rc = rec[rec <= 1e-9].index[0] if (rec <= 1e-9).any() else d.index[-1]
    eps.append((st, end, rc, d.loc[end]))
    d.loc[st:rc] = 0.0
print("\ntop 2x drawdown episodes (start, trough, recovery, depth):")
for st, en, rc, dep in eps:
    seg = r2.loc[st:en]
    print(f"  {str(st)[:10]} -> {str(en)[:10]} (rec {str(rc)[:10]})  depth={dep:.1%}  "
          f"price={seg['price'].sum():+.3f} fund={seg['fund'].sum():+.3f} cost={-seg['cost'].sum():+.3f}")

# crowding state at those episodes
fr = p["funding"]; ok = p["ok"]
crowd = fr.gt(1e-4).rolling(63, min_periods=30).mean().shift(1).where(ok).mean(axis=1)
lvl = fr.rolling(63, min_periods=30).mean().shift(1).where(ok).mean(axis=1) * 3 * 365
disp = fr.rolling(63, min_periods=30).mean().shift(1).where(ok).std(axis=1) * 3 * 365
mktvol = p["open"].where(ok).pct_change().rolling(63).std().shift(1).mean(axis=1) * np.sqrt(3*365)
print("\nstate at episode START vs full-sample percentile:")
for st, en, rc, dep in eps:
    def pct(s):
        return float((s.dropna() <= s.get(st, np.nan)).mean()) if pd.notna(s.get(st, np.nan)) else np.nan
    print(f"  {str(st)[:10]} depth={dep:.1%}  crowd_pctile={pct(crowd):.2f} "
          f"fundlvl_pctile={pct(lvl):.2f} disp_pctile={pct(disp):.2f} mktvol_pctile={pct(mktvol):.2f}")
print("\nfull-sample: crowd mean %.3f  fundlvl(ann) mean %.1f%%" % (crowd.mean(), lvl.mean()*100))
