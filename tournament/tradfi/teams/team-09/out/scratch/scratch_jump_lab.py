"""team-09 scratch lab — t09-jump-momentum-v1 (QR design phase, IS only).

Short-horizon jump/attention continuation: LONG high recent-jump names, short the boring end.
Direction is hard-coded (w = +centered-rank of the jump statistic) — family fidelity.
aux['vix'] is NEVER read (no regime switching; out of family bounds).

Usage (from worktree root):
    uv run python tournament/tradfi/teams/team-09/scratch_jump_lab.py '<json-config>'

Config keys:
    id            str   experiment id (out/<id>_metrics.json)
    k             int   top-k daily returns averaged (default 1)
    L             int   trailing window, trading days (<= 42; short-horizon family bound)
    d             int   skip days between window end and decision day (default 0)
    vol_adj       bool  JUMP/sigma(L)                  (default false)
    sector_demean bool  sector row-demean before rank  (default false)
    tercile       bool  +1/0/-1 tercile book instead of linear rank (default false)
    smooth_hl     float EMA halflife on weight panel, 0 = off (default 0)

Data reaches this script ONLY via tournament.engine (manifest-verified frozen IS snapshot).
Signals use team_view(pn)['close'] + aux['sector_map'] only; ret_fwd is never touched here.
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
    valid = (~np.isnan(win)).sum(axis=2)
    filled = np.where(np.isnan(win), -np.inf, win)
    part = np.partition(filled, L - k, axis=2)[:, :, L - k :]
    tk = part.mean(axis=2)
    ok = (valid >= min_obs) & np.isfinite(tk)
    out[L - 1 :, :] = np.where(ok, tk, np.nan)
    return pd.DataFrame(out, index=ret.index, columns=ret.columns)


def build_raw(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    k = int(cfg.get("k", 1))
    L = int(cfg.get("L", 21))
    if L > 42:
        raise ValueError("family bound: short-horizon only (L <= 42)")
    d = int(cfg.get("d", 0))
    min_obs = max(min(15, L - 2), math.ceil(0.6 * L))
    close = view["close"]
    ret = close / close.shift(1) - 1.0

    sig = topk_mean_trailing(ret, k, L, min_obs)
    if cfg.get("vol_adj", False):
        sigma = ret.rolling(L, min_periods=min_obs).std()
        sig = sig / sigma.replace(0.0, np.nan)
    if d > 0:
        sig = sig.shift(d)

    if cfg.get("sector_demean", False):
        smap = aux["sector_map"]
        gmean = sig.mean(axis=1)
        out = sig.copy()
        for sec in sorted(set(smap.values())):
            cols = [c for c in sig.columns if smap.get(c) == sec]
            if not cols:
                continue
            block = sig[cols]
            nsec = block.notna().sum(axis=1)
            smean = block.mean(axis=1).where(nsec >= 3, gmean)
            out[cols] = block.sub(smean, axis=0)
        sig = out

    rank = sig.rank(axis=1, method="average")
    n = sig.notna().sum(axis=1)
    if cfg.get("tercile", False):
        lo_cut = n / 3.0
        hi_cut = 2.0 * n / 3.0
        w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
        w = w.mask(rank.gt(hi_cut, axis=0), 1.0)
        w = w.mask(rank.le(lo_cut, axis=0), -1.0)
        w = w.where(sig.notna(), 0.0)
    else:
        c = rank.sub((n + 1) / 2.0, axis=0).div(n, axis=0)
        w = c  # LONG high-jump, short boring — family direction, hard-coded

    w = w.where(n >= 10, other=0.0).fillna(0.0)

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
