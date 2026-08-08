"""Pre-freeze check of the exact nominee, its eleven declared points, and every ablation.

Same disclosure as eda_variants.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eda_zgate  # noqa: E402
from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask, rolling_stats  # noqa: E402

NOMINEE = dict(formation=18, z=1.10, smooth=33, damp=0.35, every=3, phase=1)

POINTS = [
    ("formation", 15),
    ("formation", 24),
    ("z", 0.90),
    ("z", 1.50),
    ("smooth", 27),
    ("smooth", 39),
    ("damp", 0.20),
    ("damp", 0.50),
    ("phase", 0),
    ("phase", 2),
]

ABLATIONS = [
    ("A0 all controls off", dict(z=None, damp=0.0, equal=True, smooth=33)),
    ("A1 GATE OFF (damp+invvol+smooth kept)", dict(z=None)),
    ("A2 damping off", dict(damp=0.0)),
    ("A3 inverse-vol off", dict(equal=True)),
    ("A4 smoothing off", dict(smooth=1)),
    ("A5 cadence 1", dict(every=1, phase=0)),
    ("A6 cadence 6", dict(every=6, phase=1)),
    ("A7 formation 45", dict(formation=45)),
    ("A8 formation 9", dict(formation=9)),
    ("A9 z floor 2.0", dict(z=2.0)),
]


def build(close, mask, point) -> pd.DataFrame:
    formation = int(point["formation"])
    stats = rolling_stats(close, formation)
    mom = stats["momentum"].where(mask)
    pers = stats["persistence"].where(mask)
    vol = stats["volatility"].where(mask)
    valid = mom.notna() & pers.notna() & vol.notna() & (vol > 0) & (mom != 0)
    sign = np.sign(mom).where(valid)
    if point["z"] is not None:
        score = ((2.0 * pers - 1.0) * np.sqrt(formation)).where(valid)
        sign = sign.where(score >= point["z"])
    position = (sign if point.get("equal") else sign / vol).fillna(0.0)
    gross = position.abs().sum(axis=1)
    position = position.div(gross.where(gross > 0, 1.0), axis=0)
    smooth = int(point["smooth"])
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(mask, 0.0)
    damp = float(point["damp"])
    if damp > 0.0:
        live = (position != 0.0).sum(axis=1).replace(0, np.nan)
        position = position.sub(damp * position.sum(axis=1) / live, axis=0).where(
            position != 0.0, 0.0
        )
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def show(label, r) -> None:
    print(
        f"  {label:<40} IR {r['ir']:5.2f}  sig {r['sigma']:.2f}  turn {r['turnover_exec']:5.1f}x "
        f" e/t {r['edge_per_turn']:6.1f}  L {r['long']:+5.2f} S {r['short']:+5.2f} "
        f" nm {r['names']:4.1f} |net| {r['net']:.2f}  folds "
        + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)
    eda_zgate._CLOSE, eda_zgate._MASK = close, mask

    def run(point):
        return simulate(
            build(close, mask, point), close, funding,
            every=int(point["every"]), phase=int(point["phase"]),
        )

    print("NOMINEE + DECLARED NEIGHBOURHOOD")
    results = [run(dict(NOMINEE))]
    show("nominee", results[0])
    for name, value in POINTS:
        point = dict(NOMINEE)
        point[name] = value
        r = run(point)
        results.append(r)
        show(f"  {name}={value}", r)
    irs = sorted(r["ir"] for r in results)
    shorts = sorted(r["short"] for r in results)
    turns = sorted(r["turnover_exec"] for r in results)
    worst = sorted(min(r["fold_ir"]) for r in results)
    print(
        f"\n  MEDIAN across the 11 points: IR {irs[5]:.2f}  short {shorts[5]:+.2f}  "
        f"turnover {turns[5]:.1f}x  worst-fold IR {worst[5]:+.2f}  "
        f"positive-IR points {sum(1 for r in results if r['ir'] > 0)}/11"
    )

    print("\nABLATIONS")
    for label, override in ABLATIONS:
        point = dict(NOMINEE)
        point.update(override)
        show(label, run(point))


if __name__ == "__main__":
    main()
