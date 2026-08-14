"""Fast offline replica of the organiser's two-pass evaluator, for team-10 research only.

This is NOT a scorer. Nothing here produces a tournament number; the organiser's harness does
that, and every number in the certificate that is called a measurement came out of it. What this
buys is the ability to run thousands of full-window simulations before spending a trial, which is
the only way to explore an axis honestly under a twelve-trial budget.

Faithfulness targets, read out of ``crypto_trade.tournament.engine_v2`` and
``crypto_trade.cup20.runner``:

* fills at the boundary open, quantities sized off the boundary MARK, PnL earned open-to-open;
* funding split into the settlement exactly at the boundary (paid by the carried position, before
  the rebalance) and settlements strictly inside the bar (paid by the post-rebalance position);
* 5 bps fee + 2.5 bps slippage per side on executed notional, at 1x / 2x / 3x;
* per-symbol participation cap of 0.1% of the trailing three bars' quote volume;
* unit-gross normalisation of every explicit rebalance row, then the section-4 caps by one uniform
  per-boundary reduction, applied both before and after the common risk unit;
* the risk unit itself: s_t = clamp(0.10 / sigma_t, 0.20, 3.0) off the reference book's trailing
  90-day GROSS bar returns, rows strictly before t.

Deliberately omitted, because team-10 declares a flat risk policy: position stops, time stops,
turnover limits, drawdown brakes, side scaling. With every primitive disabled the organiser's
policy path is a no-op, so omitting it changes nothing.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from panel import Panel

FEE_BPS = 5.0
SLIP_BPS = 2.5
COST_RATE = (FEE_BPS + SLIP_BPS) / 10_000.0
MAX_GROSS = 1.0
MAX_NET = 1.0
MAX_SYMBOL = 0.20
PARTICIPATION = 0.001
INITIAL_EQUITY = 100_000.0
BARS_PER_DAY = 3
DAYS_PER_YEAR = 365.0
RISK_TARGET = 0.10
RISK_LOOKBACK_BARS = 270  # 90 days of 8h bars
RISK_MIN, RISK_MAX = 0.20, 3.0


def cap_scale(w: np.ndarray) -> np.ndarray:
    """One uniform per-row reduction until gross, |net| and per-symbol caps hold."""
    gross = np.abs(w).sum(axis=1)
    net = np.abs(w.sum(axis=1))
    largest = np.abs(w).max(axis=1) if w.shape[1] else np.zeros(len(w))
    scale = np.ones(len(w))
    for magnitude, ceiling in ((gross, MAX_GROSS), (net, MAX_NET), (largest, MAX_SYMBOL)):
        breached = magnitude > ceiling + 1e-12
        candidate = np.ones(len(w))
        candidate[breached] = ceiling / magnitude[breached]
        scale = np.minimum(scale, candidate)
    return scale


def normalise_unit_gross(w: np.ndarray, rebalance: np.ndarray) -> np.ndarray:
    out = w.copy()
    gross = np.abs(out).sum(axis=1)
    divisor = np.where(gross > 0.0, gross, 1.0)
    out = out / divisor[:, None]
    out[~rebalance] = 0.0
    return out


@dataclasses.dataclass
class PassResult:
    net: np.ndarray  # (T,) net bar return on start-of-bar equity
    gross: np.ndarray  # (T,) price + funding, on start-of-bar equity
    turnover: np.ndarray  # (T,)
    fees: np.ndarray
    long_gross: np.ndarray
    short_gross: np.ndarray
    trades: int
    equity: np.ndarray


def _evaluate(
    p: Panel,
    weights: np.ndarray,
    rebalance: np.ndarray,
    cost_multiplier: float,
) -> PassResult:
    """One evaluator pass over the whole grid with the given (already capped) target weights."""
    T, S = weights.shape
    op, mk, cl = p.open, p.mark, p.close
    qv = p.quote_volume
    fund_at, fund_in = p.fund_at, p.fund_in
    elig = p.eligible

    # Participation capacity: 0.1% of the trailing three bars' quote volume, strictly before t.
    trail = np.zeros_like(qv)
    csum = np.cumsum(np.nan_to_num(qv), axis=0)
    trail[3:] = csum[2:-1] - csum[:-3]
    trail[1] = csum[0]
    trail[2] = csum[1]
    cap_notional = trail * PARTICIPATION

    qty = np.zeros(S)
    equity = INITIAL_EQUITY
    rate = COST_RATE * cost_multiplier
    fee_rate = FEE_BPS / 10_000.0 * cost_multiplier
    slip_rate = SLIP_BPS / 10_000.0 * cost_multiplier

    net_r = np.zeros(T)
    gross_r = np.zeros(T)
    turn = np.zeros(T)
    fee_r = np.zeros(T)
    long_g = np.zeros(T)
    short_g = np.zeros(T)
    eq_path = np.zeros(T)
    trades = 0

    open_t = op
    for t in range(T):
        terminal = t == T - 1
        o = open_t[t]
        m = mk[t]
        c = cl[t]
        nxt = np.full(S, np.nan) if terminal else open_t[t + 1]
        eq0 = equity

        qty_before = qty
        f_at = -float(np.dot(np.nan_to_num(qty_before), fund_at[t]))
        eq_after_funding = equity + f_at

        el = elig[t]
        if rebalance[t]:
            desired_w = np.where(el, weights[t], 0.0)
            desired_notional = desired_w * eq_after_funding
            desired_qty = np.where(np.isnan(m), 0.0, desired_notional / np.where(np.isnan(m), 1.0, m))
            req_qty = desired_qty - qty
        else:
            req_qty = np.where(~el, -qty, 0.0)

        req_notional = np.nan_to_num(req_qty * o)
        cap = cap_notional[t]
        filled_notional = np.clip(req_notional, -cap, cap)
        fill_qty = np.where(np.isnan(o) | (o == 0), 0.0, filled_notional / np.where(np.isnan(o), 1.0, o))
        qty = qty + fill_qty
        executed = float(np.abs(filled_notional).sum())
        trades += int((np.abs(filled_notional) > 0.0).sum())

        # Central exposure caps on the realised book (reduction only, cost-aware in the organiser;
        # a simple scale here, since a flat-policy book of ours is capped by construction upstream).
        eq_after_costs = eq_after_funding - executed * rate
        held_w = np.nan_to_num(qty * m) / eq_after_costs
        gross = np.abs(held_w).sum()
        netx = abs(held_w.sum())
        big = np.abs(held_w).max() if S else 0.0
        rscale = 1.0
        for magnitude, ceiling in ((gross, MAX_GROSS), (netx, MAX_NET), (big, MAX_SYMBOL)):
            if magnitude > ceiling:
                rscale = min(rscale, ceiling / magnitude)
        red_notional = np.zeros(S)
        if rscale < 1.0:
            red_qty = qty * (rscale - 1.0)
            red_notional = np.nan_to_num(red_qty * o)
            remaining = np.clip(cap - np.abs(filled_notional), 0.0, None)
            red_notional = np.clip(red_notional, -remaining, remaining)
            qty = qty + np.where(np.isnan(o) | (o == 0), 0.0, red_notional / np.where(np.isnan(o), 1.0, o))
            executed += float(np.abs(red_notional).sum())
            trades += int((np.abs(red_notional) > 0.0).sum())

        price_change = nxt - o
        forced = (qty != 0.0) & np.isnan(price_change) & ~np.isnan(o) & ~np.isnan(c)
        if terminal:
            forced = (qty != 0.0) & ~np.isnan(o) & ~np.isnan(c)
        price_change = np.where(forced, c - o, price_change)
        price_change = np.nan_to_num(price_change)

        pnl_by_symbol = qty * price_change
        price_pnl = float(pnl_by_symbol.sum())
        long_pnl = float(pnl_by_symbol[qty > 0].sum())
        short_pnl = float(pnl_by_symbol[qty < 0].sum())

        f_in = -float(np.dot(np.nan_to_num(qty), fund_in[t]))
        long_f = -float(np.dot(np.nan_to_num(np.where(qty_before > 0, qty_before, 0.0)), fund_at[t])) - float(
            np.dot(np.nan_to_num(np.where(qty > 0, qty, 0.0)), fund_in[t])
        )
        short_f = -float(np.dot(np.nan_to_num(np.where(qty_before < 0, qty_before, 0.0)), fund_at[t])) - float(
            np.dot(np.nan_to_num(np.where(qty < 0, qty, 0.0)), fund_in[t])
        )

        # Forced exits at the last executable close, sharing the bar's participation allowance.
        forced_notional = 0.0
        residual = np.zeros(S)
        if forced.any():
            req_close = np.where(forced, -qty * np.nan_to_num(c), 0.0)
            close_cap = np.clip(np.nan_to_num(qv[t]) * PARTICIPATION - (np.abs(filled_notional) + np.abs(red_notional)), 0.0, None)
            filled_close = np.clip(req_close, -close_cap, close_cap)
            fq = np.where(np.isnan(c) | (c == 0), 0.0, filled_close / np.where(np.isnan(c), 1.0, c))
            residual = np.where(forced, qty + fq, 0.0)
            residual = np.where(np.abs(residual) < 1e-12, 0.0, residual)
            forced_notional = float(np.abs(filled_close).sum())
            trades += int((np.abs(filled_close) > 0.0).sum())
            if not terminal:
                haircut = float((np.abs(residual) * np.nan_to_num(c)).sum())
                price_pnl -= haircut
                long_pnl -= float((np.where(residual > 0, residual, 0.0) * np.nan_to_num(c)).sum())
                short_pnl -= float((np.where(residual < 0, -residual, 0.0) * np.nan_to_num(c)).sum())

        total_exec = executed + forced_notional
        fee_usd = total_exec * fee_rate
        slip_usd = total_exec * slip_rate
        net_change = f_at + price_pnl + f_in - fee_usd - slip_usd
        equity = eq0 + net_change
        if equity <= 0:
            equity = 1e-9

        net_r[t] = net_change / eq0
        gross_r[t] = (f_at + price_pnl + f_in) / eq0
        turn[t] = total_exec / eq0
        fee_r[t] = (fee_usd + slip_usd) / eq0
        long_g[t] = (long_pnl + long_f) / eq0
        short_g[t] = (short_pnl + short_f) / eq0
        eq_path[t] = equity

        qty = np.where(forced, 0.0, qty)

    return PassResult(net_r, gross_r, turn, fee_r, long_g, short_g, trades, eq_path)


def risk_scalars(gross: np.ndarray) -> np.ndarray:
    """clamp(0.10 / sigma_t, 0.20, 3.0) from rows strictly before t, 90-day trailing."""
    T = len(gross)
    out = np.ones(T)
    ann = math.sqrt(365 * 24 / 8)
    csum = np.concatenate(([0.0], np.cumsum(gross)))
    csum2 = np.concatenate(([0.0], np.cumsum(gross * gross)))
    n = RISK_LOOKBACK_BARS
    for t in range(n, T):
        s1 = csum[t] - csum[t - n]
        s2 = csum2[t] - csum2[t - n]
        var = (s2 - s1 * s1 / n) / (n - 1)
        sd = math.sqrt(max(var, 0.0)) * ann
        out[t] = RISK_MAX if sd <= 0 else min(RISK_MAX, max(RISK_MIN, RISK_TARGET / sd))
    return out


@dataclasses.dataclass
class SimResult:
    metrics: dict[str, float]
    daily: dict[int, pd.Series]
    fold_sharpe: dict[str, float]
    scalars: np.ndarray
    reference_net: np.ndarray


def _daily(times: pd.DatetimeIndex, net: np.ndarray) -> pd.Series:
    s = pd.Series(net, index=times)
    return (1.0 + s).groupby(times.normalize()).prod() - 1.0


def _sharpe(x: np.ndarray) -> float:
    if x.size < 2:
        return 0.0
    sd = float(np.std(x, ddof=1))
    return 0.0 if sd <= 0 else float(np.mean(x)) / sd * math.sqrt(DAYS_PER_YEAR)


def _max_dd(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    eq = np.concatenate(([1.0], np.cumprod(1.0 + x)))
    if np.any(eq <= 0):
        return 1.0
    return float(np.max(1.0 - eq / np.maximum.accumulate(eq)))


def simulate(p: Panel, raw_weights: np.ndarray, rebalance: np.ndarray) -> SimResult:
    """Full two-pass evaluation. ``raw_weights`` is (T, S); ``rebalance`` is (T,) bool."""
    requested = normalise_unit_gross(raw_weights, rebalance)
    reference = requested * cap_scale(requested)[:, None]
    ref = _evaluate(p, reference, rebalance, 1.0)
    s = risk_scalars(ref.gross)
    scaled = reference * s[:, None]
    executed = scaled * cap_scale(scaled)[:, None]

    results = {mult: _evaluate(p, executed, rebalance, float(mult)) for mult in (1, 2, 3)}
    times = p.times
    daily = {mult: _daily(times, r.net) for mult, r in results.items()}

    base = results[1]
    d1 = daily[1].to_numpy()
    days = max(len(d1), 1)
    years = days / DAYS_PER_YEAR
    growth = float(np.prod(1.0 + d1))
    ann_ret = growth ** (1.0 / years) - 1.0 if growth > 0 else -1.0
    dd = _max_dd(d1)
    calmar = (1000.0 if ann_ret > 0 else 0.0) if dd <= 0 else ann_ret / dd
    turnover_total = float(base.turnover.sum())
    gross_total = float(base.gross.sum())
    positive_gross = float(np.clip(base.gross, 0, None).sum())
    costs = float(base.fees.sum())
    absd = np.abs(d1)
    idx = pd.DatetimeIndex(daily[1].index)
    quarters = pd.Series(d1, index=idx).groupby(idx.tz_localize(None).to_period("Q")).apply(
        lambda x: float(np.prod(1.0 + x.to_numpy())) - 1.0
    )

    d2 = daily[2].to_numpy()
    d3 = daily[3].to_numpy()
    g2 = float(np.prod(1.0 + d2))
    ann2 = g2 ** (1.0 / years) - 1.0 if g2 > 0 else -1.0
    dd2 = _max_dd(d2)

    folds = _is_folds(times[0])
    fold_sharpe = {}
    for name, a, b in folds:
        mask = (idx >= a) & (idx < b)
        fold_sharpe[name] = _sharpe(d2[mask])

    metrics = {
        "net_sharpe": _sharpe(d1),
        "double_cost_sharpe": _sharpe(d2),
        "triple_cost_sharpe": _sharpe(d3),
        "annualized_return": ann_ret,
        "double_cost_annualized_return": ann2,
        "annualized_volatility": float(np.std(d1, ddof=1)) * math.sqrt(DAYS_PER_YEAR),
        "max_drawdown": dd,
        "max_drawdown_2x": dd2,
        "calmar_2x": (1000.0 if ann2 > 0 else 0.0) if dd2 <= 0 else ann2 / dd2,
        "calmar": calmar,
        "positive_quarter_fraction": float((quarters > 0).mean()),
        "positive_quarter_fraction_2x": float(
            (pd.Series(d2, index=idx).groupby(idx.tz_localize(None).to_period("Q")).apply(
                lambda x: float(np.prod(1.0 + x.to_numpy())) - 1.0) > 0).mean()
        ),
        "annualized_turnover": turnover_total / years,
        "gross_edge_bps_per_turnover": gross_total / turnover_total * 1e4 if turnover_total > 0 else 0.0,
        "cost_share_of_positive_gross": costs / positive_gross if positive_gross > 0 else 1.0,
        "top5_day_share": float(np.sort(absd)[-5:].sum() / absd.sum()) if absd.sum() > 0 else 0.0,
        "long_gross_pnl": float(base.long_gross.sum()),
        "short_gross_pnl": float(base.short_gross.sum()),
        "trade_count": base.trades,
        "worst_fold_sharpe": min(fold_sharpe.values()),
        "median_fold_sharpe": float(np.median(list(fold_sharpe.values()))),
        "positive_fold_count": sum(1 for v in fold_sharpe.values() if v > 0),
        "mean_scalar": float(np.mean(s)),
    }
    return SimResult(metrics, daily, fold_sharpe, s, ref.net)


def _is_folds(is_start: pd.Timestamp):
    end = pd.Timestamp("2024-08-01T00:00:00Z")
    interior = [end - pd.DateOffset(years=y) for y in (3, 2, 1)]
    bounds = [is_start, *(max(e, is_start) for e in interior), end]
    return [(f"F{i + 1}", bounds[i], bounds[i + 1]) for i in range(4)]


def bootstrap_positive_fraction(daily: pd.Series, samples: int = 2000, block: int = 10, seed: int = 20260804) -> float:
    x = daily.to_numpy(dtype=float)
    n = len(x)
    rng = np.random.default_rng(seed)
    nblocks = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(samples, nblocks))
    offsets = np.arange(block)
    idx = (starts[:, :, None] + offsets[None, None, :]).reshape(samples, -1)[:, :n] % n
    means = x[idx].mean(axis=1)
    return float((means > 0).mean())


def rank_score(m: dict, drawdown_floor: float = 0.20) -> float:
    def decaying(v: float) -> float:
        if math.isnan(v):
            return 0.0
        if v >= 0:
            return min(1.0, v)
        return -(-v) / (-v + 1.0)

    span = drawdown_floor - 0.05
    return (
        30.0 * decaying((m["worst_fold_sharpe"] + 0.25) / 1.00)
        + 20.0 * decaying((m["median_fold_sharpe"] - 0.25) / 0.75)
        + 20.0 * decaying((drawdown_floor - m["max_drawdown_2x"]) / span)
        + 15.0 * decaying(m["calmar_2x"] / 1.50)
        + 8.0 * decaying((m["positive_quarter_fraction_2x"] - 0.50) / 0.375)
        + 7.0 * decaying((m.get("trial_adjusted_confidence", 1.0) - 0.90) / 0.10)
    )
