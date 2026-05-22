"""iter-v3/109 gating EDA — ROBUSTNESS ANNEX.

The decisive horse race (model_class_horse_race.py) returned: no neural model
class beats the depth-3-5 LightGBM on held-out IS AUC, and LightGBM itself sits
at AUC ~0.50. This annex rules out two ways that headline could be a measurement
artifact rather than a true NULL:

  A. CAPACITY ARTIFACT — the single MLP geometry (64,32) was wrong; a larger or
     smaller or more/less regularized neural model would clear the bar.
     -> Sweep 5 MLP capacities (tiny -> wide -> deep -> two regularization
        strengths) and re-score the pooled held-out AUC of each.

  B. THE NULL IS MERELY "TREES ARE GOOD" — LightGBM at 0.50 might still hold a
     real edge a neural model fails to match.
     -> A 100-shuffle permutation null on the LightGBM itself: permute the
        training-fold labels, refit, re-score. If the REAL LightGBM AUC sits
        inside the permuted no-signal band, then the 14 features carry no
        IS-detectable directional signal for ANY model class — the NULL is a
        property of the data, not of the neural architecture.

Strictly IS-only — inherits the load_labeled_is() / make_walk_forward_folds()
IS-only invariant. Outputs T7-T9 under analysis/iteration_v3-109/.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb

from _shared import SYMBOLS, V3_FEATURE_COLUMNS, load_labeled_is, make_walk_forward_folds

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

OUT = "analysis/iteration_v3-109"
SEEDS = (42, 123, 456)  # 3-seed for the annex (compute budget)
N_PERMUTATIONS = 100

MLP_CAPACITIES = {
    "mlp_tiny_16": dict(hidden_layer_sizes=(16,), alpha=1e-3),
    "mlp_base_64_32": dict(hidden_layer_sizes=(64, 32), alpha=1e-3),
    "mlp_wide_128_64": dict(hidden_layer_sizes=(128, 64), alpha=1e-3),
    "mlp_deep_64_32_16": dict(hidden_layer_sizes=(64, 32, 16), alpha=1e-3),
    "mlp_base_strong_reg": dict(hidden_layer_sizes=(64, 32), alpha=1e-1),
}


def _mlp_proba(Xtr, ytr, Xte, seed, **cap):
    sc = StandardScaler().fit(Xtr)
    m = MLPClassifier(
        activation="relu",
        learning_rate_init=1e-3,
        max_iter=400,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=seed,
        **cap,
    )
    m.fit(sc.transform(Xtr), ytr)
    return m.predict_proba(sc.transform(Xte))[:, 1]


def _lgbm_proba(Xtr, ytr, Xte, seed):
    m = lgb.LGBMClassifier(
        n_estimators=200, max_depth=4, num_leaves=31, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_samples=20,
        reg_alpha=0.1, reg_lambda=0.1, random_state=seed, n_jobs=1, verbose=-1,
    )
    m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]


def _all_folds(df):
    """Yield (symbol, fold, Xtr, ytr, Xte, yte) over every walk-forward fold."""
    for sym in SYMBOLS:
        d = df[df["symbol"] == sym].sort_values("close_time").reset_index(drop=True)
        for fk, (tr_idx, te_idx) in enumerate(make_walk_forward_folds(d, n_folds=8)):
            Xtr = d.iloc[tr_idx][V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            Xte = d.iloc[te_idx][V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            ytr = (d.iloc[tr_idx]["label"].to_numpy() == 1).astype(int)
            yte = (d.iloc[te_idx]["label"].to_numpy() == 1).astype(int)
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                continue
            yield sym, fk, Xtr, ytr, Xte, yte


def run() -> None:
    df = load_labeled_is()
    print(f"[IS-only] {len(df)} labeled IS candles")
    folds = list(_all_folds(df))
    print(f"[IS-only] {len(folds)} usable walk-forward folds")

    # ---- A. MLP capacity sweep (T7) ----
    cap_rows = []
    for cap_name, cap in MLP_CAPACITIES.items():
        aucs = []
        for _sym, _fk, Xtr, ytr, Xte, yte in folds:
            p = np.mean([_mlp_proba(Xtr, ytr, Xte, s, **cap) for s in SEEDS], axis=0)
            aucs.append(roc_auc_score(yte, p))
        cap_rows.append(
            dict(capacity=cap_name, mean_auc=np.mean(aucs), std_auc=np.std(aucs),
                 min_auc=np.min(aucs), max_auc=np.max(aucs), n_folds=len(aucs))
        )
    t7 = pd.DataFrame(cap_rows).sort_values("mean_auc", ascending=False)
    t7.to_csv(f"{OUT}/T7_mlp_capacity_sweep.csv", index=False)

    # LightGBM reference AUC on the identical folds (3-seed) — the bar to beat
    lgbm_aucs = []
    for _sym, _fk, Xtr, ytr, Xte, yte in folds:
        p = np.mean([_lgbm_proba(Xtr, ytr, Xte, s) for s in SEEDS], axis=0)
        lgbm_aucs.append(roc_auc_score(yte, p))
    lgbm_mean = float(np.mean(lgbm_aucs))

    t7["lgbm_reference_auc"] = lgbm_mean
    t7["beats_lgbm"] = t7["mean_auc"] > lgbm_mean
    t7.to_csv(f"{OUT}/T7_mlp_capacity_sweep.csv", index=False)

    # ---- B. permutation null on the LightGBM itself (T8) ----
    rng = np.random.default_rng(20250519)
    perm_aucs = []
    for p_i in range(N_PERMUTATIONS):
        fold_aucs = []
        for _sym, _fk, Xtr, ytr, Xte, yte in folds:
            ytr_perm = rng.permutation(ytr)
            if len(np.unique(ytr_perm)) < 2:
                continue
            pr = _lgbm_proba(Xtr, ytr_perm, Xte, 42)  # single seed — permutation budget
            fold_aucs.append(roc_auc_score(yte, pr))
        perm_aucs.append(np.mean(fold_aucs))
    perm_aucs = np.asarray(perm_aucs)
    # observed real-label LightGBM AUC, single seed=42 — matched to the null
    real_aucs = []
    for _sym, _fk, Xtr, ytr, Xte, yte in folds:
        real_aucs.append(roc_auc_score(yte, _lgbm_proba(Xtr, ytr, Xte, 42)))
    real_lgbm_s42 = float(np.mean(real_aucs))
    p_value = float((perm_aucs >= real_lgbm_s42).mean())
    t8 = pd.DataFrame(
        [
            dict(quantity="observed_lgbm_auc_real_labels", value=round(real_lgbm_s42, 4)),
            dict(quantity="permutation_null_mean", value=round(float(perm_aucs.mean()), 4)),
            dict(quantity="permutation_null_q05", value=round(float(np.quantile(perm_aucs, 0.05)), 4)),
            dict(quantity="permutation_null_q50", value=round(float(np.quantile(perm_aucs, 0.50)), 4)),
            dict(quantity="permutation_null_q95", value=round(float(np.quantile(perm_aucs, 0.95)), 4)),
            dict(quantity="permutation_p_value", value=round(p_value, 4)),
            dict(quantity="n_permutations", value=N_PERMUTATIONS),
        ]
    )
    t8.to_csv(f"{OUT}/T8_lgbm_permutation_null.csv", index=False)

    # ---- T9 — annex verdict ----
    best_cap = t7.iloc[0]
    any_beat = bool(t7["beats_lgbm"].any())
    signal_present = bool(real_lgbm_s42 > np.quantile(perm_aucs, 0.95))
    t9 = pd.DataFrame(
        [
            dict(
                finding="best MLP capacity beats LightGBM",
                result=any_beat,
                detail=f"best={best_cap['capacity']} auc={best_cap['mean_auc']:.4f} "
                f"vs lgbm {lgbm_mean:.4f}",
            ),
            dict(
                finding="LightGBM real-label AUC clears the permutation q95 "
                "(any extractable directional signal)",
                result=signal_present,
                detail=f"real {real_lgbm_s42:.4f} vs null q95 "
                f"{np.quantile(perm_aucs, 0.95):.4f}; p={p_value:.3f}",
            ),
            dict(
                finding="ANNEX VERDICT",
                result="NO-GO confirmed — no model class extracts signal"
                if (not any_beat and not signal_present)
                else "investigate",
                detail="the NULL is a property of the 14-feature / triple-barrier / "
                "BCH-LDO-TRX data, not of the neural architecture"
                if (not any_beat and not signal_present)
                else "",
            ),
        ]
    )
    t9.to_csv(f"{OUT}/T9_annex_verdict.csv", index=False)

    print("\n=== T7 MLP capacity sweep ===")
    print(t7.to_string(index=False))
    print(f"\nLightGBM 3-seed reference pooled AUC = {lgbm_mean:.4f}")
    print("\n=== T8 LightGBM permutation null ===")
    print(t8.to_string(index=False))
    print("\n=== T9 annex verdict ===")
    print(t9.to_string(index=False))


if __name__ == "__main__":
    run()
