"""Team-01 EDA step 2 -- where the slow-persistence edge lives, per fold, per side, per quarter.

NOT a scorer. The statistic reported is the *signal-weighted mean forward return per unit of own
risk*, ``E[ s(z) * r_fwd / sigma ]``, over eligible (boundary, coin) cells, plus its pooled
t-statistic and hit rate. That is an information-coefficient-class predictability measure on the
cells, not a portfolio: nothing here is compounded, no equity path is formed, no cost is charged,
no drawdown or Sharpe is computed. Every performance number team-01 acts on comes from
``scripts/cup20_evaluate.py``.

Step 1 found the rank IC of a volatility-standardised trend against the next-bar own return is
~0 while the SIGN of that trend carries a clearly positive mean return. That is the trend-follower
signature -- payoff by magnitude in the tail, not by frequency -- so this step measures the mean
directly and asks whether it survives fold by fold, side by side, and quarter by quarter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from panel import BARS_PER_DAY, build_panel, log_returns, rolling_std, rolling_sum

FORMATIONS = [21, 45, 63, 90, 135, 180, 270, 360]
VOL_BARS = 90
VOL_FLOOR_QUANTILE = 0.01


def summarise(name: str, contrib: np.ndarray, mask: np.ndarray, folds: np.ndarray,
              grid: pd.DatetimeIndex) -> None:
    vals = np.where(mask, contrib, np.nan)
    pooled = vals[np.isfinite(vals)]
    mean = pooled.mean() * 1e4
    tstat = pooled.mean() / pooled.std(ddof=1) * np.sqrt(pooled.size)
    per_fold = []
    for fold in range(4):
        rows = folds == fold
        block = vals[rows]
        block = block[np.isfinite(block)]
        per_fold.append(block.mean() * 1e4 if block.size else np.nan)
    print(
        f"{name:>26} {mean:>8.3f} {tstat:>7.2f} " + " ".join(f"{v:>8.3f}" for v in per_fold)
    )


def main() -> None:
    panel = build_panel()
    price, opens, elig = panel.signal_price, panel.exec_open, panel.eligible
    folds = panel.fold_of_boundary()

    ret = log_returns(price)
    vol = rolling_std(ret, VOL_BARS)
    finite_vol = vol[np.isfinite(vol) & (vol > 0)]
    floor = np.quantile(finite_vol, VOL_FLOOR_QUANTILE)
    print(f"own-vol per-bar: 1% quantile {floor:.5f}  median {np.median(finite_vol):.5f} "
          f"max {finite_vol.max():.5f}")
    vol = np.maximum(vol, floor)

    fwd = np.full_like(opens, np.nan)
    fwd[:-1] = opens[1:] / opens[:-1] - 1.0
    risk_fwd = fwd / vol  # forward return expressed in units of the coin's own risk

    print()
    print("E[ s(z) * r_fwd / sigma ] in bps of own risk per 8h bar, pooled t-stat, then by fold")
    print(f"{'spec':>26} {'mean':>8} {'t':>7} {'F1':>8} {'F2':>8} {'F3':>8} {'F4':>8}")
    print("-" * 78)

    base_mask = elig & np.isfinite(risk_fwd)
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore"):
            z = trend / (vol * np.sqrt(lookback))
        mask = base_mask & np.isfinite(z)
        summarise(f"sign L={lookback}", np.sign(z) * risk_fwd, mask, folds, panel.grid)

    print()
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore"):
            z = trend / (vol * np.sqrt(lookback))
        mask = base_mask & np.isfinite(z)
        clipped = np.clip(z / 1.0, -1.0, 1.0)
        summarise(f"clip(z/1.0) L={lookback}", clipped * risk_fwd, mask, folds, panel.grid)

    print()
    print("Long-signal cells and short-signal cells separately (sign spec):")
    print(f"{'spec':>26} {'mean':>8} {'t':>7} {'F1':>8} {'F2':>8} {'F3':>8} {'F4':>8}")
    print("-" * 78)
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore"):
            z = trend / (vol * np.sqrt(lookback))
        mask = base_mask & np.isfinite(z)
        summarise(f"LONG L={lookback}", np.sign(z) * risk_fwd, mask & (z > 0), folds, panel.grid)
        summarise(f"SHORT L={lookback}", np.sign(z) * risk_fwd, mask & (z < 0), folds, panel.grid)

    print()
    print("Multi-horizon blend: mean of sign(z) over a ladder anchored on L")
    print(f"{'spec':>26} {'mean':>8} {'t':>7} {'F1':>8} {'F2':>8} {'F3':>8} {'F4':>8}")
    print("-" * 78)
    for lookback in [45, 63, 90, 135, 180, 270]:
        ladder = [max(3, lookback // 3), lookback, lookback * 2]
        parts, ok = [], np.ones_like(elig, dtype=bool)
        for length in ladder:
            trend = rolling_sum(ret, length)
            with np.errstate(invalid="ignore"):
                zi = trend / (vol * np.sqrt(length))
            parts.append(np.sign(zi))
            ok &= np.isfinite(zi)
        blend = np.nanmean(np.stack(parts), axis=0)
        mask = base_mask & ok
        summarise(f"blend L={lookback} x{ladder}"[:26], blend * risk_fwd, mask, folds, panel.grid)

    print()
    print("Quarterly consistency of the pooled cell mean (sign spec), bps of own risk per bar:")
    quarters = pd.PeriodIndex(panel.grid.tz_convert("UTC").tz_localize(None), freq="Q")
    for lookback in [21, 45, 90, 180, 270]:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore"):
            z = trend / (vol * np.sqrt(lookback))
        mask = base_mask & np.isfinite(z)
        contrib = np.where(mask, np.sign(z) * risk_fwd, np.nan)
        rowmean = np.nanmean(contrib, axis=1)
        series = pd.Series(rowmean, index=quarters).groupby(level=0).mean() * 1e4
        positive = int((series > 0).sum())
        print(f"L={lookback:>4}  positive quarters {positive}/{len(series)}   "
              + " ".join(f"{v:+.0f}" for v in series.to_numpy()))


if __name__ == "__main__":
    main()
