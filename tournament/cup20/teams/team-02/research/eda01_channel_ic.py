"""EDA 01 - does cross-sectional channel position predict forward return on top-20 perps?

Non-overlapping sampling at the horizon so the IC t-stat is not inflated by overlap.
"""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda_panel import channel_position, eligibility_mask, load_panel, summarise_ic, wide  # noqa: E402

bars, membership, funding = load_panel()
op = wide(bars, "open")
hi = wide(bars, "high")
lo = wide(bars, "low")
cl = wide(bars, "close")

index = cl.index
mask = eligibility_mask(membership, index, cl.columns)
# only boundaries where a member also has a tradable bar
mask = mask & op.notna()

start = pd.Timestamp("2020-08-17T00:00:00Z")
print("boundaries", (index >= start).sum(), "first", index.min(), "last", index.max())
print("median eligible names", mask[index >= start].sum(axis=1).median())

rows = []
for n in (21, 42, 63, 126, 189, 252):        # 8h bars: 7, 14, 21, 42, 63, 84 days
    pos = channel_position(hi, lo, cl, n)
    score = pos.sub(pos.mean(axis=1), axis=0)  # cross-sectional demean
    for h in (3, 9, 21, 42, 63):               # forward horizon in 8h bars: 1,3,7,14,21 days
        # execution-faithful: fill at next open, exit at open h bars later
        fwd = op.shift(-(1 + h)) / op.shift(-1) - 1.0
        sub = slice(None)
        for phase in (0,):
            idx = index[(index >= start)]
            idx = idx[phase::h] if h > 1 else idx
            r = summarise_ic(score.loc[idx], fwd.loc[idx], mask.loc[idx], f"pos{n}_h{h}")
            r["n"] = n
            r["h"] = h
            rows.append(r)

out = pd.DataFrame(rows)[["n", "h", "n_obs", "ic_mean", "ic_t", "ic_pos_frac"]]
pd.set_option("display.width", 200)
print(out.to_string(index=False))
