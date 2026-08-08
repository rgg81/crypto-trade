"""EDA 08 - phase-averaged screen of the base mechanism and of the two candidate controls.

Every configuration is scored as the MEAN and MIN over seven rebalance phase offsets, so no
conclusion here can be phase luck. Controls:
  FRESH - restrict the long (short) candidate set to coins that printed a new N-bar high (low)
          within the last M bars: freshness of the breach, the EDA-04 carry/snap-back separator.
  COIL  - restrict candidates to the compressed half of (H_n - L_n) / (ATR * sqrt(n)):
          a break out of a compressed range carries, a break out of a noisy range is noise.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda05_designs import atr, cadence, cl, cols, hi, index, lo, mask, op, fund  # noqa: E402
from eda_panel import channel_position  # noqa: E402
from eda_sim2 import report, run  # noqa: E402

START = pd.Timestamp("2020-08-17T00:00:00Z")
NEG = -1e9


def sleeve_weights(long_score: pd.DataFrame, short_score: pd.DataFrame, k: int) -> pd.DataFrame:
    """Top-k by long_score long, top-k by short_score short; equal weight, unit gross."""
    up = long_score.where(mask).rank(axis=1, ascending=False, method="first")
    dn = short_score.where(mask).rank(axis=1, ascending=False, method="first")
    w = (up <= k).astype(float) - (dn <= k).astype(float)
    g = w.abs().sum(axis=1)
    return w.div(g.where(g > 0), axis=0).fillna(0.0)


def build(N: int, k: int, fresh: int = 0, coil_gate: bool = False):
    u = channel_position(hi, lo, cl, N)
    long_s = u.copy()
    short_s = (1.0 - u)
    if fresh > 0:
        hh, ll = hi.rolling(N, min_periods=N).max(), lo.rolling(N, min_periods=N).min()
        new_hi = (cl > hh.shift(1)).rolling(fresh, min_periods=1).max().astype(bool)
        new_lo = (cl < ll.shift(1)).rolling(fresh, min_periods=1).max().astype(bool)
        long_s = long_s + new_hi.astype(float)      # a fresh breach outranks any non-breacher
        short_s = short_s + new_lo.astype(float)
    if coil_gate:
        width = hi.rolling(N, min_periods=N).max() - lo.rolling(N, min_periods=N).min()
        coil = width / (atr * np.sqrt(N))
        med = coil.where(mask).median(axis=1)
        compressed = coil.ge(med, axis=0)
        long_s = long_s + compressed.astype(float) * 0.5
        short_s = short_s + compressed.astype(float) * 0.5
    return sleeve_weights(long_s, short_s, k)


def phase_screen(label, w, c, phases):
    rows = []
    for p in phases:
        res = run(w, op, fund, cadence(c, p), START)
        rep = report(res)
        res2 = run(w, op, fund, cadence(c, p), START, cost_mult=2.0)
        rep["sh2x"] = report(res2)["sharpe"]
        rows.append(rep)
    d = pd.DataFrame(rows)
    print(f"{label:40s} Sh mean={d.sharpe.mean():5.2f} min={d.sharpe.min():5.2f} "
          f"| Sh2x mean={d.sh2x.mean():5.2f} min={d.sh2x.min():5.2f} "
          f"| to={d.turnover.mean():5.1f} dd={d.maxdd.max():.3f} vol={d.vol.mean():.3f} "
          f"| S>0 {int((d.short_gross > 0).sum())}/{len(d)} (min {d.short_gross.min():+.2f}) "
          f"| L>0 {int((d.long_gross > 0).sum())}/{len(d)} "
          f"| tr={int(d.trades.min())} ge={d.gross_edge_bps.mean():5.0f} "
          f"| fp2x min={int(d.folds_pos.min())} wf min={d.worst_fold.min():5.2f} "
          f"| pq min={d.posq.min():.2f} t5={d.top5day.max():.2f}")
    return d


if __name__ == "__main__":
    PH = [0, 3, 6, 9, 12, 15, 18]
    print("=== base mechanism: sleeve size and formation ===")
    for N in (189, 252, 315):
        for k in (3, 4, 5):
            phase_screen(f"base N={N} k={k} cad=21", build(N, k), 21, PH)
    print("\n=== cadence ===")
    for c, ph in ((15, [0, 2, 4, 6, 8, 10, 12]), (27, [0, 4, 8, 12, 16, 20, 24]),
                  (42, [0, 6, 12, 18, 24, 30, 36])):
        phase_screen(f"base N=252 k=3 cad={c}", build(252, 3), c, ph)
    print("\n=== controls (N=252 k=3 cad=21) ===")
    for f in (9, 21, 63):
        phase_screen(f"FRESH({f}) only", build(252, 3, fresh=f), 21, PH)
    phase_screen("COIL only", build(252, 3, coil_gate=True), 21, PH)
    phase_screen("FRESH(21)+COIL", build(252, 3, fresh=21, coil_gate=True), 21, PH)
