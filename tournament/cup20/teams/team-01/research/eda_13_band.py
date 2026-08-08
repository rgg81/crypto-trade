"""Team-01 EDA step 13 -- can a no-trade band make the F3-positive specification tradeable?

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
caps, no risk unit, no risk policy, no charter floor.

Where this comes from. Trial #7 ran the four-rung ladder at HOLDING_BARS=9 and cleared every floor
except annualised turnover (27.80 against 25). Its worst fold was **+0.122** against the frozen
nominee's -0.092, and the charter's ranking score pays 30 points for the worst fold, so #7's own
vector would score G = 61.0 where the nominee scores 55.6 at the same trial count. Trial #8 bought
the turnover by slowing the signal, and paid for it exactly there.

The calibration from trials #6, #7 and #8 says the evaluator's turnover is

    turnover  =  executed gross  x  ( 24 + 1.394 x dW )

so at #7's dW of 89 roughly 40% of the turnover is NOT the strategy's own weight changes: it is the
evaluator rebalancing price drift, membership changes, the exposure-cap scale and the declared
volatility target's moving gross scale, all of which it does at every boundary that carries a target
row. **A boundary that carries no target row costs none of that.** So the hypothesis under test is
that the churn which forced the candidate off its F3-positive specification is mostly bookkeeping
rather than signal, and that suppressing rebalances the signal did not ask for removes it without
slowing anything down.

The band is event-driven on the signal, not on a clock: a target is emitted when the newly computed
unit-gross weight vector has moved more than REBALANCE_BAND in L1 from the last one actually
emitted, and otherwise the strategy returns None and the evaluator holds quantities. There is no
phase offset to sweep because there is no cadence -- the trigger is the signal's own accumulated
movement.

Faithfulness note: on a skipped boundary the evaluator holds QUANTITIES, so the realised weights
drift with relative price moves. This file reproduces that (``w <- w (1+r) / (1+r_p)``) rather than
holding the weight vector fixed, because the drift is exactly the thing the band is trading away
and pretending it does not happen would flatter the result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from eda_06_production import prepare
from eda_08_sides import funding_panel
from panel import rolling_std, rolling_sum

LADDER_4 = (1 / 3, 2 / 3, 1.0, 2.0)
VOL_FLOOR = 1e-4
GROSS = 0.19          # executed gross fraction measured on trials #7 and #8
DRIFT_OVERHEAD = 24.0  # per-rebalanced-boundary bookkeeping, from the #6/#7/#8 fit
DW_AMPLIFY = 1.394


def target_book(ret, eligible, formation, holding, threshold, ladder=LADDER_4):
    """The unit-gross book the signal asks for at every boundary, before any band."""
    window = max(3, int(round(2.0 * formation)))
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


def apply_band(asked, eligible, price, band):
    """Held book under a no-trade band; positions drift on skipped boundaries.

    Returns the realised weight panel, a boolean of which boundaries emitted a target, and the
    annualised sum of absolute weight change actually executed.
    """
    rows, cols = asked.shape
    held = np.zeros_like(asked)
    emitted = np.zeros(rows, dtype=bool)
    executed = np.zeros(rows)
    current = np.zeros(cols)
    for row in range(rows):
        want = asked[row]
        if row > 0:
            # positions carried from the previous boundary drift with relative price moves
            grown = current * (1.0 + np.nan_to_num(price[row - 1]))
            total = np.abs(grown).sum()
            current = grown / total if total > 0 else grown
            current = np.where(eligible[row], current, 0.0)  # membership exits are mandatory
        if np.abs(want).sum() <= 0:
            executed[row] = np.abs(current).sum()
            current = np.zeros(cols)
            held[row] = current
            continue
        if float(np.abs(want - current).sum()) > band:
            executed[row] = float(np.abs(want - current).sum())
            current = want.copy()
            emitted[row] = True
        held[row] = current
    return held, emitted, executed


def diagnose(name, held, emitted, executed, price, fund, folds, grid, warm):
    total = np.nansum(held * price - held * fund, axis=1)
    live = np.zeros(len(total), dtype=bool)
    live[warm:] = True
    live &= np.abs(held).sum(axis=1) > 0
    live[-1] = False
    x = total[live]
    ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    fl = folds[live]
    per = [
        (x[fl == f].mean() / x[fl == f].std(ddof=1) * np.sqrt(BARS_PER_YEAR))
        if (fl == f).sum() > 30 else np.nan for f in range(4)
    ]
    dw = executed[live].mean() * BARS_PER_YEAR
    rate = emitted[live].mean()
    q = pd.Series(
        x, index=pd.PeriodIndex(grid[live].tz_convert("UTC").tz_localize(None), freq="Q")
    ).groupby(level=0).sum()
    short = float(np.nansum(np.where(held < 0, held * price - held * fund, 0.0)[live]))
    predicted = GROSS * (DRIFT_OVERHEAD * rate + DW_AMPLIFY * dw)
    print(
        f"{name:<28} {ir:>6.2f} " + " ".join(f"{v:>6.2f}" for v in per)
        + f" {dw:>6.0f} {rate:>6.2f} {predicted:>7.1f} "
        f"{int((q > 0).sum()):>2}/{len(q):<3} {short:>6.2f}"
    )


HEAD = (
    f"{'spec':<28} {'IR':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} "
    f"{'dW':>6} {'rate':>6} {'turn*':>7} {'+Q':>6} {'Shrt':>6}"
)


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)
    price = np.nan_to_num(fwd)

    print("Four-rung ladder (F/3, 2F/3, F, 2F) -- the trial #7 signal -- under a no-trade band.")
    print("rate = fraction of boundaries that emit a target; turn* = predicted evaluator turnover.")
    print("Floor is 25 and the neighbourhood MEDIAN is what is floored, so target turn* <= 22.")
    print(HEAD)
    print("-" * len(HEAD))
    for holding in (9, 12):
        for band in (0.0, 0.03, 0.05, 0.08, 0.12, 0.16, 0.24):
            asked = target_book(ret, elig, 45, holding, 0.35)
            held, emitted, executed = apply_band(asked, elig, price, band)
            diagnose(
                f"F=45 H={holding} band={band}", held, emitted, executed,
                price, fund, folds, grid, 3 * 45 + holding + 5,
            )
        print()

    print("Sensitivity of the winning region to FORMATION_BARS and TREND_THRESHOLD")
    print(HEAD)
    print("-" * len(HEAD))
    for formation, holding, threshold, band in (
        (36, 9, 0.35, 0.08), (45, 9, 0.35, 0.08), (54, 9, 0.35, 0.08),
        (45, 7, 0.35, 0.08), (45, 11, 0.35, 0.08),
        (45, 9, 0.28, 0.08), (45, 9, 0.42, 0.08),
        (45, 9, 0.35, 0.064), (45, 9, 0.35, 0.096),
    ):
        asked = target_book(ret, elig, formation, holding, threshold)
        held, emitted, executed = apply_band(asked, elig, price, band)
        diagnose(
            f"F={formation} H={holding} t={threshold} b={band}", held, emitted, executed,
            price, fund, folds, grid, 3 * formation + holding + 5,
        )


if __name__ == "__main__":
    main()
