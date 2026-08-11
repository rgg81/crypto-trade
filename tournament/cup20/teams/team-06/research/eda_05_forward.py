"""Team 06 EDA 5 -- is the selection forward-looking, or is it picking up persistence in the
measure rather than anything about future drawdown?

Downside-risk characteristics are strongly autocorrelated, so a book that ranks on trailing
semivariance could be paid for a LABEL rather than for a RISK. Three measurements separate those:

  (a) persistence  -- rank autocorrelation of the composite at the holding horizon;
  (b) forecast     -- does the TRAILING composite predict the FORWARD-realised composite?
  (c) the oracle   -- does the FORWARD-realised composite (not tradeable, deliberately) carry the
                      same-signed cross-sectional return relation? If it does, the trailing score is
                      a noisy proxy for a real forward characteristic and the selection is
                      forward-looking. If the forward-realised characteristic carries NOTHING while
                      the trailing one does, the label is decoration and the book is trading
                      something else under a downside-risk name.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-06/research")
from signals import characteristics, load_panel, score_row, zscore  # noqa: E402

P = load_panel()
opens, closes, member = P["opens"], P["closes"], P["member"]
N, H = 252, 21
START = pd.Timestamp("2020-08-17", tz="UTC")

F = characteristics(closes, member, N, 0)
# The same characteristics measured on the window that STARTS at the decision -- an oracle. Shifting
# by -(H) rather than +1 makes each row the realised character of the NEXT H bars.
FWD = {k: v.shift(-(1) - N + 1) for k, v in characteristics(closes, member, N, 0).items()}
FWD_SHORT = {k: v.shift(-(1) - H + 1) for k, v in characteristics(closes, member, H, 0).items()}

fwd_ret = opens.shift(-H) / opens - 1.0
grid = opens.index
sample = grid[grid >= START][::H]

rows = []
for t in sample:
    elig = member.loc[t]
    names = [c for c in opens.columns if elig[c]]
    if len(names) < 12:
        continue
    s_now = score_row(F, t, names, "mandate")
    if len(s_now) < 12:
        continue
    common = list(s_now.index)
    rec = {"t": t}
    # (a) persistence: score now vs score one holding period ahead
    j = grid.get_loc(t) + H
    if j < len(grid):
        s_next = score_row(F, grid[j], common, "mandate")
        both = s_now.index.intersection(s_next.index)
        if len(both) >= 10:
            rec["persist"] = s_now[both].rank().corr(s_next[both].rank())
    # (b) forecast: trailing composite vs forward-realised H-bar downside character
    fwd_block = pd.DataFrame({k: FWD_SHORT[k].loc[t, common] for k in
                              ("cvar", "semidev", "maxdd", "underwater")}).dropna()
    if len(fwd_block) >= 10:
        fwd_score = sum(zscore(fwd_block[c]) for c in fwd_block.columns)
        b = s_now.index.intersection(fwd_score.index)
        rec["forecast"] = s_now[b].rank().corr(fwd_score[b].rank())
        r = fwd_ret.loc[t, b].dropna()
        bb = b.intersection(r.index)
        if len(bb) >= 10:
            # (c) the oracle: forward-realised downside character vs the same forward return
            rec["oracle_IC"] = fwd_score[bb].rank().corr(r[bb].rank())
            rec["trailing_IC"] = s_now[bb].rank().corr(r[bb].rank())
            # and the trailing score's IC after removing the oracle -- what is left over
            x = fwd_score[bb].rank(pct=True)
            y = s_now[bb].rank(pct=True)
            resid = y - float(np.polyfit(x, y, 1)[0]) * x
            rec["trailing_resid_IC"] = resid.rank().corr(r[bb].rank())
    rows.append(rec)

D = pd.DataFrame(rows).set_index("t")
print(f"n = {len(D)} non-overlapping weekly cross-sections, formation {N} bars, horizon {H} bars\n")
print(
    pd.DataFrame(
        {
            "mean": D.mean(),
            "t_stat": D.mean() / D.std() * np.sqrt(D.notna().sum()),
            "n": D.notna().sum(),
        }
    ).round(4).to_string()
)
print("\nby fold:")
for name, lo, hi in [
    ("F1", "2020-08-17", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
]:
    m = (D.index >= pd.Timestamp(lo, tz="UTC")) & (D.index < pd.Timestamp(hi, tz="UTC"))
    print(f"  {name}: " + D[m].mean().round(4).to_dict().__str__())
