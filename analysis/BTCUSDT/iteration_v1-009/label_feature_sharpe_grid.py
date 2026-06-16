"""IS-ONLY label-horizon x feature-set SHARPE-PROXY grid — BTCUSDT iter-v1/009.

FE Phase 4. iter-009 axis = FREQUENCY EMULATION within the 8h sacred constant.
This script answers Question 2 of the mandate: which (feature set x expanded-horizon
label) combination has the best IS risk-adjusted (SHARPE) outcome — NOT the best
return, NOT the best directional accuracy.

The iter-008 brief (QR) found the 41/48-col LONG-skewed prune anti-directional on BTC
across every label knob. The OPEN question iter-008 did NOT test: does a feature set
SKEWED to short-window + regime/vol/funding features (the IC-strong, horizon-growing
set identified by short_vs_long_horizon_ic.py) change the picture under an EXPANDED
label horizon? The economic thesis: a fast/regime read + a LONG hold captures crypto
trend persistence; the payoff asymmetry (let winners run, cut losers) lifts SHARPE even
if dir_acc is modest.

METHOD (purged forward-chaining CV, 5 folds, 3-bar embargo — same machinery as the
iter-008 learnability script, EXTENDED with a Sharpe proxy and feature-set axis):
  For each (FEATURE_SET, LABEL_CONFIG):
    1. Build labels FAITHFULLY via the runner's label_trades logic (ATR triple-barrier
       first-hit; fixed_horizon sign). ATR = close * vol_natr_21 / 100 (lgbm.py:758).
       The per-trade realized return uses the runner's triple-barrier resolution: TP
       distance if TP hit, -SL distance if SL hit, else timeout-close return, NET fee.
    2. Train an LGBMRegressor on the SIGNED long-direction realized return, OOF over the
       forward-chaining folds, using ONLY that feature set.
    3. The model's chosen direction = sign(OOF prediction). The per-trade realized PnL =
       sign(pred) * long_realized_return (which already embeds the TP/SL geometry + fee).
    4. SHARPE PROXY = mean(per-trade PnL) / std(per-trade PnL) * sqrt(trades_per_year).
       This is the risk-adjusted contribution — the objective. Also report dir_acc, the
       avg-win/avg-loss ratio (payoff asymmetry), win rate, and trades/mo.

A directional specialist's deployed Sharpe is driven by exactly these per-trade OOF
returns; this proxy is the cleanest IS-only forecast of it short of the full bagged
backtest (which only the runner produces, with honest slippage on top of the fee here).

OOS-VIGILANCE (HARD): every quantity computed AFTER the strict open_time<OOS_CUTOFF_MS
filter. Forward labels built on the IS slice ONLY; tail NaN-masks. Leak-guard assert.
Reads ONLY the BTC 8h parquet. Never modifies src/. Never touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-009/label_feature_sharpe_grid.py
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
FEE_PCT = 0.1  # runner label fee
RANDOM_SEED = 42
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-009"
CANDLES_PER_YEAR = 365.25 * 3  # 8h bars: 3 per day

# --------------------------------------------------------------------------- #
# FEATURE SETS (the iter-009 axis). All IS-present, scale-invariant.
# --------------------------------------------------------------------------- #

# LONG prune incumbent subset — the contrast / anchor set (skews to >=14-bar windows).
FS_LONG: tuple[str, ...] = (
    "mom_rsi_14", "mom_roc_10", "mom_macd_hist_12_26_9", "mom_macd_line_12_26_9",
    "mom_stoch_k_14", "mom_stoch_d_14", "mom_willr_14",
    "mr_pct_from_high_20", "mr_pct_from_low_20", "mr_rsi_extreme_14",
    "stat_return_5", "stat_autocorr_lag5", "stat_skew_20", "stat_kurtosis_20",
    "trend_adx_14", "trend_aroon_osc_14", "trend_aroon_osc_50", "trend_minus_di_14",
    "trend_plus_di_14", "trend_supertrend_14_3",
    "vol_atr_14", "vol_natr_14", "vol_bb_bandwidth_20", "vol_cmf_14", "vol_mfi_14",
    "vol_range_spike_24", "vol_range_spike_72", "vol_volume_rel_20",
    "regime_momentum_signed_5d", "funding_rate_zscore_30", "funding_rate_zscore_90",
    "oi_delta_30_z90", "long_short_zscore_30", "btc_funding_spread_30_90",
)

# SHORT pure — high-frequency-skewed (lookback <= ~14), the user's "higher frequency
# features" set: fast momentum/MR/vol/microstructure/taker-flow.
FS_SHORT: tuple[str, ...] = (
    "mom_rsi_5", "mom_rsi_7", "mom_rsi_9", "mom_roc_3", "mom_roc_5", "mom_mom_5",
    "mom_stoch_k_5", "mom_stoch_d_5", "mom_macd_hist_5_13_3", "mom_willr_7",
    "stat_return_1", "stat_return_2", "stat_return_3", "stat_autocorr_lag1",
    "mr_zscore_10", "mr_bb_pctb_10", "mr_rsi_extreme_7", "mr_pct_from_high_5",
    "mr_pct_from_low_5", "mr_dist_sma_10",
    "vol_atr_5", "vol_natr_7", "vol_range_spike_12", "vol_garman_klass_10",
    "vol_parkinson_10", "vol_hist_5", "vol_bb_pctb_10",
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_volume_pctchg_3",
    "vol_volume_rel_5", "vol_cmf_10", "vol_mfi_7",
    "trend_adx_7", "cusum_norm_1s", "ent_shannon_10",
)

# HYBRID — the IC-evidenced recommendation: the SHORT features that carried the most
# IC (esp. those whose |IC| GROWS toward h=21) PLUS the handful of regime/funding LONG
# anchors that dominate at long horizon. This is the "fast/regime read + long hold" set.
# Selected from short_vs_long_horizon_ic.py top-mean-|IC| + horizon-slope>0.
FS_HYBRID: tuple[str, ...] = (
    # short, IC-strong, horizon-growing
    "trend_adx_7", "vol_natr_7", "vol_garman_klass_10", "vol_parkinson_10", "vol_atr_5",
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mr_rsi_extreme_7",
    "mom_rsi_9", "stat_autocorr_lag1", "mr_pct_from_high_5", "vol_cmf_10",
    "ent_shannon_10", "cusum_norm_1s",
    # long-horizon regime/funding anchors (peak h=21, steep positive slope)
    "trend_adx_14", "trend_supertrend_14_3", "btc_funding_spread_30_90",
    "funding_rate_zscore_30", "stat_autocorr_lag5", "vol_range_spike_72",
    "mr_rsi_extreme_14", "stat_kurtosis_20",
)

FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "LONG_prune(34)": FS_LONG,
    "SHORT_pure(36)": FS_SHORT,
    "HYBRID_short+regime(23)": FS_HYBRID,
}


# --------------------------------------------------------------------------- #
# Faithful label reproductions (verified against labeling.py:217-535).
# Returns per-trade LONG-direction REALIZED return (%) embedding TP/SL geometry, net
# fee — so sign(y) = correct direction and |y| = the realized payoff for the Sharpe
# proxy. This mirrors the runner's _trade_pnl resolution (labeling.py:471-481).
# --------------------------------------------------------------------------- #
def _atr_tb_long_return(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, atr: np.ndarray,
    atr_tp: float, atr_sl: float, timeout_candles: int,
) -> np.ndarray:
    """Per-bar LONG-direction realized PnL% (TP/SL/timeout resolution, net fee)."""
    n = len(close)
    long_pnl = np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i]
        if np.isnan(a):
            a = entry * 0.02
        tp_dist = a * atr_tp
        sl_dist = a * atr_sl
        tp_pct = tp_dist / entry * 100.0
        sl_pct = sl_dist / entry * 100.0
        long_tp_p = entry + tp_dist
        long_sl_p = entry - sl_dist
        res = 0  # 0 pending, 1 tp, -1 sl
        last_close = entry
        end = min(i + timeout_candles, n - 1)
        if end <= i:
            continue  # tail: cannot resolve within IS -> NaN (masked)
        for j in range(i + 1, end + 1):
            last_close = close[j]
            if res == 0:
                if low[j] <= long_sl_p:
                    res = -1
                    break
                if high[j] >= long_tp_p:
                    res = 1
                    break
        if res == 1:
            long_pnl[i] = tp_pct - FEE_PCT
        elif res == -1:
            long_pnl[i] = -sl_pct - FEE_PCT
        else:
            long_pnl[i] = (last_close - entry) / entry * 100.0 - FEE_PCT
    return long_pnl


def _fh_long_return(close: np.ndarray, horizon: int) -> np.ndarray:
    """fixed_horizon: LONG-direction realized N-candle return (%), net fee."""
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    valid = n - horizon
    if valid > 0:
        out[:valid] = (close[horizon:] - close[:valid]) / close[:valid] * 100.0 - FEE_PCT
    return out


# --------------------------------------------------------------------------- #
# Purged forward-chaining CV returning Sharpe proxy + supporting metrics.
# --------------------------------------------------------------------------- #
def _purged_cv_sharpe(
    X: np.ndarray, long_ret: np.ndarray, valid: np.ndarray,
    candidates_per_year: float, folds: int = 5, embargo: int = 3,
) -> dict:
    """OOF Sharpe proxy of betting sign(model) at each candidate candle.

    long_ret = per-trade LONG-direction realized PnL% (net fee). Trade PnL in the
    model's chosen direction = sign(pred) * long_ret. Sharpe proxy = mean/std *
    sqrt(trades_per_year), where trades_per_year scales by the candidate density.
    """
    idx = np.where(valid)[0]
    n = len(idx)
    if n < 300:
        return {k: np.nan for k in ("dir_acc", "score_ic", "sharpe", "win_rate",
                                    "avg_win", "avg_loss", "payoff", "mean_pnl",
                                    "n_oof")}
    Xm = X[idx]
    ym = long_ret[idx]
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
        all_pred.append(mdl.predict(Xm[te_start:te_end]))
        all_y.append(ym[te_start:te_end])
    pred = np.concatenate(all_pred)
    yt = np.concatenate(all_y)
    trade_pnl = np.sign(pred) * yt  # realized PnL in the model's chosen direction
    nz = yt != 0
    dir_acc = float(np.mean((np.sign(pred) == np.sign(yt))[nz])) if nz.sum() else np.nan
    mean_pnl = float(np.mean(trade_pnl))
    std_pnl = float(np.std(trade_pnl))
    # candidate density: every valid candle is a candidate -> trades_per_year is the
    # full candle cadence (matches the runner's every-candle scan).
    sharpe = (mean_pnl / std_pnl * np.sqrt(candidates_per_year)) if std_pnl > 0 else np.nan
    wins = trade_pnl[trade_pnl > 0]
    losses = trade_pnl[trade_pnl < 0]
    win_rate = float(len(wins) / len(trade_pnl)) if len(trade_pnl) else np.nan
    avg_win = float(np.mean(wins)) if len(wins) else np.nan
    avg_loss = float(np.mean(losses)) if len(losses) else np.nan
    payoff = float(avg_win / abs(avg_loss)) if avg_loss not in (0, np.nan) and not np.isnan(avg_loss) else np.nan
    if np.std(pred) > 0 and np.std(yt) > 0:
        score_ic = float(spearmanr(pred, yt).correlation)
    else:
        score_ic = np.nan
    return {"dir_acc": dir_acc, "score_ic": score_ic, "sharpe": sharpe,
            "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss,
            "payoff": payoff, "mean_pnl": mean_pnl, "n_oof": int(len(yt))}


def main() -> None:
    assert PARQUET.exists(), f"parquet not found: {PARQUET}"
    df_full = pd.read_parquet(PARQUET)
    assert "open_time" in df_full.columns, "open_time column missing"

    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr = close * natr / 100.0

    is_months = (df["open_time"].max() - df["open_time"].min()) / (1000 * 60 * 60 * 24 * 30.44)

    # Validate feature presence
    feature_arrays: dict[str, np.ndarray] = {}
    for name, cols in FEATURE_SETS.items():
        present = [c for c in cols if c in df.columns]
        miss = [c for c in cols if c not in df.columns]
        assert not miss, f"feature set {name} missing cols: {miss}"
        feature_arrays[name] = df[present].to_numpy(dtype=np.float64)

    print("=" * 92)
    print(f"IS-ONLY label x feature-set SHARPE-PROXY grid — {SYMBOL} {INTERVAL}")
    print(f"IS rows (open_time < {OOS_CUTOFF_MS} = 2025-03-24): {n_is}")
    print(f"IS window: {pd.to_datetime(df['open_time'].min(), unit='ms')} .. "
          f"{pd.to_datetime(df['open_time'].max(), unit='ms')}")
    print(f"ATR={ATR_COLUMN}*close/100; fee={FEE_PCT}%; purged 5-fold CV, 3-bar embargo")
    print("SHARPE = mean(trade_pnl)/std(trade_pnl)*sqrt(3*365.25)  [risk-adjusted, the objective]")
    print("=" * 92)

    # Label configs: CURRENT + EXPANDED-timeout (the iter-009 thesis) + wider-TP + fh.
    label_configs = [
        ("tb_2.9/1.45_to21 (CURRENT/7d)", "tb", dict(tp=2.9, sl=1.45, to=21)),
        ("tb_2.9/1.45_to42 (14d)", "tb", dict(tp=2.9, sl=1.45, to=42)),
        ("tb_2.9/1.45_to63 (21d)", "tb", dict(tp=2.9, sl=1.45, to=63)),
        ("tb_4.0/1.45_to42 (wide-tp,14d)", "tb", dict(tp=4.0, sl=1.45, to=42)),
        ("tb_4.0/2.0_to42 (wide2:1,14d)", "tb", dict(tp=4.0, sl=2.0, to=42)),
        ("tb_5.0/1.75_to63 (wide,21d)", "tb", dict(tp=5.0, sl=1.75, to=63)),
        ("tb_6.0/2.0_to63 (wide3:1,21d)", "tb", dict(tp=6.0, sl=2.0, to=63)),
        ("fh_N9 (3d)", "fh", dict(horizon=9)),
        ("fh_N21 (7d)", "fh", dict(horizon=21)),
        ("fh_N42 (14d)", "fh", dict(horizon=42)),
    ]

    rows = []
    for lname, lmode, lkw in label_configs:
        if lmode == "tb":
            long_ret = _atr_tb_long_return(high, low, close, atr, lkw["tp"], lkw["sl"], lkw["to"])
        else:
            long_ret = _fh_long_return(close, lkw["horizon"])
        valid = np.isfinite(long_ret)
        n_valid = int(valid.sum())
        trades_per_month = n_valid / is_months if is_months > 0 else np.nan
        # label oracle Sharpe ceiling (perfect-direction): |long_ret| net fee already in
        oracle = np.abs(long_ret[valid])
        oracle_sharpe = (np.mean(oracle) / np.std(oracle) * np.sqrt(CANDLES_PER_YEAR)
                         if np.std(oracle) > 0 else np.nan)
        for fs_name, X in feature_arrays.items():
            cv = _purged_cv_sharpe(X, long_ret, valid, CANDLES_PER_YEAR)
            rows.append({
                "label_config": lname, "feature_set": fs_name, "n_valid": n_valid,
                "trades/mo": trades_per_month, "oracle_sharpe": oracle_sharpe,
                "oof_dir_acc": cv["dir_acc"], "oof_score_ic": cv["score_ic"],
                "oof_SHARPE": cv["sharpe"], "win_rate": cv["win_rate"],
                "avg_win%": cv["avg_win"], "avg_loss%": cv["avg_loss"],
                "payoff_w/l": cv["payoff"], "mean_pnl%": cv["mean_pnl"],
            })

    res = pd.DataFrame(rows)

    print("\n[A] FULL GRID — oof_SHARPE is the objective (risk-adjusted, IS-only)")
    print("-" * 92)
    with pd.option_context("display.width", 240, "display.max_rows", 200,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(res[["label_config", "feature_set", "oof_SHARPE", "oof_dir_acc",
                   "win_rate", "payoff_w/l", "mean_pnl%", "trades/mo",
                   "oracle_sharpe"]].to_string(index=False))

    print("\n[B] BEST cells by oof_SHARPE (the objective)")
    print("-" * 92)
    top = res.sort_values("oof_SHARPE", ascending=False).head(12)
    with pd.option_context("display.width", 240,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(top[["label_config", "feature_set", "oof_SHARPE", "oof_dir_acc",
                   "payoff_w/l", "mean_pnl%", "trades/mo"]].to_string(index=False))

    print("\n[C] Feature-set marginal — mean oof_SHARPE across all label configs")
    print("-" * 92)
    for fs_name in FEATURE_SETS:
        sub = res[res["feature_set"] == fs_name]
        print(f"  {fs_name:26s} mean_SHARPE={sub['oof_SHARPE'].mean():+.4f}  "
              f"max_SHARPE={sub['oof_SHARPE'].max():+.4f}  "
              f"mean_dir_acc={sub['oof_dir_acc'].mean():.4f}  "
              f"#(SHARPE>0)={int((sub['oof_SHARPE'] > 0).sum())}/{len(sub)}")

    print("\n[D] Label-horizon marginal — mean oof_SHARPE across all feature sets")
    print("-" * 92)
    for lname, _, _ in label_configs:
        sub = res[res["label_config"] == lname]
        print(f"  {lname:32s} mean_SHARPE={sub['oof_SHARPE'].mean():+.4f}  "
              f"max_SHARPE={sub['oof_SHARPE'].max():+.4f}  "
              f"oracle={sub['oracle_sharpe'].iloc[0]:+.3f}")

    cur = res[(res["label_config"].str.contains("CURRENT")) &
              (res["feature_set"] == "LONG_prune(34)")].iloc[0]
    print("\n[E] ANCHOR: CURRENT label x LONG prune (the incumbent BTC specialist proxy)")
    print(f"    oof_SHARPE={cur['oof_SHARPE']:+.4f}  dir_acc={cur['oof_dir_acc']:.4f}  "
          f"payoff={cur['payoff_w/l']:+.3f}  mean_pnl%={cur['mean_pnl%']:+.4f}")
    print("    (iter-008 anchor: CURRENT x LONG OOF econ -0.2398%/cand, dir_acc 0.4886)")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "label_feature_sharpe_grid.csv"
    res.to_csv(out, index=False)
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
