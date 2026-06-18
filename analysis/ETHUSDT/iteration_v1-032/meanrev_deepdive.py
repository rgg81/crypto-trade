"""iter-v1/032 (ETHUSDT) — deep dive on the ONLY positive high-frequency mean-reversion cell.

Screen 1: pure MR mostly LOSES net of cost; the single positive cell was A4.mrz10_k1.5_N3
(fade price-vs-SMA10 z-score, 3-candle hold): +0.22 Sharpe, 651 events, 51.6% win, top-2 0.027.
Faster-trend turned out to be a noise-grid lucky spike (negative 2023+2024). So MR is now the
prime breadth candidate IF it is ROBUST. This script stress-tests it:

  1. (window W, threshold k, hold N) joint grid for the SHORT-HORIZON fade — find a PLATEAU.
     Primitive: z = (close[t-1] - SMA_W[t-1]) / rolling_std_W(close)[t-1]; fade: dir = -sign(z),
     enter if |z| >= k, hold N. (Uses the mr_zscore family algebra but parameterized.)
  2. Sub-period (yearly) Sharpe of the best robust MR cell — especially 2023/2024/2025 (the
     years adjacent to the OOS wall — the faster-trend died exactly there).
  3. VOL-REGIME conditioning (crypto mechanism): MR snapbacks work in HIGH-vol / liquidation
     regimes, fail in low-vol drift. Condition the fade on a vol-state gate (natr percentile)
     and on a NON-trending regime (|close-SMA200|/ATR small = ranging) — does conditioning lift
     and stabilize? This is the crypto-native refinement (retail-flow/liquidation snapback).
  4. Compare against the rev_* engineered features already in the parquet (rev_extension_z_3,
     rev_halflife_50, rev_vol_gate_signed) — do the purpose-built reversion features predict
     the fade's success?

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


def run(df, mask, direction, n):
    close = df["close"].to_numpy(float)
    ot = df["open_time"].to_numpy()
    fr = fwd(close, n)
    otf = np.full(len(df), np.inf)
    otf[: len(df) - n] = ot[n:]
    hs = (ot < OOS_CUTOFF_MS) & (otf < OOS_CUTOFF_MS)
    valid = mask & hs & np.isfinite(fr) & np.isfinite(direction)
    cand = np.where(valid)[0]
    if len(cand) == 0:
        return None
    sel = nonoverlap(cand, n)
    if len(sel) < 5:
        return None
    d, raw = direction[sel], fr[sel]
    pnl = d * raw - ROUND_TRIP_COST
    assert ot[sel].max() < OOS_CUTOFF_MS and otf[sel].max() < OOS_CUTOFF_MS
    spm = (ot[sel].max() - ot[sel].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
    tpy = len(sel) / max(spm / 12.0, 1e-9)
    g = np.abs(pnl)
    top2 = float(np.sort(g)[::-1][:2].sum() / g.sum()) if g.sum() > 0 else np.nan
    return {
        "events": len(sel),
        "sharpe": ann_sharpe(pnl, tpy),
        "pnl": pnl,
        "ot": ot[sel],
        "win": float((pnl > 0).mean()),
        "net": float(pnl.sum()) * 100,
        "top2": top2,
    }


def yearly(res):
    yr = pd.to_datetime(res["ot"], unit="ms").year
    out = {}
    for y in sorted(set(yr)):
        m = yr == y
        pl = res["pnl"][m]
        if len(pl) < 2:
            out[y] = np.nan
            continue
        spm = (res["ot"][m].max() - res["ot"][m].min()) / (1000 * 60 * 60 * 8 * CANDLES_PER_MONTH)
        out[y] = ann_sharpe(pl, len(pl) / max(spm / 12.0, 1e-9))
    return out


def main():
    df = load_full_for_label_horizon().sort_values("open_time").reset_index(drop=True)
    s = pd.Series(df["close"].to_numpy(float))
    log = []

    def p(x=""):
        print(x)
        log.append(str(x))

    def zscore_vs_sma(w):
        sma = s.rolling(w).mean()
        sd = s.rolling(w).std(ddof=0)
        z = (s - sma) / sd
        return z.shift(1).to_numpy()  # past-only

    p("=" * 96)
    p("iter-v1/032 — MEAN-REVERSION deep dive (fade price-vs-SMA_W z-score, short hold)")
    p("=" * 96)

    Ws = [5, 10, 15, 20, 30]
    Ns = [2, 3, 4, 6]
    ks = [1.0, 1.5, 2.0]

    p("\n[1] (W,N) Sharpe grid at k=1.5 (fade |z|>=1.5):")
    p("  W\\N | " + " ".join(f"{n:>6d}" for n in Ns) + "    | events@N3")
    grid = {}
    for w in Ws:
        z = zscore_vs_sma(w)
        row, ev = [], None
        for n in Ns:
            mask = np.abs(z) >= 1.5
            r = run(df, mask, -np.sign(z), n)
            grid[(w, n)] = r["sharpe"] if r else np.nan
            row.append(grid[(w, n)])
            if n == 3:
                ev = r["events"] if r else 0
        p(f"  {w:3d} | " + " ".join(f"{v:+6.2f}" for v in row) + f"    | {ev}")

    p("\n[1b] threshold k sweep at the best W (10) across N:")
    z10 = zscore_vs_sma(10)
    p("   k | N | events | win | sharpe | net% | top2")
    for k in ks:
        for n in (2, 3, 4):
            r = run(df, np.abs(z10) >= k, -np.sign(z10), n)
            if r:
                p(
                    f"  {k:.1f} | {n} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
                    f"{r['net']:+.1f} | {r['top2']:.4f}"
                )

    # best robust cell from grid neighborhood (min over N-neighbors at each W)
    p("\n[2] yearly Sharpe of candidate MR cells (focus 2023/2024/2025 = OOS-adjacent):")
    for w, n, k in ((10, 3, 1.5), (10, 2, 1.5), (15, 3, 1.5), (20, 3, 1.5), (10, 3, 1.0)):
        z = zscore_vs_sma(w)
        r = run(df, np.abs(z) >= k, -np.sign(z), n)
        if r:
            yr = yearly(r)
            p(
                f"  W={w} N={n} k={k}: events={r['events']} sharpe={r['sharpe']:+.3f} "
                f"win={r['win']:.3f} top2={r['top2']:.4f} | "
                + " ".join(f"{y}:{sh:+.2f}" for y, sh in yr.items())
            )

    # ---- 3. VOL-REGIME / RANGING conditioning (crypto-native refinement) -------
    p("\n[3] crypto-native conditioning of fade(W=10,k=1.5,N=3): vol-state + ranging gate")
    z10 = zscore_vs_sma(10)
    # natr percentile (past-only) — high-vol regime
    hl = df["high"] - df["low"]
    hc = (df["high"] - s.shift(1)).abs()
    lc = (df["low"] - s.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    natr = (atr14 / s).shift(1)  # past-only
    natr_arr = natr.to_numpy()
    # ranging gate: |close[t-1]-SMA200[t-1]|/ATR14 small => not trending => MR works
    sma200 = s.rolling(200).mean()
    dist_atr = ((s.shift(1) - sma200.shift(1)).abs() / atr14.shift(1)).to_numpy()
    is_mask = df["open_time"].to_numpy() < OOS_CUTOFF_MS
    base = np.abs(z10) >= 1.5

    p("   condition | events | win | sharpe | net% | top2 | yearly(23/24/25)")
    # baseline
    r = run(df, base, -np.sign(z10), 3)
    yr = yearly(r)
    p(
        f"   none      | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net']:+.1f} | "
        f"{r['top2']:.4f} | "
        + " ".join(f"{y}:{yr.get(y, float('nan')):+.2f}" for y in (2023, 2024, 2025))
    )
    # high-vol only (natr above median)
    for qn in (0.40, 0.50, 0.60):
        thr = np.nanquantile(natr_arr[is_mask & np.isfinite(natr_arr)], qn)
        r = run(df, base & (natr_arr >= thr), -np.sign(z10), 3)
        if r:
            yr = yearly(r)
            p(
                f"   natr>=q{int(qn * 100)} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
                f"{r['net']:+.1f} | {r['top2']:.4f} | "
                + " ".join(f"{y}:{yr.get(y, float('nan')):+.2f}" for y in (2023, 2024, 2025))
            )
    # ranging only (dist_atr below percentile => not strongly trending)
    for qd in (0.50, 0.60, 0.70):
        thr = np.nanquantile(dist_atr[is_mask & np.isfinite(dist_atr)], qd)
        r = run(df, base & (dist_atr <= thr), -np.sign(z10), 3)
        if r:
            yr = yearly(r)
            p(
                f"   rang<=q{int(qd * 100)} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
                f"{r['net']:+.1f} | {r['top2']:.4f} | "
                + " ".join(f"{y}:{yr.get(y, float('nan')):+.2f}" for y in (2023, 2024, 2025))
            )
    # combined high-vol AND ranging
    thr_n = np.nanquantile(natr_arr[is_mask & np.isfinite(natr_arr)], 0.50)
    thr_d = np.nanquantile(dist_atr[is_mask & np.isfinite(dist_atr)], 0.60)
    r = run(df, base & (natr_arr >= thr_n) & (dist_atr <= thr_d), -np.sign(z10), 3)
    if r:
        yr = yearly(r)
        p(
            f"   vol&rang  | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net']:+.1f} | "
            f"{r['top2']:.4f} | "
            + " ".join(f"{y}:{yr.get(y, float('nan')):+.2f}" for y in (2023, 2024, 2025))
        )

    # ---- 4. engineered rev_* features as the trigger ---------------------------
    p("\n[4] purpose-built reversion features as trigger (rev_extension_z_3), fade dir, N=3:")
    if "rev_extension_z_3" in df:
        rev = df["rev_extension_z_3"].shift(1).to_numpy()
        p("   k | events | win | sharpe | net% | top2 | yearly(23/24/25)")
        for k in (1.0, 1.5, 2.0):
            r = run(df, np.abs(rev) >= k, -np.sign(rev), 3)
            if r:
                yr = yearly(r)
                p(
                    f"  {k:.1f} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net']:+.1f} | "
                    f"{r['top2']:.4f} | "
                    + " ".join(f"{y}:{yr.get(y, float('nan')):+.2f}" for y in (2023, 2024, 2025))
                )

    (Path(__file__).parent / "meanrev_deepdive_output.txt").write_text("\n".join(log))
    print("\n[written] meanrev_deepdive_output.txt")


if __name__ == "__main__":
    main()
