"""A fast offline replica of the organiser's two-pass evaluation.

Written by reading ``crypto_trade.cup20.runner``, ``crypto_trade.cup20.risk_unit`` and
``crypto_trade.tournament.engine_v2`` line by line, and restricted to the case this team actually
uses: a declared risk policy that is entirely inert (every primitive disabled), which is the branch
``evaluate_targets`` skips wholesale when ``risk_policy`` carries no enabled primitive.

Its only purpose is unlimited offline exploration. Not one number it produces is reported as a
result: every scored number in the certificate comes from ``scripts/cup20_evaluate.py`` under a
journaled trial. ``calibrate.py`` measures the residual against the organiser's own modules.
"""

from __future__ import annotations

import math

import numpy as np

DAYS_PER_YEAR = 365.0
FEE_BPS = 5.0
SLIP_BPS = 2.5
MAX_GROSS = 1.0
MAX_NET = 1.0
MAX_SYMBOL = 0.20
MAX_PARTICIPATION = 0.001
INITIAL_EQUITY = 100_000.0
CAP_TOL = 1e-12


def _cap_scale(wm: np.ndarray) -> np.ndarray:
    """One uniform per-row reduction factor until gross/net/symbol caps hold."""
    gross = np.abs(wm).sum(1)
    net = np.abs(wm.sum(1))
    sym = np.abs(wm).max(1) if wm.shape[1] else np.zeros(len(wm))
    scale = np.ones(len(wm))
    for magnitude, ceiling in ((gross, MAX_GROSS), (net, MAX_NET), (sym, MAX_SYMBOL)):
        breached = magnitude > ceiling + CAP_TOL
        cand = np.ones(len(wm))
        with np.errstate(divide="ignore", invalid="ignore"):
            cand[breached] = ceiling / magnitude[breached]
        scale = np.minimum(scale, cand)
    return scale


def normalise_and_cap(weights: np.ndarray, rebalance: np.ndarray):
    """Unit-gross normalisation then the section 4 caps; returns (capped, requested_scale)."""
    w = np.nan_to_num(weights, nan=0.0)
    gross = np.abs(w).sum(1)
    div = np.where(gross > 0.0, gross, 1.0)
    req = w / div[:, None]
    scale = _cap_scale(req)
    return req * scale[:, None], scale


