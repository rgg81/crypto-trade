"""Turn a cross-sectional flow score into a weight matrix, and score it offline.

The book shape is deliberately plain so that the mechanism, not the packaging, is what is being
measured: rank the eligible names by the flow score, go long the top ``k``, short the bottom
``k``, equal weight inside each sleeve, dollar neutral, rebalance every ``cadence`` boundaries at
phase ``phase``, and hold in between.
"""

from __future__ import annotations

import numpy as np

from sim import Sim, metrics


def tranche_book(
    score: np.ndarray,
    elig: np.ndarray,
    *,
    k: int,
    hold: int,
    weight: str = "equal",
) -> np.ndarray:
    """``hold`` overlapping sleeves, one opened every boundary, each held ``hold`` boundaries.

    Identical in holding horizon to a cadence-``hold`` book but phase-invariant by construction:
    it is the average over all ``hold`` phase offsets rather than one arbitrary choice of phase.
    That matters because a cadence-42 book measured at a single phase spanned Sharpe -0.00 to
    +1.36 across its 42 offsets in this window; the tranche book is the mean of that distribution
    and cannot be lucky in phase.
    """
    n, m = score.shape
    daily = np.zeros((n, m))
    for i in range(n):
        row = np.where(elig[i] & np.isfinite(score[i]), score[i], np.nan)
        idx = np.flatnonzero(np.isfinite(row))
        if idx.size < 2 * k + 2:
            daily[i] = daily[i - 1] if i else 0.0
            continue
        order = idx[np.argsort(row[idx], kind="stable")]
        shorts, longs = order[:k], order[-k:]
        if weight == "equal":
            daily[i, longs] = 0.5 / k
            daily[i, shorts] = -0.5 / k
        else:
            lw = np.arange(1, k + 1, dtype=float)
            lw /= lw.sum()
            daily[i, longs] = 0.5 * lw
            daily[i, shorts] = -0.5 * lw[::-1]
    cs = np.concatenate([np.zeros((1, m)), np.cumsum(daily, axis=0)])
    W = np.empty((n, m))
    for i in range(n):
        lo = max(0, i - hold + 1)
        W[i] = (cs[i + 1] - cs[lo]) / (i + 1 - lo)
    return np.where(elig, W, 0.0)


def cross_sectional_book(
    score: np.ndarray,
    elig: np.ndarray,
    *,
    k: int,
    cadence: int,
    phase: int,
    smooth: float = 0.0,
    weight: str = "equal",
) -> np.ndarray:
    """Long the top-k, short the bottom-k of ``score`` within each boundary's eligible set."""
    n, m = score.shape
    W = np.zeros((n, m))
    live = np.zeros(m)
    for i in range(n):
        if (i % cadence) == (phase % cadence):
            row = np.where(elig[i] & np.isfinite(score[i]), score[i], np.nan)
            idx = np.flatnonzero(np.isfinite(row))
            if idx.size >= 2 * k + 2:
                order = idx[np.argsort(row[idx], kind="stable")]
                target = np.zeros(m)
                shorts, longs = order[:k], order[-k:]
                if weight == "equal":
                    target[longs] = 0.5 / k
                    target[shorts] = -0.5 / k
                else:  # linear in within-sleeve rank
                    lw = np.arange(1, k + 1, dtype=float)
                    lw /= lw.sum()
                    target[longs] = 0.5 * lw
                    target[shorts] = -0.5 * lw[::-1]
                live = target if smooth <= 0 else (1 - smooth) * live + smooth * target
        # names that left the eligible set are dropped, never carried
        W[i] = np.where(elig[i], live, 0.0)
    return W


def score_book(sim: Sim, W: np.ndarray, folds, levels=(1, 2, 3)) -> dict:
    out = sim.run(W, cost_levels=levels)
    m = metrics(out, sim.days)
    base = m[levels[0]]
    res = {
        "sharpe1": m[1]["sharpe"] if 1 in m else np.nan,
        "sharpe2": m[2]["sharpe"] if 2 in m else np.nan,
        "sharpe3": m[3]["sharpe"] if 3 in m else np.nan,
        "ann1": m[1]["ann_return"] if 1 in m else np.nan,
        "ann2": m[2]["ann_return"] if 2 in m else np.nan,
        "vol": base["ann_vol"],
        "dd1": m[1]["maxdd"] if 1 in m else np.nan,
        "dd2": m[2]["maxdd"] if 2 in m else np.nan,
        "turn": base["ann_turnover"],
        "edge_bps": base["gross_edge_bps"],
        "cost_share": base["cost_share"],
        "trades": base["trades"],
        "long_gross": base["long_gross"],
        "short_gross": base["short_gross"],
        "req_min_scale": out["requested_min_scale"],
    }
    if 2 in m:
        d2 = m[2]["daily"]
        res.update(fold_sharpes(d2, sim, folds, prefix="f"))
        res["calmar2"] = m[2]["calmar"]
        res["pq2"] = positive_quarter_fraction(d2, sim)
    return res


def _daily_index(sim: Sim):
    import pandas as pd

    uniq = np.unique(sim.days)
    return pd.DatetimeIndex(uniq * 86_400_000_000_000).tz_localize("UTC")


def fold_sharpes(daily: np.ndarray, sim: Sim, folds, prefix="f") -> dict:
    from sim import sharpe

    idx = _daily_index(sim)
    out = {}
    vals = []
    for j, (name, lo, hi) in enumerate(folds):
        mask = (idx >= lo) & (idx < hi)
        s = sharpe(daily[mask])
        out[f"{prefix}{j + 1}"] = s
        vals.append(s)
    out["worst_fold"] = min(vals)
    out["median_fold"] = float(np.median(vals))
    out["pos_folds"] = int(sum(v > 0 for v in vals))
    return out


def positive_quarter_fraction(daily: np.ndarray, sim: Sim) -> float:
    import pandas as pd

    idx = _daily_index(sim)
    q = pd.Series(daily, index=idx.tz_convert("UTC").tz_localize(None))
    grouped = (1.0 + q).groupby(q.index.to_period("Q")).prod() - 1.0
    return float((grouped > 0).mean())


def G(res: dict) -> float:
    """Charter section 7.4 ranking score, computed offline from offline metrics."""
    C = lambda x: min(1.0, max(0.0, x))  # noqa: E731
    cal = res.get("calmar2", 0.0)
    if not np.isfinite(cal):
        cal = 0.0
    return (
        30 * C((res["worst_fold"] + 0.25) / 1.00)
        + 20 * C((res["median_fold"] - 0.25) / 0.75)
        + 20 * C((0.20 - res["dd2"]) / 0.15)
        + 15 * C(cal / 1.50)
        + 8 * C((res["pq2"] - 0.50) / 0.375)
    )
