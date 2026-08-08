"""Three cheap lifts tried against the frozen-candidate design, before any trial is spent.

L1  skip the most recent bars when measuring the trend, since the last day of an 8h trend carries
    short-horizon reversal that the formation window otherwise treats as continuation;
L2  size by how far the run score clears the floor instead of a binary admit;
L3  average the gate over several formation lengths, which diversifies the horizon rather than
    picking one.

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

CLOSE: pd.DataFrame
MASK: pd.DataFrame


@lru_cache(maxsize=None)
def pieces(formation: int, skip: int):
    stats = rolling_stats(CLOSE.shift(skip) if skip else CLOSE, formation)
    mom = stats["momentum"].where(MASK)
    pers = stats["persistence"].where(MASK)
    vol = stats["volatility"].where(MASK)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    score = ((2.0 * pers - 1.0) * np.sqrt(formation)).where(valid)
    return sign, score, vol


def build(formations, z, smooth, damp, skip=0, mode="binary") -> pd.DataFrame:
    parts = []
    for formation in formations:
        sign, score, vol = pieces(formation, skip)
        if mode == "binary":
            strength = (score >= z).astype(float).where(score.notna())
        else:
            strength = (score - z).clip(lower=0.0).where(score.notna())
        part = (sign * strength / vol).fillna(0.0)
        gross = part.abs().sum(axis=1)
        parts.append(part.div(gross.where(gross > 0, 1.0), axis=0))
    position = sum(parts) / len(parts)
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(MASK, 0.0)
    if damp > 0.0:
        live = (position != 0.0).sum(axis=1).replace(0, np.nan)
        position = position.sub(damp * position.sum(axis=1) / live, axis=0).where(
            position != 0.0, 0.0
        )
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def main() -> None:
    global CLOSE, MASK
    close, _ = load_close_panel()
    CLOSE = close
    MASK = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    def show(label, book):
        r = simulate(book, close, funding, every=3, phase=1)
        ok = (
            r["turnover_exec"] <= 22.0
            and r["edge_per_turn"] >= 45.0
            and r["short"] > 0.05
            and min(r["fold_ir"]) > 0.0
        )
        print(
            f"  {label:<44} IR {r['ir']:5.2f} sig {r['sigma']:.2f} turn {r['turnover_exec']:5.1f} "
            f"e/t {r['edge_per_turn']:6.1f} L {r['long']:+5.2f} S {r['short']:+5.2f} "
            f"nm {r['names']:4.1f} folds "
            + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
            + ("  PASS" if ok else "")
        )

    print("L1 skip the most recent bars (formation 18, z 1.10, smooth 33, damp 0.35)")
    for skip in (0, 1, 2, 3):
        show(f"skip={skip}", build((18,), 1.10, 33, 0.35, skip=skip))

    print("\nL2 strength sizing vs binary")
    for mode in ("binary", "strength"):
        for z in (0.6, 0.9, 1.1):
            show(f"{mode} z={z}", build((18,), z, 33, 0.35, mode=mode))

    print("\nL3 multi-formation ensembles (z 1.10, smooth 33, damp 0.35)")
    for formations in ((12, 18), (15, 21), (12, 18, 27), (9, 15, 21), (12, 21, 33), (9, 18, 27)):
        show(f"f={formations}", build(formations, 1.10, 33, 0.35))

    print("\nL4 damping scan on the best ensemble")
    for formations in ((12, 18, 27), (9, 15, 21)):
        for damp in (0.20, 0.35, 0.50, 0.65):
            show(f"f={formations} damp={damp}", build(formations, 1.10, 33, damp))

    print("\nL5 ensemble x smoothing x z")
    for formations, smooth, z in itertools.product(((12, 18, 27),), (27, 33, 39), (0.9, 1.1, 1.3)):
        show(f"f={formations} sm={smooth} z={z}", build(formations, z, smooth, 0.35))


if __name__ == "__main__":
    main()
