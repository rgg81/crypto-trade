"""Lightweight research simulator for team-02 EDA.

Deliberately NOT the organiser scorer: no risk unit, no risk policy, no participation cap, no
delisting logic. It exists only to screen hypotheses cheaply before spending a trial. Every
number that matters comes from scripts/cup20_evaluate.py.

Structure it does copy faithfully, because getting these wrong would make the screen useless:
  * decisions on the 8h grid, fills at the NEXT bar open;
  * point-in-time weekly membership;
  * explicit rebalance only on cadence boundaries (otherwise quantities are held, no turnover);
  * per-side cost of 7.5 bps on executed notional;
  * funding accrued on held notional over the interval.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BARS_PER_YEAR = 365 * 24 / 8
COST_BPS = 7.5


def funding_matrix(funding: pd.DataFrame, index: pd.DatetimeIndex,
                   columns: pd.Index) -> pd.DataFrame:
    """Funding paid by a long over the interval [open_time, open_time + 8h)."""
    f = funding[["funding_time", "symbol", "funding_rate"]].copy()
    f["slot"] = f["funding_time"].dt.floor("8h")
    agg = f.groupby(["slot", "symbol"])["funding_rate"].sum().unstack()
    return agg.reindex(index=index, columns=columns).fillna(0.0)


def simulate(weights: pd.DataFrame, opens: pd.DataFrame, fund: pd.DataFrame,
             rebalance: pd.Series, start: pd.Timestamp,
             cost_bps: float = COST_BPS) -> dict:
    """weights: desired unit-gross weights at each decision; fills at next open."""
    idx = opens.index
    sel = idx[idx >= start]
    cols = opens.columns
    o = opens.to_numpy(float)
    w = weights.reindex(index=idx, columns=cols).to_numpy(float)
    fnd = fund.reindex(index=idx, columns=cols).to_numpy(float)
    reb = rebalance.reindex(idx).fillna(False).to_numpy(bool)
    pos = np.arange(len(idx))
    first = int(pos[idx >= start][0])
    last = len(idx) - 2  # need open[t+1]

    equity = 1.0
    qty = np.zeros(len(cols))          # notional at previous fill price, tracked as units
    rets, turns, trades = [], [], 0
    long_pnl = short_pnl = 0.0
    eq_path = []
    for t in range(first, last + 1):
        px = o[t + 1]                   # fill price for decisions at t is open[t+1]
        px_next = o[t + 2] if t + 2 < len(idx) else o[t + 1]
        held_notional = qty * np.nan_to_num(px, nan=0.0)
        # rebalance
        if reb[t]:
            target_w = np.nan_to_num(w[t], nan=0.0)
            tradable = np.isfinite(px) & (px > 0)
            target_notional = target_w * equity * tradable
            delta = target_notional - np.nan_to_num(held_notional)
            delta[~tradable] = 0.0
            turnover = np.abs(delta).sum() / equity
            cost = np.abs(delta).sum() * cost_bps / 1e4
            trades += int((np.abs(delta) > 1e-9 * equity).sum())
            new_notional = np.nan_to_num(held_notional) + delta
            qty = np.where(tradable, new_notional / np.where(tradable, px, 1.0), qty)
            equity -= cost
        else:
            turnover = 0.0
        # carry over interval [t+1, t+2)
        notional = qty * np.nan_to_num(px, nan=0.0)
        step = np.nan_to_num(px_next, nan=0.0) / np.where(np.isfinite(px) & (px > 0), px, 1.0) - 1.0
        step = np.where(np.isfinite(px) & (px > 0) & np.isfinite(px_next), step, 0.0)
        price_pnl = notional * step
        funding_pnl = -notional * np.nan_to_num(fnd[t + 1], nan=0.0)
        pnl = price_pnl + funding_pnl
        long_pnl += float(pnl[notional > 0].sum())
        short_pnl += float(pnl[notional < 0].sum())
        ret = pnl.sum() / equity
        equity += pnl.sum()
        rets.append(ret)
        turns.append(turnover)
        eq_path.append(equity)
    r = pd.Series(rets, index=idx[first:last + 1])
    eq = pd.Series(eq_path, index=r.index)
    return {
        "returns": r,
        "equity": eq,
        "turnover_annual": float(np.sum(turns) / (len(r) / BARS_PER_YEAR)),
        "trades": trades,
        "long_gross": long_pnl,
        "short_gross": short_pnl,
    }


def stats(res: dict) -> dict:
    r = res["returns"]
    eq = res["equity"]
    daily = (1 + r).groupby(r.index.floor("1D")).prod() - 1
    ann_ret = float(daily.mean() * 365)
    ann_vol = float(daily.std() * np.sqrt(365))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan
    dd = float((1 - eq / eq.cummax()).max())
    return {
        "sharpe": sharpe,
        "ann_ret": ann_ret,
        "ann_vol": ann_vol,
        "maxdd": dd,
        "turnover": res["turnover_annual"],
        "trades": res["trades"],
        "long_gross": res["long_gross"],
        "short_gross": res["short_gross"],
    }


def yearly_sharpe(res: dict) -> pd.Series:
    r = res["returns"]
    daily = (1 + r).groupby(r.index.floor("1D")).prod() - 1
    folds = {
        "F1": ("2020-08-17", "2021-08-01"),
        "F2": ("2021-08-01", "2022-08-01"),
        "F3": ("2022-08-01", "2023-08-01"),
        "F4": ("2023-08-01", None),
    }
    out = {}
    for k, (a, b) in folds.items():
        sub = daily[daily.index >= pd.Timestamp(a, tz="UTC")]
        if b is not None:
            sub = sub[sub.index < pd.Timestamp(b, tz="UTC")]
        out[k] = float(sub.mean() / sub.std() * np.sqrt(365)) if sub.std() > 0 else np.nan
    return pd.Series(out)
