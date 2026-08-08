"""Team-01 EDA step 6 -- the exact production formulation, and the plateau around it.

Same scope declaration as ``eda_03_shape.py``: gross, cost-free signal diagnostics only. No cost
model, no funding, no exposure caps, no common risk unit, no declared risk policy, no charter
floor. The nominee and the neighbourhood are chosen from this surface; every number that gates
anything comes from ``scripts/cup20_evaluate.py``.

Production form (per coin, own history only, stateless at every boundary):

    r          8h log returns of the coin's own closes visible at the boundary
    sigma      std(r, 2 * FORMATION_BARS)                    own realised volatility
    z_l        sum(r, l) / (sigma * sqrt(l))   for l in (FORMATION_BARS//3, FORMATION_BARS,
                                                          2*FORMATION_BARS)
    c_l        clip( sign(z_l) * max(|z_l| - TREND_THRESHOLD, 0), -1, +1 )
    c          mean of c_l over the three legs
    c_bar      mean of c over the last HOLDING_BARS boundaries       (phase-free holding horizon)
    w          c_bar / sigma, normalised to unit gross over the eligible set

Nothing in it compares one coin with another: every quantity above is a function of that coin's
own price history alone, and the only cross-coin operation is the unit-gross normalisation the
organiser performs anyway.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from panel import build_panel, log_returns, rolling_std, rolling_sum

LADDER = (1 / 3, 1.0, 2.0)
VOL_MULTIPLE = 2.0


def prepare():
    panel = build_panel()
    ret = log_returns(panel.signal_price)
    fwd = np.full_like(panel.exec_open, np.nan)
    fwd[:-1] = panel.exec_open[1:] / panel.exec_open[:-1] - 1.0
    return panel, ret, fwd


def production_weights(ret, eligible, formation, holding, threshold):
    vol_bars = max(3, int(round(VOL_MULTIPLE * formation)))
    vol = rolling_std(ret, vol_bars)
    finite = vol[np.isfinite(vol) & (vol > 0)]
    vol = np.maximum(vol, np.quantile(finite, 0.01))

    parts, ok = [], None
    for multiple in LADDER:
        length = max(3, int(round(formation * multiple)))
        with np.errstate(invalid="ignore"):
            z = rolling_sum(ret, length) / (vol * np.sqrt(length))
        good = np.isfinite(z)
        ok = good if ok is None else (ok & good)
        shrunk = np.sign(z) * np.maximum(np.abs(z) - threshold, 0.0)
        parts.append(np.where(good, np.clip(shrunk, -1.0, 1.0), 0.0))
    conv = np.where(ok, np.mean(np.stack(parts), axis=0), np.nan)
    if holding > 1:
        conv = (
            pd.DataFrame(conv).rolling(holding, min_periods=holding).mean().to_numpy(dtype=float)
        )
    raw = np.where(eligible & np.isfinite(conv), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    return np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0)


HEAD = (
    f"{'F(bars)':>7} {'H':>4} {'thr':>5} | {'IR':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} "
    f"{'vol':>5} {'dW':>5} {'e/dW':>5} {'Lng':>6} {'Shrt':>6} {'+Q':>6} {'act':>5} {'|net|':>5}"
)


def line(formation, holding, threshold, weights, fwd, folds, grid, warm=None):
    warm = warm or (2 * formation + holding + 5)
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
    long_p = np.nansum(np.where(weights > 0, weights * np.nan_to_num(fwd), 0.0)[live])
    short_p = np.nansum(np.where(weights < 0, weights * np.nan_to_num(fwd), 0.0)[live])
    q = pd.Series(x, index=pd.PeriodIndex(grid[live].tz_convert("UTC").tz_localize(None), freq="Q"))
    qs = q.groupby(level=0).sum()
    act = (np.abs(weights) > 1e-12).sum(axis=1)[live].mean()
    net = np.abs(weights.sum(axis=1))[live].mean()
    print(
        f"{formation:>7} {holding:>4} {threshold:>5.2f} | {ir:>6.2f} "
        + " ".join(f"{v:>6.2f}" for v in per)
        + f" {vol:>5.2f} {dw:>5.0f} {ir * vol / dw * 1e4:>5.0f} {long_p:>6.2f} {short_p:>6.2f}"
        f" {int((qs > 0).sum()):>2}/{len(qs):<3} {act:>5.1f} {net:>5.2f}"
    )


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    print("GROSS signal diagnostics only. Not tournament metrics. See module docstring.")
    print(HEAD)
    print("-" * len(HEAD))
    for formation in (30, 36, 45, 54, 63, 90):
        for holding in (3, 6, 9):
            for threshold in (0.20, 0.35, 0.50):
                w = production_weights(ret, elig, formation, holding, threshold)
                line(formation, holding, threshold, w, fwd, folds, grid)
        print()


if __name__ == "__main__":
    main()
