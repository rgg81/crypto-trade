"""Sign persistence as the trend-quality gate: is it distinct from magnitude, and does it hold?

Follow-up to eda_gates_compare.py, which falsified the premise that the efficiency ratio is a
distinct path reading (corr(ER, |z|) = 0.98 across every formation tested). Sign persistence --
the fraction of formation bars whose step agreed with the net direction -- is scale free and
depends on the ORDER and SIGN of the increments rather than their sizes, so it is the candidate
path statistic that magnitude cannot already express.

Reports only conditional forward gross log return per unit gross exposure, correlations between
gate statistics, gate coverage, and one-way turnover of the emitted weight stream.
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
    cells = [
        f"{1e4 * pnl[live & (folds == n)].sum() / gross[live & (folds == n)].sum():7.1f}"
        if (live & (folds == n)).sum()
        else "    n/a"
        for n, _, _ in FOLDS
    ]
    total = 1e4 * pnl[live].sum() / gross[live].sum() if live.any() else float("nan")
    print(
        f"  {label:<46} {total:7.1f}  live {live.mean():5.1%}  names "
        f"{(weights.abs() > 1e-12).sum(axis=1)[live].mean():4.1f}  n/g "
        f"{(weights.sum(axis=1)[live] / gross[live]).mean():+5.2f}  " + " ".join(cells)
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    forward = forward_log_return(close, 21)

    for formation in (18, 21, 24, 27, 30, 36):
        stats = rolling_stats(close, formation)
        mom = stats["momentum"].where(mask)
        eff = stats["efficiency"].where(mask)
        pers = stats["persistence"].where(mask)
        vol = stats["volatility"].where(mask)
        zmom = (mom / (vol * np.sqrt(formation))).where(mask)
        valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0)
        sign = np.sign(mom).where(valid)

        flat = pd.DataFrame(
            {
                "pers": pers.stack(),
                "absz": zmom.abs().stack(),
                "eff": eff.stack(),
            }
        ).dropna()
        print(
            f"\n=== formation {formation} ({formation * 8 / 24:.1f}d)  "
            f"corr(pers,|z|)={flat['pers'].corr(flat['absz']):.3f}  "
            f"corr(pers,ER)={flat['pers'].corr(flat['eff']):.3f}  "
            f"corr(ER,|z|)={flat['eff'].corr(flat['absz']):.3f}"
        )
        summarise(sign.fillna(0.0).loc[START:], forward.loc[START:], "ungated directional")

        for k in range(int(formation * 0.52), int(formation * 0.72) + 1):
            thr = k / formation
            gate = pers >= thr - 1e-9
            gated = sign.where(gate).fillna(0.0).loc[START:]
            coverage = gate.where(valid).stack().mean()
            summarise(
                gated,
                forward.loc[START:],
                f"pers >= {k}/{formation} = {thr:.3f}  (cover {coverage:.0%})",
            )

        # Does persistence survive INSIDE magnitude buckets? Double sort, |z| tertile x pers half.
        panel = pd.DataFrame(
            {
                "pers": pers.stack(),
                "absz": zmom.abs().stack(),
                "sign": sign.stack(),
                "fwd": forward.stack(),
            }
        ).dropna()
        panel = panel.loc[panel.index.get_level_values(0) >= START]
        panel["cont"] = 1e4 * panel["sign"] * panel["fwd"]
        panel["zq"] = pd.qcut(panel["absz"], 3, labels=False, duplicates="drop")
        panel["pq"] = (panel["pers"] >= panel["pers"].median()).astype(int)
        print("  continuation bps, rows |z| tertile, cols persistence half:")
        print(
            panel.pivot_table(index="zq", columns="pq", values="cont", aggfunc="mean")
            .round(1)
            .to_string()
        )


if __name__ == "__main__":
    main()
