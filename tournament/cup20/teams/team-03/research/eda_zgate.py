"""Standardise the persistence gate so its selectivity does not move with the formation length.

A fixed FRACTION threshold ("at least 62% of bars agreed with the net direction") is not the same
test at N=15 and at N=45: under a coin-flip null the fraction concentrates as sqrt(N), so 0.62
selects the top ~30% of readings at N=15 and the top ~5% at N=45. That is why the formation axis
was so sharp in eda_final_scout.py -- moving the formation silently moved the selectivity.

The invariant version is the standardised run score

    z = (2 * persistence - 1) * sqrt(formation)

which is the number of standard deviations by which the count of agreeing bars exceeds the
coin-flip null. Gating on z holds selectivity fixed while the formation moves, which is what the
neighbourhood needs if the formation coordinate is to explore the horizon rather than the
threshold.

Same disclosure as eda_variants.py.
"""

from __future__ import annotations

import itertools
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask, rolling_stats  # noqa: E402

_CLOSE: pd.DataFrame
_MASK: pd.DataFrame


@lru_cache(maxsize=None)
def components(formation: int):
    stats = rolling_stats(_CLOSE, formation)
    mom = stats["momentum"].where(_MASK)
    pers = stats["persistence"].where(_MASK)
    vol = stats["volatility"].where(_MASK)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    score = ((2.0 * pers - 1.0) * np.sqrt(formation)).where(valid)
    return sign, score, vol


def book(formation: int, z_floor: float | None, smooth: int, demean: float) -> pd.DataFrame:
    sign, score, vol = components(formation)
    gated = sign if z_floor is None else sign.where(score >= z_floor)
    position = (gated / vol).fillna(0.0)
    gross = position.abs().sum(axis=1)
    position = position.div(gross.where(gross > 0, 1.0), axis=0)
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(_MASK, 0.0)
    if demean > 0.0:
        live = (position != 0.0).sum(axis=1).replace(0, np.nan)
        position = position.sub(demean * position.sum(axis=1) / live, axis=0).where(
            position != 0.0, 0.0
        )
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def main() -> None:
    global _CLOSE, _MASK
    _CLOSE, _MASK = (lambda pair: pair)(load_close_panel())[0], None
    close, _ = load_close_panel()
    _CLOSE = close
    _MASK = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    print("coverage of the z gate by formation (fraction of member/bar readings admitted)")
    for formation in (9, 15, 21, 27, 33, 45):
        _, score, _ = components(formation)
        flat = score.stack()
        print(
            f"  N={formation:>3}  "
            + "  ".join(f"z>={z:.1f}: {(flat >= z).mean():.0%}" for z in (0.8, 1.0, 1.2, 1.5, 1.8))
        )

    rows = []
    for formation, z_floor, smooth, demean in itertools.product(
        (9, 12, 15, 18, 21, 27, 33), (0.8, 1.0, 1.2, 1.5, 1.8), (27, 33, 39), (0.20, 0.33, 0.45)
    ):
        r = simulate(book(formation, z_floor, smooth, demean), close, funding, every=3, phase=1)
        rows.append(((formation, z_floor, smooth, demean), r))
    rows.sort(key=lambda item: -item[1]["ir"])
    print(f"\n{'N':>3} {'z':>4} {'sm':>3} {'dm':>4} | {'IR':>5} {'sig':>5} {'turn':>5} {'e/t':>5} "
          f"{'L':>5} {'S':>5} {'nm':>5} | fold IRs        | ok")
    shown = 0
    for key, r in rows:
        ok = (
            r["turnover_exec"] <= 22.0
            and r["edge_per_turn"] >= 50.0
            and r["short"] > 0.05
            and min(r["fold_ir"]) > 0.0
        )
        if not ok:
            continue
        shown += 1
        if shown > 45:
            break
        print(
            f"{key[0]:>3} {key[1]:>4.1f} {key[2]:>3} {key[3]:>4.2f} | {r['ir']:5.2f} "
            f"{r['sigma']:5.2f} {r['turnover_exec']:5.1f} {r['edge_per_turn']:5.1f} "
            f"{r['long']:+5.2f} {r['short']:+5.2f} {r['names']:5.1f} | "
            + " ".join(f"{v:+5.2f}" for v in r["fold_ir"]) + " | PASS"
        )
    print(f"\n{sum(1 for _, r in rows if r['ir'] > 0)}/{len(rows)} points have positive IR")


if __name__ == "__main__":
    main()
