"""Candidate book, research form. Mirrors strategy.py 1:1."""
from __future__ import annotations
import sys, numpy as np, pandas as pd
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from strat import data
from sim2 import simulate, reference_scalars, metrics, show, G

BASELINE = 1e-4   # Binance interest component: funding above it means the perp trades at a premium


def targets(carry_lb=63, risk_lb=63, crowd_lb=63, crowd_max=1.01, crowd_min=-0.01,
            n_side=7, cadence=6, phase=0, brake_lb=0, brake_max=1.01, brake_floor=0.0,
            symmetric=False, invert=False):
    p = data(); g = p["grid"]; fr = p["funding"]; op = p["open"]; ok = p["ok"]
    carry = fr.rolling(carry_lb, min_periods=max(2, carry_lb // 2)).mean().shift(1)
    risk = op.pct_change().rolling(risk_lb, min_periods=max(4, risk_lb // 2)).std().shift(1)
    crowd = fr.gt(BASELINE).rolling(crowd_lb, min_periods=max(2, crowd_lb // 2)).mean().shift(1)
    C, R, K, OK = carry.to_numpy(), risk.to_numpy(), crowd.to_numpy(), ok.to_numpy()
    if brake_lb:
        agg = crowd.where(ok).mean(axis=1).rolling(brake_lb, min_periods=1).mean().to_numpy()
    else:
        agg = None
    out = []
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence):
            out.append(None); continue
        c, r, k, o = C[i], R[i], K[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0) & np.isfinite(k)
        if v.sum() < 2 * n_side + 2:
            out.append(None); continue
        idx = np.where(v)[0]
        score = (c[idx] - np.median(c[idx])) / r[idx]
        order = idx[np.argsort(score)]                       # ascending: cheapest carry first
        srt = np.argsort(score)
        # --- crowding protection -------------------------------------------------
        short_pool = [j for j in order[::-1] if k[j] <= crowd_max]        # richest carry first
        long_pool = [j for j in order if (not symmetric) or (k[j] >= crowd_min)]
        shorts = np.array(short_pool[:n_side], dtype=int)
        longs = np.array([j for j in long_pool if j not in set(shorts)][:n_side], dtype=int)
        if len(shorts) < n_side or len(longs) < n_side:
            out.append(None); continue
        w = np.zeros(len(c))
        sgn = -1.0 if invert else 1.0
        w[longs] = sgn / r[longs]
        w[shorts] = -sgn / r[shorts]
        pos = w > 0; neg = w < 0
        w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        if agg is not None and np.isfinite(agg[i]) and agg[i] > brake_max:
            w = w * brake_floor
        out.append(w)
    return out


def ev(tag="", **kw):
    p = data(); tl = targets(**kw)
    ref, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, p["grid"])
    r1, tr = simulate(tl, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(tl, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1, tr), metrics(r2, tr)
    if tag: show(tag, m1, m2, tr)
    return m1, m2, r1, r2, tr
