"""iter-v3/123 — cycle-7 EXPLORATION #2 — ETH-vs-symbol VOL-REGIME-RATIO EDA orchestrator.

Pipeline (steps 1-5 + SSC-RISK gate + the /122 Critic Rec 1 PAIRWISE IC gate):
  Step 1 — T1: candidate catalog (4 ETH/sym vol-ratio candidates: B1, B1a, B1b, B1c).
  Step 2 — T2: Linear Redundancy Pre-Falsifier:
                (a) joint R² < 0.70 strict (vs full 14-feature anchor)
                (b) PAIRWISE IC < 0.40 STRICT with vwap_dev_20 + regime_momentum_signed_5d
                    (per /122 Critic Rec 1 — IC-spanning diagnostic missed at /122 EDA).
  Step 3 — T3: walk-forward POOLED univariate OOF AUC + 100-perm null.
           T4: per-symbol univariate AUC (the /117 g1 hard gate).
  Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance rank.
  Step 5 — T7: multivariate-LIFT screen (14 vs 14+1 OOF AUC, POOLED +
               per-symbol).
           T9: SSC-RISK gate per the /119 definition.
           T6: GO/NO-GO verdict synthesis.

All outputs CSV-committed to analysis/iteration_v3-123/.

NOTE: B1 candidates are SIMPLE PRIMITIVES (cross-asset realized-vol RATIOS)
NOT composed features per the /025-class definition (no sign() × magnitude
gating). The composed-feature carve-out at `feedback_v3_engineered_feature_pivot.md`
does NOT apply — the strict R² < 0.70 gate + the strict pairwise-IC < 0.40
gate both apply (the /122 Critic Rec 1 strict regime).
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from _shared import (  # noqa: E402
    CANDIDATE_CATEGORY,
    CANDIDATE_MOTIVATION,
    CANDIDATE_NAMES,
    IC_TARGET_INCUMBENTS,
    IC_TARGET_THRESHOLD,
    PRIMARY_CANDIDATE,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    build_labeled_panel,
    walk_forward_folds,
)

warnings.filterwarnings("ignore")

RNG_SEED = 42
N_PERM = 100  # univariate permutation-null trials


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _logistic_regression_auc(X: np.ndarray, y: np.ndarray) -> float:
    """Single-feature logistic-regression AUC via sklearn (no LightGBM for univariate)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    if X.ndim == 1:
        X = X.reshape(-1, 1)
    try:
        x_mean = X.mean(axis=0)
        x_std = X.std(axis=0) + 1e-12
        Xs = (X - x_mean) / x_std
        clf = LogisticRegression(max_iter=200, random_state=RNG_SEED, solver="lbfgs")
        clf.fit(Xs, y)
        prob = clf.predict_proba(Xs)[:, 1]
        return float(roc_auc_score(y, prob))
    except Exception:
        return 0.5


def _lightgbm_oof_auc(X: pd.DataFrame, y: np.ndarray, folds) -> tuple[float, np.ndarray]:
    """Walk-forward multivariate LightGBM OOF predictions; returns (POOLED_AUC, oof_prob)."""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score

    n = len(X)
    oof = np.full(n, np.nan, dtype="float64")
    for train_idx, test_idx in folds:
        if len(train_idx) < 200 or len(test_idx) < 30:
            continue
        X_tr = X.iloc[train_idx]
        y_tr = y[train_idx]
        X_te = X.iloc[test_idx]
        # Skip degenerate train sets.
        if len(np.unique(y_tr)) < 2:
            continue
        params = dict(
            num_leaves=15,
            max_depth=4,
            learning_rate=0.05,
            n_estimators=100,
            min_child_samples=20,
            random_state=RNG_SEED,
            verbosity=-1,
        )
        clf = lgb.LGBMClassifier(**params)
        clf.fit(X_tr, y_tr)
        oof[test_idx] = clf.predict_proba(X_te)[:, 1]

    valid = ~np.isnan(oof)
    if valid.sum() < 50 or len(np.unique(y[valid])) < 2:
        return 0.5, oof
    pooled_auc = float(roc_auc_score(y[valid], oof[valid]))
    return pooled_auc, oof


