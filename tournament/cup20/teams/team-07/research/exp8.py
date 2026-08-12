import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; cl=p["close"]; ok=p["ok"]; mk=p["mark"]
prem = (cl / mk - 1.0).where(ok)
print("perp close vs mark premium, bps:", (prem.stack()*1e4).describe(percentiles=[.01,.05,.5,.95,.99]).round(2).to_dict())
print("premium autocorr (xs-rank, lag 1/9/63):")
def xr(A,B):
    o=[]
    for t in A.index:
        a=A.loc[t].dropna(); b=B.loc[t].dropna(); j=a.index.intersection(b.index)
        if len(j)>=10:
            ar,br=a[j].rank(),b[j].rank()
            if ar.std()>0 and br.std()>0: o.append(np.corrcoef(ar,br)[0,1])
    return float(np.mean(o))
for L in (1,9,63):
    print(f"   lag {L}: {xr(prem, prem.shift(L)):+.3f}")

R = op.pct_change().rolling(63, min_periods=32).std().shift(1).where(ok)

def build(carry_lb=63, risk_lb=63, theta=0.40, cadence=1, phase=0, gate=None, gate_q=None,
          gate_mode="drop_short"):
    C = fr.rolling(carry_lb, min_periods=max(2,carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    Rk = op.pct_change().rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); Gt = gate.to_numpy() if gate is not None else None
    out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        c, r, o = C[i], Rk[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        K = int(v.sum())
        if K < 10: out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        u = 2.0 * (np.argsort(np.argsort(sc)) / (K - 1)) - 1.0
        tilt = -np.sign(u) * np.maximum(0.0, np.abs(u) - theta)
        if Gt is not None:
            gv = Gt[i][idx]
            if gate_mode == "drop_short":
                bad = np.isfinite(gv) & (gv > gate_q) & (tilt < 0)
                tilt = np.where(bad, 0.0, tilt)
            elif gate_mode == "drop_long":
                bad = np.isfinite(gv) & (gv < gate_q) & (tilt > 0)
                tilt = np.where(bad, 0.0, tilt)
        w = np.zeros(len(c))
        w[idx] = tilt / r[idx]
        pos = w > 0; neg = w < 0
        if not pos.any() or not neg.any(): out.append(np.zeros(len(c))); continue
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    return out

def ev(tl, tag=""):
    ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1,tr), metrics(r2,tr)
    if tag: show(tag, m1, m2, tr)
    return m1, m2, tr

print("\n=== soft-threshold tilt theta sweep (cad=1, lb=63) ===")
for th in (0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8):
    ev(build(theta=th), f"theta={th}")
print("\n=== theta x carry_lb (cad=1) ===")
for lb in (42, 63, 90, 126):
    for th in (0.3, 0.4, 0.5, 0.6):
        ev(build(carry_lb=lb, theta=th), f"carry_lb={lb} theta={th}")
