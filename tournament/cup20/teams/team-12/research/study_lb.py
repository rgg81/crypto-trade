"""Combined-book sensitivity to each sleeve's own formation horizon (cadence 6, phase 3)."""
from __future__ import annotations
import sys
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
import combo as CO
from sleevegen import sleeve_matrix

p = Panel()
base = {s: sleeve_matrix(p, s, {}) for s in CO.SLEEVES}
GRID = {
    "flow":    ("FLOW_BASE_LOOKBACK",    [48, 55, 72, 80, 90]),
    "lowrisk": ("LOWRISK_BASE_LOOKBACK", [150, 168, 210, 231, 252]),
    "trend":   ("TREND_BASE_LOOKBACK",   [72, 80, 100, 110, 126]),
    "carry":   ("CARRY_LOOKBACK",        [84, 105, 147, 168, 189]),
}
for sleeve, (const, values) in GRID.items():
    print(f"\n=== {const} (nominee {'63' if sleeve=='flow' else '189' if sleeve=='lowrisk' else '90' if sleeve=='trend' else '126'}) ===")
    for v in values:
        m = dict(base)
        m[sleeve] = sleeve_matrix(p, sleeve, {const: v})
        W, _ = CO.combine(p, m, bars=270)
        CO.score(p, W, 6, 3, label=f"{const}={v}")
