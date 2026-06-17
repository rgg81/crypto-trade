"""IS-ONLY: DECOMPOSE the leading exogenous kill-switch (vol_state_z_natr_30 high-state) to distinguish
a GENUINE generalizing kill from the iter-011 FRAGILE recent-regime curve-fit. — iter-v1/024 (BTCUSDT).

exogenous_kill_switch.py found the realized-vol NATR z-state kill (vol_state_z_natr_30 >= past-only
cut) lifts the iter-020 trend-state book's recent3 Sharpe across ALL 6/6 cuts (plateau), best in the
0.70-0.80 band. THIS SCRIPT is the iter-011 fragility CONTROL. A plateau on recent3 is necessary but
NOT sufficient: it could still be the iter-011 failure mode (helps only by deleting the single
most-recent sub-period = OOS-curve-fit by proxy; or lifts recent3 while degrading the earlier
sub-periods = a fragile regime beta).

DECISIVE QUESTIONS (all IS-only):
  Q1. SIGN CONSISTENCY: of the sub-periods where the kill removes >=1 trade, in how many does the
      per-sub-period Sharpe go UP? A genuine kill helps in MANY sub-periods; a recent-regime curve-fit
      helps only in the last 1-2.
  Q2. NO EARLY DEGRADATION: does the kill leave the early/middle sub-periods >= incumbent (within
      noise), or does it sacrifice them for the recent ones (iter-011 fragility)?
  Q3. KILLED-TRADE EDGE: are the trades the kill REMOVES actually net-LOSERS (so removing them is
      principled), and is that loss-edge consistent across sub-periods (not just recent)?
  Q4. RECENT-SUB-PERIOD ROBUSTNESS: if we drop the single most-recent sub-period entirely from the
      recent3 average, does the kill STILL lift recent2 / the negative sub-periods? (curve-fit-by-proxy
      detector: a kill that only helps via the last sub-period FAILS this.)
  Q5. CROSS-MECHANISM CONFIRM: does the SAME high-RVOL-state kill help on the second plateau candidate
      (OI-price-divergence) and the ungated (no strength gate) trend-state book -- i.e. is the kill's
      benefit a property of the RVOL regime, not an artifact of the strength gate?

OOS-VIGILANCE (HARD): strict IS filter + leak assert; `.shift(1)` past-only SMA200/ATR14 and stress
signal; per-sub-period stress cut quantile trained on PAST rows only (purged by N_LABEL); OOS never
read. The chosen cut (0.80) is selected on the PLATEAU EVIDENCE (mid-band, robust), NOT on what helps OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-024/kill_decomposition.py
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
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
SMA_WIN = 200
ATR_WIN = 14
RT_COST = 0.14
Q_STRENGTH = 0.40

KILL_COL = "vol_state_z_natr_30"  # leading PLATEAU candidate
KILL_CUT = 0.80  # mid-band plateau cut (chosen on plateau evidence, IS-only)
CONFIRM_COL = "oi_price_divergence_30"  # second plateau candidate (cross-mechanism confirm)
CONFIRM_CUT = 0.85


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


def per_sub(pnl, fire, ot_days, bounds, tpy):
    out = []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(pnl)
        arr = pnl[m]
        n = int(np.isfinite(arr).sum())
        out.append((ann_sharpe(arr, tpy) if n >= MIN_SUB_TRADES else np.nan, n))
    return out


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
    labs = [str(pd.to_datetime(lo * 86400_000, unit="ms").date())[2:7] for lo, _ in bounds]

    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    absd = np.abs(dist_atr)
    dir_ts = np.where(cp > sma, 1.0, -1.0)
    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    pnl = dir_ts * y - (RT_COST / 100.0)

    thr_str = past_only_quantile_threshold(absd, ot_days, bounds, Q_STRENGTH)
    fire_inc = base & np.isfinite(thr_str) & (absd >= thr_str)

    # KILL signal (RVOL high-state, past-only)
    sig = pd.Series(df[KILL_COL].to_numpy(float)).shift(1).to_numpy()
    thr_k = past_only_quantile_threshold(sig, ot_days, bounds, KILL_CUT)
    stress = np.isfinite(sig) & np.isfinite(thr_k) & (sig >= thr_k)
    fire_kill = fire_inc & ~stress  # retained (kill ON)
    fire_removed = fire_inc & stress  # the trades the kill REMOVES

    inc_sub = per_sub(pnl, fire_inc, ot_days, bounds, tpy)
    kill_sub = per_sub(pnl, fire_kill, ot_days, bounds, tpy)
    rem_sub = per_sub(pnl, fire_removed, ot_days, bounds, tpy)

    print(
        f"IS rows {len(df)}  KILL={KILL_COL}>=q{KILL_CUT}  N={N_LABEL}  sub-periods={len(bounds)}"
    )
    print("=" * 130)
    print(
        "Q1/Q2/Q3 — PER-SUB-PERIOD DECOMPOSITION (incumbent vs kill-ON, and the REMOVED trades' edge)"
    )
    print("=" * 130)
    print(
        f"{'sub':>6s} {'inc_S':>7s} {'inc_n':>6s} {'kill_S':>7s} {'kill_n':>6s} "
        f"{'dS':>7s} {'#removed':>8s} {'removed_S':>9s} {'rem_meanPnL%':>12s}"
    )
    rows = []
    n_eval = n_up = n_dn = 0
    for i, lab in enumerate(labs):
        iS, iN = inc_sub[i]
        kS, kN = kill_sub[i]
        rS, rN = rem_sub[i]
        n_removed = iN - kN
        # mean PnL% of removed trades this sub-period
        lo, hi = bounds[i]
        msk = (ot_days >= lo) & (ot_days < hi) & fire_removed & np.isfinite(pnl)
        rem_mean = float(np.mean(pnl[msk]) * 100.0) if msk.sum() else np.nan
        dS = (kS - iS) if (np.isfinite(kS) and np.isfinite(iS)) else np.nan
        if n_removed > 0 and np.isfinite(dS):
            n_eval += 1
            if dS > 0:
                n_up += 1
            elif dS < 0:
                n_dn += 1

        def f(v, nd=2):
            return f"{v:+.{nd}f}" if (v is not None and np.isfinite(v)) else "   ·  "

        print(
            f"{lab:>6s} {f(iS):>7s} {iN:>6d} {f(kS):>7s} {kN:>6d} {f(dS):>7s} "
            f"{n_removed:>8d} {f(rS):>9s} {f(rem_mean):>12s}"
        )
        rows.append(
            dict(
                sub=lab,
                inc_sharpe=iS,
                inc_n=iN,
                kill_sharpe=kS,
                kill_n=kN,
                d_sharpe=dS,
                n_removed=n_removed,
                removed_sharpe=rS,
                removed_mean_pnl_pct=rem_mean,
            )
        )
    pd.DataFrame(rows).to_csv(OUTDIR / "kill_decomposition.csv", index=False)

    print("\n" + "=" * 130)
    print(
        f"Q1 SIGN CONSISTENCY: of {n_eval} sub-periods where the kill removed >=1 trade, "
        f"{n_up} improved (dS>0), {n_dn} worsened (dS<0)."
    )
    print(
        "   GENUINE kill -> improves in a MAJORITY across the span. FRAGILE/curve-fit -> helps only recently."
    )

    # Q3 aggregate: are removed trades net-losers, and consistently?
    rem_all = pnl[fire_removed & np.isfinite(pnl)]
    ret_all = pnl[fire_kill & np.isfinite(pnl)]
    print(
        f"\nQ3 KILLED-TRADE EDGE (aggregate): removed n={len(rem_all)} "
        f"meanPnL%={np.mean(rem_all) * 100:+.4f} WR={np.mean(rem_all > 0):.3f} Sharpe={ann_sharpe(rem_all, tpy):+.3f}"
    )
    print(
        f"   RETAINED n={len(ret_all)} meanPnL%={np.mean(ret_all) * 100:+.4f} "
        f"WR={np.mean(ret_all > 0):.3f} Sharpe={ann_sharpe(ret_all, tpy):+.3f}"
    )
    print(
        "   PRINCIPLED kill -> removed trades are net-WORSE than retained (kill cuts the losing tail)."
    )

    # Q4 curve-fit-by-proxy detector: recompute recent stats DROPPING the last scored sub-period.
    inc_S = np.array([s for s, _ in inc_sub], float)
    kill_S = np.array([s for s, _ in kill_sub], float)

    def recent_avg(arr, k, drop_last=0):
        seq = [v for v in reversed(arr) if np.isfinite(v)]
        seq = seq[drop_last:]
        return float(np.mean(seq[:k])) if len(seq) >= 1 else np.nan

    print("\n" + "=" * 130)
    print("Q4 CURVE-FIT-BY-PROXY DETECTOR (drop the single most-recent scored sub-period):")
    for drop_last, tag in ((0, "all sub-periods"), (1, "DROP most-recent")):
        ir3 = recent_avg(inc_S, 3, drop_last)
        kr3 = recent_avg(kill_S, 3, drop_last)
        ir2 = recent_avg(inc_S, 2, drop_last)
        kr2 = recent_avg(kill_S, 2, drop_last)
        print(
            f"   [{tag:18s}] recent3: inc={ir3:+.3f} kill={kr3:+.3f} (d={kr3 - ir3:+.3f})   "
            f"recent2: inc={ir2:+.3f} kill={kr2:+.3f} (d={kr2 - ir2:+.3f})"
        )
    print(
        "   GENUINE kill -> still lifts recent2/recent3 AFTER dropping the last sub-period. "
        "CURVE-FIT-by-proxy -> lift vanishes when the last sub-period is removed."
    )

    # Negative-sub-period rescue: does the kill rescue the incumbent's NEGATIVE sub-periods?
    print("\nNEGATIVE-SUB-PERIOD RESCUE (incumbent sub-periods that were < 0):")
    for i, lab in enumerate(labs):
        iS, _ = inc_sub[i]
        kS, _ = kill_sub[i]
        if np.isfinite(iS) and iS < 0:
            d = (kS - iS) if np.isfinite(kS) else np.nan
            print(
                f"   {lab}: inc={iS:+.3f} -> kill={kS if np.isfinite(kS) else float('nan'):+.3f} "
                f"(d={d:+.3f})"
            )

    # Q5 cross-mechanism + ungated confirm
    print("\n" + "=" * 130)
    print(
        "Q5 CROSS-MECHANISM / UNGATED CONFIRM (is the RVOL-kill benefit a regime property, "
        "not a strength-gate artifact?):"
    )
    # ungated trend-state book (no strength gate) under the same RVOL kill
    fire_ung = base.copy()
    fire_ung_kill = fire_ung & ~stress

    def r3(fire):
        ps = per_sub(pnl, fire, ot_days, bounds, tpy)
        seq = [s for s, _ in ps if np.isfinite(s)]
        seq = list(reversed(seq))
        full = ann_sharpe(pnl[fire & np.isfinite(pnl)], tpy)
        return (
            float(np.mean(seq[:3])) if len(seq) >= 3 else np.nan,
            full,
            int(np.isfinite(pnl[fire]).sum()),
        )

    ung_r3, ung_full, ung_n = r3(fire_ung)
    ungk_r3, ungk_full, ungk_n = r3(fire_ung_kill)
    print(
        f"   UNGATED trend-state (no strength gate): recent3 {ung_r3:+.3f} full {ung_full:+.3f} "
        f"n={ung_n}  -> + RVOL kill: recent3 {ungk_r3:+.3f} full {ungk_full:+.3f} n={ungk_n}  "
        f"(d_recent3 {ungk_r3 - ung_r3:+.3f})"
    )
    # second plateau mechanism (OI-price divergence) on the strength-gated book
    sig2 = pd.Series(df[CONFIRM_COL].to_numpy(float)).shift(1).to_numpy()
    sig2 = np.abs(sig2)
    thr2 = past_only_quantile_threshold(sig2, ot_days, bounds, CONFIRM_CUT)
    stress2 = np.isfinite(sig2) & np.isfinite(thr2) & (sig2 >= thr2)
    fire_c = fire_inc & ~stress2
    c_r3, c_full, c_n = r3(fire_c)
    inc_r3, inc_full, inc_n = r3(fire_inc)
    print(f"   INCUMBENT strength-gated: recent3 {inc_r3:+.3f} full {inc_full:+.3f} n={inc_n}")
    print(
        f"   2nd mechanism (OI-price-divergence kill q{CONFIRM_CUT}): recent3 {c_r3:+.3f} "
        f"full {c_full:+.3f} n={c_n}  (d_recent3 {c_r3 - inc_r3:+.3f})"
    )
    # combined RVOL + OI kill (do they stack or overlap?)
    fire_both = fire_inc & ~stress & ~stress2
    b_r3, b_full, b_n = r3(fire_both)
    print(
        f"   COMBINED RVOL+OI kill: recent3 {b_r3:+.3f} full {b_full:+.3f} n={b_n}  "
        f"(d_recent3 vs incumbent {b_r3 - inc_r3:+.3f})"
    )
    print("\nWrote: " + str(OUTDIR / "kill_decomposition.csv"))


if __name__ == "__main__":
    main()
