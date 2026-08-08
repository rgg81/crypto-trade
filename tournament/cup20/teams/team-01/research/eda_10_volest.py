"""Team-01 EDA step 10 -- does a range-based own-volatility estimator earn its place?

Same scope declaration as ``eda_03_shape.py``: gross diagnostics (price + funding), no fees, no
caps, no risk unit, no risk policy, no charter floor.

Own volatility enters the specification twice -- it standardises the trend into a t-statistic and
it sizes the position -- so its estimator error enters the book twice. The close-to-close estimator
throws away the high and the low of every 8h bar; the Parkinson range estimator uses them and has
several times lower variance for the same window. Both are per-coin own-history transforms, so
neither leaves the lane. Question posed before the numbers: does the lower-variance estimator move
the neighbourhood median, or is the specification insensitive to it?
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from eda_08_sides import funding_panel
from eda_09_neighbourhood import diagnostics, points
from panel import CONFIG, build_panel, log_returns, rolling_sum

from crypto_trade.cup20.config import IS_END
from crypto_trade.cup20.runner import decision_grid
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start

LADDER = (1 / 3, 2 / 3, 1.0, 2.0)
VOL_FLOOR = 1e-4


def range_panels():
    snapshot = load_snapshot(CONFIG["data"]["is_root"])
    bars = snapshot.bars
    membership = snapshot.membership
    is_start = resolve_is_start(membership, target_size=20)
    grid = pd.DatetimeIndex(decision_grid(is_start, IS_END, interval_hours=8))
    high = bars.pivot(index="open_time", columns="symbol", values="high").sort_index()
    low = bars.pivot(index="open_time", columns="symbol", values="low").sort_index()
    symbols = sorted(high.columns)
    return (
        high[symbols].shift(1).reindex(grid).to_numpy(dtype=float),
        low[symbols].shift(1).reindex(grid).to_numpy(dtype=float),
    )


def volatility(kind, ret, high, low, window):
    if kind == "close":
        return pd.DataFrame(ret).rolling(window, min_periods=window).std(ddof=1).to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        squared = np.log(high / low) ** 2 / (4.0 * math.log(2.0))
    park = pd.DataFrame(squared).rolling(window, min_periods=window).mean().to_numpy(float)
    park = np.sqrt(park)
    if kind == "parkinson":
        return park
    close = pd.DataFrame(ret).rolling(window, min_periods=window).std(ddof=1).to_numpy(float)
    return 0.5 * (park + close)


def build(kind, ret, high, low, eligible, formation, holding, threshold):
    window = max(3, int(round(2 * formation)))
    vol = volatility(kind, ret, high, low, window)
    vol = np.where(np.isfinite(vol) & (vol > VOL_FLOOR), vol, np.nan)
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
        conv = pd.DataFrame(conv).rolling(holding, min_periods=holding).mean().to_numpy(float)
    raw = np.where(eligible & np.isfinite(conv) & np.isfinite(vol), conv / vol, 0.0)
    gross = np.abs(raw).sum(axis=1, keepdims=True)
    return np.divide(raw, gross, out=np.zeros_like(raw), where=gross > 0)


def main() -> None:
    panel = build_panel()
    ret = log_returns(panel.signal_price)
    high, low = range_panels()
    fwd = np.full_like(panel.exec_open, np.nan)
    fwd[:-1] = panel.exec_open[1:] / panel.exec_open[:-1] - 1.0
    price = np.nan_to_num(fwd)
    folds, elig, grid = panel.fold_of_boundary(), panel.eligible, panel.grid
    fund = funding_panel(grid, panel.symbols)

    for kind in ("close", "parkinson", "blend"):
        for nominee in ((45, 9, 0.35), (45, 6, 0.35), (54, 9, 0.35)):
            rows = {}
            for label, (formation, holding, threshold) in points(*nominee):
                w = build(kind, ret, high, low, elig, formation, holding, threshold)
                rows[label] = diagnostics(
                    w, price, fund, folds, grid, 3 * formation + holding + 5
                )
            med_ir = float(np.median([r["ir"] for r in rows.values()]))
            med_folds = [
                float(np.median([r["folds"][i] for r in rows.values()])) for i in range(4)
            ]
            med_dw = float(np.median([r["dw"] for r in rows.values()]))
            med_q = float(np.median([r["posq"] for r in rows.values()]))
            med_s = float(np.median([r["short"] for r in rows.values()]))
            print(
                f"{kind:>10} F={nominee[0]:>3} H={nominee[1]:>2} thr={nominee[2]:<5} "
                f"nominee IR {rows['nominee']['ir']:>5.2f}  MEDIAN IR {med_ir:>5.2f}  "
                f"folds " + " ".join(f"{v:>5.2f}" for v in med_folds)
                + f"  dW {med_dw:>4.0f}  +Q {med_q:>4.2f}  Short {med_s:>5.2f}"
            )
        print()


if __name__ == "__main__":
    main()
