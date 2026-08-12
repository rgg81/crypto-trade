"""Plateau mapping around the working region, plus a half-sample stability check.

Two questions this answers before a nominee is fixed.

1. WHERE IS THE PLATEAU? The score is the neighbourhood median, so the nominee has to sit at
   the centre of a region that works, not on its best point. This maps the surface finely
   enough to see the region's shape.
2. IS THE REGION THE SAME IN BOTH HALVES OF THE WINDOW? A parameter choice that is only best
   over the whole four years can still be an artifact of the last two. The same surface is
   therefore re-scored on the first half and the second half separately, and the two are
   compared.
"""

from __future__ import annotations

import itertools
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import load  # noqa: E402
from sim import daily, evaluate, sharpe, summary  # noqa: E402
from signals import rolling_means  # noqa: E402
from sweep5 import mean_spread  # noqa: E402
from sweep7 import dispersion_rank  # noqa: E402
from sweep8 import event_book  # noqa: E402

SPLIT = pd.Timestamp("2022-08-01T00:00:00Z")


def half_sharpes(panel, W, reb):
    """1x Sharpe on each half of the window, from the same single evaluation."""
    from sim import _run, cap_rows, normalise, risk_scalars  # noqa: PLC0415

    times = pd.DatetimeIndex(panel["times"], tz="UTC")
    W_ref = cap_rows(normalise(W, reb))
    ref = _run(panel, W_ref, reb, 1.0)
    s = risk_scalars(ref["gross_ret"])
    res = _run(panel, cap_rows(W_ref * s[:, None]), reb, 1.0)
    d = daily(res["net"], times)
    idx = pd.DatetimeIndex(d.index)
    return sharpe(d[idx < SPLIT]), sharpe(d[idx >= SPLIT])


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)

    rows = []
    t0 = time.time()
    cache = {}
    grid = list(
        itertools.product(
            [2, 3, 4, 5], [21, 24, 27, 30, 36], [6, 9, 12], [0.20, 0.30, 0.40], [1, 2]
        )
    )
    for ks, kl, hold, dg, n_side in grid:
        if (ks, kl) not in cache:
            s = mean_spread(rm, rate, ks, kl)
            cache[(ks, kl)] = (s, dispersion_rank(s, elig, 270))
        score, disp = cache[(ks, kl)]
        W, reb = event_book(score, elig, disp, n_side=n_side, hold=hold, gate=dg)
        m = evaluate(panel, W, reb)
        s = summary(m)
        h1, h2 = half_sharpes(panel, W, reb)
        s.update(ks=ks, kl=kl, hold=hold, dg=dg, n=n_side, h1=h1, h2=h2)
        rows.append(s)
    df = pd.DataFrame(rows)
    df.to_csv("tournament/cup20/teams/team-08/research/sweep_plateau.csv", index=False)

    pd.set_option("display.width", 250)
    keep = ["ks", "kl", "hold", "dg", "n", "sh1", "sh2", "worst", "median", "dd2", "turn",
            "edge", "trades", "L", "S", "G", "h1", "h2"]
    top = df.sort_values("G", ascending=False)[keep].head(25)
    print("=== top 25 by G (offline estimate, not a score) ===")
    print(top.round(3).to_string(index=False))
    print(f"\n{len(df)} configs in {time.time()-t0:.0f}s")
    print(f"\nboth halves positive: {int(((df.h1 > 0) & (df.h2 > 0)).sum())} of {len(df)}")
    print(f"median G over the whole grid: {df.G.median():.1f}")


if __name__ == "__main__":
    main()
