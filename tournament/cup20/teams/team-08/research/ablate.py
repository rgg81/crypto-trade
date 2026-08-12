"""The ablation matrix and the dynamics-versus-level control, run offline first.

The lane's central hazard is that a funding-dynamics book is really a funding-LEVEL book in
disguise, because level and change are correlated. This runs every variant through the
IDENTICAL machinery -- same event clock, same concentration, same dispersion gate, same
holding period -- and changes only the score:

  spread        the nominee: (mean of the last KS funding events - mean of the last KL),
                divided by the coin's own funding standard deviation over KL
  spread_orth   the same spread with the cross-sectional funding LEVEL regressed out, so
                nothing the level can explain survives
  level         the funding level itself: team 07's economics wearing team 08's machinery
  raw_change    the spread WITHOUT the own-units denominator (controls-off)
  no_gate       the nominee with the dispersion gate removed
  shuffled      the nominee's score randomly permuted across the eligible cross-section at
                each boundary: the machinery alone, with the mechanism removed

It also reports, for every book, the fraction of gross PnL that is funding carry and the
mean cross-sectional correlation between the emitted weights and the funding level. A book
whose weights barely correlate with the level, and whose PnL is not carry, is not a level
book whatever its inputs are made of.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import load  # noqa: E402
from sim import evaluate, summary  # noqa: E402
from signals import rolling_means, xs_orthogonalise  # noqa: E402
from sweep5 import mean_spread  # noqa: E402
from sweep7 import dispersion_rank  # noqa: E402
from sweep8 import event_book  # noqa: E402

KS, KL, HOLD, GATE, NSIDE = 3, 30, 9, 0.35, 1


def weight_level_correlation(W, level, elig):
    out = []
    for t in range(len(W)):
        m = elig[t] & np.isfinite(level[t]) & (np.abs(W[t]) > 0)
        if m.sum() < 2:
            continue
        w, x = W[t, m], level[t, m]
        if np.std(w) <= 0 or np.std(x) <= 0:
            continue
        out.append(float(np.corrcoef(w, x)[0, 1]))
    return float(np.mean(out)) if out else float("nan")


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    level = rm[KL - 1]
    rng = np.random.default_rng(20240801)

    spread = mean_spread(rm, rate, KS, KL)
    variants = {
        "spread (nominee)": (spread, GATE),
        "spread_orth": (xs_orthogonalise(spread, level, elig), GATE),
        "level": (level, GATE),
        "raw_change": (rm[KS - 1] - rm[KL - 1], GATE),
        "no_gate": (spread, 0.0),
    }
    shuffled = np.full(spread.shape, np.nan)
    for t in range(len(spread)):
        idx = np.flatnonzero(elig[t] & np.isfinite(spread[t]))
        if len(idx) > 1:
            shuffled[t, idx] = spread[t, rng.permutation(idx)]
    variants["shuffled"] = (shuffled, GATE)

    disp = dispersion_rank(spread, elig, 270)
    # A gate that admits the same FRACTION of boundaries but chooses them at random. This is
    # the "you only traded less" null for the dispersion gate: if trading fewer boundaries is
    # what helps, a random gate of the same selectivity helps as much.
    accept = float((disp >= GATE).mean())
    random_gate = rng.permutation(disp)
    print(f"(dispersion gate admits {accept:.1%} of boundaries; random control matched)\n")
    rows = []
    variants["random_gate"] = (spread, GATE)
    for name, (score, gate) in variants.items():
        if name == "random_gate":
            d = random_gate
        elif name in ("level", "raw_change"):
            d = dispersion_rank(score, elig, 270)
        else:
            d = disp
        W, reb = event_book(score, elig, d, n_side=NSIDE, hold=HOLD, gate=gate)
        m = evaluate(panel, W, reb)
        s = summary(m)
        gross = m["price_pnl_share"] + m["fund_pnl_share"]
        s["carry_share"] = m["fund_pnl_share"] / gross if gross != 0 else float("nan")
        s["w_level_corr"] = weight_level_correlation(W, level, elig)
        s["variant"] = name
        rows.append(s)
        print(
            f"{name:<18} sh1={s['sh1']:+.2f} sh2={s['sh2']:+.2f} worst={s['worst']:+.2f} "
            f"med={s['median']:+.2f} dd2={s['dd2']:.2f} turn={s['turn']:5.1f} "
            f"edge={s['edge']:5.1f} L={s['L']:+.2f} S={s['S']:+.2f} tr={s['trades']:5d} "
            f"G={s['G']:6.1f} | carry_share={s['carry_share']:+.2f} "
            f"w~level corr={s['w_level_corr']:+.3f} folds={s['folds']}",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/ablation_matrix.csv", index=False
    )


if __name__ == "__main__":
    main()
