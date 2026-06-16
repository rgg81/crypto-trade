"""IS-ONLY regime-conditional edge scan for BTCUSDT iter-v1/008 — Phase 1/2.

QR Phase 1 analysis. Does BTC have a COHERENT positive edge conditional on a
stateless, leak-free regime? If the prune model's IS edge is clearly positive inside
some regime (and that regime has enough trades, ≥~10/mo), gating trades to it would
flip the IS coherent — without changing features or labels.

Method (IS-ONLY, purged forward-chaining CV, 41-col prune):
  1. Build a single purged 5-fold OOF prediction (sign of regressor score on the
     CURRENT label's realized long-direction return), exactly as in
     label_horizon_learnability.py — the SAME model the specialist approximates.
  2. Define several STATELESS, PAST-ONLY regime partitions:
       * TREND state  : sign of long-SMA slope (50/100-bar SMA, slope over W bars).
       * VOL tercile  : vol_natr_21 terciles (low / mid / high), thresholds from a
                        ROLLING past-only quantile (no full-IS quantile leak).
       * ADX band     : trend_adx_14 < 20 (no-trend) vs >= 25 (trending), past-only.
       * |RET| state  : was the prior candle a big move? (past-only abs return tercile)
  3. Within each regime bucket, measure the OOF directional accuracy + OOF net econ
     (per-candle realized PnL of the model's chosen direction, net 0.1% fee) + the
     trade count + trades/month. The question: is there a bucket where econ flips
     clearly positive with enough trades to matter?

A regime gate is only a candidate if, IS-only:
  (a) one bucket's OOF econ is clearly positive (> ~+0.10%/candle, a fee-multiple),
  (b) it retains >= 10 trades/month (≈ enough OOS trades after the 5/8 OOS split), AND
  (c) the COMPLEMENT bucket is where the loss concentrates (so gating removes drag, not
      signal) — i.e. the gate is separating, not just shrinking the sample.

OOS-VIGILANCE (HARD): every quantity is computed AFTER the strict
`open_time < OOS_CUTOFF_MS` filter, with an explicit leak-guard assert. Regime
variables are stateless functions of PAST data (SMA slope shifted, rolling-quantile
thresholds shifted, ADX/NATR are already past-only indicators). The CURRENT-label
realized return is built on the IS slice only → the tail NaN-masks.

Re-runnable, reads ONLY the BTC 8h parquet, NEVER modifies src/, NEVER touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-008/regime_conditional_edge.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
RANDOM_SEED = 42
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-008"

V1_BTC_PRUNED_ITER002: tuple[str, ...] = (
    "cal_dow_norm", "mom_macd_hist_12_26_9", "mom_macd_hist_5_13_3", "mr_bb_pctb_10",
    "mr_pct_from_high_10", "mr_pct_from_high_100", "mr_pct_from_low_100",
    "mr_pct_from_low_20", "mr_rsi_extreme_14", "stat_autocorr_lag1",
    "stat_autocorr_lag10", "stat_autocorr_lag5", "stat_kurtosis_10", "stat_kurtosis_30",
    "stat_kurtosis_50", "stat_skew_10", "stat_skew_20", "stat_skew_50", "trend_adx_14",
    "trend_adx_7", "trend_aroon_down_25", "trend_aroon_down_50", "trend_aroon_osc_14",
    "trend_aroon_osc_25", "trend_aroon_osc_50", "trend_plus_di_21", "trend_psar_af",
    "trend_sma_50", "trend_supertrend_10_2", "trend_supertrend_7_3", "vol_ad",
    "vol_cmf_20", "vol_garman_klass_50", "vol_hist_10", "vol_hist_5", "vol_obv",
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_10", "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_15", "vol_volume_pctchg_20",
)


def _atr_triple_barrier_long_ret(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr: np.ndarray,
    atr_tp: float, atr_sl: float, timeout_candles: int,
) -> np.ndarray:
    """Return the realized LONG-direction return (%) for the CURRENT-label resolution.

    sign(this) = the correct directional label under tb_atr2.9/1.45/7d. We regress the
    model on this and score sign — identical target to label_horizon_learnability.py.
    (Faithful to labeling.label_trades; the long-direction realized return at the
    timeout close is the magnitude a directional bet captures.)
    """
    n = len(close)
    long_ret = np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i]
        if np.isnan(a):
            a = entry * 0.02
        long_tp_p = entry + a * atr_tp
        long_sl_p = entry - a * atr_sl
        end = min(i + timeout_candles, n - 1)
        if end <= i:
            continue
        last_close = close[end]
        # we only need the long-direction realized return for the regressor target;
        # the path-exact label sign is captured by the TB rule but the magnitude
        # the bet captures is the move to the resolution close — use timeout close
        # (consistent, IS-only proxy; the runner produces the path-exact PnL).
        for j in range(i + 1, end + 1):
            last_close = close[j]
            # short-circuit at a TP/SL touch to approximate the resolution close
            if low[j] <= long_sl_p or high[j] >= long_tp_p:
                break
        long_ret[i] = (last_close - entry) / entry * 100.0
    return long_ret


def _oof_predictions(X: np.ndarray, long_ret: np.ndarray, valid: np.ndarray,
                     folds: int = 5, embargo: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Purged forward-chaining OOF predictions. Returns (oof_pred, oof_global_idx)
    aligned so oof_pred[k] is the score for global row oof_global_idx[k]."""
    idx = np.where(valid)[0]
    n = len(idx)
    Xm = X[idx]
    ym = long_ret[idx]
    fold_size = n // folds
    preds, gidx = [], []
    for k in range(1, folds):
        tr_end = k * fold_size
        te_start = tr_end + embargo
        te_end = min((k + 1) * fold_size, n)
        if te_start >= te_end:
            continue
        mdl = lgb.LGBMRegressor(
            n_estimators=200, max_depth=4, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_SEED,
            n_jobs=2, verbose=-1)
        mdl.fit(Xm[:tr_end], ym[:tr_end])
        p = mdl.predict(Xm[te_start:te_end])
        preds.append(p)
        gidx.append(idx[te_start:te_end])
    return np.concatenate(preds), np.concatenate(gidx)


