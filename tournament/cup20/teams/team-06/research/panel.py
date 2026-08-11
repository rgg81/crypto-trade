"""Team 06 offline research panel.

A fast, vectorised stand-in for the organiser's evaluator, used ONLY to choose a mechanism before
spending trials. It is not a scorer and no number from it is ever reported as a score: the
organiser's ``cup20_evaluate.py`` is the only authority. What it has to get right is the causal
alignment, so that an offline conclusion is not an artifact of look-ahead:

    decision boundary t      -> the strategy may see bars whose close_time <= t, i.e. open_time <= t-8h
    fill                     -> the open of the bar that opens at t
    holding return           -> open[t+8h] / open[t] - 1

So in a frame indexed by ``open_time``: the weight placed on row i may only use rows <= i-1, and it
earns ``opens[i+1]/opens[i] - 1``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ROOT = "data/cup20/is"
BARS_PER_DAY = 3
BARS_PER_YEAR = 365 * BARS_PER_DAY
COST_BPS_PER_SIDE = 7.5  # 5 taker + 2.5 slippage

FOLD_EDGES = [
    ("F1", "2020-08-17", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
]


def load_panel() -> dict[str, pd.DataFrame]:
    bars = pd.read_parquet(f"{ROOT}/bars.parquet")
    membership = pd.read_parquet(f"{ROOT}/membership.parquet")
    funding = pd.read_parquet(f"{ROOT}/funding.parquet")

    opens = bars.pivot(index="open_time", columns="symbol", values="open").sort_index()
    closes = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    highs = bars.pivot(index="open_time", columns="symbol", values="high").sort_index()
    lows = bars.pivot(index="open_time", columns="symbol", values="low").sort_index()
    qvol = bars.pivot(index="open_time", columns="symbol", values="quote_volume").sort_index()

    grid = opens.index
    # Point-in-time membership: forward-fill the weekly reconstitution onto the 8h grid.
    member = pd.DataFrame(False, index=grid, columns=opens.columns)
    recon = sorted(membership["reconstitution_time"].unique())
    by_time = {t: set(g["symbol"]) for t, g in membership.groupby("reconstitution_time")}
    current: set[str] = set()
    recon_iter = iter(recon)
    next_recon = next(recon_iter, None)
    rows = []
    for t in grid:
        while next_recon is not None and next_recon <= t:
            current = by_time[next_recon]
            next_recon = next(recon_iter, None)
        rows.append([c in current for c in opens.columns])
    member = pd.DataFrame(rows, index=grid, columns=opens.columns)
    # A member is only tradeable where the evaluator has an executable open.
    member &= opens.notna()

    # Funding accrued over the holding interval (open[t], open[t+1]]: sum the events landing in it.
    f = funding.copy()
    f["bucket"] = f["funding_time"].dt.floor("8h")
    fund = (
        f.groupby(["bucket", "symbol"])["funding_rate"]
        .sum()
        .unstack("symbol")
        .reindex(index=grid, columns=opens.columns)
        .fillna(0.0)
    )

    return {
        "opens": opens,
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "qvol": qvol,
        "member": member,
        "funding": fund,
    }


def fold_slices(index: pd.DatetimeIndex) -> list[tuple[str, np.ndarray]]:
    out = []
    for name, lo, hi in FOLD_EDGES:
        mask = (index >= pd.Timestamp(lo, tz="UTC")) & (index < pd.Timestamp(hi, tz="UTC"))
        out.append((name, mask))
    return out


def book_stats(
    weights: pd.DataFrame,
    opens: pd.DataFrame,
    fund: pd.DataFrame,
    *,
    cost_bps: float = COST_BPS_PER_SIDE,
    cost_multiplier: float = 1.0,
    risk_unit: bool = True,
) -> dict:
    """Approximate the two-pass common risk unit and score the executed book.

    ``weights`` is a unit-gross target frame on the decision grid; NaN rows mean "hold".
    """
    fwd = opens.shift(-1) / opens - 1.0
    fwd = fwd.reindex(columns=weights.columns)
    fundr = fund.shift(-1).reindex(columns=weights.columns).fillna(0.0)

    # Held weights: a row of NaN means hold, so the previous target drifts forward. Approximating
    # quantity-hold by weight-hold overstates nothing about turnover and is close enough for a lab.
    held = weights.ffill().fillna(0.0)
    gross_ret = (held * fwd.fillna(0.0)).sum(axis=1) + (held * fundr).sum(axis=1)

    scale = pd.Series(1.0, index=weights.index)
    if risk_unit:
        lookback = 90 * BARS_PER_DAY
        sigma = gross_ret.rolling(lookback, min_periods=lookback).std().shift(1) * np.sqrt(
            BARS_PER_YEAR
        )
        scale = (0.10 / sigma).clip(0.20, 3.0).fillna(1.0)
        # gross cap 1.0 -- weights already sum to 1 gross, so the scalar cannot exceed 1.
        scale = scale.clip(upper=1.0)

    exec_w = held.mul(scale, axis=0)
    turn = exec_w.diff().abs().sum(axis=1).fillna(exec_w.abs().sum(axis=1))
    cost = turn * cost_bps * cost_multiplier / 1e4
    net = (exec_w * fwd.fillna(0.0)).sum(axis=1) + (exec_w * fundr).sum(axis=1) - cost
    gross = (exec_w * fwd.fillna(0.0)).sum(axis=1) + (exec_w * fundr).sum(axis=1)

    net = net.iloc[:-1]
    gross = gross.iloc[:-1]
    turn = turn.iloc[:-1]

    equity = (1 + net).cumprod()
    dd = 1 - equity / equity.cummax()
    ann_ret = equity.iloc[-1] ** (BARS_PER_YEAR / len(net)) - 1
    vol = net.std() * np.sqrt(BARS_PER_YEAR)
    sharpe = net.mean() / net.std() * np.sqrt(BARS_PER_YEAR) if net.std() > 0 else np.nan
    ann_turn = turn.sum() / len(turn) * BARS_PER_YEAR

    folds = {}
    for name, mask in fold_slices(net.index):
        seg = net[mask]
        folds[name] = seg.mean() / seg.std() * np.sqrt(BARS_PER_YEAR) if seg.std() > 0 else np.nan

    trades = int((exec_w.diff().abs() > 1e-9).sum().sum())
    gross_edge_bps = gross.sum() / turn.sum() * 1e4 if turn.sum() > 0 else np.nan

    return {
        "ann_ret": ann_ret,
        "vol": vol,
        "sharpe": sharpe,
        "maxdd": dd.max(),
        "ann_turnover": ann_turn,
        "trades": trades,
        "gross_edge_bps": gross_edge_bps,
        "folds": folds,
        "net": net,
        "scale": scale,
    }
