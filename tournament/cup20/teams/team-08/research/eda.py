"""Cross-sectional information-coefficient EDA for the funding / basis dynamics lane.

Measures are formed at boundary t from funding rows strictly before t, and scored
against the forward h-bar net-of-funding return the book would actually earn. No
trial is spent here; this is the map that decides where trials go.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-08/research")
from panel import build_panel, observation_lags  # noqa: E402
from signals import rolling_means, xs_orthogonalise  # noqa: E402

CACHE = (
    "/tmp/claude-1000/-home-roberto-crypto-trade--worktrees-"
    "quant-portfolio-blind-top20-low-dd/6c9e8e1e-1fa6-43e6-85e2-97a8d7826612/scratchpad"
)


def load(depth=90):
    panel = build_panel()
    try:
        d = np.load(f"{CACHE}/lags{depth}.npz")
        rate, bas = d["rate"], d["bas"]
    except FileNotFoundError:
        rate, bas = observation_lags(panel, depth)
        rate, bas = rate.astype(np.float32), bas.astype(np.float32)
        np.savez_compressed(f"{CACHE}/lags{depth}.npz", rate=rate, bas=bas)
    return panel, rate, bas


def forward_return(panel, h):
    """Total return including funding over the next h bars, per symbol."""
    fwd, fund = panel["fwd"], panel["fund_hold"]
    r = np.nan_to_num(fwd, nan=0.0) - fund
    n_t = r.shape[0]
    out = np.full(r.shape, np.nan)
    c = np.cumsum(np.vstack([np.zeros((1, r.shape[1])), r]), axis=0)
    valid_h = min(h, n_t)
    out[: n_t - valid_h] = c[valid_h : n_t] - c[0 : n_t - valid_h]
    # invalidate windows where the symbol had no bar
    ok = np.isfinite(fwd)
    okc = np.cumsum(np.vstack([np.zeros((1, r.shape[1])), ok.astype(float)]), axis=0)
    full = (okc[valid_h:n_t] - okc[0 : n_t - valid_h]) >= valid_h
    out[: n_t - valid_h][~full] = np.nan
    return out


def spearman_ic(sig, ret, elig, stride=1):
    ics = []
    for t in range(0, sig.shape[0], stride):
        m = elig[t] & np.isfinite(sig[t]) & np.isfinite(ret[t])
        n = int(m.sum())
        if n < 8:
            continue
        a = pd.Series(sig[t, m]).rank().to_numpy()
        b = pd.Series(ret[t, m]).rank().to_numpy()
        a = a - a.mean()
        b = b - b.mean()
        d = np.sqrt((a * a).sum() * (b * b).sum())
        if d <= 0:
            continue
        ics.append(float((a * b).sum() / d))
    ics = np.asarray(ics)
    if len(ics) < 10:
        return np.nan, np.nan, 0
    return float(ics.mean()), float(ics.mean() / ics.std(ddof=1) * np.sqrt(len(ics))), len(ics)


def main():
    panel, rate, bas = load()
    elig = panel["elig"]
    rm = rolling_means(rate)
    bm = rolling_means(bas)

    print(f"funding obs at exactly 1bp: {np.nanmean(np.isclose(rate[0], 1e-4)):.3f}")
    print(f"funding obs |rate|<0.5bp:  {np.nanmean(np.abs(rate[0]) < 0.5e-4):.3f}")
    d1 = rate[0] - rate[1]
    print(f"1-lag funding change exactly zero: {np.nanmean(np.isclose(d1, 0.0)):.3f}")
    db = bas[0] - bas[1]
    print(f"1-lag basis change exactly zero:   {np.nanmean(np.isclose(db, 0.0)):.4f}")
    print()

    measures = {}
    for k in (3, 6, 9, 15, 21, 30, 45, 63, 90):
        measures[f"fund_level_{k}"] = rm[k - 1]
        measures[f"basis_level_{k}"] = bm[k - 1]
    for ks in (1, 3, 6, 9, 15):
        for kl in (9, 15, 21, 30, 45, 63, 90):
            if kl <= ks * 2:
                continue
            measures[f"fund_spread_{ks}_{kl}"] = rm[ks - 1] - rm[kl - 1]
            measures[f"basis_spread_{ks}_{kl}"] = bm[ks - 1] - bm[kl - 1]

    horizons = (3, 9, 21, 45)
    rets = {h: forward_return(panel, h) for h in horizons}

    rows = []
    for name, sig in measures.items():
        row = {"measure": name}
        for h in horizons:
            ic, t, n = spearman_ic(sig, rets[h], elig, stride=3)
            row[f"ic{h}"] = ic
            row[f"t{h}"] = t
        rows.append(row)
    df = pd.DataFrame(rows).set_index("measure")
    pd.set_option("display.width", 200)
    print("=== raw cross-sectional Spearman IC (signal vs forward total return) ===")
    print(df.round(4).to_string())
    df.to_csv("tournament/cup20/teams/team-08/research/ic_raw.csv")


if __name__ == "__main__":
    main()
