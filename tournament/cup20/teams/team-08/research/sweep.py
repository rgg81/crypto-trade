"""Offline book sweep over the funding term-dynamics design space.

Not a scorer. Produces the map that decides where the twelve trials go.
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

MIN_SD = 2e-5  # 0.2 bp: floors the own-units denominator so a pinned-funding coin cannot explode


def build_measures(rate, bas, depth=90):
    rm = rolling_means(rate)
    bm = rolling_means(bas)
    return rm, bm


def fz(rm, rate, ks, kl, min_sd=MIN_SD):
    sd = np.nanstd(np.where(np.isfinite(rate[:kl]), rate[:kl], np.nan), axis=0)
    return (rm[ks - 1] - rm[kl - 1]) / np.maximum(sd, min_sd)


def run_one(panel, score, *, n_side, cadence, phase, scheme, sign=-1.0):
    n_t = panel["opens"].shape[0]
    reb = rebalance_mask(n_t, cadence, phase)
    W = to_weights(sign * score, panel["elig"], n_side=n_side, scheme=scheme)
    W[~reb] = 0.0
    return evaluate(panel, W, reb)


def main(mode="coarse"):
    panel, rate, bas = load()
    elig = panel["elig"]
    rm, bm = build_measures(rate, bas)
    lev = {k: rm[k - 1] for k in (15, 21, 30, 45)}
    orth_cache: dict = {}

    rows = []
    t0 = time.time()

    if mode == "coarse":
        combos = itertools.product(
            [(3, 21), (3, 30), (6, 21), (1, 21), (9, 21), (3, 45)],  # ks, kl
            [False, True],  # orthogonalise to level
            [4, 6, 8],  # n_side
            [3, 6, 9],  # cadence
            ["equal"],
        )
    else:
        combos = []

    for (ks, kl), orth, n_side, cadence, scheme in combos:
        key = (ks, kl, orth)
        if key not in orth_cache:
            s = fz(rm, rate, ks, kl)
            if orth:
                s = xs_orthogonalise(s, lev[kl], elig)
            orth_cache[key] = s
        score = orth_cache[key]
        for phase in range(cadence):
            m = run_one(
                panel, score, n_side=n_side, cadence=cadence, phase=phase, scheme=scheme
            )
            s = summary(m)
            s.update(
                ks=ks, kl=kl, orth=orth, n=n_side, cad=cadence, ph=phase, scheme=scheme
            )
            rows.append(s)
        print(
            f"{ks:>2}/{kl:<2} orth={int(orth)} n={n_side} cad={cadence} "
            f"| {time.time()-t0:6.0f}s | last sh1={s['sh1']:.2f} sh2={s['sh2']:.2f} "
            f"worst={s['worst']:.2f} turn={s['turn']:.1f} vol={s['vol']:.3f}",
            flush=True,
        )

    df = pd.DataFrame(rows)
    df.to_csv(f"tournament/cup20/teams/team-08/research/sweep_{mode}.csv", index=False)
    print(f"\n{len(df)} configs in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "coarse")
