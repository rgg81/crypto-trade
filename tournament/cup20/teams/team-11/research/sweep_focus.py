"""Focused offline sweep on the DESK-CLOSED design: cadence, phase, weighting and window.

The rebalance phase is a first-order axis for this lane rather than a robustness detail: at a
weekly cadence (21 bars) the phase names the (weekday, settlement slot) at which the book is
reset, so the full phase surface is the lane's own experiment and is swept exhaustively here.
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import book as B  # noqa: E402
import fastsim  # noqa: E402
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402
from sweep import fold_stats, summarise  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
MONDAY_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")


def desk_closed_mask(p, w):
    return np.isin(p.dow[w], [5, 6]) | (p.slot[w] == 0)


def power_book(sig_rank, eligible, power):
    out = np.zeros_like(sig_rank)
    for i in range(sig_rank.shape[0]):
        m = np.isfinite(sig_rank[i])
        if m.sum() < 8:
            continue
        v = sig_rank[i, m]
        wgt = np.sign(v) * np.abs(v) ** power
        wgt = wgt - wgt.mean()
        g = np.abs(wgt).sum()
        if g > 0:
            out[i, m] = wgt / g
    return out


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    w = p.times >= IS_START
    start_idx = int(np.where(p.times == IS_START)[0][0])
    el = p.eligible[w]
    times = p.times[w]
    n = len(times)
    # bar index measured from a Monday 00:00 UTC epoch, so a phase at cadence 21 names
    # (weekday, settlement slot) directly
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)

    quantities = {
        "trades": np.where(el, p.trade_count[w], np.nan),
        "volume": np.where(el, p.quote_volume[w], np.nan),
    }
    cell = desk_closed_mask(p, w)
    rows = []
    for qname, q in quantities.items():
        for W in (252, 378):
            share = M.share_of_activity(q, cell, W)
            sig = M.cross_section_rank(-share, el)
            dshare = share - np.vstack([np.full((126, share.shape[1]), np.nan), share[:-126]])
            dsig = M.cross_section_rank(-dshare, el)
            for signal_name, s in (("level", sig), ("change126", dsig)):
                for power in (0.5, 1.0, 2.0):
                    wts = power_book(s, el, power)
                    for cadence in (1, 3, 9, 21, 42):
                        phases = range(cadence) if cadence <= 21 else range(0, cadence, 3)
                        for phase in phases:
                            reb = ((bar_index - phase) % cadence) == 0
                            res = fastsim.full_evaluate(p, start_idx, wts, reb, levels=(1, 2))
                            res[3] = res[2]
                            extra = {
                                "quantity": qname, "W": W, "signal": signal_name,
                                "power": power, "cadence": cadence, "phase": phase,
                                "weekday": (phase // 3) % 7 if cadence == 21 else -1,
                                "slot": phase % 3,
                            }
                            extra.update(fold_stats(res, times))
                            rows.append(summarise(
                                res,
                                f"{qname}|W{W}|{signal_name}|p{power}|c{cadence}|ph{phase}",
                                extra,
                            ))
            print(f"  {qname} W={W} done ({time.time() - t0:.0f}s, {len(rows)} configs)",
                  flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("tournament/cup20/teams/team-11/research/sweep_focus.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 300)
    cols = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "turnover", "gross_edge",
            "cost_share", "trades", "worst", "median_fold", "npos", "long_gross", "short_gross"]
    print(f"\n{len(out)} configs in {time.time() - t0:.0f}s")
    print("\n=== top 30 by 2x Sharpe ===")
    print(out.sort_values("sharpe_2x", ascending=False).head(30)[cols].to_string(
        index=False, float_format="%.3f"))
    print("\n=== weekly cadence: the full phase surface (level signal) ===")
    sel = out[(out.cadence == 21) & (out.signal == "level")]
    for (qn, W, pw), g in sel.groupby(["quantity", "W", "power"]):
        print(f"\n{qn} W={W} power={pw}")
        g2 = g.sort_values("phase")
        print("  phase(wd,slot): " + " ".join(
            f"{int(r.phase):>2}({int(r.weekday)},{int(r.slot)}):{r.sharpe_2x:>+5.2f}"
            for r in g2.itertuples()))


if __name__ == "__main__":
    main()
