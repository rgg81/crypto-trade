"""team-09 scratch — trade-size composition signal (research_brief.md v3 Section 2)."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

DEFAULTS = dict(
    W=21, B=90, h=9, transform="rank", min_names=10, zclip=3.0,
    source="comp",  # comp | vol_ctrl | cnt_ctrl  (F3 controls)
)


def _sums(f: pd.DataFrame, w: int) -> pd.DataFrame:
    return f.rolling(w, min_periods=int(np.ceil(0.8 * w))).sum()


def build_signal(pn: dict, aux: dict, **over) -> pd.DataFrame:
    p = {**DEFAULTS, **over}
    W, B, h = int(p["W"]), int(p["B"]), int(p["h"])
    qv, tr_ = pn["quote_volume"], pn["trades"]
    elig = aux["eligibility"]

    if p["source"] == "comp":
        ats_num = _sums(qv, W) / _sums(tr_, W)
        ats_den = (_sums(qv, B) / _sums(tr_, B)).shift(W)
        raw = np.log(ats_num / ats_den)
    elif p["source"] == "vol_ctrl":  # F3: fade volume-attention alone
        raw = -np.log((_sums(qv, W) / _sums(qv, B).shift(W)) * (B / W))
    elif p["source"] == "cnt_ctrl":  # F3: fade count-attention alone
        raw = -np.log((_sums(tr_, W) / _sums(tr_, B).shift(W)) * (B / W))
    else:
        raise ValueError(p["source"])
    raw = raw.replace([np.inf, -np.inf], np.nan).where(elig)

    if p["transform"] == "rank":
        r = raw.rank(axis=1)
        sig = r.sub(r.mean(axis=1), axis=0).div(r.count(axis=1).clip(lower=1), axis=0)
    elif p["transform"] == "z":
        mu = raw.mean(axis=1)
        sd = raw.std(axis=1)
        sig = raw.sub(mu, axis=0).div(sd, axis=0).clip(-p["zclip"], p["zclip"])
    else:
        raise ValueError(p["transform"])

    n_valid = raw.notna().sum(axis=1)
    sig = sig.where(n_valid >= int(p["min_names"]))
    return sig.rolling(h, min_periods=max(1, int(np.ceil(0.8 * h)))).mean()


def score(raw_sig: pd.DataFrame, pn: dict, scoring: dict, cost_mult=1.0, slip_mult=1.0):
    raw_sig = te.conform_raw(raw_sig, pn)
    net, w, parts = te.net_series(raw_sig, pn, scoring, cost_mult=cost_mult, slip_mult=slip_mult)
    m = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    return net, w, parts, m


def brief_row(tag: str, m) -> str:
    return (
        f"{tag:26s} SR={m.sharpe:+.3f} DD={m.maxdd:+.3f} TO={m.ann_turnover:6.1f} "
        f"br=({m.median_names_long:.0f}/{m.median_names_short:.0f}) "
        f"fund={m.total_funding_pnl:+.4f} cost={m.total_cost:.4f} "
        f"bull={m.regime_sharpe.get('bull', float('nan')):+.2f} "
        f"bear={m.regime_sharpe.get('bear', float('nan')):+.2f} "
        f"chop={m.regime_sharpe.get('chop', float('nan')):+.2f}"
    )
