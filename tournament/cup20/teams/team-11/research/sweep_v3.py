"""Corrected-bench sweep, stages A2 / B / C.

A2  the activity quantity (quote volume vs trade count) across the window grid, all three cells
B   the full 21-point weekly phase surface at the chosen design -- this lane's own experiment
C   cadence and holding horizon, with the phase offset swept at every cadence (playbook section 7)
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
        "trades", "F1", "F2", "F3", "F4", "worst", "median_fold", "npos",
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

    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 500)

    for cellname in cells:
        for aw in (126, 189, 252, 315, 378):
            run(cellname, aw, 378, False, 1.0, 21, BASE_PHASE, "volume", "A2")
            for vw in (189, 252, 378, 504):
                run(cellname, aw, vw, True, 1.0, 21, BASE_PHASE, "volume", "A2")
        print(f"  A2 {cellname} done ({time.time() - t0:.0f}s, {len(rows)})", flush=True)
    a2 = pd.DataFrame(rows)
    a2.to_csv("tournament/cup20/teams/team-11/research/sweep_v3_A2.csv", index=False)
    print(f"\n===== STAGE A2 quote volume ({len(a2)}) by 1x Sharpe =====")
    print(a2.sort_values("sharpe_1x", ascending=False)[COLS].to_string(
        index=False, float_format="%.3f"))

    base = ("deskclosed", 252, 378, True, "volume")
    rows_b = len(rows)
    for power in (0.6, 1.0, 1.5):
        for phase in range(21):
            run(base[0], base[1], base[2], base[3], power, 21, phase, base[4], "B")
    print(f"  B done ({time.time() - t0:.0f}s)", flush=True)
    b = pd.DataFrame(rows[rows_b:])
    b.to_csv("tournament/cup20/teams/team-11/research/sweep_v3_B.csv", index=False)
    print("\n===== STAGE B: full weekly phase surface, deskclosed/volume/a252/v378/N =====")
    for pw, g in b.groupby("power"):
        g = g.sort_values("phase")
        print(f"\npower={pw}")
        print("  1x Sharpe : " + " ".join(
            f"{int(r.phase):>2}:{r.sharpe_1x:>+5.2f}" for r in g.itertuples()))
        print("  worst fold: " + " ".join(
            f"{int(r.phase):>2}:{r.worst:>+5.2f}" for r in g.itertuples()))
        arr = g.sharpe_1x.to_numpy()
        wa = g.worst.to_numpy()
        print(f"  Sharpe mean {arr.mean():+.3f} sd {arr.std(ddof=1):.3f} "
              f"min {arr.min():+.3f} max {arr.max():+.3f} | positive at "
              f"{(arr > 0).sum()}/21 phases")
        wk = np.array([(ph // 3) % 7 for ph in g.phase])
        print(f"  weekday phases (Mon-Fri) mean Sharpe {arr[wk < 5].mean():+.3f} "
              f"worst {wa[wk < 5].mean():+.3f} | weekend phases mean Sharpe "
              f"{arr[wk >= 5].mean():+.3f} worst {wa[wk >= 5].mean():+.3f}")

    rows_c = len(rows)
    for cadence in (3, 6, 9, 12, 21, 42, 63):
        for phase in range(cadence) if cadence <= 12 else range(0, cadence, max(1, cadence // 7)):
            run(base[0], base[1], base[2], base[3], 1.0, cadence, phase, base[4], "C")
    print(f"  C done ({time.time() - t0:.0f}s)", flush=True)
    c = pd.DataFrame(rows[rows_c:])
    c.to_csv("tournament/cup20/teams/team-11/research/sweep_v3_C.csv", index=False)
    print("\n===== STAGE C: cadence x phase =====")
    print(c.groupby("cadence")[
        ["sharpe_1x", "sharpe_2x", "dd_1x", "turnover", "gross_edge", "trades", "worst",
         "median_fold"]].agg(["median", "min", "max"]).to_string(float_format="%.3f"))
    print()
    print(c[COLS].to_string(index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()
