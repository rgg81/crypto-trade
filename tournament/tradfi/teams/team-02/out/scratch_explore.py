"""team-02 scratch explorer — 52-week-high proximity / anchoring (t02-52wk-high-anchor-v1).

Run from the worktree root:  uv run python tournament/tradfi/teams/team-02/scratch_explore.py exp-001
Data reaches this script ONLY via tournament.engine (manifest-verified frozen IS snapshot).
Signals use team_view(pn) + aux ONLY — pn['ret_fwd'] is touched by te.run_is scoring alone.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import engine as te  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------- signal ------------------------
def ph_signal(view: dict[str, pd.DataFrame], *, L: int = 252, M: int = 126) -> pd.DataFrame:
    """PH = close / rolling_max(high, L, min_periods=M); NaN when close NaN or history < M."""
    close, high = view["close"], view["high"]
    roll_max = high.rolling(L, min_periods=M).max()
    ph = close / roll_max
    return ph.where(close.notna())


def transform(ph: pd.DataFrame, kind: str = "rank", q: float = 1 / 3) -> pd.DataFrame:
    """Cross-sectional transform; output rows are (approximately) dollar-neutral raw books."""
    if kind == "rank":
        r = ph.rank(axis=1, pct=True)
        return r.sub(r.mean(axis=1), axis=0)
    if kind == "zscore":
        mu = ph.mean(axis=1)
        sd = ph.std(axis=1)
        z = ph.sub(mu, axis=0).div(sd, axis=0).clip(-3.0, 3.0)
        return z.sub(z.mean(axis=1), axis=0)
    if kind == "quantile":
        r = ph.rank(axis=1, pct=True)
        w = pd.DataFrame(0.0, index=ph.index, columns=ph.columns).where(ph.notna())
        w = w.mask(r >= 1.0 - q, 1.0).mask(r <= q, -1.0)
        return w
    raise ValueError(kind)


def build_raw(
    view: dict[str, pd.DataFrame],
    *,
    L: int = 252,
    M: int = 126,
    kind: str = "rank",
    q: float = 1 / 3,
    halflife: float | None = None,
    inv_vol: bool = False,
    sign: float = 1.0,
    skip: int = 0,
) -> pd.DataFrame:
    ph = ph_signal(view, L=L, M=M)
    if skip:
        ph = ph.shift(skip).where(view["close"].notna())  # month-old anchor distance,
        # but never a position without a current bar
    s = sign * transform(ph, kind=kind, q=q)
    if halflife is not None:
        s = s.ewm(halflife=halflife, adjust=True, ignore_na=False, min_periods=1).mean()
        s = s.where(ph.notna())  # no position without a current bar + valid anchor
    if inv_vol:
        sigma = view["close"].pct_change().rolling(63, min_periods=40).std()
        s = s / sigma
        s = s.where(sigma.notna())
    return s


# ---------------------------------------------------------------- runner ------------------------
def score(raw: pd.DataFrame, pn: dict, label: str) -> dict:
    _, _, m1 = te.run_is(raw, pn)
    _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
    d = {
        "label": label,
        "sharpe_1x": round(m1.sharpe, 4),
        "sharpe_2x": round(m2.sharpe, 4),
        "maxdd_1x": round(m1.maxdd, 4),
        "ann_turnover": round(m1.ann_turnover, 2),
        "median_long": m1.median_names_long,
        "median_short": m1.median_names_short,
        "mean_gross": round(m1.mean_gross, 3),
        "mean_net": round(m1.mean_net, 4),
        "total_return_1x": round(m1.total_return, 3),
        "n_months": m1.n_months,
        "regime_sharpe_1x": {k: round(v, 3) for k, v in m1.regime_sharpe.items()},
    }
    print(json.dumps(d))
    return d


def main(exp: str) -> None:
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    grids: dict[str, list[dict]] = {
        "exp-001": [dict(L=252, M=126, kind="rank")],
        "exp-002": [dict(L=x, M=min(126, x // 2), kind="rank") for x in (126, 189, 252, 315, 378)],
        "exp-003": [
            dict(L=252, M=126, kind="rank"),
            dict(L=252, M=126, kind="zscore"),
            dict(L=252, M=126, kind="quantile", q=1 / 3),
            dict(L=252, M=126, kind="quantile", q=1 / 5),
        ],
        "exp-004": [dict(L=252, M=126, kind="rank", halflife=h) for h in (None, 5, 10, 21)],
        "exp-005": [
            dict(L=252, M=126, kind="rank", halflife=10, inv_vol=False),
            dict(L=252, M=126, kind="rank", halflife=10, inv_vol=True),
        ],
        "exp-006": [dict(L=252, M=m, kind="rank", halflife=10) for m in (63, 126, 252)],
        # falsification DIAGNOSTIC (pivot-request evidence): reversed sign = anti-anchor book
        "exp-006": [
            dict(L=252, M=126, kind="rank", sign=-1.0),
            dict(L=252, M=126, kind="rank", halflife=5, sign=-1.0),
            dict(L=252, M=126, kind="rank", halflife=10, sign=-1.0),
            dict(L=252, M=126, kind="rank", halflife=21, sign=-1.0),
            dict(L=189, M=94, kind="rank", halflife=10, sign=-1.0),
            dict(L=315, M=126, kind="rank", halflife=10, sign=-1.0),
            dict(L=252, M=126, kind="rank", halflife=10, inv_vol=True, sign=-1.0),
        ],
        # ---- PART C (pivoted family t02-anchor-discount-contrarian-v1, approved) ----
        "exp-007": [dict(L=252, M=126, kind="rank", halflife=h, sign=-1.0) for h in (21, 42, 63)],
        "exp-008": [
            dict(L=x, M=126, kind="rank", halflife=42, sign=-1.0) for x in (252, 378, 504)
        ],
        "exp-009": [
            dict(L=252, M=126, kind="rank", halflife=42, sign=-1.0),
            dict(L=252, M=126, kind="quantile", q=1 / 3, halflife=42, sign=-1.0),
        ],
        "exp-010": [
            dict(L=252, M=126, kind="rank", halflife=42, sign=-1.0, skip=0),
            dict(L=252, M=126, kind="rank", halflife=42, sign=-1.0, skip=21),
        ],
        "exp-011": [
            dict(L=252, M=m, kind="rank", halflife=42, sign=-1.0, skip=21) for m in (63, 126, 252)
        ],
        "exp-012": [  # final confirmation: chosen config + one-step neighbors, every axis
            dict(L=252, M=126, kind="rank", halflife=42, sign=-1.0, skip=21),
            dict(L=189, M=94, kind="rank", halflife=42, sign=-1.0, skip=21),
            dict(L=315, M=126, kind="rank", halflife=42, sign=-1.0, skip=21),
            dict(L=252, M=126, kind="rank", halflife=21, sign=-1.0, skip=21),
            dict(L=252, M=126, kind="rank", halflife=63, sign=-1.0, skip=21),
            dict(L=252, M=126, kind="rank", halflife=42, sign=-1.0, skip=0),
            dict(L=252, M=63, kind="rank", halflife=42, sign=-1.0, skip=21),
            dict(L=252, M=252, kind="rank", halflife=42, sign=-1.0, skip=21),
        ],
    }
    if exp == "shape":  # descriptive plumbing only — not a material experiment
        c = view["close"]
        print(
            json.dumps(
                {
                    "rows": len(c),
                    "names": c.shape[1],
                    "first": str(c.index[0].date()),
                    "last": str(c.index[-1].date()),
                    "names_with_bar_2010": int(c.iloc[:5].notna().any().sum()),
                    "names_with_bar_end": int(c.iloc[-5:].notna().any().sum()),
                    "vix_present": aux["vix"] is not None,
                }
            )
        )
        return
    results = [
        score(build_raw(view, **cfg), pn, label=json.dumps(cfg, sort_keys=True, default=str))
        for cfg in grids[exp]
    ]
    (OUT / f"scratch_{exp}.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
