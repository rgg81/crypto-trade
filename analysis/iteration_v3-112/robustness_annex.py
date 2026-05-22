"""iter-v3/112 gating EDA — robustness annex for the pooled-vs-per-symbol axis.

The horse race (pooled_vs_persymbol_horse_race.py) measures the held-out AUC of
the pooled vs per-symbol architectures. This annex adds three controls the /109
chain proved are needed before a verdict on a v3 model-architecture axis:

  A. Permutation null on the per-symbol architecture. v3's feature->label AUC
     sits near 0.50 (the /109 finding); an eyeballed "pooled beats per-symbol by
     +0.012" is meaningless without knowing the no-signal band. T7 permutes the
     training-fold labels, refits the per-symbol arm, re-scores — if the real-
     label per-symbol AUC sits inside the no-signal band, then there is no
     directional signal for EITHER architecture to extract and the axis is
     NULL-AT-EDA territory (/109 Lesson 2).

  B. Gated-tail edge. The horse-race AUC is a BROAD-population statistic over
     every candle. /059 only TRADES the gated tail — the high-confidence
     signals. /109's reconciliation showed broad AUC ~0.50 yet the production
     book has a real (geometry-carried) edge. T8 asks the production-relevant
     question: does pooling improve the directional hit rate of the
     HIGH-CONFIDENCE tail (top-quartile |proba-0.5|)? A gated-tail lift can
     exist even when the broad-AUC lift is thin — and the gated tail is what the
     Phase-6 backtest actually trades.

  C. Sample-starvation gradient. The /111 diary's MECHANISM claim is that
     per-symbol models fail BECAUSE the per-symbol sample is thin. T9 tests the
     claim directly: it correlates each per-symbol fold's held-out AUC with that
     fold's training-sample size. If per-symbol AUC rises with sample size, the
     starvation mechanism is real and pooling (which removes the starvation) has
     a credible lever. If per-symbol AUC is FLAT in sample size, the starvation
     story is not supported and the pooled hypothesis loses its mechanism.

NO CHEATING — strict IS-only invariant inherited from _shared.py.

Outputs T7-T9 + T10 (annex verdict) under analysis/iteration_v3-112/.
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

OUT = "analysis/iteration_v3-112"
EMBARGO_MS = EMBARGO_CANDLES * INTERVAL_MINUTES * 60 * 1000
N_PERMUTATIONS = 100
PERM_SEED = 42  # single-seed for the permutation null (matched to /109's T8)


def _fit_lgbm(Xtr, ytr, Xte, seed):
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


def _ensemble_proba(Xtr, ytr, Xte, seeds=(42, 123, 456, 789, 1001)):
    return np.mean([_fit_lgbm(Xtr, ytr, Xte, s) for s in seeds], axis=0)


def run() -> None:
    df = load_labeled_is()
    folds = make_time_aligned_folds(df, n_folds=8)
    print(f"[annex] {len(df)} IS candles, {len(folds)} time-aligned folds")

    # ============================================================
    # T7 — permutation null on the PER-SYMBOL architecture
    # ============================================================
    # Pool the real-label per-symbol predictions across all (symbol, fold) cells
    # for the observed AUC; then the 100-shuffle null on the same cells.
    real_y, real_p = [], []
    perm_aucs = []

    rng = np.random.default_rng(PERM_SEED)

    # collect per-(symbol,fold) train/test slices once
    cells = []
    for fk, (test_start, test_end) in enumerate(folds):
        train_end = test_start - EMBARGO_MS
        for sym in SYMBOLS:
            tr = df[(df["close_time"] < train_end) & (df["symbol"] == sym)]
            te = df[
                (df["close_time"] >= test_start)
                & (df["close_time"] < test_end)
                & (df["symbol"] == sym)
            ]
            if len(te) < 5 or len(tr) < 30:
                continue
            ytr = (tr["label"].to_numpy() == 1).astype(int)
            yte = (te["label"].to_numpy() == 1).astype(int)
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                continue
            Xtr = tr[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            Xte = te[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            cells.append((Xtr, ytr, Xte, yte))

    # observed (real-label) per-symbol AUC — single-seed=42 to match the null
    for Xtr, ytr, Xte, yte in cells:
        p = _fit_lgbm(Xtr, ytr, Xte, PERM_SEED)
        real_y.append(yte)
        real_p.append(p)
    observed_auc = roc_auc_score(np.concatenate(real_y), np.concatenate(real_p))

    # 100-shuffle null — permute the TRAINING labels, refit, re-score
    for _ in range(N_PERMUTATIONS):
        py, pp = [], []
        for Xtr, ytr, Xte, yte in cells:
            ytr_shuf = rng.permutation(ytr)
            if len(np.unique(ytr_shuf)) < 2:
                ytr_shuf = ytr  # degenerate guard
            p = _fit_lgbm(Xtr, ytr_shuf, Xte, PERM_SEED)
            py.append(yte)
            pp.append(p)
        perm_aucs.append(roc_auc_score(np.concatenate(py), np.concatenate(pp)))

    perm_aucs = np.array(perm_aucs)
    perm_p = float((perm_aucs >= observed_auc).mean())
    t7 = pd.DataFrame(
        [
            dict(
                observed_per_symbol_auc=round(observed_auc, 4),
                perm_null_mean=round(float(perm_aucs.mean()), 4),
                perm_null_q05=round(float(np.quantile(perm_aucs, 0.05)), 4),
                perm_null_q50=round(float(np.quantile(perm_aucs, 0.50)), 4),
                perm_null_q95=round(float(np.quantile(perm_aucs, 0.95)), 4),
                permutation_p_value=round(perm_p, 4),
                n_cells=len(cells),
                n_permutations=N_PERMUTATIONS,
            )
        ]
    )
    t7.to_csv(f"{OUT}/T7_per_symbol_permutation_null.csv", index=False)

    # ============================================================
    # T8 — gated-tail directional hit rate: pooled vs per-symbol
    # ============================================================
    # For each architecture, take the top-quartile-confidence test predictions
    # (largest |proba - 0.5|) and measure the directional hit rate.
    gated_rows = []
    for fk, (test_start, test_end) in enumerate(folds):
        train_end = test_start - EMBARGO_MS
        pooled_train = df[df["close_time"] < train_end]
        pooled_test = df[
            (df["close_time"] >= test_start) & (df["close_time"] < test_end)
        ]
        if len(pooled_train) < 30:
            continue
        ytr_p = (pooled_train["label"].to_numpy() == 1).astype(int)
        if len(np.unique(ytr_p)) < 2:
            continue
        Xtr_p = pooled_train[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        Xte_p = pooled_test[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        proba_pooled = _ensemble_proba(Xtr_p, ytr_p, Xte_p)
        pooled_test = pooled_test.assign(_pp=proba_pooled)

        for sym in SYMBOLS:
            sym_train = pooled_train[pooled_train["symbol"] == sym]
            sym_test = pooled_test[pooled_test["symbol"] == sym]
            if len(sym_test) < 8 or len(sym_train) < 30:
                continue
            ytr_s = (sym_train["label"].to_numpy() == 1).astype(int)
            if len(np.unique(ytr_s)) < 2:
                continue
            Xtr_s = sym_train[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            Xte_s = sym_test[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            proba_persym = _ensemble_proba(Xtr_s, ytr_s, Xte_s)
            yte = (sym_test["label"].to_numpy() == 1).astype(int)

            for arch, p in (("pooled", sym_test["_pp"].to_numpy()), ("per_symbol", proba_persym)):
                conf = np.abs(p - 0.5)
                if len(conf) < 4:
                    continue
                thresh = np.quantile(conf, 0.75)
                tail = conf >= thresh
                if tail.sum() == 0:
                    continue
                pred_dir = (p[tail] >= 0.5).astype(int)
                hit = (pred_dir == yte[tail]).mean()
                gated_rows.append(
                    dict(
                        symbol=sym,
                        fold=fk,
                        architecture=arch,
                        gated_hit_rate=hit,
                        gated_n=int(tail.sum()),
                    )
                )
    t8_raw = pd.DataFrame(gated_rows)
    t8 = (
        t8_raw.groupby("architecture")
        .apply(
            lambda g: pd.Series(
                {
                    "weighted_gated_hit_rate": np.average(
                        g["gated_hit_rate"], weights=g["gated_n"]
                    ),
                    "mean_gated_hit_rate": g["gated_hit_rate"].mean(),
                    "total_gated_n": int(g["gated_n"].sum()),
                    "n_cells": len(g),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    t8.to_csv(f"{OUT}/T8_gated_tail_hit_rate.csv", index=False)

    # ============================================================
    # T9 — sample-starvation gradient: does per-symbol AUC rise with sample size?
    # ============================================================
    # Reconstruct per-(symbol,fold) per-symbol AUC + training-sample size, then
    # correlate. A positive Spearman = the starvation mechanism is real.
    grad_rows = []
    for fk, (test_start, test_end) in enumerate(folds):
        train_end = test_start - EMBARGO_MS
        for sym in SYMBOLS:
            tr = df[(df["close_time"] < train_end) & (df["symbol"] == sym)]
            te = df[
                (df["close_time"] >= test_start)
                & (df["close_time"] < test_end)
                & (df["symbol"] == sym)
            ]
            if len(te) < 5 or len(tr) < 30:
                continue
            ytr = (tr["label"].to_numpy() == 1).astype(int)
            yte = (te["label"].to_numpy() == 1).astype(int)
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                continue
            Xtr = tr[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            Xte = te[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            p = _ensemble_proba(Xtr, ytr, Xte)
            grad_rows.append(
                dict(
                    symbol=sym,
                    fold=fk,
                    per_symbol_train_n=len(tr),
                    per_symbol_auc=roc_auc_score(yte, p),
                )
            )
    grad = pd.DataFrame(grad_rows)
    rho, pval = spearmanr(grad["per_symbol_train_n"], grad["per_symbol_auc"])
    # also the pooled comparison: pooled train n is always larger
    t9 = pd.DataFrame(
        [
            dict(
                spearman_rho_trainN_vs_auc=round(float(rho), 4),
                spearman_p_value=round(float(pval), 4),
                n_cells=len(grad),
                mean_per_symbol_auc=round(float(grad["per_symbol_auc"].mean()), 4),
                min_train_n=int(grad["per_symbol_train_n"].min()),
                max_train_n=int(grad["per_symbol_train_n"].max()),
                interpretation=(
                    "positive rho => starvation mechanism SUPPORTED"
                    if rho > 0.15
                    else "flat/negative rho => starvation mechanism NOT supported"
                ),
            )
        ]
    )
    t9.to_csv(f"{OUT}/T9_sample_starvation_gradient.csv", index=False)
    grad.to_csv(f"{OUT}/T9_raw_per_cell.csv", index=False)

    # ============================================================
    # T10 — annex verdict
    # ============================================================
    perm_signal = observed_auc > np.quantile(perm_aucs, 0.95)
    gated_pooled = float(
        t8.loc[t8["architecture"] == "pooled", "weighted_gated_hit_rate"].iloc[0]
    )
    gated_persym = float(
        t8.loc[t8["architecture"] == "per_symbol", "weighted_gated_hit_rate"].iloc[0]
    )
    t10 = pd.DataFrame(
        [
            dict(
                control="A_permutation_null",
                finding=f"observed per-symbol AUC {observed_auc:.4f} vs null q95 "
                f"{np.quantile(perm_aucs, 0.95):.4f}, p={perm_p:.3f}",
                signal_present=bool(perm_signal),
            ),
            dict(
                control="B_gated_tail",
                finding=f"gated-tail hit rate: pooled {gated_pooled:.4f} vs "
                f"per-symbol {gated_persym:.4f} (lift {gated_pooled - gated_persym:+.4f})",
                signal_present=bool(gated_pooled > gated_persym),
            ),
            dict(
                control="C_sample_starvation_gradient",
                finding=f"Spearman rho(train_n, per-symbol AUC) = {rho:.4f}, p={pval:.3f}",
                signal_present=bool(rho > 0.15),
            ),
        ]
    )
    t10.to_csv(f"{OUT}/T10_annex_verdict.csv", index=False)

    print("\n=== T7 per-symbol permutation null ===")
    print(t7.to_string(index=False))
    print("\n=== T8 gated-tail directional hit rate ===")
    print(t8.to_string(index=False))
    print("\n=== T9 sample-starvation gradient ===")
    print(t9.to_string(index=False))
    print("\n=== T10 annex verdict ===")
    print(t10.to_string(index=False))


if __name__ == "__main__":
    run()
