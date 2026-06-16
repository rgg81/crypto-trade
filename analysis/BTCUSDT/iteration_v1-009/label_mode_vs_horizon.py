"""IS-ONLY disentangling probe: LABEL MODE vs HORIZON — BTCUSDT iter-v1/009.

FE Phase 4. The Sharpe grid showed the CURRENT triple-barrier(7d) cell is negative
while expanded-horizon and fixed_horizon cells flip positive. Two confounded levers:
  (a) LABEL MODE  — triple_barrier (first TP/SL hit) vs fixed_horizon (sign of N-candle
                    forward return). fixed_horizon lets the full hold run with NO early
                    TP/SL truncation, which is exactly the "let winners run" thesis.
  (b) HORIZON     — number of candles the trade is held / scanned.

This script holds the HYBRID feature set fixed and crosses {mode} x {horizon} at MATCHED
horizons so the marginal effect of each lever is isolated:
  horizon in {21 (7d), 42 (14d), 63 (21d)} x mode in {triple_barrier 2.9/1.45, fixed_horizon}.
Multi-seed (n=6) Sharpe proxy so the comparison is not a single-seed artifact.

OOS-VIGILANCE (HARD): IS-only filter + leak guard; forward labels on IS slice only;
tail NaN-masks. Reads ONLY the BTC 8h parquet. Never modifies src/. Never touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-009/label_mode_vs_horizon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

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
SEEDS = (42, 123, 456, 789, 1001, 2002)

from label_feature_sharpe_grid import (  # noqa: E402
    FS_HYBRID,
    _atr_tb_long_return,
    _fh_long_return,
)


def _cv_sharpe_seed(X, long_ret, valid, seed, folds=5, embargo=3):
    idx = np.where(valid)[0]
    Xm, ym = X[idx], long_ret[idx]
    n = len(idx)
    fold_size = n // folds
    preds, ys = [], []
    for k in range(1, folds):
        tr_end = k * fold_size
        te_start = tr_end + embargo
        te_end = min((k + 1) * fold_size, n)
        if te_start >= te_end:
            continue
        mdl = lgb.LGBMRegressor(
            n_estimators=200, max_depth=4, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=seed, bagging_seed=seed,
            feature_fraction_seed=seed, n_jobs=2, verbose=-1)
        mdl.fit(Xm[:tr_end], ym[:tr_end])
        preds.append(mdl.predict(Xm[te_start:te_end]))
        ys.append(ym[te_start:te_end])
    pred = np.concatenate(preds)
    yt = np.concatenate(ys)
    tp = np.sign(pred) * yt
    mu, sd = float(np.mean(tp)), float(np.std(tp))
    sh = (mu / sd * np.sqrt(CANDLES_PER_YEAR)) if sd > 0 else np.nan
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
    cols = [c for c in FS_HYBRID if c in df.columns]
    X = df[cols].to_numpy(dtype=np.float64)

    print("=" * 88)
    print(f"IS-ONLY LABEL-MODE vs HORIZON probe (HYBRID feature set) — {SYMBOL} {INTERVAL}")
    print(f"IS rows: {len(df)}; seeds={SEEDS}; matched-horizon mode crossing")
    print("=" * 88)

    horizons = [21, 42, 63]
    rows = []
    for to in horizons:
        # triple_barrier at current geometry 2.9/1.45
        lr_tb = _atr_tb_long_return(high, low, close, atr, 2.9, 1.45, to)
        # fixed_horizon at the SAME candle count
        lr_fh = _fh_long_return(close, to)
        for mode, lr in (("triple_barrier_2.9/1.45", lr_tb), ("fixed_horizon", lr_fh)):
            valid = np.isfinite(lr)
            shs, das = [], []
            for s in SEEDS:
                sh, da = _cv_sharpe_seed(X, lr, valid, s)
                shs.append(sh)
                das.append(da)
            shs = np.array(shs)
            rows.append({
                "horizon_cand": to, "horizon_days": to / 3.0, "mode": mode,
                "mean_SHARPE": float(np.mean(shs)), "spread": float(shs.max() - shs.min()),
                "min_SHARPE": float(shs.min()), "max_SHARPE": float(shs.max()),
                "mean_dir_acc": float(np.mean(das)), "frac_pos": float(np.mean(shs > 0)),
            })

    res = pd.DataFrame(rows)
    print("\n[A] MODE x HORIZON Sharpe proxy (HYBRID set, n=%d seeds)" % len(SEEDS))
    print("-" * 88)
    with pd.option_context("display.width", 220,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(res.to_string(index=False))

    print("\n[B] Marginal of LABEL MODE at matched horizon (fixed_horizon - triple_barrier)")
    print("-" * 88)
    for to in horizons:
        tb = res[(res["horizon_cand"] == to) & (res["mode"].str.startswith("triple"))].iloc[0]
        fh = res[(res["horizon_cand"] == to) & (res["mode"] == "fixed_horizon")].iloc[0]
        print(f"  h={to:2d}c ({to/3:.0f}d): fixed_horizon {fh['mean_SHARPE']:+.3f} vs "
              f"triple_barrier {tb['mean_SHARPE']:+.3f}  "
              f"Δ(mode)={fh['mean_SHARPE'] - tb['mean_SHARPE']:+.3f}")

    print("\n[C] Marginal of HORIZON within each mode (vs 21c/7d baseline horizon)")
    print("-" * 88)
    for mode in ("triple_barrier_2.9/1.45", "fixed_horizon"):
        base = res[(res["horizon_cand"] == 21) & (res["mode"] == mode)].iloc[0]["mean_SHARPE"]
        for to in horizons:
            cur = res[(res["horizon_cand"] == to) & (res["mode"] == mode)].iloc[0]["mean_SHARPE"]
            print(f"  {mode:26s} h={to:2d}c: {cur:+.3f}  Δ(vs 21c)={cur - base:+.3f}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "label_mode_vs_horizon.csv"
    res.to_csv(out, index=False)
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
