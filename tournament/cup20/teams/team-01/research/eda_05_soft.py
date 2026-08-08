"""Team-01 EDA step 5 -- soft-thresholded trend conviction, and the churn it costs.

Same scope declaration as ``eda_03_shape.py``: gross, cost-free signal diagnostics only.

Hypothesis under test. Two distinct things happen near ``z = 0``. A HARD sign flips the whole
position for an arbitrarily small change in the underlying trend, which is churn carrying no
information. A CHOP regime -- the post-FTX fold F3 is the clearest example in this window -- is a
stretch where |z| stays small for every coin at once, and a book that insists on a full-size
directional position through it is manufacturing losses out of noise. A soft threshold
``max(|z| - THRESHOLD, 0)`` addresses both with one primitive: it is continuous at the crossing,
so the churn goes away, and it is exactly zero while the trend is insignificant, so the book steps
aside in chop instead of guessing.

``edge/dW`` is the gross annual return at unit gross divided by the annualised absolute weight
change -- both are properties of the signal and its own weight sequence, no cost model is applied.
It is reported because a specification whose churn is structurally untradeable should not consume
a trial.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR, book
from panel import build_panel, log_returns, rolling_std, rolling_sum

LADDER = (1 / 3, 1.0, 2.0)


def prepare(vol_bars=90):
    panel = build_panel()
    ret = log_returns(panel.signal_price)
    vol = rolling_std(ret, vol_bars)
    finite = vol[np.isfinite(vol) & (vol > 0)]
    vol = np.maximum(vol, np.quantile(finite, 0.01))
    fwd = np.full_like(panel.exec_open, np.nan)
    fwd[:-1] = panel.exec_open[1:] / panel.exec_open[:-1] - 1.0
    return panel, ret, vol, fwd


def soft(ret, vol, anchor, threshold, scale, ladder=LADDER):
    parts, ok = [], None
    for multiple in ladder:
        length = max(3, int(round(anchor * multiple)))
        with np.errstate(invalid="ignore"):
            z = rolling_sum(ret, length) / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        shrunk = np.sign(z) * np.maximum(np.abs(z) - threshold, 0.0)
        parts.append(np.where(good, np.clip(shrunk / scale, -1.0, 1.0), 0.0))
    return np.where(ok, np.mean(np.stack(parts), axis=0), np.nan)


HEAD = (
    f"{'spec':<30} {'IR':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} {'vol':>5} "
    f"{'dW':>6} {'e/dW':>6} {'Shrt':>6} {'+Q':>5} {'act':>5}"
)


def line(name, weights, fwd, folds, grid, warm=270):
    r = np.nansum(np.where(np.isfinite(fwd), weights * np.nan_to_num(fwd), 0.0), axis=1)
    live = np.zeros(len(r), dtype=bool)
    live[warm:] = True
    live &= np.abs(weights).sum(axis=1) > 0
    live[-1] = False
    x = r[live]
    vol = x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    fl = folds[live]
    per = [
        (x[fl == f].mean() / x[fl == f].std(ddof=1) * np.sqrt(BARS_PER_YEAR))
        if (fl == f).sum() > 30 else np.nan
        for f in range(4)
    ]
    dw = np.abs(np.diff(weights, axis=0)).sum(axis=1)[live[1:]].mean() * BARS_PER_YEAR
    edge = ir * vol
    short = np.nansum(np.where(weights < 0, weights * np.nan_to_num(fwd), 0.0)[live])
    q = pd.Series(x, index=pd.PeriodIndex(grid[live].tz_convert("UTC").tz_localize(None), freq="Q"))
    qsum = q.groupby(level=0).sum()
    active = (np.abs(weights) > 1e-12).sum(axis=1)[live].mean()
    print(
        f"{name:<30} {ir:>6.2f} " + " ".join(f"{v:>6.2f}" for v in per)
        + f" {vol:>5.2f} {dw:>6.0f} {edge / dw * 1e4:>6.0f} {short:>6.2f} "
        f"{int((qsum > 0).sum())}/{len(qsum)} {active:>5.1f}"
    )


def main() -> None:
    panel, ret, vol, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    print("Gross signal diagnostics only -- no costs, no caps, no risk unit, no floor computed.")
    print("dW = annualised sum|dw| at unit gross; e/dW = gross edge in bps per unit of that churn.")
    print("+Q = quarters with positive gross sum; act = mean number of non-zero positions.")
    for anchor in (45, 63, 90, 135):
        print()
        print(HEAD)
        for threshold in (0.0, 0.2, 0.35, 0.5, 0.75):
            conv = soft(ret, vol, anchor, threshold, 1.0)
            for hold in (1, 3, 6, 9):
                line(
                    f"L={anchor} thr={threshold} h={hold}",
                    book(conv, vol, elig, hold=hold), fwd, folds, grid,
                )


if __name__ == "__main__":
    main()
