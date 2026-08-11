"""EDA 10 -- why the harness number is below the gross-book number, and what the book can do about it.

Trial #46 (the nominee) reported, among other things:

    requested  78/276 boundaries reduced, minimum scale 0.4000, median 0.4000, binding symbol:78
    risk-unit scalar  median 0.4703  min 0.2000  max 1.2483

The first line is the one the book controls. More than half of the entries carried exactly two
names, so at unit gross each name asked for 0.50 against a 0.20 per-symbol cap and the whole
episode executed at 0.40 gross. The number of names that happened to cross a threshold was
therefore silently setting the size of the position -- an exposure lottery the mechanism never
asked for, and one charter section 14.7 says will not be redistributed back.

The fix that follows from the mechanism rather than from the scoreboard: the THRESHOLD decides
whether a cascade is happening; the RANKING decides which names to buy; and the basket size is a
fixed structural choice. Five names is where the per-symbol cap stops binding at unit gross.

This file measures what fixing the basket does to the gross book: does diluting with the
next-most-shocked names destroy the edge per unit of turnover, or does the extra exposure pay for
it? It models the per-symbol cap, because that is a property of the book's own shape. It does NOT
model the common risk unit and computes no floor and no ranking score.
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
STEP = (op.shift(-2) / op.shift(-1) - 1.0).where(mask)
FOLDS = [("F1", "2020-08-17", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
         ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", "2024-08-01")]
COST = 7.5 / 1e4
IDX, COLS, N = z.index, list(z.columns), len(z.index)
TRADABLE = mask.to_numpy()
STEP_A = STEP.fillna(0.0).to_numpy()
FOLD_SEL = [((IDX >= pd.Timestamp(lo, tz="UTC")) & (IDX < pd.Timestamp(hi, tz="UTC")))
            for _, lo, hi in FOLDS]
CAP = 0.20


def simulate(shock_z=-2.0, flow_spike=2.0, breadth=2, hold_bars=3, entry_delay=1,
             basket=None, max_names=8, apply_cap=True) -> dict:
    """`basket=None` keeps the threshold-set basket; an int takes the top-N by shock depth."""
    qual = ((z <= shock_z) & (ts >= flow_spike)).fillna(False).to_numpy()
    depth_all = (-z).where(z < 0).fillna(0.0).to_numpy()
    depth_q = (-z).where((z <= shock_z) & (ts >= flow_spike)).fillna(0.0).to_numpy()
    cascade = qual.sum(axis=1) >= breadth

    W = np.zeros((N, len(COLS)))
    emitted = np.zeros(N, dtype=bool)
    held = np.zeros(len(COLS))
    age, in_pos = 0, False
    for i in range(N):
        if in_pos:
            age += 1
            if age >= hold_bars:
                emitted[i] = True
                in_pos, held = False, np.zeros(len(COLS))
            else:
                W[i] = held
            continue
        j = i - entry_delay
        if j < 0 or not cascade[j]:
            continue
        if basket is None:
            cand = depth_q[j] * TRADABLE[i]
            keep = [k for k in np.argsort(-cand) if cand[k] > 0][:max_names]
        else:
            cand = depth_all[j] * TRADABLE[i]
            keep = [k for k in np.argsort(-cand) if cand[k] > 0][:basket]
        if not keep:
            continue
        w = np.zeros(len(COLS))
        w[keep] = 1.0 / len(keep)
        if apply_cap:
            top = w.max()
            if top > CAP:
                w = w * (CAP / top)  # one uniform reduction, never redistributed
        W[i] = w
        held, age, in_pos, emitted[i] = w, 0, True, True

    Wd = pd.DataFrame(W, index=IDX, columns=COLS)
    dw = (Wd - Wd.shift(1).fillna(0.0)).abs().sum(axis=1)
    dw[~emitted] = 0.0
    tt = float(dw.sum())
    years = N / 1095.0
    pnl = pd.Series((W * STEP_A).sum(axis=1), index=IDX)
    cost = dw * COST

    def sh(s):
        d = s.groupby(pd.DatetimeIndex(s.index).floor("D")).sum()
        return float(d.mean() / d.std() * np.sqrt(365)) if d.std() > 0 else np.nan

    folds = [sh((pnl - 2 * cost)[sel]) for sel in FOLD_SEL]
    daily = (pnl - cost).groupby(pd.DatetimeIndex(IDX).floor("D")).sum()
    eq = (1 + daily).cumprod()
    q = (1 + daily).groupby(pd.DatetimeIndex(daily.index).tz_convert("UTC").tz_localize(None)
                            .to_period("Q")).prod() - 1
    nz = (W != 0).sum(axis=1)
    return {
        "turn/yr": tt / years, "gross%/yr": float(pnl.sum()) / years * 100,
        "bps/turn": float(pnl.sum()) / tt * 1e4 if tt > 0 else np.nan,
        "shp_2x": sh(pnl - 2 * cost), "wfold": min(folds), "mfold": float(np.median(folds)),
        "F1": folds[0], "F2": folds[1], "F3": folds[2], "F4": folds[3],
        "maxDD": float((1 - eq / eq.cummax()).max()), "posQ": float((q > 0).mean()),
        "avg gross": float(W.sum(axis=1)[nz > 0].mean()) if (nz > 0).any() else 0.0,
        "names": float(nz[nz > 0].mean()) if (nz > 0).any() else 0.0,
        "eps/yr": float(emitted.sum()) / 2 / years,
    }


KEYS = ["turn/yr", "gross%/yr", "bps/turn", "shp_2x", "wfold", "mfold", "F1", "F2", "F3", "F4",
        "maxDD", "posQ", "avg gross", "names", "eps/yr"]
print(f"{'config':<44}" + "".join(f"{k:>11}" for k in KEYS))
print("-" * 220)


def show(label, **kw):
    r = simulate(**kw)
    print(f"{label:<44}" + "".join(f"{r[k]:>11.2f}" for k in KEYS))
    return r


print("== reproduce the nominee's shape, with and without the per-symbol cap ==")
show("nominee, cap OFF (the old EDA)", apply_cap=False)
show("nominee, cap ON  (what executes)", apply_cap=True)
print("== fixed basket, ranked by shock depth (cap ON) ==")
for b in (3, 5, 6, 8, 10):
    show(f"fixed basket = {b}", basket=b)
print("== fixed basket 5, breadth sensitivity ==")
for br in (1, 2, 3, 4, 5):
    show(f"basket 5, breadth>={br}", basket=5, breadth=br)
print("== fixed basket 5, flow spike sensitivity ==")
for f in (1.0, 1.5, 2.0, 2.5, 3.0):
    show(f"basket 5, ts>={f}", basket=5, flow_spike=f)
print("== fixed basket 5, shock z sensitivity ==")
for s in (-1.5, -1.75, -2.0, -2.25, -2.5):
    show(f"basket 5, z<={s}", basket=5, shock_z=s)
print("== fixed basket 5, hold sensitivity ==")
for h in (2, 3, 4):
    show(f"basket 5, hold={h}", basket=5, hold_bars=h)
