"""EDA 07 - rebalance phase sweep. Phase is a first-order axis, not a detail."""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cadence, cl, hi, lo, rank_weights, show, topk_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402

for N in (189, 252, 315):
    u = channel_position(hi, lo, cl, N)
    for c in (9, 21):
        sh = []
        for p in range(0, c, max(1, c // 7)):
            r = show(f"top3 u N={N} cad={c:2d} phase={p:2d}", topk_weights(u, 3), cadence(c, p))
            sh.append(r["sharpe"])
        print(f"  -> top3 N={N} cad={c}: phase Sharpe mean={np.mean(sh):.2f} "
              f"min={np.min(sh):.2f} max={np.max(sh):.2f}\n")
    for c in (21,):
        sh = []
        for p in range(0, c, max(1, c // 7)):
            r = show(f"rank u N={N} cad={c:2d} phase={p:2d}", rank_weights(u), cadence(c, p))
            sh.append(r["sharpe"])
        print(f"  -> rank N={N} cad={c}: phase Sharpe mean={np.mean(sh):.2f} "
              f"min={np.min(sh):.2f} max={np.max(sh):.2f}\n")
