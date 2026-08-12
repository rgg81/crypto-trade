"""Approximate research simulator v2 with HOLD (None) semantics. Design guidance only."""
from __future__ import annotations
import numpy as np, pandas as pd

BPS = 7.5e-4
BPY = 3 * 365
FOLD_EDGES = ["2021-08-01", "2022-08-01", "2023-08-01"]
MAX_GROSS, MAX_SYM, MAX_NET = 1.0, 0.20, 1.0


def _cap(w):
    """One uniform scale until gross/net/per-symbol caps hold (reduction only)."""
    a = np.abs(w).sum()
    if a <= 0:
        return w
    s = 1.0
    if a > MAX_GROSS:
        s = min(s, MAX_GROSS / a)
    pk = np.abs(w).max()
    if pk > 0:
        s = min(s, MAX_SYM / pk)
    nt = abs(w.sum())
    if nt > MAX_NET:
        s = min(s, MAX_NET / nt)
    return w * min(s, 1.0)


def simulate(target_list, fwd_price, fwd_fund, cost_mult=1.0, scalars=None, brakes=None):
    """target_list[i] is a np.array of raw weights, or None to hold. Returns per-boundary results."""
    idx = fwd_price.index
    n = fwd_price.shape[1]
    P = np.nan_to_num(fwd_price.to_numpy(), nan=0.0)
    F = np.nan_to_num(fwd_fund.to_numpy(), nan=0.0)
    valid = fwd_price.notna().to_numpy()
    w = np.zeros(n)
    ref_w = np.zeros(n)
    equity, peak = 1.0, 1.0
    net = np.zeros(len(idx)); grs = np.zeros(len(idx)); prc = np.zeros(len(idx))
    fnd = np.zeros(len(idx)); cst = np.zeros(len(idx)); trn = np.zeros(len(idx)); ntr = 0
    grossw = np.zeros(len(idx))
    for i in range(len(idx)):
        tgt = target_list[i]
        if tgt is not None:
            raw = np.where(valid[i], tgt, 0.0)
            a = np.abs(raw).sum()
            new = raw / a if a > 0 else raw
            new = _cap(new)
            if scalars is not None and np.isfinite(scalars[i]):
                new = _cap(new * scalars[i])
        else:
            new = w.copy()
        if brakes:
            # mirrors the evaluator: the brake scales the LAST SUPPLIED reference book and is
            # applied reduction-only against the carried position, so it never compounds.
            if tgt is not None:
                ref_w = new.copy()
            ddown = max(0.0, 1.0 - equity / peak)
            gs = 1.0
            for lvl, sc_ in brakes:
                if ddown >= lvl:
                    gs = min(gs, sc_)
            if gs < 1.0:
                cap = np.abs(ref_w) * gs
                new = np.sign(new) * np.minimum(np.abs(new), cap)
        d = np.abs(new - w)
        turn = d.sum()
        ntr += int((d > 1e-9).sum())
        w = new
        grossw[i] = np.abs(w).sum()
        pr = float((w * P[i]).sum()); fu = -float((w * F[i]).sum())
        c = turn * BPS * cost_mult
        prc[i], fnd[i], cst[i], trn[i] = pr, fu, c, turn
        grs[i] = pr + fu; net[i] = pr + fu - c
        r = net[i]
        # quantities held: weights drift with relative price performance
        denom = 1.0 + pr + fu
        if denom > 1e-8:
            w = w * (1.0 + P[i]) / denom
        equity *= (1.0 + net[i])
        peak = max(peak, equity)
    return pd.DataFrame({"net": net, "gross": grs, "price": prc, "fund": fnd,
                         "cost": cst, "turnover": trn, "grossw": grossw}, index=idx), ntr


def reference_scalars(res, index):
    g = pd.Series(res["gross"].to_numpy(), index=index)
    lb = 90 * 3
    sd = g.shift(1).rolling(lb, min_periods=lb).std() * np.sqrt(BPY)
    s = (0.10 / sd).clip(0.20, 3.0)
    return s.fillna(1.0).to_numpy()


def metrics(res, trades=None):
    net = res["net"]
    eq = (1 + net).cumprod()
    dd = 1 - eq / eq.cummax()
    out = {}
    out["ann_ret"] = eq.iloc[-1] ** (BPY / len(net)) - 1
    out["vol"] = net.std() * np.sqrt(BPY)
    out["sharpe"] = net.mean() / net.std() * np.sqrt(BPY) if net.std() > 0 else np.nan
    out["maxdd"] = float(dd.max())
    out["calmar"] = out["ann_ret"] / out["maxdd"] if out["maxdd"] > 0 else np.nan
    out["turn_ann"] = res["turnover"].mean() * BPY
    pos = res["gross"].clip(lower=0).sum()
    out["cost_share"] = res["cost"].sum() / pos if pos > 0 else np.nan
    out["trades"] = trades
    out["grossw"] = res["grossw"].mean()
    edges = [net.index[0]] + [pd.Timestamp(e, tz="UTC") for e in FOLD_EDGES] + [net.index[-1] + pd.Timedelta(hours=8)]
    fs = []
    for a, b in zip(edges[:-1], edges[1:]):
        seg = net[(net.index >= a) & (net.index < b)]
        fs.append(float(seg.mean() / seg.std() * np.sqrt(BPY)) if len(seg) > 10 and seg.std() > 0 else np.nan)
    out["folds"] = [round(f, 3) for f in fs]
    out["worst_fold"] = float(np.nanmin(fs)); out["median_fold"] = float(np.nanmedian(fs))
    q = net.groupby([net.index.year, net.index.quarter]).agg(lambda s: s.mean() / s.std() if s.std() > 0 else np.nan)
    out["pos_q"] = float((q > 0).mean())
    return out


def dec(x):
    if x != x: return 0.0
    return min(1.0, x) if x >= 0 else -(-x) / (-x + 1.0)


def G(m2):
    return (30 * dec((m2["worst_fold"] + 0.25) / 1.0) + 20 * dec((m2["median_fold"] - 0.25) / 0.75)
            + 20 * dec((0.20 - m2["maxdd"]) / 0.15) + 15 * dec(m2["calmar"] / 1.5)
            + 8 * dec((m2["pos_q"] - 0.50) / 0.375))


def show(tag, m1, m2, tr):
    print(f"{tag:40s} 1x Sh={m1['sharpe']:+.2f} r={m1['ann_ret']:+.1%} v={m1['vol']:.1%} "
          f"dd={m1['maxdd']:.1%} T={m1['turn_ann']:.1f}x cs={m1['cost_share']:.2f} gw={m1['grossw']:.2f} | "
          f"2x Sh={m2['sharpe']:+.2f} f={m2['folds']} wf={m2['worst_fold']:+.2f} "
          f"cal={m2['calmar']:+.2f} pq={m2['pos_q']:.2f} G={G(m2):.1f} tr={tr}")
