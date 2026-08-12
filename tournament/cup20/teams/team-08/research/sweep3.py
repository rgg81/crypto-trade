"""Structural round: continuous weights + temporal smoothing at cadence 1.

Round 2's lesson was twofold. (a) Top/bottom-N selection at a fast cadence rotates the
whole book every rebalance, which is why turnover ran 100-230x and gross edge per unit
turnover sat near 4 bps. (b) At the slow cadences that fix turnover, the *phase* offset
moves the full-window Sharpe by more than 1.5 -- so any single-phase slow-cadence result
is a statement about that phase, not about the design.

Both are fixed by the same change: continuous score-proportional weights, smoothed over
time, rebalanced every boundary. Cadence 1 has no phase axis at all, and a smoothed
continuous book turns over only as fast as the signal itself moves plus the drift it
corrects.
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
from signals import rolling_means, xs_orthogonalise, xs_z  # noqa: E402
from sweep import fz  # noqa: E402


def ema(x: np.ndarray, halflife: float) -> np.ndarray:
    """Causal EMA down the time axis, NaN-tolerant (NaN contributes nothing)."""
    if halflife <= 0:
        return x
    a = 1.0 - 0.5 ** (1.0 / halflife)
    out = np.zeros_like(x)
    num = np.zeros(x.shape[1])
    den = np.zeros(x.shape[1])
    for t in range(x.shape[0]):
        v = x[t]
        ok = np.isfinite(v)
        num = num * (1 - a)
        den = den * (1 - a)
        num[ok] += a * v[ok]
        den[ok] += a
        out[t] = np.where(den > 1e-9, num / np.where(den > 1e-9, den, 1.0), 0.0)
    return out


def continuous_weights(score, elig, *, clip=2.0, halflife=0.0):
    z = xs_z(score, elig)
    z = np.clip(np.nan_to_num(z, nan=0.0), -clip, clip)
    z = np.where(elig, z, 0.0)
    # re-neutralise after clipping so the book is dollar neutral by construction
    cnt = elig.sum(1, keepdims=True)
    z = np.where(elig, z - np.where(cnt > 0, z.sum(1, keepdims=True) / np.maximum(cnt, 1), 0), 0.0)
    if halflife > 0:
        z = ema(z, halflife)
        z = np.where(elig, z, 0.0)
    g = np.abs(z).sum(1, keepdims=True)
    return np.where(g > 0, z / np.maximum(g, 1e-12), 0.0)


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    bm = rolling_means(bas)
    lev21 = rm[20]

    scores = {}
    for ks, kl in ((1, 21), (3, 21), (3, 30), (6, 21), (6, 45), (9, 30)):
        s = fz(rm, rate, ks, kl)
        scores[f"fz{ks}_{kl}"] = s
        scores[f"fz{ks}_{kl}o"] = xs_orthogonalise(s, lev21, elig)
    scores["LEVEL21"] = lev21

    rows = []
    t0 = time.time()
    for name, hl, clip in itertools.product(
        sorted(scores), [0.0, 3.0, 9.0, 21.0, 45.0, 90.0], [2.0]
    ):
        W = continuous_weights(scores[name], elig, clip=clip, halflife=hl)
        reb = np.ones(len(W), dtype=bool)
        m = evaluate(panel, -W if name != "LEVEL21" else -W, reb)
        s = summary(m)
        s.update(score=name, hl=hl, clip=clip)
        rows.append(s)
        print(
            f"{name:<10} hl={hl:>5.0f} | sh1={s['sh1']:+.2f} sh2={s['sh2']:+.2f} "
            f"worst={s['worst']:+.2f} med={s['median']:+.2f} dd2={s['dd2']:.3f} "
            f"turn={s['turn']:6.1f} edge={s['edge']:6.1f} vol={s['vol']:.3f} "
            f"L={s['L']:+.2f} S={s['S']:+.2f} fund={s['fund']:+.3f} | {time.time()-t0:4.0f}s",
            flush=True,
        )
    pd.DataFrame(rows).to_csv(
        "tournament/cup20/teams/team-08/research/sweep_continuous.csv", index=False
    )


if __name__ == "__main__":
    main()
