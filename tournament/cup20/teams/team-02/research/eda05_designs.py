"""EDA 05 - structural design screen against the full floor vector (research sim, not the scorer)."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-02/research")
from eda_panel import channel_position, eligibility_mask, load_panel, true_range, wide  # noqa: E402
from eda_sim import funding_matrix  # noqa: E402
from eda_sim2 import bootstrap_B, report, run  # noqa: E402

bars, membership, funding = load_panel()
op, hi, lo, cl = (wide(bars, c) for c in ("open", "high", "low", "close"))
index, cols = cl.index, cl.columns
mask = eligibility_mask(membership, index, cols) & op.notna()
fund = funding_matrix(funding, index, cols)
START = pd.Timestamp("2020-08-17T00:00:00Z")
atr = true_range(hi, lo, cl).ewm(alpha=1 / 42, min_periods=42).mean()


def cadence(c: int, phase: int = 0) -> pd.Series:
    return pd.Series(((np.arange(len(index)) - phase) % c) == 0, index=index)


def rank_weights(score: pd.DataFrame) -> pd.DataFrame:
    s = score.where(mask)
    r = s.rank(axis=1, pct=True)
    z = r.sub(r.mean(axis=1), axis=0)
    g = z.abs().sum(axis=1)
    return z.div(g.where(g > 0), axis=0).fillna(0.0)


def topk_weights(score: pd.DataFrame, k: int) -> pd.DataFrame:
    s = score.where(mask)
    up = s.rank(axis=1, ascending=False, method="first")
    dn = s.rank(axis=1, ascending=True, method="first")
    w = (up <= k).astype(float) - (dn <= k).astype(float)
    g = w.abs().sum(axis=1)
    return w.div(g.where(g > 0), axis=0).fillna(0.0)


def hysteresis(w: pd.DataFrame, reb: pd.Series, k: int, score: pd.DataFrame,
               buffer_k: int) -> pd.DataFrame:
    """Keep an incumbent while it stays inside the wider (k+buffer) band."""
    s = score.where(mask)
    up = s.rank(axis=1, ascending=False, method="first")
    dn = s.rank(axis=1, ascending=True, method="first")
    held = np.zeros(len(cols))
    out = np.zeros((len(index), len(cols)))
    upn, dnn = up.to_numpy(), dn.to_numpy()
    mk = mask.to_numpy()
    rb = reb.to_numpy()
    for t in range(len(index)):
        if not rb[t]:
            out[t] = held
            continue
        u_, d_ = upn[t], dnn[t]
        new = np.zeros(len(cols))
        keep_long = (held > 0) & (u_ <= k + buffer_k) & mk[t]
        keep_short = (held < 0) & (d_ <= k + buffer_k) & mk[t]
        new[keep_long] = 1.0
        new[keep_short] = -1.0
        nl, ns = int(keep_long.sum()), int(keep_short.sum())
        if nl < k:
            cand = np.argsort(np.where(mk[t] & (new == 0), u_, np.inf))[: k - nl]
            new[cand[np.isfinite(u_[cand])]] = 1.0
        if ns < k:
            cand = np.argsort(np.where(mk[t] & (new == 0), d_, np.inf))[: k - ns]
            new[cand[np.isfinite(d_[cand])]] = -1.0
        g = np.abs(new).sum()
        held = new / g if g > 0 else new
        out[t] = held
    return pd.DataFrame(out, index=index, columns=cols)


def show(label, w, reb):
    res = run(w, op, fund, reb, START)
    rep = report(res)
    rep["B"] = bootstrap_B(res["net"])
    res2 = run(w, op, fund, reb, START, cost_mult=2.0)
    rep2 = report(res2)
    rep["sharpe2x"] = rep2["sharpe"]
    rep["folds_pos2x"] = rep2["folds_pos"]
    rep["worst_fold2x"] = rep2["worst_fold"]
    print(f"{label:44s} Sh={rep['sharpe']:5.2f} Sh2x={rep['sharpe2x']:5.2f} "
          f"vol={rep['vol']:.3f} dd={rep['maxdd']:.3f} to={rep['turnover']:6.1f} "
          f"tr={rep['trades']:6d} ge={rep['gross_edge_bps']:6.1f} "
          f"L={rep['long_gross']:+.2f} S={rep['short_gross']:+.2f} "
          f"pq={rep['posq']:.2f} fp2x={rep['folds_pos2x']} wf2x={rep['worst_fold2x']:5.2f} "
          f"B={rep['B']:.4f} gx={rep['gross_exp']:.2f} "
          f"F={rep['F1']:.1f}/{rep['F2']:.1f}/{rep['F3']:.1f}/{rep['F4']:.1f}")
    return rep


if __name__ == "__main__":
    for N in (63, 126, 189, 252, 378):
        pos = channel_position(hi, lo, cl, N)
        for c in (9, 21, 42):
            show(f"rank u  N={N:3d} cad={c:2d}", rank_weights(pos), cadence(c))
        print()
    for N in (126, 252, 378):
        pos = channel_position(hi, lo, cl, N)
        for k in (3, 5, 7):
            for c in (9, 21):
                show(f"top{k}   u  N={N:3d} cad={c:2d}", topk_weights(pos, k), cadence(c))
        print()
