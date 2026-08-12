"""Decomposition: is any of the funding IC a PRICE effect, or is it all carry?

The books so far collect funding (positive funding PnL share) and lose on price. If the
whole cross-sectional funding IC is the carry itself, then a funding-dynamics lane has no
price mechanism at all and the honest answer is a negative result. This splits the forward
return into its price and funding halves and re-measures every candidate measure against
each. It also checks whether the perp-minus-mark "basis" proxy is a real premium series or
a one-bar residual with no memory.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import load, spearman_ic  # noqa: E402
from signals import rolling_means, xs_orthogonalise  # noqa: E402
from sweep import fz  # noqa: E402


def fwd_parts(panel, h):
    fwd, fund = panel["fwd"], panel["fund_hold"]
    ok = np.isfinite(fwd)
    n_t = fwd.shape[0]

    def cum(x):
        c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), np.nan_to_num(x, nan=0.0)]), axis=0)
        out = np.full(x.shape, np.nan)
        out[: n_t - h] = c[h:n_t] - c[: n_t - h]
        return out

    okc = np.cumsum(np.vstack([np.zeros((1, fwd.shape[1])), ok.astype(float)]), axis=0)
    full = np.zeros(fwd.shape, dtype=bool)
    full[: n_t - h] = (okc[h:n_t] - okc[: n_t - h]) >= h
    price = np.where(full, cum(fwd), np.nan)
    carry = np.where(full, -cum(fund), np.nan)
    return price, carry


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    lev21 = rm[20]

    print("--- basis proxy diagnostics ---")
    b0, b1, b2 = bas[0], bas[1], bas[2]
    m = np.isfinite(b0) & np.isfinite(b1) & elig
    print(f"corr(basis_t, basis_t-1) = {np.corrcoef(b0[m], b1[m])[0,1]:+.4f}")
    m2 = np.isfinite(b0) & np.isfinite(b2) & elig
    print(f"corr(basis_t, basis_t-2) = {np.corrcoef(b0[m2], b2[m2])[0,1]:+.4f}")
    mf = np.isfinite(b0) & np.isfinite(rate[0]) & elig
    print(f"corr(basis_t, funding_t) = {np.corrcoef(b0[mf], rate[0][mf])[0,1]:+.4f}")
    r0, r1 = rate[0], rate[1]
    mr = np.isfinite(r0) & np.isfinite(r1) & elig
    print(f"corr(funding_t, funding_t-1) = {np.corrcoef(r0[mr], r1[mr])[0,1]:+.4f}")
    print()

    measures = {"LEVEL_21": lev21, "LEVEL_9": rm[8], "LEVEL_45": rm[44]}
    for ks, kl in ((1, 21), (3, 21), (6, 21), (3, 45), (9, 45)):
        s = fz(rm, rate, ks, kl)
        measures[f"fz{ks}_{kl}"] = s
        measures[f"fz{ks}_{kl}o"] = xs_orthogonalise(s, lev21, elig)
    measures["dfund_1"] = rate[0] - rate[1]
    measures["dfund_3"] = rm[2] - (rm[5] * 6 - rm[2] * 3) / 3.0

    rows = []
    for h in (3, 9, 21, 45):
        price, carry = fwd_parts(panel, h)
        for name, sig in measures.items():
            icp, tp, _ = spearman_ic(sig, price, elig, stride=3)
            icc, tc, _ = spearman_ic(sig, carry, elig, stride=3)
            rows.append(
                {"h": h, "measure": name, "ic_price": icp, "t_price": tp,
                 "ic_carry": icc, "t_carry": tc}
            )
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("=== IC vs forward PRICE-only return, and vs forward CARRY (funding received) ===")
    print(df.pivot(index="measure", columns="h",
                   values=["ic_price", "t_price", "ic_carry"]).round(4).to_string())
    df.to_csv("tournament/cup20/teams/team-08/research/ic_decomposed.csv", index=False)


if __name__ == "__main__":
    main()
