"""EDA 14 -- the control matrix and the long / short / chop role check.

Controls, for this lane, are the three things layered on a plain cross-sectional momentum book:
  C1  market residualisation      (MARKET_REMOVAL 1.0 against 0.0)
  C2  the one-bar skip            (SKIP_BARS 1 against 0)
  C3  the narrowed short sleeve   (short fifth against short third)
Controls-off is raw / no skip / symmetric thirds. Each control alone, then all three together.

Regimes are cut off the equal-weight index itself, causally: trailing 63-bar return above +5%
is 'up', below -5% is 'down', in between is 'chop'. Role PnL is reported per sleeve so the
`long_gross_pnl > 0` / `short_gross_pnl > 0` floors can be read regime by regime.
"""

from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-04/research")
from book import simulate  # noqa: E402
from eda_03_portfolio import FUND, elig, grid, make_signal, opens, start  # noqa: E402
from eda_09_asym import build  # noqa: E402
from panel import load_panel, log_returns, rolling_sum  # noqa: E402

P = load_panel()
R = np.where(elig, log_returns(P["closes"]), np.nan)
with np.errstate(invalid="ignore"):
    MKT = np.nanmean(R, axis=1)
TREND = np.full(len(grid), np.nan)
TREND[1:] = rolling_sum(MKT[:, None], 63)[:-1, 0]


def metrics(kind, K, ml, ms, skip):
    sig, _ = make_signal(kind, 270, 63, skip)
    sh, lp, sp, folds = [], [], [], []
    reg = {"up": [], "chop": [], "down": []}
    for p in range(K):
        w, reb = build(sig, K, p, ml, ms)
        res = simulate(w, reb, opens, FUND, start)
        daily = pd.Series(res["net"], index=grid[start:]).resample("1D").sum()
        sh.append(float(daily.mean() / daily.std() * np.sqrt(365.0)))
        lp.append(float(res["long_gross"].sum()))
        sp.append(float(res["short_gross"].sum()))
        net = pd.Series(res["net"], index=grid[start:])
        t = TREND[start:]
        for name, mask in (
            ("up", t > 0.05),
            ("chop", (t >= -0.05) & (t <= 0.05)),
            ("down", t < -0.05),
        ):
            seg = net[mask & np.isfinite(t)]
            if len(seg) > 30:
                d = seg.resample("1D").sum()
                reg[name].append(float(d.mean() / d.std() * np.sqrt(365.0)))
    return (
        float(np.mean(sh)),
        float(np.mean(lp)),
        float(np.mean(sp)),
        int(sum(1 for x in sp if x > 0)),
        K,
        {k: float(np.mean(v)) if v else float("nan") for k, v in reg.items()},
    )


if __name__ == "__main__":
    print(f"{'C1 resid':>8} {'C2 skip':>8} {'C3 narrow':>10} | {'Sharpe':>7} {'long':>7} "
          f"{'short':>7} {'S>0':>7} | {'up':>6} {'chop':>6} {'down':>6}")
    for c1, c2, c3 in itertools.product((0, 1), repeat=3):
        kind = "resid" if c1 else "raw"
        skip = 1 if c2 else 0
        ms = 4 if c3 else 7
        sh, lp, sp, n, K, reg = metrics(kind, 21, 7, ms, skip)
        print(f"{c1:>8} {c2:>8} {c3:>10} | {sh:>7.2f} {lp:>7.3f} {sp:>7.3f} {n:>3}/{K:<3} | "
              f"{reg['up']:>6.2f} {reg['chop']:>6.2f} {reg['down']:>6.2f}")
    print()
    t = TREND[start:]
    ok = np.isfinite(t)
    print(f"regime occupancy: up={float((t[ok] > 0.05).mean()):.2f} "
          f"chop={float(((t[ok] >= -0.05) & (t[ok] <= 0.05)).mean()):.2f} "
          f"down={float((t[ok] < -0.05).mean()):.2f}")
