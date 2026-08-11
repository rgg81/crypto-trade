"""EDA 3 -- split the shock by direction, and separate the beta component from the residual.

EDA 2 showed a strong asymmetry: market-wide down-shocks snap back over 16-24h, while up-shocks
do not. Pooling the two directions through ``-sign(z)`` was hiding it. This file measures the two
sleeves separately, on both raw and cross-sectionally-demeaned forward returns, and asks whether
the liquidity signature adds anything once direction is respected.

Free research. No trial.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel, demean, forward_from_open, summarise  # noqa: E402

P = build_panel(lookback=60)
op, cl, ret, sigma = P["open"], P["close"], P["ret"], P["sigma"]
mask = P["tradable"]
fwd = forward_from_open(op, horizons=(1, 2, 3, 6, 9))
fwd_i = {h: demean(f, mask) for h, f in fwd.items()}
fwd_r = {h: f.where(mask) for h, f in fwd.items()}

z = (ret / sigma).where(mask)
vs = P["vspike"].where(mask)
ts = P["tspike"].where(mask)
rr = P["rr"].where(mask)

mkt_ret = ret.where(mask).mean(axis=1)
mkt_sig = mkt_ret.rolling(60, min_periods=30).std().shift(1)
mkt_z = (mkt_ret / mkt_sig).rename("mkt_z")


def broadcast(series: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        np.repeat(series.to_numpy()[:, None], z.shape[1], axis=1), index=z.index, columns=z.columns
    )


MZ = broadcast(mkt_z)

print("=" * 104)
print("1. DOWN shocks -> long. RAW forward return (includes beta) and IDIO (demeaned).")
print("=" * 104)
for zth in (-1.5, -2.0, -2.5, -3.0):
    sel = z <= zth
    for h in (1, 2, 3, 6, 9):
        raw = fwd_r[h].where(sel).to_numpy().ravel()
        idio = fwd_i[h].where(sel).to_numpy().ravel()
        print(f"   z<={zth} h={h}:  RAW " + summarise("", raw)[38:]
              + "   | IDIO " + summarise("", idio)[38:])

print()
print("=" * 104)
print("2. UP shocks -> short. RAW (short pays -raw) and IDIO.")
print("=" * 104)
for zth in (1.5, 2.0, 2.5, 3.0):
    sel = z >= zth
    for h in (1, 2, 3, 6, 9):
        raw = (-fwd_r[h]).where(sel).to_numpy().ravel()
        idio = (-fwd_i[h]).where(sel).to_numpy().ravel()
        print(f"   z>={zth} h={h}:  RAW " + summarise("", raw)[38:]
              + "   | IDIO " + summarise("", idio)[38:])

print()
print("=" * 104)
print("3. DOWN shocks, conditioned on the liquidity signature (IDIO forward, h=3)")
print("=" * 104)
down = z <= -2.0
for label, sig in (("vspike", vs), ("tspike", ts), ("rr", rr)):
    vals = sig.where(down)
    q1, q2 = np.nanquantile(vals.to_numpy(), [1 / 3, 2 / 3])
    for lab, sel in (
        (f"{label} low ", down & (sig <= q1)),
        (f"{label} mid ", down & (sig > q1) & (sig <= q2)),
        (f"{label} high", down & (sig > q2)),
    ):
        for h in (1, 3, 6):
            print("   " + summarise(f"{lab} h={h} IDIO", fwd_i[h].where(sel).to_numpy().ravel())
                  + " | RAW " + summarise("", fwd_r[h].where(sel).to_numpy().ravel())[38:])

print()
print("=" * 104)
print("4. DOWN shocks x market-wide stress (mkt_z), RAW forward -- the cascade case")
print("=" * 104)
for mz_hi in (0.0, -1.0, -1.5, -2.0):
    for zth in (-1.5, -2.0, -2.5):
        sel = (z <= zth) & (MZ <= mz_hi)
        for h in (1, 3, 6):
            print("   " + summarise(f"z<={zth} mkt_z<={mz_hi} h={h}",
                                    fwd_r[h].where(sel).to_numpy().ravel()))

print()
print("=" * 104)
print("5. Baseline for comparison: unconditional forward return of an equal-weight member basket")
print("=" * 104)
for h in (1, 3, 6, 9):
    print("   " + summarise(f"all member bars h={h}", fwd_r[h].to_numpy().ravel()))
