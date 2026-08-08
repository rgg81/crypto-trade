"""Formation x smoothing surface for the gated book, with funding folded into the sleeves.

The short sleeve is the binding shape floor for a near-neutral trend book on a universe that rose
over the window, and price PnL alone understates it: perpetual funding is paid by longs to shorts
whenever it is positive, which it mostly is. The evaluator sums native per-event funding into the
holding interval, so a sleeve check that ignores funding is checking the wrong quantity.

Still descriptive: turnover, fill counts, gross edge per unit turnover, per-sleeve gross PnL, the
reference book's gross-return standard deviation (the input to the organiser's risk scalar) and
per-fold gross PnL. No net returns, no costs, no equity curve, no Sharpe, no drawdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_book import FOLDS, fold_of  # noqa: E402
from eda_smooth import BARS_PER_YEAR, START, smoothed_book  # noqa: E402
from panel import DATA_ROOT, load_close_panel, load_membership_mask  # noqa: E402


def funding_per_bar(index: pd.DatetimeIndex, columns: pd.Index) -> pd.DataFrame:
    """Funding settled inside each 8h bar, as a rate paid by a long position."""
    funding = pd.read_parquet(DATA_ROOT / "funding.parquet")
    funding["funding_time"] = pd.to_datetime(funding["funding_time"], utc=True)
    # Attribute each settlement to the bar whose (open, close] interval contains it.
    bucket = funding["funding_time"].dt.ceil("8h")
    grouped = funding.assign(bucket=bucket).groupby(["bucket", "symbol"])["funding_rate"].sum()
    frame = grouped.unstack("symbol")
    return frame.reindex(index=index, columns=columns).fillna(0.0)


def simulate(
    book: pd.DataFrame,
    close: pd.DataFrame,
    funding: pd.DataFrame,
    *,
    every: int,
    phase: int,
) -> dict:
    index = book.index
    columns = book.columns
    simple = np.expm1(np.log(close).diff().reindex(index=index, columns=columns).fillna(0.0)
                      .to_numpy())
    fund = funding.to_numpy()
    targets = book.to_numpy()
    live = np.zeros(len(columns))
    turnover = 0.0
    fills = 0
    price_long = price_short = fund_long = fund_short = 0.0
    bar_returns: list[float] = []
    per_fold = {name: 0.0 for name, _, _ in FOLDS}
    folds = fold_of(index).to_numpy()
    start = int(index.searchsorted(START))
    names: list[int] = []
    for i in range(start, len(index)):
        bar = simple[i]
        price = live * bar
        carry = -live * fund[i]
        total = price.sum() + carry.sum()
        price_long += price[live > 0].sum()
        price_short += price[live < 0].sum()
        fund_long += carry[live > 0].sum()
        fund_short += carry[live < 0].sum()
        bar_returns.append(total)
        if folds[i] in per_fold:
            per_fold[folds[i]] += total
        live = live * (1.0 + bar) / (1.0 + total)
        names.append(int((np.abs(live) > 1e-9).sum()))
        if (i % every) == (phase % every):
            delta = targets[i] - live
            turnover += np.abs(delta).sum()
            fills += int((np.abs(delta) > 1e-9).sum())
            live = targets[i].copy()
    years = (len(index) - start) / BARS_PER_YEAR
    sigma = float(np.std(bar_returns, ddof=1) * np.sqrt(BARS_PER_YEAR))
    scale = float(np.clip(0.10 / sigma, 0.20, 3.0)) if sigma > 0 else 1.0
    gross = price_long + price_short + fund_long + fund_short
    return {
        "turnover_exec": turnover / years * scale,
        "edge_per_turn": 1e4 * gross / turnover if turnover > 0 else float("nan"),
        "fills": fills,
        "sigma": sigma,
        "scale": scale,
        "vol_exec": sigma * scale,
        "names": float(np.mean(names)),
        "gross": gross,
        "long": price_long + fund_long,
        "short": price_short + fund_short,
        "fund_short": fund_short,
        **{f"fold_{k}": v for k, v in per_fold.items()},
    }


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)
    print(f"mean 8h funding rate paid by longs: {funding.replace(0.0, np.nan).stack().mean():.6f}")

    floor = float(sys.argv[1]) if len(sys.argv) > 1 else 0.585
    print(f"\ncadence 3 phase 1, inverse-vol, persistence floor {floor}")
    header = f"  {'formation':>9} {'smooth':>6} {'turn':>6} {'edge':>6} {'sigma':>6} {'vol':>5} " \
             f"{'names':>5} {'gross':>6} {'long':>6} {'short':>6} {'fundS':>6}   folds"
    print(header)
    for formation in (15, 21, 27, 33, 45):
        for smooth in (9, 18, 30, 45):
            book = smoothed_book(
                close, mask, formation=formation, floor=floor, smooth=smooth, inverse_vol=True
            )
            r = simulate(book, close, funding, every=3, phase=1)
            print(
                f"  {formation:>9} {smooth:>6} {r['turnover_exec']:6.1f} {r['edge_per_turn']:6.1f} "
                f"{r['sigma']:6.2f} {r['vol_exec']:5.2f} {r['names']:5.1f} {r['gross']:+6.2f} "
                f"{r['long']:+6.2f} {r['short']:+6.2f} {r['fund_short']:+6.2f}   "
                + " ".join(f"{r[f'fold_{n}']:+5.2f}" for n, _, _ in FOLDS)
            )
    print("\n  ungated reference (same smoothing grid)")
    for formation in (21, 27):
        for smooth in (9, 18, 30, 45):
            book = smoothed_book(
                close, mask, formation=formation, floor=None, smooth=smooth, inverse_vol=True
            )
            r = simulate(book, close, funding, every=3, phase=1)
            print(
                f"  {formation:>9} {smooth:>6} {r['turnover_exec']:6.1f} {r['edge_per_turn']:6.1f} "
                f"{r['sigma']:6.2f} {r['vol_exec']:5.2f} {r['names']:5.1f} {r['gross']:+6.2f} "
                f"{r['long']:+6.2f} {r['short']:+6.2f} {r['fund_short']:+6.2f}   "
                + " ".join(f"{r[f'fold_{n}']:+5.2f}" for n, _, _ in FOLDS)
            )


if __name__ == "__main__":
    main()