class FastSim:
    """One evaluation pass, quantity-carrying, matching ``evaluate_targets``'s arithmetic."""

    def __init__(self, panel, start_idx: int):
        self.p = panel
        self.s = start_idx
        sl = slice(start_idx, len(panel.times))
        self.open = panel.open[sl]
        self.close = panel.close[sl]
        self.mark = panel.mark[sl]
        self.qv = np.nan_to_num(panel.quote_volume[sl])
        self.fund_at = panel.fund_at_cash[sl]
        self.fund_mid = panel.fund_mid_cash[sl]
        self.eligible = panel.eligible[sl]
        self.n, self.k = self.open.shape
        # rolling 3-bar quote volume strictly before each row (ceil(24/8) = 3)
        cs = np.cumsum(self.qv, axis=0)
        hist = np.zeros_like(self.qv)
        for t in range(1, self.n):
            lo = max(0, t - 3)
            hist[t] = cs[t - 1] - (cs[lo - 1] if lo >= 1 else 0.0)
        self.cap_notional = hist * MAX_PARTICIPATION

    def run(self, targets: np.ndarray, rebalance: np.ndarray, cost_mult: float) -> dict:
        p_open, p_close, p_mark = self.open, self.close, self.mark
        elig = self.eligible
        n, k = self.n, self.k
        q = np.zeros(k)
        equity = INITIAL_EQUITY
        cost_rate = (FEE_BPS + SLIP_BPS) / 10_000.0 * cost_mult
        gross_r = np.zeros(n)
        net_r = np.zeros(n)
        fund_r = np.zeros(n)
        cost_r = np.zeros(n)
        turn = np.zeros(n)
        long_g = np.zeros(n)
        short_g = np.zeros(n)
        trades = 0
        eq_path = np.zeros(n)
        for t in range(n):
            terminal = t == n - 1
            o = p_open[t]
            mk = p_mark[t]
            c = p_close[t]
            nxt = p_open[t + 1] if not terminal else np.full(k, np.nan)
            eq0 = equity
            qb = q.copy()
            fund_at_usd = float(-(qb * self.fund_at[t]).sum())
            eq_after_f = equity + fund_at_usd
            fillable = np.isfinite(o)
            eligible = elig[t] & fillable
            cap = self.cap_notional[t]
            if rebalance[t]:
                desired = np.where(eligible, np.nan_to_num(targets[t]), 0.0)
                dq = desired * eq_after_f / np.where(np.isfinite(mk) & (mk > 0), mk, np.nan)
                dq = np.nan_to_num(dq)
                req_q = dq - q
            else:
                req_q = np.where(~eligible, -q, 0.0)
            req_n = np.nan_to_num(req_q * o)
            filled_n = np.clip(req_n, -cap, cap)
            fq = np.divide(filled_n, o, out=np.zeros(k), where=np.isfinite(o) & (o != 0))
            q = q + fq
            executed = float(np.abs(filled_n).sum())
            trades += int((np.abs(filled_n) > 0).sum())
            eq_after_cost = eq_after_f - executed * cost_rate
            # central exposure caps on the held book, applied cost-aware and by reduction only
            marked = np.nan_to_num(q * mk)
            risk_n = 0.0
            if _cap_scale((marked / max(eq_after_cost, 1e-9))[None, :])[0] < 1.0 - 1e-12:
                liq = float(np.abs(np.nan_to_num(q * o)).sum())
                lo_s, hi_s = 0.0, 1.0
                for _ in range(60):
                    mid_s = 0.5 * (lo_s + hi_s)
                    post = eq_after_cost - cost_rate * liq * (1.0 - mid_s)
                    ok = post > 0 and _cap_scale((marked * mid_s / post)[None, :])[0] >= 1.0 - 1e-12
                    if ok:
                        lo_s = mid_s
                    else:
                        hi_s = mid_s
                sc = lo_s
                rn = np.nan_to_num(q * (sc - 1.0) * o)
                rem = np.clip(cap - np.abs(filled_n), 0.0, None)
                rn = np.clip(rn, -rem, rem)
                q = q + np.divide(rn, o, out=np.zeros(k), where=np.isfinite(o) & (o != 0))
                risk_n = float(np.abs(rn).sum())
                executed += risk_n
                trades += int((np.abs(rn) > 0).sum())
            fee = executed * FEE_BPS / 10_000.0 * cost_mult
            slip = executed * SLIP_BPS / 10_000.0 * cost_mult
            dpx = nxt - o
            forced = (q != 0) & ~np.isfinite(dpx) & np.isfinite(o) & np.isfinite(c)
            if terminal:
                forced = (q != 0) & np.isfinite(o) & np.isfinite(c)
            dpx = np.where(forced, c - o, dpx)
            dpx = np.nan_to_num(dpx)
            pnl = q * dpx
            price_pnl = float(pnl.sum())
            lp = float(pnl[q > 0].sum())
            sp = float(pnl[q < 0].sum())
            # forced exits at the last executable close, sharing the bar participation budget
            fe_req = np.where(forced, -q * np.nan_to_num(c), 0.0)
            fe_cap = np.clip(self.qv[t] * MAX_PARTICIPATION - np.abs(filled_n), 0.0, None)
            fe_fill = np.clip(fe_req, -fe_cap, fe_cap)
            fe_notional = float(np.abs(fe_fill).sum())
            fq2 = np.divide(fe_fill, c, out=np.zeros(k), where=np.isfinite(c) & (c != 0))
            residual = np.where(forced, q + fq2, 0.0)
            residual = np.where(np.abs(residual) < 1e-12, 0.0, residual)
            if not terminal:
                haircut = float((np.abs(residual) * np.nan_to_num(c)).sum())
                price_pnl -= haircut
                lp -= float((np.where(residual > 0, residual, 0.0) * np.nan_to_num(c)).sum())
                sp -= float((np.where(residual < 0, -residual, 0.0) * np.nan_to_num(c)).sum())
            fee += fe_notional * FEE_BPS / 10_000.0 * cost_mult
            slip += fe_notional * SLIP_BPS / 10_000.0 * cost_mult
            trades += int((np.abs(fe_fill) > 0).sum())
            f_next = self.fund_at[t + 1] if not terminal else np.zeros(k)
            qf = np.where(forced, q, 0.0)
            fund_forced = float(-(qf * f_next).sum())
            fund_hold = float(-(q * self.fund_mid[t]).sum())
            total_fund = fund_at_usd + fund_forced + fund_hold
            lf = float(-(np.where(qb > 0, qb, 0.0) * self.fund_at[t]).sum()
                       - (np.where(q > 0, q, 0.0) * self.fund_mid[t]).sum()
                       - (np.where(qf > 0, qf, 0.0) * f_next).sum())
            sf = float(-(np.where(qb < 0, qb, 0.0) * self.fund_at[t]).sum()
                       - (np.where(q < 0, q, 0.0) * self.fund_mid[t]).sum()
                       - (np.where(qf < 0, qf, 0.0) * f_next).sum())
            lp += lf
            sp += sf
            net_change = total_fund + price_pnl - fee - slip
            equity = eq0 + net_change
            if equity <= 0:
                equity = 1e-6
            gross_r[t] = (price_pnl + total_fund) / eq0
            fund_r[t] = total_fund / eq0
            net_r[t] = net_change / eq0
            cost_r[t] = (fee + slip) / eq0
            turn[t] = (executed + fe_notional) / eq0
            long_g[t] = lp / eq0
            short_g[t] = sp / eq0
            eq_path[t] = equity
            q = np.where(forced, 0.0, q)
        return {
            "gross": gross_r,
            "net": net_r,
            "funding": fund_r,
            "cost": cost_r,
            "turnover": turn,
            "long_gross": long_g,
            "short_gross": short_g,
            "trades": trades,
            "equity": eq_path,
        }


