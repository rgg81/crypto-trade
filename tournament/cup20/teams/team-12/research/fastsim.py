"""Fast numpy re-implementation of the organiser's evaluator core, for offline exploration only.

It is NOT a scorer. Every number of record comes from scripts/cup20_evaluate.py. This exists so
sleeve design can be explored over the full window thousands of times without spending a trial,
and it is validated against the organiser's own evaluate_targets in validate_fastsim.py.

Modelled: boundary funding on the carried book, next-open fills, per-side fee+slippage at the
cost multiplier, holding-period funding, membership forced exits, terminal close-out, the three
section-4 exposure caps applied by uniform reduction at both ends of the common risk unit, and
the common risk unit itself (trailing-90d gross-return volatility, clamp 0.20..3.0).
Not modelled: per-bar participation caps, delisting 100% haircuts, declared risk policies.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

FEE = 5.0 / 10_000.0
SLIP = 2.5 / 10_000.0
MAX_GROSS = 1.0
MAX_NET = 1.0
MAX_SYMBOL = 0.20
BARS_PER_YEAR = 365 * 24 / 8
DAYS_PER_YEAR = 365.0


def cap_rows(W: np.ndarray) -> np.ndarray:
    """One uniform per-row reduction until the gross/net/symbol caps hold. Never redistributes."""
    gross = np.abs(W).sum(axis=1)
    net = np.abs(W.sum(axis=1))
    sym = np.abs(W).max(axis=1) if W.shape[1] else np.zeros(len(W))
    scale = np.ones(len(W))
    for mag, ceil in ((gross, MAX_GROSS), (net, MAX_NET), (sym, MAX_SYMBOL)):
        breach = mag > ceil + 1e-12
        cand = np.ones(len(W))
        cand[breach] = ceil / mag[breach]
        scale = np.minimum(scale, cand)
    return W * scale[:, None]


def normalise_unit_gross(W: np.ndarray, rebal: np.ndarray) -> np.ndarray:
    g = np.abs(W).sum(axis=1)
    d = np.where(g > 0.0, g, 1.0)
    out = W / d[:, None]
    out[~rebal] = 0.0
    return out


def simulate(
    W: np.ndarray,
    rebal: np.ndarray,
    panel,
    *,
    cost_multiplier: float = 1.0,
    initial_equity: float = 100_000.0,
    participation: float = 0.001,
):
    """Run the executed book. W rows are target weights already scaled and capped."""
    t0 = panel.t0
    n = len(panel.times)
    op = panel.open[t0 : t0 + n + 1]
    cl = panel.close[t0 : t0 + n]
    mk = panel.mark[t0 : t0 + n]
    fat = panel.fund_at[t0 : t0 + n]
    faf = panel.fund_after[t0 : t0 + n]
    elig = panel.eligible[t0 : t0 + n]
    qv = panel.quote_volume
    qv_trail3 = np.nan_to_num(qv[t0 - 3 : t0 + n - 3]) + np.nan_to_num(qv[t0 - 2 : t0 + n - 2]) \
        + np.nan_to_num(qv[t0 - 1 : t0 + n - 1])
    qv_now = np.nan_to_num(qv[t0 : t0 + n])
    ns = W.shape[1]

    q = np.zeros(ns)
    equity = initial_equity
    rate = (FEE + SLIP) * cost_multiplier
    fee_rate = FEE * cost_multiplier
    slip_rate = SLIP * cost_multiplier

    net_ret = np.empty(n); price_pnl = np.empty(n); fund_pnl = np.empty(n)
    long_price = np.empty(n); short_price = np.empty(n)
    long_fund = np.empty(n); short_fund = np.empty(n)
    fees_arr = np.empty(n); slip_arr = np.empty(n); turn = np.empty(n)
    eq_arr = np.empty(n)
    trades = 0

    for i in range(n):
        terminal = i == n - 1
        eq0 = equity
        qb = q
        f_at = -float(np.dot(qb, np.nan_to_num(fat[i])))
        long_f = -float(np.dot(np.where(qb > 0, qb, 0.0), np.nan_to_num(fat[i])))
        short_f = -float(np.dot(np.where(qb < 0, qb, 0.0), np.nan_to_num(fat[i])))
        eq_af = eq0 + f_at

        mask = elig[i]
        mkt = mk[i]
        opt = op[i]
        cap = qv_trail3[i] * participation
        if rebal[i]:
            w = np.where(mask, W[i], 0.0)
            desired = np.nan_to_num(w * eq_af / np.where(np.isfinite(mkt) & (mkt > 0), mkt, np.inf))
        else:
            desired = np.where(mask, q, 0.0)
        req = desired - q
        req = np.where(np.isfinite(opt) & (opt > 0), req, 0.0)
        req_not = req * np.nan_to_num(opt)
        fill_not = np.clip(req_not, -cap, cap)
        executed = float(np.abs(fill_not).sum())
        trades += int((np.abs(fill_not) > 0).sum())
        q = q + np.nan_to_num(fill_not / np.where(np.isfinite(opt) & (opt > 0), opt, np.inf))

        eq_after_costs = eq_af - executed * rate
        held = np.nan_to_num(q * mkt) / eq_after_costs
        s = 1.0
        for mag, ceil in ((np.abs(held).sum(), MAX_GROSS), (abs(held.sum()), MAX_NET),
                          (np.abs(held).max() if ns else 0.0, MAX_SYMBOL)):
            if mag > ceil:
                s = min(s, ceil / mag)
        rr_not = np.zeros(ns)
        if s < 1.0:
            rem = np.clip(cap - np.abs(fill_not), 0.0, None)
            rr_req = np.nan_to_num(q * (s - 1.0) * np.nan_to_num(opt))
            rr_not = np.clip(rr_req, -rem, rem)
            executed += float(np.abs(rr_not).sum())
            trades += int((np.abs(rr_not) > 0).sum())
            q = q + np.nan_to_num(rr_not / np.where(np.isfinite(opt) & (opt > 0), opt, np.inf))

        fees = executed * fee_rate
        slips = executed * slip_rate

        nxt = op[i + 1] if i + 1 < len(op) else np.full(ns, np.nan)
        dp = nxt - opt
        forced = (q != 0) & (~np.isfinite(dp)) & np.isfinite(opt) & np.isfinite(cl[i])
        if terminal:
            forced = (q != 0) & np.isfinite(opt) & np.isfinite(cl[i])
        dp = np.where(forced, cl[i] - opt, dp)
        dp = np.nan_to_num(dp)
        pp = q * dp
        ppl = float(pp[q > 0].sum()); pps = float(pp[q < 0].sum()); pp_tot = float(pp.sum())

        f_af = -float(np.dot(q, np.nan_to_num(faf[i])))
        lf2 = -float(np.dot(np.where(q > 0, q, 0.0), np.nan_to_num(faf[i])))
        sf2 = -float(np.dot(np.where(q < 0, q, 0.0), np.nan_to_num(faf[i])))

        fx_not = 0.0
        if forced.any():
            fx_req = np.where(forced, -q * np.nan_to_num(cl[i]), 0.0)
            cur_exec = np.abs(fill_not) + np.abs(rr_not)
            fx_cap = np.clip(qv_now[i] * participation - cur_exec, 0.0, None)
            fx_fill = np.clip(fx_req, -fx_cap, fx_cap)
            fx_not = float(np.abs(fx_fill).sum())
            trades += int((np.abs(fx_fill) > 0).sum())
            fx_qty = np.nan_to_num(fx_fill / np.where(cl[i] > 0, cl[i], np.inf))
            resid = np.where(forced, q + fx_qty, 0.0)
            resid = np.where(np.abs(resid) < 1e-12, 0.0, resid)
            if not terminal:
                hair = float(np.abs(resid * np.nan_to_num(cl[i])).sum())
                hl = float(np.abs(np.where(resid > 0, resid, 0.0) * np.nan_to_num(cl[i])).sum())
                hs = float(np.abs(np.where(resid < 0, resid, 0.0) * np.nan_to_num(cl[i])).sum())
                pp_tot -= hair; ppl -= hl; pps -= hs
            fees += fx_not * fee_rate
            slips += fx_not * slip_rate

        change = f_at + pp_tot + f_af - fees - slips
        equity = eq0 + change
        net_ret[i] = change / eq0
        price_pnl[i] = pp_tot / eq0
        fund_pnl[i] = (f_at + f_af) / eq0
        long_price[i] = ppl / eq0
        short_price[i] = pps / eq0
        long_fund[i] = (long_f + lf2) / eq0
        short_fund[i] = (short_f + sf2) / eq0
        fees_arr[i] = fees / eq0
        slip_arr[i] = slips / eq0
        turn[i] = (executed + fx_not) / eq0
        eq_arr[i] = equity
        q = np.where(forced, 0.0, q)

    return {
        "net_return": net_ret, "price_pnl": price_pnl, "funding_pnl": fund_pnl,
        "long_price_pnl": long_price, "short_price_pnl": short_price,
        "long_funding_pnl": long_fund, "short_funding_pnl": short_fund,
        "fees": fees_arr, "slippage": slip_arr, "turnover": turn,
        "trade_count": trades, "equity": eq_arr,
    }


def daily(net: np.ndarray, times: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(net, index=times)
    return (1.0 + s).groupby(times.normalize()).prod() - 1.0


def sharpe(d: pd.Series) -> float:
    v = d.dropna().to_numpy(dtype=float)
    if v.size < 2:
        return 0.0
    sd = float(np.std(v, ddof=1))
    if sd <= 0:
        return 0.0
    return float(np.mean(v)) / sd * math.sqrt(DAYS_PER_YEAR)


def max_dd(d: pd.Series) -> float:
    v = d.dropna().to_numpy(dtype=float)
    if v.size == 0:
        return 0.0
    eq = np.concatenate(([1.0], np.cumprod(1.0 + v)))
    if np.any(eq <= 0):
        return 1.0
    return float(np.max(1.0 - eq / np.maximum.accumulate(eq)))


def run_book(W_raw: np.ndarray, rebal: np.ndarray, panel, cost_levels=(1, 2, 3)):
    """Full two-pass pipeline: normalise, cap, reference pass, risk unit, cap, score."""
    req = normalise_unit_gross(W_raw, rebal)
    tgt = cap_rows(req)
    ref = simulate(tgt, rebal, panel, cost_multiplier=1.0)
    gross = ref["price_pnl"] + ref["funding_pnl"]
    required = max(2, math.ceil(90 * 24 / 8))
    s = np.ones(len(gross))
    for i in range(len(gross)):
        if i < required:
            s[i] = 1.0
            continue
        win = gross[i - required : i]
        realized = float(np.std(win, ddof=1)) * math.sqrt(BARS_PER_YEAR)
        s[i] = 3.0 if realized <= 0 else min(3.0, max(0.20, 0.10 / realized))
    scaled = cap_rows(tgt * s[:, None])
    out = {}
    for c in cost_levels:
        out[c] = simulate(scaled, rebal, panel, cost_multiplier=float(c))
    return {"scalars": s, "reference": ref, "results": out, "targets": scaled}
