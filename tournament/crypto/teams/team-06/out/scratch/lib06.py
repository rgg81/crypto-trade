"""team-06 scratch research library — evaluator-only data access (allowed in out/scratch).

Loads the frozen IS panels once per process, provides the family signal builder
(per-coin z of log positioning ratio, faded) and a one-call scorer that returns the
official full-window metrics plus honest-window Sharpe at both cost tiers.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

_CACHE: dict = {}

RATIO_KEYS = ("ls_accounts", "tt_ls_accounts", "tt_ls_positions", "taker_ls_vol")


def load():
    if "pn" not in _CACHE:
        pn, aux, scoring = te.load_is_panels()
        _CACHE.update(pn=pn, aux=aux, scoring=scoring)
    return _CACHE["pn"], _CACHE["aux"], _CACHE["scoring"]


def zpanel(ratio: pd.DataFrame, w_win: int, clip: float = 3.0,
           min_periods: int | None = None) -> pd.DataFrame:
    """Per-coin rolling z of log ratio, current bar included, clipped."""
    if min_periods is None:
        min_periods = w_win // 2
    x = np.log(ratio.where(ratio > 0))
    mu = x.rolling(w_win, min_periods=min_periods).mean()
    sd = x.rolling(w_win, min_periods=min_periods).std()
    z = (x - mu) / sd.where(sd > 0)
    return z.clip(-clip, clip)


def xs_transform(sig: pd.DataFrame, elig: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Cross-sectional transform over names eligible AND non-NaN at t. NaN stays NaN."""
    avail = sig.where(elig)
    if mode == "demean":
        return avail.sub(avail.mean(axis=1), axis=0)
    if mode == "rank":
        r = avail.rank(axis=1)
        n = avail.notna().sum(axis=1)
        return r.sub((n + 1) / 2.0, axis=0).div(n.where(n > 1), axis=0)
    raise ValueError(mode)


def fade_signal(panel_key: str, w_win: int, ema_span: int = 1, mode: str = "demean",
                clip: float = 3.0, min_periods: int | None = None) -> pd.DataFrame:
    """Core family signal: fade per-coin positioning-extreme z on one ratio panel."""
    pn, aux, _ = load()
    z = zpanel(aux[panel_key], w_win, clip=clip, min_periods=min_periods)
    s = -z
    if ema_span > 1:
        s = s.ewm(span=ema_span, min_periods=1).mean().where(s.notna())
    return xs_transform(s, aux["eligibility"], mode)


def spread_signal(w_win: int, ema_span: int = 1, mode: str = "demean",
                  clip: float = 3.0) -> pd.DataFrame:
    """Smart-dumb spread: z(tt_ls_positions) − z(ls_accounts) (fade retail vs smart anchor)."""
    pn, aux, _ = load()
    z_smart = zpanel(aux["tt_ls_positions"], w_win, clip=clip)
    z_retail = zpanel(aux["ls_accounts"], w_win, clip=clip)
    s = z_smart - z_retail
    if ema_span > 1:
        s = s.ewm(span=ema_span, min_periods=1).mean().where(s.notna())
    return xs_transform(s, aux["eligibility"], mode)


def hw_sharpe(net: pd.Series, t0: pd.Timestamp) -> float:
    return te.msharpe(net, t0, tc.TRN_IS_HI)


def score(raw: pd.DataFrame, t0: pd.Timestamp | None = None, stress: bool = True) -> dict:
    """Official full-window metrics @1x (+ honest-window Sharpe, + 2x stress)."""
    pn, aux, scoring = load()
    raw = te.conform_raw(raw, pn)
    net, w, parts = te.net_series(raw, pn, scoring)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    out = {
        "sharpe_1x": round(m.sharpe, 3),
        "maxdd": round(m.maxdd, 3),
        "turnover": round(m.ann_turnover, 1),
        "med_long": m.median_names_long,
        "med_short": m.median_names_short,
        "regime": {k: round(v, 2) for k, v in m.regime_sharpe.items()},
        "fund_pnl": round(m.total_funding_pnl, 4),
        "cost": round(m.total_cost, 4),
    }
    if t0 is not None:
        out["sharpe_hw"] = round(hw_sharpe(net, t0), 3)
    if stress:
        net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
        m2 = te.evaluate(net2, w2, p2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
        out["sharpe_2x"] = round(m2.sharpe, 3)
        if t0 is not None:
            out["sharpe_hw_2x"] = round(hw_sharpe(net2, t0), 3)
    return out
