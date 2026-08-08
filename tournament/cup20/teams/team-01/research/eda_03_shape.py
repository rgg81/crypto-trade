"""Team-01 EDA step 3 -- signal shape: conviction, deadband, skip, holding overlap.

SCOPE DECLARATION, stated here and repeated in the research certificate. This file is NOT the
tournament scorer and does not reproduce it. It applies NO cost model, NO funding, NO exposure
caps, NO common risk unit, NO declared risk policy, and it computes NONE of the charter floors.
What it computes is a *gross signal information ratio in risk units*: the unit-gross weight vector
the signal implies, dotted with the coins' own open-to-open returns, summarised by mean/dispersion.
It is a property of the signal, used to choose which questions are worth a trial. Every number
team-01 reports, acts on as a gate, or nominates against comes from ``scripts/cup20_evaluate.py``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from panel import BARS_PER_DAY, build_panel, log_returns, rolling_std, rolling_sum

VOL_BARS = 90
BARS_PER_YEAR = 365 * BARS_PER_DAY


def _prepare():
    panel = build_panel()
    ret = log_returns(panel.signal_price)
    vol = rolling_std(ret, VOL_BARS)
    finite = vol[np.isfinite(vol) & (vol > 0)]
    vol = np.maximum(vol, np.quantile(finite, 0.01))
    fwd = np.full_like(panel.exec_open, np.nan)
    fwd[:-1] = panel.exec_open[1:] / panel.exec_open[:-1] - 1.0
    return panel, ret, vol, fwd


def conviction(ret, vol, lookback, ladder=(1.0,), skip=0, clip_at=None, deadband=0.0):
    """Per-coin own-history trend conviction in [-1, 1]; NaN where undefined."""
    parts, ok = [], None
    for multiple in ladder:
        length = max(3, int(round(lookback * multiple)))
        total = rolling_sum(ret, length + skip)
        if skip:
            total = total - rolling_sum(ret, skip)
        with np.errstate(invalid="ignore"):
            z = total / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        if clip_at is None:
            part = np.sign(z)
        else:
            part = np.clip(z / clip_at, -1.0, 1.0)
        if deadband > 0.0:
            part = np.where(np.abs(z) < deadband, 0.0, part)
        parts.append(np.where(good, part, 0.0))
    blended = np.mean(np.stack(parts), axis=0)
    return np.where(ok, blended, np.nan)


def book(conv, vol, eligible, hold=1):
    """Unit-gross weights from conviction / own vol, averaged over ``hold`` overlapping books."""
    raw = np.where(eligible & np.isfinite(conv), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    weights = np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0)
    if hold > 1:
        weights = (
            pd.DataFrame(weights).rolling(hold, min_periods=1).mean().to_numpy(dtype=float)
        )
        weights = np.where(eligible, weights, 0.0)
        gross = np.abs(weights).sum(axis=1, keepdims=True)
        weights = np.divide(weights, gross, out=np.zeros_like(weights), where=gross > 0)
    return weights


def report(name, weights, fwd, folds, grid, warm=270):
    r = np.nansum(np.where(np.isfinite(fwd), weights * np.nan_to_num(fwd), 0.0), axis=1)
    live = np.zeros(len(r), dtype=bool)
    live[warm:] = True
    live &= np.abs(weights).sum(axis=1) > 0
    live[-1] = False
    x = r[live]
    ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    folds_live = folds[live]
    per_fold = []
    for f in range(4):
        b = x[folds_live == f]
        per_fold.append(b.mean() / b.std(ddof=1) * np.sqrt(BARS_PER_YEAR) if b.size > 30 else np.nan)
    # gross one-way weight change per year, in units of gross book (a turnover proxy only)
    dw = np.abs(np.diff(weights, axis=0)).sum(axis=1)
    turn = dw[live[1:]].mean() * BARS_PER_YEAR
    net = np.abs(weights.sum(axis=1))[live].mean()
    ann_vol = x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    long_pnl = np.nansum(np.where(weights > 0, weights * np.nan_to_num(fwd), 0.0)[live])
    short_pnl = np.nansum(np.where(weights < 0, weights * np.nan_to_num(fwd), 0.0)[live])
    print(
        f"{name:<34} {ir:>6.2f} " + " ".join(f"{v:>6.2f}" for v in per_fold)
        + f" {ann_vol:>6.2f} {net:>5.2f} {turn:>7.1f} {long_pnl:>7.2f} {short_pnl:>7.2f}"
    )


HEAD = (
    f"{'spec':<34} {'IR':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} "
    f"{'vol':>6} {'|net|':>5} {'turn':>7} {'LongP':>7} {'ShrtP':>7}"
)


def main() -> None:
    panel, ret, vol, fwd = _prepare()
    folds = panel.fold_of_boundary()
    elig = panel.eligible
    print("GROSS signal information ratio at unit gross -- no costs, no caps, no risk unit.")
    print("Not a tournament metric. Design diagnostic only.")
    print()
    print("A. single formation horizon, sign conviction, hold=1")
    print(HEAD)
    for lookback in [21, 45, 63, 90, 135, 180, 270]:
        c = conviction(ret, vol, lookback)
        report(f"sign L={lookback}", book(c, vol, elig), fwd, folds, panel.grid)

    print()
    print("B. three-horizon ladder anchored on L (L/3, L, 2L), sign conviction")
    print(HEAD)
    for lookback in [45, 63, 90, 135, 180]:
        c = conviction(ret, vol, lookback, ladder=(1 / 3, 1.0, 2.0))
        report(f"ladder L={lookback}", book(c, vol, elig), fwd, folds, panel.grid)

    print()
    print("C. clipped conviction, ladder L=90")
    print(HEAD)
    for clip_at in [0.5, 0.75, 1.0, 1.5, 2.0]:
        c = conviction(ret, vol, 90, ladder=(1 / 3, 1.0, 2.0), clip_at=clip_at)
        report(f"ladder L=90 clip={clip_at}", book(c, vol, elig), fwd, folds, panel.grid)

    print()
    print("D. deadband on |z|, ladder L=90, sign conviction")
    print(HEAD)
    for band in [0.0, 0.15, 0.3, 0.5, 0.75]:
        c = conviction(ret, vol, 90, ladder=(1 / 3, 1.0, 2.0), deadband=band)
        report(f"ladder L=90 band={band}", book(c, vol, elig), fwd, folds, panel.grid)

    print()
    print("E. skip the most recent k bars of the formation window (ladder L=90)")
    print(HEAD)
    for skip in [0, 3, 6, 9, 15]:
        c = conviction(ret, vol, 90, ladder=(1 / 3, 1.0, 2.0), skip=skip)
        report(f"ladder L=90 skip={skip}", book(c, vol, elig), fwd, folds, panel.grid)

    print()
    print("F. holding overlap H (average of the last H implied books) -- phase-free cadence")
    print(HEAD)
    for hold in [1, 3, 9, 21, 45, 90]:
        c = conviction(ret, vol, 90, ladder=(1 / 3, 1.0, 2.0))
        report(f"ladder L=90 hold={hold}", book(c, vol, elig, hold=hold), fwd, folds, panel.grid)

    print()
    print("G. same, anchored on L=45 and L=180, hold=21")
    print(HEAD)
    for lookback in [45, 63, 90, 135, 180]:
        c = conviction(ret, vol, lookback, ladder=(1 / 3, 1.0, 2.0))
        report(f"ladder L={lookback} hold=21", book(c, vol, elig, hold=21), fwd, folds, panel.grid)


if __name__ == "__main__":
    main()
