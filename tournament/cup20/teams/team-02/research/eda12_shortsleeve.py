"""EDA 12 - anatomy of the short sleeve, and two attempts to make its sign robust.

The one floor the mechanism keeps threatening to fail is ``short_gross_pnl > 0`` at 1x cost.
This isolates it: per-fold price and funding decomposition of the short leg, then (a) tighter
sleeves, (b) an absolute outer-band screen layered on top of the cross-sectional selection.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import cadence, cl, cols, fund, hi, index, lo, mask, op  # noqa: E402
from eda08_controls import phase_screen, sleeve_weights  # noqa: E402
from eda_panel import channel_position  # noqa: E402

PH = [0, 3, 6, 9, 12, 15, 18]
mode = sys.argv[1] if len(sys.argv) > 1 else "anatomy"
START = pd.Timestamp("2020-08-17T00:00:00Z")


def hybrid(u: pd.DataFrame, k: int, band: float, cap: float = 0.20) -> pd.DataFrame:
    """Top-k long / bottom-k short, but only names in the outer band of their own range."""
    s = u.where(mask)
    up = s.rank(axis=1, ascending=False, method="first")
    dn = s.rank(axis=1, ascending=True, method="first")
    w = ((up <= k) & (s >= 1.0 - band)).astype(float) - ((dn <= k) & (s <= band)).astype(float)
    g = w.abs().sum(axis=1)
    return w.div(g.where(g > 0), axis=0).fillna(0.0).clip(-cap, cap)


if mode == "anatomy":
    # per-fold decomposition of the short leg of the base book
    for N in (189, 210, 231, 252):
        u = channel_position(hi, lo, cl, N)
        w = sleeve_weights(u, 1 - u, 3)
        for p in (0, 9, 18):
            reb = cadence(21, p).to_numpy()
            wn = w.to_numpy()
            held = np.zeros(len(cols))
            o = op.to_numpy(float)
            fn = fund.to_numpy(float)
            first = int(np.arange(len(index))[index >= START][0])
            rows = []
            for t in range(first, len(index) - 2):
                px = o[t + 1]
                tradable = np.isfinite(px) & (px > 0)
                if reb[t]:
                    held = np.where(tradable, wn[t], 0.0)
                nxt = o[t + 2]
                ok = tradable & np.isfinite(nxt) & (nxt > 0)
                step = np.where(ok, nxt / np.where(tradable, px, 1.0) - 1.0, 0.0)
                short = held < 0
                rows.append((index[t], float((held * step)[short].sum()),
                             float((-held * np.nan_to_num(fn[t + 1]))[short].sum())))
            d = pd.DataFrame(rows, columns=["t", "price", "funding"]).set_index("t")
            tot = {}
            for name, a, b in (("F1", "2020-08-17", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
                               ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", None)):
                m = d.index >= pd.Timestamp(a, tz="UTC")
                if b is not None:
                    m = m & (d.index < pd.Timestamp(b, tz="UTC"))
                tot[name] = (d.price[m].sum(), d.funding[m].sum())
            print(f"N={N} phase={p:2d} SHORT leg (unit-gross book, per fold: price / funding / net)")
            print("   " + "  ".join(
                f"{k_}: {v[0]:+.2f}/{v[1]:+.2f}={v[0] + v[1]:+.2f}" for k_, v in tot.items())
                + f"   TOTAL {d.price.sum() + d.funding.sum():+.2f}")
        print()

elif mode == "tight":
    for N in (210, 231, 252):
        u = channel_position(hi, lo, cl, N)
        for k in (2, 3):
            phase_screen(f"base N={N} k={k} cad=21", sleeve_weights(u, 1 - u, k), 21, PH)
        print()

elif mode == "hybrid":
    for N in (210, 252):
        u = channel_position(hi, lo, cl, N)
        for band in (0.50, 0.40, 0.30):
            phase_screen(f"HYB N={N} k=3 band={band:.2f} cad=21", hybrid(u, 3, band), 21, PH)
        print()
