"""Finalist screen. Disclosed approximation, and the last thing computed before the freeze.

This file goes one step further than eda_variants.py and prints an APPROXIMATE net information
ratio, IR - 0.0075 * executed_turnover, which follows from the executed book realising ~10%
annualised volatility under the common risk unit and paying 7.5 bps a side. It exists so that a
design that cannot possibly clear the Sharpe and trial-adjusted-confidence floors is not handed an
eight-minute trial. It is a screen, not a score: it ignores compounding, the exposure caps, the
declared risk policy, the participation cap, the exact funding attribution, drawdown, quarters and
folds-at-2x. Every number this team reports and every floor decision comes from
scripts/cup20_evaluate.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eda_lift  # noqa: E402
from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask  # noqa: E402

SPREAD = 6


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    eda_lift.CLOSE, eda_lift.MASK = close, mask
    funding = funding_per_bar(close.index, close.columns)

    def show(label, formations, z, smooth, damp, every, phase=1):
        book = eda_lift.build(formations, z, smooth, damp)
        r = simulate(book, close, funding, every=every, phase=phase)
        approx = r["ir"] - 0.0075 * r["turnover_exec"]
        ok = (
            r["turnover_exec"] <= 22.0
            and r["edge_per_turn"] >= 45.0
            and r["short"] > 0.05
            and min(r["fold_ir"]) > 0.0
        )
        print(
            f"  {label:<38} IR {r['ir']:5.2f} approx-net {approx:5.2f} sig {r['sigma']:.2f} "
            f"turn {r['turnover_exec']:5.1f} e/t {r['edge_per_turn']:6.1f} S {r['short']:+5.2f} "
            f"nm {r['names']:4.1f} folds "
            + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
            + ("  PASS" if ok else "")
        )

    print("centred three-horizon ensemble (centre-6, centre, centre+6), z 1.10, smooth 33")
    for centre in (12, 15, 18, 21, 24):
        for damp in (0.35, 0.50):
            for every in (3, 6):
                show(
                    f"centre={centre} damp={damp} cad={every}",
                    (centre - SPREAD, centre, centre + SPREAD),
                    1.10,
                    33,
                    damp,
                    every,
                )

    print("\nsingle-horizon finalists")
    for formation in (15, 18):
        for damp in (0.35, 0.50):
            for every in (3, 6):
                show(f"f={formation} damp={damp} cad={every}", (formation,), 1.10, 33, damp, every)

    print("\ncentre=15 ensemble, smoothing and z sensitivity, damp 0.50, cad 3")
    for smooth in (27, 33, 39):
        for z in (0.9, 1.1, 1.3):
            show(f"sm={smooth} z={z}", (9, 15, 21), z, smooth, 0.50, 3)


if __name__ == "__main__":
    main()
