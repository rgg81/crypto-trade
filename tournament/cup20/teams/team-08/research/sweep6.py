"""The overlapping-sleeve (ladder) construction at full concentration.

Concentration and phase-robustness looked like opposites: one name a side gives 22.6 bps
per unit gross at nine bars where ten names give 6.5, but a one-name book at a nine-bar
cadence is nine different books depending on which boundary the clock starts on, and the
phase spread on this window is worth more than a full point of Sharpe.

They are not opposites. A ladder of H one-name sleeves, one opened at every boundary and
each held H bars, holds every phase at once. Its alpha per unit gross is the average of the
sleeves' -- i.e. the alpha of the concentrated book, undiluted, because each sleeve is still
a top-1 pick, just at a different formation time. What falls is the DENOMINATOR: sigma per
unit gross drops with the diversification across formation dates. Since

    sharpe = (annual alpha per unit gross - annual cost per unit gross) / sigma_unit_gross

with the numerator unchanged, the ladder strictly dominates -- and it has no phase axis at
all, because it contains every phase.
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
from signals import rolling_means, xs_orthogonalise, xs_z  # noqa: E402
from sweep5 import mean_spread  # noqa: E402


def formation_books(score, elig, *, n_side, gate=None, gate_level=0.0):
    z = xs_z(score, elig)
    n_t, n_s = score.shape
    W = np.zeros((n_t, n_s))
    for t in range(n_t):
        if gate is not None and gate_level > 0 and gate[t] < gate_level:
            continue
        m = elig[t] & np.isfinite(z[t])
        idx = np.flatnonzero(m)
        if len(idx) < 2 * n_side + 2:
            continue
        ranked = idx[np.argsort(z[t, idx])]
        w = 0.5 / n_side
        W[t, ranked[-n_side:]] = -w
        W[t, ranked[:n_side]] = +w
    return W


def ladder(W, hold, cadence=1):
    """Average the formation books opened at t, t-cadence, ... spanning ``hold`` bars."""
    rungs = max(1, hold // cadence)
    out = np.zeros_like(W)
    for j in range(rungs):
        sh = j * cadence
        if sh == 0:
            out += W
        else:
            out[sh:] += W[:-sh]
    return out / rungs


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    lev21 = rm[20]

    blend = np.nanmean(
        np.stack(
            [
                mean_spread(rm, rate, 1, 21),
                mean_spread(rm, rate, 3, 21),
                mean_spread(rm, rate, 3, 30),
                mean_spread(rm, rate, 6, 21),
            ]
        ),
        axis=0,
    )
    scores = {"blend": blend, "blend_o": xs_orthogonalise(blend, lev21, elig)}
    d = np.where(elig & np.isfinite(scores["blend_o"]), scores["blend_o"], np.nan)
    disp = np.nan_to_num(
        pd.Series(np.nanstd(d, axis=1)).rolling(270, min_periods=90).rank(pct=True).to_numpy(),
        nan=1.0,
    )

    rows = []
    t0 = time.time()
    for name, n_side, hold, dg in itertools.product(
        ["blend", "blend_o"], [1, 2, 3], [6, 9, 15, 21, 30], [0.0, 0.35, 0.6]
    ):
        W0 = formation_books(scores[name], elig, n_side=n_side, gate=disp, gate_level=dg)
        W = ladder(W0, hold, cadence=1)
        W = np.where(elig, W, 0.0)
        reb = np.ones(len(W), dtype=bool)
        m = evaluate(panel, W, reb)
        s = summary(m)
        s.update(score=name, n=n_side, hold=hold, dg=dg)
        rows.append(s)
        print(
            f"{name:<8} n={n_side} H={hold:<2} dg={dg:.2f} | sh1={s['sh1']:+.2f} "
            f"sh2={s['sh2']:+.2f} worst={s['worst']:+.2f} med={s['median']:+.2f} "
            f"turn={s['turn']:6.1f} edge={s['edge']:6.1f} vol={s['vol']:.3f} dd2={s['dd2']:.2f} "
            f"L={s['L']:+.2f} S={s['S']:+.2f} tr={s['trades']} G={s['G']:5.1f} "
            f"Ge={s['G_eff']:5.1f} | {time.time()-t0:4.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_ladder.csv", index=False
    )


if __name__ == "__main__":
    main()
