"""EDA 15 - re-run the intended neighbourhood at the sim phases that correspond to the frozen
strategy's PHASE_OFFSET convention, and locate the drawdown.

The research sim stamps a decision on the bar it last saw and fills one bar later; the organiser
stamps it at the fill boundary. Organiser PHASE_OFFSET p therefore equals sim phase (p-1) mod
cadence. EDA 13 compared the wrong column of the phase surface; this is the corrected one.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cl, fund, hi, index, lo, op  # noqa: E402
from eda08_controls import sleeve_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402
from eda_sim2 import bootstrap_B, report, run  # noqa: E402

START = pd.Timestamp("2020-08-17T00:00:00Z")
BAR_INDEX = pd.Index((index.asi8 // (8 * 3600 * 10**9)).astype(np.int64))
K = 3


def sim_rebalance(cad: int, organiser_phase: int) -> pd.Series:
    return pd.Series((BAR_INDEX % cad) == ((organiser_phase - 1) % cad), index=index)


def point(N: int, cad: int, phase: int, k: int = K) -> dict:
    w = sleeve_weights(channel_position(hi, lo, cl, N), 1 - channel_position(hi, lo, cl, N), k)
    reb = sim_rebalance(cad, phase)
    r1 = run(w, op, fund, reb, START)
    rep = report(r1)
    rep["B"] = bootstrap_B(r1["net"])
    rep["sh2x"] = report(run(w, op, fund, reb, START, cost_mult=2.0))["sharpe"]
    eq = r1["equity"]
    dd = 1 - eq / eq.cummax()
    rep["dd_date"] = str(dd.idxmax().date())
    rep["dd_pre90"] = float(dd[dd.index < START + pd.Timedelta(days=120)].max())
    return rep


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "declared"
    if mode == "declared":
        pts = [(252, 21, 12), (210, 21, 12), (294, 21, 12), (252, 15, 12),
               (252, 27, 12), (252, 21, 5), (252, 21, 19)]
    elif mode == "wide":
        pts = [(252, 21, 12), (189, 21, 12), (315, 21, 12), (252, 15, 12), (252, 27, 12),
               (252, 21, 3), (252, 21, 17), (231, 21, 12), (273, 21, 12), (252, 18, 12),
               (252, 24, 12), (252, 21, 8), (252, 21, 15)]
    elif mode == "sleeve":
        pts = [(252, 21, 12)]
    rows = []
    for N, cad, ph in pts:
        for k in ((3, 4, 5) if mode == "sleeve" else (K,)):
            rep = point(N, cad, ph, k)
            rep["point"] = f"N={N},cad={cad},ph={ph},k={k}"
            rows.append(rep)
            print(f"{rep['point']:26s} Sh={rep['sharpe']:5.2f} 2x={rep['sh2x']:5.2f} "
                  f"ret={rep['ann_ret']:+.3f} vol={rep['vol']:.3f} dd={rep['maxdd']:.3f} "
                  f"(peak {rep['dd_date']}, first120d {rep['dd_pre90']:.3f}) "
                  f"to={rep['turnover']:5.1f} tr={rep['trades']:5d} "
                  f"L={rep['long_gross']:+.2f} S={rep['short_gross']:+.2f} "
                  f"pq={rep['posq']:.2f} B={rep['B']:.4f}")
    d = pd.DataFrame(rows)
    print("\nMEDIAN: Sh=%.3f 2x=%.3f dd=%.3f to=%.1f S=%.3f pq=%.3f B=%.4f" % (
        d.sharpe.median(), d.sh2x.median(), d.maxdd.median(), d.turnover.median(),
        d.short_gross.median(), d.posq.median(), d.B.median()))
