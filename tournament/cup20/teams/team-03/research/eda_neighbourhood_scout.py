"""Scout the shape of the intended neighbourhood before declaring it.

The declared neighbourhood is scored by per-metric median and must have at least 70% of its points
positive, so a declaration whose corners are structurally broken (a short sleeve that flips
negative, turnover through the floor) wastes the one trial that produces the score. This checks
the corners on the same descriptive quantities used everywhere else in research/: executed
turnover, gross edge per unit turnover, per-sleeve gross PnL including funding, and per-fold gross
PnL. No net returns, no costs, no equity curve, no Sharpe, no drawdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eda_book import FOLDS  # noqa: E402
from eda_smooth import smoothed_book  # noqa: E402
from eda_surface import funding_per_bar, simulate  # noqa: E402
from panel import load_close_panel, load_membership_mask  # noqa: E402

NOMINEE = dict(formation=21, floor=0.585, smooth=30, every=3, phase=1)


def main() -> None:
    close, _ = load_close_panel()
    mask = load_membership_mask(close.index, close.columns)
    funding = funding_per_bar(close.index, close.columns)

    points: list[tuple[str, dict]] = [("NOMINEE", dict(NOMINEE))]
    for name, value in (
        ("formation", 15),
        ("formation", 27),
        ("floor", 0.550),
        ("floor", 0.620),
        ("smooth", 21),
        ("smooth", 39),
        ("every", 2),
        ("every", 5),
        ("phase", 0),
        ("phase", 2),
    ):
        point = dict(NOMINEE)
        point[name] = value
        points.append((f"{name}={value}", point))
    # Ablations at the nominee's other settings.
    for label, override in (
        ("ABLATION gate off", dict(floor=None)),
        ("ABLATION equal weight", dict(inverse_vol=False)),
        ("ABLATION gate off + eq wt", dict(floor=None, inverse_vol=False)),
        ("ABLATION smooth off", dict(smooth=1)),
        ("ABLATION cadence 1", dict(every=1, phase=0)),
    ):
        point = dict(NOMINEE)
        point.update(override)
        points.append((label, point))

    print(
        f"  {'point':<26} {'turn':>6} {'edge':>6} {'sigma':>6} {'vol':>5} {'names':>5} "
        f"{'gross':>6} {'long':>6} {'short':>6} {'fills':>7}   folds"
    )
    for label, point in points:
        book = smoothed_book(
            close,
            mask,
            formation=point["formation"],
            floor=point["floor"],
            smooth=point["smooth"],
            inverse_vol=point.get("inverse_vol", True),
        )
        r = simulate(book, close, funding, every=point["every"], phase=point["phase"])
        print(
            f"  {label:<26} {r['turnover_exec']:6.1f} {r['edge_per_turn']:6.1f} {r['sigma']:6.2f} "
            f"{r['vol_exec']:5.2f} {r['names']:5.1f} {r['gross']:+6.2f} {r['long']:+6.2f} "
            f"{r['short']:+6.2f} {r['fills']:7d}   "
            + " ".join(f"{r[f'fold_{n}']:+5.2f}" for n, _, _ in FOLDS)
        )


if __name__ == "__main__":
    main()
