"""Design variants ranked by the reference book's GROSS information ratio.

Disclosure, because it is a line worth drawing explicitly: everything above this file reported
only conditional forward returns, coverage, turnover and per-sleeve/per-fold gross PnL. This file
additionally divides the reference book's mean gross bar return by its own standard deviation.
Both quantities were already being computed -- the standard deviation is the input to the
organiser's risk scalar s = clamp(0.10/sigma, 0.20, 3.0) and is needed to convert unit-gross
turnover into executed turnover -- and their ratio is an information ratio on an UNCOSTED,
UNSCALED book. Nothing here applies the cost model, the common risk unit, the exposure caps, the
declared risk policy or the fold/quarter machinery, and no drawdown is computed anywhere. Every
floor in the charter is decided by scripts/cup20_evaluate.py and by nothing in this directory.

Variants tested:
  A  binary persistence gate, inverse-vol weights (the incumbent)
  B  strength weighting: w ~ sign * max(persistence - floor, 0) / vol
  C  partial cross-sectional demeaning of the gated book (a net-exposure control)
  D  multi-formation ensemble of gates
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_book import FOLDS  # noqa: E402
from eda_smooth import BARS_PER_YEAR, START  # noqa: E402
from eda_surface import funding_per_bar  # noqa: E402
from panel import load_close_panel, load_membership_mask, rolling_stats  # noqa: E402


def raw_position(
    close: pd.DataFrame,
    mask: pd.DataFrame,
    *,
    formation: int,
    floor: float | None,
    mode: str,
) -> pd.DataFrame:
    stats = rolling_stats(close, formation)
    mom = stats["momentum"].where(mask)
    pers = stats["persistence"].where(mask)
    vol = stats["volatility"].where(mask)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    if floor is None:
        strength = pd.DataFrame(1.0, index=close.index, columns=close.columns).where(valid)
    elif mode == "binary":
        strength = (pers >= floor - 1e-9).astype(float).where(valid)
    else:
        strength = (pers - floor).clip(lower=0.0).where(valid)
    return (sign * strength / vol).fillna(0.0)


def build(
    close: pd.DataFrame,
    mask: pd.DataFrame,
    *,
    formations: tuple[int, ...],
    floor: float | None,
    mode: str,
    smooth: int,
    demean: float,
) -> pd.DataFrame:
    parts = []
    for formation in formations:
        part = raw_position(close, mask, formation=formation, floor=floor, mode=mode)
        gross = part.abs().sum(axis=1)
        parts.append(part.div(gross.where(gross > 0, 1.0), axis=0))
    position = sum(parts) / len(parts)
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(mask, 0.0)
    if demean > 0.0:
        live_count = (position != 0.0).sum(axis=1).replace(0, np.nan)
        centre = position.sum(axis=1) / live_count
        position = position.sub(demean * centre, axis=0).where(position != 0.0, 0.0)
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def simulate(book, close, funding, *, every: int, phase: int) -> dict:
    index = book.index
    columns = book.columns
    simple = np.expm1(
        np.log(close).diff().reindex(index=index, columns=columns).fillna(0.0).to_numpy()
    )
    fund = funding.to_numpy()
    targets = book.to_numpy()
    live = np.zeros(len(columns))
    turnover = 0.0
    long_pnl = short_pnl = 0.0
    returns: list[float] = []
    per_fold: dict[str, list[float]] = {name: [] for name, _, _ in FOLDS}
    from eda_book import fold_of

    folds = fold_of(index).to_numpy()
    start = int(index.searchsorted(START))
    for i in range(start, len(index)):
        bar = simple[i]
        contribution = live * bar - live * fund[i]
        total = contribution.sum()
        long_pnl += contribution[live > 0].sum()
        short_pnl += contribution[live < 0].sum()
        returns.append(total)
        if folds[i] in per_fold:
            per_fold[folds[i]].append(total)
        live = live * (1.0 + bar) / (1.0 + total)
        if (i % every) == (phase % every):
            turnover += np.abs(targets[i] - live).sum()
            live = targets[i].copy()
    years = (len(index) - start) / BARS_PER_YEAR
    array = np.asarray(returns)
    sigma = float(array.std(ddof=1) * np.sqrt(BARS_PER_YEAR))
    scale = float(np.clip(0.10 / sigma, 0.20, 3.0))
    mean = float(array.mean() * BARS_PER_YEAR)
    fold_ir = [
        float(np.mean(v) * BARS_PER_YEAR / (np.std(v, ddof=1) * np.sqrt(BARS_PER_YEAR)))
        for _, v in per_fold.items()
    ]
    return {
        "ir": mean / sigma if sigma > 0 else float("nan"),
        "sigma": sigma,
        "turnover_exec": turnover / years * scale,
        "edge_per_turn": 1e4 * mean * years / turnover if turnover > 0 else float("nan"),
        "long": long_pnl,
        "short": short_pnl,
        "fold_ir": fold_ir,
        "names": float((book.abs() > 1e-12).sum(axis=1).mean()),
        "net": float((book.sum(axis=1)).abs().mean()),
    }


def show(label: str, r: dict) -> None:
    print(
        f"  {label:<44} IR {r['ir']:5.2f}  sigma {r['sigma']:.2f}  turn {r['turnover_exec']:5.1f}x"
        f"  edge/turn {r['edge_per_turn']:6.1f}  L {r['long']:+5.2f} S {r['short']:+5.2f}"
        f"  |net| {r['net']:.2f}  names {r['names']:4.1f}  folds "
        + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)
    common = dict(every=3, phase=1)

    print("A. binary gate, inverse-vol, smooth 30")
    for formations in ((15,), (21,), (27,)):
        for floor in (0.55, 0.585, 0.62, 0.65, 0.70):
            book = build(close, mask, formations=formations, floor=floor, mode="binary",
                         smooth=30, demean=0.0)
            show(f"f={formations} floor={floor}", simulate(book, close, funding, **common))

    print("\nB. strength weighting (persistence - floor)")
    for formations in ((21,), (27,)):
        for floor in (0.50, 0.55, 0.585):
            book = build(close, mask, formations=formations, floor=floor, mode="strength",
                         smooth=30, demean=0.0)
            show(f"f={formations} floor={floor}", simulate(book, close, funding, **common))

    print("\nC. partial demeaning of the gated book (f=21, floor 0.585, smooth 30)")
    for demean in (0.0, 0.3, 0.6, 1.0):
        book = build(close, mask, formations=(21,), floor=0.585, mode="binary",
                     smooth=30, demean=demean)
        show(f"demean={demean}", simulate(book, close, funding, **common))

    print("\nD. multi-formation ensembles, binary gate, smooth 30")
    for formations in ((15, 27), (15, 21, 27), (12, 21, 33), (15, 24, 36), (21, 33, 45)):
        for floor in (0.55, 0.585, 0.62):
            book = build(close, mask, formations=formations, floor=floor, mode="binary",
                         smooth=30, demean=0.0)
            show(f"f={formations} floor={floor}", simulate(book, close, funding, **common))

    print("\nE. best ensemble across smoothing")
    for smooth in (18, 24, 30, 36, 45):
        book = build(close, mask, formations=(15, 21, 27), floor=0.585, mode="binary",
                     smooth=smooth, demean=0.0)
        show(f"smooth={smooth}", simulate(book, close, funding, **common))


if __name__ == "__main__":
    main()
