"""EDA 11 - absolute-extremity SIZING on cross-sectional selection.

The failure in EDA 09 is that a purely RELATIVE short sleeve is short in absolute terms even when
no coin is genuinely near its own low. Sizing each leg by how far the coin actually sits from
mid-channel makes the short sleeve shrink exactly when nothing is low in its range, which is a
statement about location within a band and nothing else.
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
mode = sys.argv[1] if len(sys.argv) > 1 else "sizing"


def extremity_book(u: pd.DataFrame, k: int, mid: float = 0.5,
                   cap: float = 0.20) -> pd.DataFrame:
    s = u.where(mask)
    up = s.rank(axis=1, ascending=False, method="first")
    dn = s.rank(axis=1, ascending=True, method="first")
    long_w = (up <= k).astype(float) * (s - mid).clip(lower=0.0)
    short_w = (dn <= k).astype(float) * (mid - s).clip(lower=0.0)
    w = long_w - short_w
    g = w.abs().sum(axis=1)
    return w.div(g.where(g > 0), axis=0).fillna(0.0).clip(-cap, cap)


def full_extremity(u: pd.DataFrame, mid: float = 0.5, cap: float = 0.20) -> pd.DataFrame:
    s = u.where(mask) - mid
    g = s.abs().sum(axis=1)
    return s.div(g.where(g > 0), axis=0).fillna(0.0).clip(-cap, cap)


if mode == "sizing":
    for N in (147, 189, 231, 252, 294, 336):
        u = channel_position(hi, lo, cl, N)
        for k in (3, 5):
            phase_screen(f"EXT-topk N={N:3d} k={k} cad=21", extremity_book(u, k), 21, PH)
        phase_screen(f"EXT-full N={N:3d}      cad=21", full_extremity(u), 21, PH)
        print()

elif mode == "longonly":
    for N in (189, 252, 315):
        u = channel_position(hi, lo, cl, N)
        for k in (3, 5, 8):
            up = u.where(mask).rank(axis=1, ascending=False, method="first")
            w = (up <= k).astype(float)
            w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
            phase_screen(f"LONG-ONLY topk N={N} k={k} cad=21", w, 21, PH)
        print()
