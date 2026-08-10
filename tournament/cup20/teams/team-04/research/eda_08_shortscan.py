"""EDA 8 -- how far does the short-sleeve floor reach?

Scans formation length, holding length, sleeve width and signal sign for a gross-positive short
sleeve, and splits price from funding so the reason for the sign is visible rather than inferred.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import build_funding_matrix  # noqa: E402
from eda_03_portfolio import elig, grid, make_signal, opens, start, symbols  # noqa: E402

N = len(grid)
FUND = build_funding_matrix(grid, symbols)


def sleeve(sig, K, m, side):
    """Phase-averaged cumulative simple return of an equal-weight sleeve, price vs funding."""
    px_tot = fd_tot = 0.0
    per_fold = np.zeros(4)
    edges = [pd.Timestamp(x, tz="UTC") for x in
             ("2020-08-17", "2021-08-01", "2022-08-01", "2023-08-01", "2024-08-01")]
    for p in range(K):
        for i in range(start + p, N - K, K):
            s, e = sig[i], elig[i]
            ok = np.isfinite(s) & e
            if ok.sum() < 9:
                continue
            idx = np.where(ok)[0]
            order = idx[np.argsort(s[idx])]
            sel = order[:m] if side < 0 else order[-m:]
            j = min(i + K, N - 1)
            with np.errstate(invalid="ignore", divide="ignore"):
                step = opens[j] / opens[i] - 1.0
            step = np.where(np.isfinite(step), step, 0.0)
            f = FUND[i:j].sum(axis=0)
            px = side * float(np.mean(step[sel])) / K
            fd = -side * float(np.mean(f[sel])) / K
            px_tot += px
            fd_tot += fd
            for q in range(4):
                if edges[q] <= grid[i] < edges[q + 1]:
                    per_fold[q] += px + fd
    return px_tot, fd_tot, per_fold


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if what == "scan":
        print(f"{'kind':<6} {'F':>3} {'K':>3} {'m':>2} | {'short px':>9} {'short fd':>9} "
              f"{'short tot':>9} | folds")
        for kind in ("resid", "raw"):
            for F in (21, 42, 63, 90):
                for K in (9, 21, 42):
                    sig, _ = make_signal(kind, 270, F, 1)
                    for m in (3, 7):
                        px, fd, pf = sleeve(sig, K, m, -1)
                        print(f"{kind:<6} {F:>3} {K:>3} {m:>2} | {px:>9.3f} {fd:>9.3f} "
                              f"{px + fd:>9.3f} | {np.round(pf, 2)}")
    elif what == "market":
        sig, _ = make_signal("resid", 270, 63, 1)
        for K in (9, 21, 42):
            # sleeve of ALL eligible names = the market basket, long side
            allsig = np.where(np.isfinite(sig), 0.0, np.nan)
            px, fd, pf = sleeve(allsig, K, 20, +1)
            print(f"market basket K={K}: px={px:+.3f} fd={fd:+.3f} tot={px + fd:+.3f} "
                  f"folds={np.round(pf, 2)}")
    elif what == "invert":
        # short the recent residual WINNERS instead (the reversal sign), for the short floor only
        for F in (3, 6, 12, 21):
            for K in (3, 9, 21):
                sig, _ = make_signal("resid", 270, F, 1)
                px, fd, pf = sleeve(sig, K, 7, +1)   # side=+1 picks TOP, we then short them
                print(f"short-winners F={F} K={K}: short tot={-(px) + fd:+.3f}")
