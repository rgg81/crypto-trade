"""iter-v3/110 gating EDA — DECISIVE TEST: per-symbol feature->label signal screen.

The /109 chain proved the 14-feature representation carries NO IS-detectable
directional signal ON THE BCH/LDO/TRX UNIVERSE (LightGBM real-label held-out
AUC 0.497, 100-shuffle permutation p=0.64). /109 Section 8.3 Option A: the
permutation null is SPECIFIC to that universe's joint feature->label
distribution — a different universe is a different distribution the null does
not touch.

This script runs the EXACT /109 measurement — a walk-forward-faithful,
embargo-purged, 5-seed-averaged LightGBM feature->label held-out AUC — across
ALL 21 v3-eligible candidate symbols (incumbents included), and adds a
per-symbol permutation null so an eyeballed AUC becomes a verdict (the central
/109 methodology lesson).

Outputs:
  T1_per_symbol_signal.csv   — per-symbol held-out AUC, rank-IC, permutation
                               band, permutation p-value, GO/NO-GO flag
  T2_per_fold_auc.csv        — the per-symbol x per-fold AUC grid (stability)
  T3_universe_ranking.csv    — symbols ranked by signal; the proposed universe

NO CHEATING — every feature row has close_time < OOS_CUTOFF_MS; the post-cutoff
OOS is never read. _shared.load_labeled_symbol asserts the invariant per symbol.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from _shared import (  # noqa: E402
    CANDIDATE_SYMBOLS,
    INCUMBENTS,
    V3_FEATURE_COLUMNS,
    load_labeled_symbol,
    make_walk_forward_folds,
)

OUT = Path(__file__).resolve().parent

# v3 inner-ensemble seeds — the production 5-seed protocol.
SEEDS = (42, 123, 456, 789, 1001)
N_PERM = 60  # permutation-null shuffles per symbol (kept modest for the 2h cap)
PERM_SEED_BASE = 20250519

# LightGBM params — the v3 depth-3-5 gradient-boosted tree (the production
# architecture; see strategies/ml/lgbm.py defaults). Held FIXED — the only
# variable across symbols is the data.
LGB_PARAMS = dict(
    objective="binary",
    num_leaves=15,        # depth ~ 3-4
    max_depth=4,
    learning_rate=0.05,
    n_estimators=200,
    subsample=0.8,
    colsample_bytree=1.0,
    min_child_samples=20,
    reg_lambda=1.0,
    verbosity=-1,
)


def _fit_predict_auc(
    X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray, y_te: np.ndarray, seed: int
) -> tuple[float, np.ndarray]:
    """Fit one LightGBM, return (held-out AUC, held-out proba). y in {0,1}."""
    if len(np.unique(y_tr)) < 2 or len(np.unique(y_te)) < 2:
        return np.nan, np.full(len(y_te), 0.5)
    params = dict(LGB_PARAMS)
    params["random_state"] = seed
    model = lgb.LGBMClassifier(**params)
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    try:
        auc = roc_auc_score(y_te, proba)
    except ValueError:
        auc = np.nan
    return auc, proba


def screen_symbol(sym: str) -> dict:
    """Run the full feature->label signal screen for one symbol.

    Returns the T1 row dict + attaches the per-fold AUC list.
    """
    df = load_labeled_symbol(sym)
    n_is = len(df)
    folds = make_walk_forward_folds(df, n_folds=8)
    feat = V3_FEATURE_COLUMNS
    X_all = df[feat].to_numpy(dtype=np.float64)
    # label {-1,+1} -> {0,1} for binary AUC
    y_all = (df["label"].to_numpy() > 0).astype(np.int64)
    best_edge = df["best_edge"].to_numpy(dtype=np.float64)

    # ---- real-label held-out AUC + rank-IC, 5-seed averaged, per fold --------
    per_fold_auc = []
    per_fold_ic = []
    pooled_true: list[np.ndarray] = []
    pooled_proba: list[np.ndarray] = []
    pooled_edge: list[np.ndarray] = []
    for tr_idx, te_idx in folds:
        X_tr, y_tr = X_all[tr_idx], y_all[tr_idx]
        X_te, y_te = X_all[te_idx], y_all[te_idx]
        seed_aucs = []
        seed_probas = []
        for sd in SEEDS:
            auc, proba = _fit_predict_auc(X_tr, y_tr, X_te, y_te, sd)
            seed_aucs.append(auc)
            seed_probas.append(proba)
        fold_auc = float(np.nanmean(seed_aucs))
        fold_proba = np.mean(seed_probas, axis=0)
        per_fold_auc.append(fold_auc)
        # rank-IC: Spearman(proba, signed best-direction edge). Map proba->signed
        # directional bet (proba>0.5 => long), realized = best_edge with sign.
        signed_pred = fold_proba - 0.5
        realized = best_edge[te_idx]  # PnL of the best direction (>=0)
        # directional realized: + if long was best, - if short was best
        dir_real = np.where(y_te > 0, realized, -realized)
        if np.std(signed_pred) > 1e-12 and np.std(dir_real) > 1e-12:
            ic = float(
                pd.Series(signed_pred).corr(pd.Series(dir_real), method="spearman")
            )
        else:
            ic = np.nan
        per_fold_ic.append(ic)
        pooled_true.append(y_te)
        pooled_proba.append(fold_proba)
        pooled_edge.append(dir_real)

    yt = np.concatenate(pooled_true)
    pp = np.concatenate(pooled_proba)
    try:
        pooled_auc = float(roc_auc_score(yt, pp))
    except ValueError:
        pooled_auc = np.nan
    mean_fold_auc = float(np.nanmean(per_fold_auc))
    std_fold_auc = float(np.nanstd(per_fold_auc))
    mean_ic = float(np.nanmean(per_fold_ic))
    pos_folds = int(np.sum(np.array(per_fold_auc) > 0.50))

    # ---- permutation null: shuffle training labels, refit, re-score ----------
    # Single-seed (42) per /109's T8 protocol — matched seed, kept cheap.
    perm_aucs = []
    rng = np.random.default_rng(PERM_SEED_BASE)
    for p in range(N_PERM):
        fold_perm = []
        for tr_idx, te_idx in folds:
            X_tr = X_all[tr_idx]
            y_tr = y_all[tr_idx].copy()
            rng.shuffle(y_tr)
            X_te, y_te = X_all[te_idx], y_all[te_idx]
            auc, _ = _fit_predict_auc(X_tr, y_tr, X_te, y_te, 42)
            fold_perm.append(auc)
        perm_aucs.append(float(np.nanmean(fold_perm)))
    perm_aucs = np.array(perm_aucs)
    perm_mean = float(np.nanmean(perm_aucs))
    perm_q05 = float(np.nanpercentile(perm_aucs, 5))
    perm_q50 = float(np.nanpercentile(perm_aucs, 50))
    perm_q95 = float(np.nanpercentile(perm_aucs, 95))
    # observed real-label single-seed-42 AUC, matched to the null's seed
    obs_seed42 = float(np.nanmean([
        _fit_predict_auc(X_all[tr], y_all[tr], X_all[te], y_all[te], 42)[0]
        for tr, te in folds
    ]))
    # one-sided permutation p-value: P(perm AUC >= observed)
    perm_p = float((np.sum(perm_aucs >= obs_seed42) + 1) / (len(perm_aucs) + 1))

    # ---- GO/NO-GO: real signal must clear the no-signal band -----------------
    # GO if the 5-seed pooled AUC materially exceeds the permutation q95 floor
    # AND the permutation p-value is small AND sub-period (fold) stable.
    above_q95 = mean_fold_auc > perm_q95
    sig_p = perm_p < 0.10
    stable = pos_folds >= 5  # >=5 of 8 folds above the 0.50 no-skill line
    signal_go = bool(above_q95 and sig_p and stable)

    return {
        "symbol": sym,
        "is_candles": n_is,
        "n_folds": len(folds),
        "pooled_auc": round(pooled_auc, 4),
        "mean_fold_auc": round(mean_fold_auc, 4),
        "std_fold_auc": round(std_fold_auc, 4),
        "obs_auc_seed42": round(obs_seed42, 4),
        "mean_rank_ic": round(mean_ic, 4),
        "pos_folds_of_8": pos_folds,
        "perm_null_mean": round(perm_mean, 4),
        "perm_null_q05": round(perm_q05, 4),
        "perm_null_q50": round(perm_q50, 4),
        "perm_null_q95": round(perm_q95, 4),
        "perm_p_value": round(perm_p, 4),
        "above_perm_q95": above_q95,
        "perm_p_lt_010": sig_p,
        "fold_stable": stable,
        "SIGNAL_GO": signal_go,
        "is_incumbent": sym in INCUMBENTS,
        "_per_fold_auc": per_fold_auc,
    }


def main() -> None:
    rows = []
    fold_rows = []
    n = len(CANDIDATE_SYMBOLS)
    for i, sym in enumerate(CANDIDATE_SYMBOLS, 1):
        print(f"[{i}/{n}] screening {sym} ...", flush=True)
        r = screen_symbol(sym)
        pfa = r.pop("_per_fold_auc")
        for fi, a in enumerate(pfa):
            fold_rows.append({"symbol": sym, "fold": fi, "fold_auc": round(a, 4)})
        rows.append(r)
        print(
            f"    pooled_auc={r['pooled_auc']} perm_q95={r['perm_null_q95']} "
            f"perm_p={r['perm_p_value']} SIGNAL_GO={r['SIGNAL_GO']}",
            flush=True,
        )

    t1 = pd.DataFrame(rows).sort_values("mean_fold_auc", ascending=False)
    t1.to_csv(OUT / "T1_per_symbol_signal.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(OUT / "T2_per_fold_auc.csv", index=False)

    # ---- T3 — the universe ranking + the proposed selection -----------------
    ranked = t1.copy().reset_index(drop=True)
    ranked["signal_rank"] = np.arange(1, len(ranked) + 1)
    # the proposed v3 universe = the SIGNAL_GO symbols, top-N by mean_fold_auc.
    go = ranked[ranked["SIGNAL_GO"]].copy()
    ranked["in_proposed_universe"] = ranked["symbol"].isin(
        go.head(min(len(go), 6))["symbol"]
    )
    ranked[
        [
            "signal_rank", "symbol", "is_incumbent", "mean_fold_auc",
            "perm_null_q95", "perm_p_value", "pos_folds_of_8", "mean_rank_ic",
            "SIGNAL_GO", "in_proposed_universe",
        ]
    ].to_csv(OUT / "T3_universe_ranking.csv", index=False)

    print("\n=== T1 per-symbol signal screen (sorted by mean_fold_auc) ===")
    print(t1[
        ["symbol", "is_incumbent", "mean_fold_auc", "perm_null_q95",
         "perm_p_value", "pos_folds_of_8", "SIGNAL_GO"]
    ].to_string(index=False))
    n_go = int(t1["SIGNAL_GO"].sum())
    print(f"\nSIGNAL_GO symbols: {n_go} of {len(t1)}")
    inc = t1[t1["is_incumbent"]]
    print("\nIncumbent (BCH/LDO/TRX) reproduction of the /109 null:")
    print(inc[
        ["symbol", "mean_fold_auc", "perm_null_q95", "perm_p_value", "SIGNAL_GO"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
