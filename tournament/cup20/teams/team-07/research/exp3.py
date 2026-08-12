import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np
from book import ev
from sim2 import G

def phase_mean(cad, **kw):
    gs, sh, wf, tn, tr, dd = [], [], [], [], [], []
    for ph in range(cad):
        m1, m2, r1, r2, t = ev(cadence=cad, phase=ph, **kw)
        gs.append(G(m2)); sh.append(m2["sharpe"]); wf.append(m2["worst_fold"])
        tn.append(m1["turn_ann"]); tr.append(t); dd.append(m2["maxdd"])
    return (np.mean(gs), np.std(gs), np.mean(sh), np.mean(wf), np.mean(tn), int(np.mean(tr)), np.mean(dd))

print("=== crowd_max veto on the SHORT sleeve (cad=6, n=7, lb=63) ===")
print("crowd_max   Gmean  Gsd   2xSh    wf    turn   trades  dd2x")
for cm in (1.01, 0.98, 0.95, 0.92, 0.90, 0.87, 0.85, 0.80, 0.75, 0.70):
    a = phase_mean(6, crowd_max=cm)
    print(f"  {cm:5.2f}   {a[0]:6.1f} {a[1]:5.1f}  {a[2]:+.2f}  {a[3]:+.2f}  {a[4]:5.1f}x  {a[5]:6d}  {a[6]:.1%}")

print("\n=== same at cadence 3 and 9 ===")
for cad in (3, 9):
    for cm in (1.01, 0.95, 0.90, 0.85, 0.80):
        a = phase_mean(cad, crowd_max=cm)
        print(f"cad={cad} crowd_max={cm:5.2f}  Gmean={a[0]:6.1f} sd={a[1]:5.1f} 2xSh={a[2]:+.2f} wf={a[3]:+.2f} turn={a[4]:5.1f}x tr={a[5]}")

print("\n=== crowd lookback (cad=6, crowd_max=0.90) ===")
for cl in (21, 42, 63, 90, 126, 189):
    a = phase_mean(6, crowd_lb=cl, crowd_max=0.90)
    print(f"crowd_lb={cl:4d}  Gmean={a[0]:6.1f} sd={a[1]:5.1f} 2xSh={a[2]:+.2f} wf={a[3]:+.2f} turn={a[4]:5.1f}x tr={a[5]}")
