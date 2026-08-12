"""Refinement around the working region, with the phase spread reported explicitly.

Working region from round 5: the single term spread (mean of the last KS funding events
minus the mean of the last KL, in the coin's own funding standard deviations), one name a
side, rebalanced every 9 bars, traded only when the cross-sectional dispersion of that
spread is in the upper part of its own trailing distribution.

Every row is the MEDIAN over all rebalance phase offsets, and the phase spread (p90-p10 of
Sharpe across offsets) is reported beside it, because a single-phase number at this cadence
is a statement about that phase.
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
from signals import rebalance_mask, rolling_means, xs_z  # noqa: E402
from sweep5 import build_book, mean_spread  # noqa: E402


def dispersion_rank(score, elig, window):
    d = np.where(elig & np.isfinite(score), score, np.nan)
    sd = np.nanstd(d, axis=1)
    return np.nan_to_num(
        pd.Series(sd).rolling(window, min_periods=window // 3).rank(pct=True).to_numpy(), nan=1.0
    )


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    n_t = panel["opens"].shape[0]

    rows = []
    t0 = time.time()
    cache = {}
    grid = list(
        itertools.product(
            [(1, 21), (2, 21), (3, 15), (3, 21), (3, 27), (4, 21), (6, 21), (3, 30)],
            [1, 2],
            [9, 12, 15],
            [0.30, 0.45, 0.60],
        )
    )
    for (ks, kl), n_side, cadence, dg in grid:
        if (ks, kl) not in cache:
            s = mean_spread(rm, rate, ks, kl)
            cache[(ks, kl)] = (s, dispersion_rank(s, elig, 270))
        score, disp = cache[(ks, kl)]
        per = []
        for phase in range(cadence):
            reb = rebalance_mask(n_t, cadence, phase)
            W = build_book(score, elig, n_side=n_side, reb=reb, disp_gate=dg, disp=disp)
            m = evaluate(panel, W, reb)
            s = summary(m)
            s.update(ks=ks, kl=kl, n=n_side, cad=cadence, dg=dg, ph=phase)
            rows.append(s)
            per.append(s)
        med = {
            k: float(np.median([r[k] for r in per]))
            for k in ("sh1", "sh2", "worst", "median", "turn", "edge", "vol", "dd2", "L", "S",
                      "trades", "G_eff", "posq2", "cal2")
        }
        sh1s = sorted(r["sh1"] for r in per)
        spread = sh1s[-1] - sh1s[0]
        print(
            f"ks={ks} kl={kl:<2} n={n_side} cad={cadence:<2} dg={dg:.2f} | "
            f"sh1={med['sh1']:+.2f}(spr{spread:.2f}) sh2={med['sh2']:+.2f} "
            f"worst={med['worst']:+.2f} med={med['median']:+.2f} turn={med['turn']:5.1f} "
            f"edge={med['edge']:5.1f} vol={med['vol']:.3f} dd2={med['dd2']:.2f} "
            f"L={med['L']:+.2f} S={med['S']:+.2f} tr={med['trades']:.0f} "
            f"Ge={med['G_eff']:5.1f} | {time.time()-t0:5.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_refine.csv", index=False
    )


if __name__ == "__main__":
    main()
