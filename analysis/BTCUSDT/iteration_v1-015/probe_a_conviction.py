"""PROBE A (iter-v1/015, BTCUSDT, IS-ONLY) — conviction-based sizing diagnostic.

HYPOTHESIS (user candidate #1): the model's own prediction MAGNITUDE (|forecast forward-return| =
conviction) separates trades that GENERALIZE from marginal noise. If high-conviction trades have a
MORE STABLE sub-period profile (fewer negative sub-periods, higher win rate, higher pooled Sharpe per
unit drawdown) than the marginal trades, then conviction-weighted sizing could lift OOS robustness
WITHOUT the iter-012 regime mistake (conviction is orthogonal to the 200-SMA regime label).

THE CRITICAL TEST (the iter-012 trap, applied here): is high-conviction simply a proxy for the
overfit IS-BULL longs? If the top-conviction trades are disproportionately the IS-bull longs that
iter-012 showed INVERT OOS, then conviction sizing is the de-lever mistake reborn (it would
UP-weight exactly the trades that don't generalize). I measure conviction's correlation with the
200-SMA bull regime and with the per-trade outcome, sub-period by sub-period.

WHAT THIS PROBE MEASURES (IS-only):
  (1) Conviction-decile table: WR / mean-net / pooled-Sharpe / fraction-of-trades by conviction
      decile of |pred|. Does edge concentrate in high conviction?
  (2) Sub-period sign-stability: how many of the 9 IS sub-periods are NET-POSITIVE for the
      top-conviction quartile vs the full book? (the generalization-robustness proxy)
  (3) Bull-regime contamination check: avg conviction in bull vs bear regime, and the conviction
      x bull-regime correlation — is high conviction just "long in a bull"?
  (4) A conviction-sizing pooled-Sharpe + maxDD sweep (size proportional to conviction percentile,
      with a floor), to see if the SIZING form lifts pooled Sharpe / cuts DD on the let-run book.

OOS-VIGILANCE: IS-only frame (cutoff filter + assert in load_is_frame); past-only signals; the
prediction margin is OOF from the expanding WF (trained strictly on past candles minus embargo).

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-015/probe_a_conviction.py
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
    ITER009_FEATURES,
    N_LABEL,
    OOS_CUTOFF_MS,
    SEEDS,
    SYMBOL,
    expanding_wf_with_margin,
    fwd_return,
    letrun,
    load_is_frame,
    pooled_ann_sharpe,
    proxy_maxdd,
    sub_period_label,
)

PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-015"
ATR_SL = 1.45


def trend_sign_regime(close):
    """iter-011/012 200-SMA-up regime label (past-only): +1 if SMA200_{t-1} rising over 20 candles."""
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    rising = (sma200 - sma200.shift(20)) > 0
    return rising.to_numpy()


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
    assert len(feats) == 19
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)
    subp = sub_period_label(ot_days)
    bull = trend_sign_regime(close)

    # ---- primary seed=42 OOF direction + prediction-margin (conviction) ----
    d, oof, pv = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb, _reason = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
    full = oof & np.isfinite(mb)
    conv = np.abs(pv)  # |forecast| = conviction proxy

    fi = np.where(full)[0]
    fi = fi[np.argsort(ot_days[fi])]  # chronological for DD
    rets = mb[fi]
    cv = conv[fi]
    sp = subp[fi]
    bl = bull[fi]
    dirs = d[fi]

    # ===================== (1) CONVICTION DECILE TABLE =====================
    print("\n" + "=" * 100)
    print("(1) CONVICTION DECILES (|pred|) — full let-run book, seed 42, IS-only")
    print("=" * 100)
    dec = pd.qcut(cv, 10, labels=False, duplicates="drop")
    rows = []
    for q in sorted(pd.unique(dec)):
        m = dec == q
        r = rets[m]
        rows.append(dict(
            decile=int(q), n=int(m.sum()),
            conv_lo=round(float(cv[m].min()), 3), conv_hi=round(float(cv[m].max()), 3),
            WR=round(float((r > 0).mean()), 3),
            mean_net=round(float(r.mean()), 3),
            pooled_sharpe=round(pooled_ann_sharpe(r, n_is), 3),
            frac_long=round(float((dirs[m] > 0).mean()), 3),
            frac_bull=round(float(bl[m].mean()), 3),
        ))
    dec_df = pd.DataFrame(rows)
    dec_df.to_csv(OUTDIR / "conviction_deciles.csv", index=False)
    print(dec_df.to_string(index=False))

    # ===================== (2) SUB-PERIOD SIGN STABILITY: top-quartile vs full =====================
    print("\n" + "=" * 100)
    print("(2) SUB-PERIOD NET SIGN — top-conviction QUARTILE vs FULL book (generalization proxy)")
    print("=" * 100)
    thr = np.quantile(cv, 0.75)
    hi = cv >= thr
    rows2 = []
    for s in sorted(pd.unique(sp)):
        m_full = sp == s
        m_hi = m_full & hi
        rows2.append(dict(
            sub_period=s, n_full=int(m_full.sum()), n_hiconv=int(m_hi.sum()),
            full_net=round(float(rets[m_full].sum()), 2),
            full_WR=round(float((rets[m_full] > 0).mean()), 3),
            hiconv_net=round(float(rets[m_hi].sum()), 2) if m_hi.sum() else float("nan"),
            hiconv_WR=round(float((rets[m_hi] > 0).mean()), 3) if m_hi.sum() else float("nan"),
        ))
    sp_df = pd.DataFrame(rows2)
    sp_df.to_csv(OUTDIR / "conviction_subperiod.csv", index=False)
    print(sp_df.to_string(index=False))
    n_full_pos = int((sp_df.full_net > 0).sum())
    n_hi_pos = int((sp_df.hiconv_net > 0).sum())
    print(f"\n  FULL book: {n_full_pos}/{len(sp_df)} sub-periods net-positive")
    print(f"  TOP-conviction quartile: {n_hi_pos}/{len(sp_df)} sub-periods net-positive")
    print("  (>= full means conviction CONCENTRATES in stable sub-periods; < full means it doesn't)")

    # ===================== (3) BULL-REGIME CONTAMINATION CHECK =====================
    print("\n" + "=" * 100)
    print("(3) IS-BULL CONTAMINATION — is high conviction just 'long-in-a-bull'? (iter-012 trap)")
    print("=" * 100)
    long_m = dirs > 0
    print(f"  avg conviction  LONG vs SHORT       : {cv[long_m].mean():.3f}  vs  {cv[~long_m].mean():.3f}")
    print(f"  avg conviction  BULL vs BEAR regime : {cv[bl].mean():.3f}  vs  {cv[~bl].mean():.3f}")
    # corr of conviction with (a) bull regime, (b) realized per-trade outcome
    corr_bull = float(np.corrcoef(cv, bl.astype(float))[0, 1])
    corr_out = float(np.corrcoef(cv, rets)[0, 1])
    print(f"  corr(conviction, bull_regime)       : {corr_bull:+.3f}")
    print(f"  corr(conviction, realized net)      : {corr_out:+.3f}  "
          "(>0 => conviction predicts outcome IS)")
    # top-quartile conviction long-share in bull vs bear
    hi_long_bull = hi & long_m & bl
    hi_long_bear = hi & long_m & (~bl)
    print(f"  top-quartile LONG trades: {hi_long_bull.sum()} in bull / {hi_long_bear.sum()} in bear "
          f"(bull share {hi_long_bull.sum()/max(hi_long_bull.sum()+hi_long_bear.sum(),1):.2f})")

    # ===================== (4) CONVICTION-SIZING POOLED SWEEP =====================
    print("\n" + "=" * 100)
    print("(4) CONVICTION-SIZING pooled-Sharpe + maxDD sweep (size = floor + (1-floor)*conv_pctile)")
    print("    conv_pctile = within-IS rank of |pred| (past-only-safe: ranked over all IS OOF trades)")
    print("=" * 100)
    # conviction percentile within the OOF book (this is a within-IS rank; for deployment it would be
    # a rolling/expanding rank, but for the IS DIAGNOSTIC the full-IS rank is the right lens).
    pct = pd.Series(cv).rank(pct=True).to_numpy()
    base_s = pooled_ann_sharpe(rets, n_is)
    base_dd = proxy_maxdd(rets)
    print(f"  baseline (size 1.0): pooled Sharpe {base_s:+.3f}  maxDD {base_dd:.1f}")
    rows4 = []
    for floor in (1.00, 0.50, 0.35, 0.25, 0.10):
        w = floor + (1.0 - floor) * pct
        rw = rets * w
        rows4.append(dict(
            floor=floor,
            pooled_sharpe=round(pooled_ann_sharpe(rw, n_is), 3),
            maxDD=round(proxy_maxdd(rw), 1),
            avg_mult=round(float(w.mean()), 3),
        ))
    sw = pd.DataFrame(rows4)
    sw.to_csv(OUTDIR / "conviction_sizing_sweep.csv", index=False)
    print(sw.to_string(index=False))

    # seed robustness of the conviction-decile monotonicity (does top decile beat bottom for all seeds?)
    print("\n" + "=" * 100)
    print("(5) SEED ROBUSTNESS — top-quartile vs bottom-quartile conviction net/WR across 5 seeds")
    print("=" * 100)
    rows5 = []
    for seed in SEEDS:
        ds, oofs, pvs = expanding_wf_with_margin(X, y, ot_days, valid, BASE_PARAMS, seed)
        mbs, _ = letrun(high, low, close, atr, ds, ATR_SL, N_LABEL)
        fm = oofs & np.isfinite(mbs)
        cs = np.abs(pvs)[fm]
        rs = mbs[fm]
        q75 = np.quantile(cs, 0.75)
        q25 = np.quantile(cs, 0.25)
        top = cs >= q75
        bot = cs <= q25
        rows5.append(dict(
            seed=seed,
            top_WR=round(float((rs[top] > 0).mean()), 3),
            top_mean=round(float(rs[top].mean()), 3),
            bot_WR=round(float((rs[bot] > 0).mean()), 3),
            bot_mean=round(float(rs[bot].mean()), 3),
            top_minus_bot_mean=round(float(rs[top].mean() - rs[bot].mean()), 3),
        ))
    sr = pd.DataFrame(rows5)
    sr.to_csv(OUTDIR / "conviction_seed_robust.csv", index=False)
    print(sr.to_string(index=False))
    print(f"\n  top-minus-bottom mean-net: mean {sr.top_minus_bot_mean.mean():+.3f}  "
          f"min {sr.top_minus_bot_mean.min():+.3f}  "
          f"(all positive: {bool((sr.top_minus_bot_mean > 0).all())})")
    print(f"\nWrote conviction_*.csv to {OUTDIR}")


if __name__ == "__main__":
    main()
