"""Blending the formation windows, to make the surface something a MEDIAN can be taken of.

The plateau map is honest about a problem. At one name a side the book is two positions, so
the full-window Sharpe is a noisy function of the formation windows: at a 12-bar hold, a
2-event short leg medians to G=+37 while a 3-event short leg medians to G=-6, and the sign of
that difference flips at a 9-bar hold. A nominee sitting on one cell of that surface has a
neighbourhood median far below its own value, which is exactly what section 7.2 is for.

The standard fix is to stop choosing a cell. Averaging the term spread over several formation
windows keeps the mechanism identical -- it is still current-leg versus own-regime in own
units -- while removing the arbitrary choice of which window states it. If the blended surface
is both good AND flat, its neighbourhood median is close to its nominee, which is the
property worth having.
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
from sweep8 import event_book  # noqa: E402
from sweep9 import half_sharpes  # noqa: E402


def blend(rm, rate, ks_list, kl_list):
    return np.nanmean(
        np.stack([mean_spread(rm, rate, ks, kl) for ks in ks_list for kl in kl_list]), axis=0
    )


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)

    scores = {
        "single_2_30": blend(rm, rate, [2], [30]),
        "blend_kl": blend(rm, rate, [2], [24, 30, 36]),
        "blend_ks": blend(rm, rate, [1, 2, 3], [30]),
        "blend_both": blend(rm, rate, [1, 2, 3], [24, 30, 36]),
        "blend_wide": blend(rm, rate, [1, 2, 3, 4], [21, 27, 33, 39]),
    }
    rows = []
    t0 = time.time()
    for name, hold, dg, n_side in itertools.product(
        sorted(scores), [9, 12, 15, 18], [0.20, 0.30, 0.40], [1, 2]
    ):
        score = scores[name]
        disp = dispersion_rank(score, elig, 270)
        W, reb = event_book(score, elig, disp, n_side=n_side, hold=hold, gate=dg)
        m = evaluate(panel, W, reb)
        s = summary(m)
        h1, h2 = half_sharpes(panel, W, reb)
        s.update(score=name, hold=hold, dg=dg, n=n_side, h1=h1, h2=h2)
        rows.append(s)
    df = pd.DataFrame(rows)
    df.to_csv("tournament/cup20/teams/team-08/research/sweep_blend.csv", index=False)
    pd.set_option("display.width", 250)
    keep = ["score", "hold", "dg", "n", "sh1", "sh2", "worst", "median", "dd2", "turn", "edge",
            "trades", "L", "S", "G", "h1", "h2"]
    print("=== median G by (score, n) ===")
    print(df.pivot_table(index="score", columns="n", values="G", aggfunc="median").round(1))
    print("\n=== median G by (score, hold) at n=1 ===")
    print(
        df[df.n == 1]
        .pivot_table(index="score", columns="hold", values="G", aggfunc="median")
        .round(1)
    )
    print("\n=== all n=1 rows ===")
    print(df[df.n == 1][keep].sort_values(["score", "hold", "dg"]).round(3).to_string(index=False))
    print(f"\n{len(df)} configs in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
