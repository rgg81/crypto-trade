"""Holding-horizon / turnover mapping.

Round-1 books at cadence 3 ran 227x annualised one-way turnover against a 25x floor and
4 bps of gross edge per unit turnover against a 40 bps floor. Both are the same fact: the
book was rotating far faster than the alpha accumulates. This maps the horizon axis, and
adds the laddered (overlapping-sleeve) construction, which decouples formation frequency
from holding period: the emitted book is the average of the last M formation portfolios,
so turnover falls roughly as 1/M while the signal stays as fresh as its formation.
"""

from __future__ import annotations

import itertools
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import load  # noqa: E402
from sim import evaluate, summary  # noqa: E402
from signals import rebalance_mask, rolling_means, to_weights, xs_orthogonalise  # noqa: E402
from sweep import fz  # noqa: E402


def ladder(W: np.ndarray, cadence: int, rungs: int) -> np.ndarray:
    """Average the last ``rungs`` formation portfolios, spaced ``cadence`` bars apart."""
    if rungs <= 1:
        return W
    out = np.zeros_like(W)
    cnt = np.zeros(len(W))
    for j in range(rungs):
        sh = j * cadence
        if sh == 0:
            out += W
            cnt += 1.0
        else:
            out[sh:] += W[:-sh]
            cnt[sh:] += 1.0
    return out / np.maximum(cnt, 1.0)[:, None]


def book(panel, score, *, n_side, cadence, phase, rungs, scheme="equal", sign=-1.0):
    n_t = panel["opens"].shape[0]
    W0 = to_weights(sign * score, panel["elig"], n_side=n_side, scheme=scheme)
    W = ladder(W0, cadence, rungs)
    # a laddered book can only be executed where every rung's name is still eligible
    W = np.where(panel["elig"], W, 0.0)
    reb = rebalance_mask(n_t, cadence, phase)
    W[~reb] = 0.0
    return evaluate(panel, W, reb)


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    lev21 = rm[20]

    scores = {
        "fz_3_21": fz(rm, rate, 3, 21),
        "fz_6_21": fz(rm, rate, 6, 21),
        "fz_1_21": fz(rm, rate, 1, 21),
    }
    scores["fz_3_21_orth"] = xs_orthogonalise(scores["fz_3_21"], lev21, elig)
    scores["fz_6_21_orth"] = xs_orthogonalise(scores["fz_6_21"], lev21, elig)
    scores["LEVEL_21"] = lev21  # the control: team 07's territory, never a candidate

    rows = []
    t0 = time.time()
    grid = list(
        itertools.product(
            sorted(scores),
            [6],  # n_side
            [(3, 1), (3, 3), (3, 7), (3, 14), (9, 1), (9, 3), (9, 7), (21, 1), (21, 3), (45, 1)],
        )
    )
    for name, n_side, (cadence, rungs) in grid:
        best = None
        for phase in range(cadence):
            m = book(panel, scores[name], n_side=n_side, cadence=cadence, phase=phase, rungs=rungs)
            s = summary(m)
            s.update(score=name, n=n_side, cad=cadence, rungs=rungs, ph=phase)
            rows.append(s)
            if best is None or s["sh1"] > best["sh1"]:
                best = s
        med = np.median([r["sh1"] for r in rows[-cadence:]])
        print(
            f"{name:<14} n={n_side} cad={cadence:<2} rungs={rungs:<2} "
            f"| sh1 med={med:+.2f} best={best['sh1']:+.2f} | turn={best['turn']:6.1f} "
            f"edge={best['edge']:6.1f} vol={best['vol']:.3f} worst={best['worst']:+.2f} "
            f"| {time.time()-t0:5.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_horizon.csv", index=False
    )


if __name__ == "__main__":
    main()
