"""team-02 scratch common — evaluator access + signal forms (scratch-only; QE re-implements).

Scratch scripts run INSIDE tournament/crypto/teams/team-02/out/scratch/ and MAY import the
evaluator (out/ is excluded from the harness scan / frozen bundle).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

_CACHE: dict = {}


def panels():
    if "pn" not in _CACHE:
        pn, aux, scoring = te.load_is_panels()
        _CACHE.update(pn=pn, aux=aux, scoring=scoring)
    return _CACHE["pn"], _CACHE["aux"], _CACHE["scoring"]


def crank(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional rank in (0,1): (rank - 0.5) / N among non-NaN entries per row."""
    r = df.rank(axis=1)
    n = df.notna().sum(axis=1)
    return r.sub(0.5).div(n, axis=0)


def build_and_move(pn, aux, L: int):
    """(b, r) log-changes over L candles, masked to eligible+positive-OI names."""
    oi = aux["oi"].where(aux["oi"] > 0)
    close = pn["close"].where(pn["close"] > 0)
    b = np.log(oi) - np.log(oi.shift(L))
    r = np.log(close) - np.log(close.shift(L))
    elig = aux["eligibility"]
    mask = elig & b.notna() & r.notna()
    return b.where(mask), r.where(mask)


def form_A(pn, aux, L: int, q: float = 0.6) -> pd.DataFrame:
    b, r = build_and_move(pn, aux, L)
    g = (crank(b) - q).clip(lower=0.0) / (1.0 - q)
    return -(g * np.sign(r))


def form_B(pn, aux, L: int) -> pd.DataFrame:
    b, r = build_and_move(pn, aux, L)
    return -((2.0 * crank(b) - 1.0) * (2.0 * crank(r) - 1.0))


def form_C(pn, aux, L: int, q: float = 0.6) -> pd.DataFrame:
    b, r = build_and_move(pn, aux, L)
    lr1 = np.log(pn["close"].where(pn["close"] > 0)).diff()
    sig = lr1.rolling(42, min_periods=30).std()
    stag = 1.0 - crank((r.abs() / sig).where(b.notna()))
    g = (crank(b) - q).clip(lower=0.0) / (1.0 - q)
    return -(g * np.sign(r) * stag)


def smooth(s: pd.DataFrame, k: int) -> pd.DataFrame:
    s = s.fillna(0.0)
    if k <= 1:
        return s
    return s.ewm(span=k).mean()


def score(raw: pd.DataFrame, cost_mult: float = 1.0, slip_mult: float = 1.0):
    pn, aux, scoring = panels()
    raw = te.conform_raw(raw.fillna(0.0), pn)
    net, w, parts = te.net_series(raw, pn, scoring, cost_mult=cost_mult, slip_mult=slip_mult)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    return net, w, parts, m


def line(tag: str, m) -> str:
    rs = {k: (None if v != v else round(v, 2)) for k, v in m.regime_sharpe.items()}
    return (
        f"{tag:34s} S={m.sharpe:+.3f} dd={m.maxdd:+.3f} to={m.ann_turnover:7.1f} "
        f"nl/ns={m.median_names_long:.0f}/{m.median_names_short:.0f} "
        f"fund={m.total_funding_pnl:+.3f} cost={m.total_cost:.3f} reg={rs}"
    )
