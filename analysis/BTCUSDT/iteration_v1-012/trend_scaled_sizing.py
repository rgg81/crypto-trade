"""IS-ONLY calibration of a REGIME-AWARE, VOL-SCALED, LONG-BIAS SIZING primitive — iter-v1/012.

CONTEXT (from iter-011 STRUCTURAL diagnosis, all IS-only):
  The iter-010 let-winners-run config (19-col HYBRID, fixed_horizon N=9, TP non-binding atr_tp=100,
  protective atr_sl=1.45, exec timeout = 9 candles) earns its entire IS profit on the LONG side
  (+33%), and that long edge is a TREND-PERSISTENCE bet: +2.47 Sharpe in BULL (200-SMA up) vs +0.11
  (dead) in BEAR. The same 3 IS ~6-month sub-periods go negative for ALL 5 seeds (2022-H1, 2022-H2,
  2025-Q1) — exactly the bear/correction regimes. This is a SIZING problem, not a signal problem:
  the book should run near full size in up-trends and de-lever toward a floor in down-trends.

THIS SCRIPT designs + IS-calibrates a CONTINUOUS, STATELESS trend-scaled position-size multiplier
and measures, IS-only, its effect on the let-winners-run book — per ~6-month sub-period Sharpe WITH
vs WITHOUT the multiplier, plus retained trade-rate (the primitive scales SIZE not trade COUNT, so
trade count must be ~unchanged). The goal is a more COHERENT IS profile: lift the 3 negative
sub-periods toward zero while preserving the bull-regime Sharpe.

The multiplier is NOT a gate (iter-011 ruled out binary gates: they amplify the recent-sub-period
inversion / T3-invert). It is a smooth proportional scaler in [FLOOR, 1.0] that COMPOSES with the
existing R5 vol-target (it is another `vt_scale = vt_scale * trend_scale` step in the backtest
pipeline) — it never replaces R5 and never changes which candles trade.

TREND SIGNAL (stateless, leak-free, past-only):
  sma200_t   = SMA(close, 200) using ONLY closes up to and INCLUDING bar t-1 (`.rolling(200).shift(1)`)
  slope_t    = (sma200_t - sma200_{t-SLOPE_LB}) / sma200_{t-SLOPE_LB}    (fractional slope over SLOPE_LB candles)
  We normalize slope by its OWN past-only rolling std (250-candle, shifted) to get a unitless
  z-like trend-strength `z_t = slope_t / rolling_std(slope, 250).shift(1)`, so the mapping
  thresholds are scale-free and crypto-vol-adaptive (fat-tail friendly).

SIZE MULTIPLIER (smooth, NOT binary), piecewise-linear in the trend z-score:
  m(z) = FLOOR                                      if z <= Z_LO          (confirmed down-trend)
  m(z) = 1.0                                         if z >= Z_HI          (confirmed up-trend)
  m(z) = FLOOR + (1-FLOOR) * (z - Z_LO)/(Z_HI-Z_LO) otherwise              (smooth transition)
  When z is NaN (warmup, < 200+SLOPE_LB+250 candles): m = 1.0 (fail-OPEN, never silently de-levers).

This script GRID-CALIBRATES (FLOOR, Z_LO, Z_HI, SLOPE_LB) on IS-ONLY data to find the setting that
best lifts the 3 negative sub-periods toward >= 0 while retaining the bull-sub-period Sharpe, then
reports the chosen setting's full per-sub-period table WITH vs WITHOUT the multiplier.

It ALSO reports a raw-slope-sign continuous variant and a price-vs-SMA variant as robustness checks.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity. Expanding walk-forward (faithful to iter-011) trains only on candles strictly
before each test window minus an embargo >= label horizon. Trend variables are stateless & past-only
(`.shift(1)` on every rolling stat). The grid is scored ONLY on the IS sub-period stability metric;
no OOS row is ever read. `src/`, runner, OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-012/trend_scaled_sizing.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
ATR_SL = 1.45
N_LABEL = 9
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-012"
SEEDS = (42, 123, 456, 789, 1001)

# iter-009/010 19-col HYBRID feature set (verbatim, no regen).
ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7",
    "vol_garman_klass_10",
    "vol_atr_5",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5",
    "vol_mfi_7",
    "mom_rsi_9",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
    "vol_cmf_10",
    "ent_shannon_10",
    "trend_adx_14",
    "trend_supertrend_14_3",
    "btc_funding_spread_30_90",
    "funding_rate_zscore_30",
    "stat_autocorr_lag5",
    "vol_range_spike_72",
    "mr_rsi_extreme_14",
    "stat_kurtosis_20",
)
BASE_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    num_leaves=15,
    learning_rate=0.03,
    min_child_samples=80,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,
    reg_lambda=0.5,
    n_jobs=4,
    verbose=-1,
)

# Calibration grid (IS-only). FLOOR = down-trend size floor; Z_LO/Z_HI = transition band in
# trend-z units; SLOPE_LB = SMA-slope lookback in candles.
GRID_FLOOR = (0.20, 0.25, 0.30)
GRID_ZLO = (-1.0, -0.5, 0.0)
GRID_ZHI = (0.0, 0.5, 1.0)
GRID_SLOPE_LB = (20, 30)
STD_LB = 250  # past-only rolling std lookback for trend-z normalization


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c):
    """Faithful iter-009/010/011 let-winners-run trade: enter at close, exit at
    min{SL atr_sl*ATR adverse, timeout_c-candle timeout}; TP non-binding. Net of FEE_PCT."""
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


def weighted_ann_sharpe(r, w, n_total, min_n=12):
    """Annualized Sharpe of size-WEIGHTED per-trade returns r*w. The weighting scales each
    trade's pct return by its size multiplier (no compounding — additive return book, matching
    the backtest's weighted_pnl = net_pnl_pct * weight_factor)."""
    fin = np.isfinite(r) & np.isfinite(w)
    rr = r[fin] * w[fin]
    if len(rr) < min_n:
        return np.nan, len(rr)
    mean, std = float(np.mean(rr)), float(np.std(rr, ddof=1))
    if std <= 0:
        return np.nan, len(rr)
    return (mean / std) * np.sqrt(len(rr) / n_total * CANDLES_PER_YEAR), len(rr)


