"""Approximate research simulator — design guidance only, NEVER a score.

Mirrors the organiser's shape: unit-gross normalisation, exposure caps by uniform reduction,
common risk unit from trailing-90d gross vol of a reference pass, open-to-open returns, funding
summed into the holding interval, 7.5 bps per side per unit of one-way turnover. It is an
approximation (no participation cap, no per-event intra-interval funding, no delisting force
exit) and every number it produces is treated as a design signal, not a result.
"""
from __future__ import annotations
import numpy as np, pandas as pd

BPS = 7.5e-4          # 5 bps fee + 2.5 bps slippage, per side
BOUND_PER_YEAR = 3 * 365
FOLD_EDGES = ["2021-08-01", "2022-08-01", "2023-08-01"]


def cap_reduce(W, max_gross=1.0, max_sym=0.20, max_net=1.0):
    """One uniform per-boundary scale until gross/net/per-symbol caps hold. Never redistributes."""
    gross = W.abs().sum(axis=1)
    peak = W.abs().max(axis=1)
    net = W.sum(axis=1).abs()
    s = pd.Series(1.0, index=W.index)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = s.combine(max_gross / gross.replace(0, np.nan), min).fillna(1.0)
        s = s.combine(max_sym / peak.replace(0, np.nan), min).fillna(1.0)
        s = s.combine(max_net / net.replace(0, np.nan), min).fillna(1.0)
    s = s.clip(upper=1.0).fillna(1.0)
    return W.mul(s, axis=0), s


def run(W, fwd_price, fwd_fund, cost_mult=1.0, risk_unit=True):
    """W: target weights indexed by decision boundary. Returns a per-boundary net return series."""
    W = W.fillna(0.0)
    gross = W.abs().sum(axis=1)
    Wn = W.div(gross.replace(0.0, np.nan), axis=0).fillna(0.0)     # unit gross
    Wc, _ = cap_reduce(Wn)

    price = (Wc * fwd_price.reindex_like(Wc)).sum(axis=1)
    fund = -(Wc * fwd_fund.reindex_like(Wc)).sum(axis=1)
    ref_gross_ret = price + fund

    if risk_unit:
        lb = 90 * 3
        sd = ref_gross_ret.shift(1).rolling(lb, min_periods=lb).std() * np.sqrt(BOUND_PER_YEAR)
        s = (0.10 / sd).clip(0.20, 3.0)
        s = s.fillna(1.0)
    else:
        s = pd.Series(1.0, index=Wc.index)
    Wx, _ = cap_reduce(Wc.mul(s, axis=0))

    price = (Wx * fwd_price.reindex_like(Wx)).sum(axis=1)
    fund = -(Wx * fwd_fund.reindex_like(Wx)).sum(axis=1)
    turn = (Wx - Wx.shift(1).fillna(0.0)).abs().sum(axis=1)
    cost = turn * BPS * cost_mult
    net = price + fund - cost
    trades = int((Wx - Wx.shift(1).fillna(0.0)).abs().gt(1e-9).sum().sum())
    return pd.DataFrame(
        {"net": net, "gross": price + fund, "price": price, "fund": fund,
         "cost": cost, "turnover": turn}
    ), Wx, trades


def metrics(res, trades=None, label=""):
    net = res["net"].dropna()
    eq = (1 + net).cumprod()
    dd = 1 - eq / eq.cummax()
    ann_ret = eq.iloc[-1] ** (BOUND_PER_YEAR / len(net)) - 1
    vol = net.std() * np.sqrt(BOUND_PER_YEAR)
    sharpe = net.mean() / net.std() * np.sqrt(BOUND_PER_YEAR) if net.std() > 0 else np.nan
    out = {"sharpe": sharpe, "ann_ret": ann_ret, "vol": vol, "maxdd": dd.max(),
           "calmar": ann_ret / dd.max() if dd.max() > 0 else np.nan,
           "turn_ann": res["turnover"].mean() * BOUND_PER_YEAR,
           "cost_share": res["cost"].sum() / max(res["gross"].clip(lower=0).sum(), 1e-12),
           "trades": trades}
    edges = [net.index[0]] + [pd.Timestamp(e, tz="UTC") for e in FOLD_EDGES] + [net.index[-1] + pd.Timedelta(hours=8)]
    fs = []
    for a, b in zip(edges[:-1], edges[1:]):
        seg = net[(net.index >= a) & (net.index < b)]
        fs.append(seg.mean() / seg.std() * np.sqrt(BOUND_PER_YEAR) if len(seg) > 10 and seg.std() > 0 else np.nan)
    out["folds"] = [round(f, 3) for f in fs]
    out["worst_fold"] = np.nanmin(fs)
    out["median_fold"] = float(np.nanmedian(fs))
    q = net.groupby([net.index.year, net.index.quarter]).apply(
        lambda s: s.mean() / s.std() if s.std() > 0 else np.nan)
    out["pos_q"] = float((q > 0).mean())
    if label:
        print(f"{label:34s} Sh={out['sharpe']:+.2f} ret={out['ann_ret']:+.1%} vol={out['vol']:.1%} "
              f"dd={out['maxdd']:.1%} cal={out['calmar'] if out['calmar']==out['calmar'] else float('nan'):+.2f} "
              f"turn={out['turn_ann']:.1f}x folds={out['folds']} wf={out['worst_fold']:+.2f} "
              f"posQ={out['pos_q']:.2f} tr={trades}")
    return out


def G(m1x, m2x):
    def dec(x):
        if np.isnan(x): return 0.0
        return min(1.0, x) if x >= 0 else -(-x) / (-x + 1.0)
    return (30 * dec((m2x["worst_fold"] + 0.25) / 1.0)
            + 20 * dec((m2x["median_fold"] - 0.25) / 0.75)
            + 20 * dec((0.20 - m2x["maxdd"]) / 0.15)
            + 15 * dec(m2x["calmar"] / 1.5)
            + 8 * dec((m2x["pos_q"] - 0.50) / 0.375))
