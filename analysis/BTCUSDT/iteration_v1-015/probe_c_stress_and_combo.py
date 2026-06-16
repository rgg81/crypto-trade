"""PROBE C + STRESS MATRIX (iter-v1/015, BTCUSDT, IS-ONLY).

THREE jobs:
  C1. TIGHTER / VOL-ADAPTIVE STOP (user candidate #3) — does shrinking the let-run SL multiple cap
      the per-trade tail and lift pooled Sharpe? The let-run book uses atr_sl=1.45; sweep
      {1.0, 1.25, 1.45, 1.75} and a vol-adaptive variant. Measure pooled Sharpe + maxDD + worst
      trade + trade-count (SL change does NOT change WHICH trades fire, but changes exit prices).
  C2. COMBO — the chosen R2 brake (Probe B) STACKED with conviction-floor sizing (Probe A) — do the
      two regime-agnostic risk controls compose, or is R2 alone the dominant lever?
  C3. STRESS MATRIX for the chosen risk config: slippage cost-stress {1x,2x,4x}, tail-loss
      (worst single trade / worst day OFF vs ON), and the vol-spike replay (highest-NATR windows).

KEY METRIC DISCIPLINE (iter-012 lesson): pooled Sharpe + additive maxDD + tail, NOT per-sub-period
Sharpe (invariant to within-window size multiplier). R2/conviction are SIZING => pooled lens; the
SL multiple is an EXIT change => it changes the return distribution itself (legitimately moves
per-trade Sharpe too).

OOS-VIGILANCE: IS-only frame; path-only brake; past-only vol; no forward info.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-015/probe_c_stress_and_combo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _harness import (  # noqa: E402
    ATR_COLUMN,
    BASE_PARAMS,
    FEE_PCT,
    ITER009_FEATURES,
    N_LABEL,
    OOS_CUTOFF_MS,
    SYMBOL,
    expanding_wf_with_margin,
    fwd_return,
    letrun,
    load_is_frame,
    pooled_ann_sharpe,
    proxy_maxdd,
)
from probe_b_drawdown_brake import apply_drawdown_brake  # noqa: E402

PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-015"
TRG, ANC, FLR = 20, 80, 0.2  # chosen R2 config


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = load_is_frame(PARQUET)
    n_is = len(df)
    print(f"IS rows: {n_is}  (max open_time {int(df['open_time'].max())} < cutoff {OOS_CUTOFF_MS})")

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    natr = df[ATR_COLUMN].to_numpy(float)
    atr = close * natr / 100.0
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)

    d, oof, pv = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, 42)

    # ===================== C1. SL-MULTIPLE SWEEP =====================
    print("\n" + "=" * 100)
    print("C1. STOP-LOSS MULTIPLE SWEEP (let-run book, seed 42) — exit change, pooled lens + tail")
    print("=" * 100)
    rows = []
    for sl_mult in (1.0, 1.25, 1.45, 1.75, 2.0):
        mb, reason = letrun(high, low, close, atr, d, sl_mult, N_LABEL)
        fm = oof & np.isfinite(mb)
        fi = np.where(fm)[0]
        fi = fi[np.argsort(ot_days[fi])]
        rets = mb[fi]
        rows.append(dict(
            atr_sl=sl_mult, n=int(fm.sum()),
            WR=round(float((rets > 0).mean()), 3),
            pooled_sharpe=round(pooled_ann_sharpe(rets, n_is), 3),
            maxDD=round(proxy_maxdd(rets), 1),
            worst_trade=round(float(rets.min()), 2),
            sl_exit_frac=round(float((reason[fm] == 1.0).mean()), 3),
            total_ret=round(float(rets.sum()), 1),
        ))
    sl_df = pd.DataFrame(rows)
    sl_df.to_csv(OUTDIR / "sl_multiple_sweep.csv", index=False)
    print(sl_df.to_string(index=False))
    print("  (atr_sl=1.45 is the iter-009/010 incumbent; tighter caps tail but may cut winners)")

    # ===================== C2. COMBO: R2 + conviction floor =====================
    print("\n" + "=" * 100)
    print("C2. COMBO — R2 brake alone vs R2 + conviction-floor sizing (both regime-agnostic)")
    print("=" * 100)
    mb, _r = letrun(high, low, close, atr, d, 1.45, N_LABEL)
    fm = oof & np.isfinite(mb)
    fi = np.where(fm)[0]
    fi = fi[np.argsort(ot_days[fi])]
    rets = mb[fi]
    conv = np.abs(pv)[fi]
    conv_pct = pd.Series(conv).rank(pct=True).to_numpy()
    base_s = pooled_ann_sharpe(rets, n_is)
    base_dd = proxy_maxdd(rets)
    # R2 alone
    rw_r2, _ = apply_drawdown_brake(rets, TRG, ANC, FLR)
    # conviction floor 0.35 alone
    w_conv = 0.35 + 0.65 * conv_pct
    rw_conv = rets * w_conv
    # combo: apply conviction size first, then R2 on the conviction-sized stream
    rw_combo, _ = apply_drawdown_brake(rets * w_conv, TRG, ANC, FLR)
    combo_rows = [
        dict(config="baseline", pooled_sharpe=round(base_s, 3), maxDD=round(base_dd, 1),
             total_ret=round(float(rets.sum()), 1)),
        dict(config="R2 only", pooled_sharpe=round(pooled_ann_sharpe(rw_r2, n_is), 3),
             maxDD=round(proxy_maxdd(rw_r2), 1), total_ret=round(float(rw_r2.sum()), 1)),
        dict(config="conviction only (floor .35)",
             pooled_sharpe=round(pooled_ann_sharpe(rw_conv, n_is), 3),
             maxDD=round(proxy_maxdd(rw_conv), 1), total_ret=round(float(rw_conv.sum()), 1)),
        dict(config="R2 + conviction", pooled_sharpe=round(pooled_ann_sharpe(rw_combo, n_is), 3),
             maxDD=round(proxy_maxdd(rw_combo), 1), total_ret=round(float(rw_combo.sum()), 1)),
    ]
    combo_df = pd.DataFrame(combo_rows)
    combo_df.to_csv(OUTDIR / "combo.csv", index=False)
    print(combo_df.to_string(index=False))

    # ===================== C3a. SLIPPAGE COST-STRESS for chosen R2 =====================
    print("\n" + "=" * 100)
    print("C3a. SLIPPAGE COST-STRESS — chosen R2 brake, slippage {1x,2x,4x} of 2bps/side merge assn")
    print("=" * 100)
    # the harness letrun already nets FEE_PCT=0.1; add round-trip slippage = 2 * bps/side / 100 (pct).
    rows3 = []
    for bps in (2.0, 4.0, 8.0):  # 1x=2 (merge), 2x=4, 4x=8
        rt_slip = 2.0 * bps / 100.0  # round-trip pct
        rets_s = rets - rt_slip  # additional per-trade drag on top of fee already in letrun
        s_off = pooled_ann_sharpe(rets_s, n_is)
        dd_off = proxy_maxdd(rets_s)
        rw_s, _ = apply_drawdown_brake(rets_s, TRG, ANC, FLR)
        s_on = pooled_ann_sharpe(rw_s, n_is)
        dd_on = proxy_maxdd(rw_s)
        rows3.append(dict(
            slippage_bps_per_side=bps, rt_drag_pct=round(rt_slip, 3),
            sharpe_OFF=round(s_off, 3), sharpe_ON=round(s_on, 3),
            sharpe_delta=round(s_on - s_off, 3),
            maxDD_OFF=round(dd_off, 1), maxDD_ON=round(dd_on, 1),
        ))
    slip_df = pd.DataFrame(rows3)
    slip_df.to_csv(OUTDIR / "slippage_stress.csv", index=False)
    print(slip_df.to_string(index=False))
    print("  (merge cost = 2.0 bps/side = v1 standard. R2 lift must stay positive at all 3.)")

    # ===================== C3b. TAIL-LOSS + VOL-SPIKE REPLAY =====================
    print("\n" + "=" * 100)
    print("C3b. TAIL-LOSS + VOL-SPIKE replay (chosen R2 brake) — worst trade / worst day / hi-NATR")
    print("=" * 100)
    rw_r2_full, scales = apply_drawdown_brake(rets, TRG, ANC, FLR)
    # worst single trade
    print(f"  worst single trade: OFF {rets.min():+.2f}%  ON {rw_r2_full.min():+.2f}%  "
          f"({100*(rw_r2_full.min()-rets.min())/abs(rets.min()):+.0f}%)")
    # worst day: group by calendar day
    days = (ot_days[fi]).astype(int)
    day_off = pd.Series(rets).groupby(days).sum()
    day_on = pd.Series(rw_r2_full).groupby(days).sum()
    print(f"  worst single day:   OFF {day_off.min():+.2f}%  ON {day_on.min():+.2f}%  "
          f"({100*(day_on.min()-day_off.min())/abs(day_off.min()):+.0f}%)")
    # vol-spike replay: highest-NATR-decile entry candles
    natr_fi = natr[fi]
    hi_vol = natr_fi >= np.quantile(natr_fi[np.isfinite(natr_fi)], 0.90)
    print(f"\n  VOL-SPIKE replay (top-10% NATR entry candles, n={int(hi_vol.sum())}):")
    print(f"    OFF: net {rets[hi_vol].sum():+.1f}  WR {(rets[hi_vol]>0).mean():.3f}  "
          f"avg brake scale (ON) {scales[hi_vol].mean():.3f}")
    print(f"    ON : net {rw_r2_full[hi_vol].sum():+.1f}  "
          f"(brake de-levers the vol-spike trades to avg {scales[hi_vol].mean():.2f}x)")

    # full-config seed-robust summary one-liner
    print("\n" + "=" * 100)
    print("SUMMARY — chosen primary risk config = R2 drawdown brake (trg=20 anc=80 flr=0.2)")
    print(f"  IS pooled Sharpe {base_s:+.3f} -> {pooled_ann_sharpe(rw_r2_full,n_is):+.3f}  "
          f"(Δ {pooled_ann_sharpe(rw_r2_full,n_is)-base_s:+.3f})")
    print(f"  IS maxDD {base_dd:.0f} -> {proxy_maxdd(rw_r2_full):.0f} "
          f"({100*(proxy_maxdd(rw_r2_full)-base_dd)/base_dd:+.0f}%)")
    print(f"  FEE accounting: per-trade fee {FEE_PCT}% already netted in letrun.")
    print("=" * 100)
    print(f"\nWrote sl_multiple_sweep.csv, combo.csv, slippage_stress.csv to {OUTDIR}")


if __name__ == "__main__":
    main()