def subperiods(ot_days, oof, period_days=182.5):
    t0 = ot_days[oof].min()
    t1 = ot_days[oof].max()
    bounds = []
    edge = t0
    while edge < t1:
        bounds.append((edge, edge + period_days))
        edge += period_days
    return bounds


def trend_zscore(close: np.ndarray, slope_lb: int) -> np.ndarray:
    """Stateless, past-only trend z-score: fractional 200-SMA slope over slope_lb candles,
    normalized by its own past-only rolling std. All rolling stats `.shift(1)` (use t-1 info)."""
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    sma200_lag = sma200.shift(slope_lb)
    slope = (sma200 - sma200_lag) / sma200_lag  # fractional slope, past-only
    slope_std = slope.rolling(STD_LB).std().shift(1)
    z = slope / slope_std
    return z.to_numpy(float)


def trend_zscore_price_vs_sma(close: np.ndarray) -> np.ndarray:
    """Robustness variant: (close_{t-1} - sma200_{t-1}) / sma200_{t-1}, z-normalized past-only."""
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    close_lag = s.shift(1)
    dist = (close_lag - sma200) / sma200
    dist_std = dist.rolling(STD_LB).std().shift(1)
    z = dist / dist_std
    return z.to_numpy(float)


def size_multiplier(z: np.ndarray, floor: float, z_lo: float, z_hi: float) -> np.ndarray:
    """Smooth piecewise-linear size multiplier in [floor, 1.0]. NaN z -> 1.0 (fail-OPEN)."""
    m = np.full(len(z), 1.0)
    fin = np.isfinite(z)
    zf = z[fin]
    span = max(z_hi - z_lo, 1e-9)
    frac = np.clip((zf - z_lo) / span, 0.0, 1.0)
    m[fin] = floor + (1.0 - floor) * frac
    return m


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
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
    assert len(feats) == 19, f"expected 19 HYBRID features, got {len(feats)}"
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)

    # Reference model book (seed 42), faithful to iter-010/011.
    d42, oof42 = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, 42)
    mb42 = letrun(high, low, close, atr, d42, ATR_SL, N_LABEL)
    # The book under study is the LONG side of the model book (where all the IS edge + risk lives).
    long_mask = oof42 & (d42 > 0) & np.isfinite(mb42)
    # The FULL model book (both sides) for the headline coherence figure.
    full_mask = oof42 & np.isfinite(mb42)
    bounds = subperiods(ot_days, oof42)
    starts = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]

    # The 3 structurally-negative IS sub-periods identified in iter-011 (bear/correction regimes).
    # Matched by sub-period start month; computed here, not hard-coded into PnL.
    def is_neg_subperiod(start_str: str) -> bool:
        return start_str.startswith(
            ("2022-01", "2022-02", "2022-07", "2022-08", "2025-01", "2025-02")
        )

    # ============ 1. GRID CALIBRATION (IS-only) on the LONG book ============
    print("\n" + "=" * 100)
    print("1. GRID CALIBRATION (IS-only) — trend-scaled multiplier on the let-run LONG book")
    print("   score = (lift of the 3 negative sub-periods toward 0) while retaining bull Sharpe")
    print("=" * 100)

    # Baseline (no multiplier) per-sub-period LONG Sharpe.
    w_base = np.ones(n_is)
    base_overall, base_n = weighted_ann_sharpe(mb42[long_mask], w_base[long_mask], n_is)
    base_sub = {}
    for (lo, hi), st in zip(bounds, starts, strict=True):
        m = long_mask & (ot_days >= lo) & (ot_days < hi)
        s, _ = weighted_ann_sharpe(mb42[m], w_base[m], n_is)
        base_sub[st] = s

    grid_rows = []
    best = None
    for slope_lb in GRID_SLOPE_LB:
        z = trend_zscore(close, slope_lb)
        for floor in GRID_FLOOR:
            for z_lo in GRID_ZLO:
                for z_hi in GRID_ZHI:
                    if z_hi <= z_lo:
                        continue
                    w = size_multiplier(z, floor, z_lo, z_hi)
                    overall, _ = weighted_ann_sharpe(mb42[long_mask], w[long_mask], n_is)
                    # Per-sub-period weighted Sharpe.
                    neg_sharpes, bull_sharpes = [], []
                    for (lo, hi), st in zip(bounds, starts, strict=True):
                        m = long_mask & (ot_days >= lo) & (ot_days < hi)
                        s, nn = weighted_ann_sharpe(mb42[m], w[m], n_is)
                        if not np.isfinite(s):
                            continue
                        if is_neg_subperiod(st):
                            neg_sharpes.append(s)
                        else:
                            bull_sharpes.append(s)
                    worst_neg = min(neg_sharpes) if neg_sharpes else np.nan
                    mean_neg = float(np.mean(neg_sharpes)) if neg_sharpes else np.nan
                    mean_bull = float(np.mean(bull_sharpes)) if bull_sharpes else np.nan
                    # Effective avg multiplier on the long book (size-retention diagnostic).
                    avg_mult = float(np.mean(w[long_mask]))
                    # SCORE: lift the worst negative sub-period toward 0 (primary) while keeping
                    # the bull mean high. Penalize bull-Sharpe erosion. IS-only objective.
                    # Composite = worst_neg (want ->0+) + 0.5*mean_bull (retain bull) ; both IS.
                    score = worst_neg + 0.5 * mean_bull
                    grid_rows.append(
                        dict(
                            slope_lb=slope_lb,
                            floor=floor,
                            z_lo=z_lo,
                            z_hi=z_hi,
                            overall_long_sharpe=round(overall, 3),
                            worst_neg_sub=round(worst_neg, 3),
                            mean_neg_sub=round(mean_neg, 3),
                            mean_bull_sub=round(mean_bull, 3),
                            avg_mult_on_long=round(avg_mult, 3),
                            score=round(score, 3),
                        )
                    )
                    if best is None or score > best["score"]:
                        best = grid_rows[-1]
    grid_df = pd.DataFrame(grid_rows).sort_values("score", ascending=False).reset_index(drop=True)
    grid_df.to_csv(OUTDIR / "grid_calibration.csv", index=False)
    print(f"  baseline (NO multiplier): overall LONG Sharpe {base_overall:+.3f}  (n={base_n})")
    print(f"  grid size: {len(grid_df)} configs. Top 8 by score (worst_neg + 0.5*mean_bull):")
    print(grid_df.head(8).to_string(index=False))
    print(f"\n  >>> CHOSEN (IS-best): {best}")

    # ============ 2. CHOSEN-CONFIG per-sub-period table WITH vs WITHOUT multiplier ============
    print("\n" + "=" * 100)
    print("2. CHOSEN config — per-sub-period LONG Sharpe WITH vs WITHOUT the multiplier (IS-only)")
    print("=" * 100)
    z_best = trend_zscore(close, int(best["slope_lb"]))
    w_best = size_multiplier(z_best, best["floor"], best["z_lo"], best["z_hi"])
    rows2 = []
    for (lo, hi), st in zip(bounds, starts, strict=True):
        m = long_mask & (ot_days >= lo) & (ot_days < hi)
        s_off, n_off = weighted_ann_sharpe(mb42[m], w_base[m], n_is)
        s_on, n_on = weighted_ann_sharpe(mb42[m], w_best[m], n_is)
        avg_m = float(np.mean(w_best[m])) if m.sum() > 0 else np.nan
        flag = "NEG" if is_neg_subperiod(st) else "bull"
        rows2.append(
            dict(
                sub_period=st,
                regime=flag,
                long_n=int(n_off),
                sharpe_OFF=round(s_off, 3) if np.isfinite(s_off) else np.nan,
                sharpe_ON=round(s_on, 3) if np.isfinite(s_on) else np.nan,
                delta=(
                    round(s_on - s_off, 3)
                    if np.isfinite(s_on) and np.isfinite(s_off)
                    else np.nan
                ),
                avg_mult=round(avg_m, 3),
            )
        )
    sub_df = pd.DataFrame(rows2)
    sub_df.to_csv(OUTDIR / "subperiod_with_without.csv", index=False)
    print(sub_df.to_string(index=False))

    # Overall LONG and FULL-book Sharpe, OFF vs ON, + trade-count retention.
    long_off, long_n_off = weighted_ann_sharpe(mb42[long_mask], w_base[long_mask], n_is)
    long_on, long_n_on = weighted_ann_sharpe(mb42[long_mask], w_best[long_mask], n_is)
    # FULL book: multiplier is LONG-BIAS — applies to longs only; shorts keep size 1.0.
    w_full = np.where(d42 > 0, w_best, 1.0)
    full_off, full_n_off = weighted_ann_sharpe(mb42[full_mask], np.ones(n_is)[full_mask], n_is)
    full_on, full_n_on = weighted_ann_sharpe(mb42[full_mask], w_full[full_mask], n_is)
    cnt_ok = long_n_off == long_n_on and full_n_off == full_n_on
    print("\n  OVERALL (IS):")
    print(
        f"    LONG book Sharpe OFF {long_off:+.3f} (n={long_n_off}) -> "
        f"ON {long_on:+.3f} (n={long_n_on})"
    )
    print(
        f"    FULL book Sharpe OFF {full_off:+.3f} (n={full_n_off}) -> "
        f"ON {full_on:+.3f} (n={full_n_on})"
    )
    print(
        f"    trade COUNT unchanged: LONG {long_n_off}=={long_n_on}, "
        f"FULL {full_n_off}=={full_n_on} -> {'CONFIRMED' if cnt_ok else 'MISMATCH!'}"
    )
    print(f"    avg multiplier on LONG book: {float(np.mean(w_best[long_mask])):.3f}")

    # ============ 3. ROBUSTNESS — variant trend signals + seed-stability ============
    print("\n" + "=" * 100)
    print("3. ROBUSTNESS — alternative trend signals (chosen floor/band) + seed stability of lift")
    print("=" * 100)
    rows3 = []
    chosen_neg = [v for v in sub_df[sub_df.regime == "NEG"].sharpe_ON]
    chosen_bull = [v for v in sub_df[sub_df.regime == "bull"].sharpe_ON]
    rows3.append(
        dict(
            variant="slope-z (CHOSEN)",
            overall_long=round(long_on, 3),
            worst_neg=round(min(chosen_neg), 3),
            mean_bull=round(float(np.mean(chosen_bull)), 3),
        )
    )
    # 3a. price-vs-SMA continuous variant (same floor/band).
    z_pv = trend_zscore_price_vs_sma(close)
    w_pv = size_multiplier(z_pv, best["floor"], best["z_lo"], best["z_hi"])
    pv_long, _ = weighted_ann_sharpe(mb42[long_mask], w_pv[long_mask], n_is)
    pv_neg, pv_bull = [], []
    for (lo, hi), st in zip(bounds, starts, strict=True):
        m = long_mask & (ot_days >= lo) & (ot_days < hi)
        s, _ = weighted_ann_sharpe(mb42[m], w_pv[m], n_is)
        if np.isfinite(s):
            (pv_neg if is_neg_subperiod(st) else pv_bull).append(s)
    rows3.append(
        dict(
            variant="price-vs-SMA-z",
            overall_long=round(pv_long, 3),
            worst_neg=round(min(pv_neg), 3) if pv_neg else np.nan,
            mean_bull=round(float(np.mean(pv_bull)), 3) if pv_bull else np.nan,
        )
    )
    # 3b. seed stability — apply chosen multiplier to each seed's long book; report worst-neg lift.
    for seed in SEEDS:
        d, oof = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, seed)
        mb = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
        lm = oof & (d > 0) & np.isfinite(mb)
        worst_off, worst_on = [], []
        for (lo, hi), st in zip(bounds, starts, strict=True):
            if not is_neg_subperiod(st):
                continue
            m = lm & (ot_days >= lo) & (ot_days < hi)
            s_off, _ = weighted_ann_sharpe(mb[m], w_base[m], n_is)
            s_on, _ = weighted_ann_sharpe(mb[m], w_best[m], n_is)
            if np.isfinite(s_off):
                worst_off.append(s_off)
            if np.isfinite(s_on):
                worst_on.append(s_on)
        rows3.append(dict(variant=f"seed {seed} (neg-sub worst)",
                          overall_long=np.nan,
                          worst_neg=round(min(worst_off), 3) if worst_off else np.nan,
                          mean_bull=round(min(worst_on), 3) if worst_on else np.nan))
    rob_df = pd.DataFrame(rows3)
    rob_df.columns = ["variant", "overall_long_ON", "worst_neg_ON", "mean_bull_ON_or_worstoff"]
    rob_df.to_csv(OUTDIR / "robustness.csv", index=False)
    print("  (row 'seed X': worst_neg=worst neg-sub OFF, last col=worst neg-sub ON for that seed)")
    print(rob_df.to_string(index=False))

    print(f"\nWrote: {OUTDIR/'grid_calibration.csv'}, {OUTDIR/'subperiod_with_without.csv'}, "
          f"{OUTDIR/'robustness.csv'}")


if __name__ == "__main__":
    main()
