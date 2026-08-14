"""Offline replica of the CUP-20 two-pass evaluation, for design-space mapping only.

It follows charter section 4 (fills at the next bar open, 5 bps fee + 2.5 bps slippage per side,
native funding into the holding interval, gross/net/per-symbol caps applied by reduction) and
section 6 (unit-gross normalisation, reference pass, common risk unit, executed pass). It is an
approximation in three places, all of them deliberate and all of them recorded:

  * the participation cap is applied per symbol per bar against 0.001 of that bar's quote volume,
    but unfilled notional is dropped rather than carried;
  * delisting force-exits are handled by exiting a symbol on the first boundary it stops being
    fillable, at that bar's last available open, rather than at the organiser's exact last open;
  * funding is folded into one per-bar per-unit charge against the book held over the bar.

No number produced here is a tournament number. Fidelity against the organiser's own packet is
measured once a real trial exists and reported in the certificate.
"""

from __future__ import annotations

import math

import numpy as np

from panel import EXEC, RISK_UNIT, Panel

BARS_PER_YEAR = 365.0 * 24.0 / 8.0
DAYS_PER_YEAR = 365.0
COST_BPS_PER_SIDE = (
    float(EXEC["taker_fee_bps_per_side"]) + float(EXEC["slippage_bps_per_side"])
) / 10_000.0
MAX_GROSS = float(EXEC["max_gross_exposure"])
MAX_NET = float(EXEC["max_abs_net_exposure"])
MAX_SYM = float(EXEC["max_symbol_exposure"])
MAX_PART = float(EXEC["max_bar_participation"])
RU_TARGET = float(RISK_UNIT["target_annualized_volatility"])
RU_LOOKBACK_BARS = int(math.ceil(float(RISK_UNIT["lookback_days"]) * 24.0 / 8.0))
RU_MIN = float(RISK_UNIT["minimum_scale"])
RU_MAX = float(RISK_UNIT["maximum_scale"])
CAP_TOL = 1e-12


def normalise_unit_gross(W: np.ndarray) -> np.ndarray:
    gross = np.abs(W).sum(axis=1)
    div = np.where(gross > 0.0, gross, 1.0)
    return W / div[:, None]


def cap_scale(W: np.ndarray) -> np.ndarray:
    gross = np.abs(W).sum(axis=1)
    net = np.abs(W.sum(axis=1))
    sym = np.abs(W).max(axis=1) if W.shape[1] else np.zeros(len(W))
    s = np.ones(len(W))
    for mag, ceil in ((gross, MAX_GROSS), (net, MAX_NET), (sym, MAX_SYM)):
        br = mag > ceil + CAP_TOL
        cand = np.ones(len(W))
        with np.errstate(divide="ignore", invalid="ignore"):
            cand[br] = ceil / mag[br]
        s = np.minimum(s, cand)
    return s


def apply_caps(W: np.ndarray) -> np.ndarray:
    return W * cap_scale(W)[:, None]


