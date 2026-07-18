"""team-07 scratch helpers — vol-structure cross-section research.

Scratch-only (out/scratch is excluded from the harness scan and the frozen bundle), so this
module MAY import the evaluator. Team strategy code must NOT.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament")
if str(ROOT / "analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "analysis"))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

_CACHE: dict = {}


def panels():
    if "pn" not in _CACHE:
        pn, aux, scoring = te.load_is_panels()
        _CACHE.update(pn=pn, aux=aux, scoring=scoring)
    return _CACHE["pn"], _CACHE["aux"], _CACHE["scoring"]


def minp(W: int) -> int:
    return max(8, int(np.ceil(0.75 * W)))


# ------------------------------------------------------------------ vol estimators (past-only,
# same-bar close/high/low of candle t usable at t's close per charter)
def cc_vol(pn, W: int) -> pd.DataFrame:
    r = np.log(pn["close"]).diff()
    return r.rolling(W, min_periods=minp(W)).std()


def pk_vol(pn, W: int) -> pd.DataFrame:
    lr2 = np.log(pn["high"] / pn["low"]) ** 2
    return np.sqrt(lr2.rolling(W, min_periods=minp(W)).mean() / (4.0 * np.log(2.0)))


def q90_ret(pn, W: int) -> pd.DataFrame:
    """Lottery right-tail proxy: rolling 90th percentile of 8h simple returns."""
    r = pn["close"].pct_change()
    return r.rolling(W, min_periods=minp(W)).quantile(0.9)


def idio_vol(pn, W: int, beta_win: int = 126) -> pd.DataFrame:
    """Vol of the return component residual to BTC (rolling beta, past-only windows)."""
    r = np.log(pn["close"]).diff()
    btc = r["BTCUSDT"]
    cov = r.rolling(beta_win, min_periods=minp(beta_win)).cov(btc)
    var = btc.rolling(beta_win, min_periods=minp(beta_win)).var()
    beta = cov.div(var, axis=0)
    resid = r.sub(beta.mul(btc, axis=0))
    return resid.rolling(W, min_periods=minp(W)).std()


def vol_trend(pn, short: int = 21, long: int = 126) -> pd.DataFrame:
    return cc_vol(pn, short) / cc_vol(pn, long)


# ------------------------------------------------------------------ transform
def rank_signal(score: pd.DataFrame, elig: pd.DataFrame, sign: float = -1.0) -> pd.DataFrame:
    """Eligible-only percentile rank, row-demeaned, sign=-1 => long low score / short high."""
    v = score.where(elig)
    p = v.rank(axis=1, pct=True)
    w = sign * p.sub(p.mean(axis=1), axis=0)
    return w.fillna(0.0)


# ------------------------------------------------------------------ evaluation
def run(raw: pd.DataFrame, tag: str, lo=None, hi=None, quiet=False) -> dict:
    pn, aux, scoring = panels()
    lo = tc.TRN_IS_START if lo is None else lo
    hi = tc.TRN_IS_HI if hi is None else hi
    raw = te.conform_raw(raw, pn)
    net1, w1, p1 = te.net_series(raw, pn, scoring)
    m1 = te.evaluate(net1, w1, p1, lo=lo, hi=hi)
    net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
    m2 = te.evaluate(net2, w2, p2, lo=lo, hi=hi)
    pre = p1["pnl"] + p1["fpnl"]
    pre_sum = float(pre[(pre.index >= lo) & (pre.index < hi)].sum())
    row = {
        "tag": tag,
        "sharpe_1x": round(m1.sharpe, 3),
        "sharpe_2x": round(m2.sharpe, 3),
        "maxdd": round(m1.maxdd, 3),
        "ann_to": round(m1.ann_turnover, 1),
        "med_L": m1.median_names_long,
        "med_S": m1.median_names_short,
        "mean_net": round(m1.mean_net, 4),
        "regime": {k: round(v, 2) for k, v in m1.regime_sharpe.items()},
        "fund_pnl": round(m1.total_funding_pnl, 4),
        "cost": round(m1.total_cost, 4),
        "precost_xs": round(pre_sum, 4),
        "total_ret": round(m1.total_return, 3),
    }
    if not quiet:
        print(
            f"{tag:28s} S1x={row['sharpe_1x']:+.3f} S2x={row['sharpe_2x']:+.3f} "
            f"dd={row['maxdd']:+.3f} to={row['ann_to']:.0f} L/S={row['med_L']:.0f}/"
            f"{row['med_S']:.0f} net={row['mean_net']:+.4f} reg={row['regime']} "
            f"fund={row['fund_pnl']:+.3f} cost={row['cost']:.3f} pre={row['precost_xs']:+.3f}"
        )
    return row


def msharpe_window(raw: pd.DataFrame, lo, hi) -> float:
    pn, aux, scoring = panels()
    raw = te.conform_raw(raw, pn)
    net1, w1, p1 = te.net_series(raw, pn, scoring)
    return te.msharpe(net1, pd.Timestamp(lo), pd.Timestamp(hi))
