import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]
r8 = op.pct_change()

def kernel(K, n, taper):
    """trapezoid over the sorted-by-score ranking: full weight for the n extreme names,
    linearly tapering over the next `taper` names, zero in the middle."""
    k = np.zeros(K)
    for j in range(K):
        if j < n: k[j] = 1.0
        elif j < n + taper: k[j] = 1.0 - (j - n + 1) / (taper + 1.0)
    return k

def build(carry_lbs=(63,), risk_lb=63, n_side=7, taper=0, cadence=1, phase=0):
    Cs = [fr.rolling(L, min_periods=max(2,L//2)).mean().shift(1).where(ok).to_numpy() for L in carry_lbs]
    Rk = r8.rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        r, o = Rk[i], OK[i]
        v = o & np.isfinite(r) & (r > 0)
        for C in Cs: v = v & np.isfinite(C[i])
        K = int(v.sum())
        if K < 2*n_side + 2: out.append(None); continue
        idx = np.where(v)[0]
        # average of per-lookback cross-sectional ranks, then divide by risk
        ranks = np.zeros(K)
        for C in Cs:
            c = C[i][idx]
            ranks += np.argsort(np.argsort(c)) / (K - 1.0)
        ranks /= len(Cs)
        sc = (ranks - np.median(ranks)) / r[idx]
        desc = np.argsort(-sc)
        kk = kernel(K, n_side, taper)
        w = np.zeros(len(r)); wk = np.zeros(K)
        wk[desc] = -kk
        wk[desc[::-1]] += kk
        w[idx] = wk / r[idx]
        pos = w>0; neg = w<0
        if not pos.any() or not neg.any(): out.append(np.zeros(len(r))); continue
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

for lbs in [(63,), (21,63,126), (42,84,168), (21,63), (63,126)]:
    for taper in (0, 2, 4):
        gs=[]
        for n in (5,6,7,8,9):
            m1,m2,tr = ev(build(carry_lbs=lbs, n_side=n, taper=taper), quiet=True)
            gs.append(G(m2))
        print(f"lbs={str(lbs):16s} taper={taper}  G by n(5..9)= " +
              " ".join(f"{x:6.1f}" for x in gs) + f"   mean={np.mean(gs):6.1f} min={min(gs):6.1f}")
