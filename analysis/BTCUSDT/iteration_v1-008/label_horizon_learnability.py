"""IS-ONLY label-horizon learnability scan for BTCUSDT iter-v1/008 — Phase 2.

QR Phase 1/2 analysis. The orthogonal-feature lever is CLOSED (iter-005/006/007 all
NEGATIVE). This script attacks the LABELING lever instead: does ANY alternative label
definition lift BTC's forward target materially OFF the prune-only noise floor
(iter-006 FE: prune-only purged-CV OOF dir_acc 0.5068, OOF R2 -0.095)?

It reproduces the runner's `label_trades` label generation FAITHFULLY (the same ATR
triple-barrier first-hit logic, fixed_horizon sign rule, and trend_scanning OLS-slope
rule from src/crypto_trade/strategies/ml/labeling.py), then measures, IS-ONLY, in a
purged forward-chaining CV (5 folds, 3-bar embargo) on the frozen 41-col prune:

  * dir_acc  — out-of-fold directional accuracy: does sign(model_score) match the
               REALIZED forward-return sign at the label's own horizon? (the metric
               that drives a directional specialist's Sharpe)
  * score_IC — Spearman corr of OOF model score vs realized forward return (calibration)
  * oof_R2   — OOF R2 of the model score predicting the realized forward return
  * econ     — mean OOF-realized net PnL per traded candle, using the model's chosen
               direction and the label's own forward-return convention (NET of the
               0.1% fee the runner applies). The bottom line: would betting on the
               model's sign at this horizon have been profitable IS?

LABEL CONFIGS SCREENED (all match the runner's exposed knobs):
  * triple_barrier ATR 2.9/1.45, timeout 7d (21 candles) — the CURRENT baseline label.
  * triple_barrier ATR variants: longer timeout (14d=42c), wider/narrower geometry.
  * fixed_horizon at N in {1, 3, 6, 9} candles (8h / 1d / 2d / 3d).
  * trend_scanning over a candle-horizon grid.

OOS-VIGILANCE (HARD, non-negotiable): every quantity is computed AFTER the strict
`open_time < OOS_CUTOFF_MS` filter. The forward labels are built on the IS slice only;
the forward reach at the tail therefore NaN-masks (it cannot see an OOS candle because
no OOS candle is in the frame). An explicit leak-guard assert verifies the IS max.

Re-runnable, reads ONLY the BTC 8h parquet, NEVER modifies src/, NEVER touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-008/label_horizon_learnability.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# --------------------------------------------------------------------------- #
# Sacred constants — IS-only, single-symbol, no look-ahead.
# --------------------------------------------------------------------------- #
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (config.OOS_CUTOFF_MS)
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"  # runner default (lgbm.py atr_column); ATR = close * natr/100
FEE_PCT = 0.1  # runner label fee (labeling.label_trades default)
RANDOM_SEED = 42
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-008"

# Frozen 41-col OHLCV prune (run_baseline_v1.V1_BTC_PRUNED_ITER002).
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


# --------------------------------------------------------------------------- #
# Faithful reproductions of src/crypto_trade/strategies/ml/labeling.py
# (verified against labeling.py:217-535, _trend_scan_label:132-214). These build
# the SAME labels the runner trains on, given the same knobs. Single-symbol so the
# per-symbol scan is just a forward window over the contiguous IS slice.
# --------------------------------------------------------------------------- #
def _atr_triple_barrier(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr: np.ndarray,
    atr_tp: float, atr_sl: float, timeout_candles: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce labeling.label_trades use_atr=True, label_mode='triple_barrier'.

    Returns (label, realized_fwd_return_pct_at_resolution) where realized return is
    the directional forward return the labeled bet would have realized (for econ).
    label uses the runner's TP-first-hit rule; if no TP hits, sign of fwd return at
    the LAST scanned close (timeout close), matching labeling.py:455/501-510.
    """
    n = len(close)
    labels = np.zeros(n, dtype=np.int8)
    fwd_signed = np.full(n, np.nan, dtype=np.float64)  # realized return in the labeled dir (%)
    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i]
        if np.isnan(a):
            a = entry * 0.02
        tp_dist = a * atr_tp
        sl_dist = a * atr_sl
        long_tp_p = entry + tp_dist
        long_sl_p = entry - sl_dist
        short_tp_p = entry - tp_dist
        short_sl_p = entry + sl_dist
        long_res = 0
        short_res = 0
        long_step = -1
        short_step = -1
        last_close = entry
        end = min(i + timeout_candles, n - 1)
        if end <= i:
            continue  # tail: cannot resolve within IS → stays neutral (NaN-masked later)
        for j in range(i + 1, end + 1):
            last_close = close[j]
            h_bar = high[j]
            lo = low[j]
            if long_res == 0:
                if lo <= long_sl_p:
                    long_res = -1
                    long_step = j
                elif h_bar >= long_tp_p:
                    long_res = 1
                    long_step = j
            if short_res == 0:
                if h_bar >= short_sl_p:
                    short_res = -1
                    short_step = j
                elif lo <= short_tp_p:
                    short_res = 1
                    short_step = j
            if long_res != 0 and short_res != 0:
                break
        fwd_ret = (last_close - entry) / entry * 100.0
        long_tp_hit = long_res == 1
        short_tp_hit = short_res == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1
        labels[i] = lab
        # realized return in the labeled direction (timeout close used as exit proxy;
        # consistent across modes for the econ comparison — this is a LEARNABILITY
        # probe, not the backtest's path-exact PnL, which only the runner produces)
        fwd_signed[i] = fwd_ret if lab == 1 else -fwd_ret
    return labels, fwd_signed


