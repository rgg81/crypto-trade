"""Faithful-enough research simulator: adds the common risk unit and the section 4 caps.

Still not the organiser scorer (no participation cap, no delisting force-exit, no risk policy,
no mark-price funding basis) -- but it now reproduces the two structural facts that decide most
of the floors: the executed book is ``clamp(0.10/sigma, 0.20, 3.0)`` x the unit-gross book, and
gross is then capped back to 1.0, so turnover, drawdown and realised volatility all scale with it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BARS_PER_YEAR = 365 * 24 / 8
COST_BPS = 7.5
MAX_SYMBOL = 0.20
MAX_GROSS = 1.0
RISK_LOOKBACK_BARS = int(90 * 24 / 8)   # 270
TARGET_VOL = 0.10


def cap_rows(w: np.ndarray) -> np.ndarray:
    """One uniform per-row reduction until gross/net/symbol caps hold."""
    gross = np.abs(w).sum(axis=1)
    net = np.abs(w.sum(axis=1))
    sym = np.abs(w).max(axis=1)
    scale = np.ones(len(w))
    for mag, ceil_ in ((gross, MAX_GROSS), (net, MAX_GROSS), (sym, MAX_SYMBOL)):
        with np.errstate(divide="ignore", invalid="ignore"):
            cand = np.where(mag > ceil_ + 1e-12, ceil_ / np.where(mag > 0, mag, 1.0), 1.0)
        scale = np.minimum(scale, cand)
    return w * scale[:, None]


def _pass(w: np.ndarray, o: np.ndarray, fnd: np.ndarray, reb: np.ndarray,
          first: int, last: int, cost_bps: float):
    equity = 1.0
    qty = np.zeros(w.shape[1])
    rets_gross, rets_net, turns, trades = [], [], [], 0
    long_pnl = short_pnl = 0.0
    eq_path = []
    for t in range(first, last + 1):
        px, px_next = o[t + 1], o[t + 2]
        tradable = np.isfinite(px) & (px > 0)
        held = qty * np.where(tradable, px, 0.0)
        if reb[t]:
            target = np.nan_to_num(w[t], nan=0.0) * equity * tradable
            delta = np.where(tradable, target - held, 0.0)
            gross_traded = np.abs(delta).sum()
            turns.append(gross_traded / equity)
            trades += int((np.abs(delta) > 1e-9 * equity).sum())
            newn = held + delta
            qty = np.where(tradable, newn / np.where(tradable, px, 1.0), qty)
            cost = gross_traded * cost_bps / 1e4
        else:
            turns.append(0.0)
            cost = 0.0
        notional = qty * np.where(tradable, px, 0.0)
        ok = tradable & np.isfinite(px_next) & (px_next > 0)
        step = np.where(ok, px_next / np.where(tradable, px, 1.0) - 1.0, 0.0)
        pnl = notional * step - notional * np.nan_to_num(fnd[t + 1], nan=0.0)
        long_pnl += float(pnl[notional > 0].sum())
        short_pnl += float(pnl[notional < 0].sum())
        gross = pnl.sum()
        rets_gross.append(gross / equity)
        rets_net.append((gross - cost) / equity)
        equity += gross - cost
        eq_path.append(equity)
    return rets_gross, rets_net, turns, trades, long_pnl, short_pnl, eq_path


def run(weights: pd.DataFrame, opens: pd.DataFrame, fund: pd.DataFrame,
        rebalance: pd.Series, start: pd.Timestamp, cost_mult: float = 1.0) -> dict:
    idx = opens.index
    cols = opens.columns
    o = opens.to_numpy(float)
    w0 = weights.reindex(index=idx, columns=cols).fillna(0.0).to_numpy(float)
    g = np.abs(w0).sum(axis=1)
    w0 = w0 / np.where(g > 0, g, 1.0)[:, None]        # unit gross = the requested book
    w_ref = cap_rows(w0)
    fnd = fund.reindex(index=idx, columns=cols).fillna(0.0).to_numpy(float)
    reb = rebalance.reindex(idx).fillna(False).to_numpy(bool)
    first = int(np.arange(len(idx))[idx >= start][0])
    last = len(idx) - 3

    # pass 1: reference book at 1x cost -> gross returns -> risk scalars
    rg, _, _, _, _, _, _ = _pass(w_ref, o, fnd, reb, first, last, COST_BPS)
    gross_series = np.asarray(rg)
    scal = np.ones(len(idx))
    for k, t in enumerate(range(first, last + 1)):
        if k < RISK_LOOKBACK_BARS:
            continue
        win = gross_series[k - RISK_LOOKBACK_BARS:k]
        sd = win.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
        scal[t] = min(3.0, max(0.20, TARGET_VOL / sd)) if sd > 0 else 3.0
    w_exec = cap_rows(w_ref * scal[:, None])

    rg2, rn2, turns, trades, lp, sp, eq = _pass(
        w_exec, o, fnd, reb, first, last, COST_BPS * cost_mult)
    ridx = idx[first:last + 1]
    return {
        "net": pd.Series(rn2, index=ridx),
        "gross": pd.Series(rg2, index=ridx),
        "equity": pd.Series(eq, index=ridx),
        "turnover_annual": float(np.sum(turns) / (len(ridx) / BARS_PER_YEAR)),
        "trades": trades,
        "long_gross": lp,
        "short_gross": sp,
        "mean_scalar": float(scal[first:last + 1].mean()),
        "mean_gross_exposure": float(np.abs(w_exec[first:last + 1]).sum(axis=1).mean()),
    }


FOLDS = (("F1", "2020-08-17", "2021-08-01"), ("F2", "2021-08-01", "2022-08-01"),
         ("F3", "2022-08-01", "2023-08-01"), ("F4", "2023-08-01", None))


def _daily(r: pd.Series) -> pd.Series:
    return (1 + r).groupby(r.index.floor("1D")).prod() - 1


def report(res: dict) -> dict:
    r, eq = res["net"], res["equity"]
    d = _daily(r)
    vol = float(d.std() * np.sqrt(365))
    ann = float(d.mean() * 365)
    dd = float((1 - eq / eq.cummax()).max())
    q = (1 + d).groupby(pd.PeriodIndex(d.index, freq="Q")).prod() - 1
    folds = {}
    for name, a, b in FOLDS:
        s = d[(d.index >= pd.Timestamp(a, tz="UTC"))]
        if b is not None:
            s = s[s.index < pd.Timestamp(b, tz="UTC")]
        folds[name] = float(s.mean() / s.std() * np.sqrt(365)) if len(s) > 2 and s.std() > 0 else np.nan
    fv = np.array(list(folds.values()))
    ad = d.abs().sum()
    turn = res["turnover_annual"]
    gross_pnl = res["gross"].sum()
    years = len(d) / 365
    return {
        "sharpe": ann / vol if vol > 0 else np.nan,
        "ann_ret": ann,
        "vol": vol,
        "maxdd": dd,
        "turnover": turn,
        "trades": res["trades"],
        "gross_edge_bps": gross_pnl / (turn * years) * 1e4 if turn > 0 else 0.0,
        "long_gross": res["long_gross"],
        "short_gross": res["short_gross"],
        "posq": float((q > 0).mean()),
        "top5day": float(np.sort(d.abs())[-5:].sum() / ad) if ad > 0 else 1.0,
        "folds_pos": int((fv > 0).sum()),
        "worst_fold": float(np.nanmin(fv)),
        "median_fold": float(np.nanmedian(fv)),
        **{k: round(v, 2) for k, v in folds.items()},
        "gross_exp": res["mean_gross_exposure"],
    }


def bootstrap_B(r: pd.Series, samples: int = 2000, block_days: int = 10, seed: int = 20260804):
    d = _daily(r).to_numpy(float)
    n = len(d)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block_days))
    starts = rng.integers(0, n, size=(samples, nb))
    offs = np.arange(block_days)
    idx = (starts[:, :, None] + offs[None, None, :]).reshape(samples, -1) % n
    means = d[idx[:, :n]].mean(axis=1)
    return float((means > 0).mean())
