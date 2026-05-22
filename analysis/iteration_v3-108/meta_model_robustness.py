"""iter-v3/108 — Gating EDA Script 3 of 2 (robustness annex to script 2).

Script 2's headline depth-4 / 200-estimator LightGBM produced train_auc=1.0 on
the 119-trade training fold — it memorizes the training set. A NULL verdict
from an over-capacity model could in principle be a CAPACITY artifact (the
model overfits noise IS, so the held-out AUC is deflated below the meta-label's
true separating power).

This annex rules that out. It re-runs the decisive F-AUC test under MULTIPLE
model capacities — from a 1-split stump-depth tree to a logistic-regression
linear baseline — all on the SAME 18 disjoint meta-features, SAME chronological
70/30 split, SAME seed-averaging. If NO capacity setting clears held-out
AUC >= 0.60 with sub-period stability, the NULL is genuine: the meta-label is
not separable from the disjoint features at any model complexity.

Also runs a PERMUTATION control: shuffle is_winner 200x, re-fit, and report the
null-distribution AUC quantiles — so the observed AUC can be read against the
no-signal band.

STRICTLY IS-ONLY (inherits the asserts from build_dataset).

Outputs (committed):
  T8_capacity_sweep.csv      — held-out + sub-period AUC across 5 model capacities
  T9_permutation_null.csv    — permutation-null AUC distribution + observed-vs-null
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# reuse the dataset builder + constants from script 2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from meta_model_auc import META_FEATURES, SEEDS, build_dataset  # noqa: E402

OUT = Path(__file__).resolve().parent


def _split(n: int, frac: float = 0.70):
    cut = int(n * frac)
    return list(range(cut)), list(range(cut, n))


def _auc_lgbm(ds, tr, va, **kw) -> float:
    X, y = ds[META_FEATURES], ds["is_winner"]
    if y.iloc[va].nunique() < 2 or y.iloc[tr].nunique() < 2:
        return np.nan
    preds = []
    for seed in SEEDS:
        clf = LGBMClassifier(
            objective="binary", is_unbalance=True, random_state=seed,
            n_jobs=1, verbose=-1, **kw,
        )
        clf.fit(X.iloc[tr], y.iloc[tr])
        preds.append(clf.predict_proba(X.iloc[va])[:, 1])
    return roc_auc_score(y.iloc[va], np.mean(preds, axis=0))


def _auc_logit(ds, tr, va) -> float:
    X, y = ds[META_FEATURES], ds["is_winner"]
    if y.iloc[va].nunique() < 2 or y.iloc[tr].nunique() < 2:
        return np.nan
    # impute (LightGBM handles NaN natively; logit needs explicit imputation)
    Xtr = X.iloc[tr].fillna(X.iloc[tr].median())
    Xva = X.iloc[va].fillna(X.iloc[tr].median())
    pipe = make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=2000, C=0.5),
    )
    pipe.fit(Xtr, y.iloc[tr])
    return roc_auc_score(y.iloc[va], pipe.predict_proba(Xva)[:, 1])


def main() -> int:
    ds = build_dataset()
    n = len(ds)
    tr, va = _split(n)
    thirds = np.array_split(np.arange(n), 3)

    # ---- T8: capacity sweep ----------------------------------------------
    capacities = [
        ("lgbm_stump_d1_n50", dict(max_depth=1, n_estimators=50,
                                   learning_rate=0.05, num_leaves=2,
                                   min_child_samples=20)),
        ("lgbm_d2_n100", dict(max_depth=2, n_estimators=100,
                              learning_rate=0.05, num_leaves=4,
                              min_child_samples=20, reg_alpha=0.5,
                              reg_lambda=0.5)),
        ("lgbm_d3_n150_reg", dict(max_depth=3, n_estimators=150,
                                  learning_rate=0.03, num_leaves=7,
                                  min_child_samples=15, reg_alpha=0.5,
                                  reg_lambda=0.5, subsample=0.8,
                                  colsample_bytree=0.8)),
        ("lgbm_d4_n200", dict(max_depth=4, n_estimators=200,
                              learning_rate=0.05, num_leaves=15,
                              min_child_samples=10, reg_alpha=0.1,
                              reg_lambda=0.1, subsample=0.8,
                              colsample_bytree=0.8)),
    ]
    rows = []
    for name, kw in capacities:
        held = _auc_lgbm(ds, tr, va, **kw)
        sub = []
        for idx in thirds:
            idx = list(idx)
            c = int(len(idx) * 0.70)
            sub.append(_auc_lgbm(ds, idx[:c], idx[c:], **kw))
        rows.append({
            "model": name,
            "held_out_auc": round(held, 4),
            "sub1_auc": round(sub[0], 4) if pd.notna(sub[0]) else np.nan,
            "sub2_auc": round(sub[1], 4) if pd.notna(sub[1]) else np.nan,
            "sub3_auc": round(sub[2], 4) if pd.notna(sub[2]) else np.nan,
            "min_sub_auc": round(np.nanmin(sub), 4),
        })
    # logistic baseline
    held_l = _auc_logit(ds, tr, va)
    sub_l = []
    for idx in thirds:
        idx = list(idx)
        c = int(len(idx) * 0.70)
        sub_l.append(_auc_logit(ds, idx[:c], idx[c:]))
    rows.append({
        "model": "logistic_C0.5_balanced",
        "held_out_auc": round(held_l, 4),
        "sub1_auc": round(sub_l[0], 4) if pd.notna(sub_l[0]) else np.nan,
        "sub2_auc": round(sub_l[1], 4) if pd.notna(sub_l[1]) else np.nan,
        "sub3_auc": round(sub_l[2], 4) if pd.notna(sub_l[2]) else np.nan,
        "min_sub_auc": round(np.nanmin(sub_l), 4),
    })
    t8 = pd.DataFrame(rows)
    t8.to_csv(OUT / "T8_capacity_sweep.csv", index=False)
    print("[T8] capacity sweep (held-out 30% AUC + 3 sub-period AUCs):")
    for _, r in t8.iterrows():
        print(f"     {r['model']:26s} held={r['held_out_auc']} "
              f"subs=[{r['sub1_auc']}, {r['sub2_auc']}, {r['sub3_auc']}] "
              f"min_sub={r['min_sub_auc']}")
    best_held = t8["held_out_auc"].max()
    # GO requires SOME capacity with held>=0.60 AND all sub-periods >=0.50
    go_rows = t8[(t8["held_out_auc"] >= 0.60) & (t8["min_sub_auc"] >= 0.50)]
    print(f"[T8] best held-out AUC across capacities: {best_held}")
    print(f"[T8] capacities clearing GO bar (held>=0.60 & min_sub>=0.50): "
          f"{len(go_rows)}")

    # ---- T9: permutation null (depth-3 regularized model) ----------------
    X, y = ds[META_FEATURES], ds["is_winner"]
    kw = dict(max_depth=3, n_estimators=150, learning_rate=0.03, num_leaves=7,
              min_child_samples=15, reg_alpha=0.5, reg_lambda=0.5,
              subsample=0.8, colsample_bytree=0.8)
    observed = _auc_lgbm(ds, tr, va, **kw)
    rng = np.random.default_rng(42)
    null_aucs = []
    for _ in range(200):
        yp = y.copy()
        yp.iloc[tr] = rng.permutation(yp.iloc[tr].values)
        if yp.iloc[va].nunique() < 2:
            continue
        clf = LGBMClassifier(objective="binary", is_unbalance=True,
                             random_state=42, n_jobs=1, verbose=-1, **kw)
        clf.fit(X.iloc[tr], yp.iloc[tr])
        null_aucs.append(
            roc_auc_score(y.iloc[va], clf.predict_proba(X.iloc[va])[:, 1])
        )
    null_aucs = np.array(null_aucs)
    p_val = float((null_aucs >= observed).mean())
    t9 = pd.DataFrame([{
        "observed_held_out_auc": round(observed, 4),
        "null_mean_auc": round(null_aucs.mean(), 4),
        "null_q05": round(np.quantile(null_aucs, 0.05), 4),
        "null_q50": round(np.quantile(null_aucs, 0.50), 4),
        "null_q95": round(np.quantile(null_aucs, 0.95), 4),
        "permutation_p_value": round(p_val, 4),
        "n_permutations": len(null_aucs),
    }])
    t9.to_csv(OUT / "T9_permutation_null.csv", index=False)
    r = t9.iloc[0]
    print(f"\n[T9] permutation null (depth-3 reg model, {len(null_aucs)} shuffles):")
    print(f"     observed held-out AUC = {r['observed_held_out_auc']}")
    print(f"     null AUC band: q05={r['null_q05']} q50={r['null_q50']} "
          f"q95={r['null_q95']}")
    print(f"     permutation p-value = {r['permutation_p_value']} "
          f"(observed AUC is {'NOT ' if p_val > 0.05 else ''}"
          f"distinguishable from no-signal)")

    # ---- verdict ----------------------------------------------------------
    print()
    print("=" * 64)
    print("ROBUSTNESS VERDICT:")
    if len(go_rows) == 0:
        print("  NO model capacity (stump -> depth-4 -> logistic) clears the")
        print("  GO bar. The NULL is NOT a capacity artifact — the meta-label")
        print("  is not separable from the 18 disjoint features at any")
        print("  complexity. F-AUC confirmed. NULL-AT-EDA stands.")
    else:
        print(f"  {len(go_rows)} capacity setting(s) clear the GO bar — the")
        print("  headline NULL may be a capacity artifact. RE-EXAMINE.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
