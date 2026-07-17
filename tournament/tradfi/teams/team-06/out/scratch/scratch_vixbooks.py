"""team-06 scratch engine — VIX-conditional regime books (t06-vix-regime-books-v1, pivot).

Calm state -> cross-sectional 12-1 momentum book; stressed state -> short-horizon reversal
book; state from trailing VIX percentile (or absolute level) with hysteresis or ramp blend.
Run from the worktree root:

    uv run python tournament/tradfi/teams/team-06/scratch_vixbooks.py run '{"tag":"exp-027"}' ...

Ledger discipline lives in the operator workflow: every config's experiments.jsonl line is
appended BEFORE the batch that produces its result runs.
"""

from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import engine as te  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DEF = dict(
    tag="",
    state="pct",  # pct | abs
    pct_win=504,
    hi=0.8,
    lo=0.6,
    abs_hi=25.0,
    abs_lo=20.0,
    blend="hard",  # hard (hysteresis) | ramp (continuous)
    mom_skip=21,
    mom_form=252,
    rev_win=5,
    rev_volstd=False,
    vol_win=21,
    wins=3.0,
    ema_hl=0.0,
    mode="composite",  # composite | mom_only | rev_only
    min_names=10,
    cost_mult=1.0,
)


def _state_series(vix: pd.Series, index: pd.DatetimeIndex, cfg: dict) -> pd.Series:
    v = vix.reindex(index).ffill()
    n = len(index)
    x = v.to_numpy(dtype=float)
    if cfg["state"] == "pct":
        win = int(cfg["pct_win"])
        lvl = np.full(n, np.nan)
        for t in range(n):
            w0 = max(0, t - win + 1)
            seg = x[w0: t + 1]
            seg = seg[np.isfinite(seg)]
            if len(seg) >= 252 and np.isfinite(x[t]):
                lvl[t] = float((seg <= x[t]).mean())
        hi, lo = float(cfg["hi"]), float(cfg["lo"])
    else:  # abs
        lvl = x
        hi, lo = float(cfg["abs_hi"]), float(cfg["abs_lo"])

    if cfg["blend"] == "ramp":
        s = np.clip((lvl - lo) / max(hi - lo, 1e-9), 0.0, 1.0)
        s = np.where(np.isfinite(s), s, 0.0)
    else:  # hard switch with hysteresis, start calm
        s = np.zeros(n)
        cur = 0.0
        for t in range(n):
            if np.isfinite(lvl[t]):
                if lvl[t] >= hi:
                    cur = 1.0
                elif lvl[t] <= lo:
                    cur = 0.0
            s[t] = cur
    return pd.Series(s, index=index)


def _xz_book(sig: pd.DataFrame, cfg: dict, negate: bool) -> pd.DataFrame:
    """Cross-sectional z -> winsorize -> re-demean -> row gross-normalise; thin rows flat."""
    mu = sig.mean(axis=1)
    sd = sig.std(axis=1, ddof=1)
    z = sig.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)
    z = z.clip(-cfg["wins"], cfg["wins"])
    z = z.sub(z.mean(axis=1), axis=0)
    if negate:
        z = -z
    n_valid = z.notna().sum(axis=1)
    z = z.where(n_valid.ge(int(cfg["min_names"])), other=np.nan)
    g = z.abs().sum(axis=1).replace(0.0, np.nan)
    return z.div(g, axis=0).fillna(0.0)


def build_raw(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    cfg = {**DEF, **cfg}
    close = view["close"].astype(float)

    mom_sig = close.shift(int(cfg["mom_skip"])) / close.shift(int(cfg["mom_form"])) - 1.0
    w_mom = _xz_book(mom_sig, cfg, negate=False)

    rev_sig = close / close.shift(int(cfg["rev_win"])) - 1.0
    if cfg["rev_volstd"]:
        dr = np.log(close).diff()
        vol = dr.rolling(int(cfg["vol_win"]), min_periods=int(cfg["vol_win"])).std()
        rev_sig = rev_sig / (vol * np.sqrt(int(cfg["rev_win"]))).replace(0.0, np.nan)
    w_rev = _xz_book(rev_sig, cfg, negate=True)

    if cfg["mode"] == "mom_only":
        s = pd.Series(0.0, index=close.index)
    elif cfg["mode"] == "rev_only":
        s = pd.Series(1.0, index=close.index)
    else:
        s = _state_series(aux["vix"], close.index, cfg)

    out = w_mom.mul(1.0 - s, axis=0) + w_rev.mul(s, axis=0)
    if cfg["ema_hl"] and cfg["ema_hl"] > 0:
        out = out.ewm(halflife=float(cfg["ema_hl"]), min_periods=1).mean()
    return out


def _fmt(m) -> dict:
    d = m.to_dict()
    return {
        "sharpe": round(d["sharpe"], 3),
        "maxdd": round(d["maxdd"], 3),
        "ann_turnover": round(d["ann_turnover"], 1),
        "total_return": round(d["total_return"], 3),
        "med_long": d["median_names_long"],
        "med_short": d["median_names_short"],
        "mean_gross": round(d["mean_gross"], 3),
        "mean_net": round(d["mean_net"], 4),
        "regime_sharpe": {k: round(v, 2) for k, v in d["regime_sharpe"].items()},
    }


def main() -> None:
    assert sys.argv[1] == "run"
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    for arg in sys.argv[2:]:
        cfg = {**DEF, **json.loads(arg)}
        t0 = time.time()
        raw = build_raw(view, aux, cfg)
        net, w, m = te.run_is(raw, pn, cost_mult=float(cfg.get("cost_mult", 1.0)))
        res = {"tag": cfg["tag"], "cfg": {k: v for k, v in cfg.items() if v != DEF.get(k)},
               "metrics": _fmt(m), "wall_s": round(time.time() - t0, 1)}
        print(json.dumps(res))


if __name__ == "__main__":
    main()
