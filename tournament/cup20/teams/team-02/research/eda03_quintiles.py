"""EDA 03 - quintile structure of channel position: absolute and relative forward returns.

Answers two questions the floors force:
  1. Is the bottom-of-channel quintile ABSOLUTELY negative (a short sleeve must be gross-positive)?
  2. How much funding carry does each quintile deliver to a short?
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda_panel import channel_position, eligibility_mask, load_panel, wide  # noqa: E402
from eda_sim import funding_matrix  # noqa: E402

bars, membership, funding = load_panel()
op, hi, lo, cl = (wide(bars, c) for c in ("open", "high", "low", "close"))
index, cols = cl.index, cl.columns
mask = eligibility_mask(membership, index, cols) & op.notna()
fund = funding_matrix(funding, index, cols)
START = pd.Timestamp("2020-08-17T00:00:00Z")

sel = index >= START
print("mean 8h funding of eligible names: %.6f  (annualised %.3f)" % (
    fund.where(mask)[sel].stack().mean(), fund.where(mask)[sel].stack().mean() * 1095))
for a, b in [("2020-08-17", "2021-08-01"), ("2021-08-01", "2022-08-01"),
             ("2022-08-01", "2023-08-01"), ("2023-08-01", None)]:
    m = index >= pd.Timestamp(a, tz="UTC")
    if b is not None:
        m = m & (index < pd.Timestamp(b, tz="UTC"))
    print("  %s..%s  mean funding ann = %.4f" % (a, b, fund.where(mask)[m].stack().mean() * 1095))

H = 9  # 3-day forward window used for the quintile table
for n in (63, 126, 252, 378):
    pos = channel_position(hi, lo, cl, n).where(mask)
    fwd = op.shift(-(1 + H)) / op.shift(-1) - 1.0          # price return over the holding window
    fnd_fwd = fund.shift(-1).rolling(H).sum().shift(-(H - 1))  # funding paid by a long
    ranks = pos.rank(axis=1, pct=True)
    idx = index[sel][::H]
    rows = []
    for q in range(5):
        sub = (ranks > q / 5) & (ranks <= (q + 1) / 5)
        sub = sub.loc[idx]
        pr = fwd.loc[idx].where(sub).stack()
        fd = fnd_fwd.loc[idx].where(sub).stack()
        rows.append({
            "q": q + 1,
            "n_obs": len(pr),
            "price_ret_ann": pr.mean() * (1095 / H),
            "funding_ann": fd.mean() * (1095 / H),
            "long_total_ann": (pr - fd).mean() * (1095 / H),
            "hit": (pr > 0).mean(),
        })
    t = pd.DataFrame(rows)
    mkt = fwd.loc[idx].where(mask.loc[idx]).stack().mean() * (1095 / H)
    print(f"\nformation n={n} bars ({n/3:.0f}d), holding {H} bars ({H/3:.0f}d). "
          f"equal-weight universe price return ann = {mkt:.3f}")
    print(t.to_string(index=False, float_format=lambda v: f"{v: .4f}"))
