"""team-03 scratch — residual-momentum signal builder + evaluator wrapper.

Scratch-only (out/ is excluded from the harness scan and the frozen bundle). Imports the
evaluator for data access, per the orchestrator's research-phase instructions. The formulas
here mirror research_brief.md Section 4 exactly; strategy.py (QE) will re-implement them
WITHOUT importing the evaluator.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

BULL2021_LO = pd.Timestamp("2020-03-13")
BULL2021_HI = pd.Timestamp("2021-04-14")

_PANELS = None
_FACTOR_CACHE: dict = {}
_BETA_CACHE: dict = {}
_RESID_CACHE: dict = {}


def panels():
    global _PANELS
    if _PANELS is None:
        _PANELS = te.load_is_panels()
    return _PANELS


def _elig(pn, aux):
    return aux["eligibility"].reindex(columns=pn["close"].columns).fillna(False).astype(bool)


def market_factor(pn, aux, kind: str) -> pd.Series:
    """EW: eligible-mean log return. DVW: trailing-dvol-weighted mean (BTC/ETH-dominated)."""
    key = kind
    if key in _FACTOR_CACHE:
        return _FACTOR_CACHE[key]
    r = np.log(pn["close"]).diff()
    elig = _elig(pn, aux)
    valid = r.notna() & elig
    if kind == "EW":
        n = valid.sum(axis=1)
        m = r.where(valid).mean(axis=1).where(n >= 5)
    elif kind == "DVW":
        wgt = pn["quote_volume"].rolling(21, min_periods=18).mean().shift(1)
        wv = wgt.where(valid)
        n = (wv.notna() & r.notna()).sum(axis=1)
        m = ((r * wv).sum(axis=1) / wv.sum(axis=1)).where(n >= 5)
    else:
        raise ValueError(kind)
    _FACTOR_CACHE[key] = m
    return m


def residuals(pn, aux, market: str, w_beta: int) -> pd.DataFrame:
    key = (market, w_beta)
    if key in _RESID_CACHE:
        return _RESID_CACHE[key]
    r = np.log(pn["close"]).diff()
    m = market_factor(pn, aux, market)
    mp = w_beta // 2
    cov = r.rolling(w_beta, min_periods=mp).cov(m)
    var = m.rolling(w_beta, min_periods=mp).var()
    beta = cov.div(var, axis=0).clip(0.0, 3.0)
    e = r.sub(beta.mul(m, axis=0))
    _BETA_CACHE[key] = beta
    _RESID_CACHE[key] = e
    return e


def build_signal(pn, aux, cfg: dict) -> pd.DataFrame:
    """cfg: market, w_beta, L, g, scaling ('sum'|'tstat'), K, weighting ('rank'|'tb12'),
    resid ('yes'|'no' — 'no' = plain XS momentum on raw log returns, context anchor)."""
    if cfg.get("resid", "yes") == "yes":
        e = residuals(pn, aux, cfg["market"], cfg["w_beta"])
    else:
        e = np.log(pn["close"]).diff()
    L, g = cfg["L"], cfg["g"]
    mp_l = int(np.ceil(0.8 * L))
    if cfg["scaling"] == "sum":
        s = e.rolling(L, min_periods=mp_l).sum()
    elif cfg["scaling"] == "tstat":
        s = e.rolling(L, min_periods=mp_l).mean() / e.rolling(L, min_periods=mp_l).std()
    else:
        raise ValueError(cfg["scaling"])
    s = s.shift(g)
    s = s.where(_elig(pn, aux))
    if cfg["weighting"] == "rank":
        rk = s.rank(axis=1, pct=True)
        w = rk.sub(rk.mean(axis=1), axis=0)
    elif cfg["weighting"] == "tb12":
        top = s.rank(axis=1, ascending=False) <= 12
        bot = s.rank(axis=1, ascending=True) <= 12
        w = top.astype(float) - bot.astype(float)
        w = w.where(s.notna(), 0.0)
    else:
        raise ValueError(cfg["weighting"])
    w = w.fillna(0.0)
    k = cfg.get("K", 1)
    if k > 1:
        w = w.ewm(span=k, adjust=True).mean()
    return w


def score(cfg: dict, *, stress: bool = False, extras: bool = False) -> dict:
    pn, aux, scoring = panels()
    raw = te.conform_raw(build_signal(pn, aux, cfg), pn)
    net, w, parts = te.net_series(raw, pn, scoring)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    out = {"cfg": cfg, "sharpe_1x": round(m.sharpe, 3), "maxdd": round(m.maxdd, 3),
           "ann_turnover": round(m.ann_turnover, 1), "total_return": round(m.total_return, 3),
           "med_long": m.median_names_long, "med_short": m.median_names_short,
           "regime": {k: round(v, 2) for k, v in m.regime_sharpe.items()},
           "fund_pnl": round(m.total_funding_pnl, 4), "cost": round(m.total_cost, 4)}
    if stress:
        net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
        m2 = te.evaluate(net2, w2, p2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
        out["sharpe_2x"] = round(m2.sharpe, 3)
    if extras:
        in_bull = (net.index >= BULL2021_LO) & (net.index < BULL2021_HI)
        out["sharpe_ex_bull2021"] = round(te.msharpe(net[~in_bull], tc.TRN_IS_START, tc.TRN_IS_HI), 3)
        net_nf, w_nf, p_nf = te.net_series(raw, pn, scoring, apply_funding=False)
        out["sharpe_no_funding"] = round(te.msharpe(net_nf, tc.TRN_IS_START, tc.TRN_IS_HI), 3)
    return out
