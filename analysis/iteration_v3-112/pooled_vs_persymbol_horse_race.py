"""iter-v3/112 gating EDA — DECISIVE TEST: pooled vs per-symbol model horse race.

The /111 diary's diagnosis of v3's recurring universe-iteration failure: v3 has
trained ONE LightGBM per symbol for all 111 iterations; each per-symbol model
gets only ~50-75 IS trades and ~18-22 OOS trades — a thin sample the 35-trial
Optuna search overfits IS and fails to transfer OOS. The /111 IS-non-fit (the
Optuna search could not even fit the IS book) is the sharpest case.

A POOLED model — ONE LightGBM trained on the concatenated BCH+LDO+TRX panel —
trains on N× the effective sample. It is the orthogonal structural response to
per-symbol sample starvation. This is cycle-6 EXPLORATION #3, menu item 2.

The axis question is cleanly EDA-gateable. The held-out predictive AUC of a
pooled model vs the per-symbol models on the IDENTICAL walk-forward folds, on
the IDENTICAL 14 features, against the IDENTICAL /059 triple-barrier label, IS
the answer. No src/ change and no backtest is needed to size the expected
effect.

Method (strictly IS-only, walk-forward-faithful, TIME-ALIGNED):
  * 8 expanding-window walk-forward folds defined on the GLOBAL IS calendar
    (shared time axis — see _shared.make_time_aligned_folds). Both architectures
    train on ``close_time < test_start - 22-candle embargo`` and are scored on
    the SAME calendar test window — so the comparison is not confounded by
    calendar misalignment.
  * Per fold, fit TWO architectures, BOTH 5-seed-averaged (v3 inner-ensemble):
      POOLED      = ONE LightGBM trained on the concatenated 3-symbol training
                    panel; predictions scored per symbol.
      PER-SYMBOL  = THREE LightGBMs, each trained on one symbol's training rows
                    only; the v3 incumbent architecture.
  * The model class, hyperparameters, feature stack, label, embargo, and seed
    ensemble are IDENTICAL between the two arms — the ONLY varied thing is the
    training panel (3-symbol pooled vs 1-symbol).
  * Held-out metrics per (symbol, fold): ROC-AUC, accuracy, rank-IC (Spearman of
    predicted P(up) vs signed best_edge).

GO bar (pre-registered): the POOLED architecture beats PER-SYMBOL on the pooled
held-out AUC by a material margin (>= +0.010) AND is positive in >= 2 of 3
chronological IS thirds. A material, stable held-out-AUC lift is the signal that
sample pooling extracts a sharper edge — and is the GO basis for the Phase-6
pooled-architecture backtest.

Outputs T1-T6 under analysis/iteration_v3-112/.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score

import lightgbm as lgb

from _shared import (
    EMBARGO_CANDLES,
    INTERVAL_MINUTES,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    load_labeled_is,
    make_time_aligned_folds,
)

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

SEEDS = (42, 123, 456, 789, 1001)  # the v3 5-seed inner ensemble
OUT = "analysis/iteration_v3-112"
EMBARGO_MS = EMBARGO_CANDLES * INTERVAL_MINUTES * 60 * 1000  # 22 candles in ms

# Pre-registered GO bar
GO_MIN_AUC_LIFT = 0.010
GO_MIN_POSITIVE_THIRDS = 2


def _fit_lgbm(Xtr, ytr, Xte, seed):
    """LightGBM at the v3 depth-3-5 representation. ytr in {0,1}.

    Hyperparameters match analysis/iteration_v3-109/model_class_horse_race.py
    (max_depth=4 = midpoint of the v3 depth-3-5 Optuna band) so the EDA is
    comparable to the /109 model-class horse race. The hyperparameters are
    IDENTICAL between the pooled and per-symbol arms — the only varied input is
    the training panel.
    """
    m = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=4,
        num_leaves=31,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=20,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=seed,
        n_jobs=1,
        verbose=-1,
    )
    m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]


def _ensemble_proba(Xtr, ytr, Xte):
    """5-seed averaged P(up) — the v3 inner-ensemble protocol."""
    probas = [_fit_lgbm(Xtr, ytr, Xte, s) for s in SEEDS]
    return np.mean(probas, axis=0)


def run() -> None:
    df = load_labeled_is()
    print(f"[IS-only] loaded {len(df)} labeled IS candles across {SYMBOLS}")
    for sym in SYMBOLS:
        s = df[df["symbol"] == sym]
        print(
            f"  {sym}: {len(s)} candles, "
            f"label +1 frac = {(s['label'] == 1).mean():.3f}, "
            f"close_time {s['close_time'].min()}..{s['close_time'].max()}"
        )

    folds = make_time_aligned_folds(df, n_folds=8)
    print(f"\n[walk-forward] {len(folds)} time-aligned folds on the global IS calendar")

    fold_rows = []  # T1 — per (symbol, fold, architecture) held-out metrics
    sample_rows = []  # T6 — per (symbol, fold) training-sample sizes (the mechanism)

    for fk, (test_start, test_end) in enumerate(folds):
        train_end = test_start - EMBARGO_MS

        # ---- POOLED arm: ONE model on the concatenated 3-symbol training panel
        pooled_train = df[df["close_time"] < train_end]
        pooled_test = df[
            (df["close_time"] >= test_start) & (df["close_time"] < test_end)
        ]
        Xtr_p = pooled_train[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        ytr_p = (pooled_train["label"].to_numpy() == 1).astype(int)
        if len(np.unique(ytr_p)) < 2 or len(pooled_train) < 30:
            continue
        Xte_p = pooled_test[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        proba_pooled_all = _ensemble_proba(Xtr_p, ytr_p, Xte_p)
        pooled_test = pooled_test.assign(_proba_pooled=proba_pooled_all)

        # ---- PER-SYMBOL arm: THREE models, one per symbol's training rows
        for sym in SYMBOLS:
            sym_train = pooled_train[pooled_train["symbol"] == sym]
            sym_test = pooled_test[pooled_test["symbol"] == sym]
            if len(sym_test) < 5:
                continue
            yte = (sym_test["label"].to_numpy() == 1).astype(int)
            if len(np.unique(yte)) < 2:
                continue
            edge_te = sym_test["best_edge"].to_numpy() * np.sign(
                sym_test["label"].to_numpy()
            )

            # pooled prediction restricted to this symbol's test rows
            p_pooled = sym_test["_proba_pooled"].to_numpy()

            # per-symbol model
            Xtr_s = sym_train[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            ytr_s = (sym_train["label"].to_numpy() == 1).astype(int)
            Xte_s = sym_test[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            if len(np.unique(ytr_s)) < 2 or len(sym_train) < 30:
                continue
            p_persym = _ensemble_proba(Xtr_s, ytr_s, Xte_s)

            for arch, p in (("pooled", p_pooled), ("per_symbol", p_persym)):
                auc = roc_auc_score(yte, p)
                acc = ((p >= 0.5).astype(int) == yte).mean()
                ic = spearmanr(p, edge_te).correlation
                fold_rows.append(
                    dict(
                        symbol=sym,
                        fold=fk,
                        architecture=arch,
                        auc=auc,
                        acc=acc,
                        ic=ic if ic == ic else 0.0,
                        n_test=len(sym_test),
                    )
                )
            sample_rows.append(
                dict(
                    symbol=sym,
                    fold=fk,
                    pooled_train_n=len(pooled_train),
                    per_symbol_train_n=len(sym_train),
                    sample_multiplier=round(len(pooled_train) / max(1, len(sym_train)), 2),
                    n_test=len(sym_test),
                )
            )

    t1 = pd.DataFrame(fold_rows)
    t1.to_csv(f"{OUT}/T1_per_fold_metrics.csv", index=False)

    # T2 — pooled (all symbols, all folds) held-out metric per architecture
    t2 = (
        t1.groupby("architecture")
        .agg(
            mean_auc=("auc", "mean"),
            median_auc=("auc", "median"),
            mean_acc=("acc", "mean"),
            mean_ic=("ic", "mean"),
            n_cells=("auc", "count"),
        )
        .reset_index()
    )
    base_auc = t2.loc[t2["architecture"] == "per_symbol", "mean_auc"].iloc[0]
    t2["auc_lift_vs_per_symbol"] = t2["mean_auc"] - base_auc
    t2 = t2.sort_values("mean_auc", ascending=False)
    t2.to_csv(f"{OUT}/T2_pooled_aggregate.csv", index=False)

    # T3 — per-symbol mean held-out AUC per architecture (symbol-consistency)
    t3 = t1.pivot_table(
        index="symbol", columns="architecture", values="auc", aggfunc="mean"
    )
    t3["pooled_minus_per_symbol"] = t3["pooled"] - t3["per_symbol"]
    t3.to_csv(f"{OUT}/T3_per_symbol_auc.csv")

    # T4 — sub-period stability: split the folds into 3 chronological thirds,
    # report the pooled-minus-per-symbol AUC lift within each third.
    sub_rows = []
    max_fold = int(t1["fold"].max())
    thirds = [
        (0, max_fold // 3),
        (max_fold // 3 + 1, 2 * max_fold // 3),
        (2 * max_fold // 3 + 1, max_fold),
    ]
    for third, (lo, hi) in enumerate(thirds):
        seg = t1[(t1["fold"] >= lo) & (t1["fold"] <= hi)]
        a_pooled = seg[seg["architecture"] == "pooled"]["auc"].mean()
        a_persym = seg[seg["architecture"] == "per_symbol"]["auc"].mean()
        sub_rows.append(
            dict(
                third=third,
                fold_lo=lo,
                fold_hi=hi,
                pooled_auc=a_pooled,
                per_symbol_auc=a_persym,
                lift=a_pooled - a_persym,
            )
        )
    t4 = pd.DataFrame(sub_rows)
    t4.to_csv(f"{OUT}/T4_subperiod_stability.csv", index=False)

    # T5 — the GO/NO-GO verdict table
    pooled_lift = t2.loc[
        t2["architecture"] == "pooled", "auc_lift_vs_per_symbol"
    ].iloc[0]
    n_pos_thirds = int((t4["lift"] > 0).sum())
    g_material = bool(pooled_lift >= GO_MIN_AUC_LIFT)
    g_stable = bool(n_pos_thirds >= GO_MIN_POSITIVE_THIRDS)
    # rank-IC corroboration
    ic_pooled = t2.loc[t2["architecture"] == "pooled", "mean_ic"].iloc[0]
    ic_persym = t2.loc[t2["architecture"] == "per_symbol", "mean_ic"].iloc[0]
    t5 = pd.DataFrame(
        [
            dict(
                pooled_auc_lift_vs_per_symbol=round(float(pooled_lift), 4),
                positive_thirds=n_pos_thirds,
                gate_material_lift_ge_0p010=g_material,
                gate_stable_2of3_thirds=g_stable,
                pooled_mean_ic=round(float(ic_pooled), 4),
                per_symbol_mean_ic=round(float(ic_persym), 4),
                ic_lift=round(float(ic_pooled - ic_persym), 4),
                verdict="GO" if (g_material and g_stable) else "NO-GO",
            )
        ]
    )
    t5.to_csv(f"{OUT}/T5_go_nogo_verdict.csv", index=False)

    # T6 — training-sample sizes: the MECHANISM. By how much does pooling expand
    # the effective training sample? This sizes the structural lever.
    t6 = pd.DataFrame(sample_rows)
    t6_summary = (
        t6.groupby("symbol")
        .agg(
            mean_pooled_train_n=("pooled_train_n", "mean"),
            mean_per_symbol_train_n=("per_symbol_train_n", "mean"),
            mean_sample_multiplier=("sample_multiplier", "mean"),
            min_per_symbol_train_n=("per_symbol_train_n", "min"),
        )
        .reset_index()
    )
    t6_summary.to_csv(f"{OUT}/T6_sample_sizes.csv", index=False)

    print("\n=== T2 pooled held-out architecture metrics ===")
    print(t2.to_string(index=False))
    print("\n=== T3 per-symbol held-out AUC ===")
    print(t3.to_string())
    print("\n=== T4 sub-period stability (pooled - per_symbol AUC lift) ===")
    print(t4.to_string(index=False))
    print("\n=== T5 GO/NO-GO verdict ===")
    print(t5.to_string(index=False))
    print("\n=== T6 training-sample sizes (the mechanism) ===")
    print(t6_summary.to_string(index=False))


if __name__ == "__main__":
    run()
