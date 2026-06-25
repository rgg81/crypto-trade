"""metals-portfolio iter-006 ML-synthesis DIAGNOSTIC (read-only, IS-only).

NOT the iter-006 implementation — a sizing/feasibility probe for the ML spec. It reifies the
per-sleeve RAW signals as a leak-safe feature panel and reports the numbers the spec's overfit
argument needs to be honest about:
  - n (IS candle count) per metal and effective independent-sample count at 8h autocorrelation,
  - feature-vs-n ratio for the proposed feature set,
  - cross-sleeve feature correlation (collinearity → argues for shallow/monotone, not deep),
  - cross-sectional dispersion of the per-metal forward return (is there cross-sectional shape
    to learn, or is it all one common factor?).

Pure measurement. No model is fit. No OOS is touched. No file is mutated.
"""

from __future__ import annotations

import iter_001_trend as it
import iter_002_mn_overlay as ov
import iter_003_ptpd as i3
import iter_004_cot as i4
import numpy as np
import pandas as pd
from universe_metals import OOS_CUTOFF, VOL_WIN, load_metals, panels

TRADEABLE = ("XAUUSDT", "XAGUSDT", "XPTUSDT", "XPDUSDT")


def sleeve_feature_panels(coins, cot_df):
    """Reconstruct the per-sleeve RAW signal as a per-metal feature (leak-safe, pre-net_from_raw).

    Returns dict[feature_name] -> DataFrame(index=grid, columns=metals). Every value is decided on
    close[t] and would be lagged by the downstream net_from_raw — identical leak surface to the
    existing sleeves. These are exactly the inputs the ML layer would consume.
    """
    pan = panels(coins)
    close = pan["close"]
    rvol = close.pct_change().rolling(VOL_WIN).std()

    feats = {}
    # 1. trend-anchor exposure (long-only, in {floor,1}) -> the trend STATE per metal
    ef = close.ewm(span=it.EMA_FAST, adjust=False).mean()
    es = close.ewm(span=it.EMA_SLOW, adjust=False).mean()
    feats["trend_expo"] = it.FLOOR + (1.0 - it.FLOOR) * (ef > es).astype(float)
    # 2. trend strength (continuous): normalized EMA gap (scale-invariant)
    feats["trend_gap"] = (ef - es) / close
    # 3. dispersion sign per metal: +1 gold leg, -1 industrials (the MN sleeve's signed dir)
    disp = ov.mn_dispersion_raw(close)
    feats["disp_sign"] = np.sign(disp).fillna(0.0)
    # 4. pt/pd ratio z (only nonzero on XPT/XPD; the reversion state)
    lr = np.log(close[i3.PT] / close[i3.PD])
    z_ptpd = ((lr - lr.rolling(i3.Z_WIN).mean()) / lr.rolling(i3.Z_WIN).std()).clip(-2.5, 2.5)
    ptpd = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    ptpd[i3.PT] = z_ptpd
    ptpd[i3.PD] = -z_ptpd
    feats["ptpd_z"] = ptpd
    # 5. COT managed-money net/OI z (the contrarian positioning state), leak-safe aligned
    mm = i4.align_cot_to_grid(cot_df, close.index)
    mm_z = ((mm - mm.rolling(i4.Z_WIN).mean()) / mm.rolling(i4.Z_WIN).std()).clip(-2.5, 2.5)
    feats["cot_mm_z"] = mm_z
    # 6. realized vol state (the sizing context the engine already uses)
    feats["rvol"] = rvol
    # 7. realized-vol regime z (cheap derived state)
    feats["rvol_z"] = (rvol - rvol.rolling(252).mean()) / rvol.rolling(252).std()
    return feats, pan


