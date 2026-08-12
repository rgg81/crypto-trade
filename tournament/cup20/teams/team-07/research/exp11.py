import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]
r8 = op.pct_change()

def build(carry_lb=63, risk_lb=63, n_side=7, tranches=1, stride=1, cadence=1, phase=0,
          skip_short=0):
    C = fr.rolling(carry_lb, min_periods=max(2,carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    Rk = r8.rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); n = C.shape[1]
    def one(i):
        c, r, o = C[i], Rk[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        if int(v.sum()) < 2*n_side + skip_short + 2: return None
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        desc = idx[np.argsort(-sc)]
        shorts = desc[skip_short:skip_short+n_side]; longs = desc[::-1][:n_side]
        w = np.zeros(n); w[longs] = 1.0/r[longs]; w[shorts] = -1.0/r[shorts]
        pos=w>0; neg=w<0
        if not pos.any() or not neg.any(): return None
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        return w
    cache = {}
    out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        acc = np.zeros(n); cnt = 0
        for k in range(tranches):
            j = i - k*stride
            if j < 0: break
            if j not in cache: cache[j] = one(j)
            wj = cache[j]
            if wj is not None: acc += wj; cnt += 1
        if cnt == 0: out.append(None); continue
        w = acc / cnt
        # names that left the eligible set must not carry weight
        w = np.where(OK[i], w, 0.0)
        pos=w>0; neg=w<0
        if not pos.any() or not neg.any(): out.append(np.zeros(n)); continue
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

print("=== tranche averaging (cadence 1, stride 3) : G across n=5..9 ===")
for tr_ in (1, 2, 3, 4, 6, 8):
    gs=[]; det=[]
    for n in (5,6,7,8,9):
        m1,m2,t = ev(build(n_side=n, tranches=tr_, stride=3), quiet=True)
        gs.append(G(m2)); det.append((m1["sharpe"], m2["sharpe"], m2["worst_fold"], m1["turn_ann"], m1["vol"], t))
    print(f"tranches={tr_}: G(n5..9)=" + " ".join(f"{x:6.1f}" for x in gs) +
          f"  mean={np.mean(gs):6.1f} min={min(gs):6.1f} | 1xSh={np.mean([d[0] for d in det]):+.2f} "
          f"2xSh={np.mean([d[1] for d in det]):+.2f} turn={np.mean([d[3] for d in det]):.0f}x "
          f"vol={np.mean([d[4] for d in det]):.1%} tr={int(np.mean([d[5] for d in det]))}")

print("\n=== stride sweep at tranches=4 ===")
for st in (1,2,3,4,6,9):
    gs=[]
    for n in (5,6,7,8,9):
        m1,m2,t = ev(build(n_side=n, tranches=4, stride=st), quiet=True); gs.append(G(m2))
    print(f"stride={st}: G(n5..9)=" + " ".join(f"{x:6.1f}" for x in gs) + f"  mean={np.mean(gs):6.1f} min={min(gs):6.1f}")

print("\n=== detail: tranches=4 stride=3 ===")
for n in (5,6,7,8,9):
    ev(build(n_side=n, tranches=4, stride=3), f"n={n} tr=4 st=3")
