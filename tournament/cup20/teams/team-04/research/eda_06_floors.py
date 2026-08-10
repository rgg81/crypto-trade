"""EDA 6 -- the floors that a cross-sectional long/short book fails first.

Two of them are not about alpha at all and are easy to discover late:
  * `long_gross_pnl > 0` AND `short_gross_pnl > 0`, each at 1x cost, INCLUDING funding. A
    dollar-neutral book in a market that tripled can have a short sleeve that lost money gross and
    still show a fine Sharpe; that is a hard fail.
  * `gross edge >= 40 bps per unit one-way turnover` and `cost share <= 30%`, which together are a
    statement about holding period, not about signal quality.
Everything below is reported as a phase MEAN over all offsets of the cadence.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from eda_03_portfolio import make_signal  # noqa: E402
from eda_05_cadence import evaluate, summarise  # noqa: E402


def line(tag, rows):
    a = lambda k: np.array([r[k] for r in rows])  # noqa: E731
    F = np.array([r["folds"] for r in rows])
    print(
        f"{tag:<34} Sh={a('sharpe').mean():+.2f}±{a('sharpe').std():.2f} "
        f"dd={a('maxdd').mean():.3f} to={a('turnover_yr').mean():5.1f} "
        f"edge={a('gross_edge_bps').mean():5.0f} cs={a('cost_share').mean():.3f} "
        f"L={a('long_pnl').mean():+.3f} S={a('short_pnl').mean():+.3f} "
        f"fund={a('funding_share').mean():+.3f} t5={a('top5_day_share').mean():.3f} "
        f"q={a('posq').mean():.2f} mf={a('minfold').mean():+.2f} folds={np.round(F.mean(0), 2)}"
    )


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "floors"
    if what == "floors":
        for kind in ("raw", "resid"):
            for F, K in ((63, 21), (63, 30), (42, 30)):
                sig, _ = make_signal(kind, 270, F, 1)
                line(f"{kind} F={F} K={K}", [evaluate(sig, K, p) for p in range(K)])
    elif what == "bwin":
        for B in (90, 180, 270, 400, 540):
            sig, _ = make_signal("resid", B, 63, 1)
            line(f"resid B={B} F=63 K=21", [evaluate(sig, 21, p) for p in range(21)])
    elif what == "skip":
        for S in (0, 1, 3, 6):
            sig, _ = make_signal("resid", 270, 63, S)
            line(f"resid B=270 F=63 S={S} K=21", [evaluate(sig, 21, p) for p in range(21)])
    elif what == "hyst":
        sig, _ = make_signal("resid", 270, 63, 1)
        for ex in (None, 0.38, 0.42, 0.45):
            for K in (9, 15, 21):
                line(f"resid F=63 K={K} exit={ex}",
                     [evaluate(sig, K, p, exit_frac=ex) for p in range(K)])
    elif what == "cost":
        sig, _ = make_signal("resid", 270, 63, 1)
        for cm in (1, 2, 3):
            for K in (15, 21, 30):
                line(f"resid F=63 K={K} cost={cm}x",
                     [evaluate(sig, K, p, cm=cm) for p in range(K)])
