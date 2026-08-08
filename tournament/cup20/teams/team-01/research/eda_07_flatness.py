"""Team-01 EDA step 7 -- is the formation-horizon surface a plateau or a spike?

Same scope declaration as ``eda_03_shape.py``: gross, cost-free signal diagnostics only.

Step 6 showed the formation anchor at 45 bars scoring well above its immediate neighbours at 36
and 54. Since the tournament scores the MEDIAN over a declared neighbourhood, a spike is worth
nothing; worse, a spike is what an overfitted parameter looks like. This step asks two things
before any trial is spent:

 1. On a fine grid, how wide is the region around the anchor, really?
 2. Does widening the horizon ladder (averaging more formation lengths per coin) flatten the
    surface without giving up the level? Mechanism: the coin's trend is one latent state; the
    lengths are noisy estimators of it, and averaging more of them should reduce estimator
    variance without changing the state being estimated. If it does not, the level at 45 was
    estimator luck.

It also measures the funding the book would actually pay, because a perpetual-futures trend book
that is net long most of the time pays the long side of funding, and that drag is real and is NOT
in the gross diagnostics above.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eda_03_shape import BARS_PER_YEAR
from eda_06_production import prepare
from panel import CONFIG, build_panel, rolling_std, rolling_sum

from crypto_trade.cup20.snapshot import load_snapshot

VOL_MULTIPLE = 2.0
LADDERS = {
    "3leg": (1 / 3, 1.0, 2.0),
    "4leg": (1 / 3, 2 / 3, 1.0, 2.0),
    "5leg": (1 / 4, 1 / 2, 1.0, 2.0, 3.0),
    "2leg": (1.0, 2.0),
    "1leg": (1.0,),
}


def weights(ret, eligible, formation, holding, threshold, ladder):
    vol_bars = max(3, int(round(VOL_MULTIPLE * formation)))
    vol = rolling_std(ret, vol_bars)
    finite = vol[np.isfinite(vol) & (vol > 0)]
    vol = np.maximum(vol, np.quantile(finite, 0.01))
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
    raw = np.where(eligible & np.isfinite(conv), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    return np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0), vol


def ir_of(w, fwd, folds, warm):
    r = np.nansum(np.where(np.isfinite(fwd), w * np.nan_to_num(fwd), 0.0), axis=1)
    live = np.zeros(len(r), dtype=bool)
    live[warm:] = True
    live &= np.abs(w).sum(axis=1) > 0
    live[-1] = False
    x = r[live]
    ir = x.mean() / x.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    fl = folds[live]
    per = [
        (x[fl == f].mean() / x[fl == f].std(ddof=1) * np.sqrt(BARS_PER_YEAR))
        if (fl == f).sum() > 30 else np.nan for f in range(4)
    ]
    dw = np.abs(np.diff(w, axis=0)).sum(axis=1)[live[1:]].mean() * BARS_PER_YEAR
    return ir, per, dw, live


def main() -> None:
    panel, ret, fwd = prepare()
    folds, elig = panel.fold_of_boundary(), panel.eligible

    print("Fine formation grid, H=6, threshold=0.35, by ladder width")
    print(f"{'ladder':>6} " + " ".join(f"{f:>6}" for f in (30, 36, 40, 45, 50, 54, 60, 72, 90, 110)))
    for name, ladder in LADDERS.items():
        row = []
        for formation in (30, 36, 40, 45, 50, 54, 60, 72, 90, 110):
            w, _ = weights(ret, elig, formation, 6, 0.35, ladder)
            ir, _, _, _ = ir_of(w, fwd, folds, 3 * formation + 12)
            row.append(ir)
        print(f"{name:>6} " + " ".join(f"{v:>6.2f}" for v in row)
              + f"   median {np.median(row):.2f}")

    print()
    print("Same, H=9")
    print(f"{'ladder':>6} " + " ".join(f"{f:>6}" for f in (30, 36, 40, 45, 50, 54, 60, 72, 90, 110)))
    for name, ladder in LADDERS.items():
        row = []
        for formation in (30, 36, 40, 45, 50, 54, 60, 72, 90, 110):
            w, _ = weights(ret, elig, formation, 9, 0.35, ladder)
            ir, _, _, _ = ir_of(w, fwd, folds, 3 * formation + 15)
            row.append(ir)
        print(f"{name:>6} " + " ".join(f"{v:>6.2f}" for v in row)
              + f"   median {np.median(row):.2f}")

    print()
    print("5leg detail (IR, folds, dW) at H in {3,6,9,12}, threshold 0.35")
    for formation in (45, 54, 63, 72, 90):
        for holding in (3, 6, 9, 12):
            w, _ = weights(ret, elig, formation, holding, 0.35, LADDERS["5leg"])
            ir, per, dw, _ = ir_of(w, fwd, folds, 3 * formation + holding + 5)
            print(f"  F={formation:>3} H={holding:>2} IR={ir:>5.2f} folds="
                  + " ".join(f"{v:>5.2f}" for v in per) + f" dW={dw:>5.0f}")

    print()
    print("Funding drag actually paid by the book (8h settlements, past-only rows).")
    snapshot = load_snapshot(CONFIG["data"]["is_root"])
    funding = snapshot.funding
    grid = panel.grid
    rate = (
        funding.pivot_table(index="funding_time", columns="symbol", values="funding_rate",
                            aggfunc="sum")
        .reindex(columns=panel.symbols)
    )
    # Sum every settlement inside (t, t+8h] onto boundary t; a long position pays a positive rate.
    edges = pd.DatetimeIndex(list(grid) + [grid[-1] + pd.Timedelta(hours=8)])
    slot = np.searchsorted(edges.to_numpy(), rate.index.to_numpy(), side="left") - 1
    fund = np.zeros((len(grid), len(panel.symbols)), dtype=float)
    values = np.nan_to_num(rate.to_numpy(dtype=float))
    keep = (slot >= 0) & (slot < len(grid))
    np.add.at(fund, slot[keep], values[keep])
    for formation, holding in ((45, 6), (54, 9), (72, 9), (90, 9)):
        w, _ = weights(ret, elig, formation, holding, 0.35, LADDERS["5leg"])
        _, _, _, live = ir_of(w, fwd, folds, 3 * formation + holding + 5)
        paid = -np.nansum(w * np.nan_to_num(fund), axis=1)  # positive = book pays
        print(f"  F={formation} H={holding}: mean net funding paid per bar "
              f"{paid[live].mean() * 1e4:>6.2f} bps -> {paid[live].mean() * BARS_PER_YEAR:.4f}/yr "
              f"at unit gross; mean net exposure {w.sum(axis=1)[live].mean():+.3f}")


if __name__ == "__main__":
    main()
