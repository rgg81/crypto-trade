"""Role checks: long sleeve, short sleeve, and the CHOP / TREND regime split (playbook section 7).

The organiser's packet measures the long and short roles directly (``role_long_gross_pnl`` /
``role_short_gross_pnl``). It does not measure a chop role, so this does it offline, on the same
frozen construction and the same data root.

"Chop" is defined WITHOUT any organiser-derived regime series -- those live outside this team's
data root and are not readable. It is built here from the snapshot's own bars: an equal-weight
basket of the eligible top-20 is formed at every boundary, and the regime at boundary t is the
trailing TREND STRENGTH of that basket over the preceding 90 bars, measured strictly before t as

    strength_t = | sum of the last 90 basket log returns | / ( std of those returns * sqrt(90) )

which is the absolute t-statistic of the basket drift. High strength = a directional market;
low strength = chop. Boundaries are split at the terciles of that statistic, and the book's net
return is scored inside each tercile.

A cross-sectional dollar-neutral book should NOT depend on the basket's direction. If this book
only earns in trending thirds, it is a market-direction bet wearing a flow costume, and the
certificate must say so.

Run:  uv run python tournament/cup20/teams/team-09/research/regime.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np

import sweep as SW
from book import tranche_book
from sim import daily, maxdd, sharpe

SW.init()
E = SW._S["E"]
sim = SW._S["sim"]
p = SW._S["p"]

# The nominee's frozen parameters.
FORMATION_BARS, NORM_BARS, HOLD_BARS, SLEEVE_NAMES = 81, 126, 72, 4
PURGE = ("ret", "size", "liq")
TREND_BARS = 90


def basket_trend_strength() -> np.ndarray:
    """|t-stat| of the eligible equal-weight basket drift over the preceding TREND_BARS bars."""
    close = p.close
    with np.errstate(invalid="ignore", divide="ignore"):
        logret = np.diff(np.log(close), axis=0, prepend=np.nan)
    elig_all = p.eligible
    basket = np.full(close.shape[0], np.nan)
    for i in range(close.shape[0]):
        row = logret[i]
        ok = np.isfinite(row) & elig_all[i]
        if ok.sum() >= 5:
            basket[i] = float(row[ok].mean())
    out = np.full(close.shape[0], np.nan)
    for i in range(TREND_BARS, close.shape[0]):
        seg = basket[i - TREND_BARS : i]  # STRICTLY before i
        seg = seg[np.isfinite(seg)]
        if seg.size >= TREND_BARS // 2 and seg.std(ddof=1) > 0:
            out[i] = abs(seg.sum()) / (seg.std(ddof=1) * np.sqrt(seg.size))
    return out[p.d0 : p.dn]


def main() -> None:
    score = SW.score(("bigp", "imbsml"), (1.0, 1.0), FORMATION_BARS, PURGE, nb=NORM_BARS, strict=True)
    weights = tranche_book(score, E, k=SLEEVE_NAMES, hold=HOLD_BARS)
    out = sim.run(weights)

    net = out[1]["net"]  # 1x cost
    strength = basket_trend_strength()
    ok = np.isfinite(strength)
    q1, q2 = np.nanquantile(strength[ok], [1 / 3, 2 / 3])
    print(f"trend-strength terciles: chop < {q1:.3f} <= mid < {q2:.3f} <= trend")

    bands = {
        "CHOP  (weakest third)": ok & (strength < q1),
        "MID   (middle third)": ok & (strength >= q1) & (strength < q2),
        "TREND (strongest third)": ok & (strength >= q2),
    }
    print()
    print(f"{'regime':26s}{'bars':>7s}{'sum net':>11s}{'sharpe':>9s}{'maxdd':>8s}")
    for name, mask in bands.items():
        seg = np.where(mask, net, 0.0)
        d = daily(seg, sim.days)[1]
        print(f"{name:26s}{int(mask.sum()):7d}{seg.sum():11.4f}{sharpe(d):9.3f}{maxdd(d):8.4f}")

    # Long sleeve vs short sleeve, gross, for completeness alongside the organiser's own roles.
    print()
    ret = sim.o_next / sim.o_now - 1.0
    ret = np.where(np.isfinite(ret), ret, 0.0)
    for label, sel in (("long sleeve", weights > 0), ("short sleeve", weights < 0)):
        contrib = np.where(sel, weights, 0.0) * ret
        tot = contrib.sum()
        per = {}
        for name, mask in bands.items():
            per[name] = contrib[mask].sum()
        parts = "  ".join(f"{k.split()[0]}={v:+.4f}" for k, v in per.items())
        print(f"{label:14s} gross total {tot:+.4f}   {parts}")


if __name__ == "__main__":
    main()
