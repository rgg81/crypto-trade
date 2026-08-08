"""Targeted grid over the surviving design, filtered by the shape constraints that are hard floors.

Same disclosure as eda_variants.py: the only risk-adjusted quantity is the UNCOSTED, UNSCALED
reference book's mean gross bar return divided by its own standard deviation. No cost model, no
common risk unit, no exposure caps, no risk policy, no drawdown, no quarter accounting.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import build, simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask  # noqa: E402


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    rows = []
    formations = (15, 18, 21, 24, 27, 30)
    floors = (0.55, 0.58, 0.60, 0.62, 0.64, 0.67)
    smooths = (24, 30, 36)
    demeans = (0.0, 0.25, 0.40)
    for formation, floor, smooth, demean in itertools.product(formations, floors, smooths, demeans):
        book = build(
            close,
            mask,
            formations=(formation,),
            floor=floor,
            mode="binary",
            smooth=smooth,
            demean=demean,
        )
        r = simulate(book, close, funding, every=3, phase=1)
        rows.append(((formation, floor, smooth, demean), r))

    rows.sort(key=lambda item: -item[1]["ir"])
    print(f"{'f':>3} {'floor':>5} {'sm':>3} {'dm':>4} | {'IR':>5} {'sig':>5} {'turn':>5} "
          f"{'e/t':>5} {'L':>5} {'S':>5} {'names':>5} | fold IRs        | ok")
    for key, r in rows:
        ok = (
            r["turnover_exec"] <= 22.0
            and r["edge_per_turn"] >= 50.0
            and r["short"] > 0.05
            and min(r["fold_ir"]) > -0.10
            and sum(1 for v in r["fold_ir"] if v > 0) >= 4
        )
        if not ok and r["ir"] < 0.95:
            continue
        print(
            f"{key[0]:>3} {key[1]:>5.2f} {key[2]:>3} {key[3]:>4.2f} | {r['ir']:5.2f} "
            f"{r['sigma']:5.2f} {r['turnover_exec']:5.1f} {r['edge_per_turn']:5.1f} "
            f"{r['long']:+5.2f} {r['short']:+5.2f} {r['names']:5.1f} | "
            + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
            + f" | {'PASS' if ok else ''}"
        )


if __name__ == "__main__":
    main()
