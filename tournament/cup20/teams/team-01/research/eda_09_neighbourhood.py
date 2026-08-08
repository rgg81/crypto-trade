"""Team-01 EDA step 9 -- what a one-at-a-time +/-20% neighbourhood would median to.

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
slippage, no exposure caps, no common risk unit, no risk policy, no charter floor.

The tournament scores the per-metric MEDIAN over a declared neighbourhood, not the nominee. This
step applies one fixed, pre-declared rule -- vary each coordinate one at a time by +/-20% of the
nominee's value -- to several candidate nominees, so the nominee is chosen for the plateau it sits
on rather than for its own reading. The step size is fixed at 20% for every coordinate before any
of these numbers were seen, precisely so it cannot be tuned; 20% is four times the charter's 5%
materiality minimum and is a real robustness test rather than a formality.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from eda_06_production import prepare
from eda_07_flatness import LADDERS, weights
from eda_08_sides import funding_panel

STEP = 0.20


def diagnostics(w, price, fund, folds, grid, warm):
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
    lw, sw = np.where(w > 0, w, 0.0)[live], np.where(w < 0, w, 0.0)[live]
    long_g = float((lw * price[live] - lw * fund[live]).sum())
    short_g = float((sw * price[live] - sw * fund[live]).sum())
    return {
        "ir": ir, "folds": per, "dw": dw,
        "posq": int((q > 0).sum()) / len(q), "long": long_g, "short": short_g,
    }


def points(formation, holding, threshold):
    yield "nominee", (formation, holding, threshold)
    for lo, hi in ((round(formation * (1 - STEP)), round(formation * (1 + STEP))),):
        yield "F-", (int(lo), holding, threshold)
        yield "F+", (int(hi), holding, threshold)
    yield "H-", (formation, max(1, round(holding * (1 - STEP))), threshold)
    yield "H+", (formation, round(holding * (1 + STEP)), threshold)
    yield "T-", (formation, holding, round(threshold * (1 - STEP), 4))
    yield "T+", (formation, holding, round(threshold * (1 + STEP), 4))


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    for ladder_name in ("3leg", "4leg"):
        ladder = LADDERS[ladder_name]
        for nominee in ((45, 6, 0.35), (45, 9, 0.35), (45, 12, 0.35), (48, 9, 0.35),
                        (54, 9, 0.35), (45, 9, 0.50)):
            rows = {}
            print(f"\n=== {ladder_name} nominee F={nominee[0]} H={nominee[1]} thr={nominee[2]}")
            print(f"{'point':>8} {'F':>4} {'H':>3} {'thr':>5} {'IR':>6} "
                  f"{'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} {'dW':>5} {'+Q':>5} "
                  f"{'Lg':>6} {'Sh':>6}")
            for label, (formation, holding, threshold) in points(*nominee):
                w, _ = weights(ret, elig, formation, holding, threshold, ladder)
                d = diagnostics(w, price, fund, folds, grid, 3 * formation + holding + 5)
                rows[label] = d
                print(f"{label:>8} {formation:>4} {holding:>3} {threshold:>5.2f} {d['ir']:>6.2f} "
                      + " ".join(f"{v:>6.2f}" for v in d["folds"])
                      + f" {d['dw']:>5.0f} {d['posq']:>5.2f} {d['long']:>6.2f} {d['short']:>6.2f}")
            med = lambda key: float(np.median([r[key] for r in rows.values()]))  # noqa: E731
            fold_med = [
                float(np.median([r["folds"][i] for r in rows.values()])) for i in range(4)
            ]
            print(f"{'MEDIAN':>8} {'':>4} {'':>3} {'':>5} {med('ir'):>6.2f} "
                  + " ".join(f"{v:>6.2f}" for v in fold_med)
                  + f" {med('dw'):>5.0f} {med('posq'):>5.2f} "
                  f"{med('long'):>6.2f} {med('short'):>6.2f}")
            worst = min(fold_med)
            npos = sum(1 for v in fold_med if v > 0)
            print(f"         median worst fold {worst:>6.2f}   median folds positive {npos}/4")


if __name__ == "__main__":
    main()
