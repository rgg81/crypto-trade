"""team-09 scratch lab — t09-short-max-lottery-v1 (QR design phase, IS only).

Usage (from worktree root):
    uv run python tournament/tradfi/teams/team-09/scratch_max_lab.py '<json-config>'

Config keys:
    id            str   experiment id (out/<id>_metrics.json)
    k             int   top-k daily returns averaged (ignored if sigma_only)
    L             int   trailing window in trading days
    vol_adj       bool  SMAX = MAX/sigma(L)            (default false)
    sigma_only    bool  DIAGNOSTIC: rank on sigma(L) alone (default false)
    sector_demean bool  sector row-demean before rank  (default false)
    smooth_hl     float EMA halflife on weight panel, 0 = off (default 0)
    sign          int   +1 classic (short high-MAX), -1 reversed DIAGNOSTIC (default +1)

Data reaches this script ONLY via tournament.engine (manifest-verified frozen IS snapshot).
Signals are built from team_view(pn) + aux only; ret_fwd is never touched here.
"""

import json
import math
import sys

sys.path.insert(0, "analysis/portfolio/tradfi")

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from tournament import engine as te


def topk_mean_trailing(ret: pd.DataFrame, k: int, L: int, min_obs: int) -> pd.DataFrame:
    """Mean of the k largest values in each trailing L-window (per column); NaN if < min_obs."""
    v = ret.to_numpy(dtype=float)  # T x N
    T, N = v.shape
    out = np.full((T, N), np.nan)
    if T < L:
        return pd.DataFrame(out, index=ret.index, columns=ret.columns)
    win = sliding_window_view(v, L, axis=0)  # (T-L+1) x N x L
    valid = (~np.isnan(win)).sum(axis=2)  # (T-L+1) x N
    filled = np.where(np.isnan(win), -np.inf, win)
    part = np.partition(filled, L - k, axis=2)[:, :, L - k :]  # top-k (may include -inf)
    tk = part.mean(axis=2)
    ok = (valid >= min_obs) & np.isfinite(tk)
    res = np.where(ok, tk, np.nan)
    out[L - 1 :, :] = res
    return pd.DataFrame(out, index=ret.index, columns=ret.columns)


def build_raw(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    k = int(cfg.get("k", 1))
    L = int(cfg.get("L", 21))
    min_obs = max(15, math.ceil(0.6 * L))
    close = view["close"]
    ret = close / close.shift(1) - 1.0

    sigma = ret.rolling(L, min_periods=min_obs).std()
    if cfg.get("sigma_only", False):
        sig = sigma
    else:
        sig = topk_mean_trailing(ret, k, L, min_obs)
        if cfg.get("vol_adj", False):
            sig = sig / sigma.replace(0.0, np.nan)

    if cfg.get("sector_demean", False):
        smap = aux["sector_map"]
        gmean = sig.mean(axis=1)
        out = sig.copy()
        for sec in sorted(set(smap.values())):
            cols = [c for c in sig.columns if smap.get(c) == sec]
            if not cols:
                continue
            block = sig[cols]
            n = block.notna().sum(axis=1)
            smean = block.mean(axis=1).where(n >= 3, gmean)
            out[cols] = block.sub(smean, axis=0)
        sig = out

    rank = sig.rank(axis=1, method="average")
    n = sig.notna().sum(axis=1)
    c = rank.sub((n + 1) / 2.0, axis=0).div(n, axis=0)
    w = float(cfg.get("sign", 1)) * (-c)

    if cfg.get("half_book", False):
        # E1: long the low-MAX (boring) half; short the SAME gross equally across all
        # valid names (equal-weight basket hedge). Row-sum returns to ~0.
        long_leg = w.clip(lower=0.0).where(sig.notna())
        gross_long = long_leg.sum(axis=1)
        valid = sig.notna()
        spread = gross_long.div(valid.sum(axis=1).replace(0, np.nan))
        w = long_leg.fillna(0.0) - valid.mul(spread, axis=0).fillna(0.0)

    w = w.where(n >= 10, other=0.0).fillna(0.0)

    p = cfg.get("vix_gate_pct", None)
    if p is not None:
        vix = aux["vix"].astype(float)
        thr = vix.rolling(252, min_periods=126).quantile(float(p)).shift(1)
        gate = (vix > thr).astype(float)
        gate = gate.reindex(w.index).ffill(limit=5).fillna(0.0)
        w = w.mul(gate, axis=0)

    hl = float(cfg.get("smooth_hl", 0) or 0)
    if hl > 0:
        w = w.ewm(halflife=hl, min_periods=1).mean()
    return w


def main() -> None:
    cfg = json.loads(sys.argv[1])
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    raw = build_raw(view, aux, cfg)
    _, _, m1 = te.run_is(raw, pn)
    _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
    out = {"config": cfg, "cost_1x": m1.to_dict(), "cost_2x": m2.to_dict()}
    path = f"tournament/tradfi/teams/team-09/out/{cfg['id']}_metrics.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(
        f"[{cfg['id']}] 1x Sharpe={m1.sharpe:+.3f} maxDD={m1.maxdd:+.3f} "
        f"turn={m1.ann_turnover:.1f} breadth L/S={m1.median_names_long:.0f}/"
        f"{m1.median_names_short:.0f} | 2x Sharpe={m2.sharpe:+.3f} | "
        f"regimes {m1.regime_sharpe}"
    )


if __name__ == "__main__":
    main()
