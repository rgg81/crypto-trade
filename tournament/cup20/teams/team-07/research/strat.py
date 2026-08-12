"""Research-side implementation of the candidate book. Mirrors what strategy.py will do."""
from __future__ import annotations
import numpy as np, pandas as pd, sys
sys.path.insert(0, "tournament/cup20/teams/team-07/research")
from panel import build_panel
from sim2 import simulate, reference_scalars, metrics, show, G

_P = None
def data():
    global _P
    if _P is None:
        p = build_panel()
        g=p["grid"]; el=p["eligible"]
        start = el.sum(axis=1).ge(20).idxmax(); m = g>=start
        for k in ("open","high","low","close","quote_volume","taker_buy_quote","trade_count","funding","eligible","rank"):
            p[k] = p[k].loc[m]
        p["grid"] = g[m]
        fr_raw = pd.read_parquet("data/cup20/is/funding.parquet")
        mk = fr_raw.assign(b=fr_raw.funding_time.dt.floor("8h")).groupby(["b","symbol"])["mark_price"].last()
        p["mark"] = mk.unstack("symbol").reindex(p["grid"]).reindex(columns=p["open"].columns)
        p["fwd_price"] = p["open"].shift(-1)/p["open"] - 1.0
        p["fwd_fund"] = p["funding"].shift(-1).fillna(0.0)
        p["ok"] = p["eligible"] & p["fwd_price"].notna()
        _P = p
    return _P


def features(carry_lb, risk_lb, pers_lb, pers_ref):
    p = data(); fr = p["funding"]; op = p["open"]; ok = p["ok"]
    carry = fr.rolling(carry_lb, min_periods=max(2, carry_lb//2)).mean().shift(1)
    risk = op.pct_change().rolling(risk_lb, min_periods=max(4, risk_lb//2)).std().shift(1)
    pers = fr.gt(pers_ref).rolling(pers_lb, min_periods=max(2, pers_lb//2)).mean().shift(1)
    return carry.where(ok), risk.where(ok), pers.where(ok)


def build(carry_lb=63, risk_lb=63, pers_lb=63, pers_ref=1e-4, n_side=8, cadence=9, phase=0,
          sizing="invvol", protect=None, prot_hi=0.85, prot_lo=0.15, gross_floor=0.0,
          scheme="topn", risk_power=1.0, prot_kw=None):
    p = data(); g = p["grid"]; ok = p["ok"]
    carry, risk, pers = features(carry_lb, risk_lb, pers_lb, pers_ref)
    C = carry.to_numpy(); R = risk.to_numpy(); PS = pers.to_numpy(); OK = ok.to_numpy()
    out = []
    for i in range(len(g)):
        if (i % cadence) != (phase % cadence):
            out.append(None); continue
        c, r, ps, o = C[i], R[i], PS[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r > 0) & np.isfinite(ps)
        if v.sum() < 2*n_side:
            out.append(None); continue
        idx = np.where(v)[0]
        rr = np.where(sizing == "invvol", r, 1.0)
        score = (c[idx] - np.median(c[idx])) / (r[idx] ** risk_power if sizing == "invvol" else 1.0)
        w = np.zeros(len(c))
        if scheme == "topn":
            order = idx[np.argsort(score)]
            longs, shorts = order[:n_side], order[-n_side:]
            sz = np.ones(len(c))
            if sizing == "invvol":
                sz = 1.0 / np.where(np.isfinite(r) & (r > 0), r, np.inf)
            w[longs] = sz[longs]; w[shorts] = -sz[shorts]
        else:  # continuous rank tilt, inverse-vol sized
            k = len(idx)
            rk = np.argsort(np.argsort(score)) / max(k - 1, 1) - 0.5
            sz = np.ones(k)
            if sizing == "invvol":
                sz = 1.0 / r[idx]
            w[idx] = -rk * sz
        if protect is not None:
            w = protect(w, idx, c, r, ps, prot_hi, prot_lo, prot_kw or {})
        if np.abs(w).sum() <= 0:
            out.append(np.zeros(len(c))); continue
        # dollar-neutralise inside each sleeve so the two sleeves carry equal gross
        pos = w > 0; neg = w < 0
        if pos.any() and neg.any():
            w[pos] /= w[pos].sum(); w[neg] /= -w[neg].sum()
        out.append(w)
    return out


def evaluate(targets, tag="", quiet=False):
    p = data()
    ref, _ = simulate(targets, p["fwd_price"], p["fwd_fund"], 1.0)
    sc = reference_scalars(ref, p["grid"])
    r1, tr = simulate(targets, p["fwd_price"], p["fwd_fund"], 1.0, sc)
    r2, _ = simulate(targets, p["fwd_price"], p["fwd_fund"], 2.0, sc)
    m1, m2 = metrics(r1, tr), metrics(r2, tr)
    if not quiet: show(tag, m1, m2, tr)
    return m1, m2, r1, r2, tr
