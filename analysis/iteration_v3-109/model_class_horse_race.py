"""iter-v3/109 gating EDA — DECISIVE TEST: model-class horse race.

The /105->/106->/107->/108 convergent chain localized v3's binding constraint
to the primary model's REPRESENTATIONAL CAPACITY — the per-symbol 8h LightGBM
(depth-3-5 trees) on the 14-feature stack. v3's one PROMISING feature ever
(/025 regime_momentum_signed_5d) was a hand-COMPOSED interaction, direct
evidence that depth-3-5 trees fail to compose the interactions that carry
signal.

The dispatch's GO bar: a higher-capacity / different-class model materially AND
sub-period-stably beats the tree's IS predictive performance on the SAME IS
folds. This script is that test.

Method (strictly IS-only, walk-forward-faithful):
  * Per symbol, 8 expanding-window walk-forward folds, embargo-purged by 22
    candles (the /059 embargo). The label is the /059 triple-barrier label.
  * On each fold, fit FOUR model classes on the IDENTICAL 14 features:
      L  = LightGBM, depth-3-5 (the v3 BASELINE — the incumbent representation)
      M  = MLP (sklearn MLPClassifier) — a per-bar neural model: CAN learn
           the deep feature interactions depth-3-5 trees cannot compose
      T  = temporal-window MLP (a TCN proxy): the 14 features over a 4-bar
           lookback flattened to 56 inputs, into an MLP — adds the sequential
           structure a per-bar tree discards
      C  = logistic regression — a linear floor (sanity reference)
  * Held-out predictive metrics per fold: ROC-AUC, accuracy, and the
    rank-IC (Spearman) of the predicted P(up) vs the signed best_edge.
  * GO requires the neural class to BEAT LightGBM materially on the pooled
    held-out AUC AND be sub-period-stable (positive lift in >=2 of 3 IS thirds).

Outputs T1-T6 under analysis/iteration_v3-109/.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb

from _shared import (
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    load_labeled_is,
    make_walk_forward_folds,
)

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

SEEDS = (42, 123, 456, 789, 1001)  # the v3 5-seed inner ensemble
LOOKBACK = 4  # temporal-window depth for the TCN proxy (4 × 8h = 32h context)
OUT = "analysis/iteration_v3-109"


def _fit_lgbm(Xtr, ytr, Xte, seed):
    """LightGBM at the v3 depth-3-5 representation. ytr in {0,1}."""
    m = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=4,  # mid-point of the v3 depth-3-5 Optuna band
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


def _fit_mlp(Xtr, ytr, Xte, seed, hidden=(64, 32)):
    """Per-bar MLP — a neural model class. Standardized inputs (NN-required)."""
    sc = StandardScaler().fit(Xtr)
    m = MLPClassifier(
        hidden_layer_sizes=hidden,
        activation="relu",
        alpha=1e-3,  # L2 — guard the thin v3 sample against overfit
        learning_rate_init=1e-3,
        max_iter=400,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=seed,
    )
    m.fit(sc.transform(Xtr), ytr)
    return m.predict_proba(sc.transform(Xte))[:, 1]


def _fit_logistic(Xtr, ytr, Xte, seed):
    sc = StandardScaler().fit(Xtr)
    m = LogisticRegression(C=0.5, max_iter=500, random_state=seed)
    m.fit(sc.transform(Xtr), ytr)
    return m.predict_proba(sc.transform(Xte))[:, 1]


def _build_temporal(df_sym: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Stack each candle's 14 features over a LOOKBACK window -> 56-dim vector.

    Row t uses features of bars [t-LOOKBACK+1 .. t] — strictly causal (no future
    bar). The first LOOKBACK-1 rows have no full window and are dropped; the
    caller aligns the label array to the same drop.
    """
    feat = df_sym[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    n = len(feat)
    windows = []
    for t in range(LOOKBACK - 1, n):
        windows.append(feat[t - LOOKBACK + 1 : t + 1].flatten())
    return np.asarray(windows), np.arange(LOOKBACK - 1, n)


def _ensemble_proba(fit_fn, Xtr, ytr, Xte, **kw):
    """5-seed averaged P(up) — the v3 inner-ensemble protocol."""
    probas = [fit_fn(Xtr, ytr, Xte, s, **kw) for s in SEEDS]
    return np.mean(probas, axis=0)


def run() -> None:
    df = load_labeled_is()
    print(f"[IS-only] loaded {len(df)} labeled IS candles across {SYMBOLS}")
    for sym in SYMBOLS:
        s = df[df["symbol"] == sym]
        print(f"  {sym}: {len(s)} candles, label +1 frac = {(s['label'] == 1).mean():.3f}")

    fold_rows = []  # T1 — per (symbol, fold, model) held-out metrics
    for sym in SYMBOLS:
        d = df[df["symbol"] == sym].sort_values("close_time").reset_index(drop=True)
        folds = make_walk_forward_folds(d, n_folds=8)
        # temporal representation for the TCN proxy
        Xtemp_all, temp_pos = _build_temporal(d)
        temp_pos_set = {p: i for i, p in enumerate(temp_pos)}

        for fk, (tr_idx, te_idx) in enumerate(folds):
            Xtr = d.iloc[tr_idx][V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            Xte = d.iloc[te_idx][V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            ytr = (d.iloc[tr_idx]["label"].to_numpy() == 1).astype(int)
            yte = (d.iloc[te_idx]["label"].to_numpy() == 1).astype(int)
            edge_te = d.iloc[te_idx]["best_edge"].to_numpy() * np.sign(
                d.iloc[te_idx]["label"].to_numpy()
            )
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                continue

            preds = {}
            preds["L_lgbm"] = _ensemble_proba(_fit_lgbm, Xtr, ytr, Xte)
            preds["M_mlp"] = _ensemble_proba(_fit_mlp, Xtr, ytr, Xte)
            preds["C_logistic"] = _ensemble_proba(_fit_logistic, Xtr, ytr, Xte)

            # temporal model — align fold indices into the windowed representation
            tr_t = [temp_pos_set[p] for p in tr_idx if p in temp_pos_set]
            te_t = [temp_pos_set[p] for p in te_idx if p in temp_pos_set]
            if len(tr_t) > 30 and len(te_t) > 5:
                ytr_t = (d.iloc[[temp_pos[i] for i in tr_t]]["label"].to_numpy() == 1).astype(int)
                yte_t = (d.iloc[[temp_pos[i] for i in te_t]]["label"].to_numpy() == 1).astype(int)
                if len(np.unique(ytr_t)) == 2 and len(np.unique(yte_t)) == 2:
                    p_t = _ensemble_proba(
                        _fit_mlp, Xtemp_all[tr_t], ytr_t, Xtemp_all[te_t], hidden=(96, 48)
                    )
                    auc_t = roc_auc_score(yte_t, p_t)
                    acc_t = ((p_t >= 0.5).astype(int) == yte_t).mean()
                else:
                    auc_t = acc_t = np.nan
            else:
                auc_t = acc_t = np.nan

            for name, p in preds.items():
                auc = roc_auc_score(yte, p)
                acc = ((p >= 0.5).astype(int) == yte).mean()
                ic = spearmanr(p, edge_te).correlation
                fold_rows.append(
                    dict(symbol=sym, fold=fk, model=name, auc=auc, acc=acc,
                         ic=ic, n_test=len(te_idx))
                )
            fold_rows.append(
                dict(symbol=sym, fold=fk, model="T_temporal_mlp", auc=auc_t,
                     acc=acc_t, ic=np.nan, n_test=len(te_t))
            )

    t1 = pd.DataFrame(fold_rows)
    t1.to_csv(f"{OUT}/T1_per_fold_metrics.csv", index=False)

    # T2 — pooled (all symbols, all folds) held-out metric per model class
    t2 = (
        t1.groupby("model")
        .agg(
            mean_auc=("auc", "mean"),
            median_auc=("auc", "mean"),
            mean_acc=("acc", "mean"),
            mean_ic=("ic", "mean"),
            n_folds=("auc", "count"),
        )
        .reset_index()
    )
    base_auc = t2.loc[t2["model"] == "L_lgbm", "mean_auc"].iloc[0]
    t2["auc_lift_vs_lgbm"] = t2["mean_auc"] - base_auc
    t2 = t2.sort_values("mean_auc", ascending=False)
    t2.to_csv(f"{OUT}/T2_pooled_model_class.csv", index=False)

    # T3 — per-symbol mean held-out AUC per model class (symbol-consistency)
    t3 = t1.pivot_table(index="symbol", columns="model", values="auc", aggfunc="mean")
    t3.to_csv(f"{OUT}/T3_per_symbol_auc.csv")

    # T4 — sub-period stability: split the 8 folds into 3 chronological thirds,
    # report each model's AUC lift over LightGBM within each third.
    sub_rows = []
    for sym in SYMBOLS:
        sym_df = t1[t1["symbol"] == sym]
        max_fold = sym_df["fold"].max()
        if pd.isna(max_fold):
            continue
        for third, (lo, hi) in enumerate(
            [(0, max_fold // 3), (max_fold // 3 + 1, 2 * max_fold // 3),
             (2 * max_fold // 3 + 1, max_fold)]
        ):
            seg = sym_df[(sym_df["fold"] >= lo) & (sym_df["fold"] <= hi)]
            base = seg[seg["model"] == "L_lgbm"]["auc"].mean()
            for name in ("M_mlp", "T_temporal_mlp", "C_logistic"):
                v = seg[seg["model"] == name]["auc"].mean()
                sub_rows.append(
                    dict(symbol=sym, third=third, model=name,
                         lgbm_auc=base, model_auc=v, lift=v - base)
                )
    t4 = pd.DataFrame(sub_rows)
    t4.to_csv(f"{OUT}/T4_subperiod_stability.csv", index=False)

    # T5 — the GO/NO-GO verdict table
    verdict_rows = []
    for name in ("M_mlp", "T_temporal_mlp", "C_logistic"):
        row = t2[t2["model"] == name]
        if row.empty:
            continue
        lift = row["auc_lift_vs_lgbm"].iloc[0]
        sub = t4[t4["model"] == name]
        n_pos_thirds = (sub.groupby("third")["lift"].mean() > 0).sum()
        # GO bar: pooled AUC lift >= +0.02 AND positive in >=2 of 3 IS thirds
        g_material = bool(lift >= 0.02)
        g_stable = bool(n_pos_thirds >= 2)
        verdict_rows.append(
            dict(
                model=name,
                pooled_auc_lift_vs_lgbm=round(float(lift), 4),
                positive_thirds=int(n_pos_thirds),
                gate_material_lift_ge_0p02=g_material,
                gate_stable_2of3_thirds=g_stable,
                verdict="GO" if (g_material and g_stable) else "NO-GO",
            )
        )
    t5 = pd.DataFrame(verdict_rows)
    t5.to_csv(f"{OUT}/T5_go_nogo_verdict.csv", index=False)

    # T6 — held-out-fold rank-IC: does the neural class produce a stronger
    # predicted-P(up)-vs-signed-edge IC than the tree?
    t6 = (
        t1[t1["model"].isin(["L_lgbm", "M_mlp", "C_logistic"])]
        .groupby("model")["ic"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    t6.to_csv(f"{OUT}/T6_rank_ic.csv", index=False)

    print("\n=== T2 pooled held-out model-class metrics ===")
    print(t2.to_string(index=False))
    print("\n=== T3 per-symbol held-out AUC ===")
    print(t3.to_string())
    print("\n=== T5 GO/NO-GO verdict ===")
    print(t5.to_string(index=False))
    print("\n=== T6 rank-IC ===")
    print(t6.to_string(index=False))


if __name__ == "__main__":
    run()
