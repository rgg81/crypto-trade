import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from book import targets
from strat import data
from sim2 import simulate, reference_scalars, metrics, G, show

p = data()

def evb(tl, brakes=None, tag=""):
    ref, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, brakes=brakes)
    sc = reference_scalars(ref, p["grid"])
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc, brakes=brakes)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc, brakes=brakes)
    m1, m2 = metrics(r1, tr), metrics(r2, tr)
    if tag: show(tag, m1, m2, tr)
    return m1, m2, tr

def pm(brakes, cad=6, **kw):
    gs=[];sh=[];wf=[];dd=[];cal=[];vol=[];tr=[]
    for ph in range(cad):
        m1, m2, t = evb(targets(cadence=cad, phase=ph, **kw), brakes)
        gs.append(G(m2)); sh.append(m2["sharpe"]); wf.append(m2["worst_fold"]); dd.append(m2["maxdd"])
        cal.append(m2["calmar"]); vol.append(m1["vol"]); tr.append(t)
    return np.mean(gs), np.std(gs), np.mean(sh), np.mean(wf), np.mean(dd), np.mean(cal), np.mean(vol), int(np.mean(tr))

print("=== drawdown brake (risk_policy) on the carry book, cad=6 n=7 ===")
for br in (None,
           [(0.10, 0.50)],
           [(0.08, 0.50)],
           [(0.06, 0.50)],
           [(0.06, 0.50), (0.10, 0.25)],
           [(0.05, 0.60), (0.08, 0.35), (0.12, 0.15)],
           [(0.04, 0.50), (0.07, 0.25)],
           [(0.10, 0.25)]):
    a = pm(br)
    print(f"{str(br):44s} G={a[0]:6.1f}±{a[1]:4.1f} 2xSh={a[2]:+.2f} wf={a[3]:+.2f} dd={a[4]:.1%} "
          f"cal={a[5]:+.2f} vol={a[6]:.1%} tr={a[7]}")
