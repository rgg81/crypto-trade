"""iter-v3/118 — T7 multivariate-LIFT screen, T8 production-importance prediction.

Even though C4_autocorr_signed_hurst clears the universe-pooled univariate AUC
gate (T3 p=0.000), and 2/3 per-symbol g1 gate (BCH 0.5125, TRX 0.5463; LDO
just misses at 0.5042 of 0.51), the production-relevant question is:
    Does adding C4 to the 14-feature stack lift the multivariate walk-forward
    OOF AUC vs the 14-feature baseline?
This is the closest IS-only proxy for "will the production LightGBM use it".

T7: 14-feature baseline AUC vs 14+1 (with C4) AUC, per symbol AND universe-pooled.
    Same walk-forward folds, same depth-4 LightGBM, only the feature set differs.

T8: Side-by-side per-symbol importance — train depth-4 LightGBM on 14+1 with C4,
    record top-5 features per symbol AND record where C4 ranks. This is the
    direct counterfactual to the /085 INERT-by-importance failure pattern.

The decision logic:
- If T7 shows multivariate lift >= 0.005 universe-pooled AND >= 0.003 per-symbol
  on at least 2 of 3 symbols, C4 is the /118 axis.
- Otherwise, document the PROMISING-INERT-RISK and pivot to PATH B per the
  brief Section 7 contingency.

All computations strict IS-only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
from _shared import (  # noqa: E402
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    build_labeled_panel,
    walk_forward_folds,
)

import lightgbm as lgb  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

OUT_DIR = THIS_DIR
RNG_SEED = 1729

CANDIDATE = "C4_autocorr_signed_hurst"  # the T3-clearing candidate from /118 EDA


def _multivariate_lgbm_auc(panel: pd.DataFrame, feat_cols: list[str]) -> tuple[float, list[float]]:
    """Walk-forward OOF AUC for a depth-4 multivariate LightGBM."""
    panel = panel.sort_values("close_time").reset_index(drop=True)
    y = panel["label"].to_numpy(dtype="int64")
    X = panel[feat_cols].to_numpy(dtype="float64")
    mask = ~np.isnan(X).any(axis=1)
    X_in = X[mask]
    y_in = y[mask]
    folds = walk_forward_folds(len(X_in), n_folds=5)
    per_fold = []
    for train_idx, test_idx in folds:
        Xtr, ytr = X_in[train_idx], y_in[train_idx]
        Xte, yte = X_in[test_idx], y_in[test_idx]
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbose": -1,
            "max_depth": 4,
            "num_leaves": 16,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "n_estimators": 300,
            "min_data_in_leaf": 80,
            "lambda_l2": 1.0,
        }
        model = lgb.LGBMClassifier(**params, random_state=RNG_SEED)
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        try:
            per_fold.append(float(roc_auc_score(yte, p)))
        except ValueError:
            continue
    return (float(np.mean(per_fold)) if per_fold else float("nan")), per_fold


def t7_lift(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    # Per-symbol.
    for sym, panel in panels.items():
        base_auc, base_folds = _multivariate_lgbm_auc(panel, list(V3_FEATURE_COLUMNS))
        plus1_auc, plus1_folds = _multivariate_lgbm_auc(
            panel, list(V3_FEATURE_COLUMNS) + [CANDIDATE]
        )
        rows.append({
            "scope": sym,
            "baseline_14f_auc": base_auc,
            "with_15f_auc": plus1_auc,
            "auc_lift": plus1_auc - base_auc,
            "base_per_fold": ";".join(f"{v:+.3f}" for v in base_folds),
            "plus1_per_fold": ";".join(f"{v:+.3f}" for v in plus1_folds),
            "lift_pass_per_sym_003": (plus1_auc - base_auc) >= 0.003,
        })
        print(f"[T7] {sym} baseline AUC={base_auc:.4f} | +C4 AUC={plus1_auc:.4f} | LIFT={plus1_auc-base_auc:+.4f}")
    # Universe-pooled.
    pooled = pd.concat(panels.values(), axis=0, ignore_index=True)
    base_auc, base_folds = _multivariate_lgbm_auc(pooled, list(V3_FEATURE_COLUMNS))
    plus1_auc, plus1_folds = _multivariate_lgbm_auc(
        pooled, list(V3_FEATURE_COLUMNS) + [CANDIDATE]
    )
    rows.append({
        "scope": "POOLED",
        "baseline_14f_auc": base_auc,
        "with_15f_auc": plus1_auc,
        "auc_lift": plus1_auc - base_auc,
        "base_per_fold": ";".join(f"{v:+.3f}" for v in base_folds),
        "plus1_per_fold": ";".join(f"{v:+.3f}" for v in plus1_folds),
        "lift_pass_per_sym_003": (plus1_auc - base_auc) >= 0.005,  # tighter at pooled
    })
    print(f"[T7] POOLED baseline AUC={base_auc:.4f} | +C4 AUC={plus1_auc:.4f} | LIFT={plus1_auc-base_auc:+.4f}")
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T7_multivariate_lift_screen.csv"
    df.to_csv(out, index=False)
    print(f"[T7] wrote {out} ({len(df)} rows)")
    return df


def t8_full_importance_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Full feature-importance table at 14+1 (depth-4) per symbol — predicts production rank."""
    rows = []
    for sym, panel in panels.items():
        panel = panel.sort_values("close_time").reset_index(drop=True)
        y = panel["label"].to_numpy(dtype="int64")
        feat_cols = list(V3_FEATURE_COLUMNS) + [CANDIDATE]
        X = panel[feat_cols].to_numpy(dtype="float64")
        mask = ~np.isnan(X).any(axis=1)
        X_in = X[mask]
        y_in = y[mask]
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbose": -1,
            "max_depth": 4,
            "num_leaves": 16,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "n_estimators": 300,
            "min_data_in_leaf": 80,
            "lambda_l2": 1.0,
        }
        model = lgb.LGBMClassifier(**params, random_state=RNG_SEED)
        model.fit(X_in, y_in, feature_name=feat_cols)
        gains = dict(zip(feat_cols, model.booster_.feature_importance(importance_type="gain")))
        sorted_feats = sorted(gains.items(), key=lambda kv: kv[1], reverse=True)
        top_gain = sorted_feats[0][1] if sorted_feats else 1
        for rank, (feat, gain) in enumerate(sorted_feats, start=1):
            pct = float(gain) / float(top_gain) if top_gain > 0 else 0.0
            rows.append({
                "symbol": sym,
                "rank": rank,
                "feature": feat,
                "gain": float(gain),
                "gain_pct_of_top": pct,
                "is_candidate": feat == CANDIDATE,
            })
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T8_importance_full_table.csv"
    df.to_csv(out, index=False)
    print(f"[T8] wrote {out} ({len(df)} rows)")
    return df


def main() -> None:
    print(f"[main] /118 T7/T8 multivariate-lift screen for {CANDIDATE} — START")
    panels: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        panels[sym] = build_labeled_panel(sym)
        print(f"  [load] {sym}: {len(panels[sym])} labeled rows")
    t7 = t7_lift(panels)
    t8 = t8_full_importance_table(panels)
    print()
    print("=" * 78)
    print("[T7 SUMMARY]")
    print(t7.to_string(index=False))
    print()
    print("[T8 — candidate rank per symbol]")
    print(t8[t8["is_candidate"]].to_string(index=False))


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    main()
