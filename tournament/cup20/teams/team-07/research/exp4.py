import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from book import ev, targets
from strat import data
from sim2 import simulate, reference_scalars, metrics, G

p = data()
EDGES = ["2021-08-01","2022-08-01","2023-08-01"]

def legs(tag, **kw):
    tl = targets(**kw)
    ref, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, p["grid"])
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    idx = r1.index
    e = [idx[0]] + [pd.Timestamp(x, tz="UTC") for x in EDGES] + [idx[-1] + pd.Timedelta(hours=8)]
    rows = []
    for a, b in zip(e[:-1], e[1:]):
        s = r1[(r1.index >= a) & (r1.index < b)]
        rows.append((s["price"].sum(), s["fund"].sum(), -s["cost"].sum(), s["net"].sum()))
    print(f"{tag:28s} " + "  ".join(f"[p{p_:+.3f} f{f_:+.3f} c{c_:+.3f} = {n_:+.3f}]" for p_,f_,c_,n_ in rows))
    return r1

print("=== leg decomposition: protection OFF vs ON (cad=6 ph=0) ===")
legs("no veto", crowd_max=1.01)
legs("veto crowd>0.90", crowd_max=0.90)
legs("veto crowd>0.80", crowd_max=0.80)

print("\n=== aggregate crowding brake: cut gross when market premium-duration is high ===")
def phase_mean(cad, **kw):
    gs, sh, wf, tn, tr, dd, vol = [], [], [], [], [], [], []
    for ph in range(cad):
        m1, m2, r1, r2, t = ev(cadence=cad, phase=ph, **kw)
        gs.append(G(m2)); sh.append(m2["sharpe"]); wf.append(m2["worst_fold"]); tn.append(m1["turn_ann"])
        tr.append(t); dd.append(m2["maxdd"]); vol.append(m1["vol"])
    return np.mean(gs), np.std(gs), np.mean(sh), np.mean(wf), np.mean(tn), int(np.mean(tr)), np.mean(dd), np.mean(vol)

for bl in (0, 21, 63):
    for bm, bf in ((1.01,0.0),(0.75,0.0),(0.70,0.0),(0.65,0.0),(0.60,0.0),(0.70,0.5),(0.65,0.5)):
        if bl == 0 and bm < 1.0:
            continue
        a = phase_mean(6, brake_lb=bl, brake_max=bm, brake_floor=bf)
        print(f"brake_lb={bl:3d} max={bm:4.2f} floor={bf:3.1f}  Gmean={a[0]:6.1f} sd={a[1]:5.1f} "
              f"2xSh={a[2]:+.2f} wf={a[3]:+.2f} dd={a[6]:.1%} vol={a[7]:.1%} tr={a[5]}")

print("\n=== symmetric veto (also drop entrenched-short names from the LONG sleeve) ===")
for cmin in (-0.01, 0.05, 0.10, 0.20):
    a = phase_mean(6, symmetric=True, crowd_min=cmin)
    print(f"crowd_min={cmin:5.2f}  Gmean={a[0]:6.1f} sd={a[1]:5.1f} 2xSh={a[2]:+.2f} wf={a[3]:+.2f} tr={a[5]}")
