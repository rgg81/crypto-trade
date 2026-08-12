import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]
r8 = op.pct_change()
EDGES = ["2021-08-01","2022-08-01","2023-08-01"]

def build(carry_lb=63, risk_lb=63, n_side=7, cadence=1, phase=0,
          adequacy=None, volspike=None, crowd_lb=63, crowd_cap=None):
    C = fr.rolling(carry_lb, min_periods=max(2,carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    Rk = r8.rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); n = C.shape[1]
    mv_s = r8.where(ok).mean(axis=1).rolling(9).std().shift(1)
    mv_l = r8.where(ok).mean(axis=1).rolling(126).std().shift(1)
    VS = (mv_s / mv_l).to_numpy()
    KR = (fr.gt(1e-4).rolling(crowd_lb, min_periods=crowd_lb//2).mean().shift(1)
          .where(ok).to_numpy()) if crowd_cap is not None else None
    out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        c, r, o = C[i], Rk[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        if int(v.sum()) < 2*n_side + 2: out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        if adequacy is not None:
            desc0 = np.sort(sc)[::-1]
            spread = desc0[:n_side].mean() - desc0[-n_side:].mean()
            if spread < adequacy: out.append({}); continue
        if volspike is not None and np.isfinite(VS[i]) and VS[i] > volspike:
            out.append({}); continue
        desc = idx[np.argsort(-sc)]
        shorts = list(desc[:n_side]); longs = list(desc[::-1][:n_side])
        w = np.zeros(n)
        ls = np.array(longs, int); ss = np.array(shorts, int)
        w[ls] = 1.0/r[ls]; w[ss] = -1.0/r[ss]
        if KR is not None:
            kv = KR[i]
            for j in ss:
                if np.isfinite(kv[j]) and kv[j] > crowd_cap:
                    w[j] *= 0.5
        pos=w>0; neg=w<0
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    return out

def norm(tl, n):
    return [np.zeros(n) if isinstance(x, dict) else x for x in tl]

def ev(tl, tag="", quiet=False, legs=False):
    tl = norm(tl, p["open"].shape[1])
    ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1,tr), metrics(r2,tr)
    if not quiet: show(tag, m1, m2, tr)
    if legs:
        e=[r1.index[0]]+[pd.Timestamp(x,tz="UTC") for x in EDGES]+[r1.index[-1]+pd.Timedelta(hours=8)]
        print("    legs: " + "  ".join(
            f"[p{r1[(r1.index>=a)&(r1.index<b)]['price'].sum():+.3f} "
            f"f{r1[(r1.index>=a)&(r1.index<b)]['fund'].sum():+.3f} "
            f"c{-r1[(r1.index>=a)&(r1.index<b)]['cost'].sum():+.3f}]" for a,b in zip(e[:-1],e[1:])))
    return m1, m2, tr

print("=== baseline decomposition (cad1 n7) ===")
ev(build(), "baseline", legs=True)
print("\n=== carry-adequacy stand-aside gate ===")
for a in (None, 0.01, 0.02, 0.03, 0.05):
    ev(build(adequacy=a), f"adequacy={a}")
print("\n=== market vol-spike stand-aside gate (9/126 realised vol ratio) ===")
for vs in (None, 2.5, 2.0, 1.75, 1.5, 1.25):
    ev(build(volspike=vs), f"volspike={vs}")
print("\n=== halve the weight of entrenched-crowd shorts ===")
for cc in (None, 0.95, 0.90, 0.80, 0.70, 0.50):
    ev(build(crowd_cap=cc), f"crowd_cap={cc}")
