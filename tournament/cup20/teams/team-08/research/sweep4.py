"""Edge-per-turnover search: concentration x threshold x holding structure.

The decay profile says the level's edge is 100% carry (price leg NEGATIVE) accumulating
over 60+ bars, while the dynamics edge is ~88% PRICE and peaks at 9 bars. The dynamics
signal is therefore in a different economic place entirely -- but it is also faster, and
the tournament charges 7.5 bps per side against a 40 bps-per-unit-turnover floor.

Three levers raise edge per unit turnover without touching the mechanism:
  concentration  n=3 doubles the per-rotation alpha versus n=10 (22.6 vs 6.5 bps at H=9)
  threshold      trade only where the funding move is a genuine shock; stay flat otherwise
  hysteresis     keep a name until it leaves a wider band, so turnover is paid once
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
from signals import rebalance_mask, rolling_means, xs_orthogonalise, xs_z  # noqa: E402
from sweep import fz  # noqa: E402


def select_book(score, elig, *, n_side, threshold, hysteresis, reb):
    """Top/bottom-n_side by score, gated at |z| >= threshold, with a hysteresis band.

    ``hysteresis`` widens the exit band: a name already held stays while it remains in
    the top/bottom ``n_side + hysteresis``. Turnover is then paid on genuine changes of
    conviction rather than on rank noise.
    """
    z = xs_z(score, elig)
    n_t, n_s = score.shape
    W = np.zeros((n_t, n_s))
    prev_long: set[int] = set()
    prev_short: set[int] = set()
    keep = n_side + hysteresis
    for t in range(n_t):
        if not reb[t]:
            continue
        m = elig[t] & np.isfinite(z[t])
        idx = np.flatnonzero(m)
        if len(idx) < 2 * n_side:
            prev_long, prev_short = set(), set()
            continue
        v = z[t, idx]
        order = np.argsort(v)
        ranked = idx[order]
        # short the highest scores (funding above its own regime), long the lowest
        cand_s = list(ranked[-n_side:])
        cand_l = list(ranked[:n_side])
        keep_s = [i for i in ranked[-keep:] if i in prev_short]
        keep_l = [i for i in ranked[:keep] if i in prev_long]
        sel_s = list(dict.fromkeys(keep_s + cand_s))[:n_side] if hysteresis else cand_s
        sel_l = list(dict.fromkeys(keep_l + cand_l))[:n_side] if hysteresis else cand_l
        if threshold > 0:
            sel_s = [i for i in sel_s if z[t, i] >= threshold]
            sel_l = [i for i in sel_l if z[t, i] <= -threshold]
            k = min(len(sel_s), len(sel_l))
            sel_s, sel_l = sel_s[:k], sel_l[:k]
        if not sel_s:
            prev_long, prev_short = set(), set()
            continue
        w = 0.5 / len(sel_s)
        W[t, sel_s] = -w
        W[t, sel_l] = +w
        prev_long, prev_short = set(sel_l), set(sel_s)
    return W


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    lev21 = rm[20]
    n_t = panel["opens"].shape[0]

    scores = {
        "fz3_21o": xs_orthogonalise(fz(rm, rate, 3, 21), lev21, elig),
        "fz1_21o": xs_orthogonalise(fz(rm, rate, 1, 21), lev21, elig),
        "fz3_21": fz(rm, rate, 3, 21),
    }

    rows = []
    t0 = time.time()
    grid = list(
        itertools.product(
            sorted(scores), [2, 3, 4], [3, 6, 9], [0.0, 0.7, 1.2], [0, 2, 4]
        )
    )
    for name, n_side, cadence, thr, hyst in grid:
        per_phase = []
        for phase in range(cadence):
            reb = rebalance_mask(n_t, cadence, phase)
            W = select_book(
                scores[name], elig, n_side=n_side, threshold=thr, hysteresis=hyst, reb=reb
            )
            m = evaluate(panel, W, reb)
            s = summary(m)
            s.update(score=name, n=n_side, cad=cadence, thr=thr, hyst=hyst, ph=phase)
            rows.append(s)
            per_phase.append(s)
        med = {
            k: float(np.median([r[k] for r in per_phase]))
            for k in ("sh1", "sh2", "worst", "turn", "edge", "vol", "dd2", "L", "S", "trades")
        }
        print(
            f"{name:<8} n={n_side} cad={cadence} thr={thr:.1f} hy={hyst} | "
            f"sh1={med['sh1']:+.2f} sh2={med['sh2']:+.2f} worst={med['worst']:+.2f} "
            f"turn={med['turn']:6.1f} edge={med['edge']:6.1f} vol={med['vol']:.3f} "
            f"dd2={med['dd2']:.2f} L={med['L']:+.2f} S={med['S']:+.2f} tr={med['trades']:.0f}"
            f" | {time.time()-t0:5.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_edge.csv", index=False
    )


if __name__ == "__main__":
    main()
