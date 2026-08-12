import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]
BASE = 1e-4

def build(carry_lb=63, risk_lb=63, n_side=7, skip_short=0, skip_long=0, cadence=1, phase=0,
          crowd_lb=None, crowd_skip=0):
    C = fr.rolling(carry_lb, min_periods=max(2,carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    Rk = op.pct_change().rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy()
    Kr = (fr.gt(BASE).rolling(crowd_lb, min_periods=max(2,crowd_lb//2)).mean().shift(1)
          .where(ok).to_numpy()) if crowd_lb else None
    out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        c, r, o = C[i], Rk[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        K = int(v.sum())
        if K < n_side*2 + max(skip_short, skip_long) + 2: out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        desc = idx[np.argsort(-sc)]
        if Kr is not None and crowd_skip:
            kv = Kr[i]
            hot = sorted([j for j in desc], key=lambda j: -(kv[j] if np.isfinite(kv[j]) else -1))[:crowd_skip]
            desc = np.array([j for j in desc if j not in set(hot)], dtype=int)
        shorts = desc[skip_short:skip_short+n_side]
        asc = desc[::-1]
        longs = np.array([j for j in asc if j not in set(shorts)][skip_long:skip_long+n_side], dtype=int)
        if len(shorts) < n_side or len(longs) < n_side: out.append(None); continue
        w = np.zeros(len(c))
        w[longs] = 1.0/r[longs]; w[shorts] = -1.0/r[shorts]
        pos = w>0; neg = w<0
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    return out

def ev(tl, tag="", quiet=False):
    ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1,tr), metrics(r2,tr)
    if not quiet: show(tag, m1, m2, tr)
    return m1, m2, tr

print("=== skip the k most crowded names in the SHORT sleeve (cad=1, n=7) ===")
for k in (0,1,2,3,4):
    ev(build(skip_short=k), f"skip_short={k}")
print("\n=== skip on BOTH sleeves ===")
for k in (0,1,2,3):
    ev(build(skip_short=k, skip_long=k), f"skip both={k}")
print("\n=== skip by PREMIUM-DURATION crowding rank instead of carry rank (cad=1, n=7) ===")
for cs in (1,2,3,4):
    ev(build(crowd_lb=63, crowd_skip=cs), f"crowd_skip={cs} (lb63)")
print("\n=== n_side plateau at skip_short=1 vs 0 ===")
for k in (0,1,2):
    gs=[]
    for n in (5,6,7,8,9):
        m1,m2,tr = ev(build(n_side=n, skip_short=k), quiet=True)
        gs.append((n, G(m2), m2["sharpe"], m2["worst_fold"], m2["maxdd"]))
    print(f"skip_short={k}: " + " ".join(f"n{n}:G{gg:5.1f}(wf{wf:+.2f})" for n,gg,_,wf,_ in gs) +
          f"   meanG={np.mean([x[1] for x in gs]):5.1f}")
