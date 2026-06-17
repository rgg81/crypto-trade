"""IS-ONLY robustness of the trend-strength gate to its one free knob + trade-rate check — iter-v1/018.

strength_gate_by_side.py established (IS-only) the genuine asymmetry:
  - strong-LONG  : full +1.79, frac_pos 0.75, WR 62%, recent3 +2.87  -> stable IS edge.
  - strong-SHORT : full +0.20, frac_pos 0.29, recent3 -9.74          -> UNSTABLE (blowup-driven).
The IS-honest asymmetry is the OPPOSITE of the OOS observation: conviction (distance-from-SMA200 in
ATR units) makes the LONG side stable, not the short side.

Two candidate merge designs emerged:
  Cd_strong_BOTH : symmetric strength gate (trade strong-trend rows both directions). full +1.21,
                   frac_pos 0.70, recent3 +2.09, trades 2328.
  E1             : long-lenient / short-strict strength gate. full +1.21, frac_pos 0.80 (best),
                   recent3 +1.61, trades 2523.

This script verifies the strength gate is NOT a knife-edge knob (sweeps the strength quantile q in
{0.30..0.70}) and reports the implied OOS TRADE RATE so the chosen design clears the v1 floor (the
let-run 14d book is naturally low-frequency; we estimate OOS trades by proportional scaling of the IS
firing rate to the ~15-month OOS window). Everything IS-only; q is selected on IS sub-period stability.

OOS-VIGILANCE (HARD): strict IS filter + leak-guard assert; `.shift(1)` past-only SMA/ATR; per-period
quantile from PAST rows only; OOS never read; trade-rate is an ESTIMATE from the IS firing fraction
(no OOS candle touched). `src/` + runner + OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-018/strength_quantile_robustness.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-018"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14
OOS_CANDLES_APPROX = 1346     # measured OOS row count (for trade-rate estimate only; not read for signal)


def fwd_log_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days):
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + SUBPERIOD_DAYS))
        edge += SUBPERIOD_DAYS
    return edges


def ann_sharpe(r, tpy):
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def stability(pnl, fire, ot_days, bounds, tpy):
    sh = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = pnl[m]
        sh.append(ann_sharpe(arr, tpy) if len(arr) >= MIN_SUB_TRADES else np.nan)
    s = np.array(sh, float)
    valid = s[np.isfinite(s)]
    rl = [v for v in reversed(s) if np.isfinite(v)]
    allt = pnl[fire & np.isfinite(pnl)]
    return dict(
        full=round(ann_sharpe(allt, tpy), 4) if len(allt) else np.nan,
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent3=round(float(np.mean(rl[:3])), 3) if len(rl) >= 3 else np.nan,
        n_pos=int(np.sum(valid > 0)), n_scored=int(len(valid)),
        n_trades=int(len(allt)),
        win_rate=round(float(np.mean(allt > 0)), 4) if len(allt) else np.nan,
        mean_ret_pct=round(float(np.mean(allt) * 100.0), 4) if len(allt) else np.nan,
    )


def past_thr(absdist, ot_days, bounds, q):
    thr = np.full(len(absdist), np.nan)
    row_idx = np.arange(len(absdist))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        cut = int(row_idx[tm].min()) - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = absdist[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    absd = np.abs(dist_atr)

    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)
    pnl = dir_ts * y - (RT_COST / 100.0)
    is_long = dir_ts > 0
    is_short = dir_ts < 0
    n_base = int(base.sum())

    print(f"IS rows {len(df)}  base rows {n_base}  N={N_LABEL}(14d) SMA{SMA_WIN} ATR{ATR_WIN}")
    print("=" * 122)
    print("STRENGTH-QUANTILE ROBUSTNESS — symmetric strength gate (Cd_strong_BOTH) across q:")
    print(f"  {'q':>5s} {'full':>8s} {'fpos':>5s} {'disp':>7s} {'recent3':>8s} {'trades':>7s} "
          f"{'WR':>6s} {'mret%':>7s} {'est_OOS_trades':>15s}")
    for q in [0.30, 0.40, 0.50, 0.60, 0.70]:
        thr = past_thr(absd, ot_days, bounds, q)
        fire = base & np.isfinite(thr) & (absd >= thr)
        b = stability(pnl, fire, ot_days, bounds, tpy)
        fire_frac = fire.sum() / max(n_base, 1)
        est_oos = int(round(fire_frac * OOS_CANDLES_APPROX))
        print(f"  {q:>5.2f} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
              f"{b['recent3']!s:>8} {b['n_trades']!s:>7} {b['win_rate']!s:>6} "
              f"{b['mean_ret_pct']!s:>7} {est_oos:>15d}")

    print("\nSTRENGTH-QUANTILE ROBUSTNESS — asymmetric E1 (LONG q_long, SHORT q_short):")
    print(f"  {'qL':>4s} {'qS':>4s} {'full':>8s} {'fpos':>5s} {'disp':>7s} {'recent3':>8s} "
          f"{'trades':>7s} {'WR':>6s} {'mret%':>7s} {'est_OOS':>8s}")
    for qL in [0.20, 0.30, 0.40]:
        for qS in [0.60, 0.70, 0.80]:
            thrL = past_thr(absd, ot_days, bounds, qL)
            thrS = past_thr(absd, ot_days, bounds, qS)
            fire = base & ((is_long & np.isfinite(thrL) & (absd >= thrL))
                           | (is_short & np.isfinite(thrS) & (absd >= thrS)))
            b = stability(pnl, fire, ot_days, bounds, tpy)
            est_oos = int(round(fire.sum() / max(n_base, 1) * OOS_CANDLES_APPROX))
            print(f"  {qL:>4.2f} {qS:>4.2f} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>7} "
                  f"{b['recent3']!s:>8} {b['n_trades']!s:>7} {b['win_rate']!s:>6} "
                  f"{b['mean_ret_pct']!s:>7} {est_oos:>8d}")

    # persist the two headline designs at their chosen knobs
    rows = []
    for label, fire in [
        ("Cd_strong_BOTH_q050", base & np.isfinite(past_thr(absd, ot_days, bounds, 0.50))
            & (absd >= past_thr(absd, ot_days, bounds, 0.50))),
        ("E1_qL030_qS070",
            base & ((is_long & np.isfinite(past_thr(absd, ot_days, bounds, 0.30))
                     & (absd >= past_thr(absd, ot_days, bounds, 0.30)))
                    | (is_short & np.isfinite(past_thr(absd, ot_days, bounds, 0.70))
                       & (absd >= past_thr(absd, ot_days, bounds, 0.70))))),
    ]:
        b = stability(pnl, fire, ot_days, bounds, tpy)
        b["design"] = label
        b["est_oos_trades"] = int(round(fire.sum() / max(n_base, 1) * OOS_CANDLES_APPROX))
        rows.append(b)
    pd.DataFrame(rows).to_csv(OUTDIR / "strength_quantile_robustness.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'strength_quantile_robustness.csv'}")

    print("\nNOTE on trade rate: the est_OOS_trades column scales the IS firing fraction onto the "
          f"~{OOS_CANDLES_APPROX}-candle OOS window. The let-run book holds ~N=42 candles, so the "
          "effective independent OOS trade count is lower than the row-firing count; the v1 "
          "specialist floor (>=50 OOS) should be checked on the REAL backtest, not this estimate.")


if __name__ == "__main__":
    main()
