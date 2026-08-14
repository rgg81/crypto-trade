"""Design sweep on the CORRECTED bench (``signals.py``), which is information-set equivalent to
the frozen strategy: verified at 206 of 207 rebalance rows agreeing to floating point, the single
exception being a rank tie broken by symbol name rather than array order.

Every economic number in the certificate's design section comes from here. Three stages:
  A  cell x neutralisation x activity window x volatility window, at one fixed phase
  B  the full 21-point weekly phase surface at the chosen design
  C  cadence and holding horizon, with the phase offset swept at every cadence
"""

from __future__ import annotations

import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import fastsim  # noqa: E402
import panel as panel_mod  # noqa: E402
import signals as S  # noqa: E402
from sweep import fold_stats, summarise  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
MONDAY_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")
BASE_PHASE = 4
COLS = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "dd_2x", "turnover", "gross_edge",
        "cost_share", "trades", "F1", "F2", "F3", "F4", "worst", "median_fold", "npos",
        "long_gross", "short_gross"]


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    start_idx = int(np.where(p.times == IS_START)[0][0])
    times = p.times[start_idx:]
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)

    cells = {
        "deskclosed": S.desk_closed_cell(p),
        "weekend": np.isin(p.dow, [5, 6]),
        "asia": p.slot == 0,
    }
    rows = []
    cache: dict = {}

    def run(cellname, aw, vw, neut, power, cadence, phase, quantity, tag):
        key = (cellname, aw, vw, neut, quantity)
        if key not in cache:
            cache[key] = S.build(p, start_idx, activity_window=aw, volatility_window=vw,
                                 cell=cells[cellname], neutralise=neut, quantity=quantity)
        sig, _ = cache[key]
        wts = S.power_book(sig, power)
        reb = ((bar_index - phase) % cadence) == 0
        res = fastsim.full_evaluate(p, start_idx, wts, reb, levels=(1, 2))
        res[3] = res[2]
        extra = {"stage": tag, "cell": cellname, "aw": aw, "vw": vw, "neut": neut,
                 "power": power, "cadence": cadence, "phase": phase, "quantity": quantity,
                 "weekday": (phase // 3) % 7 if cadence == 21 else -1, "slot": phase % 3}
        extra.update(fold_stats(res, times))
        rows.append(summarise(
            res, f"{cellname}|{quantity}|a{aw}|v{vw}|{'N' if neut else 'R'}|p{power}"
                 f"|c{cadence}|ph{phase}", extra))

    for cellname in cells:
        for aw in (126, 189, 252, 315, 378):
            run(cellname, aw, 378, False, 1.0, 21, BASE_PHASE, "trades", "A")
            for vw in (189, 252, 378, 504):
                run(cellname, aw, vw, True, 1.0, 21, BASE_PHASE, "trades", "A")
        print(f"  A {cellname} done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)
    for aw in (189, 252, 315):
        run("deskclosed", aw, 378, True, 1.0, 21, BASE_PHASE, "volume", "A")

    out = pd.DataFrame(rows)
    out.to_csv("tournament/cup20/teams/team-11/research/sweep_v2_stageA.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 400)
    print(f"\n===== STAGE A ({len(out)}) sorted by 1x Sharpe =====")
    print(out.sort_values("sharpe_1x", ascending=False)[COLS].to_string(
        index=False, float_format="%.3f"))
    print("\n===== STAGE A sorted by worst fold =====")
    print(out.sort_values("worst", ascending=False).head(25)[COLS].to_string(
        index=False, float_format="%.3f"))
    print("\n===== STAGE A: neutralised vs raw, medians by cell =====")
    print(out.groupby(["cell", "neut"])[
        ["sharpe_1x", "sharpe_2x", "dd_1x", "worst", "median_fold", "turnover", "gross_edge",
         "long_gross", "short_gross"]].median().to_string(float_format="%.3f"))


if __name__ == "__main__":
    main()
