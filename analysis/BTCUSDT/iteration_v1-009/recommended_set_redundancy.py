"""IS-ONLY recommended-set redundancy + IC matrix + final Sharpe — BTCUSDT iter-v1/009.

FE Phase 4. Records the FINAL recommended iter-009 feature set (19-col cluster-pruned
HYBRID short+regime) with:
  * its IS univariate IC vs forward 9-candle (3d) and 21-candle (7d) log returns,
  * the within-set Spearman |IC| correlation matrix (cluster-importance redundancy),
  * the multi-seed purged-CV Sharpe proxy under the recommended label (fixed_horizon
    N=21 / 7d) and the alternate (triple_barrier 2.9/1.45 to42 / 14d),
so every column in the recommendation is backed by a committed number.

OOS-VIGILANCE (HARD): IS-only filter + leak guard; forward labels on IS slice only;
tail NaN-masks. Reads ONLY the BTC 8h parquet. Never modifies src/. Never touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-009/recommended_set_redundancy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_HERE))

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = _REPO_ROOT / "data/features" / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"
OUTDIR = _HERE
CANDLES_PER_YEAR = 365.25 * 3
SEEDS = (42, 123, 456, 789, 1001, 2002, 3003, 4004)

from label_feature_sharpe_grid import _atr_tb_long_return, _fh_long_return  # noqa: E402

# FINAL recommended iter-009 feature set: 19-col cluster-pruned HYBRID.
# Dropped from the 23-col probe set: vol_natr_7 + vol_parkinson_10 (Spearman |corr|
# 0.92-0.99 with vol_garman_klass_10 — keep one realized-vol estimator); mr_rsi_extreme_7
# + cusum_norm_1s (near-inert <0.5% gain at fh_N9). 14 NEW short-window cols + 5 retained
# regime/funding anchors carried over from PRUNED-48.
RECOMMENDED: tuple[str, ...] = (
    # --- short-window (higher-frequency) additions: 11 cols ---
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10",
    # --- long-horizon regime/funding anchors (peak |IC| at h=21): 8 cols ---
    "trend_adx_14", "trend_supertrend_14_3", "btc_funding_spread_30_90",
    "funding_rate_zscore_30", "stat_autocorr_lag5", "vol_range_spike_72",
    "mr_rsi_extreme_14", "stat_kurtosis_20",
)


def _fwd_log_return(close, h):
    n = len(close)
    out = np.full(n, np.nan)
    if h < n:
        out[: n - h] = (np.log(close[h:]) - np.log(close[: n - h])) * 100.0
    return out


def _ic(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 200 or np.nanstd(x[m]) == 0:
        return np.nan
    return float(spearmanr(x[m], y[m]).correlation)


def _cv_sharpe(X, lr, seed, folds=5, embargo=3):
    valid = np.isfinite(lr)
    idx = np.where(valid)[0]
    Xm, ym = X[idx], lr[idx]
    n = len(idx)
    fs = n // folds
    pr, ys = [], []
    for k in range(1, folds):
        te = k * fs + embargo
        en = min((k + 1) * fs, n)
        if te >= en:
            continue
        m = lgb.LGBMRegressor(
            n_estimators=200, max_depth=4, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=seed, bagging_seed=seed,
            feature_fraction_seed=seed, n_jobs=2, verbose=-1)
        m.fit(Xm[: k * fs], ym[: k * fs])
        pr.append(m.predict(Xm[te:en]))
        ys.append(ym[te:en])
    pred = np.concatenate(pr)
    yt = np.concatenate(ys)
    tp = np.sign(pred) * yt
    sd = float(np.std(tp))
    sh = (np.mean(tp) / sd * np.sqrt(CANDLES_PER_YEAR)) if sd > 0 else np.nan
    nz = yt != 0
    da = float(np.mean((np.sign(pred) == np.sign(yt))[nz])) if nz.sum() else np.nan
    return sh, da


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr = close * natr / 100.0
    cols = list(RECOMMENDED)
    for c in cols:
        assert c in df.columns, f"recommended col missing from parquet: {c}"
    X = df[cols].to_numpy(dtype=np.float64)

    fwd9 = _fwd_log_return(close, 9)
    fwd21 = _fwd_log_return(close, 21)

    print("=" * 88)
    print(f"IS-ONLY recommended-set redundancy + Sharpe — {SYMBOL} {INTERVAL}")
    print(f"IS rows: {len(df)}; recommended set: {len(cols)} cols")
    print("=" * 88)

    print("\n[A] PER-COLUMN univariate IC (3d / 7d fwd log return) + NaN%")
    print("-" * 88)
    rows = []
    for c in cols:
        x = df[c].to_numpy(dtype=np.float64)
        rows.append({"feature": c, "ic_h9_3d": _ic(x, fwd9), "ic_h21_7d": _ic(x, fwd21),
                     "nan%": float(np.isnan(x).mean() * 100)})
    icdf = pd.DataFrame(rows)
    with pd.option_context("display.width", 200, "display.float_format", lambda v: f"{v:+.4f}"):
        print(icdf.to_string(index=False))

    print("\n[B] WITHIN-SET Spearman |corr| > 0.65 (cluster-importance redundancy audit)")
    print("-" * 88)
    cm = df[cols].corr(method="spearman")
    found = False
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            cc = cm.iloc[i, j]
            if abs(cc) > 0.65:
                found = True
                print(f"  {cols[i]:28s} {cols[j]:28s} {cc:+.3f}")
    if not found:
        print("  (none > 0.65 — set is cluster-de-duplicated)")

    print("\n[C] MULTI-SEED Sharpe proxy of the recommended set (n=%d seeds)" % len(SEEDS))
    print("-" * 88)
    for lname, lr in (
        ("fixed_horizon N21 (7d) [RECOMMENDED]", _fh_long_return(close, 21)),
        ("fixed_horizon N9 (3d) [alt]", _fh_long_return(close, 9)),
        ("triple_barrier 2.9/1.45 to42 (14d) [alt]",
         _atr_tb_long_return(high, low, close, atr, 2.9, 1.45, 42)),
        ("triple_barrier 2.9/1.45 to21 (7d) [CURRENT anchor]",
         _atr_tb_long_return(high, low, close, atr, 2.9, 1.45, 21)),
    ):
        shs, das = zip(*[_cv_sharpe(X, lr, s) for s in SEEDS])
        shs = np.array(shs)
        flag = "BASIN-LOTTERY(mag)" if (shs.max() - shs.min()) > 0.50 else "STABLE"
        sign = "SIGN-ROBUST" if np.all(shs > 0) else ("SIGN-NEG" if np.all(shs < 0) else "SIGN-MIXED")
        print(f"  {lname:48s} mean={shs.mean():+.3f} spread={shs.max()-shs.min():.3f} "
              f"min={shs.min():+.3f} dir_acc={np.mean(das):.4f} frac_pos={np.mean(shs>0):.2f} "
              f"[{flag}/{sign}]")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    icdf.to_csv(OUTDIR / "recommended_set_ic.csv", index=False)
    cm.to_csv(OUTDIR / "recommended_set_corr_matrix.csv")
    print(f"\nWrote: {OUTDIR / 'recommended_set_ic.csv'}")
    print(f"Wrote: {OUTDIR / 'recommended_set_corr_matrix.csv'}")


if __name__ == "__main__":
    main()
