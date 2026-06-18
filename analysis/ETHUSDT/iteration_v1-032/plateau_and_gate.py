"""iter-v1/032 (ETHUSDT) — find a ROBUST faster-trend cell (plateau, not a lucky spike).

winner_robustness.py exposed that trendSMA100_N6 is a TWO-PARAMETER LUCKY SPIKE (N=6 and W=100 are
both isolated peaks; neighbors weak; 2024 deeply negative). A robust deterministic edge needs a
PLATEAU (the iter-020/027 200-SMA sat on a flat 100-300 plateau — that is WHY it generalized).

This script:
  1. Joint (W, N) Sharpe grid — locate any region where a NEIGHBORHOOD (not one cell) is positive.
     Robustness score = min Sharpe over the 3x3 neighborhood of (W,N). High = plateau.
  2. For the most ROBUST cell, sub-period (yearly) Sharpe — must avoid a full-year blowout.
  3. Conviction-gated version of the robust cell across q — and its yearly stability (the gate
     is the durable iter-027 ingredient; does it stabilize 2024?).
  4. A directional-correctness (raw, pre-cost) heatmap by year for the robust cell — the
     deterministic primitive's health regardless of cost.

Leak-safe throughout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import OOS_CUTOFF_MS, load_full_for_label_horizon  # noqa: E402

ROUND_TRIP_COST = 2 * (0.001 + 0.0002)
CANDLES_PER_MONTH = 91.0


def ann_sharpe(p, npy):
    p = np.asarray(p, float)
    if len(p) < 2 or p.std(ddof=1) == 0:
        return 0.0
    return float(p.mean() / p.std(ddof=1) * np.sqrt(npy))


def fwd(close, n):
    out = np.full(len(close), np.nan)
    out[: len(close) - n] = close[n:] / close[: len(close) - n] - 1.0
    return out


def nonoverlap(idx, n):
    kept, le = [], -1
    for i in idx:
        if i > le:
            kept.append(i)
            le = i + n
    return np.array(kept, int)


def run(df, mask, direction, n_hold):
    close = df["close"].to_numpy(float)
    ot = df["open_time"].to_numpy()
    fr = fwd(close, n_hold)
    otf = np.full(len(df), np.inf)
    otf[: len(df) - n_hold] = ot[n_hold:]
    hs = (ot < OOS_CUTOFF_MS) & (otf < OOS_CUTOFF_MS)
    valid = mask & hs & np.isfinite(fr) & np.isfinite(direction)
    cand = np.where(valid)[0]
    if len(cand) == 0:
        return None
    sel = nonoverlap(cand, n_hold)
    d, raw = direction[sel], fr[sel]
    pnl = d * raw - ROUND_TRIP_COST
    assert ot[sel].max() < OOS_CUTOFF_MS and otf[sel].max() < OOS_CUTOFF_MS
    spm = (ot[sel].max() - ot[sel].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
    tpy = len(sel) / max(spm / 12.0, 1e-9)
    return {
        "events": len(sel),
        "sharpe": ann_sharpe(pnl, tpy),
        "pnl": pnl,
        "ot": ot[sel],
        "win": float((pnl > 0).mean()),
        "raw_acc": float(((d * raw) > 0).mean()),
        "net": float(pnl.sum()) * 100,
    }


def yearly(res):
    ot = pd.to_datetime(res["ot"], unit="ms").year
    out = {}
    for y in sorted(set(ot)):
        m = ot == y
        p = res["pnl"][m]
        if len(p) < 2:
            out[y] = (len(p), np.nan)
            continue
        spm = (res["ot"][m].max() - res["ot"][m].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
        tpy = len(p) / max(spm / 12.0, 1e-9)
        out[y] = (len(p), ann_sharpe(p, tpy))
    return out


def main():
    df = load_full_for_label_horizon().sort_values("open_time").reset_index(drop=True)
    s = pd.Series(df["close"].to_numpy(float))
    log = []

    def p(x=""):
        print(x)
        log.append(str(x))

    def ts(w):
        sma = s.rolling(w).mean()
        return np.where(s.shift(1) > sma.shift(1), 1.0, -1.0)

    def strength(w, aw=14):
        sma = s.rolling(w).mean()
        hl = df["high"] - df["low"]
        hc = (df["high"] - s.shift(1)).abs()
        lc = (df["low"] - s.shift(1)).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = tr.rolling(aw).mean()
        return ((s.shift(1) - sma.shift(1)).abs() / atr.shift(1)).to_numpy()

    Ws = [50, 75, 100, 125, 150, 200]
    Ns = [3, 5, 6, 7, 9, 12, 15, 21]

    p("=" * 96)
    p("iter-v1/032 — (W,N) joint Sharpe grid (net of cost) — looking for a PLATEAU, not a spike")
    p("=" * 96)
    grid = {}
    header = "  W\\N | " + " ".join(f"{n:>6d}" for n in Ns)
    p(header)
    for w in Ws:
        tsw = ts(w)
        row = []
        for n in Ns:
            r = run(df, np.isfinite(tsw), tsw, n)
            grid[(w, n)] = r["sharpe"] if r else np.nan
            row.append(grid[(w, n)])
        p(f"  {w:3d} | " + " ".join(f"{v:+6.2f}" for v in row))

    # robustness score: min over 3x3 neighborhood in (W index, N index)
    p("\n[robustness] min-Sharpe over 3x3 (W,N) neighborhood (plateau detector):")
    p(header)
    best_cell, best_score = None, -1e9
    for iw, w in enumerate(Ws):
        row = []
        for iN, n in enumerate(Ns):
            neigh = []
            for dw in (-1, 0, 1):
                for dn in (-1, 0, 1):
                    jw, jn = iw + dw, iN + dn
                    if 0 <= jw < len(Ws) and 0 <= jn < len(Ns):
                        neigh.append(grid[(Ws[jw], Ns[jn])])
            score = np.nanmin(neigh)
            row.append(score)
            if score > best_score:
                best_score, best_cell = score, (w, n)
        p(f"  {w:3d} | " + " ".join(f"{v:+6.2f}" for v in row))
    p(
        f"\n  MOST-ROBUST cell (max neighborhood-min Sharpe): W={best_cell[0]} N={best_cell[1]} "
        f"score={best_score:+.3f}"
    )

    # yearly stability of the robust cell vs the lucky spike
    p("\n[yearly] robust cell vs lucky spike (W=100,N=6):")
    for label, (w, n) in (("ROBUST", best_cell), ("SPIKE(100,6)", (100, 6))):
        tsw = ts(w)
        r = run(df, np.isfinite(tsw), tsw, n)
        yr = yearly(r)
        p(
            f"  {label:14s} W={w} N={n} events={r['events']} sharpe={r['sharpe']:+.3f} "
            f"net={r['net']:+.1f}% | "
            + " ".join(f"{y}:{sh:+.2f}({c})" for y, (c, sh) in yr.items())
        )

    # conviction-gate on the robust cell across q + yearly
    p("\n[gate] conviction gate |dist|/ATR14 >= q-quantile on the ROBUST cell — does it stabilize?")
    w, n = best_cell
    tsw = ts(w)
    strn = strength(w)
    valid_strn = strn[(df["open_time"].to_numpy() < OOS_CUTOFF_MS) & np.isfinite(strn)]
    p("   q | thr | events | win | sharpe | net% | yearly")
    for q in (0.0, 0.20, 0.30, 0.40, 0.50):
        thr = np.nanquantile(valid_strn, q) if q > 0 else -np.inf
        mask = np.isfinite(tsw) & (strn >= thr)
        r = run(df, mask, tsw, n)
        yr = yearly(r)
        p(
            f"  {q:.2f} | {thr:5.2f} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
            f"{r['net']:+.1f} | " + " ".join(f"{y}:{sh:+.2f}" for y, (c, sh) in yr.items())
        )

    # also gate on the SPIKE cell (since the user's strongest IS number is there) for comparison
    p("\n[gate-on-spike] same gate on W=100,N=6 (the raw IS-strongest cell):")
    tsw = ts(100)
    strn = strength(100)
    vs = strn[(df["open_time"].to_numpy() < OOS_CUTOFF_MS) & np.isfinite(strn)]
    p("   q | thr | events | win | sharpe | net% | yearly")
    for q in (0.0, 0.20, 0.30, 0.40):
        thr = np.nanquantile(vs, q) if q > 0 else -np.inf
        mask = np.isfinite(tsw) & (strn >= thr)
        r = run(df, mask, tsw, 6)
        yr = yearly(r)
        p(
            f"  {q:.2f} | {thr:5.2f} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
            f"{r['net']:+.1f} | " + " ".join(f"{y}:{sh:+.2f}" for y, (c, sh) in yr.items())
        )

    (Path(__file__).parent / "plateau_and_gate_output.txt").write_text("\n".join(log))
    print("\n[written] plateau_and_gate_output.txt")


if __name__ == "__main__":
    main()
