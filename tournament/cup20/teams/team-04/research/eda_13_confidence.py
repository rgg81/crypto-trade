"""EDA 13 -- what Sharpe the trial-adjusted confidence floor actually demands.

`confidence = 1 - T*(1-B)` against a 0.90 floor, with T the complete accepted trial count and B
the per-point median bootstrap positive fraction. At the eight-trial minimum a candidate needs
B >= 0.9875. This measures B directly, using the organiser's own bootstrap on the offline
simulator's daily returns -- the simulator reproduced trial #30's Sharpe to 0.01, so B computed
on it is a fair estimate of the B the harness would report.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from crypto_trade.cup20.bootstrap import (  # noqa: E402
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)

from book import simulate  # noqa: E402
from eda_03_portfolio import FUND, grid, make_signal, opens, start  # noqa: E402
from eda_09_asym import build  # noqa: E402


def B_of(sig, K, ml, ms, phase):
    w, reb = build(sig, K, phase, ml, ms)
    res = simulate(w, reb, opens, FUND, start)
    daily = pd.Series(res["net"], index=grid[start:]).resample("1D").sum()
    b = circular_block_bootstrap_positive_fraction(daily)
    sh = float(daily.mean() / daily.std() * np.sqrt(365.0))
    return b, sh


if __name__ == "__main__":
    print("required B for confidence >= 0.90:")
    for T in (8, 9, 10, 11, 12):
        print(f"  T={T:>2}  B >= {1 - 0.10 / T:.4f}")
    print()
    print(f"{'config':<26} {'B med':>7} {'B min':>7} {'B max':>7} {'Sh med':>7} "
          f"{'conf@T=8':>9} {'conf@T=10':>10}")
    for kind in ("resid", "raw"):
        sig, _ = make_signal(kind, 270, 63, 1)
        for K, ml, ms in ((21, 7, 7), (24, 7, 4), (30, 7, 4), (21, 7, 4)):
            bs, shs = [], []
            for p in range(K):
                b, s = B_of(sig, K, ml, ms, p)
                bs.append(b)
                shs.append(s)
            bm = float(np.median(bs))
            print(f"{kind} F=63 K={K} L{ml}/S{ms:<8} {bm:>7.4f} {min(bs):>7.4f} {max(bs):>7.4f} "
                  f"{np.median(shs):>7.2f} {trial_adjusted_confidence(bm, 8):>9.3f} "
                  f"{trial_adjusted_confidence(bm, 10):>10.3f}")
