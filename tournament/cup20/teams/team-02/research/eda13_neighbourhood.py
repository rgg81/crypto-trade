"""EDA 13 - per-metric median across the intended declared neighbourhood, in the research sim.

The declared sweep is the number that is scored, so it is the number worth screening before a
trial is spent on it. Rebalance boundaries are selected exactly as the frozen strategy will do
it -- off the absolute 8h bar index, so PHASE_OFFSET means the same thing here and there.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cl, fund, hi, index, lo, mask, op  # noqa: E402
from eda08_controls import sleeve_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402
from eda_sim2 import bootstrap_B, report, run  # noqa: E402

START = pd.Timestamp("2020-08-17T00:00:00Z")
BAR_INDEX = pd.Index((index.asi8 // (8 * 3600 * 10**9)).astype(np.int64))
SLEEVE_SIZE = 3


def rebalance(cad: int, phase: int) -> pd.Series:
    return pd.Series((BAR_INDEX % cad) == (phase % cad), index=index)


def evaluate(N: int, cad: int, phase: int) -> dict:
    u = channel_position(hi, lo, cl, N)
    w = sleeve_weights(u, 1 - u, SLEEVE_SIZE)
    reb = rebalance(cad, phase)
    r1 = run(w, op, fund, reb, START)
    rep = report(r1)
    rep["B"] = bootstrap_B(r1["net"])
    rep["sh2x"] = report(run(w, op, fund, reb, START, cost_mult=2.0))["sharpe"]
    r3 = report(run(w, op, fund, reb, START, cost_mult=3.0))
    rep["sh3x"] = r3["sharpe"]
    rep["ann3x"] = r3["ann_ret"]
    return rep


NOMINEE = (252, 21, 12)
POINTS = [
    (252, 21, 12),
    (210, 21, 12),
    (294, 21, 12),
    (252, 15, 12),
    (252, 27, 12),
    (252, 21, 5),
    (252, 21, 18),
]

rows = []
for N, cad, ph in POINTS:
    rep = evaluate(N, cad, ph)
    rep["point"] = f"N={N},cad={cad},ph={ph}"
    rows.append(rep)
    print(f"{rep['point']:22s} Sh={rep['sharpe']:5.2f} 2x={rep['sh2x']:5.2f} 3x={rep['sh3x']:5.2f} "
          f"ret={rep['ann_ret']:+.3f} vol={rep['vol']:.3f} dd={rep['maxdd']:.3f} "
          f"to={rep['turnover']:5.1f} tr={rep['trades']:5d} ge={rep['gross_edge_bps']:6.1f} "
          f"L={rep['long_gross']:+.2f} S={rep['short_gross']:+.2f} pq={rep['posq']:.2f} "
          f"fp={rep['folds_pos']} wf={rep['worst_fold']:5.2f} B={rep['B']:.4f}")

d = pd.DataFrame(rows)
print("\n--- PER-METRIC MEDIAN ACROSS THE 7 POINTS (this is what would be scored) ---")
med = d.drop(columns=["point"]).median(numeric_only=True)
floors = {
    "sharpe": (">=", 0.80), "sh2x": (">=", 0.50), "sh3x": (">", 0.0),
    "ann_ret": (">", 0.0), "maxdd": ("<=", 0.20), "vol": (">=", 0.06),
    "posq": (">=", 0.50), "folds_pos": (">=", 3), "worst_fold": (">=", -0.25),
    "turnover": ("<=", 25.0), "gross_edge_bps": (">=", 40.0), "trades": (">=", 500),
    "long_gross": (">", 0.0), "short_gross": (">", 0.0), "top5day": ("<=", 0.35),
}
for k, (op_, f) in floors.items():
    v = float(med[k])
    ok = (v >= f) if op_ == ">=" else (v <= f) if op_ == "<=" else (v > f)
    print(f"  {k:16s} median={v:9.4f}  floor {op_} {f:<8} {'PASS' if ok else '**FAIL**'}")
B = float(med["B"])
for T in (8, 10, 12):
    print(f"  confidence at T={T}: {max(0.0, min(1.0, 1 - T * (1 - B))):.4f}  (floor 0.90)")
pf = float(((d.ann_ret > 0) & (d.sh2x > 0)).mean())
print(f"  positive_point_fraction = {pf:.3f}  (floor 0.70)")
