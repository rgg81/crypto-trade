"""EDA 7 -- out-of-cell prediction.

The strongest defence a seasonality lane has: estimate the pattern on one part of the calendar and
test it on a part that was not used to estimate it. Two disjoint splits are run.

  SPLIT-A (measurement cell vs prediction cell): the session-activity share is measured using bars
  from Monday-Wednesday only, and its cross-sectional IC is then evaluated at Thursday-Sunday
  boundaries only -- and vice versa. No bar contributes to both sides.

  SPLIT-B (calendar-half): the share is measured on even ISO weeks and evaluated on odd ISO weeks,
  and vice versa.

A characteristic that says "who owns this coin" transfers across cells. A cell-specific artifact
does not.
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


def report(label, ic, sel, half):
    v = ic[sel]
    v = v[np.isfinite(v)]
    if len(v) < 40:
        print(f"{label:<58} n<40")
        return
    t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
    a = ic[sel & half]
    a = a[np.isfinite(a)]
    b = ic[sel & ~half]
    b = b[np.isfinite(b)]
    print(f"{label:<58} IC={v.mean():>+.4f} t={t:>+6.2f} n={len(v):>5}  "
          f"H1={a.mean():>+.4f} H2={b.mean():>+.4f}")


def main() -> None:
    p = panel_mod.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    slot = p.slot[w]
    dow = p.dow[w]
    n = len(times)
    half = times < times[n // 2]
    qv = np.where(el, p.quote_volume[w], np.nan)
    fwd = M.cross_section_rank(np.where(el, p.oo_ret[w], np.nan), el)
    W = 252
    iso_week = times.isocalendar().week.to_numpy()

    def share(mask_rows, cellmask):
        """Activity share of the clock cell, computed only from rows where mask_rows is True.

        Numerator and denominator are BOTH restricted to ``mask_rows``, so the measurement cell and
        the prediction cell share no bar at all.
        """
        part = M.causal_masked_sum(qv, mask_rows & cellmask, W)
        total = M.causal_masked_sum(qv, mask_rows, W)
        with np.errstate(divide="ignore", invalid="ignore"):
            return part / np.where(np.abs(total) > 1e-12, total, np.nan)

    early = np.isin(dow, [0, 1, 2])
    late = np.isin(dow, [3, 4, 5, 6])
    even_week = (iso_week % 2) == 0

    print("== SPLIT-A: measure on Mon-Wed bars, predict at Thu-Sun boundaries (and reverse) ==")
    for cellname, cellmask, sign in (("asia share", slot == 0, -1),
                                     ("US minus Asia", None, +1)):
        for measure_rows, predict_sel, lab in ((early, late, "measured Mon-Wed -> tested Thu-Sun"),
                                               (late, early, "measured Thu-Sun -> tested Mon-Wed")):
            if cellname == "asia share":
                s = share(measure_rows, cellmask)
            else:
                s = share(measure_rows, slot == 2) - share(measure_rows, slot == 0)
            ic = fast_ic(M.cross_section_rank(s, el), fwd)
            report(f"{cellname:<16} {lab}", ic, predict_sel, half)
        # in-cell reference
        if cellname == "asia share":
            s = share(np.ones(n, dtype=bool), cellmask)
        else:
            s = share(np.ones(n, dtype=bool), slot == 2) - share(
                np.ones(n, dtype=bool), slot == 0
            )
        report(f"{cellname:<16} [all bars, all boundaries -- reference]",
               fast_ic(M.cross_section_rank(s, el), fwd), np.ones(n, dtype=bool), half)
        print()

    print("== SPLIT-B: measure on even ISO weeks, predict on odd ISO weeks (and reverse) ==")
    for cellname in ("asia share", "US minus Asia"):
        for rows, sel, lab in ((even_week, ~even_week, "measured even weeks -> tested odd weeks"),
                               (~even_week, even_week, "measured odd weeks -> tested even weeks")):
            if cellname == "asia share":
                s = share(rows, slot == 0)
            else:
                s = share(rows, slot == 2) - share(rows, slot == 0)
            ic = fast_ic(M.cross_section_rank(s, el), fwd)
            report(f"{cellname:<16} {lab}", ic, sel, half)
        print()

    print("== SPLIT-C: measure on the FIRST half of the window, sign frozen, tested on the "
          "SECOND half ==")
    for cellname in ("asia share", "US minus Asia"):
        if cellname == "asia share":
            s = share(np.ones(n, dtype=bool), slot == 0)
        else:
            s = share(np.ones(n, dtype=bool), slot == 2) - share(np.ones(n, dtype=bool), slot == 0)
        ic = fast_ic(M.cross_section_rank(s, el), fwd)
        a = ic[half]
        a = a[np.isfinite(a)]
        b = ic[~half]
        b = b[np.isfinite(b)]
        ta = a.mean() / a.std(ddof=1) * np.sqrt(len(a))
        tb = b.mean() / b.std(ddof=1) * np.sqrt(len(b))
        print(f"{cellname:<16} H1 IC={a.mean():+.4f} (t={ta:+.2f}, n={len(a)})   "
              f"H2 IC={b.mean():+.4f} (t={tb:+.2f}, n={len(b)})   "
              f"{'SIGN HOLDS' if np.sign(a.mean()) == np.sign(b.mean()) else 'SIGN FLIPS'}")


if __name__ == "__main__":
    main()
