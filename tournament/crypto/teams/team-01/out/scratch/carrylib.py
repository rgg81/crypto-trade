"""team-01 scratch — funding-carry signal builder + evaluation helpers.

Scratch-only (out/ is excluded from the harness scan); MAY import the evaluator.
The eventual strategy.py must NOT import this or the evaluator.
"""

from __future__ import annotations

import sys

sys.path.insert(
    0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis"
)

import numpy as np
import pandas as pd
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

_CACHE: dict = {}


def panels():
    if "pn" not in _CACHE:
        pn, aux, scoring = te.load_is_panels()
        _CACHE.update(pn=pn, aux=aux, scoring=scoring)
    return _CACHE["pn"], _CACHE["aux"], _CACHE["scoring"]


def build_weights(
    pn,
    aux,
    *,
    L: int = 21,
    smoother: str = "mean",  # "mean" | "ema" (halflife=L)
    scheme: str = "rank",  # "rank" | "topk" | "z"
    k: int = 8,
    wspan: int = 1,  # causal EWM span over weight rows; 1 = off
    volnorm: bool = False,
    vol_win: int = 63,
    zclip: float = 2.5,
) -> pd.DataFrame:
    close = pn["close"]
    fund = aux["funding"]
    elig = aux["eligibility"] & close.notna()

    # 1. listed-ness mask (funding panel is 0.0-filled where symbol never traded)
    fund_m = fund.where(close.notna())
    # 2. smoothing
    minp = max(1, min(L, max(2, L // 3)))
    if smoother == "mean":
        sm = fund_m.rolling(L, min_periods=minp).mean()
    elif smoother == "ema":
        sm = fund_m.ewm(halflife=L, min_periods=minp).mean()
    else:
        raise ValueError(smoother)
    # 3. tradable mask
    sm = sm.where(elig)
    # 4. cross-sectional transform, sign = short high funding
    if scheme == "rank":
        r = sm.rank(axis=1, pct=True)
        w = -(r.sub(r.mean(axis=1), axis=0))
    elif scheme == "topk":
        r_hi = sm.rank(axis=1, ascending=False)
        r_lo = sm.rank(axis=1, ascending=True)
        w = pd.DataFrame(0.0, index=sm.index, columns=sm.columns)
        w = w.mask(r_hi <= k, -1.0).mask(r_lo <= k, 1.0)
        w = w.where(sm.notna(), 0.0)
    elif scheme == "z":
        mu = sm.mean(axis=1)
        sd = sm.std(axis=1)
        z = sm.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0).clip(-zclip, zclip)
        w = -z
    else:
        raise ValueError(scheme)
    # 5. optional inverse-vol sizing
    if volnorm:
        vol = close.pct_change().rolling(vol_win, min_periods=21).std()
        w = w.div(vol.replace(0.0, np.nan))
        w = w.replace([np.inf, -np.inf], np.nan)
    # mask + flatten NaN
    w = w.where(elig, 0.0).fillna(0.0)
    # 6. optional causal weight smoothing
    if wspan > 1:
        w = w.ewm(span=wspan).mean()
        w = w.where(elig, 0.0)  # never carry smoothed weight on ineligible names
    return w


def run_cfg(cfg: dict, *, cost_mult=1.0, slip_mult=1.0, apply_funding=True):
    pn, aux, scoring = panels()
    raw = build_weights(pn, aux, **cfg)
    raw = te.conform_raw(raw, pn)
    net, w, parts = te.net_series(
        raw, pn, scoring, cost_mult=cost_mult, slip_mult=slip_mult, apply_funding=apply_funding
    )
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    return net, w, parts, m


def window_sharpes(net: pd.Series) -> dict[str, float]:
    out = {}
    for i, (label, lo, hi) in enumerate(tc._REGIMES):
        s = net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]
        g = s.groupby(s.index.to_period("M")).sum()
        out[f"w{i}:{label}:{lo[:7]}"] = (
            float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")
        )
    return out


def sharpe_excluding_window(net: pd.Series, widx: int) -> float:
    label, lo, hi = tc._REGIMES[widx]
    mask = (net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))
    s = net[~mask]
    s = s[(s.index >= tc.TRN_IS_START) & (s.index < tc.TRN_IS_HI)]
    g = s.groupby(s.index.to_period("M")).sum()
    return float(g.mean() / g.std() * np.sqrt(12)) if len(g) > 1 and g.std() > 0 else float("nan")


def split_half(net: pd.Series) -> tuple[float, float]:
    mid = pd.Timestamp("2022-04-01")
    return (
        te.msharpe(net, tc.TRN_IS_START, mid),
        te.msharpe(net, mid, tc.TRN_IS_HI),
    )


def summarize(tag: str, cfg: dict) -> dict:
    net, w, parts, m = run_cfg(cfg)
    h1, h2 = split_half(net)
    row = {
        "tag": tag,
        "sharpe": round(m.sharpe, 3),
        "maxdd": round(m.maxdd, 3),
        "turn": round(m.ann_turnover, 1),
        "ret": round(m.total_return, 3),
        "nL": m.median_names_long,
        "nS": m.median_names_short,
        "h1": round(h1, 3),
        "h2": round(h2, 3),
        "fpnl": round(m.total_funding_pnl, 4),
        "cost": round(m.total_cost, 4),
        "reg": {kk: round(vv, 2) for kk, vv in m.regime_sharpe.items()},
    }
    return row
