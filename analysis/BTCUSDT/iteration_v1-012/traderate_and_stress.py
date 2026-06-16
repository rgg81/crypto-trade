"""IS-ONLY trade-rate + stress confirmation for the trend-scaled de-lever primitive — iter-v1/012.

Confirms three things the SPEC needs, IS-ONLY:
  (A) TRADE-COUNT INVARIANCE: the primitive scales SIZE, not trade count. The long-book and full-book
      trade counts are IDENTICAL with and without the multiplier (it never gates an entry). Reports
      IS trades/month for the full book (must be >> the >=10/mo floor; OOS trade-rate is the same
      mechanism — entries are unchanged, so the OOS >= 10/mo floor holds by construction since
      iter-010 ran ~73/mo full / ~40/mo long IS and ~6/mo... -> we report the IS rate and the
      mechanism guarantees OOS count == ungated count).
  (B) MULTIPLIER DISTRIBUTION BY REGIME: the avg multiplier on BEAR-regime long trades is far below
      the avg on BULL-regime long trades (the primitive really de-levers the bear, not random
      candles) — using the iter-011 200-SMA-slope-sign regime label as an independent cross-check.
  (C) SLIPPAGE COST-STRESS: pooled LONG + FULL Sharpe OFF vs ON at slippage {0, 2, 4} bps/side
      (round-trip 2x), to pre-register the cost assumption the merge is judged at and show the
      de-lever lift survives a 2x and 4x cost shock. Slippage applied as an extra round-trip drag on
      every trade's pct return BEFORE size weighting (matches backtest: 2*slippage_bps_per_side).

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert; expanding WF
embargo >= horizon; trend vars stateless past-only. No OOS row read.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-012/traderate_and_stress.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
ATR_SL = 1.45
N_LABEL = 9
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3
STD_LB = 250
SLOPE_LB = 20
Z_LO = -0.5
Z_HI = 0.0
FLOOR = 0.25
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-012"

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)
BASE_PARAMS = dict(
    n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03,
    min_child_samples=80, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.5, reg_lambda=0.5, n_jobs=4, verbose=-1,
)


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c, extra_drag_pct=0.0):
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n):
        d = direction[i]
        if not np.isfinite(d) or d == 0 or close[i] == 0:
            continue
        entry = close[i]
        a = atr[i] if np.isfinite(atr[i]) else entry * 0.02
        end = min(i + timeout_c, n - 1)
        if end <= i:
            continue
        if d > 0:
            sl = entry - a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if low[j] <= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (ex - entry) / entry * 100.0
        else:
            sl = entry + a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if high[j] >= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (entry - ex) / entry * 100.0
        out[i] = raw - FEE_PCT - extra_drag_pct
    return out


def expanding_wf(X, y, ot_days, valid, params, seed, min_train_days=365.0, step_days=30.0):
    n = len(X)
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    t0 = ot_days.min()
    ts = t0 + min_train_days + embargo_days
    preds, idx = [], []
    while ts < ot_days.max():
        te = ts + step_days
        tc = ts - embargo_days
        tr = valid & (ot_days < tc) & (ot_days >= t0)
        tem = valid & (ot_days >= ts) & (ot_days < te)
        if tr.sum() >= 200 and tem.sum() > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[tr], y[tr])
            preds.append(m.predict(X[tem]))
            idx.append(np.where(tem)[0])
        ts = te
    if not idx:
        return np.zeros(n), np.zeros(n, dtype=bool)
    p = np.concatenate(preds)
    g = np.concatenate(idx)
    d = np.zeros(n)
    d[g] = np.sign(p)
    oof = np.zeros(n, dtype=bool)
    oof[g] = True
    return d, oof


def pooled_ann_sharpe(rw, n_total, min_n=12):
    rr = rw[np.isfinite(rw)]
    if len(rr) < min_n:
        return np.nan
    mean, std = float(np.mean(rr)), float(np.std(rr, ddof=1))
    if std <= 0:
        return np.nan
    return (mean / std) * np.sqrt(len(rr) / n_total * CANDLES_PER_YEAR)


def trend_zscore(close, slope_lb):
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    slope = (sma200 - sma200.shift(slope_lb)) / sma200.shift(slope_lb)
    return (slope / slope.rolling(STD_LB).std().shift(1)).to_numpy(float)


def size_multiplier(z, floor, z_lo=Z_LO, z_hi=Z_HI):
    m = np.full(len(z), 1.0)
    fin = np.isfinite(z)
    frac = np.clip((z[fin] - z_lo) / max(z_hi - z_lo, 1e-9), 0.0, 1.0)
    m[fin] = floor + (1.0 - floor) * frac
    return m


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)
    is_years = (df["open_time"].max() - df["open_time"].min()) / 86400_000.0 / 365.25
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

    d42, oof42 = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb = letrun(high, low, close, atr, d42, ATR_SL, N_LABEL)
    long_mask = oof42 & (d42 > 0) & np.isfinite(mb)
    full_mask = oof42 & np.isfinite(mb)
    z = trend_zscore(close, SLOPE_LB)
    w = size_multiplier(z, FLOOR)

    # ---- (A) TRADE-COUNT INVARIANCE + trade-rate ----
    print("=" * 100)
    print("(A) TRADE-COUNT INVARIANCE + IS trade-rate")
    print("=" * 100)
    n_long = int(long_mask.sum())
    n_full = int(full_mask.sum())
    # the multiplier never zeroes a trade (floor>0), so count is identical ON vs OFF.
    months = is_years * 12.0
    print(f"  IS span ~{is_years:.2f} yr ({months:.1f} months)")
    print(f"  FULL book trades: {n_full}  -> {n_full/months:.1f}/mo  (floor=10/mo: "
          f"{'PASS' if n_full/months >= 10 else 'FAIL'})")
    print(f"  LONG book trades: {n_long}  -> {n_long/months:.1f}/mo")
    print(f"  min multiplier across all long trades: {float(np.min(w[long_mask])):.3f} (> 0)")
    print("       -> no trade is gated off; trade COUNT is identical ON vs OFF by construction")

    # ---- (B) MULTIPLIER DISTRIBUTION BY INDEPENDENT REGIME LABEL ----
    print("\n" + "=" * 100)
    print("(B) MULTIPLIER vs INDEPENDENT 200-SMA-slope-sign regime (iter-011) — de-levers BEAR?")
    print("=" * 100)
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    bull = ((sma200 - sma200.shift(20)) > 0).to_numpy()
    lb = long_mask & bull
    lr = long_mask & (~bull)
    print(f"  BULL-regime long trades: n={int(lb.sum())}  avg mult={float(np.mean(w[lb])):.3f}")
    print(f"  BEAR-regime long trades: n={int(lr.sum())}  avg mult={float(np.mean(w[lr])):.3f}")
    print(f"  -> de-lever ratio (bear/bull) = {float(np.mean(w[lr]))/float(np.mean(w[lb])):.2f} "
          "(< 1.0 confirms the primitive concentrates de-levering in the bear regime)")

    # ---- (C) SLIPPAGE COST-STRESS ----
    print("\n" + "=" * 100)
    print("(C) SLIPPAGE COST-STRESS — pooled Sharpe OFF vs ON at slippage {0,2,4} bps/side (2x RT)")
    print("=" * 100)
    rows = []
    for bps in (0.0, 2.0, 4.0):
        drag = 2.0 * bps / 100.0  # round-trip drag in PCT points (bps/100 = pct per side)
        mb_s = letrun(high, low, close, atr, d42, ATR_SL, N_LABEL, extra_drag_pct=drag)
        lm = oof42 & (d42 > 0) & np.isfinite(mb_s)
        fm = oof42 & np.isfinite(mb_s)
        wf = np.where(d42 > 0, w, 1.0)
        long_off = pooled_ann_sharpe(mb_s[lm], n_is)
        long_on = pooled_ann_sharpe(mb_s[lm] * w[lm], n_is)
        full_off = pooled_ann_sharpe(mb_s[fm], n_is)
        full_on = pooled_ann_sharpe(mb_s[fm] * wf[fm], n_is)
        rows.append(dict(
            slippage_bps_per_side=bps,
            roundtrip_drag_pct=round(drag, 3),
            long_sharpe_OFF=round(long_off, 3), long_sharpe_ON=round(long_on, 3),
            long_delta=round(long_on - long_off, 3),
            full_sharpe_OFF=round(full_off, 3), full_sharpe_ON=round(full_on, 3),
            full_delta=round(full_on - full_off, 3),
        ))
    stress = pd.DataFrame(rows)
    stress.to_csv(OUTDIR / "slippage_stress.csv", index=False)
    print(stress.to_string(index=False))
    print("\n  Pre-registered merge cost: slippage_bps_per_side = 2.0 (round-trip 0.04%).")
    print("  The de-lever lift (full_delta) must remain POSITIVE at 2 AND 4 bps/side to pass.")

    print(f"\nWrote: {OUTDIR/'slippage_stress.csv'}")


if __name__ == "__main__":
    main()
