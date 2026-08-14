"""Cross-sectional information-coefficient study over the flow-measure library.

Every measure is evaluated against the tradeable forward return -- ``open[i+h] / open[i]`` --
because that is the price the evaluator fills at. Rank IC is Spearman within each boundary's
eligible set. Per-fold ICs are reported alongside the pooled number, because a measure that
only works in one regime is a regime bet wearing a flow costume.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from flow import Flow, rank_rows
from panel import Panel


def forward_returns(p: Panel, h: int) -> np.ndarray:
    """``open[i+h]/open[i] - 1`` on the decision slice, NaN where unavailable."""
    o = p.open
    d0, dn = p.d0, p.dn
    n = dn - d0
    out = np.full((n, p.n_sym), np.nan)
    hi = min(dn, p.n_all - h)
    if hi > d0:
        seg = slice(d0, hi)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[: hi - d0] = o[d0 + h : hi + h] / o[seg] - 1.0
    return out


def rank_ic(sig: np.ndarray, fwd: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Per-boundary Spearman IC."""
    n = sig.shape[0]
    out = np.full(n, np.nan)
    rs = rank_rows(sig, mask)
    rf = rank_rows(fwd, mask & np.isfinite(sig))
    for i in range(n):
        a, b = rs[i], rf[i]
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < 6:
            continue
        x, y = a[ok], b[ok]
        sx, sy = x.std(), y.std()
        if sx <= 0 or sy <= 0:
            continue
        out[i] = float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))
    return out


def summarise(ics: np.ndarray, times: pd.DatetimeIndex, fold_edges) -> dict:
    v = ics[np.isfinite(ics)]
    if v.size < 30:
        return {"ic": np.nan, "t": np.nan}
    # Block-aware t-stat: 30-bar (10-day) non-overlapping block means.
    blocks = v[: (v.size // 30) * 30].reshape(-1, 30).mean(axis=1)
    t = blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks))) if len(blocks) > 2 else np.nan
    row = {"ic": float(v.mean()), "t": float(t), "n": int(v.size)}
    for name, lo, hi in fold_edges:
        m = (times >= lo) & (times < hi)
        w = ics[m]
        w = w[np.isfinite(w)]
        row[name] = float(w.mean()) if w.size > 10 else np.nan
    return row


def fold_edges(times: pd.DatetimeIndex):
    end = times[-1].ceil("D") + pd.Timedelta(hours=8)
    end = pd.Timestamp("2024-08-01T00:00:00Z")
    interior = [end - pd.DateOffset(years=y) for y in (3, 2, 1)]
    b = [times[0], *[max(e, times[0]) for e in interior], end]
    return [(f"F{i + 1}", b[i], b[i + 1]) for i in range(4)]


def build_measures(p: Panel, f: Flow) -> dict[str, np.ndarray]:
    """The candidate library. Windows in 8h bars: 3=1d, 9=3d, 21=7d, 42=14d, 90=30d."""
    d0, dn = p.d0, p.dn

    def cut(a):
        return a[d0:dn]

    M: dict[str, np.ndarray] = {}
    WINDOWS = (1, 3, 6, 9, 21, 42, 90)
    for w in WINDOWS:
        M[f"netflow_{w}"] = cut(f.netflow(w))
        M[f"ret_{w}"] = cut(f.ret_w(w))
    for w in (3, 9, 21, 42):
        M[f"flowint_{w}_90"] = cut(f.flow_intensity(w, 90))
        M[f"volshock_{w}_90"] = cut(f.vol_shock(w, 90))
        M[f"atsshock_{w}_90"] = cut(f.ats_shock(w, 90))
        M[f"ntshock_{w}_90"] = cut(f.nt_shock(w, 90))
    for w in (21, 90):
        M[f"amihud_{w}"] = cut(f.amihud(w))
        M[f"rvol_{w}"] = cut(f.realised_vol(w))
    M["ats_level"] = cut(np.log(np.where(f.ats > 0, f.ats, np.nan)))
    return M
