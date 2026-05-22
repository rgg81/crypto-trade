"""iter-v3/118 — T9 multivariate-LIFT screen for C3 (the high-importance,
no-univariate-signal candidate).

C3_ema_signed_volregime: T3 univariate AUC = 0.4977 (FAIL, p=0.61)
but T5 multivariate importance ranks 8-10/15 with gain 37-63% of top across
all 3 symbols (the highest of all 6 candidates). The R²<0.50 LR-PF clears.

Question: does adding C3 to the 14-feature stack lift multivariate AUC despite
the univariate AUC being null? Could be:
(a) genuine interaction signal — the multivariate model uses C3 in conjunction
    with other features at a deeper split layer than univariate captures
(b) noise inflation — the LightGBM allocates splits to C3 but they don't
    improve OOF AUC (similar to /085 funding_regime_momentum)
(c) gain-rank artifact — high gain at training time can still produce no OOF
    discriminative advantage if the splits overfit
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

C3 = "C3_ema_signed_volregime"


def _multivariate_lgbm_auc(panel: pd.DataFrame, feat_cols: list[str]) -> tuple[float, list[float]]:
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


def main() -> None:
    print(f"[main] /118 T9 multivariate-LIFT screen for {C3} — START")
    panels = {sym: build_labeled_panel(sym) for sym in SYMBOLS}
    rows = []
    for sym, panel in panels.items():
        base_auc, base_folds = _multivariate_lgbm_auc(panel, list(V3_FEATURE_COLUMNS))
        plus_auc, plus_folds = _multivariate_lgbm_auc(panel, list(V3_FEATURE_COLUMNS) + [C3])
        rows.append({
            "scope": sym,
            "baseline_14f_auc": base_auc,
            "with_15f_auc": plus_auc,
            "auc_lift": plus_auc - base_auc,
            "base_per_fold": ";".join(f"{v:+.3f}" for v in base_folds),
            "plus_per_fold": ";".join(f"{v:+.3f}" for v in plus_folds),
            "lift_pass_003": (plus_auc - base_auc) >= 0.003,
        })
        print(f"[T9] {sym} baseline={base_auc:.4f} | +C3={plus_auc:.4f} | LIFT={plus_auc-base_auc:+.4f}")
    pooled = pd.concat(panels.values(), axis=0, ignore_index=True)
    base_auc, base_folds = _multivariate_lgbm_auc(pooled, list(V3_FEATURE_COLUMNS))
    plus_auc, plus_folds = _multivariate_lgbm_auc(pooled, list(V3_FEATURE_COLUMNS) + [C3])
    rows.append({
        "scope": "POOLED",
        "baseline_14f_auc": base_auc,
        "with_15f_auc": plus_auc,
        "auc_lift": plus_auc - base_auc,
        "base_per_fold": ";".join(f"{v:+.3f}" for v in base_folds),
        "plus_per_fold": ";".join(f"{v:+.3f}" for v in plus_folds),
        "lift_pass_003": (plus_auc - base_auc) >= 0.005,
    })
    print(f"[T9] POOLED baseline={base_auc:.4f} | +C3={plus_auc:.4f} | LIFT={plus_auc-base_auc:+.4f}")
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T9_c3_multivariate_lift_screen.csv"
    df.to_csv(out, index=False)
    print(f"[T9] wrote {out}")
    print()
    print("=" * 78)
    print("[T9 SUMMARY]")
    print(df.to_string(index=False))


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    main()