def _fixed_horizon(close: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce label_mode='fixed_horizon': label = sign(N-candle fwd return).

    Returns (label, realized_directional_return_pct). fwd_ret = (close[t+N]-close[t])/
    close[t]*100; label = +1 if fwd_ret>=0 else -1; realized dir return = fwd_ret if
    long else -fwd_ret (= |fwd_ret| since label = sign, by construction).
    """
    n = len(close)
    fwd = np.full(n, np.nan, dtype=np.float64)
    valid = n - horizon
    if valid > 0:
        fwd[:valid] = (close[horizon:] - close[:valid]) / close[:valid] * 100.0
    labels = np.where(np.isnan(fwd), 0, np.where(fwd >= 0, 1, -1)).astype(np.int8)
    fwd_signed = np.where(labels == 1, fwd, -fwd)
    return labels, fwd_signed


def _ols_t(y: np.ndarray) -> tuple[float, float]:
    """Closed-form OLS slope + t-stat over index 0..len-1 (matches _trend_scan_label)."""
    n = len(y)
    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = y.mean()
    ss_xx = float(np.sum((x - x_mean) ** 2))
    if ss_xx == 0.0:
        return 0.0, 0.0
    slope = float(np.sum((x - x_mean) * (y - y_mean))) / ss_xx
    y_hat = y_mean + slope * (x - x_mean)
    ss_res = float(np.sum((y - y_hat) ** 2))
    dof = n - 2
    if dof <= 0:
        return slope, 0.0
    se = (ss_res / dof / ss_xx) ** 0.5
    if se == 0.0:
        return slope, (1e10 if slope > 0 else -1e10)
    return slope, slope / se


def _trend_scanning(close: np.ndarray, grid: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce label_mode='trend_scanning' (_trend_scan_label:132-214).

    For each bar, fit OLS over close[t:t+h+1] for each h in grid, pick max |t|,
    label = sign(slope). Returns (label, realized return at selected horizon, signed).
    """
    n = len(close)
    labels = np.zeros(n, dtype=np.int8)
    fwd_signed = np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        if i + 1 >= n:
            continue
        entry = close[i]
        best_abs_t = -1.0
        best_label = 1
        best_h = grid[0]
        for h in grid:
            if i + h >= n:
                continue
            y = close[i : i + h + 1]
            _, t = _ols_t(y)
            if abs(t) > best_abs_t:
                best_abs_t = abs(t)
                best_label = 1 if _ols_t(y)[0] >= 0 else -1
                best_h = h
        if best_abs_t < 0:
            continue  # no valid horizon within IS (tail) → neutral, NaN-masked
        labels[i] = best_label
        hz_close = close[i + best_h]
        fwd_ret = (hz_close - entry) / entry * 100.0 if entry != 0 else 0.0
        fwd_signed[i] = fwd_ret if best_label == 1 else -fwd_ret
    return labels, fwd_signed


# --------------------------------------------------------------------------- #
# Purged forward-chaining CV — learnability of each label by the prune features.
# A directional specialist's edge = can the features predict the label's direction
# out-of-fold, and does betting that direction make money net of fee? We train a
# regressor on the SIGNED realized return (the runner's weight = |pnl|, label = sign;
# regressing the signed return captures both sign + magnitude, then we score sign).
# --------------------------------------------------------------------------- #
def _purged_cv(X: np.ndarray, y_signed_ret: np.ndarray, valid: np.ndarray,
               folds: int = 5, embargo: int = 3) -> dict:
    """5 forward-chaining folds, 3-bar embargo. y_signed_ret = realized fwd return (%)
    in the LONG direction (so sign(y) = the correct directional label). The model
    predicts this; sign(pred) = chosen direction. Metrics computed OOF on valid rows.
    """
    idx = np.where(valid)[0]
    n = len(idx)
    if n < 200:
        return {"dir_acc": np.nan, "score_ic": np.nan, "oof_r2": np.nan,
                "econ_net": np.nan, "n_oof": 0, "trade_frac": np.nan}
    Xm = X[idx]
    ym = y_signed_ret[idx]  # realized LONG-direction return (%) at the label horizon
    fold_size = n // folds
    all_pred, all_y = [], []
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
        all_pred.append(p)
        all_y.append(ym[te_start:te_end])
    pred = np.concatenate(all_pred)
    yt = np.concatenate(all_y)
    # directional accuracy: model's chosen direction vs realized sign
    nz = yt != 0
    dir_acc = float(np.mean((np.sign(pred) == np.sign(yt))[nz])) if nz.sum() else np.nan
    # economic: net PnL per candle = sign(pred) * realized_long_return - fee (already in y)
    #   realized PnL in the model's chosen direction = sign(pred) * yt ; minus fee
    econ = float(np.mean(np.sign(pred) * yt - FEE_PCT))
    # calibration
    if np.std(pred) > 0 and np.std(yt) > 0:
        score_ic = float(spearmanr(pred, yt).correlation)
    else:
        score_ic = np.nan
    ss_res = float(np.sum((yt - pred) ** 2))
    ss_tot = float(np.sum((yt - yt.mean()) ** 2))
    oof_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return {"dir_acc": dir_acc, "score_ic": score_ic, "oof_r2": oof_r2,
            "econ_net": econ, "n_oof": int(len(yt))}


def main() -> None:
    assert PARQUET.exists(), f"parquet not found: {PARQUET}"
    df_full = pd.read_parquet(PARQUET)
    assert "open_time" in df_full.columns, "open_time column missing"

    # ---- IS-only filter (HARD leak guard) ----
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr = close * natr / 100.0  # runner ATR convention (lgbm.py:758)

    prune_present = [c for c in V1_BTC_PRUNED_ITER002 if c in df.columns]
    assert len(prune_present) == 41, f"expected 41 prune cols, got {len(prune_present)}"
    X = df[prune_present].to_numpy(dtype=np.float64)

    print("=" * 80)
    print(f"IS-ONLY label-horizon learnability — {SYMBOL} {INTERVAL}")
    print(f"IS rows (open_time < {OOS_CUTOFF_MS} = 2025-03-24): {n_is}")
    print(f"IS window: {pd.to_datetime(df['open_time'].min(), unit='ms')} .. "
          f"{pd.to_datetime(df['open_time'].max(), unit='ms')}")
    print(f"ATR col = {ATR_COLUMN} (ATR=close*natr/100); fee={FEE_PCT}%; 41-col prune features")
    print("=" * 80)

    # IS months for the trades/month floor (≈ months in IS window)
    is_months = (df["open_time"].max() - df["open_time"].min()) / (1000 * 60 * 60 * 24 * 30.44)

    configs = []
    # --- current baseline label: ATR triple-barrier 2.9/1.45, 7d=21c ---
    configs.append(("tb_atr2.9/1.45_to21 (CURRENT)", "triple_barrier",
                    dict(atr_tp=2.9, atr_sl=1.45, timeout_candles=21)))
    # --- longer timeout ---
    configs.append(("tb_atr2.9/1.45_to42 (14d)", "triple_barrier",
                    dict(atr_tp=2.9, atr_sl=1.45, timeout_candles=42)))
    configs.append(("tb_atr2.9/1.45_to63 (21d)", "triple_barrier",
                    dict(atr_tp=2.9, atr_sl=1.45, timeout_candles=63)))
    # --- alternative geometry (tighter / symmetric / wider) ---
    configs.append(("tb_atr2.0/2.0_to21 (sym)", "triple_barrier",
                    dict(atr_tp=2.0, atr_sl=2.0, timeout_candles=21)))
    configs.append(("tb_atr2.0/1.0_to21 (tight2:1)", "triple_barrier",
                    dict(atr_tp=2.0, atr_sl=1.0, timeout_candles=21)))
    configs.append(("tb_atr4.0/2.0_to42 (wide2:1,14d)", "triple_barrier",
                    dict(atr_tp=4.0, atr_sl=2.0, timeout_candles=42)))
    # --- fixed horizon at several N ---
    for nN, lab in ((1, "fh_N1 (8h)"), (3, "fh_N3 (1d)"), (6, "fh_N6 (2d)"),
                    (9, "fh_N9 (3d)"), (21, "fh_N21 (7d)")):
        configs.append((lab, "fixed_horizon", dict(horizon=nN)))
    # --- trend scanning ---
    configs.append(("ts_grid(5,8,13,21)", "trend_scanning", dict(grid=(5, 8, 13, 21))))
    configs.append(("ts_grid(3,6,9)", "trend_scanning", dict(grid=(3, 6, 9))))

    rows = []
    for name, mode, kw in configs:
        if mode == "triple_barrier":
            lab, fwd_signed = _atr_triple_barrier(
                high, low, close, atr, kw["atr_tp"], kw["atr_sl"], kw["timeout_candles"])
        elif mode == "fixed_horizon":
            lab, fwd_signed = _fixed_horizon(close, kw["horizon"])
        elif mode == "trend_scanning":
            lab, fwd_signed = _trend_scanning(close, kw["grid"])
        else:
            continue
        # signed realized LONG-direction return: y for the regressor must be the LONG
        # return so sign(y) = correct label. fwd_signed is in the labeled direction;
        # recover the long-direction return: long_ret = fwd_signed if lab==1 else -fwd_signed
        long_ret = np.where(lab == 1, fwd_signed, -fwd_signed)
        valid = (~np.isnan(long_ret)) & (lab != 0)
        n_valid = int(valid.sum())
        # label balance + base economic profile (the realized signed return per label)
        long_share = float(np.mean(lab[valid] == 1)) if n_valid else np.nan
        base_econ = float(np.mean(fwd_signed[valid] - FEE_PCT)) if n_valid else np.nan
        cv = _purged_cv(X, long_ret, valid)
        # trades/month at this label cadence (every valid candle is a candidate)
        trades_per_month = n_valid / is_months if is_months > 0 else np.nan
        rows.append({
            "label_config": name, "mode": mode, "n_valid": n_valid,
            "long_share": long_share, "base_label_econ_net%": base_econ,
            "oof_dir_acc": cv["dir_acc"], "oof_score_ic": cv["score_ic"],
            "oof_r2": cv["oof_r2"], "oof_econ_net%/cand": cv["econ_net"],
            "trades/mo": trades_per_month,
        })

    res = pd.DataFrame(rows)

    print("\n[A] LABEL LEARNABILITY (purged 5-fold CV, 3-bar embargo, 41-col prune)")
    print("-" * 80)
    print("  dir_acc>0.5 = learnable direction; econ_net>0 = profitable IS net of fee;")
    print("  base_label_econ = realized signed return of the LABEL itself (oracle-direction,")
    print("  net fee) — its ceiling; oof_econ = what the MODEL captures out-of-fold.")
    print("-" * 80)
    with pd.option_context("display.width", 200, "display.max_columns", 30,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(res.to_string(index=False))

    # delta vs current baseline label
    cur = res[res["label_config"].str.contains("CURRENT")].iloc[0]
    print("\n[B] Δ vs CURRENT baseline label (tb_atr2.9/1.45_to21)")
    print("-" * 80)
    print(f"  baseline: oof_dir_acc={cur['oof_dir_acc']:+.4f}  "
          f"oof_econ_net%={cur['oof_econ_net%/cand']:+.4f}  oof_r2={cur['oof_r2']:+.4f}")
    print("  noise-floor anchor (iter-006 FE, 1-bar fwd target): dir_acc=0.5068, R2=-0.095")
    print("-" * 80)
    for _, r in res.iterrows():
        d_acc = r["oof_dir_acc"] - cur["oof_dir_acc"]
        d_econ = r["oof_econ_net%/cand"] - cur["oof_econ_net%/cand"]
        flag = ""
        if r["oof_dir_acc"] > 0.52:
            flag += " [dir_acc>0.52]"
        if r["oof_econ_net%/cand"] > 0:
            flag += " [econ>0]"
        print(f"  {r['label_config']:34s} Δdir_acc={d_acc:+.4f}  Δecon={d_econ:+.4f}{flag}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "label_horizon_learnability.csv"
    res.to_csv(out, index=False)
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
