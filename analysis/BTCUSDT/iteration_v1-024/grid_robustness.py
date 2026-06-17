"""IS-ONLY: is the RVOL-kill 'plateau' robust to the SUB-PERIOD GRID, or is it an artifact of the thin
final 24-12 sub-period? — iter-v1/024 (BTCUSDT). The fragility CONTROL's control.

kill_decomposition.py found the RVOL-kill (vol_state_z_natr_30 >= q0.80) recent3 lift (+0.785) is
ENTIRELY carried by the single thin final IS sub-period (24-12, only 21 incumbent trades): the lift
collapses to +0.005 when that sub-period is dropped, sign-consistency is 5/10 (coin-flip), and the
removed trades are net-WINNERS (Sharpe +1.26 vs retained +0.94). That is the iter-011 fragility
fingerprint (thin-recent-slice curve-fit). This script confirms the NULL is robust to the arbitrary
6-month sub-period binning by re-running the recent-lift decision under:
  (a) different SUBPERIOD_DAYS (4mo / 6mo / 9mo) -- does the 'lift' survive a coarser/finer grid?
  (b) a calendar-anchored last-FULL-year IS slice (2024-03-24 .. 2025-03-24, the 1y OOS-proxy) -- on a
      grid-free window, is the kill better or worse than the incumbent? (the honest recency test)
  (c) the MIN_SUB_TRADES floor raised (drop the thin 24-12 slice mechanically) -- recent lift then?

If the recent lift evaporates under any reasonable grid change while the FULL-IS kill is flat/negative,
the kill-switch is the iter-011 fragile gate (NULL). If it survives all three, it is a genuine kill.

OOS-VIGILANCE (HARD): strict IS filter + leak assert; `.shift(1)` past-only; PAST-only cut quantiles
purged by N_LABEL; OOS never read. The 1y window END is the cutoff (2025-03-24) so it is the LAST IS
year, fully pre-cutoff -- not OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-024/grid_robustness.py
"""
# ruff: noqa: E501, N806

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-024"

N_LABEL = 42
BARS_PER_YEAR = 365.0 * 3.0
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14
Q_STRENGTH = 0.40
KILL_COL = "vol_state_z_natr_30"
KILL_CUT = 0.80


def fwd_log_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def ann_sharpe(r, tpy):
    r = r[np.isfinite(r)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(tpy))


def bounds_for(ot_days, days):
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        edges.append((edge, edge + days))
        edge += days
    return edges