def main():
    coins = load_metals()
    cot_df = i4.load_cot()
    feats, pan = sleeve_feature_panels(coins, cot_df)
    close = pan["close"]
    ret_fwd = pan["ret_fwd"]
    is_mask = close.index < OOS_CUTOFF

    print("=== iter-006 ML-synthesis DIAGNOSTIC (IS-only) ===\n")

    # ── 1. SAMPLE SIZE per metal (the overfit-budget governor) ──────────────────────────────
    print("[1] IS SAMPLE SIZE per metal (candles with both signal+fwd-ret present)")
    tot_rows = 0
    for m in TRADEABLE:
        valid = (close[m].notna() & ret_fwd[m].notna() & is_mask)
        n = int(valid.sum())
        tot_rows += n
        # effective independent count: 8h candles, forward return is 1-candle so low autocorr;
        # but trend/COT features are slow -> decorrelation time ~ feature half-life. Report a
        # conservative weekly-block effective n (21 candles/week-ish slow-feature block).
        eff_weekly = n / 21
        print(f"  {m:8} n={n:5d} candles   ~{eff_weekly:5.0f} slow-feature (3-wk) blocks")
    print(f"  STACKED panel rows (pooled cross-metal) = {tot_rows}\n")

    # ── 2. FEATURE COUNT vs n ───────────────────────────────────────────────────────────────
    p = len(feats)
    print(f"[2] FEATURE COUNT p={p}  -> stacked rows/feature = {tot_rows / p:.0f}")
    print("    (rule-of-thumb: >50 indep samples/feature for a shallow tree; pooled stack helps)\n")

    # ── 3. CROSS-SLEEVE FEATURE COLLINEARITY (pooled IS, the depth argument) ─────────────────
    print("[3] FEATURE COLLINEARITY (pooled IS Spearman across all metal-rows)")
    long_rows = {}
    for name, df in feats.items():
        s = df.loc[is_mask].stack()
        long_rows[name] = s
    fmat = pd.DataFrame(long_rows).dropna()
    corr = fmat.corr(method="spearman")
    # print the upper triangle compactly
    names = list(corr.columns)
    for i, a in enumerate(names):
        row = "  ".join(f"{corr.loc[a, b]:+.2f}" for b in names[i + 1 :])
        if row:
            print(f"  {a:11}-> {row}")
    print(f"  (pooled feature-matrix rows after dropna = {len(fmat)})\n")

    # ── 4. CROSS-SECTIONAL SHAPE: is there per-metal dispersion to learn? ────────────────────
    print("[4] CROSS-SECTIONAL forward-return dispersion (is there shape, or one common factor?)")
    rf = ret_fwd.loc[is_mask]
    # cross-sectional std of fwd return each bar (when >=2 metals present), and the common-factor
    # share (variance of the cross-sectional MEAN vs total).
    present = rf.notna().sum(axis=1) >= 2
    xs = rf[present]
    xs_mean = xs.mean(axis=1)
    xs_demeaned = xs.sub(xs_mean, axis=0)
    common_var = float(xs_mean.var())
    resid_var = float(xs_demeaned.stack().var())
    share = common_var / (common_var + resid_var)
    med_xs = xs_demeaned.abs().stack().median()
    print(f"  bars with >=2 metals present = {int(present.sum())}")
    print(f"  common-factor variance share = {share:.2f}  (1.0 => pure beta, no XS shape)")
    print(f"  median cross-sectional |demeaned fwd-ret| = {med_xs:.4f}\n")

    # ── 5. SIGNAL PERSISTENCE (turnover argument: how fast does each feature flip?) ──────────
    print("[5] FEATURE PERSISTENCE (mean |Δfeature| per candle, IS — slow=low-turnover-friendly)")
    for name, df in feats.items():
        d = df.loc[is_mask]
        flip = (d - d.shift(1)).abs().stack().mean()
        print(f"  {name:11} mean|Δ/candle| = {flip:.4f}")
    print()

    # ── 6. BASELINE the ML must beat (re-print, IS-only) ────────────────────────────────────
    from universe_metals import LO0, msharpe, turnover

    net4, w4 = i4.build_combined4(coins, cot_df)
    sr = msharpe(net4, LO0, OOS_CUTOFF)
    tnov = turnover(w4, LO0, OOS_CUTOFF)
    print(f"[6] LINEAR BASELINE (bar): 4-sleeve IS Sharpe={sr:+.3f}  turnover/candle={tnov:.4f}")


if __name__ == "__main__":
    main()
