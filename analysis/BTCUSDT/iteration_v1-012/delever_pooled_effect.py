"""IS-ONLY: the CORRECT metric for a de-lever sizing primitive — POOLED Sharpe + loss/DD contribution.

KEY INSIGHT (from trend_scaled_sizing.py result): per-sub-period Sharpe is the WRONG target for a
SIZING primitive. Sharpe is INVARIANT to a constant size multiplier within a window, so scaling a
bear sub-period uniformly cannot change its own Sharpe. Where the multiplier VARIES within a bear
window it can even lower that window's Sharpe by chance. What de-levering a bear regime ACTUALLY
does — and what the Sharpe objective rewards — is reduce that regime's CONTRIBUTION to the POOLED
return distribution: fewer/smaller losing trades when the trend is down => lower pooled variance,
higher pooled mean/std => higher POOLED (overall) Sharpe, and a smaller absolute-loss / drawdown
footprint from the bear sub-periods.

This script measures, IS-ONLY, on the let-run LONG book (and the full book) the metrics a de-lever
primitive is supposed to move:
  (1) POOLED annualized Sharpe of the (size-weighted) per-trade returns, OFF vs ON.
  (2) Loss contribution: sum of the NEGATIVE weighted returns from the 3 bear sub-periods, OFF vs ON
      (the de-lever thesis: this should shrink substantially).
  (3) Bull-regime preservation: sum of POSITIVE weighted returns from the 6 bull sub-periods, OFF vs
      ON (should be largely retained).
  (4) Worst single-trade and a proxy max-drawdown (running sum of weighted returns) OFF vs ON.
  (5) A FLOOR sweep (0.0..1.0) to show the Sharpe/DD tradeoff curve and locate the IS-best floor.

Uses the SAME stateless past-only trend z-score and smooth multiplier as trend_scaled_sizing.py.
The primitive is LONG-BIAS: it scales LONG trades only; SHORT trades keep size 1.0 (shorts are flat,
not the risk source). Slope_lb / z-band fixed at the trend_scaled_sizing chosen transition; the
FLOOR is the single load-bearing knob and is the focus of the IS sweep.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; expanding WF respects an embargo >= label horizon; trend vars stateless past-only.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-012/delever_pooled_effect.py
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
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-012"
SEEDS = (42, 123, 456, 789, 1001)

# Fixed transition band (from trend_scaled_sizing grid: slope_lb=20, z_lo=-0.5, z_hi=0.0).
SLOPE_LB = 20
Z_LO = -0.5
Z_HI = 0.0

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


def letrun(high, low, close, atr, direction, atr_sl, timeout_c):
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
        out[i] = raw - FEE_PCT
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


def pooled_ann_sharpe(r_weighted, n_total, min_n=12):
    rr = r_weighted[np.isfinite(r_weighted)]
    if len(rr) < min_n:
        return np.nan
    mean, std = float(np.mean(rr)), float(np.std(rr, ddof=1))
    if std <= 0:
        return np.nan
    return (mean / std) * np.sqrt(len(rr) / n_total * CANDLES_PER_YEAR)


def trend_zscore(close, slope_lb):
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    sma200_lag = sma200.shift(slope_lb)
    slope = (sma200 - sma200_lag) / sma200_lag
    slope_std = slope.rolling(STD_LB).std().shift(1)
    return (slope / slope_std).to_numpy(float)


def size_multiplier(z, floor, z_lo=Z_LO, z_hi=Z_HI):
    m = np.full(len(z), 1.0)
    fin = np.isfinite(z)
    frac = np.clip((z[fin] - z_lo) / max(z_hi - z_lo, 1e-9), 0.0, 1.0)
    m[fin] = floor + (1.0 - floor) * frac
    return m


def proxy_maxdd(weighted_returns_ordered):
    """Running-sum equity max drawdown (in cumulative pct points) of an ordered weighted-return
    sequence. Additive book (no compounding), matching the backtest weighted_pnl accounting."""
    eq = np.cumsum(weighted_returns_ordered)
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    return float(np.max(dd)) if len(dd) else 0.0


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
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

    d42, oof42 = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb42 = letrun(high, low, close, atr, d42, ATR_SL, N_LABEL)
    long_mask = oof42 & (d42 > 0) & np.isfinite(mb42)
    full_mask = oof42 & np.isfinite(mb42)

    z = trend_zscore(close, SLOPE_LB)

    def is_bear_sub(ts_days):
        d = pd.to_datetime(ts_days * 86400_000, unit="ms")
        ym = d.strftime("%Y-%m")
        return ym in ("2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06",
                      "2022-07", "2022-08", "2022-09", "2022-10", "2022-11", "2022-12",
                      "2025-01", "2025-02", "2025-03")

    bear_flag = np.array([is_bear_sub(t) for t in ot_days])

    # ============ FLOOR SWEEP (IS-only): pooled Sharpe + DD + loss contribution ============
    print("\n" + "=" * 100)
    print("FLOOR SWEEP (IS-only) — POOLED metrics on the let-run LONG book (LONG-bias multiplier)")
    print(f"  fixed band slope_lb={SLOPE_LB} z_lo={Z_LO} z_hi={Z_HI}; FLOOR is the key knob")
    print("=" * 100)

    # ordering index for the proxy-DD (chronological, OOF long trades).
    long_idx = np.where(long_mask)[0]
    full_idx = np.where(full_mask)[0]

    rows = []
    for floor in (1.00, 0.50, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.00):
        w = size_multiplier(z, floor)
        # LONG book.
        wlong = mb42[long_mask] * w[long_mask]
        s_long = pooled_ann_sharpe(wlong, n_is)
        dd_long = proxy_maxdd(mb42[long_idx] * w[long_idx])
        # FULL book — multiplier on longs only; shorts size 1.0.
        wfull_vec = np.where(d42 > 0, w, 1.0)
        wfull = mb42[full_mask] * wfull_vec[full_mask]
        s_full = pooled_ann_sharpe(wfull, n_is)
        dd_full = proxy_maxdd(mb42[full_idx] * wfull_vec[full_idx])
        # Loss contribution from BEAR sub-periods (long book).
        bear_long = long_mask & bear_flag
        bull_long = long_mask & (~bear_flag)
        bear_w = mb42[bear_long] * w[bear_long]
        bull_w = mb42[bull_long] * w[bull_long]
        bear_loss = float(np.sum(bear_w[bear_w < 0]))  # negative sum
        bull_gain = float(np.sum(bull_w[bull_w > 0]))  # positive sum
        bear_net = float(np.sum(bear_w))
        worst_trade = float(np.min(mb42[long_idx] * w[long_idx]))
        rows.append(dict(
            floor=floor,
            long_pooled_sharpe=round(s_long, 3),
            full_pooled_sharpe=round(s_full, 3),
            long_proxy_maxDD=round(dd_long, 1),
            full_proxy_maxDD=round(dd_full, 1),
            bear_loss_sum=round(bear_loss, 1),
            bull_gain_sum=round(bull_gain, 1),
            bear_net=round(bear_net, 1),
            worst_long_trade=round(worst_trade, 2),
            avg_mult_long=round(float(np.mean(w[long_mask])), 3),
        ))
    sweep = pd.DataFrame(rows)
    sweep.to_csv(OUTDIR / "floor_sweep.csv", index=False)
    print(sweep.to_string(index=False))

    base = sweep[sweep.floor == 1.00].iloc[0]
    print("\n  Reads (vs FLOOR=1.0 baseline = no de-lever):")
    for _, r in sweep.iterrows():
        if r.floor == 1.00:
            continue
        print(f"    floor={r.floor:.2f}: LONG Sharpe {base.long_pooled_sharpe:+.3f}->"
              f"{r.long_pooled_sharpe:+.3f} "
              f"(Δ{r.long_pooled_sharpe-base.long_pooled_sharpe:+.3f}) | "
              f"LONG maxDD {base.long_proxy_maxDD:.0f}->{r.long_proxy_maxDD:.0f} "
              f"({100*(r.long_proxy_maxDD-base.long_proxy_maxDD)/base.long_proxy_maxDD:+.0f}%) | "
              f"bear_loss {base.bear_loss_sum:.0f}->{r.bear_loss_sum:.0f} | "
              f"bull_gain {base.bull_gain_sum:.0f}->{r.bull_gain_sum:.0f}")

    # ============ SEED ROBUSTNESS of the pooled-Sharpe lift at the chosen floor ============
    CHOSEN_FLOOR = 0.25
    print("\n" + "=" * 100)
    print(f"SEED ROBUSTNESS — POOLED LONG Sharpe OFF vs ON (floor={CHOSEN_FLOOR}) across 5 seeds")
    print("=" * 100)
    w_chosen = size_multiplier(z, CHOSEN_FLOOR)
    rows2 = []
    for seed in SEEDS:
        d, oof = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, seed)
        mb = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
        lm = oof & (d > 0) & np.isfinite(mb)
        fm = oof & np.isfinite(mb)
        s_off = pooled_ann_sharpe(mb[lm], n_is)
        s_on = pooled_ann_sharpe(mb[lm] * w_chosen[lm], n_is)
        wf = np.where(d > 0, w_chosen, 1.0)
        sf_off = pooled_ann_sharpe(mb[fm], n_is)
        sf_on = pooled_ann_sharpe(mb[fm] * wf[fm], n_is)
        li = np.where(lm)[0]
        dd_off = proxy_maxdd(mb[li])
        dd_on = proxy_maxdd(mb[li] * w_chosen[li])
        rows2.append(dict(
            seed=seed,
            long_sharpe_OFF=round(s_off, 3), long_sharpe_ON=round(s_on, 3),
            long_delta=round(s_on - s_off, 3),
            full_sharpe_OFF=round(sf_off, 3), full_sharpe_ON=round(sf_on, 3),
            full_delta=round(sf_on - sf_off, 3),
            long_maxDD_OFF=round(dd_off, 1), long_maxDD_ON=round(dd_on, 1),
            maxDD_reduction_pct=round(100 * (dd_on - dd_off) / dd_off, 1),
        ))
    seed_df = pd.DataFrame(rows2)
    seed_df.to_csv(OUTDIR / "seed_robustness_floor25.csv", index=False)
    print(seed_df.to_string(index=False))
    print(f"\n  long Sharpe Δ: mean {seed_df.long_delta.mean():+.3f}  "
          f"min {seed_df.long_delta.min():+.3f}  max {seed_df.long_delta.max():+.3f}  "
          f"(all positive: {bool((seed_df.long_delta > 0).all())})")
    print(f"  full Sharpe Δ: mean {seed_df.full_delta.mean():+.3f}  "
          f"min {seed_df.full_delta.min():+.3f}  max {seed_df.full_delta.max():+.3f}  "
          f"(all positive: {bool((seed_df.full_delta > 0).all())})")
    print(f"  maxDD reduction: mean {seed_df.maxDD_reduction_pct.mean():+.1f}%  "
          f"(all reduce: {bool((seed_df.maxDD_reduction_pct < 0).all())})")

    print(f"\nWrote: {OUTDIR/'floor_sweep.csv'}, {OUTDIR/'seed_robustness_floor25.csv'}")


if __name__ == "__main__":
    main()
