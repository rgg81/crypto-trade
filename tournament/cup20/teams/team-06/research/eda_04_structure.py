"""Team 06 EDA 4 -- the structural axes, judged on the objective the tournament actually ranks on.

Axes, in the order the mandate makes them interesting:
  1. score family      -- plain volatility (the ablation) vs left-tail depth vs drawdown geometry
  2. skip              -- is the selection forward-looking (chronic character) or backward-looking
                          (whatever crashed last week)?
  3. formation horizon
  4. beta balance
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from lab import evaluate, line  # noqa: E402
from signals import build_book, characteristics, load_panel  # noqa: E402

P = load_panel()
START = pd.Timestamp("2020-08-17", tz="UTC")
FAMILIES = ["sigma", "semidev", "cvar", "maxdd", "dd_pair", "cvar_dd", "downside", "mandate", "resid"]
FAMILIES = [f for f in FAMILIES if f != "underwater_x"]

cache: dict[tuple[int, int], dict] = {}


def feats(n: int, skip: int) -> dict:
    key = (n, skip)
    if key not in cache:
        cache[key] = characteristics(P["closes"], P["member"], n, skip)
    return cache[key]


def run(family, n, skip, k, cadence, phase, bb):
    F = feats(n, skip)
    W = build_book(
        P, F, family=family, k=k, cadence=cadence, phase=phase, beta_balance=bb, start=START
    )
    W = W.loc[W.index >= START]
    m = evaluate(W, P["opens"], P["funding"])
    tag = f"{family:9s} n={n:3d} skip={skip:2d} k={k} c={cadence} p={phase} bb={int(bb)}"
    print(line(tag, m), flush=True)
    return m


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "families"
    if which == "families":
        print("--- score family x formation, weekly cadence, k=6, beta-balanced ---")
        for n in (126, 189, 252, 315):
            for fam in FAMILIES:
                run(fam, n, 0, 6, 21, 0, True)
            print()
    elif which == "skip":
        print("--- skip: chronic character vs the last crash ---")
        for n in (189, 252):
            for skip in (0, 9, 21, 63):
                for fam in ("sigma", "cvar", "downside", "mandate"):
                    run(fam, n, skip, 6, 21, 0, True)
                print()
    elif which == "bb":
        print("--- beta balance on/off ---")
        for fam in ("sigma", "cvar", "cvar_dd", "downside"):
            for bb in (False, True):
                run(fam, 126, 0, 6, 21, 0, bb)
    elif which == "k":
        print("--- breadth ---")
        for fam in ("mandate", "sigma"):
            for k in (5, 6, 7, 8):
                run(fam, 252, 0, k, 21, 0, True)
            print()
    elif which == "cadence":
        print("--- cadence and phase (phase is a first-order axis, not a detail) ---")
        for cadence in (9, 21, 42):
            for phase in range(0, cadence, max(1, cadence // 7)):
                run("mandate", 252, 0, 6, cadence, phase, True)
            print()
    elif which == "controls":
        print("--- controls-off / individual / combined (control A = beta balance, B = skip) ---")
        for bb in (False, True):
            for skip in (0, 9):
                run("mandate", 252, skip, 6, 21, 0, bb)
                run("sigma", 252, skip, 6, 21, 0, bb)