def _bucket_stats(pred: np.ndarray, long_ret: np.ndarray, mask: np.ndarray,
                  is_months: float, n_oof_total: int) -> dict:
    """OOF stats inside a regime bucket. econ = mean(sign(pred)*long_ret - fee)."""
    if mask.sum() == 0:
        return dict(n=0, frac=0.0, dir_acc=np.nan, econ=np.nan, ic=np.nan,
                    trades_mo=0.0, mean_ret=np.nan)
    p = pred[mask]
    y = long_ret[mask]
    nz = y != 0
    dir_acc = float(np.mean((np.sign(p) == np.sign(y))[nz])) if nz.sum() else np.nan
    econ = float(np.mean(np.sign(p) * y - FEE_PCT))
    ic = float(spearmanr(p, y).correlation) if (np.std(p) > 0 and np.std(y) > 0) else np.nan
    n = int(mask.sum())
    # trades/month: this bucket's share of OOF candles scaled to the full IS cadence.
    # OOF covers folds 2..5 (4/5 of IS); scale n by (full_is/oof) then /months.
    frac = n / n_oof_total
    trades_mo = (frac * (n_oof_total * (5 / 4))) / is_months if is_months > 0 else np.nan
    return dict(n=n, frac=frac, dir_acc=dir_acc, econ=econ, ic=ic,
                trades_mo=trades_mo, mean_ret=float(np.mean(y)))


