import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np
from strat import build, evaluate

print("=== sizing: equal vs inverse-vol (carry_lb=63, cad=9, ph=0) ===")
for sizing in ("equal", "invvol"):
    for n in (5, 7, 8, 10):
        evaluate(build(n_side=n, sizing=sizing), f"{sizing} n={n}")

print("\n=== carry lookback (invvol, n=8, cad=9) ===")
for lb in (9, 21, 42, 63, 90, 126):
    evaluate(build(carry_lb=lb, n_side=8, sizing="invvol"), f"carry_lb={lb}")

print("\n=== risk lookback (invvol, n=8, carry_lb=63, cad=9) ===")
for rl in (21, 42, 63, 126, 189):
    evaluate(build(risk_lb=rl, n_side=8, sizing="invvol"), f"risk_lb={rl}")
