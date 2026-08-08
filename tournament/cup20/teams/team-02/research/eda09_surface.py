"""EDA 09 - formation surface and structural alternatives, all phase-averaged over 7 offsets."""

from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cl, hi, lo, mask  # noqa: E402
from eda08_controls import phase_screen, sleeve_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402

PH = [0, 3, 6, 9, 12, 15, 18]
mode = sys.argv[1] if len(sys.argv) > 1 else "surface"

if mode == "surface":
    for k in (3, 4):
        for N in (147, 168, 189, 210, 231, 252, 273, 294, 315, 336):
            u = channel_position(hi, lo, cl, N)
            phase_screen(f"N={N:3d} k={k} cad=21", sleeve_weights(u, 1 - u, k), 21, PH)
        print()

elif mode == "longonly":
    for N in (189, 252, 315):
        for k in (3, 5, 8):
            u = channel_position(hi, lo, cl, N)
            up = u.where(mask).rank(axis=1, ascending=False, method="first")
            w = (up <= k).astype(float)
            w = w.div(w.abs().sum(axis=1).replace(0, 1), axis=0).fillna(0.0)
            phase_screen(f"LONG-ONLY N={N} k={k} cad=21", w, 21, PH)
        print()