def past_only_quantile_threshold(x, ot_days, bounds, q):
    thr = np.full(len(x), np.nan)
    row_idx = np.arange(len(x))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        cut = int(row_idx[tm].min()) - N_LABEL
        if cut < SMA_WIN + ATR_WIN:
            continue
        past = x[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def recent_lift(pnl, fire_inc, fire_kill, ot_days, bounds, tpy, min_sub_trades, k=3):
    def ps(fire):
        sh = []
        for lo, hi in bounds:
            m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
            arr = pnl[m]
            sh.append(
                ann_sharpe(arr, tpy) if int(np.isfinite(arr).sum()) >= min_sub_trades else np.nan
            )
        seq = [v for v in reversed(sh) if np.isfinite(v)]
        return float(np.mean(seq[:k])) if len(seq) >= 1 else np.nan

    return ps(fire_inc), ps(fire_kill)


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

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    absd = np.abs(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)
    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    pnl = dir_ts * y - (RT_COST / 100.0)

    rows = []
    print(f"IS rows {len(df)}  KILL={KILL_COL}>=q{KILL_CUT}")
    print("=" * 110)
    print(
        "(a) GRID SENSITIVITY — recent3 lift (kill - incumbent) under different sub-period lengths"
    )
    print("=" * 110)
    for days in (121.7, 182.5, 273.75):  # ~4mo / 6mo / 9mo
        b = bounds_for(ot_days, days)
        thr_str = past_only_quantile_threshold(absd, ot_days, b, Q_STRENGTH)
        fire_inc = base & np.isfinite(thr_str) & (absd >= thr_str)
        sig = pd.Series(df[KILL_COL].to_numpy(float)).shift(1).to_numpy()
        thr_k = past_only_quantile_threshold(sig, ot_days, b, KILL_CUT)
        stress = np.isfinite(sig) & np.isfinite(thr_k) & (sig >= thr_k)
        fire_kill = fire_inc & ~stress
        for mst in (8,):
            ir, kr = recent_lift(pnl, fire_inc, fire_kill, ot_days, b, tpy, mst, k=3)
            d = (kr - ir) if (np.isfinite(kr) and np.isfinite(ir)) else np.nan
            print(
                f"  sub={days / 30.4:.0f}mo n_subs={len(b):2d} min_sub_trades={mst}: "
                f"inc_recent3={ir:+.3f} kill_recent3={kr:+.3f}  d={d:+.3f}"
            )
            rows.append(
                dict(
                    test="grid",
                    sub_months=round(days / 30.4, 1),
                    n_subs=len(b),
                    min_sub_trades=mst,
                    inc_recent3=ir,
                    kill_recent3=kr,
                    d_recent3=d,
                )
            )

    print(
        "\n(c) THIN-SLICE FLOOR — raise MIN_SUB_TRADES on 6mo grid (drops the 21-trade 24-12 slice)"
    )
    print("=" * 110)
    b = bounds_for(ot_days, 182.5)
    thr_str = past_only_quantile_threshold(absd, ot_days, b, Q_STRENGTH)
    fire_inc = base & np.isfinite(thr_str) & (absd >= thr_str)
    sig = pd.Series(df[KILL_COL].to_numpy(float)).shift(1).to_numpy()
    thr_k = past_only_quantile_threshold(sig, ot_days, b, KILL_CUT)
    stress = np.isfinite(sig) & np.isfinite(thr_k) & (sig >= thr_k)
    fire_kill = fire_inc & ~stress
    for mst in (8, 25, 50):
        ir, kr = recent_lift(pnl, fire_inc, fire_kill, ot_days, b, tpy, mst, k=3)
        d = (kr - ir) if (np.isfinite(kr) and np.isfinite(ir)) else np.nan
        print(
            f"  min_sub_trades={mst:>3d}: inc_recent3={ir:+.3f} kill_recent3={kr:+.3f}  d={d:+.3f}"
        )
        rows.append(
            dict(
                test="thin_floor",
                sub_months=6.0,
                n_subs=len(b),
                min_sub_trades=mst,
                inc_recent3=ir,
                kill_recent3=kr,
                d_recent3=d,
            )
        )

    # (b) calendar-anchored LAST-IS-YEAR slice (grid-free) — the honest recency test
    print(
        "\n(b) LAST-IS-YEAR SLICE (2024-03-24 .. 2025-03-24, grid-free, pre-cutoff) — kill vs incumbent"
    )
    print("=" * 110)
    yr_start_ms = OOS_CUTOFF_MS - int(365.25 * 86400_000)
    yr_start_days = yr_start_ms / 86400_000.0
    last_yr = ot_days >= yr_start_days
    full_inc = fire_inc & last_yr & np.isfinite(pnl)
    full_kill = fire_kill & last_yr & np.isfinite(pnl)
    inc_S = ann_sharpe(pnl[full_inc], tpy)
    kill_S = ann_sharpe(pnl[full_kill], tpy)
    n_rem = int(full_inc.sum() - full_kill.sum())
    rem_msk = fire_inc & stress & last_yr & np.isfinite(pnl)
    rem_mean = float(np.mean(pnl[rem_msk]) * 100.0) if rem_msk.sum() else np.nan
    rem_S = ann_sharpe(pnl[rem_msk], tpy)
    print(f"  incumbent last-IS-yr: Sharpe={inc_S:+.3f} n={int(full_inc.sum())}")
    print(
        f"  kill-ON   last-IS-yr: Sharpe={kill_S:+.3f} n={int(full_kill.sum())}  "
        f"(d={kill_S - inc_S:+.3f})"
    )
    print(
        f"  REMOVED   last-IS-yr: n={n_rem} mean_pnl%={rem_mean:+.3f} Sharpe={rem_S:+.3f}  "
        f"(removed trades net-{'WINNERS' if rem_mean > 0 else 'losers'})"
    )
    rows.append(
        dict(
            test="last_is_year",
            sub_months=np.nan,
            n_subs=np.nan,
            min_sub_trades=np.nan,
            inc_recent3=inc_S,
            kill_recent3=kill_S,
            d_recent3=kill_S - inc_S,
        )
    )
    rows.append(
        dict(
            test="last_is_year_removed",
            sub_months=np.nan,
            n_subs=n_rem,
            min_sub_trades=np.nan,
            inc_recent3=rem_mean,
            kill_recent3=rem_S,
            d_recent3=np.nan,
        )
    )

    pd.DataFrame(rows).to_csv(OUTDIR / "grid_robustness.csv", index=False)
    print("\nWrote: " + str(OUTDIR / "grid_robustness.csv"))


if __name__ == "__main__":
    main()
