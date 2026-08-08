"""EDA 02 - baseline cross-sectional channel-position book: (formation, cadence) screen."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda_panel import channel_position, eligibility_mask, load_panel, wide  # noqa: E402
from eda_sim import funding_matrix, simulate, stats, yearly_sharpe  # noqa: E402

bars, membership, funding = load_panel()
op, hi, lo, cl = (wide(bars, c) for c in ("open", "high", "low", "close"))
index, cols = cl.index, cl.columns
mask = eligibility_mask(membership, index, cols) & op.notna()
fund = funding_matrix(funding, index, cols)
START = pd.Timestamp("2020-08-17T00:00:00Z")


def book_from_score(score: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    s = score.where(mask)
    s = s.sub(s.mean(axis=1), axis=0)
    g = s.abs().sum(axis=1)
    return s.div(g.where(g > 0), axis=0).fillna(0.0)


rows = []
for n in (63, 126, 189, 252, 378):
    pos = channel_position(hi, lo, cl, n)
    w = book_from_score(pos, mask)
    for c in (3, 9, 21, 42):
        reb = pd.Series((np.arange(len(index)) % c) == 0, index=index)
        res = simulate(w, op, fund, reb, START)
        st = stats(res)
        fs = yearly_sharpe(res)
        rows.append({"n": n, "cad": c, **{k: round(v, 3) for k, v in st.items()},
                     **{k: round(v, 2) for k, v in fs.items()}})

out = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(out.to_string(index=False))
