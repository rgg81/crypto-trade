"""EDA 10 -- is a gross-positive short sleeve a mechanism or a handful of collapses?

A floor whose sign flips with the rebalance offset is not passed, it is won. This prints the sign
distribution of the short sleeve across every phase offset, and the single largest per-name
contributions, so the certificate can say which one it is.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import build_funding_matrix  # noqa: E402
from eda_03_portfolio import elig, grid, make_signal, opens, start, symbols  # noqa: E402
from eda_09_asym import run  # noqa: E402

N = len(grid)
FUND = build_funding_matrix(grid, symbols)


def contributions(sig, K, m):
    """Per-name short-sleeve contribution, phase-averaged, unscaled equal-weight sleeve."""
    acc = {}
    for p in range(K):
        for i in range(start + p, N - K, K):
            s, e = sig[i], elig[i]
            ok = np.isfinite(s) & e
            if ok.sum() < 9:
                continue
            idx = np.where(ok)[0]
            order = idx[np.argsort(s[idx])]
            lo = order[:m]
            j = min(i + K, N - 1)
            with np.errstate(invalid="ignore", divide="ignore"):
                step = opens[j] / opens[i] - 1.0
            step = np.where(np.isfinite(step), step, 0.0)
            f = FUND[i:j].sum(axis=0)
            for c in lo:
                acc.setdefault(symbols[c], []).append(
                    ((-step[c] + f[c]) / m / K, grid[i])
                )
    rows = []
    for sym, vals in acc.items():
        tot = sum(v for v, _ in vals)
        worst = min(vals, key=lambda v: v[0])
        rows.append((sym, tot, len(vals), worst[0], worst[1].date()))
    return pd.DataFrame(rows, columns=["symbol", "total", "n", "worst", "when"]).sort_values(
        "total"
    )


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "sign"
    if what == "sign":
        sig, _ = make_signal("resid", 270, 63, 1)
        for K in (21, 30):
            for ml, ms in ((7, 7), (7, 5), (7, 4), (7, 3), (7, 2)):
                rows = run(sig, K, ml, ms)
                sp = np.array([r["short_pnl"] for r in rows])
                lp = np.array([r["long_pnl"] for r in rows])
                print(f"K={K} L{ml}/S{ms}: short>0 at {int((sp > 0).sum())}/{len(sp)} phases  "
                      f"median={np.median(sp):+.4f} mean={sp.mean():+.4f} "
                      f"range=[{sp.min():+.3f},{sp.max():+.3f}]  long median={np.median(lp):+.3f}")
    elif what == "who":
        sig, _ = make_signal("resid", 270, 63, 1)
        for m in (2, 4, 7):
            d = contributions(sig, 21, m)
            print(f"\n--- short sleeve m={m}, per-name contribution (unscaled) ---")
            print(f"total={d.total.sum():+.3f}")
            print(d.head(5).to_string(index=False))
            print(d.tail(5).to_string(index=False))
