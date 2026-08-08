"""Team-01 EDA step 14 -- the exhaustive free search for a candidate that beats the nominee.

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
caps, no risk unit, no risk policy, no charter floor. No trial is spent by this file.

Three thresholds, derived from the frozen nominee's scored result and fixed before this search ran.
A replacement has to clear all three simultaneously or it is not a replacement.

 1. ``dW <= 66``.  Turnover = executed gross x (24 + 1.394 dW), fitted on trials #6/#7/#8 and
    accurate to better than 2% on both anchors (#7 predicted 28.1 against 27.80 actual, #8
    predicted 19.4 against 19.52). At gross 0.19 the 25x floor needs dW <= 74, and the floor is
    applied to the neighbourhood MEDIAN, so 66 leaves margin for the points either side.
 2. ``IR >= 1.10``.  The EDA-to-evaluator offset measured on #7 and #8 is about +0.11 of Sharpe, so
    IR 1.10 maps to a scored Sharpe near 1.21. This is NOT a preference -- it is forced. The
    trial-adjusted confidence floor needs B >= 0.99091 at T=11 and B >= 0.99167 at T=12, and the
    measured B-to-Sharpe relation across six scored runs puts that at a net Sharpe of roughly 1.19.
    A slower, safer, lower-Sharpe candidate is not safer at all: it is disqualified.
 3. ``F3 >= -0.05``.  The nominee's scored worst fold is -0.092 and the ranking score pays 30
    points for it. The EDA-to-evaluator offset on fold F3 is about +0.13 (both #7 and #8), so
    -0.05 here maps to roughly +0.08 scored, which is where the improvement becomes worth the two
    trials a re-freeze costs.

The families searched: diluting the fast rung by adding slower rungs (the fast rung is what carries
fold F3 and it is also what carries the churn, so its WEIGHT in the ladder, not its presence, is the
axis), unequal rung weighting, and formation/holding/threshold combinations around each.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from eda_06_production import prepare
from eda_08_sides import funding_panel
from panel import rolling_std, rolling_sum

VOL_FLOOR = 1e-4
GROSS = 0.19
DW_MAX, IR_MIN, F3_MIN = 66.0, 1.10, -0.05

FAMILIES = {
    "4rung 1/3,2/3,1,2": ((1 / 3, 2 / 3, 1.0, 2.0), None),
    "5rung +3/2": ((1 / 3, 2 / 3, 1.0, 3 / 2, 2.0), None),
    "6rung +3/2,3": ((1 / 3, 2 / 3, 1.0, 3 / 2, 2.0, 3.0), None),
    "5rung 1/3,1,3/2,2,3": ((1 / 3, 1.0, 3 / 2, 2.0, 3.0), None),
    "4rung 1/3,1,3/2,2": ((1 / 3, 1.0, 3 / 2, 2.0), None),
    "2rung 1,2 (nominee)": ((1.0, 2.0), None),
    "fast-lite w=1/6": ((1 / 3, 1.0, 2.0), (1 / 6, 5 / 12, 5 / 12)),
    "fast-lite w=1/8": ((1 / 3, 1.0, 2.0), (1 / 8, 7 / 16, 7 / 16)),
    "fast-lite w=1/4": ((1 / 3, 1.0, 2.0), (1 / 4, 3 / 8, 3 / 8)),
    "fast-lite w=1/5 +3/2": ((1 / 3, 1.0, 3 / 2, 2.0), (0.20, 0.2667, 0.2667, 0.2667)),
}


def book(ret, eligible, formation, holding, threshold, ladder, weights=None):
    window = max(3, int(round(2.0 * formation)))
    vol = rolling_std(ret, window)
    vol = np.where(np.isfinite(vol) & (vol > VOL_FLOOR), vol, np.nan)
    if weights is None:
        weights = [1.0 / len(ladder)] * len(ladder)
    parts, ok = [], None
    for multiple, weight in zip(ladder, weights, strict=True):
        length = max(3, int(round(formation * multiple)))
        with np.errstate(invalid="ignore"):
            z = rolling_sum(ret, length) / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        shrunk = np.sign(z) * np.maximum(np.abs(z) - threshold, 0.0)
        parts.append(weight * np.where(good, np.clip(shrunk, -1.0, 1.0), 0.0))
    conv = np.where(ok, np.sum(np.stack(parts), axis=0), np.nan)
    if holding > 1:
        conv = pd.DataFrame(conv).rolling(holding, min_periods=holding).mean().to_numpy(float)
    raw = np.where(eligible & np.isfinite(conv) & np.isfinite(vol), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    return np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0)


def stats(w, price, fund, folds, grid, warm):
    total = np.nansum(w * price - w * fund, axis=1)
    live = np.zeros(len(total), dtype=bool)
    live[warm:] = True
    live &= np.abs(w).sum(axis=1) > 0
    live[-1] = False
    x = total[live]
    ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    fl = folds[live]
    per = [
        (x[fl == f].mean() / x[fl == f].std(ddof=1) * np.sqrt(BARS_PER_YEAR))
        if (fl == f).sum() > 30 else np.nan for f in range(4)
    ]
    dw = np.abs(np.diff(w, axis=0)).sum(axis=1)[live[1:]].mean() * BARS_PER_YEAR
    q = pd.Series(
        x, index=pd.PeriodIndex(grid[live].tz_convert("UTC").tz_localize(None), freq="Q")
    ).groupby(level=0).sum()
    short = float(np.nansum(np.where(w < 0, w * price - w * fund, 0.0)[live]))
    return dict(ir=ir, folds=per, dw=dw, posq=int((q > 0).sum()) / len(q), short=short)


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    print(f"Simultaneous thresholds: dW <= {DW_MAX:.0f}, IR >= {IR_MIN:.2f}, F3 >= {F3_MIN:+.2f}")
    print(f"{'family':<22} {'F':>3} {'H':>3} {'thr':>5} | {'IR':>6} {'F1':>6} {'F2':>6} "
          f"{'F3':>6} {'F4':>6} {'dW':>5} {'turn*':>6} {'+Q':>5} {'Shrt':>6}  verdict")
    print("-" * 116)
    survivors = []
    for name, (ladder, weights) in FAMILIES.items():
        for formation in (45, 54):
            for holding in (9, 12, 15, 18):
                w = book(ret, elig, formation, holding, 0.35, ladder, weights)
                s = stats(w, price, fund, folds, grid, 3 * formation + holding + 5)
                ok = s["dw"] <= DW_MAX and s["ir"] >= IR_MIN and s["folds"][2] >= F3_MIN
                verdict = "**CLEARS**" if ok else (
                    "dW" if s["dw"] > DW_MAX else "IR" if s["ir"] < IR_MIN else "F3"
                )
                if ok:
                    survivors.append((name, formation, holding, s))
                print(
                    f"{name:<22} {formation:>3} {holding:>3} {0.35:>5.2f} | {s['ir']:>6.2f} "
                    + " ".join(f"{v:>6.2f}" for v in s["folds"])
                    + f" {s['dw']:>5.0f} {GROSS * (24 + 1.394 * s['dw']):>6.1f} "
                    f"{s['posq']:>5.2f} {s['short']:>6.2f}  {verdict}"
                )
        print()
    print(f"SURVIVORS clearing all three thresholds: {len(survivors)}")
    for name, formation, holding, s in survivors:
        print(f"  {name} F={formation} H={holding}: IR {s['ir']:.2f} F3 {s['folds'][2]:+.2f} "
              f"dW {s['dw']:.0f}")


if __name__ == "__main__":
    main()
