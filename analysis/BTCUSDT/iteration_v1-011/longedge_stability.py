"""IS-ONLY long-edge sub-period stability + the three iter-011 levers — iter-v1/011 (BTCUSDT).

iter-010 hit the FIRST positive IS Sharpe of the campaign (+0.39) on a fixed_horizon N=9 (3d)
let-winners-run book, then inverted OOS (-1.48). The backtest diagnosed: ALL IS profit is LONG
(+33% longs / -3.5% shorts) and the LONG edge collapses OOS (long WR 45.5%->31.2%, net +33%->-22.7%).
The model's long directional skill does not generalize.

This script asks — IS-ONLY — whether that long-edge collapse is REDUCIBLE OVERFIT or STRUCTURAL
REGIME, by measuring ONE unifying quantity across three levers:

  the CROSS-IS-SUB-PERIOD STABILITY of the let-winners-run LONG edge
  (fraction of IS sub-periods with positive LONG Sharpe; dispersion of sub-period LONG Sharpe).

An edge that is stable across IS sub-periods (spanning bull/bear/chop) is the IS-visible signature
of OOS robustness. An edge concentrated in one IS sub-period (e.g. a bull) and absent/negative in
others is the IS-visible signature of OOS fragility. The lever that most improves IS-internal
stability is the one most likely to generalize OOS — and it is chosen ENTIRELY on IS.

Three levers tested, all measured by the SAME stability metric:

  Q1  BASELINE STABILITY. The iter-010 setup (19-col HYBRID, fixed_horizon N=9, let-run LONG book)
      under an EXPANDING walk-forward. Split IS into rolling ~6-month sub-periods; report LONG
      let-run Sharpe + WR per sub-period. Is the IS long edge stable, or bull-concentrated?

  Q2  TRAINING-WINDOW SENSITIVITY (rolling walk-forward). Re-fit the SAME 19-col model under a
      ROLLING window of length {180, 365, 545, 730} days and an EXPANDING window. For each, measure
      the per-sub-period LONG Sharpe and its dispersion. Crypto-native thesis: a long edge learned
      on a narrow recent window overfits that regime; a longer window spanning bull+bear+chop yields
      a more stable (lower-dispersion) long edge. Does raising the training_days floor reduce
      sub-period dispersion?

  Q3  MODEL-COMPLEXITY SENSITIVITY. At the BEST window from Q2, compare model complexity:
      (a) 19-col baseline regularized config; (b) LEANER feature set (drop FE-flagged near-inert
      mom_rsi_9 / vol_cmf_10 / ent_shannon_10 -> 16 cols; and a tight top-8 by stable IS gain);
      (c) STRONGER regularization (fewer leaves/trees, higher min_child_samples). Does a leaner /
      more-regularized model reduce LONG sub-period dispersion?

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; rolling/expanding walk-forward trains ONLY on candles strictly before each test
window (with an embargo gap >= label horizon to purge the forward-label overlap); the forward label
and let-run trade are computed on the IS slice only (tail rows NaN-mask — no OOS candle in the
frame). `src/`, the runner, and OOS are UNTOUCHED. Nothing here is fit/selected/calibrated against
OOS; OOS rows are never read.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-011/longedge_stability.py
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
N_LABEL = 9  # fixed_horizon 3d (iter-010)
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3  # purge >= label horizon at the train/test boundary
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-011"

# iter-009/010 19-col HYBRID set (verbatim).
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
# FE-flagged near-inert columns to drop for the LEANER variant.
NEAR_INERT = ("mom_rsi_9", "vol_cmf_10", "ent_shannon_10")
LEANER_16 = tuple(c for c in ITER009_FEATURES if c not in NEAR_INERT)

# Regularized LightGBM configs (the iter-010 proxy default + a stronger-regularization variant).
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
STRONG_REG_PARAMS = dict(
    n_estimators=150,
    max_depth=3,
    num_leaves=7,
    learning_rate=0.03,
    min_child_samples=160,
    subsample=0.7,
    colsample_bytree=0.7,
    reg_alpha=1.0,
    reg_lambda=1.0,
    n_jobs=4,
    verbose=-1,
)


def fwd_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c) -> np.ndarray:
    """Enter at close in `direction`, exit at min(SL @ atr_sl*ATR adverse, timeout). TP non-binding."""
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


def walk_forward_predict(
    X: np.ndarray,
    y: np.ndarray,
    ot_days: np.ndarray,
    valid: np.ndarray,
    params: dict,
    seed: int,
    window_days: float | None,  # None => expanding
    step_days: float = 30.0,
    min_train_days: float = 365.0,
) -> tuple[np.ndarray, np.ndarray]:
    """IS-only walk-forward. For each monthly test step, train on candles strictly before the test
    window start MINUS an embargo (>= label horizon), using either an EXPANDING window (window_days
    None) or a ROLLING window of `window_days`. Returns (predictions on test candles, their indices).

    All indices are within the IS slice (caller passes the IS frame); no OOS row exists in X.
    """
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    t0 = ot_days.min()
    t_end = ot_days.max()
    # first test window starts once we have >= min_train_days of history + embargo.
    test_start = t0 + min_train_days + embargo_days
    preds_all, idx_all = [], []
    while test_start < t_end:
        test_end = test_start + step_days
        train_cutoff = test_start - embargo_days  # train candles must be < this day
        train_lo = (train_cutoff - window_days) if window_days is not None else t0
        train_mask = valid & (ot_days < train_cutoff) & (ot_days >= train_lo)
        test_mask = valid & (ot_days >= test_start) & (ot_days < test_end)
        n_tr, n_te = int(train_mask.sum()), int(test_mask.sum())
        if n_tr >= 200 and n_te > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[train_mask], y[train_mask])
            ti = np.where(test_mask)[0]
            preds_all.append(m.predict(X[test_mask]))
            idx_all.append(ti)
        test_start = test_end
    if not idx_all:
        return np.array([]), np.array([], dtype=int)
    return np.concatenate(preds_all), np.concatenate(idx_all)


def ann_sharpe(r: np.ndarray, n_total: int, min_n: int = 12) -> tuple[float, float, int]:
    r = r[np.isfinite(r)]
    if len(r) < min_n:
        return np.nan, np.nan, len(r)
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    if std <= 0:
        return np.nan, float(np.mean(r > 0)), len(r)
    sann = (mean / std) * np.sqrt(len(r) / n_total * CANDLES_PER_YEAR)
    return sann, float(np.mean(r > 0)), len(r)


def subperiod_long_stats(
    model_dir: np.ndarray,
    oof_mask: np.ndarray,
    longbook: np.ndarray,
    modelbook: np.ndarray,
    ot_days: np.ndarray,
    n_total: int,
    period_days: float = 182.5,
) -> list[dict]:
    """Per ~6-month sub-period: LONG-only let-run Sharpe/WR (model trades that are LONG), the
    always-LONG Sharpe, and the model (both-side) Sharpe. The LONG-only model book isolates the
    diagnosed long edge."""
    t0 = ot_days[oof_mask].min()
    t1 = ot_days[oof_mask].max()
    rows = []
    edge = t0
    k = 0
    while edge < t1:
        hi = edge + period_days
        win = oof_mask & (ot_days >= edge) & (ot_days < hi)
        # model LONG-only book: model trades whose direction is +1
        long_model_mask = win & (model_dir > 0) & np.isfinite(modelbook)
        lm_sann, lm_wr, lm_n = ann_sharpe(modelbook[long_model_mask], n_total)
        # always-LONG book on the same sub-period candles
        always_long_mask = win & np.isfinite(longbook)
        al_sann, al_wr, _ = ann_sharpe(longbook[always_long_mask], n_total)
        # full model book (both sides)
        full_mask = win & np.isfinite(modelbook)
        full_sann, _, _ = ann_sharpe(modelbook[full_mask], n_total)
        rows.append(
            dict(
                period=f"P{k}",
                start=str(pd.to_datetime(edge * 86400_000, unit="ms").date()),
                long_model_n=lm_n,
                long_model_sharpe=round(lm_sann, 3) if np.isfinite(lm_sann) else np.nan,
                long_model_wr=round(lm_wr, 3) if np.isfinite(lm_wr) else np.nan,
                always_long_sharpe=round(al_sann, 3) if np.isfinite(al_sann) else np.nan,
                full_model_sharpe=round(full_sann, 3) if np.isfinite(full_sann) else np.nan,
            )
        )
        edge = hi
        k += 1
    return rows


def stability_summary(rows: list[dict], key: str = "long_model_sharpe") -> dict:
    vals = np.array([r[key] for r in rows if np.isfinite(r[key])])
    if len(vals) == 0:
        return dict(
            n_periods=0,
            frac_pos=np.nan,
            mean=np.nan,
            std=np.nan,
            min=np.nan,
            worst_period_sharpe=np.nan,
        )
    return dict(
        n_periods=len(vals),
        frac_pos=round(float(np.mean(vals > 0)), 3),
        mean=round(float(np.mean(vals)), 3),
        std=round(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0, 3),
        min=round(float(np.min(vals)), 3),
        worst_period_sharpe=round(float(np.min(vals)), 3),
    )


def build_books(
    X, y, ot_days, valid, high, low, close, atr, params, seed, window_days, min_train_days
):
    preds, idx = walk_forward_predict(
        X, y, ot_days, valid, params, seed, window_days, min_train_days=min_train_days
    )
    n = len(close)
    d = np.zeros(n)
    if len(idx):
        d[idx] = np.sign(preds)
    oof = np.zeros(n, dtype=bool)
    if len(idx):
        oof[idx] = True
    modelbook = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
    return d, oof, modelbook


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    natr = df[ATR_COLUMN].to_numpy(float)
    atr = close * natr / 100.0
    ot_ms = df["open_time"].to_numpy(float)
    ot_days = ot_ms / 86400_000.0

    feats19 = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats19) == 19
    X19 = df[feats19].to_numpy(float)
    feats16 = [c for c in LEANER_16 if c in df.columns]
    assert len(feats16) == 16
    X16 = df[feats16].to_numpy(float)

    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)
    long_dir = np.ones(n_is)
    longbook = letrun(high, low, close, atr, long_dir, ATR_SL, N_LABEL)

    print("IS rows:", n_is, "span days:", round(ot_days.max() - ot_days.min(), 0))
    print("=" * 100)

    # ============================ Q1 + Q2 — TRAINING WINDOW ============================
    print("Q1+Q2 — LONG-edge sub-period stability across TRAINING-WINDOW configs (19-col, seed 42)")
    print("  metric: per-~6mo LONG let-run Sharpe; stability = frac_pos + dispersion(std) + worst")
    print("=" * 100)
    window_configs = [
        ("roll_180d", 180.0, 180.0),
        ("roll_365d", 365.0, 365.0),
        ("roll_545d", 545.0, 545.0),
        ("roll_730d", 730.0, 730.0),
        ("expanding", None, 365.0),  # expanding with a 365d warmup floor
    ]
    q2_rows = []
    q1_detail = None
    for name, wdays, mintrain in window_configs:
        d, oof, modelbook = build_books(
            X19, y, ot_days, valid, high, low, close, atr, BASE_PARAMS, 42, wdays, mintrain
        )
        sp = subperiod_long_stats(d, oof, longbook, modelbook, ot_days, n_is)
        summ = stability_summary(sp, "long_model_sharpe")
        # full-book ungated annualized Sharpe (overall) + overall LONG-only
        full_mask = oof & np.isfinite(modelbook)
        full_sann, _, full_n = ann_sharpe(modelbook[full_mask], n_is)
        lm_mask = oof & (d > 0) & np.isfinite(modelbook)
        lm_sann, lm_wr, lm_n = ann_sharpe(modelbook[lm_mask], n_is)
        q2_rows.append(
            dict(
                config=name,
                full_n=full_n,
                full_sharpe_ann=round(full_sann, 3),
                long_n=lm_n,
                long_sharpe_ann=round(lm_sann, 3),
                long_wr=round(lm_wr, 3),
                sp_n=summ["n_periods"],
                sp_frac_pos=summ["frac_pos"],
                sp_mean=summ["mean"],
                sp_dispersion=summ["std"],
                sp_worst=summ["worst_period_sharpe"],
            )
        )
        print(
            f"  {name:11s} full[n={full_n:4d} S={full_sann:+.3f}]  "
            f"LONG[n={lm_n:4d} S={lm_sann:+.3f} WR={lm_wr:.3f}]  "
            f"sub-period LONG: {summ['n_periods']}p frac_pos={summ['frac_pos']} "
            f"disp={summ['std']} worst={summ['worst_period_sharpe']:+.3f}"
        )
        if name == "expanding":
            q1_detail = sp

    # Q1 detail: print the expanding-window per-sub-period table (the iter-010 setup proxy)
    print("\n  Q1 DETAIL — expanding window (iter-010 proxy) per ~6-month sub-period:")
    print(
        f"  {'period':6s} {'start':12s} {'LONGn':>6s} {'LONG_S':>8s} {'LONG_WR':>8s} "
        f"{'alwaysLONG_S':>13s} {'full_S':>8s}"
    )
    for r in q1_detail:
        ls = f"{r['long_model_sharpe']:+.3f}" if np.isfinite(r["long_model_sharpe"]) else "  nan"
        als = f"{r['always_long_sharpe']:+.3f}" if np.isfinite(r["always_long_sharpe"]) else "  nan"
        fs = f"{r['full_model_sharpe']:+.3f}" if np.isfinite(r["full_model_sharpe"]) else "  nan"
        wr = f"{r['long_model_wr']:.3f}" if np.isfinite(r["long_model_wr"]) else " nan"
        print(
            f"  {r['period']:6s} {r['start']:12s} {r['long_model_n']:>6d} {ls:>8s} "
            f"{wr:>8s} {als:>13s} {fs:>8s}"
        )

    pd.DataFrame(q2_rows).to_csv(OUTDIR / "training_window_stability.csv", index=False)
    pd.DataFrame(q1_detail).to_csv(OUTDIR / "expanding_subperiod_detail.csv", index=False)

    # pick best window = highest sub-period frac_pos, tie-break lowest dispersion
    valid_cfg = [r for r in q2_rows if r["sp_n"] and np.isfinite(r["sp_frac_pos"])]
    best = max(valid_cfg, key=lambda r: (r["sp_frac_pos"], -(r["sp_dispersion"] or 9)))
    best_name = best["config"]
    best_wdays = dict((n, w) for n, w, _ in window_configs)[best_name]
    best_mintrain = dict((n, m) for n, _, m in window_configs)[best_name]
    print(
        f"\n  => BEST WINDOW by sub-period stability: {best_name} "
        f"(frac_pos={best['sp_frac_pos']}, dispersion={best['sp_dispersion']})"
    )

    # ============================ Q3 — MODEL COMPLEXITY ============================
    print("\n" + "=" * 100)
    print(f"Q3 — MODEL-COMPLEXITY sub-period stability at the best window ({best_name}, seed 42)")
    print("=" * 100)
    # top-8 by stable IS gain: rank features by frequency-of-top via a quick expanding-window
    # gain importance averaged across walk-forward refits (IS-only). Compute once on 19-col.
    imp_accum = np.zeros(len(feats19))
    n_fits = 0
    t0 = ot_days.min()
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    ts = t0 + 365.0 + embargo_days
    while ts < ot_days.max():
        te = ts + 30.0
        tc = ts - embargo_days
        tr = valid & (ot_days < tc) & (ot_days >= t0)
        if tr.sum() >= 200:
            mm = lgb.LGBMRegressor(random_state=42, **BASE_PARAMS)
            mm.fit(X19[tr], y[tr])
            imp = mm.booster_.feature_importance(importance_type="gain").astype(float)
            if imp.sum() > 0:
                imp_accum += imp / imp.sum()
                n_fits += 1
        ts = te
    imp_mean = imp_accum / max(n_fits, 1)
    rank = np.argsort(-imp_mean)
    top8 = [feats19[i] for i in rank[:8]]
    print(f"  Stable IS gain ranking (top 8): {top8}")
    X8 = df[top8].to_numpy(float)

    complexity_configs = [
        ("19col_base", X19, BASE_PARAMS),
        ("16col_lean", X16, BASE_PARAMS),
        ("8col_top", X8, BASE_PARAMS),
        ("19col_strongreg", X19, STRONG_REG_PARAMS),
    ]
    q3_rows = []
    for name, Xc, params in complexity_configs:
        d, oof, modelbook = build_books(
            Xc, y, ot_days, valid, high, low, close, atr, params, 42, best_wdays, best_mintrain
        )
        sp = subperiod_long_stats(d, oof, longbook, modelbook, ot_days, n_is)
        summ = stability_summary(sp, "long_model_sharpe")
        full_mask = oof & np.isfinite(modelbook)
        full_sann, _, full_n = ann_sharpe(modelbook[full_mask], n_is)
        lm_mask = oof & (d > 0) & np.isfinite(modelbook)
        lm_sann, lm_wr, lm_n = ann_sharpe(modelbook[lm_mask], n_is)
        q3_rows.append(
            dict(
                config=name,
                full_n=full_n,
                full_sharpe_ann=round(full_sann, 3),
                long_n=lm_n,
                long_sharpe_ann=round(lm_sann, 3),
                long_wr=round(lm_wr, 3),
                sp_n=summ["n_periods"],
                sp_frac_pos=summ["frac_pos"],
                sp_mean=summ["mean"],
                sp_dispersion=summ["std"],
                sp_worst=summ["worst_period_sharpe"],
            )
        )
        print(
            f"  {name:16s} full[n={full_n:4d} S={full_sann:+.3f}]  "
            f"LONG[n={lm_n:4d} S={lm_sann:+.3f} WR={lm_wr:.3f}]  "
            f"sub-period LONG: {summ['n_periods']}p frac_pos={summ['frac_pos']} "
            f"disp={summ['std']} worst={summ['worst_period_sharpe']:+.3f}"
        )
    pd.DataFrame(q3_rows).to_csv(OUTDIR / "complexity_stability.csv", index=False)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(
        f"\nWrote: {OUTDIR / 'training_window_stability.csv'}, "
        f"{OUTDIR / 'expanding_subperiod_detail.csv'}, {OUTDIR / 'complexity_stability.csv'}"
    )


if __name__ == "__main__":
    main()
