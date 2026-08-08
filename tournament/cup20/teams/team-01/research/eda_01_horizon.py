"""Team-01 EDA step 1 -- does slow own-price persistence exist, and over what horizon?

NOT a scorer: this reports information coefficients, hit rates and sign-flip rates only. No equity
curve, no Sharpe, no drawdown, no cost model.

Question posed before the numbers: for a per-coin, own-history trend measured over L 8h bars and
standardised by that coin's own realised volatility, is the rank correlation with the coin's own
next-bar open-to-open return positive, and is it positive in every one of the four charter folds?
A mechanism that only exists in the 2020-21 bull is a regime exposure, not persistence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from panel import BARS_PER_DAY, build_panel, log_returns, pearson, rolling_std, rolling_sum, spearman

FORMATIONS = [21, 45, 63, 90, 135, 180, 270, 360]  # 8h bars -> 7 .. 120 days
VOL_BARS = 90  # 30 days of 8h bars


def main() -> None:
    panel = build_panel()
    price = panel.signal_price
    opens = panel.exec_open
    elig = panel.eligible
    folds = panel.fold_of_boundary()

    ret = log_returns(price)
    vol = rolling_std(ret, VOL_BARS)  # per-bar sigma from own history only

    # What the book earns from a decision at t held one bar: O[t+1]/O[t] - 1.
    fwd = np.full_like(opens, np.nan)
    fwd[:-1] = opens[1:] / opens[:-1] - 1.0

    print(f"boundaries {len(panel.grid)}  symbols {len(panel.symbols)}")
    print(f"eligible cells {int(elig.sum())}")
    ann = np.nanmedian(vol[elig]) * np.sqrt(365 * BARS_PER_DAY)
    print(f"median annualised own-vol of eligible cells: {ann:.3f}")
    print()

    header = (
        f"{'L(bars)':>8} {'days':>5} {'IC_s':>7} {'IC_p':>7} {'hit':>6} "
        f"{'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6} {'flips/yr':>9} {'|s|mean':>8}"
    )
    print("z = log(P[t]/P[t-L]) / (sigma * sqrt(L));  target = own next-bar open-to-open return")
    print(header)
    print("-" * len(header))
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore", divide="ignore"):
            z = trend / (vol * np.sqrt(lookback))
        # Restrict to cells the runner would actually let us trade.
        mask = elig & np.isfinite(z) & np.isfinite(fwd)
        zz = np.where(mask, z, np.nan)
        ff = np.where(mask, fwd, np.nan)
        ic_s = spearman(zz.ravel(), ff.ravel())
        ic_p = pearson(zz.ravel(), ff.ravel())
        same = np.sign(zz) == np.sign(ff)
        hit = float(np.nanmean(np.where(mask, same, np.nan)))
        per_fold = []
        for fold in range(4):
            rows = folds == fold
            per_fold.append(spearman(zz[rows].ravel(), ff[rows].ravel()))
        # Sign-flip rate per eligible coin-year: a direct turnover proxy.
        sign = np.sign(zz)
        flip = (sign[1:] * sign[:-1]) < 0
        both = mask[1:] & mask[:-1]
        flips = flip[both].mean() * 365 * BARS_PER_DAY
        mean_abs = float(np.nanmean(np.abs(zz)))
        print(
            f"{lookback:>8} {lookback / BARS_PER_DAY:>5.0f} {ic_s:>7.4f} {ic_p:>7.4f} "
            f"{hit:>6.3f} " + " ".join(f"{v:>6.3f}" for v in per_fold)
            + f" {flips:>9.2f} {mean_abs:>8.3f}"
        )

    print()
    print("Same measurement, target = next-bar return divided by own sigma (what a risk-parity")
    print("book actually earns per unit of risk):")
    print(header)
    print("-" * len(header))
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        with np.errstate(invalid="ignore", divide="ignore"):
            z = trend / (vol * np.sqrt(lookback))
            scaled_fwd = fwd / vol
        mask = elig & np.isfinite(z) & np.isfinite(scaled_fwd)
        zz = np.where(mask, z, np.nan)
        ff = np.where(mask, scaled_fwd, np.nan)
        ic_s = spearman(zz.ravel(), ff.ravel())
        ic_p = pearson(zz.ravel(), ff.ravel())
        same = np.sign(zz) == np.sign(ff)
        hit = float(np.nanmean(np.where(mask, same, np.nan)))
        per_fold = [spearman(zz[folds == f].ravel(), ff[folds == f].ravel()) for f in range(4)]
        sign = np.sign(zz)
        flip = (sign[1:] * sign[:-1]) < 0
        both = mask[1:] & mask[:-1]
        flips = flip[both].mean() * 365 * BARS_PER_DAY
        print(
            f"{lookback:>8} {lookback / BARS_PER_DAY:>5.0f} {ic_s:>7.4f} {ic_p:>7.4f} "
            f"{hit:>6.3f} " + " ".join(f"{v:>6.3f}" for v in per_fold)
            + f" {flips:>9.2f} {'':>8}"
        )

    print()
    print("Raw sign-only control (no volatility standardisation): sign(log P[t]/P[t-L])")
    print(f"{'L(bars)':>8} {'hit':>6} {'F1':>6} {'F2':>6} {'F3':>6} {'F4':>6}")
    for lookback in FORMATIONS:
        trend = rolling_sum(ret, lookback)
        mask = elig & np.isfinite(trend) & np.isfinite(fwd)
        s = np.where(mask, np.sign(trend), np.nan)
        ff = np.where(mask, fwd, np.nan)
        hit = float(np.nanmean(np.where(mask, np.sign(s) == np.sign(ff), np.nan)))
        per_fold = []
        for fold in range(4):
            rows = folds == fold
            m = mask[rows]
            per_fold.append(float(np.nanmean(np.where(m, s[rows] * ff[rows], np.nan)) * 1e4))
        print(
            f"{lookback:>8} {hit:>6.3f} " + " ".join(f"{v:>6.2f}" for v in per_fold)
            + "   (fold cells are mean signed bps per bar)"
        )


if __name__ == "__main__":
    main()
