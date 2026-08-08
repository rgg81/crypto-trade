"""Mechanical properties of the emitted weight stream, plus per-sleeve gross edge.

Feasibility screening only, so a trial is never spent on a design that cannot clear a shape floor:

  * annualised one-way turnover of the weight stream (floor: <= 25x equity at 1x cost)
  * executed fill count (floor: >= 500 over the window)
  * gross edge per unit one-way turnover (floor: >= 40 bps)
  * long-sleeve and short-sleeve GROSS edge separately (floor: each > 0)

Positions are held between rebalances exactly as the evaluator holds quantities on a ``None``
row, so weights drift with relative price. No costs, no funding, no equity curve, no Sharpe and
no drawdown are computed anywhere here -- those come only from scripts/cup20_evaluate.py.
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
DAYS_PER_YEAR = 365.0


def target_book(
    close: pd.DataFrame,
    mask: pd.DataFrame,
    *,
    formation: int,
    floor: float | None,
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
    weight = sign / vol if inverse_vol else sign
    weight = weight.fillna(0.0)
    gross = weight.abs().sum(axis=1)
    return weight.div(gross.where(gross > 0, 1.0), axis=0)


def simulate(
    book: pd.DataFrame,
    close: pd.DataFrame,
    *,
    every: int,
    phase: int,
) -> dict[str, float]:
    """Hold quantities between rebalances; report turnover, fills and gross edge only."""
    index = book.index
    columns = book.columns
    step = np.log(close).diff().reindex(index=index, columns=columns).fillna(0.0)
    simple = np.expm1(step.to_numpy())
    targets = book.to_numpy()
    live = np.zeros(len(columns))
    total_turnover = 0.0
    fills = 0
    gross_pnl = 0.0
    long_pnl = 0.0
    short_pnl = 0.0
    per_fold_gross: dict[str, float] = {name: 0.0 for name, _, _ in FOLDS}
    folds = fold_of(index).to_numpy()
    start_position = int(index.searchsorted(START))
    exposure_sum = 0.0
    exposure_n = 0
    for i in range(start_position, len(index)):
        # mark the carried book to the bar that just closed
        bar = simple[i]
        pnl_vector = live * bar
        gross_pnl += pnl_vector.sum()
        long_pnl += pnl_vector[live > 0].sum()
        short_pnl += pnl_vector[live < 0].sum()
        if folds[i] in per_fold_gross:
            per_fold_gross[folds[i]] += pnl_vector.sum()
        equity_growth = 1.0 + pnl_vector.sum()
        live = live * (1.0 + bar) / equity_growth
        exposure_sum += np.abs(live).sum()
        exposure_n += 1
        if (i % every) == (phase % every):
            desired = targets[i]
            delta = desired - live
            traded = np.abs(delta) > 1e-9
            total_turnover += np.abs(delta).sum()
            fills += int(traded.sum())
            live = desired.copy()
    years = (len(index) - start_position) / (24 / 8) / DAYS_PER_YEAR
    return {
        "annualised_turnover": total_turnover / years,
        "fills": fills,
        "gross_pnl": gross_pnl,
        "gross_edge_bps_per_turnover": (
            1e4 * gross_pnl / total_turnover if total_turnover > 0 else float("nan")
        ),
        "long_gross": long_pnl,
        "short_gross": short_pnl,
        "mean_gross_exposure": exposure_sum / max(exposure_n, 1),
        **{f"fold_{k}": v for k, v in per_fold_gross.items()},
    }


def report(label: str, result: dict[str, float]) -> None:
    print(
        f"  {label:<44} turnover {result['annualised_turnover']:6.2f}x  fills {result['fills']:6d}"
        f"  edge/turn {result['gross_edge_bps_per_turnover']:7.1f}bps  grossPnL "
        f"{result['gross_pnl']:+6.2f}  long {result['long_gross']:+6.2f}  short "
        f"{result['short_gross']:+6.2f}  expo {result['mean_gross_exposure']:.2f}  folds "
        + " ".join(f"{result[f'fold_{n}']:+5.2f}" for n, _, _ in FOLDS)
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)

    configurations = [
        ("controls off (ungated, equal wt)", 27, None, False),
        ("gate only (equal wt)", 27, 0.585, False),
        ("inverse-vol only (ungated)", 27, None, True),
        ("gate + inverse-vol  f=27", 27, 0.585, True),
        ("gate + inverse-vol  f=21", 21, 0.585, True),
        ("gate + inverse-vol  f=33", 33, 0.585, True),
        ("gate + inverse-vol  f=45", 45, 0.585, True),
        ("gate + inverse-vol  floor=0.55", 27, 0.55, True),
        ("gate + inverse-vol  floor=0.62", 27, 0.62, True),
    ]
    for every, phase in ((3, 1), (1, 0), (2, 1), (5, 1)):
        print(f"\n=== rebalance every {every} bars, phase {phase}")
        for label, formation, floor, inverse_vol in configurations:
            book = target_book(
                close, mask, formation=formation, floor=floor, inverse_vol=inverse_vol
            )
            report(label, simulate(book, close, every=every, phase=phase))


if __name__ == "__main__":
    main()
