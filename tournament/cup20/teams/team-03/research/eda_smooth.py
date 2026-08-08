"""Turnover repair: overlapping-tranche smoothing of the gated book.

eda_mechanics.py showed the hard gate churns -- ~0.86 one-way turnover per daily rebalance at
unit gross, i.e. an average holding period near two days, which cannot clear either the 25x
annualised turnover floor or the 40 bps gross-edge-per-turnover floor once the common risk unit's
scalar is applied.

The repair is the standard overlapping-portfolio construction: the target weight is the average of
the gated position over the last SMOOTH_BARS bars, so at most 1/SMOOTH_BARS of the book can be
re-formed per bar and the effective holding period becomes SMOOTH_BARS. It also expresses the
mandate directly -- a name armed 25 of the last 30 bars deserves more size than one armed 5 of 30.

Also estimates the annualised standard deviation of the reference book's GROSS bar returns, which
is the input to the organiser's own risk scalar s = clamp(0.10 / sigma, 0.20, 3.0). Executed gross
-- and therefore executed turnover -- is roughly s x the unit-gross figures, so the floor cannot be
judged without it. No net returns, no costs, no equity curve, no Sharpe, no drawdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_book import FOLDS, fold_of  # noqa: E402
from panel import load_close_panel, load_membership_mask, rolling_stats  # noqa: E402

START = pd.Timestamp("2020-08-17", tz="UTC")
BARS_PER_YEAR = 365.0 * 3.0


def smoothed_book(
    close: pd.DataFrame,
    mask: pd.DataFrame,
    *,
    formation: int,
    floor: float | None,
    smooth: int,
    inverse_vol: bool,
) -> pd.DataFrame:
    stats = rolling_stats(close, formation)
    mom = stats["momentum"].where(mask)
    pers = stats["persistence"].where(mask)
    vol = stats["volatility"].where(mask)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    if floor is not None:
        sign = sign.where(pers >= floor - 1e-9)
    position = (sign / vol if inverse_vol else sign).fillna(0.0)
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(mask, 0.0)
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def simulate(book: pd.DataFrame, close: pd.DataFrame, *, every: int, phase: int) -> dict:
    index = book.index
    columns = book.columns
    step = np.log(close).diff().reindex(index=index, columns=columns).fillna(0.0)
    simple = np.expm1(step.to_numpy())
    targets = book.to_numpy()
    live = np.zeros(len(columns))
    turnover = 0.0
    fills = 0
    gross_pnl = 0.0
    long_pnl = 0.0
    short_pnl = 0.0
    bar_returns: list[float] = []
    per_fold = {name: 0.0 for name, _, _ in FOLDS}
    folds = fold_of(index).to_numpy()
    start = int(index.searchsorted(START))
    exposure = []
    names = []
    for i in range(start, len(index)):
        bar = simple[i]
        contribution = live * bar
        total = contribution.sum()
        gross_pnl += total
        long_pnl += contribution[live > 0].sum()
        short_pnl += contribution[live < 0].sum()
        bar_returns.append(total)
        if folds[i] in per_fold:
            per_fold[folds[i]] += total
        live = live * (1.0 + bar) / (1.0 + total)
        exposure.append(np.abs(live).sum())
        names.append(int((np.abs(live) > 1e-9).sum()))
        if (i % every) == (phase % every):
            delta = targets[i] - live
            turnover += np.abs(delta).sum()
            fills += int((np.abs(delta) > 1e-9).sum())
            live = targets[i].copy()
    years = (len(index) - start) / BARS_PER_YEAR
    sigma = float(np.std(bar_returns, ddof=1) * np.sqrt(BARS_PER_YEAR))
    scale = float(np.clip(0.10 / sigma, 0.20, 3.0)) if sigma > 0 else 1.0
    return {
        "turnover_unit": turnover / years,
        "turnover_executed": turnover / years * scale,
        "fills": fills,
        "edge_per_turn": 1e4 * gross_pnl / turnover if turnover > 0 else float("nan"),
        "gross": gross_pnl,
        "long": long_pnl,
        "short": short_pnl,
        "sigma": sigma,
        "scale": scale,
        "exposure": float(np.mean(exposure)),
        "names": float(np.mean(names)),
        **{f"fold_{k}": v for k, v in per_fold.items()},
    }


def report(label: str, r: dict) -> None:
    print(
        f"  {label:<40} turn {r['turnover_unit']:6.1f}x -> exec {r['turnover_executed']:5.1f}x  "
        f"edge/turn {r['edge_per_turn']:6.1f}  fills {r['fills']:6d}  sigma {r['sigma']:.2f} "
        f"s={r['scale']:.2f}  names {r['names']:4.1f}  gross {r['gross']:+5.2f} L {r['long']:+5.2f} "
        f"S {r['short']:+5.2f}  folds " + " ".join(f"{r[f'fold_{n}']:+5.2f}" for n, _, _ in FOLDS)
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    for smooth in (1, 15, 30, 45, 63):
        print(f"\n=== SMOOTH_BARS = {smooth} ({smooth * 8 / 24:.1f}d)")
        for every, phase in ((1, 0), (3, 1)):
            for formation, floor, inverse_vol in (
                (27, None, True),
                (27, 0.585, True),
                (27, 0.585, False),
                (45, 0.585, True),
                (21, 0.585, True),
            ):
                book = smoothed_book(
                    close,
                    mask,
                    formation=formation,
                    floor=floor,
                    smooth=smooth,
                    inverse_vol=inverse_vol,
                )
                gate = "ungated" if floor is None else f"floor{floor}"
                weight = "iv" if inverse_vol else "eq"
                report(
                    f"cad{every}p{phase} f{formation} {gate} {weight}",
                    simulate(book, close, every=every, phase=phase),
                )


if __name__ == "__main__":
    main()
