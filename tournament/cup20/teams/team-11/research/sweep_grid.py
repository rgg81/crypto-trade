"""Confirmation grid for the volatility-neutralised desk-closed book.

Two passes:
  1. window grid at a fixed mechanism-chosen phase, to see whether the choice of activity window
     and volatility window sits on a plateau or on a spike;
  2. the full 21-point weekly phase surface at the chosen windows, which is this lane's own
     experiment rather than a robustness footnote.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import fastsim  # noqa: E402
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402
from eda_neutralise import residualise  # noqa: E402
from sweep import fold_stats, summarise  # noqa: E402
from sweep_focus import desk_closed_mask, power_book  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
MONDAY_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")
BASE_PHASE = 4


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    w = p.times >= IS_START
    start_idx = int(np.where(p.times == IS_START)[0][0])
    el = p.eligible[w]
    times = p.times[w]
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)
    absr = np.abs(M.close_log_return(p.close[w]))
    tc = np.where(el, p.trade_count[w], np.nan)
    cell = desk_closed_mask(p, w)

    rv_cache = {
        v: M.cross_section_rank(np.sqrt(M.causal_rolling_sum(absr**2, v)), el)
        for v in (189, 252, 315, 378, 441, 504)
    }
    share_cache = {
        a: M.cross_section_rank(M.share_of_activity(tc, cell, a), el)
        for a in (126, 189, 252, 315, 378)
    }

    rows = []

    def run(aw, vw, power, cadence, phase, tag):
        sig = residualise(share_cache[aw], [rv_cache[vw]], el)
        wts = power_book(M.cross_section_rank(-sig, el), el, power)
        reb = ((bar_index - phase) % cadence) == 0
        res = fastsim.full_evaluate(p, start_idx, wts, reb, levels=(1, 2))
        res[3] = res[2]
        extra = {"pass": tag, "aw": aw, "vw": vw, "power": power,
                 "cadence": cadence, "phase": phase,
                 "weekday": (phase // 3) % 7 if cadence == 21 else -1, "slot": phase % 3}
        extra.update(fold_stats(res, times))
        rows.append(summarise(res, f"a{aw}|v{vw}|p{power}|c{cadence}|ph{phase}", extra))

    for aw in (126, 189, 252, 315, 378):
        for vw in (189, 252, 315, 378, 441, 504):
            run(aw, vw, 1.0, 21, BASE_PHASE, "windows")
    print(f"window grid done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)

    for power in (0.6, 0.8, 1.0, 1.3, 1.6):
        for phase in range(21):
            run(252, 378, power, 21, phase, "phase")
    print(f"phase surface done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)

    for cadence in (3, 6, 9, 12, 21, 42, 63):
        for phase in range(0, cadence, max(1, cadence // 7)):
            run(252, 378, 1.0, cadence, phase, "cadence")
    print(f"cadence grid done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("tournament/cup20/teams/team-11/research/sweep_grid.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 400)
    cols = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "dd_2x", "turnover",
            "gross_edge", "trades", "F1", "F2", "F3", "F4", "worst", "median_fold", "npos",
            "long_gross", "short_gross"]
    for tag in ("windows", "phase", "cadence"):
        sel = out[out["pass"] == tag]
        print(f"\n===== {tag} ({len(sel)}) =====")
        print(sel[cols].to_string(index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()
