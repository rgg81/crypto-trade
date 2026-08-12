"""The state-driven clock: entries set by the gate, not by an arbitrary phase offset.

The refinement round exposed the real robustness problem. At one name a side and a 9-15
bar cadence the SAME design scores anywhere in a 1.1 to 2.0 Sharpe band depending purely
on which boundary the rebalance clock starts on. A nominee at a fixed phase is a lottery
ticket, and the charter is explicit that a cadence result run at one phase is a result
about that phase.

The fix is to stop having a phase. Positions are opened when the dispersion gate opens and
we are flat, held for exactly HOLD bars, then closed; the next entry is the next boundary at
which the gate is open. The clock is set by the data rather than by an offset, so there is no
phase parameter to sweep -- but the residual dependence on WHERE the sequence starts is still
measured here, by forcing the strategy to sit out its first ``offset`` boundaries.
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
from signals import rolling_means  # noqa: E402
from sweep5 import mean_spread  # noqa: E402
from sweep7 import dispersion_rank  # noqa: E402


def event_book(score, elig, disp, *, n_side, hold, gate, offset=0, min_xs=8):
    """Enter when the gate opens and we are flat; hold ``hold`` bars; exit; repeat."""
    n_t, n_s = score.shape
    W = np.zeros((n_t, n_s))
    reb = np.zeros(n_t, dtype=bool)
    held = 0
    invested = False
    for t in range(n_t):
        if t < offset:
            continue
        if invested:
            held += 1
            if held < hold:
                continue
        m = elig[t] & np.isfinite(score[t])
        idx = np.flatnonzero(m)
        can_enter = (
            len(idx) >= max(min_xs, 2 * n_side + 2) and (gate <= 0.0 or disp[t] >= gate)
        )
        if can_enter:
            ranked = idx[np.argsort(score[t, idx])]
            w = 0.5 / n_side
            W[t, ranked[-n_side:]] = -w
            W[t, ranked[:n_side]] = +w
            reb[t] = True
            invested = True
            held = 0
        elif invested:
            reb[t] = True  # target all-zero: close out, the alpha window has expired
            invested = False
            held = 0
    return W, reb


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)

    rows = []
    t0 = time.time()
    cache = {}
    grid = list(
        itertools.product(
            [(2, 21), (3, 21), (3, 27), (3, 30), (4, 21), (6, 21), (3, 15)],
            [1, 2],
            [6, 9, 12, 15],
            [0.0, 0.30, 0.45, 0.60],
        )
    )
    for (ks, kl), n_side, hold, dg in grid:
        if (ks, kl) not in cache:
            s = mean_spread(rm, rate, ks, kl)
            cache[(ks, kl)] = (s, dispersion_rank(s, elig, 270))
        score, disp = cache[(ks, kl)]
        per = []
        for offset in (0, 2, 4, 6):
            W, reb = event_book(
                score, elig, disp, n_side=n_side, hold=hold, gate=dg, offset=offset
            )
            m = evaluate(panel, W, reb)
            s = summary(m)
            s.update(ks=ks, kl=kl, n=n_side, hold=hold, dg=dg, off=offset)
            rows.append(s)
            per.append(s)
        med = {
            k: float(np.median([r[k] for r in per]))
            for k in ("sh1", "sh2", "worst", "median", "turn", "edge", "vol", "dd2", "L", "S",
                      "trades", "G_eff", "posq2", "cal2", "G")
        }
        spread = max(r["sh1"] for r in per) - min(r["sh1"] for r in per)
        print(
            f"ks={ks} kl={kl:<2} n={n_side} H={hold:<2} dg={dg:.2f} | "
            f"sh1={med['sh1']:+.2f}(spr{spread:.2f}) sh2={med['sh2']:+.2f} "
            f"worst={med['worst']:+.2f} med={med['median']:+.2f} turn={med['turn']:5.1f} "
            f"edge={med['edge']:5.1f} vol={med['vol']:.3f} dd2={med['dd2']:.2f} "
            f"cal2={med['cal2']:+.2f} L={med['L']:+.2f} S={med['S']:+.2f} tr={med['trades']:.0f} "
            f"G={med['G']:5.1f} Ge={med['G_eff']:5.1f} | {time.time()-t0:5.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_event.csv", index=False
    )


if __name__ == "__main__":
    main()
