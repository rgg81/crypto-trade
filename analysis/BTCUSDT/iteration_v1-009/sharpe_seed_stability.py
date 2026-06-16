"""IS-ONLY multi-seed Sharpe-proxy stability for the iter-v1/009 top cells — BTCUSDT.

FE Phase 4 trial-stability / basin pre-check. The single-seed Sharpe grid
(label_feature_sharpe_grid.py) identified a small set of top (feature_set, label)
cells. Before recommending an iter-009 config the FE must predict LOTTERY RISK:
cross-seed Sharpe-proxy dispersion. v1's basin-lottery rule downgrades a verdict if
the per-seed spread > 0.50. This script re-runs the purged-CV Sharpe proxy across
N seeds (LightGBM random_state + bagging variation) for the candidate cells and
reports mean / std / min / max / spread.

It also reports LightGBM feature importance (gain) for the WINNING cell so the
recommended column list is evidence-based (which features actually carry split-share).

OOS-VIGILANCE (HARD): IS-only filter with leak guard; forward labels on IS slice only;
tail NaN-masks. Reads ONLY the BTC 8h parquet. Never modifies src/. Never touches OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-009/sharpe_seed_stability.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

# Resolve repo root from this script's location so the script is runnable from any cwd
# (the import below + the parquet path are anchored to repo root, not the caller's cwd).
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[2]  # analysis/BTCUSDT/iteration_v1-009 -> repo root
sys.path.insert(0, str(_HERE))

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = _REPO_ROOT / "data/features" / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
OUTDIR = _HERE
CANDLES_PER_YEAR = 365.25 * 3
SEEDS = (42, 123, 456, 789, 1001, 2002, 3003, 4004)

# Reuse the exact feature sets + label fns from label_feature_sharpe_grid.py
from label_feature_sharpe_grid import (  # noqa: E402
    FS_HYBRID,
    FS_LONG,
    FS_SHORT,
    _atr_tb_long_return,
    _fh_long_return,
)

FEATURE_SETS = {
    "LONG_prune(34)": FS_LONG,
    "SHORT_pure(36)": FS_SHORT,
    "HYBRID_short+regime(23)": FS_HYBRID,
}

# Top candidate cells to stress (from grid [B]) + the CURRENT/anchor for contrast.
CANDIDATE_CELLS = [
    ("HYBRID_short+regime(23)", "fh", dict(horizon=9), "fh_N9 (3d)"),
    ("LONG_prune(34)", "fh", dict(horizon=9), "fh_N9 (3d)"),
    ("SHORT_pure(36)", "fh", dict(horizon=9), "fh_N9 (3d)"),
    ("HYBRID_short+regime(23)", "fh", dict(horizon=21), "fh_N21 (7d)"),
    ("HYBRID_short+regime(23)", "tb", dict(tp=2.9, sl=1.45, to=42), "tb_2.9/1.45_to42 (14d)"),
    ("LONG_prune(34)", "tb", dict(tp=2.9, sl=1.45, to=42), "tb_2.9/1.45_to42 (14d)"),
    ("LONG_prune(34)", "tb", dict(tp=6.0, sl=2.0, to=63), "tb_6.0/2.0_to63 (21d)"),
    ("HYBRID_short+regime(23)", "tb", dict(tp=2.9, sl=1.45, to=21), "tb CURRENT/7d (anchor)"),
    ("LONG_prune(34)", "tb", dict(tp=2.9, sl=1.45, to=21), "tb CURRENT/7d (anchor)"),
]


def _purged_cv_sharpe_seed(X, long_ret, valid, seed, folds=5, embargo=3):
    idx = np.where(valid)[0]
    Xm, ym = X[idx], long_ret[idx]
    n = len(idx)
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
            subsample=0.8, colsample_bytree=0.8, random_state=seed, bagging_seed=seed,
            feature_fraction_seed=seed, n_jobs=2, verbose=-1)
        mdl.fit(Xm[:tr_end], ym[:tr_end])
        all_pred.append(mdl.predict(Xm[te_start:te_end]))
        all_y.append(ym[te_start:te_end])
    pred = np.concatenate(all_pred)
    yt = np.concatenate(all_y)
    trade_pnl = np.sign(pred) * yt
    mean_pnl, std_pnl = float(np.mean(trade_pnl)), float(np.std(trade_pnl))
    sharpe = (mean_pnl / std_pnl * np.sqrt(CANDLES_PER_YEAR)) if std_pnl > 0 else np.nan
    nz = yt != 0
    dir_acc = float(np.mean((np.sign(pred) == np.sign(yt))[nz])) if nz.sum() else np.nan
    return sharpe, dir_acc


def _full_fit_importance(X, long_ret, valid, cols, seed=42):
    """Train on the full IS slice and return gain-importance ranking (interpretation)."""
    idx = np.where(valid)[0]
    mdl = lgb.LGBMRegressor(
        n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=seed, n_jobs=2, verbose=-1,
        importance_type="gain")
    mdl.fit(X[idx], long_ret[idx])
    imp = mdl.feature_importances_.astype(float)
    tot = imp.sum() if imp.sum() > 0 else 1.0
    return sorted(zip(cols, imp / tot * 100.0), key=lambda t: -t[1])


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr = close * natr / 100.0

    feature_arrays, feature_cols = {}, {}
    for name, cols in FEATURE_SETS.items():
        present = [c for c in cols if c in df.columns]
        feature_arrays[name] = df[present].to_numpy(dtype=np.float64)
        feature_cols[name] = present

    print("=" * 92)
    print(f"IS-ONLY multi-seed Sharpe-proxy stability — {SYMBOL} {INTERVAL}")
    print(f"IS rows: {len(df)}; seeds={SEEDS}")
    print("BASIN-LOTTERY rule: per-seed Sharpe spread (max-min) > 0.50 => verdict downgrade")
    print("=" * 92)

    rows = []
    for fs_name, lmode, lkw, lname in CANDIDATE_CELLS:
        X = feature_arrays[fs_name]
        if lmode == "tb":
            long_ret = _atr_tb_long_return(high, low, close, atr, lkw["tp"], lkw["sl"], lkw["to"])
        else:
            long_ret = _fh_long_return(close, lkw["horizon"])
        valid = np.isfinite(long_ret)
        sharpes, diras = [], []
        for s in SEEDS:
            sh, da = _purged_cv_sharpe_seed(X, long_ret, valid, s)
            sharpes.append(sh)
            diras.append(da)
        sharpes = np.array(sharpes)
        rows.append({
            "label_config": lname, "feature_set": fs_name,
            "mean_SHARPE": float(np.mean(sharpes)), "std_SHARPE": float(np.std(sharpes)),
            "min_SHARPE": float(np.min(sharpes)), "max_SHARPE": float(np.max(sharpes)),
            "spread": float(np.max(sharpes) - np.min(sharpes)),
            "mean_dir_acc": float(np.mean(diras)),
            "frac_pos": float(np.mean(sharpes > 0)),
        })

    res = pd.DataFrame(rows)
    print("\n[A] MULTI-SEED Sharpe-proxy stability (n=%d seeds)" % len(SEEDS))
    print("-" * 92)
    with pd.option_context("display.width", 240,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(res.to_string(index=False))

    print("\n  basin flag: spread>0.50 = BASIN-LOTTERY (downgrade); spread<=0.50 = STABLE")
    for _, r in res.iterrows():
        flag = "BASIN-LOTTERY" if r["spread"] > 0.50 else "STABLE"
        print(f"  {r['feature_set']:26s} {r['label_config']:26s} "
              f"mean={r['mean_SHARPE']:+.3f} spread={r['spread']:.3f} "
              f"frac_pos={r['frac_pos']:.2f} -> {flag}")

    # Importance for the two leading HYBRID cells
    print("\n[B] Feature importance (gain %, full-IS fit) — HYBRID set, fh_N9 label")
    print("-" * 92)
    long_ret_n9 = _fh_long_return(close, 9)
    valid_n9 = np.isfinite(long_ret_n9)
    imp = _full_fit_importance(feature_arrays["HYBRID_short+regime(23)"], long_ret_n9,
                               valid_n9, feature_cols["HYBRID_short+regime(23)"])
    for c, g in imp:
        print(f"  {c:30s} {g:6.2f}%")

    print("\n[C] Feature importance (gain %, full-IS fit) — HYBRID set, tb_2.9/1.45_to42 label")
    print("-" * 92)
    long_ret_to42 = _atr_tb_long_return(high, low, close, atr, 2.9, 1.45, 42)
    valid_to42 = np.isfinite(long_ret_to42)
    imp2 = _full_fit_importance(feature_arrays["HYBRID_short+regime(23)"], long_ret_to42,
                                valid_to42, feature_cols["HYBRID_short+regime(23)"])
    for c, g in imp2:
        print(f"  {c:30s} {g:6.2f}%")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "sharpe_seed_stability.csv"
    res.to_csv(out, index=False)
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
