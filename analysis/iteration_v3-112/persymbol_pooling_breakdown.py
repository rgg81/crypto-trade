"""iter-v3/112 gating EDA — per-symbol pooling-effect breakdown.

The horse race (T2-T5) returned a NO-GO at the AGGREGATE level: the pooled-minus-
per-symbol AUC lift is -0.0008, GO bar fails. But T3 surfaced strong per-symbol
HETEROGENEITY: LDO shows a +0.052 pooled AUC lift while BCH/TRX show small
negatives (-0.007 / -0.021). LDO is also the symbol with the thinnest per-symbol
sample (T6: 10.3x pooled-sample multiplier, min 370 training rows vs BCH/TRX's
~1100) AND v3's chronic OOS-weak symbol (BASELINE_V3.md: LDO 5 consecutive
negative CONFIRMATION-class OOS weighted_pnl).

This script asks the SHARP question the aggregate horse race cannot: is the LDO
pooled lift a genuine, isolable, statistically-credible signal — or is it 3-seed
fold noise on a thin symbol? It runs:

  D1. Per-symbol permutation null. For EACH symbol separately, permute the
      training labels, refit per-symbol, re-score — locating each symbol's
      observed pooled AND per-symbol AUC against ITS OWN no-signal band. If LDO's
      pooled AUC clears its own q95 while its per-symbol AUC does not, the LDO
      pooled lift is real signal, not noise.

  D2. Per-symbol gated-tail hit rate, pooled vs per-symbol, broken out by symbol
      (T8 only reported the aggregate). The production-relevant question: does
      pooling lift the high-confidence tail FOR LDO specifically?

  D3. LDO-fold detail: LDO's per-fold pooled vs per-symbol AUC, so the +0.052
      aggregate is decomposed into per-fold contributions (is it one lucky fold
      or a consistent tilt?).

NO CHEATING — strict IS-only invariant inherited from _shared.py.

Outputs T11-T13 + T14 (breakdown verdict) under analysis/iteration_v3-112/.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
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
SEEDS = (42, 123, 456, 789, 1001)
N_PERM = 60  # per-symbol null — 60 shuffles per symbol (3 symbols x 60 = 180 fits)
PERM_SEED = 42


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


def _ens(Xtr, ytr, Xte):
    return np.mean([_fit_lgbm(Xtr, ytr, Xte, s) for s in SEEDS], axis=0)


def run() -> None:
    df = load_labeled_is()
    folds = make_time_aligned_folds(df, n_folds=8)
    print(f"[breakdown] {len(df)} IS candles, {len(folds)} folds")

    # ---- collect per-(symbol,fold) slices: pooled-train, per-symbol-train, test
    per_cell = {sym: [] for sym in SYMBOLS}
    for fk, (test_start, test_end) in enumerate(folds):
        train_end = test_start - EMBARGO_MS
        pooled_train = df[df["close_time"] < train_end]
        if len(pooled_train) < 30:
            continue
        for sym in SYMBOLS:
            sym_tr = pooled_train[pooled_train["symbol"] == sym]
            te = df[
                (df["close_time"] >= test_start)
                & (df["close_time"] < test_end)
                & (df["symbol"] == sym)
            ]
            if len(te) < 5 or len(sym_tr) < 30:
                continue
            ytr_s = (sym_tr["label"].to_numpy() == 1).astype(int)
            ytr_p = (pooled_train["label"].to_numpy() == 1).astype(int)
            yte = (te["label"].to_numpy() == 1).astype(int)
            if (
                len(np.unique(ytr_s)) < 2
                or len(np.unique(ytr_p)) < 2
                or len(np.unique(yte)) < 2
            ):
                continue
            per_cell[sym].append(
                dict(
                    fold=fk,
                    Xtr_s=sym_tr[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64),
                    ytr_s=ytr_s,
                    Xtr_p=pooled_train[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64),
                    ytr_p=ytr_p,
                    Xte=te[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64),
                    yte=yte,
                    best_edge=te["best_edge"].to_numpy(),
                    label=te["label"].to_numpy(),
                )
            )

    # ============================================================
    # D1 — per-symbol permutation null (pooled + per-symbol arms)
    # ============================================================
    rng = np.random.default_rng(PERM_SEED)
    d1_rows = []
    for sym in SYMBOLS:
        cells = per_cell[sym]
        if not cells:
            continue
        # observed (single-seed=42, matched to the null)
        obs_p_y, obs_p_p, obs_s_y, obs_s_p = [], [], [], []
        for c in cells:
            obs_p_y.append(c["yte"])
            obs_p_p.append(_fit_lgbm(c["Xtr_p"], c["ytr_p"], c["Xte"], PERM_SEED))
            obs_s_y.append(c["yte"])
            obs_s_p.append(_fit_lgbm(c["Xtr_s"], c["ytr_s"], c["Xte"], PERM_SEED))
        auc_pooled_obs = roc_auc_score(np.concatenate(obs_p_y), np.concatenate(obs_p_p))
        auc_persym_obs = roc_auc_score(np.concatenate(obs_s_y), np.concatenate(obs_s_p))

        # null — permute per-symbol training labels (the per-symbol arm is what
        # the pooled lift is measured against; the per-symbol null is the band)
        null_aucs = []
        for _ in range(N_PERM):
            ny, npp = [], []
            for c in cells:
                yshuf = rng.permutation(c["ytr_s"])
                if len(np.unique(yshuf)) < 2:
                    yshuf = c["ytr_s"]
                ny.append(c["yte"])
                npp.append(_fit_lgbm(c["Xtr_s"], yshuf, c["Xte"], PERM_SEED))
            null_aucs.append(roc_auc_score(np.concatenate(ny), np.concatenate(npp)))
        null_aucs = np.array(null_aucs)
        d1_rows.append(
            dict(
                symbol=sym,
                auc_per_symbol_obs=round(auc_persym_obs, 4),
                auc_pooled_obs=round(auc_pooled_obs, 4),
                pooled_lift=round(auc_pooled_obs - auc_persym_obs, 4),
                null_q05=round(float(np.quantile(null_aucs, 0.05)), 4),
                null_q50=round(float(np.quantile(null_aucs, 0.50)), 4),
                null_q95=round(float(np.quantile(null_aucs, 0.95)), 4),
                pooled_clears_null_q95=bool(
                    auc_pooled_obs > np.quantile(null_aucs, 0.95)
                ),
                per_symbol_clears_null_q95=bool(
                    auc_persym_obs > np.quantile(null_aucs, 0.95)
                ),
            )
        )
    t11 = pd.DataFrame(d1_rows)
    t11.to_csv(f"{OUT}/T11_per_symbol_permutation_null.csv", index=False)

    # ============================================================
    # D2 — per-symbol gated-tail hit rate, pooled vs per-symbol
    # ============================================================
    d2_rows = []
    for sym in SYMBOLS:
        for c in per_cell[sym]:
            p_pool = _ens(c["Xtr_p"], c["ytr_p"], c["Xte"])
            p_sym = _ens(c["Xtr_s"], c["ytr_s"], c["Xte"])
            for arch, p in (("pooled", p_pool), ("per_symbol", p_sym)):
                conf = np.abs(p - 0.5)
                if len(conf) < 4:
                    continue
                thr = np.quantile(conf, 0.75)
                tail = conf >= thr
                if tail.sum() == 0:
                    continue
                hit = ((p[tail] >= 0.5).astype(int) == c["yte"][tail]).mean()
                d2_rows.append(
                    dict(
                        symbol=sym,
                        fold=c["fold"],
                        architecture=arch,
                        gated_hit_rate=hit,
                        gated_n=int(tail.sum()),
                    )
                )
    d2 = pd.DataFrame(d2_rows)
    t12 = (
        d2.groupby(["symbol", "architecture"])
        .apply(
            lambda g: pd.Series(
                {
                    "weighted_gated_hit_rate": np.average(
                        g["gated_hit_rate"], weights=g["gated_n"]
                    ),
                    "total_gated_n": int(g["gated_n"].sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    t12.to_csv(f"{OUT}/T12_per_symbol_gated_tail.csv", index=False)

    # ============================================================
    # D3 — LDO per-fold detail
    # ============================================================
    d3_rows = []
    for c in per_cell["LDOUSDT"]:
        p_pool = _ens(c["Xtr_p"], c["ytr_p"], c["Xte"])
        p_sym = _ens(c["Xtr_s"], c["ytr_s"], c["Xte"])
        d3_rows.append(
            dict(
                fold=c["fold"],
                n_test=len(c["yte"]),
                per_symbol_auc=round(roc_auc_score(c["yte"], p_sym), 4),
                pooled_auc=round(roc_auc_score(c["yte"], p_pool), 4),
                lift=round(
                    roc_auc_score(c["yte"], p_pool) - roc_auc_score(c["yte"], p_sym),
                    4,
                ),
            )
        )
    t13 = pd.DataFrame(d3_rows)
    t13.to_csv(f"{OUT}/T13_ldo_per_fold.csv", index=False)

    # ============================================================
    # T14 — breakdown verdict
    # ============================================================
    ldo_row = t11[t11["symbol"] == "LDOUSDT"].iloc[0]
    ldo_pooled_real = bool(ldo_row["pooled_clears_null_q95"])
    ldo_gated = t12[t12["symbol"] == "LDOUSDT"]
    ldo_gp = float(
        ldo_gated.loc[ldo_gated["architecture"] == "pooled", "weighted_gated_hit_rate"].iloc[0]
    )
    ldo_gs = float(
        ldo_gated.loc[
            ldo_gated["architecture"] == "per_symbol", "weighted_gated_hit_rate"
        ].iloc[0]
    )
    n_ldo_pos_folds = int((t13["lift"] > 0).sum())
    t14 = pd.DataFrame(
        [
            dict(
                question="Is the LDO pooled AUC lift genuine signal?",
                ldo_pooled_lift=float(ldo_row["pooled_lift"]),
                ldo_pooled_clears_own_null_q95=ldo_pooled_real,
                ldo_gated_tail_lift=round(ldo_gp - ldo_gs, 4),
                ldo_positive_lift_folds=f"{n_ldo_pos_folds}/{len(t13)}",
                verdict=(
                    "LDO pooled lift is CREDIBLE — clears its own no-signal q95"
                    if ldo_pooled_real
                    else "LDO pooled lift is WITHIN no-signal band — not credible signal"
                ),
            )
        ]
    )
    t14.to_csv(f"{OUT}/T14_breakdown_verdict.csv", index=False)

    print("\n=== T11 per-symbol permutation null ===")
    print(t11.to_string(index=False))
    print("\n=== T12 per-symbol gated-tail hit rate ===")
    print(t12.to_string(index=False))
    print("\n=== T13 LDO per-fold detail ===")
    print(t13.to_string(index=False))
    print("\n=== T14 breakdown verdict ===")
    print(t14.to_string(index=False))


if __name__ == "__main__":
    run()
