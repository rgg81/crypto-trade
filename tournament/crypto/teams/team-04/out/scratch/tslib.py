"""team-04 scratch — TS-trend signal builder + evaluator wrapper (out/scratch only).

Pre-registered signal space (research_brief.md section 4):
  score_L = ln(C/C.shift(L)) / (vol * sqrt(L)); vol = rolling std of 8h log returns (V, V//2)
  blended = NaN-skipping mean over horizons of clip(score_L, -Z, Z)   [or sign(score_L)]
  w_raw   = blended [/ vol if invvol]  -> optional EMA span E
Engine owns everything else.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

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


def build_signal(
    close: pd.DataFrame,
    H=(21, 63, 126, 252),
    Z: float = 2.0,
    invvol: bool = True,
    E: int = 1,
    V: int = 63,
    transform: str = "clip",  # "clip" | "sign" | "raw"
) -> pd.DataFrame:
    lp = np.log(close.astype(float))
    r = lp.diff(1)
    vol = r.rolling(V, min_periods=V // 2).std()
    vol = vol.where(vol > 1e-6)
    num = None
    cnt = None
    for L in H:
        s = (lp - lp.shift(L)) / (vol * np.sqrt(L))
        if transform == "clip":
            s = s.clip(-Z, Z)
        elif transform == "sign":
            s = np.sign(s)
        elif transform != "raw":
            raise ValueError(transform)
        m = s.notna()
        s0 = s.fillna(0.0)
        num = s0 if num is None else num + s0
        cnt = m.astype(float) if cnt is None else cnt + m.astype(float)
    sig = num / cnt.replace(0.0, np.nan)
    w = sig / vol if invvol else sig
    if E and E > 1:
        w = w.ewm(span=E, min_periods=1).mean()
        w = w.where(sig.notna())  # EMA must not resurrect flat cells
    return w


def score(raw: pd.DataFrame, label: str = "", stress: bool = True) -> dict:
    pn, aux, scoring = panels()
    raw = te.conform_raw(raw, pn)
    net, w, parts = te.net_series(raw, pn, scoring)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    out = {
        "label": label,
        "sharpe": round(m.sharpe, 3),
        "maxdd": round(m.maxdd, 3),
        "turn": round(m.ann_turnover, 1),
        "medL": m.median_names_long,
        "medS": m.median_names_short,
        "gross": round(m.mean_gross, 3),
        "net_exp": round(m.mean_net, 3),
        "fpnl": round(m.total_funding_pnl, 4),
        "cost": round(m.total_cost, 4),
        "reg": {k: round(v, 2) for k, v in m.regime_sharpe.items()},
    }
    if stress:
        net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
        m2 = te.evaluate(net2, w2, p2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
        out["sharpe2x"] = round(m2.sharpe, 3)
    return out


def run_config(label: str, stress: bool = True, **kw) -> dict:
    pn, _, _ = panels()
    return score(build_signal(pn["close"], **kw), label=label, stress=stress)


def fmt(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        lines.append(
            f"{r['label']:<28} S1x={r['sharpe']:+.3f} S2x={r.get('sharpe2x', float('nan')):+.3f} "
            f"dd={r['maxdd']:+.3f} T={r['turn']:6.1f} L/S={r['medL']:.0f}/{r['medS']:.0f} "
            f"g={r['gross']:.2f} n={r['net_exp']:+.3f} f={r['fpnl']:+.4f} c={r['cost']:.4f} "
            f"reg={r['reg']}"
        )
    return "\n".join(lines)