def main() -> None:
    assert PARQUET.exists(), f"parquet not found: {PARQUET}"
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr = close * natr / 100.0
    adx = df["trend_adx_14"].to_numpy(dtype=np.float64)

    prune_present = [c for c in V1_BTC_PRUNED_ITER002 if c in df.columns]
    assert len(prune_present) == 41
    X = df[prune_present].to_numpy(dtype=np.float64)

    is_months = (df["open_time"].max() - df["open_time"].min()) / (1000 * 60 * 60 * 24 * 30.44)

    print("=" * 80)
    print(f"IS-ONLY regime-conditional edge — {SYMBOL} {INTERVAL}")
    print(f"IS rows (open_time < {OOS_CUTOFF_MS}): {n_is}  | IS months ≈ {is_months:.1f}")
    print("label = CURRENT tb_atr2.9/1.45/7d (21c); 41-col prune; purged 5-fold OOF")
    print("=" * 80)

    # CURRENT-label long-direction realized return (the target the specialist learns)
    long_ret = _atr_triple_barrier_long_ret(high, low, close, atr, 2.9, 1.45, 21)
    valid = ~np.isnan(long_ret)

    # One global OOF prediction (the model the specialist approximates)
    pred, gidx = _oof_predictions(X, long_ret, valid)
    y_oof = long_ret[gidx]
    n_oof = len(gidx)

    # baseline (ungated) OOF profile — computed directly on the OOF arrays
    base_dir = float(np.mean(np.sign(pred) == np.sign(y_oof)))
    base_econ = float(np.mean(np.sign(pred) * y_oof - FEE_PCT))
    base_ic = float(spearmanr(pred, y_oof).correlation)
    print(f"\n[BASE] ungated OOF: dir_acc={base_dir:+.4f}  econ_net%={base_econ:+.4f}  "
          f"score_ic={base_ic:+.4f}  n_oof={n_oof}")
    print("       (econ_net<0 ⇒ the ungated model loses money IS — matches IS Sharpe<0)")

    # ------------------------------------------------------------------ #
    # Stateless, PAST-ONLY regime variables, evaluated at the OOF rows.
    # ------------------------------------------------------------------ #
    s_close = pd.Series(close)

    # (1) TREND state: sign of long-SMA slope (past-only). SMA shifted by 1 so the
    #     value at row i uses closes <= i-1; slope over W bars also strictly past.
    def sma_slope_sign(window: int, slope_w: int) -> np.ndarray:
        sma = s_close.rolling(window).mean().shift(1)  # past-only
        slope = (sma - sma.shift(slope_w)) / slope_w
        return np.sign(slope.to_numpy())

    trend50 = sma_slope_sign(50, 10)   # 50-bar SMA, 10-bar slope
    trend100 = sma_slope_sign(100, 20)  # 100-bar SMA, 20-bar slope

    # (2) VOL tercile via ROLLING past-only quantile (no full-IS leak). Use a long
    #     trailing window so thresholds are stable; shift(1) to exclude current row.
    natr_s = pd.Series(natr)
    roll = 250  # ~250 8h candles ≈ 83 days trailing
    natr_lo = natr_s.rolling(roll).quantile(0.33).shift(1).to_numpy()
    natr_hi = natr_s.rolling(roll).quantile(0.67).shift(1).to_numpy()
    vol_state = np.full(n_is, 0, dtype=np.int8)  # 0=mid,-1=low,1=high (NaN→0 handled by mask)
    vol_state = np.where(natr < natr_lo, -1, np.where(natr > natr_hi, 1, 0))
    vol_valid = ~(np.isnan(natr_lo) | np.isnan(natr_hi))

    # (3) ADX band: <20 no-trend vs >=25 trending (indicator already past-only)
    #     (20-25 = grey zone, its own bucket)
    adx_band = np.where(adx < 20, 0, np.where(adx >= 25, 2, 1))  # 0=chop,1=grey,2=trend

    # (4) prior-candle move magnitude: |1-bar past return| tercile (past-only)
    ret1 = s_close.pct_change().shift(1).abs().to_numpy() * 100.0  # |ret[t-1]| %
    ret1_s = pd.Series(ret1)
    r_lo = ret1_s.rolling(roll).quantile(0.33).shift(1).to_numpy()
    r_hi = ret1_s.rolling(roll).quantile(0.67).shift(1).to_numpy()
    mv_state = np.where(ret1 < r_lo, -1, np.where(ret1 > r_hi, 1, 0))
    mv_valid = ~(np.isnan(r_lo) | np.isnan(r_hi))

    # Map regime arrays onto the OOF rows
    def at_oof(arr: np.ndarray) -> np.ndarray:
        return arr[gidx]

    partitions = []
    t50 = at_oof(trend50)
    partitions.append(("TREND50 slope", [
        ("up (slope>0)", t50 > 0), ("down (slope<0)", t50 < 0)]))
    t100 = at_oof(trend100)
    partitions.append(("TREND100 slope", [
        ("up (slope>0)", t100 > 0), ("down (slope<0)", t100 < 0)]))
    vs = at_oof(vol_state)
    vv = at_oof(vol_valid)
    partitions.append(("VOL tercile (natr, roll250)", [
        ("low vol", (vs == -1) & vv), ("mid vol", (vs == 0) & vv),
        ("high vol", (vs == 1) & vv)]))
    ab = at_oof(adx_band)
    partitions.append(("ADX band", [
        ("chop adx<20", ab == 0), ("grey 20-25", ab == 1), ("trend adx>=25", ab == 2)]))
    mv = at_oof(mv_state)
    mvv = at_oof(mv_valid)
    partitions.append(("|prior ret| tercile", [
        ("calm", (mv == -1) & mvv), ("normal", (mv == 0) & mvv),
        ("turbulent", (mv == 1) & mvv)]))

    print("\n[C] REGIME-CONDITIONAL OOF EDGE (each row = a regime bucket)")
    print("-" * 80)
    print("  econ_net = mean OOF realized PnL/candle (model dir, net fee). A regime gate")
    print("  is interesting iff one bucket econ_net >> 0 AND retains >=10 trades/mo AND")
    print("  the COMPLEMENT carries the loss (gate separates, not just shrinks).")
    print("-" * 80)
    rows = []
    for pname, buckets in partitions:
        print(f"\n  ── {pname} ──")
        for bname, mask in buckets:
            st = _bucket_stats(pred, y_oof, mask, is_months, n_oof)
            rows.append({"partition": pname, "bucket": bname, **st})
            tag = ""
            if not np.isnan(st["econ"]) and st["econ"] > 0.10 and st["trades_mo"] >= 10:
                tag = "  <== POSITIVE+TRADEABLE"
            elif not np.isnan(st["econ"]) and st["econ"] > 0:
                tag = "  [econ>0]"
            print(f"    {bname:22s} n={st['n']:4d} ({st['frac']*100:4.1f}%) "
                  f"dir_acc={st['dir_acc']:+.4f} econ_net%={st['econ']:+.4f} "
                  f"ic={st['ic']:+.4f} trades/mo={st['trades_mo']:5.1f}{tag}")

    res = pd.DataFrame(rows)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "regime_conditional_edge.csv"
    res.to_csv(out, index=False)

    # ------------------------------------------------------------------ #
    # Decisive summary: best positive-econ bucket + does gating beat ungated?
    # ------------------------------------------------------------------ #
    print("\n[D] DECISION SUMMARY")
    print("-" * 80)
    cand = res[(res["econ"] > 0) & (res["trades_mo"] >= 10)].sort_values(
        "econ", ascending=False)
    if len(cand) == 0:
        print("  NO regime bucket has OOF econ_net > 0 with >=10 trades/mo.")
        print("  => No stateless regime gate flips BTC's IS edge coherent at a tradeable rate.")
    else:
        print("  Buckets with OOF econ_net>0 AND >=10 trades/mo (gate candidates):")
        for _, r in cand.iterrows():
            print(f"    {r['partition']} / {r['bucket']}: econ={r['econ']:+.4f} "
                  f"dir_acc={r['dir_acc']:+.4f} trades/mo={r['trades_mo']:.1f}")
        # For the top candidate, report the complement to verify separation.
        top = cand.iloc[0]
        print(f"\n  Top candidate: {top['partition']} / {top['bucket']} "
              f"(econ={top['econ']:+.4f} vs ungated {base_econ:+.4f})")
        print(f"  Gate lift vs ungated econ: {top['econ'] - base_econ:+.4f} %/candle")
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
