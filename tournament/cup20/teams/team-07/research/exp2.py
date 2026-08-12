import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np
from strat import build, evaluate
from sim2 import G

print("=== weighting scheme x breadth (carry_lb=63, risk_lb=63, cad=9, ph=0) ===")
for n in (5, 6, 7, 8, 9):
    evaluate(build(n_side=n, scheme="topn"), f"topn n={n}")
for rp in (0.5, 1.0, 1.5, 2.0):
    evaluate(build(scheme="cont", risk_power=rp), f"cont risk_power={rp}")

print("\n=== cadence x phase, phase-agnostic mean G  (topn n=7) ===")
for cad in (1, 3, 6, 9, 12, 21):
    gs = []
    for ph in range(cad):
        m1, m2, r1, r2, tr = evaluate(build(n_side=7, cadence=cad, phase=ph), quiet=True)
        gs.append((G(m2), m2["sharpe"], m2["worst_fold"], m1["turn_ann"], tr))
    arr = np.array([x[0] for x in gs])
    print(f"cad={cad:3d}  G mean={arr.mean():6.1f} sd={arr.std():5.1f} min={arr.min():6.1f} max={arr.max():6.1f} "
          f"| 2xSh mean={np.mean([x[1] for x in gs]):+.2f} wf mean={np.mean([x[2] for x in gs]):+.2f} "
          f"turn={np.mean([x[3] for x in gs]):.1f}x trades={int(np.mean([x[4] for x in gs]))}")

print("\n=== cadence x phase, phase-agnostic mean G  (cont risk_power=1.0) ===")
for cad in (3, 6, 9, 12, 21):
    gs = []
    for ph in range(cad):
        m1, m2, r1, r2, tr = evaluate(build(scheme="cont", risk_power=1.0, cadence=cad, phase=ph), quiet=True)
        gs.append((G(m2), m2["sharpe"], m2["worst_fold"], m1["turn_ann"], tr))
    arr = np.array([x[0] for x in gs])
    print(f"cad={cad:3d}  G mean={arr.mean():6.1f} sd={arr.std():5.1f} min={arr.min():6.1f} max={arr.max():6.1f} "
          f"| 2xSh mean={np.mean([x[1] for x in gs]):+.2f} wf mean={np.mean([x[2] for x in gs]):+.2f} "
          f"turn={np.mean([x[3] for x in gs]):.1f}x trades={int(np.mean([x[4] for x in gs]))}")
