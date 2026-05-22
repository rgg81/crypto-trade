"""iter-v3/108 — Gating EDA Script 2 of 2. THE DECISIVE GO/NO-GO TEST.

Question: can a depth-4 LightGBM trained ONLY on the 18 disjoint meta-features
(verified zero-overlap with V3_FEATURE_COLUMNS by script 1) separate the
primary model's IS WINNERS from its IS LOSERS — IS-only?

If yes (held-out AUC >= 0.60, sub-period stable) -> the meta-label has
IS-detectable separating power that /017's redundant feature set could not
access -> GO.
If no (AUC < 0.60 or unstable) -> the primary model's errors are unpredictable
from orthogonal information -> meta-labeling is genuinely dead -> NULL-AT-EDA.

This is the F-AUC falsifier.

Method (matches the dispatch spec exactly):
  - roster   : /059 IS trade roster (171 trades), target = is_winner (net_pnl>0)
  - features : the 18 disjoint meta-features, joined to each trade's ENTRY bar
               (open_time) — causal, bar t uses only data <= t
  - model    : LightGBM depth-4 binary classifier (the v3 architecture depth)
  - split    : chronological 70/30 (NO shuffle) — train = oldest 70%,
               validation = newest 30%
  - metric   : ROC-AUC on the held-out 30%
  - stability: AUC re-computed on 3 disjoint chronological IS sub-periods

STRICTLY IS-ONLY. Asserts (trades.open_time < OOS_CUTOFF_MS).all() and joins
features whose own bar is < OOS_CUTOFF_MS. The post-cutoff OOS roster is
NEVER read.

Outputs (committed):
  T4_meta_model_auc.csv          — headline: 70/30 held-out AUC + train AUC
  T5_subperiod_stability.csv     — AUC across 3 chronological IS sub-periods
  T6_meta_feature_importance.csv — which disjoint features the meta-model used
  T7_threshold_tradeoff.csv      — trades kept vs win-rate lift at M2 thresholds
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score

# --- sacred constant -------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 ; IMMUTABLE

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FEAT_DIR = REPO / "data" / "features_v3"
TRADES = REPO / "reports-v3" / "iteration_v3-059" / "in_sample" / "trades.csv"
V3_SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]

# The 18 disjoint meta-features — IDENTICAL to script 1's pruned catalog.
META_FEATURES = [
    "hurst_200",
    "adx_14",
    "btc_vol_14d",
    "cross_asset_divergence_norm",
    "vol_regime_x_momentum",
    "vol_transition_slope_20",
    "atr_pct_rank_200",
    "bb_width_pct_rank_100",
    "parkinson_gk_ratio_20",
    "volume_cv_50",
    "range_efficiency_50",
    "taker_buy_imbalance_20",
    "obv_slope_50",
    "funding_rate_zscore_30",
    "funding_sign_persist_9",
    "basis_zscore_30",
    "candle_dow_sin",
    "candle_dow_cos",
]

# the v3 inner-ensemble seeds — the meta-model is averaged over them so the
# AUC is not a single-seed lottery (the gating EDA's own robustness check).
SEEDS = [42, 123, 456, 789, 1001]


def build_dataset() -> pd.DataFrame:
    """Join the 18 disjoint meta-features onto each /059 IS trade entry bar."""
    trades = pd.read_csv(TRADES)
    # IS-ONLY INVARIANT — hard assert.
    assert (trades["open_time"] < OOS_CUTOFF_MS).all(), "trades roster has OOS leak"
    trades["is_winner"] = (trades["net_pnl_pct"] > 0).astype(int)

    # JOIN KEY: trade.open_time == feature bar's close_time (verified 83/83 BCH).
    # The trade enters at a candle's CLOSE; that candle's trailing-window
    # features are the causal signal known at the entry instant. Joining on
    # close_time is the correct causal join (bar t uses only data <= t).
    feat_frames = {}
    for sym in V3_SYMBOLS:
        df = pd.read_parquet(FEAT_DIR / f"{sym}_8h_features.parquet")
        df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
        assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: OOS leak in features"
        # close_time is unique per symbol — safe index
        feat_frames[sym] = df.set_index("close_time")

    rows = []
    unmatched = 0
    for _, tr in trades.iterrows():
        sym = tr["symbol"]
        ot = tr["open_time"]  # == entry-candle close_time
        fdf = feat_frames[sym]
        if ot not in fdf.index:
            unmatched += 1
            continue
        frow = fdf.loc[ot]
        # the feature bar's own close must be IS — causal + IS-only
        assert ot < OOS_CUTOFF_MS, "feature bar OOS"
        rec = {"symbol": sym, "open_time": ot, "is_winner": tr["is_winner"]}
        for mf in META_FEATURES:
            rec[mf] = frow[mf]
        rows.append(rec)

    ds = pd.DataFrame(rows).sort_values("open_time").reset_index(drop=True)
    print(f"[build] joined {len(ds)}/{len(trades)} trades to entry-bar features "
          f"({unmatched} unmatched)")
    print(f"[build] winners={ds['is_winner'].sum()} losers={(1-ds['is_winner']).sum()} "
          f"WR={ds['is_winner'].mean():.4f}")
    # NaN audit — early-history bars may lack long-lookback features
    na = ds[META_FEATURES].isna().sum()
    if na.sum() > 0:
        print(f"[build] NaN per feature (LightGBM handles natively):\n{na[na > 0]}")
    return ds


def fit_auc(ds: pd.DataFrame, train_idx, val_idx, label: str) -> dict:
    """Fit the depth-4 LightGBM meta-model, seed-averaged, return AUC pair."""
    X = ds[META_FEATURES]
    y = ds["is_winner"]
    Xtr, ytr = X.iloc[train_idx], y.iloc[train_idx]
    Xva, yva = X.iloc[val_idx], y.iloc[val_idx]

    if yva.nunique() < 2 or ytr.nunique() < 2:
        return {"split": label, "n_train": len(train_idx), "n_val": len(val_idx),
                "train_auc": np.nan, "val_auc": np.nan,
                "note": "degenerate (single class in a fold)"}

    tr_preds, va_preds = [], []
    for seed in SEEDS:
        clf = LGBMClassifier(
            objective="binary",
            max_depth=4,
            n_estimators=200,
            learning_rate=0.05,
            num_leaves=15,
            min_child_samples=10,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            is_unbalance=True,
            random_state=seed,
            n_jobs=1,
            verbose=-1,
        )
        clf.fit(Xtr, ytr)
        tr_preds.append(clf.predict_proba(Xtr)[:, 1])
        va_preds.append(clf.predict_proba(Xva)[:, 1])
    tr_p = np.mean(tr_preds, axis=0)
    va_p = np.mean(va_preds, axis=0)
    return {
        "split": label,
        "n_train": len(train_idx),
        "n_val": len(val_idx),
        "val_winners": int(yva.sum()),
        "val_losers": int((1 - yva).sum()),
        "train_auc": round(roc_auc_score(ytr, tr_p), 4),
        "val_auc": round(roc_auc_score(yva, va_p), 4),
        "note": "",
    }


def main() -> int:
    ds = build_dataset()
    n = len(ds)

    # ---- T4: headline chronological 70/30 held-out AUC -------------------
    cut = int(n * 0.70)
    headline = fit_auc(ds, list(range(cut)), list(range(cut, n)), "chrono_70_30")
    t4 = pd.DataFrame([headline])
    t4.to_csv(OUT / "T4_meta_model_auc.csv", index=False)
    print(f"\n[T4] chronological 70/30: train_auc={headline['train_auc']} "
          f"HELD-OUT val_auc={headline['val_auc']} "
          f"(val: {headline.get('val_winners')}W / {headline.get('val_losers')}L)")

    # ---- T5: sub-period stability (3 disjoint chronological thirds) ------
    # each third is itself split 70/30 chrono; we report the held-out AUC of
    # each third — the F-AUC stability check.
    stab_rows = []
    thirds = np.array_split(np.arange(n), 3)
    for i, idx in enumerate(thirds):
        idx = list(idx)
        sub_cut = int(len(idx) * 0.70)
        if sub_cut < 10 or len(idx) - sub_cut < 5:
            stab_rows.append({"split": f"sub_period_{i+1}", "n_train": sub_cut,
                              "n_val": len(idx) - sub_cut, "train_auc": np.nan,
                              "val_auc": np.nan, "note": "too few trades"})
            continue
        r = fit_auc(ds, idx[:sub_cut], idx[sub_cut:], f"sub_period_{i+1}")
        ot_lo = ds.iloc[idx[0]]["open_time"]
        ot_hi = ds.iloc[idx[-1]]["open_time"]
        r["open_time_lo"] = ot_lo
        r["open_time_hi"] = ot_hi
        stab_rows.append(r)
    t5 = pd.DataFrame(stab_rows)
    t5.to_csv(OUT / "T5_subperiod_stability.csv", index=False)
    print("[T5] sub-period held-out AUC:")
    for _, r in t5.iterrows():
        print(f"     {r['split']}: val_auc={r['val_auc']} "
              f"(n_val={r['n_val']}) {r.get('note', '')}")

    # ---- T6: meta-feature importance (full-roster fit) -------------------
    X, y = ds[META_FEATURES], ds["is_winner"]
    imp_acc = np.zeros(len(META_FEATURES))
    for seed in SEEDS:
        clf = LGBMClassifier(
            objective="binary", max_depth=4, n_estimators=200,
            learning_rate=0.05, num_leaves=15, min_child_samples=10,
            subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
            is_unbalance=True, random_state=seed, n_jobs=1, verbose=-1,
        )
        clf.fit(X, y)
        imp_acc += clf.feature_importances_
    t6 = pd.DataFrame(
        {"meta_feature": META_FEATURES, "gain_importance": imp_acc / len(SEEDS)}
    ).sort_values("gain_importance", ascending=False)
    t6.to_csv(OUT / "T6_meta_feature_importance.csv", index=False)
    print(f"[T6] top-5 meta-features: "
          f"{t6.head(5)['meta_feature'].tolist()}")

    # ---- T7: threshold trade-off (informational; F-RATE context) --------
    # Using the held-out 30% fold's seed-averaged proba, sweep M2 thresholds:
    # how many trades kept, and the win-rate of the kept set.
    val_idx = list(range(cut, n))
    Xva = ds[META_FEATURES].iloc[val_idx]
    yva = ds["is_winner"].iloc[val_idx]
    va_preds = []
    Xtr_full, ytr_full = ds[META_FEATURES].iloc[:cut], ds["is_winner"].iloc[:cut]
    for seed in SEEDS:
        clf = LGBMClassifier(
            objective="binary", max_depth=4, n_estimators=200,
            learning_rate=0.05, num_leaves=15, min_child_samples=10,
            subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
            is_unbalance=True, random_state=seed, n_jobs=1, verbose=-1,
        )
        clf.fit(Xtr_full, ytr_full)
        va_preds.append(clf.predict_proba(Xva)[:, 1])
    va_p = np.mean(va_preds, axis=0)
    base_wr = yva.mean()
    thr_rows = []
    for thr in [0.40, 0.45, 0.50, 0.55, 0.60]:
        keep = va_p >= thr
        n_keep = int(keep.sum())
        wr_keep = float(yva[keep].mean()) if n_keep > 0 else np.nan
        thr_rows.append({
            "m2_threshold": thr,
            "n_kept": n_keep,
            "n_total": len(yva),
            "frac_kept": round(n_keep / len(yva), 3),
            "wr_kept": round(wr_keep, 4) if n_keep > 0 else np.nan,
            "wr_base": round(base_wr, 4),
            "wr_lift": round(wr_keep - base_wr, 4) if n_keep > 0 else np.nan,
        })
    t7 = pd.DataFrame(thr_rows)
    t7.to_csv(OUT / "T7_threshold_tradeoff.csv", index=False)
    print("[T7] threshold trade-off (held-out fold): see CSV")

    # ---- F-AUC verdict ----------------------------------------------------
    print()
    print("=" * 64)
    print("F-AUC falsifier (GO bar: held-out AUC >= 0.60 AND sub-period stable):")
    held = headline["val_auc"]
    sub_aucs = [r["val_auc"] for _, r in t5.iterrows()
                if pd.notna(r["val_auc"])]
    print(f"  headline held-out AUC : {held}")
    print(f"  sub-period AUCs       : {sub_aucs}")
    auc_pass = pd.notna(held) and held >= 0.60
    # stability: all sub-period AUCs above the 0.50 no-skill line AND
    # the spread modest (no sub-period collapses below 0.50).
    stab_pass = len(sub_aucs) >= 2 and all(a >= 0.50 for a in sub_aucs)
    if auc_pass and stab_pass:
        print("  -> F-AUC does NOT fire. Meta-label has IS-detectable "
              "separating power. GO.")
    else:
        reason = []
        if not auc_pass:
            reason.append(f"held-out AUC {held} < 0.60")
        if not stab_pass:
            reason.append("sub-period AUC unstable / below 0.50")
        print(f"  -> F-AUC FIRES ({'; '.join(reason)}). "
              "Meta-labeling is genuinely dead. NULL-AT-EDA.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
