"""Targeted sweep: does removing the measure's volatility loading fix the fold profile?

The raw desk-closed share is cross-sectionally correlated with realised volatility (a coin traded
mostly when desks are shut is a coin retail leverage prices). Shorting it therefore embeds a short
high-beta tilt that is not part of the lane's claim and that is run over by a retail mania -- which
is precisely what F1 (2020-08 to 2021-08) is.

Neutralising the measure against realised volatility is both the lane-purity fix (the edge must be
the clock's, not team 06's) and a risk control. This sweep measures what it costs and what it buys,
across the full weekly phase surface.
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


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    w = p.times >= IS_START
    start_idx = int(np.where(p.times == IS_START)[0][0])
    el = p.eligible[w]
    times = p.times[w]
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)
    clr = M.close_log_return(p.close[w])
    absr = np.abs(clr)
    qv = np.where(el, p.quote_volume[w], np.nan)
    tc = np.where(el, p.trade_count[w], np.nan)
    cell = desk_closed_mask(p, w)

    rv126 = M.cross_section_rank(np.sqrt(M.causal_rolling_sum(absr**2, 126)), el)
    rv378 = M.cross_section_rank(np.sqrt(M.causal_rolling_sum(absr**2, 378)), el)
    size = M.cross_section_rank(np.log(np.maximum(M.causal_rolling_sum(qv, 126), 1.0)), el)

    rows = []
    for qname, q in (("trades", tc),):
        for W in (252, 378):
            share = M.share_of_activity(q, cell, W)
            base = M.cross_section_rank(share, el)
            variants = {
                "raw": base,
                "neut_rv126": residualise(base, [rv126], el),
                "neut_rv378": residualise(base, [rv378], el),
                "neut_rv_size": residualise(base, [rv126, size], el),
            }
            for vname, sig in variants.items():
                s = M.cross_section_rank(-sig, el)
                for power in (1.0,):
                    wts = power_book(s, el, power)
                    for cadence in (21,):
                        for phase in range(cadence):
                            reb = ((bar_index - phase) % cadence) == 0
                            res = fastsim.full_evaluate(p, start_idx, wts, reb, levels=(1, 2))
                            res[3] = res[2]
                            extra = {"quantity": qname, "W": W, "variant": vname,
                                     "power": power, "cadence": cadence, "phase": phase,
                                     "weekday": (phase // 3) % 7 if cadence == 21 else -1,
                                     "slot": phase % 3}
                            extra.update(fold_stats(res, times))
                            rows.append(summarise(
                                res, f"{qname}|W{W}|{vname}|p{power}|c{cadence}|ph{phase}", extra))
            print(f"  {qname} W={W} done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("tournament/cup20/teams/team-11/research/sweep_neutral.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 400)
    cols = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "turnover", "gross_edge",
            "trades", "F1", "F2", "F3", "F4", "worst", "median_fold", "npos",
            "long_gross", "short_gross"]
    print(f"\n{len(out)} configs in {time.time() - t0:.0f}s")
    print("\n=== top 35 by worst-fold 2x Sharpe (the 30-point term in G) ===")
    print(out.sort_values("worst", ascending=False).head(35)[cols].to_string(
        index=False, float_format="%.3f"))
    print("\n=== top 25 by 1x Sharpe ===")
    print(out.sort_values("sharpe_1x", ascending=False).head(25)[cols].to_string(
        index=False, float_format="%.3f"))
    print("\n=== variant medians ===")
    print(out.groupby(["variant", "quantity", "W"])[
        ["sharpe_1x", "sharpe_2x", "worst", "median_fold", "turnover", "gross_edge",
         "short_gross"]].median().to_string(float_format="%.3f"))


if __name__ == "__main__":
    main()
