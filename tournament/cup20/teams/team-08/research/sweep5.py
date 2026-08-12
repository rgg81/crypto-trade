"""Concentration, robustness and the dispersion gate.

The arithmetic that decides this lane, written down so the search is aimed rather than
broad. With realised volatility pinned at 10% by the common risk unit,

    sharpe_2x  ~=  annual_turnover * (gross_edge_bps - 15) / 1000

so a book needs gross edge per unit one-way turnover well above 15 bps just to break even
at double cost. The rounds so far reach 9-14 bps. The decay profile says the missing
factor is concentration: per unit gross the alpha runs 22.6 bps at three names a side, 11.9
at six and 6.5 at ten, i.e. the sum of alpha over the selected tail is roughly constant, so
nearly all of it lives in the most extreme name. Concentrating therefore raises edge per
unit turnover almost proportionally, because turnover per rotation is 2 per unit gross
whatever the name count.

Three further levers, all inside the mandate:
  robust    median/MAD instead of mean/sd -- funding sits exactly on the 0.01% anchor 37%
            of the time, so a standard deviation is measuring quantisation, not regime
  disp      cross-sectional dispersion of the dynamics measure as a gate: when every coin's
            funding is moving together the move is market-wide, not positioning
  blend     average the term spread over several formation pairs, for a steadier score
"""

from __future__ import annotations

import itertools
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from eda import load  # noqa: E402
from sim import evaluate, summary  # noqa: E402
from signals import rebalance_mask, rolling_means, xs_orthogonalise, xs_z  # noqa: E402

MIN_SD = 2e-5


def rolling_median(lags, k):
    return np.nanmedian(np.where(np.isfinite(lags[:k]), lags[:k], np.nan), axis=0)


def robust_spread(rate, ks, kl):
    """(short-window median - long-window median) / long-window MAD."""
    ms = rolling_median(rate, ks) if ks > 1 else rate[0]
    ml = rolling_median(rate, kl)
    mad = np.nanmedian(np.abs(np.where(np.isfinite(rate[:kl]), rate[:kl], np.nan) - ml), axis=0)
    return (ms - ml) / np.maximum(1.4826 * mad, MIN_SD)


def mean_spread(rm, rate, ks, kl):
    sd = np.nanstd(np.where(np.isfinite(rate[:kl]), rate[:kl], np.nan), axis=0)
    return (rm[ks - 1] - rm[kl - 1]) / np.maximum(sd, MIN_SD)


def build_book(score, elig, *, n_side, reb, disp_gate=0.0, disp=None):
    z = xs_z(score, elig)
    n_t, n_s = score.shape
    W = np.zeros((n_t, n_s))
    for t in range(n_t):
        if not reb[t]:
            continue
        if disp_gate > 0 and disp is not None and disp[t] < disp_gate:
            continue  # market-wide funding move: the cross-section has nothing to say
        m = elig[t] & np.isfinite(z[t])
        idx = np.flatnonzero(m)
        if len(idx) < 2 * n_side + 2:
            continue
        order = np.argsort(z[t, idx])
        ranked = idx[order]
        w = 0.5 / n_side
        W[t, ranked[-n_side:]] = -w
        W[t, ranked[:n_side]] = +w
    return W


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    lev21 = rm[20]
    n_t = panel["opens"].shape[0]

    base = {
        "mean_3_21": mean_spread(rm, rate, 3, 21),
        "robust_3_21": robust_spread(rate, 3, 21),
        "robust_1_21": robust_spread(rate, 1, 21),
        "blend": np.nanmean(
            np.stack(
                [
                    mean_spread(rm, rate, 1, 21),
                    mean_spread(rm, rate, 3, 21),
                    mean_spread(rm, rate, 3, 30),
                    mean_spread(rm, rate, 6, 21),
                ]
            ),
            axis=0,
        ),
    }
    scores = {}
    for k, v in base.items():
        scores[k] = v
        scores[k + "_o"] = xs_orthogonalise(v, lev21, elig)

    # dispersion of the (orthogonalised) dynamics measure across the eligible cross-section
    d = np.where(elig & np.isfinite(scores["mean_3_21_o"]), scores["mean_3_21_o"], np.nan)
    disp_raw = np.nanstd(d, axis=1)
    disp_rank = pd.Series(disp_raw).rolling(270, min_periods=90).rank(pct=True).to_numpy()
    disp_rank = np.nan_to_num(disp_rank, nan=1.0)

    rows = []
    t0 = time.time()
    grid = list(
        itertools.product(sorted(scores), [1, 2, 3], [6, 9, 15], [0.0, 0.35, 0.6])
    )
    for name, n_side, cadence, dg in grid:
        per = []
        for phase in range(cadence):
            reb = rebalance_mask(n_t, cadence, phase)
            W = build_book(
                scores[name], elig, n_side=n_side, reb=reb, disp_gate=dg, disp=disp_rank
            )
            m = evaluate(panel, W, reb)
            s = summary(m)
            s.update(score=name, n=n_side, cad=cadence, dg=dg, ph=phase)
            rows.append(s)
            per.append(s)
        med = {
            k: float(np.median([r[k] for r in per]))
            for k in ("sh1", "sh2", "worst", "median", "turn", "edge", "vol", "dd2", "L", "S",
                      "trades", "G_eff")
        }
        print(
            f"{name:<14} n={n_side} cad={cadence:<2} dg={dg:.2f} | "
            f"sh1={med['sh1']:+.2f} sh2={med['sh2']:+.2f} worst={med['worst']:+.2f} "
            f"turn={med['turn']:6.1f} edge={med['edge']:6.1f} vol={med['vol']:.3f} "
            f"dd2={med['dd2']:.2f} L={med['L']:+.2f} S={med['S']:+.2f} tr={med['trades']:.0f} "
            f"Geff={med['G_eff']:5.1f} | {time.time()-t0:5.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_conc.csv", index=False
    )


if __name__ == "__main__":
    main()
