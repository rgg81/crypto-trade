"""EDA 6 -- the null that has teeth for a CALENDAR claim.

This snapshot cannot supply a non-settlement 8h boundary: every eligible symbol-boundary carries a
settlement (measured at 100.0000%). The identifiable control is therefore not "settlement vs no
settlement" but "the true clock vs a scrambled clock of identical shape":

  * SCRAMBLED-SLOT: the three slot labels are randomly permuted per calendar day, so each pseudo
    cell keeps exactly the same number of bars, the same coins and the same volatility mix, and
    only the alignment with the settlement clock is destroyed.
  * ROTATED-WEEK: day-of-week labels rotated by k days, matched on cell sizes.

An effect that is really about the settlement clock must beat its own scrambled twin. An effect
that is about anything else -- size, volatility, crowding -- will not notice the scramble.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402
from eda_broad import fast_ic  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
N_PERM = 300


def share_with_mask(q, mask, window):
    return M.share_of_activity(q, mask, window)


def main() -> None:
    rng = np.random.default_rng(20260814)
    p = panel_mod.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    slot = p.slot[w]
    dow = p.dow[w]
    n = len(times)
    qv = np.where(el, p.quote_volume[w], np.nan)
    absr = np.abs(M.close_log_return(p.close[w]))
    fwd = M.cross_section_rank(np.where(el, p.oo_ret[w], np.nan), el)
    day_id = np.searchsorted(np.unique(times.normalize().to_numpy()),
                             times.normalize().to_numpy())

    W = 126
    tests = {
        "asia_volume_share": (qv, slot == 0, -1.0),
        "us_minus_asia_volume_share": (qv, None, +1.0),
        "asia_volatility_share": (absr, slot == 0, -1.0),
        "weekend_volatility_share": (absr, np.isin(dow, [5, 6]), -1.0),
    }

    print(f"permutations = {N_PERM}; window = {W} bars; boundaries = {n}")
    print("\nmeasure                       true IC    perm mean    perm sd    z      p(one-sided)")
    for name, (q, mask, sign) in tests.items():
        if name.startswith("us_minus"):
            true = share_with_mask(q, slot == 2, W) - share_with_mask(q, slot == 0, W)
        else:
            true = share_with_mask(q, mask, W)
        ic_true = np.nanmean(fast_ic(M.cross_section_rank(true, el), fwd))
        n_days = int(day_id.max()) + 1
        n_weeks = n_days // 7 + 1
        week_id = day_id // 7
        perms = []
        for _ in range(N_PERM):
            if name.startswith("weekend"):
                # each week independently nominates a random pair of its own days as the pseudo
                # "weekend": identical cell size (2 of 7 days), clock alignment destroyed
                pick = np.array([rng.choice(7, size=2, replace=False) for _ in range(n_weeks + 1)])
                dpos = day_id % 7
                pseudo = (dpos == pick[week_id, 0]) | (dpos == pick[week_id, 1])
                s = share_with_mask(q, pseudo, W)
            else:
                # each DAY independently permutes its own three slot labels: every pseudo cell
                # keeps exactly one bar per day, so cell sizes, coin mix and the volatility mix
                # are all preserved and only the alignment with the settlement clock is destroyed
                perday = np.argsort(rng.random((n_days, 3)), axis=1)
                pslot = perday[day_id, slot]
                if name.startswith("us_minus"):
                    s = share_with_mask(q, pslot == 2, W) - share_with_mask(q, pslot == 0, W)
                else:
                    s = share_with_mask(q, pslot == 0, W)
            perms.append(np.nanmean(fast_ic(M.cross_section_rank(s, el), fwd)))
        perms = np.array(perms)
        z = (ic_true - perms.mean()) / perms.std(ddof=1)
        if sign > 0:
            pval = float((perms >= ic_true).mean())
        else:
            pval = float((perms <= ic_true).mean())
        print(f"{name:<30}{ic_true:>+8.4f}  {perms.mean():>+10.4f} {perms.std(ddof=1):>10.4f} "
              f"{z:>+7.2f}   {pval:>8.4f}")


if __name__ == "__main__":
    main()
