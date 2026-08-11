"""Team 06 offline laboratory -- a faithful-enough stand-in for the organiser's two-pass evaluator.

Not a scorer. Nothing from here is ever reported as a score; ``cup20_evaluate.py`` is the only
authority. What this has to get right is the three things that decide whether an offline conclusion
survives contact with the real pipeline:

* causal alignment -- weight placed at boundary t may use only bars closing at or before t, and
  earns ``open[t+1]/open[t] - 1``;
* fills happen ONLY at explicit rebalance boundaries. Between them the strategy returns ``None``
  and the evaluator holds QUANTITIES, so weights drift with relative prices and no cost is paid;
* the common risk unit: ``s_t = clamp(0.10/sigma_t, 0.20, 3.0)`` off the trailing 90-day annualised
  volatility of the reference book's gross returns, then the gross cap at 1.0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BARS_PER_DAY = 3
BARS_PER_YEAR = 365 * BARS_PER_DAY
COST_BPS_PER_SIDE = 7.5

FOLD_EDGES = [
    ("F1", "2020-08-17", "2021-08-01"),
    ("F2", "2021-08-01", "2022-08-01"),
    ("F3", "2022-08-01", "2023-08-01"),
    ("F4", "2023-08-01", "2024-08-01"),
]


def _hold_path(targets: pd.DataFrame, fwd: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Executed weight path under quantity-hold, and the one-way turnover at each boundary."""
    T, S = targets.shape
    tgt = targets.to_numpy(dtype=float)
    ret = np.nan_to_num(fwd.to_numpy(dtype=float))
    held = np.zeros((T, S))
    turn = np.zeros(T)
    current = np.zeros(S)
    for i in range(T):
        row = tgt[i]
        if not np.isnan(row[0]) if S else False:
            pass
        if not np.all(np.isnan(row)):
            new = np.nan_to_num(row)
            turn[i] = np.abs(new - current).sum()
            current = new
        held[i] = current
        # quantity-hold drift to the next boundary
        port = 1.0 + float(current @ ret[i])
        if port <= 0:
            port = 1e-6
        current = current * (1.0 + ret[i]) / port
    return held, turn


def evaluate(
    targets: pd.DataFrame,
    opens: pd.DataFrame,
    fund: pd.DataFrame,
    *,
    cost_multipliers=(1, 2),
) -> dict:
    """``targets``: unit-gross weight frame on the decision grid, NaN rows = hold."""
    cols = targets.columns
    fwd = (opens.shift(-1) / opens - 1.0).reindex(columns=cols).loc[targets.index]
    fundr = fund.shift(-1).reindex(columns=cols).loc[targets.index].fillna(0.0)
    eff = fwd.fillna(0.0) + fundr

    ref_held, ref_turn = _hold_path(targets, eff)
    ref_gross = pd.Series((ref_held * eff.to_numpy()).sum(axis=1), index=targets.index)

    lookback = 90 * BARS_PER_DAY
    sigma = ref_gross.rolling(lookback, min_periods=lookback).std().shift(1) * np.sqrt(
        BARS_PER_YEAR
    )
    s = (0.10 / sigma).clip(0.20, 3.0)
    s = s.where(sigma.notna(), 1.0).clip(upper=1.0)  # gross cap: unit-gross book cannot lever up

    scaled = targets.mul(s, axis=0)
    held, turn = _hold_path(scaled, eff)
    gross = pd.Series((held * eff.to_numpy()).sum(axis=1), index=targets.index)
    turn_s = pd.Series(turn, index=targets.index)

    long_pnl = float((np.where(held > 0, held, 0.0) * eff.to_numpy()).sum())
    short_pnl = float((np.where(held < 0, held, 0.0) * eff.to_numpy()).sum())

    out = {
        "long_gross_pnl": long_pnl,
        "short_gross_pnl": short_pnl,
        # A trade is one non-zero executed symbol/boundary fill. Fills happen only where an
        # explicit target row exists; between them the evaluator holds quantities.
        "fills": int(
            (
                (~np.isnan(scaled.to_numpy(dtype=float))).any(axis=1)[:, None]
                & (np.abs(np.diff(held, axis=0, prepend=0.0)) > 1e-9)
            ).sum()
        ),
        "ann_turnover": float(turn_s.sum() / len(turn_s) * BARS_PER_YEAR),
        "gross_edge_bps": float(gross.sum() / turn_s.sum() * 1e4) if turn_s.sum() > 0 else np.nan,
        "risk_scale_median": float(s.median()),
    }
    for cm in cost_multipliers:
        net = gross - turn_s * COST_BPS_PER_SIDE * cm / 1e4
        eq = (1 + net).cumprod()
        dd = 1 - eq / eq.cummax()
        years = len(net) / BARS_PER_YEAR
        out[f"ann_return_{cm}x"] = float(eq.iloc[-1] ** (1 / years) - 1)
        out[f"vol_{cm}x"] = float(net.std() * np.sqrt(BARS_PER_YEAR))
        out[f"sharpe_{cm}x"] = float(net.mean() / net.std() * np.sqrt(BARS_PER_YEAR))
        out[f"maxdd_{cm}x"] = float(dd.max())
        folds = {}
        for name, lo, hi in FOLD_EDGES:
            m = (net.index >= pd.Timestamp(lo, tz="UTC")) & (net.index < pd.Timestamp(hi, tz="UTC"))
            seg = net[m]
            folds[name] = float(seg.mean() / seg.std() * np.sqrt(BARS_PER_YEAR)) if len(seg) > 10 else np.nan
        out[f"folds_{cm}x"] = folds
        q = net.groupby([net.index.year, net.index.quarter]).sum()
        out[f"posq_{cm}x"] = float((q > 0).mean())
        out[f"net_{cm}x"] = net
    return out


def clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def ranking_score(m: dict) -> float:
    f = list(m["folds_2x"].values())
    worst, med = min(f), float(np.median(f))
    dd = m["maxdd_2x"]
    calmar = m["ann_return_2x"] / dd if dd > 0 else 0.0
    return (
        30 * clamp01((worst + 0.25) / 1.00)
        + 20 * clamp01((med - 0.25) / 0.75)
        + 20 * clamp01((0.20 - dd) / 0.15)
        + 15 * clamp01(calmar / 1.50)
        + 8 * clamp01((m["posq_2x"] - 0.50) / 0.375)
    )


def line(tag: str, m: dict) -> str:
    f = m["folds_2x"]
    return (
        f"{tag:44s} G~{ranking_score(m):5.1f} shp1={m['sharpe_1x']:+.2f} shp2={m['sharpe_2x']:+.2f} "
        f"vol={m['vol_1x']:.3f} dd1={m['maxdd_1x']:.3f} dd2={m['maxdd_2x']:.3f} "
        f"to={m['ann_turnover']:4.1f} edge={m['gross_edge_bps']:5.0f} fills={m['fills']:5d} "
        f"L={m['long_gross_pnl']:+.2f} S={m['short_gross_pnl']:+.2f} | "
        + " ".join(f"{k}={v:+.2f}" for k, v in f.items())
    )
