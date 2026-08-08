"""Final pre-freeze scout: the intended nominee, its declared neighbourhood, and the ablations.

Same disclosure as eda_variants.py -- the only risk-adjusted number is the uncosted, unscaled
reference book's gross mean over its own standard deviation.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_surface import funding_per_bar  # noqa: E402
from eda_variants import build, simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask  # noqa: E402

NOMINEE = dict(formation=21, floor=0.62, smooth=33, demean=0.33, every=3, phase=1)

NEIGHBOURHOOD = [
    ("formation", 17),
    ("formation", 26),
    ("floor", 0.57),
    ("floor", 0.68),
    ("smooth", 27),
    ("smooth", 39),
    ("demean", 0.20),
    ("demean", 0.45),
    ("phase", 0),
    ("phase", 2),
]

ABLATIONS = [
    ("A0 controls off (no gate, no damp, eq wt)", dict(floor=None, demean=0.0, equal=True)),
    ("A1 gate off (damp + inv-vol kept)", dict(floor=None)),
    ("A2 damping off (gate + inv-vol)", dict(demean=0.0)),
    ("A3 inverse-vol off (gate + damp)", dict(equal=True)),
    ("A4 smoothing off", dict(smooth=1)),
    ("A5 cadence 1 (every bar)", dict(every=1, phase=0)),
    ("A6 cadence 6", dict(every=6, phase=1)),
    ("A7 formation 45", dict(formation=45)),
    ("A8 formation 9", dict(formation=9)),
]


def run(close, mask, funding, point) -> dict:
    book = build(
        close,
        mask,
        formations=(int(point["formation"]),),
        floor=point["floor"],
        mode="binary",
        smooth=int(point["smooth"]),
        demean=float(point["demean"]),
    )
    if point.get("equal"):
        book = build_equal(close, mask, point)
    return simulate(book, close, funding, every=int(point["every"]), phase=int(point["phase"]))


def build_equal(close, mask, point):
    """Equal-weight variant: identical construction with the inverse-vol divisor removed."""
    import numpy as np

    from panel import rolling_stats

    formation = int(point["formation"])
    stats = rolling_stats(close, formation)
    mom = stats["momentum"].where(mask)
    pers = stats["persistence"].where(mask)
    valid = mom.notna() & pers.notna() & (mom != 0)
    sign = np.sign(mom).where(valid)
    if point["floor"] is not None:
        sign = sign.where(pers >= point["floor"] - 1e-9)
    position = sign.fillna(0.0)
    gross = position.abs().sum(axis=1)
    position = position.div(gross.where(gross > 0, 1.0), axis=0)
    smooth = int(point["smooth"])
    if smooth > 1:
        position = position.rolling(smooth, min_periods=1).mean()
    position = position.where(mask, 0.0)
    demean = float(point["demean"])
    if demean > 0.0:
        live = (position != 0.0).sum(axis=1).replace(0, float("nan"))
        position = position.sub(demean * position.sum(axis=1) / live, axis=0).where(
            position != 0.0, 0.0
        )
    gross = position.abs().sum(axis=1)
    return position.div(gross.where(gross > 0, 1.0), axis=0)


def show(label, r) -> None:
    print(
        f"  {label:<42} IR {r['ir']:5.2f}  sig {r['sigma']:.2f}  turn {r['turnover_exec']:5.1f}x "
        f" e/t {r['edge_per_turn']:6.1f}  L {r['long']:+5.2f} S {r['short']:+5.2f} "
        f" names {r['names']:4.1f} |net| {r['net']:.2f}  folds "
        + " ".join(f"{v:+5.2f}" for v in r["fold_ir"])
    )


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    print("NOMINEE and declared neighbourhood")
    show("nominee", run(close, mask, funding, dict(NOMINEE)))
    for name, value in NEIGHBOURHOOD:
        point = dict(NOMINEE)
        point[name] = value
        show(f"  {name}={value}", run(close, mask, funding, point))

    print("\nABLATIONS")
    for label, override in ABLATIONS:
        point = dict(NOMINEE)
        point.update(override)
        show(label, run(close, mask, funding, point))


if __name__ == "__main__":
    main()
