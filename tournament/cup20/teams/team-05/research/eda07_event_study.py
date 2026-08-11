"""EDA 7 -- the shape of the snap-back, bar by bar, instead of inferred from Sharpe.

EDA 6 picked entry_delay=1 and hold=3 because those configurations scored best. That is exactly
the way to fit a spike. This file measures the thing directly: for a shock event on bar i, what is
the mean return of bar i+k for k = 0..10, in each fold, with and without the flow signature.

If the mechanism is real the profile should look like: a continuation bar (the cascade completing),
then a positive block while the forced flow is unwound, then nothing. If instead it looks like a
single positive bar surrounded by noise, the earlier configuration choice was a fit.

Approximation, not a scorer.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from panel import build_panel  # noqa: E402

P = build_panel(lookback=60)
op, ret, sigma = P["open"], P["ret"], P["sigma"]
mask = P["tradable"]
z = (ret / sigma).where(mask)
ts = P["tspike"].where(mask)

# bar return measured open-to-open, the way the evaluator would realise it
bar = (op.shift(-1) / op - 1.0).where(mask)

FOLDS = [("F1", "2020-08-01", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
         ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", "2024-08-01")]


def event_profile(sel: pd.DataFrame, kmax: int = 10, rows: np.ndarray | None = None) -> list:
    out = []
    for k in range(kmax + 1):
        v = bar.shift(-k).where(sel)
        if rows is not None:
            v = v.loc[rows]
        arr = v.to_numpy().ravel()
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            out.append((0, np.nan, np.nan))
            continue
        se = arr.std(ddof=1) / np.sqrt(arr.size)
        out.append((arr.size, arr.mean() * 1e4, arr.mean() / se if se > 0 else np.nan))
    return out


shock_sig = ((z <= -2.0) & (ts >= 2.0)).fillna(False)
breadth = shock_sig.sum(axis=1)
casc = breadth >= 2
CASC = pd.DataFrame(np.repeat(casc.to_numpy()[:, None], z.shape[1], axis=1),
                    index=z.index, columns=z.columns)
sel_sig = shock_sig & CASC
shock_nosig = ((z <= -2.0)).fillna(False)
breadth_ns = shock_nosig.sum(axis=1)
CASC_NS = pd.DataFrame(np.repeat((breadth_ns >= 2).to_numpy()[:, None], z.shape[1], axis=1),
                       index=z.index, columns=z.columns)
sel_nosig = shock_nosig & CASC_NS

print("=" * 100)
print("Per-bar mean open-to-open return after a down-shock, bp (t-stat in brackets)")
print("bar k=0 is the shock bar itself (already realised; not tradable)")
print("=" * 100)
print(f"{'k':>3} | {'WITH signature (z<=-2, ts>=2)':>34} | {'NO signature (z<=-2 only)':>34}")
a = event_profile(sel_sig)
b = event_profile(sel_nosig)
for k in range(len(a)):
    print(f"{k:>3} | n={a[k][0]:>6} {a[k][1]:>8.1f}bp [{a[k][2]:>5.2f}] | "
          f"n={b[k][0]:>6} {b[k][1]:>8.1f}bp [{b[k][2]:>5.2f}]")

print()
print("=" * 100)
print("Cumulative from a fill at the open of bar i+d, held H bars (WITH signature)")
print("=" * 100)
print(f"{'delay d':>8}" + "".join(f"{'H=' + str(h):>12}" for h in (1, 2, 3, 4, 5, 6)))
for d in (1, 2, 3):
    line = f"{d:>8}"
    for h in (1, 2, 3, 4, 5, 6):
        tot = sum(a[k][1] for k in range(d, d + h))
        line += f"{tot:>12.1f}"
    print(line)

print()
print("=" * 100)
print("Per-fold profile, WITH signature (bp)")
print("=" * 100)
print(f"{'fold':<6}" + "".join(f"{'k=' + str(k):>10}" for k in range(0, 7)))
for name, lo, hi in FOLDS:
    rows = (z.index >= pd.Timestamp(lo, tz="UTC")) & (z.index < pd.Timestamp(hi, tz="UTC"))
    prof = event_profile(sel_sig, kmax=6, rows=rows)
    print(f"{name:<6}" + "".join(f"{p[1]:>10.1f}" for p in prof) + f"   n={prof[0][0]}")

print()
print("=" * 100)
print("Same, NO signature (bp) -- the ablation, per fold")
print("=" * 100)
print(f"{'fold':<6}" + "".join(f"{'k=' + str(k):>10}" for k in range(0, 7)))
for name, lo, hi in FOLDS:
    rows = (z.index >= pd.Timestamp(lo, tz="UTC")) & (z.index < pd.Timestamp(hi, tz="UTC"))
    prof = event_profile(sel_nosig, kmax=6, rows=rows)
    print(f"{name:<6}" + "".join(f"{p[1]:>10.1f}" for p in prof) + f"   n={prof[0][0]}")

print()
print("=" * 100)
print("Signature graded: mean of bars k=2..4 (the tradable snap-back block) by tspike bucket")
print("=" * 100)
blk = sum([bar.shift(-k) for k in (2, 3, 4)])
base = ((z <= -2.0) & CASC_NS).fillna(False)
for lo_b, hi_b in [(0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 5.0), (5.0, 1e9)]:
    sel = base & (ts >= lo_b) & (ts < hi_b)
    arr = blk.where(sel).to_numpy().ravel()
    arr = arr[np.isfinite(arr)]
    se = arr.std(ddof=1) / np.sqrt(arr.size) if arr.size > 1 else np.nan
    print(f"   tspike [{lo_b},{hi_b}): n={arr.size:>6}  mean={arr.mean() * 1e4:>8.1f}bp  "
          f"t={arr.mean() / se if se and se > 0 else float('nan'):>6.2f}")
print()
for lo_b, hi_b in [(0, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 5.0), (5.0, 1e9)]:
    sel = base & (P["vspike"] >= lo_b) & (P["vspike"] < hi_b)
    arr = blk.where(sel).to_numpy().ravel()
    arr = arr[np.isfinite(arr)]
    se = arr.std(ddof=1) / np.sqrt(arr.size) if arr.size > 1 else np.nan
    print(f"   vspike [{lo_b},{hi_b}): n={arr.size:>6}  mean={arr.mean() * 1e4:>8.1f}bp  "
          f"t={arr.mean() / se if se and se > 0 else float('nan'):>6.2f}")
