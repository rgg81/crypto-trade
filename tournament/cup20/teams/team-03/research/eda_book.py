"""Book-level signal diagnostics: does the quality gate change the edge, the exposure, or both?

Strictly descriptive. Nothing here simulates fills, costs, funding or equity; there is no Sharpe
and no drawdown anywhere in this file. What it reports is
  * mean forward GROSS log return per unit of gross exposure ("edge") for a weight rule,
  * how much gross exposure the rule actually carries and how that varies through time,
  * one-way turnover of the emitted weight stream, which is a mechanical property of the rule.
The tournament's only scorer is scripts/cup20_evaluate.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from panel import (  # noqa: E402
    forward_log_return,
    load_close_panel,
    load_membership_mask,
    rolling_stats,
)

FOLDS = (
    ("F1", "2020-08-17", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
)


def fold_of(index: pd.DatetimeIndex) -> pd.Series:
    out = pd.Series("", index=index, dtype=object)
    for name, start, end in FOLDS:
        lo = pd.Timestamp(start, tz="UTC")
        hi = pd.Timestamp(end, tz="UTC")
        out[(index >= lo) & (index < hi)] = name
    return out


def book_edge(weights: pd.DataFrame, forward: pd.DataFrame, label: str) -> None:
    """Mean forward gross return of the book, per unit gross, overall and per fold."""
    gross = weights.abs().sum(axis=1)
    pnl = (weights * forward).sum(axis=1)
    live = gross > 1e-12
    folds = fold_of(weights.index)
    per_fold = []
    for name, _, _ in FOLDS:
        sel = live & (folds == name)
        if sel.sum() == 0:
            per_fold.append("   n/a")
            continue
        per_fold.append(f"{1e4 * pnl[sel].sum() / gross[sel].sum():6.1f}")
    total = 1e4 * pnl[live].sum() / gross[live].sum() if live.any() else np.nan
    net = weights.sum(axis=1)
    print(
        f"  {label:<38} edge/unit-gross {total:7.1f} bps  live {live.mean():5.1%}  "
        f"mean gross {gross[live].mean():5.2f}  mean net {net[live].mean():+5.2f}  "
        f"names {(weights.abs() > 1e-12).sum(axis=1)[live].mean():4.1f}  folds "
        + " ".join(per_fold)
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    start = pd.Timestamp("2020-08-17", tz="UTC")
    horizon = int(sys.argv[1]) if len(sys.argv) > 1 else 9

    forward = forward_log_return(close, horizon)
    for formation in (21, 45, 90, 135):
        stats = rolling_stats(close, formation)
        mom = stats["momentum"].where(mask)
        eff = stats["efficiency"].where(mask)
        valid = mom.notna() & eff.notna()
        print(f"\n=== formation {formation} ({formation * 8 / 24:.0f}d), forward {horizon} bars")

        sign = np.sign(mom).where(valid)
        # 1. ungated directional book: +-1 per member, equal weight
        raw = sign.fillna(0.0).loc[start:]
        book_edge(raw, forward.loc[start:], "ungated TSMOM (directional)")

        # 2. cross-sectionally demeaned ungated
        dm = (sign.sub(sign.mean(axis=1), axis=0)).where(valid).fillna(0.0).loc[start:]
        book_edge(dm, forward.loc[start:], "ungated TSMOM (demeaned)")

        # 3. ER-gated directional at several thresholds
        for q in (0.4, 0.5, 0.6, 0.7):
            thr = eff.stack().quantile(q)
            gated = sign.where(eff >= thr).fillna(0.0).loc[start:]
            book_edge(gated, forward.loc[start:], f"ER-gated directional  q={q:.1f} thr={thr:.3f}")

        # 4. absolute-threshold gate (what the strategy will actually use)
        for thr in (0.10, 0.15, 0.20, 0.25, 0.30):
            gated = sign.where(eff >= thr).fillna(0.0).loc[start:]
            book_edge(gated, forward.loc[start:], f"ER-gated directional  abs thr={thr:.2f}")


if __name__ == "__main__":
    main()
