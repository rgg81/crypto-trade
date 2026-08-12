"""Team 08 offline research simulator.

A fast, faithful-but-approximate re-implementation of the documented CUP-20 execution
contract, written so hundreds of designs can be compared before a trial is spent.

It is NOT the organiser scorer and is never cited as a score. Differences known and
accepted:
  * per-symbol participation caps are not modelled;
  * target quantities here use the bar open rather than the boundary mark;
  * delisting haircuts and terminal residuals are not modelled;
  * funding is attributed to the position that held it across (t, t+1].
Everything else follows charter section 4 / section 6: next-bar-open fills, 7.5 bps per
side, unit-gross normalisation, the three exposure caps applied by uniform reduction at
both ends of the common risk unit, and s_t = clamp(0.10 / sigma_t, 0.20, 3.0) from the
reference book's trailing-90-day gross bar returns.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365.0
BARS_PER_DAY = 3
COST_BPS_PER_SIDE = 7.5  # 5.0 taker + 2.5 slippage
MAX_GROSS = 1.0
MAX_NET = 1.0
MAX_SYMBOL = 0.20
RISK_TARGET = 0.10
RISK_LOOKBACK_BARS = 90 * BARS_PER_DAY
RISK_MIN, RISK_MAX = 0.20, 3.0

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")


def cap_rows(w: np.ndarray) -> np.ndarray:
    """One uniform per-row reduction until gross / net / per-symbol caps hold."""
    gross = np.abs(w).sum(1)
    net = np.abs(w.sum(1))
    sym = np.abs(w).max(1)
    scale = np.ones(len(w))
    for mag, ceil in ((gross, MAX_GROSS), (net, MAX_NET), (sym, MAX_SYMBOL)):
        bad = mag > ceil + 1e-12
        cand = np.ones(len(w))
        cand[bad] = ceil / mag[bad]
        scale = np.minimum(scale, cand)
    return w * scale[:, None]


def normalise(w: np.ndarray, reb: np.ndarray) -> np.ndarray:
    out = np.zeros_like(w)
    g = np.abs(w).sum(1)
    d = np.where(g > 0, g, 1.0)
    out[reb] = (w / d[:, None])[reb]
    return out


def _run(panel, W, reb, cost_mult):
    """Sequential book simulation. Returns per-bar diagnostics."""
    opens, fwd, fund, elig = panel["opens"], panel["fwd"], panel["fund_hold"], panel["elig"]
    n_t, n_s = opens.shape
    q = np.zeros(n_s)
    equity = 100_000.0
    rate = COST_BPS_PER_SIDE / 1e4 * cost_mult

    price_pnl = np.zeros(n_t)
    fund_pnl = np.zeros(n_t)
    long_gross = np.zeros(n_t)
    short_gross = np.zeros(n_t)
    costs = np.zeros(n_t)
    net = np.zeros(n_t)
    turn = np.zeros(n_t)
    trades = np.zeros(n_t)
    gross_exp = np.zeros(n_t)

    op_safe = np.where(np.isfinite(opens) & (opens > 0), opens, np.nan)
    for t in range(n_t):
        o = op_safe[t]
        held = q != 0.0
        cur_notional = np.where(held & np.isfinite(o), q * o, 0.0)
        if reb[t]:
            tgt_notional = W[t] * equity
            tgt_notional = np.where(elig[t] & np.isfinite(o), tgt_notional, 0.0)
        else:
            tgt_notional = cur_notional.copy()
            tgt_notional[~elig[t]] = 0.0  # mandatory membership exit
        trade = tgt_notional - cur_notional
        trade = np.where(np.isfinite(o), trade, 0.0)
        exec_notional = np.abs(trade).sum()
        cost = exec_notional * rate
        turn[t] = exec_notional / equity
        trades[t] = int((np.abs(trade) > 1e-9).sum())

        q = np.where(np.isfinite(o) & (o > 0), tgt_notional / np.where(o > 0, o, 1.0), q)
        w_eff = tgt_notional / equity
        gross_exp[t] = np.abs(w_eff).sum()

        r = np.nan_to_num(fwd[t], nan=0.0)
        f = fund[t]
        pp = tgt_notional * r
        fp = -tgt_notional * f
        price_pnl[t] = pp.sum()
        fund_pnl[t] = fp.sum()
        lg = (tgt_notional > 0)
        sg = (tgt_notional < 0)
        long_gross[t] = pp[lg].sum() + fp[lg].sum()
        short_gross[t] = pp[sg].sum() + fp[sg].sum()
        costs[t] = cost
        chg = price_pnl[t] + fund_pnl[t] - cost
        net[t] = chg / equity
        equity += chg
        if equity <= 0:
            raise ValueError(f"insolvent at bar {t}")

    return {
        "net": net,
        "gross_ret": (price_pnl + fund_pnl) / _lag_equity(net),
        "price_pnl": price_pnl,
        "fund_pnl": fund_pnl,
        "long_gross": long_gross,
        "short_gross": short_gross,
        "costs": costs,
        "turnover": turn,
        "trades": trades,
        "gross_exp": gross_exp,
    }


def _lag_equity(net):
    eq = np.empty(len(net))
    eq[0] = 1.0
    np.cumprod(1.0 + net[:-1], out=eq[1:])
    return eq * 100_000.0


def risk_scalars(gross_bar_returns: np.ndarray) -> np.ndarray:
    n = len(gross_bar_returns)
    s = np.ones(n)
    x = gross_bar_returns
    csum = np.concatenate([[0.0], np.cumsum(x)])
    csq = np.concatenate([[0.0], np.cumsum(x * x)])
    for t in range(RISK_LOOKBACK_BARS, n):
        lo = t - RISK_LOOKBACK_BARS
        m = RISK_LOOKBACK_BARS
        mean = (csum[t] - csum[lo]) / m
        var = (csq[t] - csq[lo]) / m - mean * mean
        var = max(var, 0.0)
        sd = math.sqrt(var * m / (m - 1)) * math.sqrt(DAYS_PER_YEAR * BARS_PER_DAY)
        s[t] = 1.0 if sd <= 0 else min(RISK_MAX, max(RISK_MIN, RISK_TARGET / sd))
    return s


def daily(net: np.ndarray, times) -> pd.Series:
    idx = pd.DatetimeIndex(times)
    ser = pd.Series(net, index=idx)
    return (1.0 + ser).groupby(idx.normalize()).prod() - 1.0


def sharpe(x: pd.Series) -> float:
    v = x.dropna().to_numpy(float)
    if v.size < 2:
        return 0.0
    sd = float(np.std(v, ddof=1))
    return 0.0 if sd <= 0 else float(np.mean(v)) / sd * math.sqrt(DAYS_PER_YEAR)


def maxdd(x: pd.Series) -> float:
    v = x.dropna().to_numpy(float)
    if v.size == 0:
        return 0.0
    eq = np.concatenate(([1.0], np.cumprod(1.0 + v)))
    if np.any(eq <= 0):
        return 1.0
    return float(np.max(1.0 - eq / np.maximum.accumulate(eq)))


def _folds(times):
    start = pd.Timestamp(times[0])
    edges = [start] + [IS_END - pd.DateOffset(years=y) for y in (3, 2, 1)] + [IS_END]
    return [(f"F{i+1}", edges[i], edges[i + 1]) for i in range(4)]


def evaluate(panel, W_raw, reb, want_folds=True):
    """Full two-pass evaluation of a raw weight matrix. Returns the metric dict."""
    times = pd.DatetimeIndex(panel["times"], tz="UTC")
    W_req = normalise(W_raw, reb)
    W_ref = cap_rows(W_req)
    ref = _run(panel, W_ref, reb, 1.0)
    s = risk_scalars(ref["gross_ret"])
    W_exec = cap_rows(W_ref * s[:, None])
    out = {}
    res = {}
    for m in (1, 2, 3):
        res[m] = _run(panel, W_exec, reb, float(m))
    for m in (1, 2, 3):
        d = daily(res[m]["net"], times)
        out[f"sharpe_{m}x"] = sharpe(d)
        yrs = max(len(d), 1) / DAYS_PER_YEAR
        growth = float(np.prod(1.0 + d.to_numpy(float)))
        out[f"ret_{m}x"] = growth ** (1 / yrs) - 1 if growth > 0 else -1.0
        out[f"dd_{m}x"] = maxdd(d)
        q = (1.0 + d).groupby(pd.DatetimeIndex(d.index).tz_localize(None).to_period("Q")).prod() - 1
        out[f"posq_{m}x"] = float((q > 0).sum()) / len(q)
        if m == 1:
            out["vol_1x"] = float(np.std(d.to_numpy(float), ddof=1)) * math.sqrt(DAYS_PER_YEAR)
            eq = _lag_equity(res[1]["net"])
            gross_bar = (res[1]["price_pnl"] + res[1]["fund_pnl"]) / eq
            tot_turn = float(res[1]["turnover"].sum())
            out["turnover_1x"] = tot_turn / yrs
            out["gross_edge_bps"] = (
                float(gross_bar.sum()) / tot_turn * 1e4 if tot_turn > 0 else 0.0
            )
            pos_gross = float(np.clip(gross_bar, 0, None).sum())
            cost_frac = float((res[1]["costs"] / eq).sum())
            out["cost_share"] = cost_frac / pos_gross if pos_gross > 0 else 1.0
            ad = d.abs()
            out["top5_share"] = (
                float(ad.nlargest(5).sum()) / float(ad.sum()) if float(ad.sum()) > 0 else 0.0
            )
            out["trades"] = int(res[1]["trades"].sum())
            out["long_gross"] = float((res[1]["long_gross"] / eq).sum())
            out["short_gross"] = float((res[1]["short_gross"] / eq).sum())
            out["fund_pnl_share"] = float((res[1]["fund_pnl"] / eq).sum())
            out["price_pnl_share"] = float((res[1]["price_pnl"] / eq).sum())
            out["mean_gross_exp"] = float(res[1]["gross_exp"].mean())
            out["mean_scalar"] = float(s.mean())
        out[f"calmar_{m}x"] = out[f"ret_{m}x"] / out[f"dd_{m}x"] if out[f"dd_{m}x"] > 0 else 0.0
    if want_folds:
        d2 = daily(res[2]["net"], times)
        d1 = daily(res[1]["net"], times)
        fs, shares = [], []
        pos1 = d1.clip(lower=0)
        tot = float(pos1.sum())
        for _, a, b in _folds(times):
            fs.append(sharpe(d2[(d2.index >= a) & (d2.index < b)]))
            shares.append(
                float(pos1[(pos1.index >= a) & (pos1.index < b)].sum()) / tot if tot > 0 else 0.0
            )
        out["fold_sharpes"] = fs
        out["worst_fold"] = min(fs)
        out["median_fold"] = float(np.median(fs))
        out["pos_folds"] = int(sum(1 for x in fs if x > 0))
        out["max_fold_share"] = max(shares)
    return out


def _dec(x):
    if math.isnan(x):
        return 0.0
    if x >= 0:
        return min(1.0, x)
    return -(-x) / (-x + 1.0)


def g_score(m, confidence=0.90):
    return (
        30 * _dec((m["worst_fold"] + 0.25) / 1.00)
        + 20 * _dec((m["median_fold"] - 0.25) / 0.75)
        + 20 * _dec((0.20 - m["dd_2x"]) / 0.15)
        + 15 * _dec(m["calmar_2x"] / 1.50)
        + 8 * _dec((m["posq_2x"] - 0.50) / 0.375)
        + 7 * _dec((confidence - 0.90) / 0.10)
    )


FLOORS = [
    ("net_sharpe", lambda m: m["sharpe_1x"] >= 0.80, lambda m: m["sharpe_1x"] / 0.80),
    ("dbl_sharpe", lambda m: m["sharpe_2x"] >= 0.50, lambda m: m["sharpe_2x"] / 0.50),
    ("tri_sharpe", lambda m: m["sharpe_3x"] > 0, lambda m: 1.0 if m["sharpe_3x"] > 0 else 0.0),
    ("ret_1x", lambda m: m["ret_1x"] > 0, lambda m: 1.0 if m["ret_1x"] > 0 else 0.0),
    ("ret_2x", lambda m: m["ret_2x"] > 0, lambda m: 1.0 if m["ret_2x"] > 0 else 0.0),
    ("pos_folds", lambda m: m["pos_folds"] >= 3, lambda m: m["pos_folds"] / 3.0),
    ("turnover", lambda m: m["turnover_1x"] <= 25.0, lambda m: 2 - m["turnover_1x"] / 25.0),
    ("gross_edge", lambda m: m["gross_edge_bps"] >= 40.0, lambda m: m["gross_edge_bps"] / 40.0),
    ("cost_share", lambda m: m["cost_share"] <= 0.30, lambda m: 2 - m["cost_share"] / 0.30),
    ("top5", lambda m: m["top5_share"] <= 0.35, lambda m: 2 - m["top5_share"] / 0.35),
    ("fold_share", lambda m: m["max_fold_share"] <= 0.60, lambda m: 2 - m["max_fold_share"] / 0.6),
    ("long_pnl", lambda m: m["long_gross"] > 0, lambda m: 1.0 if m["long_gross"] > 0 else 0.0),
    ("short_pnl", lambda m: m["short_gross"] > 0, lambda m: 1.0 if m["short_gross"] > 0 else 0.0),
]


def compliance(m):
    c = [min(1.0, max(0.0, credit(m))) if not ok(m) else 1.0 for _, ok, credit in FLOORS]
    return float(np.mean(c))


def failed_floors(m):
    return [name for name, ok, _ in FLOORS if not ok(m)]


def summary(m, confidence=0.90):
    g = g_score(m, confidence)
    return {
        "G": g,
        "G_eff": g * compliance(m),
        "compliance": compliance(m),
        "sh1": m["sharpe_1x"],
        "sh2": m["sharpe_2x"],
        "sh3": m["sharpe_3x"],
        "worst": m["worst_fold"],
        "median": m["median_fold"],
        "dd2": m["dd_2x"],
        "dd1": m["dd_1x"],
        "cal2": m["calmar_2x"],
        "posq2": m["posq_2x"],
        "vol": m["vol_1x"],
        "turn": m["turnover_1x"],
        "edge": m["gross_edge_bps"],
        "costsh": m["cost_share"],
        "trades": m["trades"],
        "L": m["long_gross"],
        "S": m["short_gross"],
        "fund": m["fund_pnl_share"],
        "folds": [round(x, 2) for x in m["fold_sharpes"]],
        "fails": failed_floors(m),
    }
