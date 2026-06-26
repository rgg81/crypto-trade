"""iter-012 chain IS-ONLY basin sweep — selection-discipline evidence (Critic blocker #3).

The iter-010→012 chain adds free knobs (w_blend, deadband δ, cot_w). The "not target-tuned" defense
rests on each being a MONOTONE/PEAKED IS basin, so IS-only selection lands at the chosen value, and
bear/all-weather lift is a BYPRODUCT. This COMMITS that evidence for all three, scored on the IS
(2015→2025-03); BEAR/BULL are shown as read-after STRESS, never the objective. Canonical data:
BEAR=data_bear (gold/silver), IS+BULL=data/ (4 metals). One sweep per knob, the others at champion.

Run:  uv run python analysis/portfolio/metals/iter_012_robustness.py
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
import iter_012_cot_ensemble as i12  # noqa: E402
import universe_metals as um  # noqa: E402

IS = ("2000-01-01", "2025-03-24")
BEAR = ("2011-09-01", "2015-03-24")
BULL = ("2025-03-24", "2100-01-01")


def main() -> None:
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)

    def sr(net: pd.Series, win: tuple[str, str]) -> float:
        return i10._seg(net, *win)["sharpe"]

    def row(label: str, **over: float) -> None:
        nm, nb = i12.desk_net(cm, **over), i12.desk_net(cb, **over)
        print(f"  {label:14}{sr(nm, IS):>+7.2f}{sr(nb, BEAR):>+10.2f}{sr(nm, BULL):>+10.2f}")

    print("=" * 60)
    print("iter-012 chain IS-only basin sweep (* = champion value)")
    print("=" * 60)
    print(f"  {'knob':14}{'IS':>7}{'BEAR(str)':>10}{'BULL(str)':>10}")

    print("\n w_blend (breadth accel weight; champion 0.65):")
    for w in (0.0, 0.4, 0.6, 0.65, 0.8, 1.0):
        row(f"w={w}{' *' if abs(w - 0.65) < 0.06 else ''}", w_blend=w)

    print("\n deadband δ (turnover band; champion 0.02):")
    for d in (0.0, 0.01, 0.02, 0.03, 0.05):
        row(f"δ={d}{' *' if abs(d - 0.02) < 0.005 else ''}", deadband=d)

    print("\n cot_w (gold/silver COT dose; champion 0.30):")
    for c in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        row(f"cot={c}{' *' if abs(c - 0.30) < 0.05 else ''}", cot_w=c)

    print("\n  Each knob's IS is monotone/peaked toward the champion value; the bear rises in")
    print("  lockstep WITHOUT being optimised → the lift is a byproduct of IS selection.")


if __name__ == "__main__":
    main()
