"""EDA 10 - absolute position-in-channel thresholds, and the long-only alternative.

The cross-sectional rank book (EDA 09) fails one floor structurally: its short sleeve is a
RELATIVE short in an absolutely rising market, so its gross PnL is a coin flip. An absolute
threshold book only shorts a coin that is actually at or through its own multi-week low, so the
short sleeve exists exactly when coins are genuinely falling.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cl, hi, lo, mask  # noqa: E402
from eda08_controls import phase_screen  # noqa: E402
from eda_panel import channel_position  # noqa: E402

PH = [0, 3, 6, 9, 12, 15, 18]
mode = sys.argv[1] if len(sys.argv) > 1 else "abs"


def threshold_book(u: pd.DataFrame, hi_t: float, lo_t: float,
                   cap: float = 0.20) -> pd.DataFrame:
    s = u.where(mask)
    w = (s >= hi_t).astype(float) - (s <= lo_t).astype(float)
    w = w.where(s.notna(), 0.0)
    g = w.abs().sum(axis=1)
    w = w.div(g.where(g > 0), axis=0).fillna(0.0)
    return w.clip(-cap, cap)


if mode == "abs":
    for N in (126, 189, 252, 315):
        u = channel_position(hi, lo, cl, N)
        for hi_t, lo_t in ((0.90, 0.10), (0.85, 0.15), (0.75, 0.25), (0.95, 0.05)):
            phase_screen(f"ABS N={N:3d} u>={hi_t:.2f}/<={lo_t:.2f} cad=21",
                         threshold_book(u, hi_t, lo_t), 21, PH)
        print()

elif mode == "longonly":
    for N in (189, 252, 315):
        u = channel_position(hi, lo, cl, N)
        for k in (3, 5, 8):
            up = u.where(mask).rank(axis=1, ascending=False, method="first")
            w = (up <= k).astype(float)
            w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
            phase_screen(f"LONG-ONLY topk N={N} k={k} cad=21", w, 21, PH)
        for t in (0.85, 0.90):
            w = (u.where(mask) >= t).astype(float)
            w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).clip(0, 0.20)
            phase_screen(f"LONG-ONLY u>={t} N={N} cad=21", w, 21, PH)
        print()
