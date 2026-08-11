"""EDA 2 -- if single-bar idiosyncratic shocks CONTINUE, where does the snap-back live?

EDA 1 found the naive form of the lane is backwards: at 8h, a large idiosyncratic move continues,
and it continues MOST when volume and trade count spiked with it. That is the informed-flow case,
not the forced-flow case. This file hunts for the subset where the overshoot is mechanical:

  1. multi-bar formation (a cascade is rarely one 8h bar)
  2. close location inside the bar range (absorbed wick vs unabsorbed close-on-low)
  3. raw vs idiosyncratic (a market-wide deleveraging is a beta event, not a cross-sectional one)
  4. market-wide stress conditioning
  5. funding dislocation

Free research. No trial.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel, demean, forward_from_open, summarise  # noqa: E402

P = build_panel(lookback=60)
op, cl = P["open"], P["close"]
mask = P["tradable"]
ret, sigma = P["ret"], P["sigma"]
fwd = forward_from_open(op, horizons=(1, 2, 3, 6))
fwd_i = {h: demean(f, mask) for h, f in fwd.items()}

z = (ret / sigma).where(mask)
vs = P["vspike"].where(mask)

bars = pd.read_parquet("data/cup20/is/bars.parquet").sort_values(["symbol", "open_time"])
hi = bars.pivot(index="open_time", columns="symbol", values="high").sort_index()
lo = bars.pivot(index="open_time", columns="symbol", values="low").sort_index()
clv = ((cl - lo) / (hi - lo).replace(0.0, np.nan)).where(mask)

print("=" * 100)
print("1. Multi-bar formation: cumulative k-bar move / (sigma*sqrt(k))")
print("=" * 100)
for k in (1, 2, 3, 6, 9):
    cum = cl / cl.shift(k) - 1.0
    zk = (cum / (sigma * np.sqrt(k))).where(mask)
    sel = zk.abs() >= 2.5
    for h in (1, 3, 6):
        rev = (-np.sign(zk) * fwd_i[h]).where(sel)
        print("   " + summarise(f"k={k} |zk|>=2.5  h={h}", rev.to_numpy().ravel()))

print()
print("=" * 100)
print("2. Close location in range (clv): shock bars split by whether the move was absorbed")
print("   down-shock (z<-2.5): clv high = closed well off the low = wick absorbed")
print("=" * 100)
down = z <= -2.5
up = z >= 2.5
for tag, sel_base, side in (("DOWN->long", down, +1.0), ("UP->short", up, -1.0)):
    vals = clv.where(sel_base)
    q1, q2 = np.nanquantile(vals.to_numpy(), [1 / 3, 2 / 3])
    print(f"-- {tag}: clv terciles {q1:.2f}/{q2:.2f}")
    for lab, sel in (
        ("clv low ", sel_base & (clv <= q1)),
        ("clv mid ", sel_base & (clv > q1) & (clv <= q2)),
        ("clv high", sel_base & (clv > q2)),
    ):
        for h in (1, 3):
            print("   " + summarise(f"{lab} h={h}", (side * fwd_i[h]).where(sel).to_numpy().ravel()))

print()
print("=" * 100)
print("3. RAW (not demeaned) forward returns -- market-wide cascade reversal")
print("=" * 100)
mkt_ret = ret.where(mask).mean(axis=1)
mkt_sig = mkt_ret.rolling(60, min_periods=30).std().shift(1)
mkt_z = mkt_ret / mkt_sig
mkt_fwd = {h: fwd[h].where(mask).mean(axis=1) for h in (1, 2, 3, 6)}
for lo_b, hi_b in [(-100, -3), (-3, -2), (-2, -1), (-1, 1), (1, 2), (2, 3), (3, 100)]:
    sel = (mkt_z >= lo_b) & (mkt_z < hi_b)
    for h in (1, 3):
        v = mkt_fwd[h].where(sel).to_numpy()
        print("   " + summarise(f"mkt_z in [{lo_b},{hi_b}) h={h}", v))

print()
print("=" * 100)
print("4. Cross-sectional shock reversal CONDITIONED on market-wide stress")
print("=" * 100)
stress = (mkt_z.abs() >= 1.5)
for tag, cond in (("calm market ", ~stress), ("stressed mkt", stress)):
    sel = (z.abs() >= 2.5) & pd.DataFrame(
        np.repeat(cond.to_numpy()[:, None], z.shape[1], axis=1), index=z.index, columns=z.columns
    )
    for h in (1, 3):
        print("   " + summarise(f"{tag} h={h}", (-np.sign(z) * fwd_i[h]).where(sel).to_numpy().ravel()))

print()
print("=" * 100)
print("5. Funding dislocation at the shock (funding z-score over trailing 60 bars)")
print("=" * 100)
f8 = P["funding"].where(mask)
fz = ((f8 - f8.rolling(60, min_periods=30).mean().shift(1))
      / f8.rolling(60, min_periods=30).std().shift(1)).where(mask)
big = z.abs() >= 2.5
vals = (np.sign(z) * fz).where(big)
q1, q2 = np.nanquantile(vals.to_numpy(), [1 / 3, 2 / 3])
print(f"   sign(z)*funding_z terciles {q1:.2f}/{q2:.2f}")
for lab, sel in (
    ("fund against move", big & (np.sign(z) * fz <= q1)),
    ("fund neutral     ", big & (np.sign(z) * fz > q1) & (np.sign(z) * fz <= q2)),
    ("fund with move   ", big & (np.sign(z) * fz > q2)),
):
    for h in (1, 3):
        print("   " + summarise(f"{lab} h={h}", (-np.sign(z) * fwd_i[h]).where(sel).to_numpy().ravel()))

print()
print("=" * 100)
print("6. LOW-volume shocks only (the air-pocket case), by |z| and horizon")
print("=" * 100)
for vth in (0.8, 1.0, 1.3):
    for zth in (2.0, 2.5, 3.0):
        sel = (z.abs() >= zth) & (vs <= vth)
        for h in (1, 2, 3):
            print("   " + summarise(f"vspike<={vth} |z|>={zth} h={h}",
                                    (-np.sign(z) * fwd_i[h]).where(sel).to_numpy().ravel()))
