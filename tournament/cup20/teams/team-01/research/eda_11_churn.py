"""Team-01 EDA step 11 -- cut churn structurally, after trial #7 failed the turnover floor by 11%.

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
caps, no risk unit, no risk policy, no charter floor.

What trial #7 established, and it is a calibration this EDA could not have produced on its own:
the evaluator's realised one-way turnover is about 1.6x this file's ``dW`` proxy at the same gross
exposure. ``dW`` counts only the change in the target weight vector; the evaluator additionally
rebalances price drift, membership changes and the risk policy's own moving gross scale, and those
terms are together roughly 40% of the total. Trial #7 measured 27.80x against a 25x floor at
``dW`` = 89, so the specification needs ``dW`` at or below about 68 to clear the floor with margin,
and the neighbourhood MEDIAN is what is floored, so the whole declared neighbourhood has to clear
it, not just the nominee.

Two structural levers, tested here against the same +/-20% one-at-a-time neighbourhood rule fixed
in step 9. Neither is a change of mechanism: both make the same own-price trend slower.

 1. Slow the ladder. The fastest rung at FORMATION_BARS/3 is five days at the anchor, and a rung
    that fast dominates the weight changes while contributing the least to a lane whose thesis is
    persistence over weeks.
 2. Lengthen the holding overlap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_06_production import prepare
from eda_08_sides import funding_panel
from eda_09_neighbourhood import diagnostics, points
from panel import rolling_std, rolling_sum

LADDERS = {
    "1/3,2/3,1,2": (1 / 3, 2 / 3, 1.0, 2.0),
    "2/3,1,4/3,2": (2 / 3, 1.0, 4 / 3, 2.0),
    "1/2,1,3/2,2": (1 / 2, 1.0, 3 / 2, 2.0),
    "2/3,1,2": (2 / 3, 1.0, 2.0),
    "1,3/2,2,3": (1.0, 3 / 2, 2.0, 3.0),
    "1,2": (1.0, 2.0),
}
VOL_FLOOR = 1e-4


def weights(ret, eligible, formation, holding, threshold, ladder, vol_multiple=2.0):
    window = max(3, int(round(vol_multiple * formation)))
    vol = rolling_std(ret, window)
    vol = np.where(np.isfinite(vol) & (vol > VOL_FLOOR), vol, np.nan)
    parts, ok = [], None
    for multiple in ladder:
        length = max(3, int(round(formation * multiple)))
        with np.errstate(invalid="ignore"):
            z = rolling_sum(ret, length) / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        shrunk = np.sign(z) * np.maximum(np.abs(z) - threshold, 0.0)
        parts.append(np.where(good, np.clip(shrunk, -1.0, 1.0), 0.0))
    conv = np.where(ok, np.mean(np.stack(parts), axis=0), np.nan)
    if holding > 1:
        conv = pd.DataFrame(conv).rolling(holding, min_periods=holding).mean().to_numpy(float)
    raw = np.where(eligible & np.isfinite(conv) & np.isfinite(vol), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    return np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0)


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    print("Neighbourhood MEDIANS under the step-9 rule (each coordinate one at a time, +/-20%).")
    print("dW target <= 68 so the evaluator's ~1.6x realised turnover clears 25x with margin.")
    print(f"{'ladder':>12} {'F':>4} {'H':>3} {'thr':>5} | {'IRmed':>6} {'F1':>6} {'F2':>6} "
          f"{'F3':>6} {'F4':>6} {'dWmed':>6} {'dWmax':>6} {'+Qmed':>6} {'Shmed':>6} {'IRnom':>6}")
    for name, ladder in LADDERS.items():
        for formation, holding, threshold in (
            (45, 9, 0.35), (45, 12, 0.35), (45, 15, 0.35), (45, 18, 0.35),
            (54, 12, 0.35), (63, 12, 0.35), (63, 9, 0.35), (90, 9, 0.35),
        ):
            rows = {}
            for _label, (f, h, t) in points(formation, holding, threshold):
                w = weights(ret, elig, f, h, t, ladder)
                rows[_label] = diagnostics(
                    w, price, fund, folds, grid, int(3 * f + h + 5)
                )
            med = lambda k: float(np.median([r[k] for r in rows.values()]))  # noqa: E731
            fold_med = [float(np.median([r["folds"][i] for r in rows.values()])) for i in range(4)]
            print(
                f"{name:>12} {formation:>4} {holding:>3} {threshold:>5.2f} | "
                f"{med('ir'):>6.2f} " + " ".join(f"{v:>6.2f}" for v in fold_med)
                + f" {med('dw'):>6.0f} {max(r['dw'] for r in rows.values()):>6.0f} "
                f"{med('posq'):>6.2f} {med('short'):>6.2f} {rows['nominee']['ir']:>6.2f}"
            )
        print()


if __name__ == "__main__":
    main()
