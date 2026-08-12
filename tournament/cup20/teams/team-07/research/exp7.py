import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data(); g = p["grid"]; fr = p["funding"]; op = p["open"]; cl = p["close"]; ok = p["ok"]; mk = p["mark"]
BASE = 1e-4

# ---------- 1. how separable are "carry" and "crowding"? ----------
carry = fr.rolling(63, min_periods=32).mean().shift(1).where(ok)
crowd = fr.gt(BASE).rolling(63, min_periods=32).mean().shift(1).where(ok)
risk = op.pct_change().rolling(63, min_periods=32).std().shift(1).where(ok)
basis = (cl / mk - 1.0).rolling(63, min_periods=32).mean().shift(1).where(ok)
accel = (fr.rolling(9).mean() - fr.rolling(63).mean()).shift(1).where(ok)
score = (carry.sub(carry.median(axis=1), axis=0)) / risk

def xsrank_corr(A, B):
    out = []
    for t in A.index:
        a = A.loc[t].dropna(); b = B.loc[t].dropna()
        j = a.index.intersection(b.index)
        if len(j) >= 10:
            ar, br = a[j].rank(), b[j].rank()
            if ar.std() > 0 and br.std() > 0:
                out.append(np.corrcoef(ar, br)[0, 1])
    return float(np.mean(out))

print("cross-sectional rank correlations (mean over boundaries):")
print(f"  carry  vs crowd(premium duration) : {xsrank_corr(carry, crowd):+.3f}")
print(f"  score  vs crowd                   : {xsrank_corr(score, crowd):+.3f}")
print(f"  carry  vs basis                   : {xsrank_corr(carry, basis):+.3f}")
print(f"  score  vs basis                   : {xsrank_corr(score, basis):+.3f}")
print(f"  carry  vs accel                   : {xsrank_corr(carry, accel):+.3f}")
print(f"  score  vs accel                   : {xsrank_corr(score, accel):+.3f}")
print(f"  carry  vs risk                    : {xsrank_corr(carry, risk):+.3f}")

# ---------- 2. flexible book with hysteresis + generic protection ----------
def build(carry_lb=63, risk_lb=63, n_side=7, hyst=0, cadence=1, phase=0,
          gate=None, gate_hi=None, gate_lo=None, invert_gate=False):
    C = fr.rolling(carry_lb, min_periods=max(2, carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    R = op.pct_change().rolling(risk_lb, min_periods=max(4, risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy()
    Gt = gate.to_numpy() if gate is not None else None
    prev_l, prev_s = set(), set()
    out = []
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence):
            out.append(None); continue
        c, r, o = C[i], R[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        if v.sum() < 2*n_side + 2:
            out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        rank_desc = idx[np.argsort(-sc)]
        M = n_side + hyst
        def pick(pool, prev):
            keep = [j for j in pool[:M] if j in prev]
            rest = [j for j in pool[:n_side] if j not in keep]
            sel = (keep + rest)[:n_side]
            k = 0
            while len(sel) < n_side and k < len(pool):
                if pool[k] not in sel: sel.append(pool[k])
                k += 1
            return sel
        shorts = pick(list(rank_desc), prev_s)
        longs = pick([j for j in list(rank_desc[::-1]) if j not in shorts], prev_l)
        if Gt is not None:
            gv = Gt[i]
            if gate_hi is not None:
                bad = [j for j in shorts if np.isfinite(gv[j]) and gv[j] > gate_hi]
                if invert_gate:
                    pass
                else:
                    pool = [j for j in rank_desc if j not in shorts and j not in longs
                            and np.isfinite(gv[j]) and gv[j] <= gate_hi]
                    shorts = [j for j in shorts if j not in bad] + pool[:len(bad)]
                    if len(shorts) < n_side: out.append(None); continue
        prev_l, prev_s = set(longs), set(shorts)
        w = np.zeros(len(c))
        w[np.array(longs, dtype=int)] = 1.0 / r[np.array(longs, dtype=int)]
        w[np.array(shorts, dtype=int)] = -1.0 / r[np.array(shorts, dtype=int)]
        pos = w > 0; neg = w < 0
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    return out

def ev(tl, tag=""):
    ref, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1, tr), metrics(r2, tr)
    if tag: show(tag, m1, m2, tr)
    return m1, m2, tr

print("\n=== cadence 1 + hysteresis buffer (n=7) ===")
for h in (0, 1, 2, 3, 4, 5, 6):
    ev(build(n_side=7, hyst=h, cadence=1), f"cad1 n=7 hyst={h}")
print()
for h in (0, 2, 3, 4):
    for n in (6, 7, 8):
        ev(build(n_side=n, hyst=h, cadence=1), f"cad1 n={n} hyst={h}")
