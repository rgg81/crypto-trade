"""EDA 2 -- cross-sectional IC of calendar-decomposed formation returns, by harvest slot.

The lane's non-obvious question: total momentum is the SUM of its per-slot components. If those
components carry different cross-sectional information, the calendar is informative even where the
aggregate per-slot drift (eda_calendar.py) is pure noise.

Every IC below is a per-boundary Spearman rank correlation across the eligible cross-section,
market-demeaned where stated. The unit of independent observation is the BOUNDARY, not the
symbol-boundary, so t-statistics use the boundary count.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import panel  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")
SLOT = {0: "Asia(00-08)", 1: "Euro(08-16)", 2: "US(16-24)"}


def rank_z(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Row-wise rank, mapped to a zero-mean unit-scale score. NaN outside the mask."""
    out = np.full(x.shape, np.nan)
    for i in range(x.shape[0]):
        m = mask[i] & np.isfinite(x[i])
        n = int(m.sum())
        if n < 5:
            continue
        v = x[i, m]
        order = np.argsort(np.argsort(v)).astype(float)
        out[i, m] = (order - (n - 1) / 2.0) / ((n - 1) / 2.0)
    return out


def ic_series(sig: np.ndarray, fwd: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Per-boundary rank IC."""
    s = rank_z(sig, mask)
    f = rank_z(fwd, mask)
    out = np.full(sig.shape[0], np.nan)
    for i in range(sig.shape[0]):
        m = np.isfinite(s[i]) & np.isfinite(f[i])
        if m.sum() < 5:
            continue
        a, b = s[i, m], f[i, m]
        sa, sb = a.std(), b.std()
        if sa <= 0 or sb <= 0:
            continue
        out[i] = float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))
    return out


def summarise(name: str, ic: np.ndarray, sel: np.ndarray, half: np.ndarray) -> dict:
    v = ic[sel]
    v = v[np.isfinite(v)]
    if len(v) < 30:
        return {}
    t = v.mean() / v.std(ddof=1) * np.sqrt(len(v))
    v1 = ic[sel & half]
    v1 = v1[np.isfinite(v1)]
    v2 = ic[sel & ~half]
    v2 = v2[np.isfinite(v2)]
    return {
        "name": name,
        "n": len(v),
        "ic": v.mean(),
        "t": t,
        "ic_h1": v1.mean() if len(v1) else np.nan,
        "ic_h2": v2.mean() if len(v2) else np.nan,
        "t_h1": v1.mean() / v1.std(ddof=1) * np.sqrt(len(v1)) if len(v1) > 2 else np.nan,
        "t_h2": v2.mean() / v2.std(ddof=1) * np.sqrt(len(v2)) if len(v2) > 2 else np.nan,
    }


def slot_sum(ret: np.ndarray, slot: np.ndarray, s: int, days: int) -> np.ndarray:
    """Sum of returns earned in slot ``s`` over the last ``days`` occurrences of that slot,
    using only bars that have already CLOSED at the decision boundary."""
    n, k = ret.shape
    out = np.full((n, k), np.nan)
    idx = np.where(slot == s)[0]
    # returns are open[t]->open[t+1], so at boundary t the last fully observed row is t-1
    contrib = np.nan_to_num(ret, nan=0.0)
    valid = np.isfinite(ret)
    csum = np.cumsum(contrib[idx], axis=0)
    cval = np.cumsum(valid[idx].astype(float), axis=0)
    # position of the last slot-s row strictly before each boundary
    pos = np.searchsorted(idx, np.arange(n), side="left") - 1
    for t in range(n):
        p = pos[t]
        if p < days - 1:
            continue
        tot = csum[p] - (csum[p - days] if p - days >= 0 else 0.0)
        cnt = cval[p] - (cval[p - days] if p - days >= 0 else 0.0)
        row = np.where(cnt >= days - 1, tot, np.nan)
        out[t] = row
    return out


def dow_sum(ret: np.ndarray, dow: np.ndarray, keep: set[int], weeks: int) -> np.ndarray:
    n, k = ret.shape
    out = np.full((n, k), np.nan)
    idx = np.where(np.isin(dow, list(keep)))[0]
    per_week = 3 * len(keep)
    take = weeks * per_week
    contrib = np.nan_to_num(ret, nan=0.0)
    valid = np.isfinite(ret)
    csum = np.cumsum(contrib[idx], axis=0)
    cval = np.cumsum(valid[idx].astype(float), axis=0)
    pos = np.searchsorted(idx, np.arange(n), side="left") - 1
    for t in range(n):
        p = pos[t]
        if p < take - 1:
            continue
        tot = csum[p] - (csum[p - take] if p - take >= 0 else 0.0)
        cnt = cval[p] - (cval[p - take] if p - take >= 0 else 0.0)
        out[t] = np.where(cnt >= take - 1, tot, np.nan)
    return out


def main() -> None:
    p = panel.load()
    w = p.times >= IS_START
    times = p.times[w]
    el = p.eligible[w]
    ret = np.where(el, p.oo_ret[w], np.nan)
    slot = p.slot[w]
    dow = p.dow[w]
    n = len(times)
    half = times < times[n // 2]
    fwd = ret.copy()
    allb = np.ones(n, dtype=bool)

    rows = []

    # ---------- control: plain total momentum over K bars ---------------------------------
    contrib = np.nan_to_num(ret, nan=0.0)
    csum = np.cumsum(contrib, axis=0)
    for K in (1, 3, 6, 9, 21, 63, 126, 252):
        sig = np.full_like(ret, np.nan)
        for t in range(K, n):
            sig[t] = csum[t - 1] - (csum[t - 1 - K] if t - 1 - K >= 0 else 0.0)
        rows.append(("CONTROL", f"total_mom_{K}b", summarise(f"total_mom_{K}b",
                                                             ic_series(sig, fwd, el), allb, half)))
        for h in range(3):
            r = summarise(f"total_mom_{K}b@{SLOT[h]}", ic_series(sig, fwd, el), slot == h, half)
            rows.append(("CONTROL-harvest", f"total_mom_{K}b@h{h}", r))

    # ---------- slot-decomposed formation --------------------------------------------------
    for D in (3, 7, 14, 30, 60):
        sigs = {s: slot_sum(ret, slot, s, D) for s in range(3)}
        for s in range(3):
            ic = ic_series(sigs[s], fwd, el)
            rows.append(("SLOT-FORM", f"slot{s}_{D}d", summarise(f"slot{s}_{D}d", ic, allb, half)))
            for h in range(3):
                rows.append(
                    ("SLOT-FORM-harvest", f"slot{s}_{D}d@h{h}",
                     summarise(f"slot{s}_{D}d@h{h}", ic, slot == h, half))
                )
        # slot tilt: one slot minus the average of the other two
        for s in range(3):
            others = [x for x in range(3) if x != s]
            tilt = sigs[s] - 0.5 * (sigs[others[0]] + sigs[others[1]])
            ic = ic_series(tilt, fwd, el)
            rows.append(("SLOT-TILT", f"tilt{s}_{D}d", summarise(f"tilt{s}_{D}d", ic, allb, half)))
            for h in range(3):
                rows.append(
                    ("SLOT-TILT-harvest", f"tilt{s}_{D}d@h{h}",
                     summarise(f"tilt{s}_{D}d@h{h}", ic, slot == h, half))
                )

    # ---------- weekend vs weekday formation ------------------------------------------------
    for W in (2, 4, 8, 13):
        we = dow_sum(ret, dow, {5, 6}, W)
        wd = dow_sum(ret, dow, {0, 1, 2, 3, 4}, W)
        for label, sig in (("weekend", we), ("weekday", wd), ("we_minus_wd", we - wd)):
            ic = ic_series(sig, fwd, el)
            rows.append(("WEEKEND", f"{label}_{W}w", summarise(f"{label}_{W}w", ic, allb, half)))
            for h in range(3):
                rows.append(("WEEKEND-harvest", f"{label}_{W}w@h{h}",
                             summarise(f"{label}_{W}w@h{h}", ic, slot == h, half)))

    out = pd.DataFrame([r[2] | {"family": r[0]} for r in rows if r[2]])
    out = out[["family", "name", "n", "ic", "t", "ic_h1", "t_h1", "ic_h2", "t_h2"]]
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 500)
    out["abs_t"] = out["t"].abs()
    out["consistent"] = np.sign(out["ic_h1"]) == np.sign(out["ic_h2"])
    print(out.sort_values("abs_t", ascending=False).head(45).to_string(index=False,
                                                                      float_format="%.4f"))
    print("\n== families ranked by best consistent |t| ==")
    cons = out[out["consistent"]]
    print(cons.sort_values("abs_t", ascending=False).head(40).to_string(index=False,
                                                                       float_format="%.4f"))
    out.to_csv("tournament/cup20/teams/team-11/research/ic_study.csv", index=False)
    print(f"\nmeasures evaluated: {len(out)}")


if __name__ == "__main__":
    main()