class Sim:
    """Holds the panel and precomputed price/funding arrays for repeated simulation."""

    def __init__(self, panel: Panel | None = None) -> None:
        self.p = panel or Panel()
        p = self.p
        d0, dn = p.d0, p.dn
        # Decision rows: i indexes decisions; panel row = d0 + i.
        self.n = dn - d0
        self.open = p.open[d0 : dn + 1]  # one extra row for the final next-open
        self.close = p.close[d0:dn]
        self.qvol = np.nan_to_num(p.quote_volume[d0:dn], nan=0.0)
        self.fund = np.nan_to_num(p.funding_per_unit[d0:dn], nan=0.0)
        self.elig = p.eligible[d0:dn]
        self.times = p.times
        # next-open return per bar; NaN where the symbol has no next open (delist/suspension)
        o0 = self.open[:-1] if len(self.open) > self.n else self.open
        if o0.shape[0] != self.n:
            o0 = self.open[: self.n]
        self.o_now = o0
        nxt = np.full_like(o0, np.nan)
        if p.open.shape[0] > dn:
            nxt = p.open[d0 + 1 : dn + 1]
        else:
            nxt[:-1] = p.open[d0 + 1 : dn]
            nxt[-1] = p.close[dn - 1]
        # Terminal bar: organiser force-closes at the close, so use close as the exit price.
        nxt[-1] = np.where(np.isnan(nxt[-1]), p.close[dn - 1], nxt[-1])
        self.o_next = nxt
        # Where the next open is missing but a close exists, the organiser force-exits at the
        # close of this bar.
        self.exit_px = np.where(np.isnan(self.o_next), self.close, self.o_next)
        self.days = np.array(
            [t.value // 86_400_000_000_000 for t in self.times], dtype=np.int64
        )

    # ---------------------------------------------------------------- core replay
    def replay(self, W: np.ndarray, cost_mult: float) -> dict:
        """One evaluator pass over an already-capped weight matrix."""
        n, m = W.shape
        o_now, exit_px = self.o_now, self.exit_px
        fund, qvol = self.fund, self.qvol
        cost = COST_BPS_PER_SIDE * cost_mult

        qty = np.zeros(m)
        equity = float(EXEC["initial_equity"])
        net_r = np.empty(n)
        gross_r = np.empty(n)
        turn = np.empty(n)
        long_g = np.empty(n)
        short_g = np.empty(n)
        fee_r = np.empty(n)
        trades = 0

        for i in range(n):
            px = o_now[i]
            live = np.isfinite(px)
            e0 = equity
            # rebalance
            tgt_notional = np.where(live, W[i] * e0, 0.0)
            cur_notional = np.where(live, qty * np.nan_to_num(px, nan=0.0), 0.0)
            order = tgt_notional - cur_notional
            # symbols that went unfillable are force-exited at exit price (handled in PnL)
            cap = qvol[i] * MAX_PART
            order = np.clip(order, -cap, cap)
            order = np.where(live, order, 0.0)
            traded = np.abs(order) > 1e-9
            trades += int(traded.sum())
            notional_traded = float(np.abs(order).sum())
            costs = notional_traded * cost
            qty = np.where(live, qty + order / np.where(live, px, 1.0), qty)
            # price PnL over the bar
            dpx = exit_px[i] - px
            dpx = np.where(np.isfinite(dpx), dpx, 0.0)
            pnl_sym = qty * dpx
            pnl = float(np.nansum(pnl_sym))
            f_now = -float(np.nansum(qty * fund[i]))
            g = pnl + f_now
            long_g[i] = float(np.nansum(np.where(qty > 0, pnl_sym, 0.0)))
            short_g[i] = float(np.nansum(np.where(qty < 0, pnl_sym, 0.0)))
            net = g - costs
            net_r[i] = net / e0
            gross_r[i] = g / e0
            turn[i] = notional_traded / e0
            fee_r[i] = costs / e0
            equity = e0 + net
            if equity <= 0:
                net_r[i:] = np.nan
                break
            # symbols that lose fillability next bar get force-closed there; approximate by
            # zeroing quantity whose next open is missing
            gone = ~np.isfinite(exit_px[i]) | (~np.isfinite(self.o_next[i]))
            qty = np.where(gone, 0.0, qty)

        return {
            "net": net_r,
            "gross": gross_r,
            "turnover": turn,
            "long_gross": long_g,
            "short_gross": short_g,
            "fees": fee_r,
            "trades": trades,
        }

    # ---------------------------------------------------------------- two passes
    def run(self, W_raw: np.ndarray, cost_levels=(1, 2, 3)) -> dict:
        Wn = normalise_unit_gross(W_raw)
        Wc = apply_caps(Wn)
        ref = self.replay(Wc, 1.0)
        g = ref["gross"]
        s = np.ones(len(g))
        req = RU_LOOKBACK_BARS
        if len(g) > req:
            roll_std = _rolling_std(g, req)
            ann = roll_std * math.sqrt(BARS_PER_YEAR)
            with np.errstate(divide="ignore", invalid="ignore"):
                sc = RU_TARGET / ann
            sc = np.clip(sc, RU_MIN, RU_MAX)
            sc[~np.isfinite(sc)] = RU_MAX
            s[req:] = sc[req:]
        Ws = apply_caps(Wc * s[:, None])
        out = {"scalars": s, "requested_min_scale": float(cap_scale(Wn).min())}
        for c in cost_levels:
            out[c] = self.replay(Ws, float(c))
        return out


def _rolling_std(x: np.ndarray, w: int) -> np.ndarray:
    """std(ddof=1) of the w rows strictly before each index; NaN for the first w."""
    n = len(x)
    out = np.full(n, np.nan)
    cs = np.concatenate(([0.0], np.cumsum(x)))
    cs2 = np.concatenate(([0.0], np.cumsum(x * x)))
    idx = np.arange(w, n)
    s1 = cs[idx] - cs[idx - w]
    s2 = cs2[idx] - cs2[idx - w]
    var = (s2 - s1 * s1 / w) / (w - 1)
    out[idx] = np.sqrt(np.maximum(var, 0.0))
    return out


# -------------------------------------------------------------------- metrics
def daily(net: np.ndarray, days: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ok = np.isfinite(net)
    net = np.where(ok, net, 0.0)
    uniq, inv = np.unique(days, return_inverse=True)
    growth = np.ones(len(uniq))
    np.multiply.at(growth, inv, 1.0 + net)
    return uniq, growth - 1.0


def sharpe(d: np.ndarray) -> float:
    if len(d) < 2:
        return 0.0
    sd = float(np.std(d, ddof=1))
    return 0.0 if sd <= 0 else float(np.mean(d)) / sd * math.sqrt(DAYS_PER_YEAR)


def maxdd(d: np.ndarray) -> float:
    eq = np.concatenate(([1.0], np.cumprod(1.0 + d)))
    if np.any(eq <= 0):
        return 1.0
    return float(np.max(1.0 - eq / np.maximum.accumulate(eq)))


def metrics(res: dict, days: np.ndarray, fold_edges=None) -> dict:
    out = {}
    for c in (1, 2, 3):
        if c not in res:
            continue
        r = res[c]
        _, d = daily(r["net"], days)
        yrs = len(d) / DAYS_PER_YEAR
        growth = float(np.prod(1.0 + d))
        ann = growth ** (1.0 / yrs) - 1.0 if growth > 0 else -1.0
        dd = maxdd(d)
        tot_turn = float(np.nansum(r["turnover"]))
        gross_tot = float(np.nansum(r["gross"]))
        pos_gross = float(np.nansum(np.clip(r["gross"], 0, None)))
        costs = float(np.nansum(r["fees"]))
        out[c] = {
            "sharpe": sharpe(d),
            "ann_return": ann,
            "ann_vol": float(np.std(d, ddof=1)) * math.sqrt(DAYS_PER_YEAR),
            "maxdd": dd,
            "calmar": (ann / dd) if dd > 0 else float("inf"),
            "ann_turnover": tot_turn / yrs,
            "gross_edge_bps": (gross_tot / tot_turn * 1e4) if tot_turn > 0 else 0.0,
            "cost_share": (costs / pos_gross) if pos_gross > 0 else 9.99,
            "trades": r["trades"],
            "long_gross": float(np.nansum(r["long_gross"])),
            "short_gross": float(np.nansum(r["short_gross"])),
            "daily": d,
        }
    return out