def _lightgbm_feature_importance(X: pd.DataFrame, y: np.ndarray) -> dict[str, float]:
    """Single-fit depth-4 LightGBM importance on full panel; returns gain dict."""
    import lightgbm as lgb

    params = dict(
        num_leaves=15,
        max_depth=4,
        learning_rate=0.05,
        n_estimators=100,
        min_child_samples=20,
        random_state=RNG_SEED,
        verbosity=-1,
    )
    clf = lgb.LGBMClassifier(**params)
    clf.fit(X, y)
    gain = dict(zip(X.columns, clf.booster_.feature_importance(importance_type="gain")))
    return gain


# -----------------------------------------------------------------------------
# Step 1 — T1: candidate catalog
# -----------------------------------------------------------------------------


def step1_catalog() -> pd.DataFrame:
    """T1: emit the candidate catalog with categories, formulas, motivations."""
    rows = []
    for name in CANDIDATE_NAMES:
        rows.append(
            {
                "candidate": name,
                "is_primary": (name == PRIMARY_CANDIDATE),
                "category": CANDIDATE_CATEGORY[name],
                "motivation": CANDIDATE_MOTIVATION[name],
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(THIS_DIR / "T1_candidate_catalog.csv", index=False)
    print(f"[T1] Wrote candidate catalog ({len(df)} rows) -> T1_candidate_catalog.csv")
    return df


# -----------------------------------------------------------------------------
# Step 2 — T2: Linear Redundancy Pre-Falsifier
# (a) joint R² < 0.70 strict vs full 14-feature anchor
# (b) PAIRWISE IC < 0.40 STRICT with vwap_dev_20 + regime_momentum_signed_5d
#     (per /122 Critic Rec 1)
# -----------------------------------------------------------------------------


def step2_linear_redundancy(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """T2: per-candidate joint R² vs 14-feature anchor + pairwise IC with the
    /122 spanning incumbents (vwap_dev_20, regime_momentum_signed_5d).

    Lineage discipline:
    - ETH vol-ratio features are NOT composed features → strict R² < 0.70
      gate applies (NO composed-feature carve-out).
    - /122 Critic Rec 1 mandates pairwise IC < 0.40 with the two spanning
      incumbents specifically (vwap_dev_20, regime_momentum_signed_5d).
    """
    pooled = pd.concat(panels.values(), ignore_index=True)
    rows = []
    for cand in CANDIDATE_NAMES:
        y = pooled[cand].to_numpy(dtype="float64")
        X = pooled[V3_FEATURE_COLUMNS].to_numpy(dtype="float64")
        # OLS via lstsq.
        Xint = np.concatenate([np.ones((len(X), 1)), X], axis=1)
        beta, *_ = np.linalg.lstsq(Xint, y, rcond=None)
        y_hat = Xint @ beta
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1.0 - ss_res / max(ss_tot, 1e-12)

        # Per-incumbent absolute IC (correlation with the candidate)
        corrs = {col: float(np.corrcoef(pooled[col], pooled[cand])[0, 1]) for col in V3_FEATURE_COLUMNS}
        top_prim = max(corrs.items(), key=lambda kv: abs(kv[1]))
        ic_vwap_dev_20 = abs(corrs["vwap_dev_20"])
        ic_regime_mom = abs(corrs["regime_momentum_signed_5d"])
        # Max pairwise IC across the entire 14-feature stack (informational)
        max_pairwise_ic = max(abs(v) for v in corrs.values())

        # /122 Critic Rec 1 strict gate
        gate_r2 = (r2 < 0.70)
        gate_ic_vwap = (ic_vwap_dev_20 < IC_TARGET_THRESHOLD)
        gate_ic_regime = (ic_regime_mom < IC_TARGET_THRESHOLD)

        if not gate_r2:
            verdict = "REJECT-R2"
        elif not (gate_ic_vwap and gate_ic_regime):
            failing = []
            if not gate_ic_vwap:
                failing.append(f"vwap_dev_20({ic_vwap_dev_20:.2f})")
            if not gate_ic_regime:
                failing.append(f"regime_momentum({ic_regime_mom:.2f})")
            verdict = f"REJECT-IC-PAIR ({','.join(failing)})"
        else:
            verdict = "PASS"

        rows.append(
            {
                "candidate": cand,
                "pooled_r2": round(r2, 4),
                "top_primitive": top_prim[0],
                "top_abs_corr": round(abs(top_prim[1]), 4),
                "ic_vwap_dev_20": round(ic_vwap_dev_20, 4),
                "ic_regime_momentum_signed_5d": round(ic_regime_mom, 4),
                "max_pairwise_ic": round(max_pairwise_ic, 4),
                "verdict": verdict,
            }
        )
    df = pd.DataFrame(rows).sort_values("pooled_r2")
    df.to_csv(THIS_DIR / "T2_linear_redundancy_pre_falsifier.csv", index=False)
    print(f"[T2] Wrote linear-redundancy ({len(df)} rows) -> T2_linear_redundancy_pre_falsifier.csv")
    return df


# -----------------------------------------------------------------------------
# Step 3 — T3 + T4: univariate walk-forward AUC
# -----------------------------------------------------------------------------


def step3_univariate_pooled(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """T3: walk-forward POOLED univariate OOF AUC with 100-perm null."""
    rng = np.random.default_rng(RNG_SEED)
    pooled = pd.concat(panels.values(), ignore_index=True).sort_values("close_time").reset_index(drop=True)
    folds = walk_forward_folds(len(pooled), n_folds=5)
    y_real = pooled["label"].to_numpy(dtype="int64")

    rows = []
    for cand in CANDIDATE_NAMES:
        # Real OOF AUC across folds
        oof = np.full(len(pooled), np.nan, dtype="float64")
        for train_idx, test_idx in folds:
            if len(train_idx) < 200 or len(test_idx) < 30:
                continue
            x_tr = pooled[cand].iloc[train_idx].to_numpy(dtype="float64")
            y_tr = y_real[train_idx]
            x_te = pooled[cand].iloc[test_idx].to_numpy(dtype="float64")
            if len(np.unique(y_tr)) < 2:
                continue
            try:
                from sklearn.linear_model import LogisticRegression
                x_mean = float(np.mean(x_tr))
                x_std = float(np.std(x_tr) + 1e-12)
                Xs_tr = ((x_tr - x_mean) / x_std).reshape(-1, 1)
                Xs_te = ((x_te - x_mean) / x_std).reshape(-1, 1)
                clf = LogisticRegression(max_iter=200, random_state=RNG_SEED, solver="lbfgs")
                clf.fit(Xs_tr, y_tr)
                oof[test_idx] = clf.predict_proba(Xs_te)[:, 1]
            except Exception:
                pass
        valid = ~np.isnan(oof)
        if valid.sum() < 50 or len(np.unique(y_real[valid])) < 2:
            real_auc = 0.5
        else:
            from sklearn.metrics import roc_auc_score
            real_auc = float(roc_auc_score(y_real[valid], oof[valid]))

        # Permutation null: shuffle labels N_PERM times.
        null_aucs = []
        for _ in range(N_PERM):
            y_shuf = rng.permutation(y_real)
            oof_n = np.full(len(pooled), np.nan, dtype="float64")
            for train_idx, test_idx in folds:
                if len(train_idx) < 200 or len(test_idx) < 30:
                    continue
                x_tr = pooled[cand].iloc[train_idx].to_numpy(dtype="float64")
                y_tr = y_shuf[train_idx]
                x_te = pooled[cand].iloc[test_idx].to_numpy(dtype="float64")
                if len(np.unique(y_tr)) < 2:
                    continue
                try:
                    from sklearn.linear_model import LogisticRegression
                    x_mean = float(np.mean(x_tr))
                    x_std = float(np.std(x_tr) + 1e-12)
                    Xs_tr = ((x_tr - x_mean) / x_std).reshape(-1, 1)
                    Xs_te = ((x_te - x_mean) / x_std).reshape(-1, 1)
                    clf = LogisticRegression(max_iter=200, random_state=RNG_SEED, solver="lbfgs")
                    clf.fit(Xs_tr, y_tr)
                    oof_n[test_idx] = clf.predict_proba(Xs_te)[:, 1]
                except Exception:
                    pass
            v_n = ~np.isnan(oof_n)
            if v_n.sum() < 50 or len(np.unique(y_shuf[v_n])) < 2:
                continue
            try:
                from sklearn.metrics import roc_auc_score
                null_aucs.append(float(roc_auc_score(y_shuf[v_n], oof_n[v_n])))
            except Exception:
                pass

        q95 = float(np.quantile(null_aucs, 0.95)) if null_aucs else 0.5
        if null_aucs:
            p = float(np.mean([a >= real_auc for a in null_aucs]))
        else:
            p = 1.0
        rows.append(
            {
                "candidate": cand,
                "pooled_auc": round(real_auc, 4),
                "null_q95": round(q95, 4),
                "p_value": round(p, 3),
                "clears_q95": bool(real_auc > q95),
            }
        )

    df = pd.DataFrame(rows).sort_values("pooled_auc", ascending=False)
    df.to_csv(THIS_DIR / "T3_walkforward_pooled_auc.csv", index=False)
    print(f"[T3] Wrote walk-forward POOLED univariate AUC ({len(df)} rows) -> T3_walkforward_pooled_auc.csv")
    return df


def step3_univariate_per_symbol(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """T4: per-symbol univariate walk-forward OOF AUC (the /117 g1 hard gate)."""
    rows = []
    for cand in CANDIDATE_NAMES:
        per_sym = {}
        n_pass = 0
        for sym in SYMBOLS:
            panel = panels[sym]
            folds = walk_forward_folds(len(panel), n_folds=5)
            y = panel["label"].to_numpy(dtype="int64")
            oof = np.full(len(panel), np.nan, dtype="float64")
            for train_idx, test_idx in folds:
                if len(train_idx) < 200 or len(test_idx) < 30:
                    continue
                x_tr = panel[cand].iloc[train_idx].to_numpy(dtype="float64")
                y_tr = y[train_idx]
                x_te = panel[cand].iloc[test_idx].to_numpy(dtype="float64")
                if len(np.unique(y_tr)) < 2:
                    continue
                try:
                    from sklearn.linear_model import LogisticRegression
                    x_mean = float(np.mean(x_tr))
                    x_std = float(np.std(x_tr) + 1e-12)
                    Xs_tr = ((x_tr - x_mean) / x_std).reshape(-1, 1)
                    Xs_te = ((x_te - x_mean) / x_std).reshape(-1, 1)
                    clf = LogisticRegression(max_iter=200, random_state=RNG_SEED, solver="lbfgs")
                    clf.fit(Xs_tr, y_tr)
                    oof[test_idx] = clf.predict_proba(Xs_te)[:, 1]
                except Exception:
                    pass
            valid = ~np.isnan(oof)
            if valid.sum() < 50 or len(np.unique(y[valid])) < 2:
                auc = 0.5
            else:
                from sklearn.metrics import roc_auc_score
                auc = float(roc_auc_score(y[valid], oof[valid]))
            per_sym[sym] = round(auc, 4)
            if auc > 0.50:
                n_pass += 1
        rows.append(
            {
                "candidate": cand,
                "BCHUSDT": per_sym.get("BCHUSDT", 0.5),
                "LDOUSDT": per_sym.get("LDOUSDT", 0.5),
                "TRXUSDT": per_sym.get("TRXUSDT", 0.5),
                "n_g1_pass": n_pass,
            }
        )

    df = pd.DataFrame(rows).sort_values("n_g1_pass", ascending=False)
    df.to_csv(THIS_DIR / "T4_per_symbol_auc.csv", index=False)
    print(f"[T4] Wrote per-symbol univariate AUC ({len(df)} rows) -> T4_per_symbol_auc.csv")
    return df


# -----------------------------------------------------------------------------
# Step 4 — T5: multivariate (14+1) per-symbol importance
# -----------------------------------------------------------------------------


def step4_multivariate_importance(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """T5: per-symbol depth-4 LightGBM multivariate (14+1) importance rank+gain."""
    rows = []
    for cand in CANDIDATE_NAMES:
        per_sym = {}
        for sym in SYMBOLS:
            panel = panels[sym]
            cols = V3_FEATURE_COLUMNS + [cand]
            X = panel[cols].copy()
            y = panel["label"].to_numpy(dtype="int64")
            gain = _lightgbm_feature_importance(X, y)
            # Build rank table
            sorted_gain = sorted(gain.items(), key=lambda kv: kv[1], reverse=True)
            ranked = {name: i + 1 for i, (name, _) in enumerate(sorted_gain)}
            total_gain = sum(gain.values()) + 1e-12
            cand_rank = ranked.get(cand, len(cols))
            cand_gain_pct = 100.0 * gain.get(cand, 0.0) / total_gain
            per_sym[sym] = (cand_rank, cand_gain_pct)
        rows.append(
            {
                "candidate": cand,
                "BCH_rank": per_sym["BCHUSDT"][0],
                "BCH_gain_pct": round(per_sym["BCHUSDT"][1], 2),
                "LDO_rank": per_sym["LDOUSDT"][0],
                "LDO_gain_pct": round(per_sym["LDOUSDT"][1], 2),
                "TRX_rank": per_sym["TRXUSDT"][0],
                "TRX_gain_pct": round(per_sym["TRXUSDT"][1], 2),
            }
        )
    df = pd.DataFrame(rows).sort_values("BCH_rank")
    df.to_csv(THIS_DIR / "T5_importance_rank_multivariate.csv", index=False)
    print(f"[T5] Wrote multivariate importance ({len(df)} rows) -> T5_importance_rank_multivariate.csv")
    return df


# -----------------------------------------------------------------------------
# Step 5 — T7 multivariate LIFT + T9 SSC-RISK
# -----------------------------------------------------------------------------


def step5_multivariate_lift_and_ssc(panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """T7: walk-forward POOLED LIFT (14 vs 14+1) + per-symbol LIFT. T9: SSC-RISK gate."""
    pooled = pd.concat(panels.values(), ignore_index=True).sort_values("close_time").reset_index(drop=True)
    folds_p = walk_forward_folds(len(pooled), n_folds=5)
    y_p = pooled["label"].to_numpy(dtype="int64")

    # Baseline (14-feature) POOLED AUC
    base_auc_p, _ = _lightgbm_oof_auc(pooled[V3_FEATURE_COLUMNS], y_p, folds_p)
    print(f"[T7] Baseline POOLED 14-feat AUC = {base_auc_p:.4f}")

    # Per-symbol baselines
    base_per_sym = {}
    for sym in SYMBOLS:
        panel = panels[sym]
        folds_s = walk_forward_folds(len(panel), n_folds=5)
        y_s = panel["label"].to_numpy(dtype="int64")
        auc, _ = _lightgbm_oof_auc(panel[V3_FEATURE_COLUMNS], y_s, folds_s)
        base_per_sym[sym] = auc
        print(f"[T7] Baseline {sym} 14-feat AUC = {auc:.4f}")

    rows_t7 = []
    rows_t9 = []
    for cand in CANDIDATE_NAMES:
        cols = V3_FEATURE_COLUMNS + [cand]
        # POOLED with candidate
        auc_pooled_with, _ = _lightgbm_oof_auc(pooled[cols], y_p, folds_p)
        pooled_lift = auc_pooled_with - base_auc_p
        per_sym_lifts = {}
        for sym in SYMBOLS:
            panel = panels[sym]
            folds_s = walk_forward_folds(len(panel), n_folds=5)
            y_s = panel["label"].to_numpy(dtype="int64")
            auc_s, _ = _lightgbm_oof_auc(panel[cols], y_s, folds_s)
            per_sym_lifts[sym] = auc_s - base_per_sym[sym]
        rows_t7.append(
            {
                "candidate": cand,
                "base_auc_pooled": round(base_auc_p, 4),
                "with_auc_pooled": round(auc_pooled_with, 4),
                "pooled_lift": round(pooled_lift, 4),
                "BCH_lift": round(per_sym_lifts["BCHUSDT"], 4),
                "LDO_lift": round(per_sym_lifts["LDOUSDT"], 4),
                "TRX_lift": round(per_sym_lifts["TRXUSDT"], 4),
            }
        )
        # SSC-RISK gate per /119
        max_abs_per_sym = max(abs(per_sym_lifts[s]) for s in SYMBOLS)
        carrier = max(SYMBOLS, key=lambda s: abs(per_sym_lifts[s]))
        if abs(pooled_lift) < 1e-6:
            ssc_ratio = float("inf")
        else:
            ssc_ratio = max_abs_per_sym / abs(pooled_lift)
        ssc_risk = ssc_ratio >= 2.0
        rows_t9.append(
            {
                "candidate": cand,
                "pooled_lift": round(pooled_lift, 4),
                "max_abs_per_symbol": round(max_abs_per_sym, 4),
                "max_carrier": carrier,
                "ssc_ratio": round(ssc_ratio, 2) if not np.isinf(ssc_ratio) else "inf",
                "ssc_risk": ssc_risk,
            }
        )

    df_t7 = pd.DataFrame(rows_t7).sort_values("pooled_lift", ascending=False)
    df_t7.to_csv(THIS_DIR / "T7_multivariate_lift_screen.csv", index=False)
    print(f"[T7] Wrote multivariate-lift ({len(df_t7)} rows) -> T7_multivariate_lift_screen.csv")

    df_t9 = pd.DataFrame(rows_t9).sort_values("ssc_ratio", ascending=False)
    df_t9.to_csv(THIS_DIR / "T9_ssc_risk_gate.csv", index=False)
    print(f"[T9] Wrote SSC-RISK gate ({len(df_t9)} rows) -> T9_ssc_risk_gate.csv")
    return df_t7, df_t9


# -----------------------------------------------------------------------------
# T6: synthesis — GO/NO-GO verdict
# -----------------------------------------------------------------------------


def step6_synthesize(t2: pd.DataFrame, t3: pd.DataFrame, t5: pd.DataFrame, t7: pd.DataFrame, t9: pd.DataFrame) -> pd.DataFrame:
    """T6: GO/NO-GO verdict combining T2/T3/T5/T7/T9. Single top candidate emerges."""
    rows = []
    t2_map = t2.set_index("candidate").to_dict("index")
    t3_map = t3.set_index("candidate").to_dict("index")
    t5_map = t5.set_index("candidate").to_dict("index")
    t7_map = t7.set_index("candidate").to_dict("index")
    t9_map = t9.set_index("candidate").to_dict("index")

    for cand in CANDIDATE_NAMES:
        r2 = t2_map[cand]["pooled_r2"]
        t2_verdict = t2_map[cand]["verdict"]
        ic_vwap = t2_map[cand]["ic_vwap_dev_20"]
        ic_regime = t2_map[cand]["ic_regime_momentum_signed_5d"]
        auc_p = t3_map[cand]["pooled_auc"]
        clears_q95 = t3_map[cand]["clears_q95"]
        ranks = (t5_map[cand]["BCH_rank"], t5_map[cand]["LDO_rank"], t5_map[cand]["TRX_rank"])
        gains = (t5_map[cand]["BCH_gain_pct"], t5_map[cand]["LDO_gain_pct"], t5_map[cand]["TRX_gain_pct"])
        pooled_lift = t7_map[cand]["pooled_lift"]
        ssc_risk = t9_map[cand]["ssc_risk"]

        # Decision logic (incorporates /122 Critic Rec 1 pairwise-IC strict gate)
        if "REJECT" in t2_verdict:
            verdict = t2_verdict
        elif pooled_lift > 0.003 and not ssc_risk and min(ranks) <= 13:
            verdict = "GO"
        elif pooled_lift > 0.003 and ssc_risk:
            verdict = "GO-SSC-RISK"
        elif pooled_lift > 0.001:
            verdict = "MARGINAL"
        elif pooled_lift > 0:
            verdict = "WEAK"
        else:
            verdict = "REJECT"

        rows.append(
            {
                "candidate": cand,
                "is_primary": (cand == PRIMARY_CANDIDATE),
                "category": CANDIDATE_CATEGORY[cand],
                "T2_r2": r2,
                "T2_ic_vwap_dev_20": ic_vwap,
                "T2_ic_regime_momentum": ic_regime,
                "T3_pooled_auc": auc_p,
                "T3_clears_q95": clears_q95,
                "T5_ranks_BCH_LDO_TRX": f"{ranks[0]}/{ranks[1]}/{ranks[2]}",
                "T5_gains_BCH_LDO_TRX": f"{gains[0]}/{gains[1]}/{gains[2]}",
                "T7_pooled_lift": pooled_lift,
                "T9_ssc_risk": ssc_risk,
                "verdict": verdict,
            }
        )

    df = pd.DataFrame(rows)
    # Order: GO > GO-SSC-RISK > MARGINAL > WEAK > REJECT-*
    order = {"GO": 0, "GO-SSC-RISK": 1, "MARGINAL": 2, "WEAK": 3, "REJECT": 4, "REJECT-R2": 5}
    def _ord(v):
        if v in order:
            return order[v]
        if v.startswith("REJECT-IC-PAIR"):
            return 6
        return 99
    df["__o"] = df["verdict"].apply(_ord)
    df = df.sort_values(["__o", "T7_pooled_lift"], ascending=[True, False]).drop(columns="__o")
    df.to_csv(THIS_DIR / "T6_go_nogo_verdict.csv", index=False)
    print(f"[T6] Wrote GO/NO-GO synthesis ({len(df)} rows) -> T6_go_nogo_verdict.csv")
    return df


# -----------------------------------------------------------------------------
# Main pipeline driver
# -----------------------------------------------------------------------------


def main() -> None:
    print("[iter-v3/123 EDA] ETH-vs-symbol vol-regime-ratio screen — pipeline start")
    print(f"  Symbols: {SYMBOLS}")
    print(f"  Candidates: {CANDIDATE_NAMES}  (PRIMARY = {PRIMARY_CANDIDATE})")
    print(f"  IC strict gate (per /122 Critic Rec 1): pairwise IC < {IC_TARGET_THRESHOLD}")
    print(f"  IC target incumbents: {IC_TARGET_INCUMBENTS}")

    # Build IS-only labeled panels with ETH-vs-sym vol-ratio candidates attached.
    panels: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        panel = build_labeled_panel(sym)
        panels[sym] = panel
        print(f"  {sym} IS-only labeled panel: {len(panel)} rows")

    # Steps
    t1 = step1_catalog()
    t2 = step2_linear_redundancy(panels)
    t3 = step3_univariate_pooled(panels)
    t4 = step3_univariate_per_symbol(panels)
    t5 = step4_multivariate_importance(panels)
    t7, t9 = step5_multivariate_lift_and_ssc(panels)
    t6 = step6_synthesize(t2, t3, t5, t7, t9)

    # Summary
    print("\n[T6 verdict summary]")
    print(t6[["candidate", "is_primary", "T2_r2", "T2_ic_vwap_dev_20",
              "T2_ic_regime_momentum", "T7_pooled_lift", "T9_ssc_risk", "verdict"]].to_string(index=False))

    # Past-only and OOS-leak audits (assert-style; logged)
    print("\n[past-only + OOS-leak audit]")
    for sym in SYMBOLS:
        panel = panels[sym]
        is_count = len(panel)
        oos_count = int((panel.get("close_time", pd.Series([], dtype="int64")) >= 1742774400000).sum())
        print(f"  {sym}: {is_count} IS rows / {oos_count} OOS rows (expect 0 OOS)")

    print("\n[iter-v3/123 EDA] pipeline complete.")


if __name__ == "__main__":
    main()
