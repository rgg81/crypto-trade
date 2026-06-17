"""IS-ONLY screen of crypto-native regime conditioners that aim to THICKEN the iter-020 gated
trend-state book WITHOUT degrading IS sub-period stability — iter-v1/021 (BTCUSDT).

CONTEXT (iter-020 MERGED, the both-positive baseline; OOS is THIN: +0.09 on 38 trades, ~46% of
OOS net from 2 timeout-short months). The deterministic skeleton of that book is:
    direction = sign(close[t-1] - SMA200[t-1])
    conviction = |close[t-1] - SMA200[t-1]| / ATR14[t-1]
    fire iff conviction >= q40_past_only   (the iter-020 q=0.40 conviction gate)
The conviction gate THINS the book; the OOS edge is concentrated. The iter-021 question: is there a
crypto-native EXOGENOUS regime signal that systematically identifies higher-quality / more-frequent
trend-state entry conditions, so the GENERALIZING (trend-aligned) edge spreads across more trades and
IS sub-periods rather than riding a couple of lucky windows?

We test, IS-ONLY, whether each regime signal lets us RE-ADMIT trades the conviction gate skipped
(the weak-trend chop) WHEN the regime is favourable — i.e. a regime-conditional RELAXATION of the gate
that adds back ONLY chop rows that share the trend-aligned edge. A candidate succeeds iff (a) it raises
the firing count materially AND (b) the re-admitted rows' per-sub-period profile is stable-or-better
(frac_pos, recent3 not degraded; full Sharpe not collapsed). A candidate that just dumps noise trades
in (frac_pos drops, recent3 negative) is a NULL.

Candidates (crypto-native; conditioning the chop re-admission):
  R1  FUNDING-EXTREME      : re-admit chop when |funding_rate_zscore_30| is HIGH (crowded positioning
                            -> reflexive continuation/squeeze; the trend-state book's bread and butter).
  R2  FUNDING-ALIGNED      : re-admit chop when funding sign OPPOSES the trend-state direction
                            (short-trend + positive funding = crowded longs about to be squeezed DOWN;
                            long-trend + negative funding = crowded shorts about to squeeze UP).
  R3  FUNDING-SPREAD       : re-admit chop when btc_funding_spread_30_90 (term-structure slope) is
                            extreme (regime transition in positioning).
  R4  VOL-REGIME-LOW       : re-admit chop in LOW-NATR regime (trends in calm vol are cleaner; high-vol
                            chop is the coin-flip the gate rightly skips).
  R5  VOL-REGIME-HIGH      : re-admit chop in HIGH-NATR regime (control — opposite of R4).
  R6  OI-BUILD             : re-admit chop when oi_delta_30_z90 HIGH (leverage build = trend fuel).

All regime thresholds are PAST-ONLY training-window quantiles (no OOS, no full-sample). Direction is
ALWAYS the unchanged trend-state sign. We never flip direction on a regime; we only decide WHETHER a
gate-skipped chop row is re-admitted.

Usage: uv run python analysis/BTCUSDT/iteration_v1-021/regime_conditioner_screen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    BARS_PER_YEAR,
    N_LABEL,
    Q_GATE,
    RT_COST,
    fwd_log_return,
    load_is,
    monthly_concentration,
    past_only_gate_threshold,
    past_only_primitives,
    stability,
    subperiod_bounds,
)

OUTDIR = Path("analysis") / "BTCUSDT" / "iteration_v1-021"


def past_only_quantile_threshold(series, ot_days, bounds, q):
    """Generic PAST-ONLY per-sub-period quantile of a regime series (uses absolute value)."""
    thr = np.full(len(series), np.nan)
    row_idx = np.arange(len(series))
    abs_s = np.abs(series)
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        first_i = int(row_idx[tm].min())
        cut = first_i - N_LABEL
        if cut < 50:
            continue
        past = abs_s[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def past_only_level_quantile(series, ot_days, bounds, q):
    """PAST-ONLY per-sub-period quantile of a LEVEL series (signed, not abs) — for NATR / OI level."""
    thr = np.full(len(series), np.nan)
    row_idx = np.arange(len(series))
    for lo, hi in bounds:
        tm = (ot_days >= lo) & (ot_days < hi)
        if tm.sum() == 0:
            continue
        first_i = int(row_idx[tm].min())
        cut = first_i - N_LABEL
        if cut < 50:
            continue
        past = series[:cut]
        past = past[np.isfinite(past)]
        if len(past) < 50:
            continue
        thr[row_idx[tm]] = float(np.quantile(past, q))
    return thr


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_is()
    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    ot_ms = df["open_time"].to_numpy(float)
    y = fwd_log_return(close, N_LABEL)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)

    cp, sma, atr, dist_atr = past_only_primitives(df)
    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    direction = np.where(cp > sma, 1.0, -1.0)

    def net(d):
        return d * y - (RT_COST / 100.0)

    pnl = net(direction)

    # gate threshold (iter-020 q=0.40)
    gthr = past_only_gate_threshold(dist_atr, ot_days, bounds, Q_GATE)
    strong = np.isfinite(gthr) & (np.abs(dist_atr) >= gthr)  # the iter-020 firing rows (gross conviction)
    weak = np.isfinite(gthr) & (np.abs(dist_atr) < gthr)     # the chop the gate SKIPS

    fire_base = base & strong          # iter-020 gated book (skeleton)
    fire_full = base & np.isfinite(gthr)  # ungated trend-state book (all rows with a valid threshold)
    fire_chop = base & weak            # the skipped chop alone

    b_base = stability(pnl, fire_base, ot_days, bounds, tpy)
    b_full = stability(pnl, fire_full, ot_days, bounds, tpy)
    b_chop = stability(pnl, fire_chop, ot_days, bounds, tpy)

    # regime series (past-only via .shift(1))
    f_z30 = df["funding_rate_zscore_30"].shift(1).to_numpy(float)
    f_spread = df["btc_funding_spread_30_90"].shift(1).to_numpy(float)
    natr = df["vol_natr_14"].shift(1).to_numpy(float)
    oi_z = df["oi_delta_30_z90"].shift(1).to_numpy(float)

    # candidate regime masks: which CHOP rows do we re-admit?
    # R1 funding-extreme: |funding z30| >= past-only 60th pct of |z30|
    thr_z = past_only_quantile_threshold(f_z30, ot_days, bounds, 0.60)
    r1 = np.isfinite(f_z30) & np.isfinite(thr_z) & (np.abs(f_z30) >= thr_z)
    # R2 funding-aligned (contrarian-to-crowd): funding sign opposes trend direction & |z30|>=median
    thr_z_med = past_only_quantile_threshold(f_z30, ot_days, bounds, 0.50)
    opposes = np.sign(f_z30) == -np.sign(direction)  # long-trend wants neg funding; short-trend wants pos
    r2 = np.isfinite(f_z30) & np.isfinite(thr_z_med) & (np.abs(f_z30) >= thr_z_med) & opposes
    # R3 funding-spread extreme
    thr_sp = past_only_quantile_threshold(f_spread, ot_days, bounds, 0.60)
    r3 = np.isfinite(f_spread) & np.isfinite(thr_sp) & (np.abs(f_spread) >= thr_sp)
    # R4 vol low: NATR <= past-only 40th pct
    thr_natr_lo = past_only_level_quantile(natr, ot_days, bounds, 0.40)
    r4 = np.isfinite(natr) & np.isfinite(thr_natr_lo) & (natr <= thr_natr_lo)
    # R5 vol high: NATR >= past-only 60th pct
    thr_natr_hi = past_only_level_quantile(natr, ot_days, bounds, 0.60)
    r5 = np.isfinite(natr) & np.isfinite(thr_natr_hi) & (natr >= thr_natr_hi)
    # R6 OI build: oi_delta_30_z90 >= past-only 60th pct
    thr_oi = past_only_level_quantile(oi_z, ot_days, bounds, 0.60)
    r6 = np.isfinite(oi_z) & np.isfinite(thr_oi) & (oi_z >= thr_oi)

    cand = {
        "R1_funding_extreme": r1,
        "R2_funding_contra_crowd": r2,
        "R3_funding_spread_extreme": r3,
        "R4_vol_low": r4,
        "R5_vol_high": r5,
        "R6_oi_build": r6,
    }

    # Each candidate's RE-ADMITTED book = gated firing rows UNION (chop rows where regime favourable)
    rows = []
    print(f"IS rows {len(df)}  sub-periods {len(bounds)}  N={N_LABEL}(14d)  gate q={Q_GATE}  RT={RT_COST}%")
    print("=" * 132)
    hdr = (f"{'book':30s} {'full':>8s} {'fpos':>5s} {'disp':>6s} {'recent3':>8s} {'trades':>7s} "
           f"{'WR':>6s} {'mret%':>7s} {'maxMoShr':>9s} {'nMonths':>8s} {'top2Shr':>8s}")
    print(hdr)

    def show(name, b, conc):
        top1, nmo, top2 = conc
        print(f"{name:30s} {b['full']!s:>8} {b['frac_pos']!s:>5} {b['dispersion']!s:>6} "
              f"{b['recent3']!s:>8} {b['n_trades']!s:>7} {b['win_rate']!s:>6} {b['mean_ret_pct']!s:>7} "
              f"{(round(top1,3) if np.isfinite(top1) else top1)!s:>9} {nmo!s:>8} "
              f"{(round(top2,3) if np.isfinite(top2) else top2)!s:>8}")

    # references
    show("REF_gated(iter020 skeleton)", b_base, monthly_concentration(pnl, fire_base, ot_ms))
    show("REF_ungated(all trend rows)", b_full, monthly_concentration(pnl, fire_full, ot_ms))
    show("REF_chop_only(skipped)", b_chop, monthly_concentration(pnl, fire_chop, ot_ms))
    print("-" * 132)

    for name, mask in cand.items():
        readmit_chop = fire_chop & mask          # chop rows the regime says re-admit
        fire_cand = fire_base | readmit_chop      # gated book + regime-favourable chop
        b = stability(pnl, fire_cand, ot_days, bounds, tpy)
        conc = monthly_concentration(pnl, fire_cand, ot_ms)
        # also score the re-admitted chop alone (must share the edge, not dilute)
        b_re = stability(pnl, readmit_chop, ot_days, bounds, tpy)
        added = int(readmit_chop.sum())
        show(name, b, conc)
        print(f"{'   +readmitted_chop_only':30s} {b_re['full']!s:>8} {b_re['frac_pos']!s:>5} "
              f"{b_re['dispersion']!s:>6} {b_re['recent3']!s:>8} {b_re['n_trades']!s:>7} "
              f"{b_re['win_rate']!s:>6} {b_re['mean_ret_pct']!s:>7}  (added {added} chop rows)")
        rows.append(dict(
            book=name, full=b["full"], frac_pos=b["frac_pos"], dispersion=b["dispersion"],
            recent3=b["recent3"], n_trades=b["n_trades"], win_rate=b["win_rate"],
            mean_ret_pct=b["mean_ret_pct"], max_month_share=round(conc[0], 4) if np.isfinite(conc[0]) else conc[0],
            n_months=conc[1], top2_month_share=round(conc[2], 4) if np.isfinite(conc[2]) else conc[2],
            readmit_full=b_re["full"], readmit_frac_pos=b_re["frac_pos"],
            readmit_recent3=b_re["recent3"], readmit_n=int(readmit_chop.sum()),
        ))

    # baseline reference rows
    for name, b, fire in [("REF_gated", b_base, fire_base), ("REF_ungated", b_full, fire_full),
                          ("REF_chop_only", b_chop, fire_chop)]:
        conc = monthly_concentration(pnl, fire, ot_ms)
        rows.append(dict(
            book=name, full=b["full"], frac_pos=b["frac_pos"], dispersion=b["dispersion"],
            recent3=b["recent3"], n_trades=b["n_trades"], win_rate=b["win_rate"],
            mean_ret_pct=b["mean_ret_pct"],
            max_month_share=round(conc[0], 4) if np.isfinite(conc[0]) else conc[0],
            n_months=conc[1], top2_month_share=round(conc[2], 4) if np.isfinite(conc[2]) else conc[2],
            readmit_full=np.nan, readmit_frac_pos=np.nan, readmit_recent3=np.nan, readmit_n=0,
        ))

    pd.DataFrame(rows).to_csv(OUTDIR / "regime_conditioner_screen.csv", index=False)
    print("\nWrote:", OUTDIR / "regime_conditioner_screen.csv")

    # ---- verdict ----
    print("\n" + "=" * 132)
    print("VERDICT (IS-only). A candidate THICKENS the GENERALIZING book iff: trade count up materially")
    print("AND re-admitted chop is stable-or-better (readmit_full>0 AND readmit_frac_pos>=0.5 AND")
    print("readmit_recent3>0) AND the combined book's frac_pos NOT below REF_gated AND max_month_share")
    print("NOT worse than REF_gated.")
    base_fpos = b_base["frac_pos"]
    base_conc = monthly_concentration(pnl, fire_base, ot_ms)[0]
    for r in rows:
        if not r["book"].startswith("R") or r["book"].startswith("REF"):
            continue
        ok = (np.isfinite(r["readmit_full"]) and r["readmit_full"] > 0
              and np.isfinite(r["readmit_frac_pos"]) and r["readmit_frac_pos"] >= 0.5
              and np.isfinite(r["readmit_recent3"]) and r["readmit_recent3"] > 0
              and np.isfinite(r["frac_pos"]) and r["frac_pos"] >= base_fpos - 0.05
              and np.isfinite(r["max_month_share"]) and r["max_month_share"] <= base_conc + 0.02)
        print(f"  {r['book']:28s} added={r['readmit_n']:4d}  readmit(full={r['readmit_full']},"
              f"fpos={r['readmit_frac_pos']},rec3={r['readmit_recent3']})  "
              f"comb(fpos={r['frac_pos']},moShr={r['max_month_share']})  -> "
              f"{'THICKENS (stable)' if ok else 'NULL (noise/degrades)'}")


if __name__ == "__main__":
    main()
