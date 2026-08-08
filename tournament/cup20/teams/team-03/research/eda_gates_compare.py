"""Is the efficiency ratio doing something a magnitude gate does not?

The sharpest internal falsifier for this lane. ER = |sum x| / sum|x| and the vol-normalised
momentum z = sum x / (s * sqrt(N)) are close cousins: for Gaussian steps ER is a monotone
transform of |z|. They separate on FAT TAILS -- s is quadratic in a single jump while sum|x| is
only linear -- so ER tolerates a jumpy trend that z rejects, and z tolerates a slow grind that ER
rejects. If the ER gate is not distinguishable from the |z| gate at matched selectivity, then the
mandate's "path quality" reading is really a risk-adjusted-magnitude reading and the certificate
must say so.

Also compares two genuinely non-collinear quality readings: sign persistence (fraction of steps
in the trend direction) and jump share (largest single step / path length).

Reports only mean forward gross log return per unit gross exposure. No costs, no equity curve,
no Sharpe, no drawdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_book import FOLDS, fold_of  # noqa: E402
from panel import (  # noqa: E402
    forward_log_return,
    load_close_panel,
    load_membership_mask,
    rolling_stats,
)

START = pd.Timestamp("2020-08-17", tz="UTC")


def summarise(weights: pd.DataFrame, forward: pd.DataFrame, label: str) -> None:
    gross = weights.abs().sum(axis=1)
    pnl = (weights * forward).sum(axis=1)
    live = gross > 1e-12
    folds = fold_of(weights.index)
    cells = []
    for name, _, _ in FOLDS:
        sel = live & (folds == name)
        cells.append(
            f"{1e4 * pnl[sel].sum() / gross[sel].sum():6.1f}" if sel.sum() else "   n/a"
        )
    total = 1e4 * pnl[live].sum() / gross[live].sum() if live.any() else float("nan")
    print(
        f"  {label:<40} {total:7.1f}  live {live.mean():5.1%}  names "
        f"{(weights.abs() > 1e-12).sum(axis=1)[live].mean():4.1f}  net/gross "
        f"{(weights.sum(axis=1)[live] / gross[live]).mean():+5.2f}   " + " ".join(cells)
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    horizon = 21
    forward = forward_log_return(close, horizon)

    for formation in (15, 21, 27, 33, 45, 63):
        stats = rolling_stats(close, formation)
        mom = stats["momentum"].where(mask)
        eff = stats["efficiency"].where(mask)
        pers = stats["persistence"].where(mask)
        jump = stats["jump_share"].where(mask)
        vol = stats["volatility"].where(mask)
        zmom = mom / (vol * np.sqrt(formation))
        valid = mom.notna() & eff.notna() & vol.notna() & (vol > 0)
        sign = np.sign(mom).where(valid)

        print(f"\n=== formation {formation} bars ({formation * 8 / 24:.1f}d), fwd {horizon} bars")
        print(f"  corr(ER, |z|) = {eff.stack().corr(zmom.abs().stack()):.4f}")
        summarise(sign.fillna(0.0).loc[START:], forward.loc[START:], "ungated")

        for keep in (0.60, 0.45, 0.35, 0.25):
            er_thr = eff.stack().quantile(1 - keep)
            z_thr = zmom.abs().stack().quantile(1 - keep)
            p_thr = pers.stack().quantile(1 - keep)
            j_thr = jump.stack().quantile(keep)
            print(f"  -- keep {keep:.0%}: ER>={er_thr:.3f} |z|>={z_thr:.3f} "
                  f"pers>={p_thr:.3f} jump<={j_thr:.3f}")
            summarise(sign.where(eff >= er_thr).fillna(0.0).loc[START:],
                      forward.loc[START:], "gate: efficiency ratio")
            summarise(sign.where(zmom.abs() >= z_thr).fillna(0.0).loc[START:],
                      forward.loc[START:], "gate: |vol-normalised momentum|")
            summarise(sign.where(pers >= p_thr).fillna(0.0).loc[START:],
                      forward.loc[START:], "gate: sign persistence")
            summarise(sign.where(jump <= j_thr).fillna(0.0).loc[START:],
                      forward.loc[START:], "gate: low jump share")


if __name__ == "__main__":
    main()
