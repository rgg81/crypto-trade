"""iter-v1/032 (ETHUSDT) — robustness + crypto-mechanism probes for the breadth winner.

Screen 1 found EDGE-B faster-trend (trendSMA100_N6) the clear breadth winner (818 IS events,
per-trade Sharpe +0.63, top-2 gross 0.020). Pure mean-reversion (EDGE-A) mostly LOSES net of
cost; funding-FADE (EDGE-C) uniformly loses. The uniform pattern says ETH IS is MOMENTUM /
trend-persistent, not mean-reverting. This script:

  1. Sub-period robustness of the winner (yearly per-trade Sharpe + event count) — is the
     +0.63 broad-based or one-regime?
  2. FUNDING-MOMENTUM (follow, not fade): direction = +sign(funding_z) — the crypto-native
     test of whether funding is a continuation signal on ETH (the mechanism: crowded funding
     during a strong trend = the trend persists). Also funding-CONFIRMED faster-trend (trade
     SMA100 trend only when funding agrees) as a quality filter.
  3. Conviction-gate feasibility: does adding a trend-strength gate (|dist|/ATR >= q) to the
     winner LIFT per-trade Sharpe (like iter-027's gate did)? This is the iter-027 conviction
     primitive transplanted to the fast-trend.
  4. Hold-horizon sweep around N=6 for trendSMA100 (N in 3..12) to confirm N=6 is not a lucky
     point and find the plateau.
  5. Direction-correctness (raw, pre-cost) by sub-period — the deterministic-primitive health.

All leak-safe (load_full_for_label_horizon + per-N horizon drop + .shift(1) primitives).
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


def ann_sharpe(pnls, n_per_year):
    p = np.asarray(pnls, float)
    if len(p) < 2 or p.std(ddof=1) == 0:
        return 0.0
    return float(p.mean() / p.std(ddof=1) * np.sqrt(n_per_year))


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    out[: len(close) - n] = close[n:] / close[: len(close) - n] - 1.0
    return out


def non_overlap(idx, n_hold):
    kept, last_exit = [], -1
    for i in idx:
        if i > last_exit:
            kept.append(i)
            last_exit = i + n_hold
    return np.array(kept, dtype=int)


def run_edge(df, mask, direction, n_hold):
    close = df["close"].to_numpy(float)
    open_time = df["open_time"].to_numpy()
    fr = fwd_return(close, n_hold)
    ot_future = np.full(len(df), np.inf)
    ot_future[: len(df) - n_hold] = open_time[n_hold:]
    horizon_safe = (open_time < OOS_CUTOFF_MS) & (ot_future < OOS_CUTOFF_MS)
    valid = mask & horizon_safe & np.isfinite(fr) & np.isfinite(direction)
    cand = np.where(valid)[0]
    if len(cand) == 0:
        return None
    sel = non_overlap(cand, n_hold)
    d = direction[sel]
    raw = fr[sel]
    pnl = d * raw - ROUND_TRIP_COST
    assert open_time[sel].max() < OOS_CUTOFF_MS
    assert ot_future[sel].max() < OOS_CUTOFF_MS
    span_months = (open_time[sel].max() - open_time[sel].min()) / (
        1000 * 60 * 60 * 8 * CANDLES_PER_MONTH
    )
    tpy = len(sel) / max(span_months / 12.0, 1e-9)
    return {
        "events": len(sel),
        "win": float((pnl > 0).mean()),
        "sharpe": ann_sharpe(pnl, tpy),
        "net_pct": float(pnl.sum()) * 100,
        "mean_pct": float(pnl.mean()) * 100,
        "raw_dir_acc": float(((d * raw) > 0).mean()),  # pre-cost correctness
        "pnl": pnl,
        "open_time": open_time[sel],
        "sel": sel,
    }


def by_year(res):
    ot = pd.to_datetime(res["open_time"], unit="ms")
    yrs = ot.year
    out = []
    for y in sorted(set(yrs)):
        m = yrs == y
        p = res["pnl"][m]
        if len(p) < 2:
            out.append((y, len(p), np.nan, np.nan))
            continue
        spm = (res["open_time"][m].max() - res["open_time"][m].min()) / (
            1000 * 60 * 60 * 8 * CANDLES_PER_MONTH
        )
        tpy = len(p) / max(spm / 12.0, 1e-9)
        out.append((y, len(p), ann_sharpe(p, tpy), float(p.sum()) * 100))
    return out


def main():
    df = load_full_for_label_horizon().sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(float)
    s = pd.Series(close)
    log = []

    def p(x=""):
        print(x)
        log.append(str(x))

    def trend_state(w):
        sma = s.rolling(w).mean()
        return np.where(s.shift(1) > sma.shift(1), 1.0, -1.0)

    def trend_strength(w, aw=14):
        sma = s.rolling(w).mean()
        hl = df["high"] - df["low"]
        hc = (df["high"] - s.shift(1)).abs()
        lc = (df["low"] - s.shift(1)).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = tr.rolling(aw).mean()
        return ((s.shift(1) - sma.shift(1)).abs() / atr.shift(1)).to_numpy()

    fz30 = df["funding_rate_zscore_30"].shift(1).to_numpy()

    p("=" * 96)
    p("iter-v1/032 ETHUSDT — WINNER ROBUSTNESS + crypto-mechanism probes")
    p("=" * 96)

    # ---- 1. Sub-period robustness of the winner trendSMA100_N6 -----------------
    p("\n[1] Sub-period robustness — trendSMA100, N=6 (the breadth winner)")
    ts100 = trend_state(100)
    res = run_edge(df, np.isfinite(ts100), ts100, 6)
    p(
        f"  FULL IS: events={res['events']} win={res['win']:.3f} sharpe={res['sharpe']:+.4f} "
        f"net={res['net_pct']:+.1f}% raw_dir_acc={res['raw_dir_acc']:.3f}"
    )
    p("  year | events | sharpe | net% ")
    for y, n, sh, net in by_year(res):
        p(f"   {y}  |  {n:4d}  | {sh:+.3f} | {net:+.1f}")

    # ---- 2. Hold-horizon sweep around N=6 for trendSMA100 ----------------------
    p("\n[2] Hold-horizon plateau — trendSMA100, N in 3..12")
    p("   N | events | win | sharpe | net% | mean_pct")
    for n_hold in (3, 4, 5, 6, 7, 8, 9, 10, 12):
        r = run_edge(df, np.isfinite(ts100), ts100, n_hold)
        p(
            f"  {n_hold:2d} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | "
            f"{r['net_pct']:+.1f} | {r['mean_pct']:+.3f}"
        )

    # SMA window sweep at N=6
    p("\n[2b] SMA-window sweep at N=6 (50,75,100,150,200)")
    p("   W | events | win | sharpe | net%")
    for w in (50, 75, 100, 150, 200):
        tsw = trend_state(w)
        r = run_edge(df, np.isfinite(tsw), tsw, 6)
        p(
            f"  {w:3d} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net_pct']:+.1f}"
        )

    # ---- 3. Conviction-gate transplant (iter-027 primitive on the fast trend) --
    p("\n[3] Conviction-gate transplant — trendSMA100_N6, gate |dist|/ATR14 >= q-quantile")
    strn = trend_strength(100)
    # past-only IS quantile threshold (single global IS quantile as a proxy; backtest uses per-month)
    valid_strn = strn[(df["open_time"].to_numpy() < OOS_CUTOFF_MS) & np.isfinite(strn)]
    p("   q | thresh | events | win | sharpe | net%")
    for q in (0.0, 0.20, 0.40, 0.50, 0.60):
        thr = np.nanquantile(valid_strn, q) if q > 0 else -np.inf
        mask = np.isfinite(ts100) & (strn >= thr)
        r = run_edge(df, mask, ts100, 6)
        p(
            f"  {q:.2f} | {thr:6.2f} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net_pct']:+.1f}"
        )

    # ---- 4. FUNDING as MOMENTUM (follow) vs FADE -------------------------------
    p("\n[4] FUNDING direction test — FOLLOW (+sign) vs FADE (-sign), N=6, |fz30|>=k")
    p("   mode | k | events | win | sharpe | net% | raw_dir_acc")
    for k in (0.5, 1.0, 1.5):
        mask = np.abs(fz30) >= k
        for mode, dsign in (("FOLLOW", +1), ("FADE", -1)):
            direction = dsign * np.sign(fz30)
            r = run_edge(df, mask, direction, 6)
            if r:
                p(
                    f"  {mode:6s} | {k:.1f} | {r['events']:5d} | {r['win']:.3f} | "
                    f"{r['sharpe']:+.4f} | {r['net_pct']:+.1f} | {r['raw_dir_acc']:.3f}"
                )

    # ---- 5. FUNDING-CONFIRMED faster trend (quality filter) --------------------
    p("\n[5] FUNDING-CONFIRMED faster-trend — trendSMA100_N6 traded ONLY when funding agrees")
    p("    (direction = trend-state; entry only if sign(fz30) == trend-state sign)")
    p("   k | events | win | sharpe | net% | (vs unfiltered sharpe +0.63)")
    for k in (0.0, 0.5, 1.0):
        agree = np.sign(fz30) == ts100
        mask = np.isfinite(ts100) & agree & (np.abs(fz30) >= k)
        r = run_edge(df, mask, ts100, 6)
        if r:
            p(
                f"  {k:.1f} | {r['events']:5d} | {r['win']:.3f} | {r['sharpe']:+.4f} | {r['net_pct']:+.1f}"
            )

    # ---- 6. Independence vs iter-027 trend roster proxy ------------------------
    p("\n[6] Event spread of winner (trendSMA100_N6) — monthly distribution")
    ot = pd.to_datetime(res["open_time"], unit="ms").to_period("M")
    mon_counts = pd.Series(1, index=ot).groupby(level=0).sum()
    mon_pnl = pd.Series(res["pnl"], index=ot).groupby(level=0).sum()
    p(
        f"   active months: {(mon_counts > 0).sum()}/{len(mon_counts)}  "
        f"events/mo mean={mon_counts.mean():.1f} max={mon_counts.max()} min={mon_counts.min()}"
    )
    p(
        f"   monthly net: {(mon_pnl > 0).sum()}/{len(mon_pnl)} positive  "
        f"best={mon_pnl.max() * 100:+.1f}% worst={mon_pnl.min() * 100:+.1f}%"
    )
    # top-2 share gross
    g = np.abs(res["pnl"])
    srt = np.sort(g)[::-1]
    p(
        f"   top-2 trade share (gross) = {srt[:2].sum() / g.sum():.4f} "
        f"(iter-027 IS ~0.073 / OOS ~0.44 — winner is FAR more diffuse)"
    )

    (Path(__file__).parent / "winner_robustness_output.txt").write_text("\n".join(log))
    print("\n[written] winner_robustness_output.txt")


if __name__ == "__main__":
    main()
