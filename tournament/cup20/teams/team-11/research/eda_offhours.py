"""EDA 8 -- the unified human-schedule cell.

The intraday cell (00:00-08:00 UTC, the thinnest global window) and the weekly cell (Sat/Sun) both
beat a shape-matched scrambled clock. They are the same mechanism seen at two frequencies: the
hours when professional desks are shut. This script tests the union as one cell -- a coin's
DESK-CLOSED SHARE of trading activity -- against each half separately, against the scrambled-clock
null, and out-of-cell.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402
from eda_broad import fast_ic  # noqa: E402
from eda_neutralise import residualise  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
N_PERM = 300


def line(label, ic, half, sel=None):
    sel = np.ones(len(ic), dtype=bool) if sel is None else sel
    v = ic[sel]
    v = v[np.isfinite(v)]
    t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
    a = ic[sel & half]
    a = a[np.isfinite(a)]
    b = ic[sel & ~half]
    b = b[np.isfinite(b)]
    ta = a.mean() / a.std(ddof=1) * np.sqrt(len(a))
    tb = b.mean() / b.std(ddof=1) * np.sqrt(len(b))
    print(f"{label:<50} IC={v.mean():>+.4f} t={t:>+6.2f} | H1 {a.mean():>+.4f} (t={ta:>+5.2f}) "
          f"| H2 {b.mean():>+.4f} (t={tb:>+5.2f})  "
          f"{'STABLE' if np.sign(a.mean()) == np.sign(b.mean()) else 'FLIPS'}")


def main() -> None:
    rng = np.random.default_rng(11202608)
    p = panel_mod.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    slot = p.slot[w]
    dow = p.dow[w]
    n = len(times)
    half = times < times[n // 2]
    qv = np.where(el, p.quote_volume[w], np.nan)
    absr = np.abs(M.close_log_return(p.close[w]))
    tc = np.where(el, p.trade_count[w], np.nan)
    fwd = M.cross_section_rank(np.where(el, p.oo_ret[w], np.nan), el)
    day_id = np.searchsorted(np.unique(times.normalize().to_numpy()),
                             times.normalize().to_numpy())

    weekend = np.isin(dow, [5, 6])
    asia = slot == 0
    desk_closed = weekend | asia
    cells = {
        "asia only (00-08 UTC)": asia,
        "weekend only (Sat/Sun)": weekend,
        "DESK-CLOSED (weekend OR 00-08)": desk_closed,
        "weekday 00-08 only": asia & ~weekend,
    }
    quantities = {"quote volume": qv, "abs return": absr, "trade count": tc}

    print("== raw IC by cell, quantity and window ==")
    best = {}
    for qname, q in quantities.items():
        for cname, cell in cells.items():
            for W in (63, 126, 252, 378):
                s = M.share_of_activity(q, cell, W)
                ic = fast_ic(M.cross_section_rank(s, el), fwd)
                line(f"{qname:<13} {cname:<32} W={W}", ic, half)
                v = ic[np.isfinite(ic)]
                best[(qname, cname, W)] = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
        print()

    # ---- neutralised, for the DESK-CLOSED cell -------------------------------------------
    print("== DESK-CLOSED share, neutralised against the other lanes' factors ==")
    logv = np.log(np.maximum(M.causal_rolling_sum(qv, 126), 1.0))
    rv = np.sqrt(M.causal_rolling_sum(absr**2, 126))
    mom = M.causal_rolling_sum(M.close_log_return(p.close[w]), 63)
    absf = M.causal_rolling_sum(np.abs(np.where(el, p.funding_at_f[w], np.nan)), 126)
    ctrl = [M.cross_section_rank(x, el) for x in (rv, logv, mom, absf)]
    names = ["volatility", "size", "momentum", "crowding"]
    for W in (126, 252, 378):
        base = M.cross_section_rank(M.share_of_activity(qv, desk_closed, W), el)
        line(f"W={W} raw", fast_ic(base, fwd), half)
        for nm, c in zip(names, ctrl, strict=True):
            line(f"W={W}   | {nm}", fast_ic(residualise(base, [c], el), fwd), half)
        line(f"W={W}   | ALL FOUR", fast_ic(residualise(base, ctrl, el), fwd), half)
        print()

    # ---- scrambled-clock null for the DESK-CLOSED cell ------------------------------------
    print("== scrambled-clock null for the DESK-CLOSED cell (cell size held exactly) ==")
    n_days = int(day_id.max()) + 1
    n_weeks = n_days // 7 + 1
    week_id = day_id // 7
    dpos = day_id % 7
    for W in (126, 252):
        true_ic = np.nanmean(fast_ic(
            M.cross_section_rank(M.share_of_activity(qv, desk_closed, W), el), fwd))
        perms = []
        for _ in range(N_PERM):
            perday = np.argsort(rng.random((n_days, 3)), axis=1)
            pslot = perday[day_id, slot]
            pick = np.array([rng.choice(7, size=2, replace=False) for _ in range(n_weeks + 1)])
            pweek = (dpos == pick[week_id, 0]) | (dpos == pick[week_id, 1])
            pseudo = pweek | (pslot == 0)
            perms.append(np.nanmean(fast_ic(
                M.cross_section_rank(M.share_of_activity(qv, pseudo, W), el), fwd)))
        perms = np.array(perms)
        z = (true_ic - perms.mean()) / perms.std(ddof=1)
        print(f"W={W}: true IC {true_ic:+.4f}  null mean {perms.mean():+.4f} sd "
              f"{perms.std(ddof=1):.4f}  z={z:+.2f}  p={float((perms <= true_ic).mean()):.4f}")


if __name__ == "__main__":
    main()
