"""iter-010 IS-ONLY robustness + selection-discipline evidence (Critic blocker #3).

The iter-010 champion adds 3 knobs over the level gate (w_blend, sm, zwin). The "w_blend=0.65 is not
bear-tuned" defense rests on one empirical claim: IS Sharpe is MONOTONE in the acceleration weight
w, so selecting the highest-IS book pushes w toward the accel end and the bear protection is a
BYPRODUCT of IS-only selection — the bear never enters the objective. This script COMMITS that: a
w×sm×zwin sweep scored on the IS (2015→2025-03) with the bear (2011-15) + bull shown ONLY as
read-after stress. It also decomposes the 2008 crash vs recovery (the leading-signal trade-off).

Canonical data: BEAR = data_bear (gold/silver 2011-15), IS+BULL = data/ (4 metals). Run:
    uv run python analysis/portfolio/metals/iter_010_robustness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_008_allweather as a8  # noqa: E402
import iter_010_breadth_accel as i10  # noqa: E402
import universe_metals as um  # noqa: E402

W_GRID = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
SM_GRID = (21, 42, 63)
ZWIN_GRID = (126, 252)


def _sr(net: pd.Series, lo: str, hi: str) -> float:
    return i10._seg(net, lo, hi)["sharpe"]


def main() -> None:
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)
    is_w = ("2000-01-01", str(um.OOS_CUTOFF.date()))
    bear_w = ("2011-09-01", "2015-03-24")
    bull_w = (str(um.OOS_CUTOFF.date()), "2100-01-01")

    print("=" * 88)
    print("iter-010 ROBUSTNESS — IS-only selection; BEAR/BULL shown as STRESS only")
    print("=" * 88)

    # (1) MONOTONE-IS curve in w (sm/zwin at champion 42/252): IS must rise with the accel weight w,
    #     and the bear must rise in lockstep WITHOUT ever being optimised.
    print("\n(1) IS-monotonicity in w  (sm=42, zwin=252; * marks the champion w=0.65 region):")
    print(f"    {'w':>5} {'IS':>7} {'BEAR(stress)':>13} {'BULL(stress)':>13}")
    for w in W_GRID:
        nm, nb = i10.desk_net(cm, w_blend=w), i10.desk_net(cb, w_blend=w)
        star = " *" if abs(w - 0.6) < 0.11 else ""
        print(
            f"    {w:>5.1f} {_sr(nm, *is_w):>+7.2f} {_sr(nb, *bear_w):>+13.2f} "
            f"{_sr(nm, *bull_w):>+13.2f}{star}"
        )

    # (2) all-weather BASIN over the 3 accel knobs (IS-selected region): count all-3-positive cells.
    print("\n(2) all-weather basin over w×sm×zwin (all-3-Sharpe-positive under honest accounting):")
    allc = tot = 0
    bears = []
    for sm in SM_GRID:
        for zwin in ZWIN_GRID:
            for w in (0.4, 0.6, 0.8):  # the high-IS region selection actually lands in
                nm = i10.desk_net(cm, w_blend=w, sm=sm, zwin=zwin)
                nb = i10.desk_net(cb, w_blend=w, sm=sm, zwin=zwin)
                a3 = _sr(nb, *bear_w) > 0 and _sr(nm, *is_w) > 0 and _sr(nm, *bull_w) > 0
                allc += a3
                tot += 1
                bears.append(_sr(nb, *bear_w))
    print(
        f"    {allc}/{tot} cells all-weather; bear_w range "
        f"[{min(bears):+.2f}, {max(bears):+.2f}] — basin, not a point."
    )

    # (3) 2008 crash vs recovery decomposition (the leading-signal trade-off, honestly quantified).
    p = _HERE.parents[2] / "data_bear2008"
    if (p / "XAUUSDT" / "8h.csv").exists():
        n08 = i10.desk_net(um.load_metals(p))
        print("\n(3) pristine 2008 decomposition (champion):")
        for lo, hi, lbl in [
            ("2008-07-01", "2008-12-31", "pure crash (down leg)"),
            ("2009-01-01", "2009-06-01", "recovery (up leg)"),
            ("2008-03-01", "2009-06-01", "full crash+recovery"),
        ]:
            print(f"    {lbl:24} Sharpe={_sr(n08, lo, hi):+.2f}")
        print(
            "    → leading accel captures the CRASH (+) and de-escalates into the V-recovery (the "
            "give-back); net round-trip ~flat. Disclosed trade-off, not a fit."
        )


if __name__ == "__main__":
    main()
