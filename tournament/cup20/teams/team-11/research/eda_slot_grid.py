"""EDA 3 -- the identification that separates HARVEST slot from FORMATION slot.

At lag 1 the two are perfectly confounded: deciding at 00:00 UTC, the most recent bar is always
the 16:00-24:00 (US) bar. Lags 1..9 break the confound, because formation slot = (harvest - lag)
mod 3. The grid below is therefore read three ways:

  * rows constant  -> the effect belongs to the HARVEST slot (when you trade)
  * columns constant -> the effect belongs to the FORMATION slot (whose move it was)
  * diagonal vs off-diagonal -> the effect is SAME-SLOT persistence vs CROSS-SLOT reversal

Also splits the window in half, and reports the per-cell effective sample.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import panel  # noqa: E402
from ic_study import ic_series  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
SLOT = {0: "Asia", 1: "Euro", 2: "US  "}


def main() -> None:
    p = panel.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    ret = np.where(el, p.oo_ret[w], np.nan)
    slot = p.slot[w]
    n = len(times)
    half = times < times[n // 2]

    lag_ic = {}
    for k in range(1, 10):
        sig = np.full_like(ret, np.nan)
        sig[k:] = ret[:-k]
        lag_ic[k] = ic_series(sig, ret, el)

    print("== rank IC of the lag-k bar return vs the next bar, by harvest slot ==")
    print("(t-stats in brackets; n ~ 1444 boundaries per harvest cell)")
    header = "lag  formation-slot |" + "".join(f"{'harvest ' + SLOT[h]:>22}" for h in range(3))
    print(header)
    for k in range(1, 10):
        cells = []
        for h in range(3):
            m = slot == h
            v = lag_ic[k][m]
            v = v[np.isfinite(v)]
            t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
            cells.append(f"{v.mean():>+.4f} [{t:>+5.2f}]")
        fslots = "/".join(SLOT[(h - k) % 3].strip() for h in range(3))
        print(f"{k:>3}  {fslots:<14} |" + "".join(f"{c:>22}" for c in cells))

    print("\n== same aggregation, collapsed ==")
    for k in range(1, 10):
        v = lag_ic[k][np.isfinite(lag_ic[k])]
        t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
        print(f"  lag {k}: IC={v.mean():+.4f} [t={t:+.2f}]  n={len(v)}")

    # ---- SAME-slot vs CROSS-slot at matched lag distance ---------------------------------
    print("\n== matched-lag contrast: is the reversal about the CLOCK or about the DISTANCE? ==")
    print("lag 3/6/9 are same-slot; lag 1,2,4,5,7,8 are cross-slot at comparable distance")
    same = [3, 6, 9]
    cross = [1, 2, 4, 5, 7, 8]
    for label, ks in (("same-slot", same), ("cross-slot", cross)):
        vals = np.concatenate([lag_ic[k][np.isfinite(lag_ic[k])] for k in ks])
        print(f"  {label:<11} mean IC = {vals.mean():+.4f}  n={len(vals)}")

    # ---- half-window stability of the whole grid ------------------------------------------
    print("\n== both-halves stability of each (lag, harvest slot) cell ==")
    print("lag  slot   IC_all      IC_H1       IC_H2      same sign?")
    for k in (1, 2, 3, 6):
        for h in range(3):
            m = slot == h
            a = lag_ic[k][m & half]
            b = lag_ic[k][m & ~half]
            a, b = a[np.isfinite(a)], b[np.isfinite(b)]
            allv = lag_ic[k][m]
            allv = allv[np.isfinite(allv)]
            print(
                f"{k:>3}  {SLOT[h]}  {allv.mean():>+.4f}   {a.mean():>+.4f}    {b.mean():>+.4f}"
                f"     {'YES' if np.sign(a.mean()) == np.sign(b.mean()) else 'no'}"
            )


if __name__ == "__main__":
    main()
