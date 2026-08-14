"""Final offline check of the nominee and of every candidate neighbourhood point.

Prints the full weekly phase surface at the nominee's own windows (so the nominee can be seen to
sit inside the surface rather than on top of it) and the metric vector of each declared point, so
the sweep trial is spent on a declaration already known to be valid and non-degenerate.
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
COLS = ["config", "sharpe_1x", "sharpe_2x", "sharpe_3x", "ret_1x", "vol_1x", "dd_1x", "dd_2x",
        "turnover", "gross_edge", "cost_share", "trades", "F1", "F2", "F3", "F4", "worst",
        "median_fold", "npos", "long_gross", "short_gross", "top5"]

NOMINEE = {"aw": 252, "vw": 252, "phase": 4, "power": 1.0, "cadence": 21}
POINTS = [
    {"aw": 189, "vw": 252, "phase": 4, "power": 1.0, "cadence": 21},
    {"aw": 315, "vw": 252, "phase": 4, "power": 1.0, "cadence": 21},
    {"aw": 252, "vw": 189, "phase": 4, "power": 1.0, "cadence": 21},
    {"aw": 252, "vw": 315, "phase": 4, "power": 1.0, "cadence": 21},
    {"aw": 252, "vw": 252, "phase": 2, "power": 1.0, "cadence": 21},
    {"aw": 252, "vw": 252, "phase": 7, "power": 1.0, "cadence": 21},
    {"aw": 252, "vw": 252, "phase": 4, "power": 0.7, "cadence": 21},
    {"aw": 252, "vw": 252, "phase": 4, "power": 1.4, "cadence": 21},
    {"aw": 189, "vw": 189, "phase": 2, "power": 0.7, "cadence": 21},
    {"aw": 315, "vw": 315, "phase": 7, "power": 1.4, "cadence": 21},
]


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    start_idx = int(np.where(p.times == IS_START)[0][0])
    times = p.times[start_idx:]
    bar_index = ((times - MONDAY_EPOCH) // pd.Timedelta(hours=8)).to_numpy().astype(np.int64)
    cell = S.desk_closed_cell(p)
    cache: dict = {}
    rows = []

    def run(cfg, tag):
        key = (cfg["aw"], cfg["vw"])
        if key not in cache:
            cache[key] = S.build(p, start_idx, activity_window=cfg["aw"],
                                 volatility_window=cfg["vw"], cell=cell,
                                 neutralise=True, quantity="volume")
        sig, _ = cache[key]
        wts = S.power_book(sig, cfg["power"])
        reb = ((bar_index - cfg["phase"]) % cfg["cadence"]) == 0
        res = fastsim.full_evaluate(p, start_idx, wts, reb)
        extra = {"tag": tag, **cfg}
        extra.update(fold_stats(res, times))
        rows.append(summarise(
            res, f"a{cfg['aw']}|v{cfg['vw']}|ph{cfg['phase']}|p{cfg['power']}", extra))

    pd.set_option("display.width", 300)
    pd.set_option("display.max_rows", 200)

    for phase in range(21):
        run({**NOMINEE, "phase": phase}, "surface")
    surf = pd.DataFrame(rows)
    surf.to_csv("tournament/cup20/teams/team-11/research/nominee_phase_surface.csv", index=False)
    print("===== weekly phase surface at the nominee's own windows (a252/v252) =====")
    g = surf.sort_values("phase")
    print("  phase(wd,slot) 1x Sharpe: " + " ".join(
        f"{int(r.phase):>2}:{r.sharpe_1x:>+5.2f}" for r in g.itertuples()))
    print("  phase          worst fold: " + " ".join(
        f"{int(r.phase):>2}:{r.worst:>+5.2f}" for r in g.itertuples()))
    arr = g.sharpe_1x.to_numpy()
    wk = np.array([(ph // 3) % 7 for ph in g.phase])
    print(f"  Sharpe mean {arr.mean():+.3f} sd {arr.std(ddof=1):.3f} min {arr.min():+.3f} "
          f"max {arr.max():+.3f}  positive at {(arr > 0).sum()}/21")
    print(f"  weekday phases mean Sharpe {arr[wk < 5].mean():+.3f}  worst "
          f"{g.worst.to_numpy()[wk < 5].mean():+.3f}")
    print(f"  weekend phases mean Sharpe {arr[wk >= 5].mean():+.3f}  worst "
          f"{g.worst.to_numpy()[wk >= 5].mean():+.3f}")
    nom_rank = int((arr > arr[g.phase.to_numpy() == NOMINEE['phase']][0]).sum())
    print(f"  the nominee's phase ({NOMINEE['phase']}) is beaten by {nom_rank} of the other 20 "
          "phases on 1x Sharpe")

    rows.clear()
    run(NOMINEE, "nominee")
    for pt in POINTS:
        run(pt, "point")
    nb = pd.DataFrame(rows)
    nb.to_csv("tournament/cup20/teams/team-11/research/nominee_neighbourhood.csv", index=False)
    print("\n===== nominee and declared neighbourhood points =====")
    print(nb[["tag"] + COLS].to_string(index=False, float_format="%.4f"))
    print("\n===== PER-METRIC MEDIAN over all points including the nominee (the score) =====")
    med = nb[["sharpe_1x", "sharpe_2x", "sharpe_3x", "ret_1x", "vol_1x", "dd_1x", "dd_2x",
              "turnover", "gross_edge", "cost_share", "trades", "worst", "median_fold",
              "long_gross", "short_gross", "top5"]].median()
    print(med.to_string(float_format="%.4f"))
    dup = nb.duplicated(subset=["sharpe_1x", "dd_1x", "turnover", "trades"], keep=False)
    print(f"\npoints sharing an identical metric vector (A1 inertness risk): {int(dup.sum())}")
    print(f"wall clock {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
