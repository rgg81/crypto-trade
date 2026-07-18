"""team-09 scratch — liq/squeeze-reversal signal builder + eval helpers.

Scratch-only (out/scratch is excluded from harness scan & frozen bundle).
Implements EXACTLY the research_brief.md Section 2 pipeline.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

DEFAULTS = dict(
    k=2,
    h=6,
    gamma=1.0,
    sig_win=42,
    sig_minp=28,
    base=90,
    base_minp=60,
    xmax=6.0,
    ev_cap=8.0,
    sig_floor=0.001,
    demean=True,
    oi_w=0.0,
    oi_x_cap=0.5,
    oi_mult_cap=2.0,
    rank=False,          # robustness alternative: cross-sectional rank of sm
    evidence="combined",  # "combined" | "range" | "volume"
)


def build_signal(pn: dict, aux: dict, **over) -> pd.DataFrame:
    p = {**DEFAULTS, **over}
    close, high, low, qv = pn["close"], pn["high"], pn["low"], pn["quote_volume"]
    k, h = int(p["k"]), int(p["h"])

    r1 = np.log(close).diff()
    sigma = r1.rolling(p["sig_win"], min_periods=p["sig_minp"]).std()
    sigma = sigma.clip(lower=p["sig_floor"])
    x = (r1.rolling(k).sum() / (sigma * np.sqrt(k))).clip(-p["xmax"], p["xmax"])

    tr = (high - low) / close
    rs = tr.rolling(k).mean() / tr.rolling(p["base"], min_periods=p["base_minp"]).mean().shift(k)
    vs = qv.rolling(k).mean() / qv.rolling(p["base"], min_periods=p["base_minp"]).mean().shift(k)
    if p["evidence"] == "combined":
        ev = np.sqrt(rs * vs)
    elif p["evidence"] == "range":
        ev = rs
    elif p["evidence"] == "volume":
        ev = vs
    else:
        raise ValueError(p["evidence"])
    ev = ev.clip(lower=0.0, upper=p["ev_cap"])

    s = -x * ev ** p["gamma"]

    if p["oi_w"] > 0:
        oi = aux["oi"]
        oi_x = (-(oi / oi.shift(k) - 1.0)).clip(lower=0.0, upper=p["oi_x_cap"])
        m_oi = (1.0 + p["oi_w"] * oi_x / 0.10).clip(upper=1.0 + p["oi_mult_cap"])
        m_oi = m_oi.fillna(1.0)  # NaN OI -> kline-only fallback
        s = s * m_oi

    sm = s.rolling(h).mean()

    elig = aux["eligibility"]
    sm = sm.where(elig)  # only eligible names carry signal (engine masks anyway)
    if p["rank"]:
        sm = sm.rank(axis=1)  # 1..n across valid names
    if p["demean"]:
        sm = sm.sub(sm.mean(axis=1), axis=0)
    return sm


def score(raw: pd.DataFrame, pn: dict, scoring: dict, cost_mult=1.0, slip_mult=1.0):
    raw = te.conform_raw(raw, pn)
    net, w, parts = te.net_series(raw, pn, scoring, cost_mult=cost_mult, slip_mult=slip_mult)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    return net, w, parts, m


def sub_sharpe(net: pd.Series, lo: str, hi: str) -> float:
    return te.msharpe(net, pd.Timestamp(lo), pd.Timestamp(hi))


def brief_row(tag: str, m) -> str:
    return (
        f"{tag:28s} SR={m.sharpe:+.3f} DD={m.maxdd:+.3f} TO={m.ann_turnover:7.1f} "
        f"br=({m.median_names_long:.0f}/{m.median_names_short:.0f}) "
        f"fund={m.total_funding_pnl:+.4f} cost={m.total_cost:.4f} "
        f"bull={m.regime_sharpe.get('bull', float('nan')):+.2f} "
        f"bear={m.regime_sharpe.get('bear', float('nan')):+.2f} "
        f"chop={m.regime_sharpe.get('chop', float('nan')):+.2f}"
    )