def risk_scalars(gross: np.ndarray, times, lookback_days: int = 90,
                 target: float = 0.10, interval_hours: int = 8) -> np.ndarray:
    """clamp(0.10 / sigma_t, 0.20, 3.0) on the trailing 90 days of the reference book's gross
    bar returns, using rows strictly before t."""
    per_year = DAYS_PER_YEAR * 24.0 / interval_hours
    bars = int(round(lookback_days * 24.0 / interval_hours))
    out = np.ones(len(gross))
    for t in range(len(gross)):
        lo = t - bars
        if lo < 0:
            continue
        v = gross[lo:t]
        if len(v) < bars:
            continue
        sd = float(np.std(v, ddof=1))
        if sd <= 0:
            continue
        sigma = sd * math.sqrt(per_year)
        out[t] = min(max(target / sigma, 0.20), 3.0)
    return out


def daily(net: np.ndarray, times) -> tuple[np.ndarray, np.ndarray]:
    days = times.normalize()
    uniq, inv = np.unique(days.to_numpy(), return_inverse=True)
    out = np.ones(len(uniq))
    np.multiply.at(out, inv, 1.0 + net)
    return uniq, out - 1.0


def metrics(res: dict, times) -> dict:
    d_index, d = daily(res["net"], times)
    ndays = max(len(d), 1)
    years = ndays / DAYS_PER_YEAR
    growth = float(np.prod(1.0 + d))
    ann_ret = growth ** (1.0 / years) - 1.0 if growth > 0 else -1.0
    sd = float(np.std(d, ddof=1)) if len(d) > 1 else 0.0
    sharpe = float(np.mean(d)) / sd * math.sqrt(DAYS_PER_YEAR) if sd > 0 else 0.0
    eq = np.concatenate(([1.0], np.cumprod(1.0 + d)))
    peaks = np.maximum.accumulate(eq)
    mdd = float(np.max(1.0 - eq / peaks)) if np.all(eq > 0) else 1.0
    total_turn = float(res["turnover"].sum())
    gross_total = float(res["gross"].sum())
    pos_gross = float(np.clip(res["gross"], 0.0, None).sum())
    costs = float(res["cost"].sum())
    absd = np.abs(d)
    return {
        "sharpe": sharpe,
        "ann_return": ann_ret,
        "ann_vol": sd * math.sqrt(DAYS_PER_YEAR) if len(d) > 1 else 0.0,
        "max_dd": mdd,
        "calmar": ann_ret / mdd if mdd > 0 else (1000.0 if ann_ret > 0 else 0.0),
        "ann_turnover": total_turn / years if years > 0 else 0.0,
        "gross_edge_bps": gross_total / total_turn * 1e4 if total_turn > 0 else 0.0,
        "cost_share": costs / pos_gross if pos_gross > 0 else 1.0,
        "top5_share": float(np.sort(absd)[-5:].sum() / absd.sum()) if absd.sum() > 0 else 0.0,
        "long_gross": float(res["long_gross"].sum()),
        "short_gross": float(res["short_gross"].sum()),
        "trades": res["trades"],
        "daily_index": d_index,
        "daily": d,
    }


def full_evaluate(panel, start_idx: int, weights: np.ndarray, rebalance: np.ndarray,
                  levels=(1, 2, 3)) -> dict:
    sim = FastSim(panel, start_idx)
    times = panel.times[start_idx:]
    capped, req_scale = normalise_and_cap(weights, rebalance)
    ref = sim.run(capped, rebalance, 1.0)
    s = risk_scalars(ref["gross"], times)
    scaled = capped * s[:, None]
    sc2 = _cap_scale(scaled)
    executed = scaled * sc2[:, None]
    out = {"requested_min_scale": float(req_scale[rebalance].min()) if rebalance.any() else 1.0,
           "executed_min_scale": float(sc2[rebalance].min()) if rebalance.any() else 1.0,
           "risk_scalar_mean": float(s.mean())}
    for lv in levels:
        r = sim.run(executed, rebalance, float(lv))
        out[lv] = metrics(r, times)
    return out
