import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, dec

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]
r8 = op.pct_change()
CACHE = {}

def build(carry_lb, risk_lb, n_side, cadence, phase=0, crowd_cap=None, crowd_lb=63):
    key = (carry_lb, risk_lb, n_side, cadence, phase, crowd_cap, crowd_lb)
    if key in CACHE: return CACHE[key]
    C = fr.rolling(carry_lb, min_periods=max(2,carry_lb//2)).mean().shift(1).where(ok).to_numpy()
    Rk = r8.rolling(risk_lb, min_periods=max(4,risk_lb//2)).std().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); n = C.shape[1]
    KR = (fr.gt(1e-4).rolling(crowd_lb, min_periods=crowd_lb//2).mean().shift(1).where(ok).to_numpy()
          if crowd_cap is not None else None)
    out=[]
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence): out.append(None); continue
        c, r, o = C[i], Rk[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0)
        if int(v.sum()) < 2*n_side + 2: out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx] - np.median(c[idx])) / r[idx]
        desc = idx[np.argsort(-sc)]
        ss = desc[:n_side]; ls = desc[::-1][:n_side]
        w = np.zeros(n); w[ls] = 1.0/r[ls]; w[ss] = -1.0/r[ss]
        if KR is not None:
            kv = KR[i]
            for j in ss:
                if np.isfinite(kv[j]) and kv[j] > crowd_cap: w[j] *= 0.5
        pos=w>0; neg=w<0
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    CACHE[key] = out
    return out

def one(carry_lb, risk_lb, n_side, cadence, **kw):
    tl = build(carry_lb, risk_lb, n_side, cadence, **kw)
    ref,_ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, g)
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1,tr), metrics(r2,tr)
    gross = r1["gross"].sum(); turn = r1["turnover"].sum()
    return {"wf": m2["worst_fold"], "mf": m2["median_fold"], "dd": m2["maxdd"], "cal": m2["calmar"],
            "pq": m2["pos_q"], "sh1": m1["sharpe"], "sh2": m2["sharpe"], "ret1": m1["ann_ret"],
            "vol": m1["vol"], "turn": m1["turn_ann"], "trades": tr,
            "gedge": gross/turn*1e4 if turn>0 else 0.0,
            "posfrac": 1.0 if (m1["ann_ret"] > 0 and m2["sharpe"] > 0) else 0.0}

def nbhd(cl, rl, ns, cad, dcl=(15,21), drl=(15,21), dns=1, **kw):
    pts = [(cl,rl,ns), (cl-dcl[0],rl,ns), (cl+dcl[1],rl,ns), (cl,rl-drl[0],ns), (cl,rl+drl[1],ns),
           (cl,rl,ns-dns), (cl,rl,ns+dns)]
    res = [one(a,b,c,cad,**kw) for a,b,c in pts]
    med = {k: float(np.median([r[k] for r in res])) for k in res[0]}
    med["G"] = (30*dec((med["wf"]+0.25)/1.0) + 20*dec((med["mf"]-0.25)/0.75)
                + 20*dec((0.20-med["dd"])/0.15) + 15*dec(med["cal"]/1.5)
                + 8*dec((med["pq"]-0.50)/0.375))
    return med, res

print("nominee (63,63,7); neighbourhood +-{15,21} on lookbacks, +-1 on n_side")
print(f"{'cad':>4} {'G_med':>6} {'G_nom':>6} {'wf':>6} {'mf':>6} {'dd':>6} {'cal':>6} {'pq':>5} "
      f"{'sh1':>5} {'sh2':>5} {'vol':>6} {'turn':>6} {'gedge':>6} {'trades':>7} {'pos%':>5}")
for cad in (1,2,3,6,9):
    med, res = nbhd(63,63,7,cad)
    nom = res[0]
    gn = (30*dec((nom["wf"]+0.25)/1.0) + 20*dec((nom["mf"]-0.25)/0.75) + 20*dec((0.20-nom["dd"])/0.15)
          + 15*dec(nom["cal"]/1.5) + 8*dec((nom["pq"]-0.50)/0.375))
    print(f"{cad:>4} {med['G']:6.1f} {gn:6.1f} {med['wf']:+6.2f} {med['mf']:+6.2f} {med['dd']:6.1%} "
          f"{med['cal']:+6.2f} {med['pq']:5.2f} {med['sh1']:+5.2f} {med['sh2']:+5.2f} {med['vol']:6.1%} "
          f"{med['turn']:6.1f} {med['gedge']:6.1f} {int(med['trades']):7d} {np.mean([r['posfrac'] for r in res]):5.2f}")

print("\nalternative nominees at cadence 1:")
for cl in (42, 63, 84, 105):
    for ns in (6, 7, 8):
        med, res = nbhd(cl, 63, ns, 1)
        print(f"  carry_lb={cl:3d} n={ns}  G_med={med['G']:6.1f} wf={med['wf']:+.2f} mf={med['mf']:+.2f} "
              f"dd={med['dd']:.1%} sh1={med['sh1']:+.2f} vol={med['vol']:.1%} pos%={np.mean([r['posfrac'] for r in res]):.2f}")

print("\nprotection ON (halve entrenched-crowd shorts) at the same nominee, cadence 1:")
for cc in (0.95, 0.85, 0.75, 0.60):
    med, res = nbhd(63,63,7,1, crowd_cap=cc)
    print(f"  crowd_cap={cc}  G_med={med['G']:6.1f} wf={med['wf']:+.2f} mf={med['mf']:+.2f} dd={med['dd']:.1%} sh1={med['sh1']:+.2f}")
