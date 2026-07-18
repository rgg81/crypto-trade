"""e09/e10 — form E refinements: inverse-vol sizing; deadband x smoothing at N=60."""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

from breakout import channel_pos
from common import line, panels, score

pn, aux, scoring = panels()
close = pn["close"]

lr1 = np.log(close.where(close > 0)).diff()
sig_vol = lr1.rolling(42, min_periods=30).std()
vol_floor = sig_vol.quantile(0.2, axis=1)
vol_adj = sig_vol.clip(lower=pd.DataFrame(
    np.tile(vol_floor.to_numpy()[:, None], (1, sig_vol.shape[1])),
    index=sig_vol.index, columns=sig_vol.columns))

print("== e09: inverse-vol sizing, form E d=0.25 k=1 ==")
for N in (30, 60, 90):
    s = (channel_pos(close, N, 0.25) / vol_adj).fillna(0.0)
    _, _, _, m1 = score(s)
    _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
    print(line(f"ivE N={N:3d} @1x", m1) + f"  S2x={m2.sharpe:+.3f}")

print("\n== e10: d x k grid at N=60 (raw sizing unless e09 wins) ==")
for d in (0.0, 0.25, 0.5):
    for k in (1, 3, 6):
        s = channel_pos(close, 60, d).fillna(0.0)
        if k > 1:
            s = s.ewm(span=k).mean()
        _, _, _, m1 = score(s)
        _, _, _, m2 = score(s, cost_mult=2.0, slip_mult=2.0)
        print(line(f"E N=60 d={d:.2f} k={k} @1x", m1) + f"  S2x={m2.sharpe:+.3f} min={min(m1.sharpe, m2.sharpe):+.3f}")
