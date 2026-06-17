"""IS-ONLY robustness + decomposition of the R2 funding-CONTRA-CROWD chop re-admission — iter-v1/021.

R2 won the regime_conditioner_screen: re-admitting weak-trend (chop) rows ONLY when funding OPPOSES
the trend-state direction (and |funding z30| is at-least-median) adds back trades that THEMSELVES carry
a positive, sub-period-stable edge (readmit_full +0.56, recent3 +0.74) AND de-concentrates the combined
book (max single-month share 0.396 -> 0.349; top2-month 0.62 -> 0.545). The other candidates' re-admitted
rows are noise (full ~0 or negative). The mechanism is crypto-native:

  - SHORT trend (price below SMA200) + POSITIVE funding  = crowded LONGS paying to hold against the
    downtrend -> funding squeeze DOWN fuels the short. The trend-state direction (short) is RIGHT.
  - LONG trend (price above SMA200) + NEGATIVE funding   = crowded SHORTS paying to hold against the
    uptrend -> short squeeze UP fuels the long. The trend-state direction (long) is RIGHT.

In BOTH cases the funding-vs-trend OPPOSITION marks a positioning-fragility regime where the existing
trend-aligned direction is the high-quality side — exactly the entries the conviction gate over-skipped
because |dist_atr| was small (price near the SMA200), not because the trade was bad.

This script:
  (1) sweeps the funding-magnitude quantile q_f in {0.40, 0.50, 0.60, 0.70} -> NO knife-edge.
  (2) decomposes the re-admitted book by SIDE (must not be a single-leg artifact).
  (3) reports per-sub-period Sharpe of the COMBINED book vs REF_gated (stability lens).
  (4) reports the monthly-concentration improvement explicitly.
All thresholds PAST-ONLY; OOS never read.

Usage: uv run python analysis/BTCUSDT/iteration_v1-021/r2_funding_contra_robustness.py
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
from regime_conditioner_screen import past_only_quantile_threshold  # noqa: E402

OUTDIR = Path("analysis") / "BTCUSDT" / "iteration_v1-021"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_is()
    close = df["close"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    ot_ms = df["open_time"].to_numpy(float)
    y = fwd_log_return(close, N_LABEL)
    tpy = BARS_PER_YEAR / N_LABEL
    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    cp, sma, atr, dist_atr = past_only_primitives(df)
    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    direction = np.where(cp > sma, 1.0, -1.0)
    pnl = direction * y - (RT_COST / 100.0)

    gthr = past_only_gate_threshold(dist_atr, ot_days, bounds, Q_GATE)
    strong = np.isfinite(gthr) & (np.abs(dist_atr) >= gthr)
    weak = np.isfinite(gthr) & (np.abs(dist_atr) < gthr)
    fire_base = base & strong
    fire_chop = base & weak

    f_z30 = df["funding_rate_zscore_30"].shift(1).to_numpy(float)
    # funding OPPOSES trend: long-trend(+1) wants funding<0 (crowded shorts); short-trend(-1) wants funding>0
    opposes = np.sign(f_z30) == -np.sign(direction)

    b_base = stability(pnl, fire_base, ot_days, bounds, tpy)
    conc_base = monthly_concentration(pnl, fire_base, ot_ms)

    print(f"IS rows {len(df)}  N={N_LABEL}(14d)  gate q={Q_GATE}  RT={RT_COST}%")
    print("REF_gated(iter020 skeleton):", {k: b_base[k] for k in
          ["full", "frac_pos", "dispersion", "recent3", "n_trades", "win_rate"]},
          f"max_month_share={conc_base[0]:.3f} n_months={conc_base[1]} top2={conc_base[2]:.3f}")
    print("=" * 132)

    rows = []
    print(f"{'q_f':>5s} {'comb_full':>9s} {'comb_fpos':>9s} {'comb_disp':>9s} {'comb_rec3':>9s} "
          f"{'comb_trd':>8s} {'comb_WR':>7s} {'readmit_n':>9s} {'readmit_full':>12s} {'readmit_rec3':>12s} "
          f"{'maxMoShr':>9s} {'top2Shr':>8s}")
    for q_f in [0.40, 0.50, 0.60, 0.70]:
        thr = past_only_quantile_threshold(f_z30, ot_days, bounds, q_f)
        r2 = np.isfinite(f_z30) & np.isfinite(thr) & (np.abs(f_z30) >= thr) & opposes
        readmit = fire_chop & r2
        fire_cand = fire_base | readmit
        b = stability(pnl, fire_cand, ot_days, bounds, tpy)
        b_re = stability(pnl, readmit, ot_days, bounds, tpy)
        conc = monthly_concentration(pnl, fire_cand, ot_ms)
        print(f"{q_f:>5.2f} {b['full']!s:>9} {b['frac_pos']!s:>9} {b['dispersion']!s:>9} "
              f"{b['recent3']!s:>9} {b['n_trades']!s:>8} {b['win_rate']!s:>7} "
              f"{int(readmit.sum())!s:>9} {b_re['full']!s:>12} {b_re['recent3']!s:>12} "
              f"{round(conc[0],3)!s:>9} {round(conc[2],3)!s:>8}")
        rows.append(dict(q_f=q_f, comb_full=b["full"], comb_frac_pos=b["frac_pos"],
                         comb_dispersion=b["dispersion"], comb_recent3=b["recent3"],
                         comb_trades=b["n_trades"], comb_wr=b["win_rate"],
                         readmit_n=int(readmit.sum()), readmit_full=b_re["full"],
                         readmit_frac_pos=b_re["frac_pos"], readmit_recent3=b_re["recent3"],
                         readmit_wr=b_re["win_rate"], readmit_mret=b_re["mean_ret_pct"],
                         max_month_share=round(conc[0], 4), top2_month_share=round(conc[2], 4)))

    # --- side decomposition at the chosen q_f = 0.50 (median; the un-tuned mid choice) ---
    q_f = 0.50
    thr = past_only_quantile_threshold(f_z30, ot_days, bounds, q_f)
    r2 = np.isfinite(f_z30) & np.isfinite(thr) & (np.abs(f_z30) >= thr) & opposes
    readmit = fire_chop & r2
    fire_cand = fire_base | readmit
    print("\n" + "=" * 132)
    print(f"SIDE DECOMPOSITION of the COMBINED book at q_f={q_f} (long/short must both contribute; "
          "not a single-leg artifact):")
    for side_name, side_mask in [("LONG", direction > 0), ("SHORT", direction < 0)]:
        b = stability(pnl, fire_cand & side_mask, ot_days, bounds, tpy)
        b_re = stability(pnl, readmit & side_mask, ot_days, bounds, tpy)
        print(f"  combined {side_name:5s}: full={b['full']} fpos={b['frac_pos']} rec3={b['recent3']} "
              f"trd={b['n_trades']} WR={b['win_rate']} | readmitted {side_name}: full={b_re['full']} "
              f"rec3={b_re['recent3']} n={b_re['n_trades']} WR={b_re['win_rate']}")

    # --- per-sub-period combined vs gated (stability lens) ---
    b_comb = stability(pnl, fire_cand, ot_days, bounds, tpy)
    print("\n" + "=" * 132)
    print("PER-SUB-PERIOD NET ANNUALIZED SHARPE (last col = most-recent IS sub-period):")
    print("  " + f"{'book':30s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for name, b in [("REF_gated", b_base), (f"R2_combined_q{q_f}", b_comb)]:
        cells = [f"{v:+7.2f}" if (v is not None and np.isfinite(v)) else f"{'·':>7s}" for v in b["per_sub"]]
        print(f"  {name:30s} " + " ".join(cells))

    # --- explicit concentration table (per-month net share, gated vs combined) ---
    print("\n" + "=" * 132)
    print("MONTHLY-CONCENTRATION (top-5 months by |net share| of book net):")
    for name, fire in [("REF_gated", fire_base), (f"R2_combined_q{q_f}", fire_cand)]:
        f = fire & np.isfinite(pnl)
        ts = pd.to_datetime(ot_ms[f], unit="ms").to_period("M").astype(str)
        by = pd.DataFrame({"m": ts, "pnl": pnl[f]}).groupby("m")["pnl"].agg(["sum", "count"])
        netsum = by["sum"].sum()
        by["share"] = by["sum"] / netsum
        top = by.reindex(by["share"].abs().sort_values(ascending=False).index).head(5)
        print(f"  {name}: net={netsum:+.3f} months={by.shape[0]}")
        for m, r in top.iterrows():
            print(f"      {m}  share={r['share']:+.3f}  net={r['sum']:+.3f}  trades={int(r['count'])}")

    pd.DataFrame(rows).to_csv(OUTDIR / "r2_funding_contra_robustness.csv", index=False)
    print("\nWrote:", OUTDIR / "r2_funding_contra_robustness.csv")


if __name__ == "__main__":
    main()
