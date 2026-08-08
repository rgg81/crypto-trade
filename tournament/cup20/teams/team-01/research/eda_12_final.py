"""Team-01 EDA step 12 -- the last design question: most edge per unit of churn.

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
caps, no risk unit, no risk policy, no charter floor.

Calibration taken from trials #6 and #7, which is the only reason this step can be posed
quantitatively at all:

    realised one-way turnover  ~=  executed gross  x  ( dW + 30 + 25 )

where ``dW`` is this file's target-weight-change proxy at unit gross, the +30 is the evaluator's
own rebalancing of price drift, membership changes and the exposure-cap scale, and the +25 is the
declared volatility target's gross scale moving from boundary to boundary. Trial #7 ran at an
executed gross of 0.193 and 27.80x turnover against a 25x floor, so the specification needs
``dW`` at or below about 59 for the neighbourhood MEDIAN to clear 25x with real margin.

The question is therefore not "which specification has the highest information ratio" -- step 11
already answered that, and the answer fails a hard floor -- but "which has the highest information
ratio among those that can be traded", with the fold-F3 profile as a second constraint because the
worst-fold floor at -0.25 is the other gate with no margin.
"""

from __future__ import annotations

import numpy as np

from eda_06_production import prepare
from eda_08_sides import funding_panel
from eda_09_neighbourhood import diagnostics, points
from eda_11_churn import weights

GROSS = 0.193
OVERHEAD = 55.0

LADDERS = {
    "1,2": (1.0, 2.0),
    "1,3/2,2": (1.0, 3 / 2, 2.0),
    "1,4/3,2": (1.0, 4 / 3, 2.0),
    "3/4,1,3/2,2": (3 / 4, 1.0, 3 / 2, 2.0),
    "1,3/2,2,5/2": (1.0, 3 / 2, 2.0, 5 / 2),
    "4/5,1,3/2,2": (4 / 5, 1.0, 3 / 2, 2.0),
}


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    print("Neighbourhood medians (step-9 rule). turn* = predicted evaluator turnover from the")
    print("trial #6/#7 calibration; the 25x floor applies to the median.")
    print(f"{'ladder':>12} {'F':>4} {'H':>3} {'thr':>5} | {'IRmed':>6} {'F1':>6} {'F2':>6} "
          f"{'F3':>6} {'F4':>6} {'dWmed':>6} {'turn*':>6} {'+Qmed':>6} {'Shmed':>6}")
    for name, ladder in LADDERS.items():
        for formation, holding, threshold in (
            (45, 12, 0.35), (45, 15, 0.35), (45, 18, 0.35),
            (50, 15, 0.35), (54, 15, 0.35), (45, 15, 0.50), (45, 15, 0.20),
        ):
            rows = {}
            for label, (f, h, t) in points(formation, holding, threshold):
                w = weights(ret, elig, f, h, t, ladder)
                rows[label] = diagnostics(w, price, fund, folds, grid, int(3 * f + h + 5))
            med = lambda k: float(np.median([r[k] for r in rows.values()]))  # noqa: E731
            fold_med = [float(np.median([r["folds"][i] for r in rows.values()])) for i in range(4)]
            dw = med("dw")
            print(
                f"{name:>12} {formation:>4} {holding:>3} {threshold:>5.2f} | "
                f"{med('ir'):>6.2f} " + " ".join(f"{v:>6.2f}" for v in fold_med)
                + f" {dw:>6.0f} {GROSS * (dw + OVERHEAD):>6.1f} "
                f"{med('posq'):>6.2f} {med('short'):>6.2f}"
            )
        print()


if __name__ == "__main__":
    main()
