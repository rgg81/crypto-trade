"""EDA 12 -- the corrected sweep.

Trial #30 calibrated the offline simulator against the organiser's own numbers. Two corrections
came out of it and both matter:
  * every metric is computed on DAILY returns x sqrt(365), not 8h bars x sqrt(1095). On this book
    that moved fold 3 from -0.03 to -0.45 and left fold 1 and fold 4 almost unchanged, which is
    the whole reason the offline fold profile looked survivable when it was not.
  * the simulator understates one-way turnover by about 19% (20.2 against 24.9 measured) and
    overstates the short sleeve's bleed (-0.19 against -0.045 measured). Turnover figures below
    carry the 1.23x haircut; short-sleeve figures do not, so they are the pessimistic side.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from eda_03_portfolio import make_signal  # noqa: E402
from eda_09_asym import run  # noqa: E402

HAIRCUT = 1.23


def line(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    F = np.array([r["folds"] for r in rows])
    sp = a("short_pnl")
    print(
        f"{tag:<28} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f} "
        f"dd={a('maxdd').mean():.3f} to*={a('turnover_yr').mean() * HAIRCUT:5.1f} "
        f"edge={a('gross_edge_bps').mean():5.0f} S={sp.mean():+.3f}({int((sp > 0).sum())}/{len(sp)}) "
        f"F3={F[:, 2].mean():+.2f}[{F[:, 2].min():+.2f}] mf={a('minfold').mean():+.2f} "
        f"q={a('posq').mean():.2f} folds={np.round(F.mean(0), 2)}"
    )


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "cad"
    if what == "cad":
        for kind in ("resid", "raw"):
            for F in (63, 90):
                sig, _ = make_signal(kind, 270, F, 1)
                for K in (21, 42, 63, 84):
                    line(f"{kind} F={F} K={K} L7/S7", run(sig, K, 7, 7))
            print()
    elif what == "width":
        for kind in ("resid", "raw"):
            for K in (21, 30, 42):
                sig, _ = make_signal(kind, 270, 63, 1)
                for ml, ms in ((7, 7), (7, 5), (7, 4), (7, 3)):
                    line(f"{kind} F=63 K={K} L{ml}/S{ms}", run(sig, K, ml, ms))
                print()
    elif what == "long":
        # does a longer formation carry fold 3 better?
        for F in (63, 90, 126, 180):
            sig, _ = make_signal("resid", 270, F, 1)
            for K in (42, 63):
                line(f"resid F={F} K={K} L7/S4", run(sig, K, 7, 4))
