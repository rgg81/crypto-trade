"""Round 2 EDA: does the dynamics signal survive orthogonalisation to the funding LEVEL?

Round 1 established that the funding *level* is the dominant cross-sectional predictor
(IC -0.03 to -0.07, |t| up to 10) and that raw funding *spreads* carry a weaker,
shorter-horizon negative IC. Since spread and level are correlated, the round-1 spread
result may be nothing but level leaking through. This round strips the level out
cross-sectionally and re-measures, and adds the constructions the mandate actually points
at: own-units normalisation, acceleration, persistence, and the basis-versus-funding
divergence that exists because the funding rate is censored at the 0.01% anchor 37% of
the time while the basis is not.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import forward_return, load, spearman_ic  # noqa: E402
from signals import rolling_means, xs_orthogonalise  # noqa: E402


def rolling_std(lags, k):
    x = np.where(np.isfinite(lags[:k]), lags[:k], np.nan)
    return np.nanstd(x, axis=0)


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    bm = rolling_means(bas)

    horizons = (3, 9, 21)
    rets = {h: forward_return(panel, h) for h in horizons}

    measures = {}
    # A: raw spreads (round-1 best region)
    for ks, kl in ((1, 21), (3, 21), (3, 30), (6, 21), (9, 21), (3, 45), (6, 45)):
        measures[f"fspread_{ks}_{kl}"] = rm[ks - 1] - rm[kl - 1]
        measures[f"bspread_{ks}_{kl}"] = bm[ks - 1] - bm[kl - 1]
    # B: own-units (time-series z within the coin)
    for ks, kl in ((1, 21), (3, 21), (3, 30), (6, 21), (9, 21), (3, 45), (6, 45)):
        sd = rolling_std(rate, kl)
        measures[f"fz_{ks}_{kl}"] = (rm[ks - 1] - rm[kl - 1]) / np.where(sd > 0, sd, np.nan)
        sdb = rolling_std(bas, kl)
        measures[f"bz_{ks}_{kl}"] = (bm[ks - 1] - bm[kl - 1]) / np.where(sdb > 0, sdb, np.nan)
    # C: acceleration (second difference of the level path)
    for k in (3, 6, 9, 15):
        measures[f"faccel_{k}"] = (rm[k - 1] - rm[2 * k - 1]) - (rm[2 * k - 1] - rm[3 * k - 1])
        measures[f"baccel_{k}"] = (bm[k - 1] - bm[2 * k - 1]) - (bm[2 * k - 1] - bm[3 * k - 1])
    # D: basis-vs-funding divergence -- the premium the censored funding rate cannot express
    for k in (3, 6, 9, 15, 21):
        measures[f"bfdiv_{k}"] = bm[k - 1] - rm[k - 1]
    # E: persistence of the current funding sign
    for k in (9, 21, 45):
        sgn = np.sign(rate[:k])
        measures[f"fpersist_{k}"] = np.nanmean(sgn, axis=0)

    levels = {kl: rm[kl - 1] for kl in (9, 21, 30, 45, 63)}

    rows = []
    for name, sig in measures.items():
        row = {"measure": name}
        for h in horizons:
            ic, t, _ = spearman_ic(sig, rets[h], elig, stride=3)
            row[f"ic{h}"] = ic
            row[f"t{h}"] = t
        # orthogonalise to the 21-event funding level and re-measure
        orth = xs_orthogonalise(sig, levels[21], elig)
        for h in horizons:
            ic, t, _ = spearman_ic(orth, rets[h], elig, stride=3)
            row[f"oic{h}"] = ic
            row[f"ot{h}"] = t
        rows.append(row)

    # the level itself, as the control
    for kl, lev in levels.items():
        row = {"measure": f"LEVEL_{kl}"}
        for h in horizons:
            ic, t, _ = spearman_ic(lev, rets[h], elig, stride=3)
            row[f"ic{h}"] = ic
            row[f"t{h}"] = t
            row[f"oic{h}"] = np.nan
            row[f"ot{h}"] = np.nan
        rows.append(row)

    df = pd.DataFrame(rows).set_index("measure")
    pd.set_option("display.width", 250)
    print("=== IC raw (ic/t) and IC orthogonal to fund_level_21 (oic/ot) ===")
    print(df.round(4).to_string())
    df.to_csv("tournament/cup20/teams/team-08/research/ic_orth.csv")


if __name__ == "__main__":
    main()
