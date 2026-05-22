"""iter-v3/119 — main EDA orchestrator (steps 1-5 + SSC-RISK gate).

Pipeline:
  Step 1 — T1: candidate catalog (6 candidates), cycle-6 motivation.
  Step 2 — T2: Linear Redundancy Pre-Falsifier (R² vs 14-feature anchor).
  Step 3 — T3: walk-forward POOLED univariate OOF AUC + 100-perm null.
           T4: per-symbol univariate AUC (the /117 g1 hard gate).
  Step 4 — T5: multivariate (14+1) depth-4 LightGBM importance rank.
  Step 5 — T7: multivariate-LIFT screen (14 vs 14+1 OOF AUC).
           T9: NEW Single-Symbol-Carrier RISK gate (per-symbol asymmetry).
           T6: GO/NO-GO verdict synthesis.

All outputs CSV-committed to analysis/iteration_v3-119/.
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
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    build_labeled_panel,
    walk_forward_folds,
)

warnings.filterwarnings("ignore")

RNG_SEED = 42
N_PERM = 100  # univariate permutation-null trials


def _logistic_regression_auc(X: np.ndarray, y: np.ndarray) -> float:
    """Single-feature logistic-regression AUC via sklearn (no LightGBM for univariate)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    if X.ndim == 1:
        X = X.reshape(-1, 1)
    try:
        # Standardise the feature
        x_mean = X.mean(axis=0)
        x_std = X.std(axis=0) + 1e-12
        Xs = (X - x_mean) / x_std
        clf = LogisticRegression(max_iter=200, random_state=RNG_SEED, solver="lbfgs")
        clf.fit(Xs, y)
        prob = clf.predict_proba(Xs)[:, 1]
        return float(roc_auc_score(y, prob))
    except Exception:  # singular feature or constant target
        return float("nan")


def _walk_forward_univariate_auc(
    df_per_sym: dict[str, pd.DataFrame], col: str
) -> tuple[float, dict[str, float]]:
    """POOLED + per-symbol walk-forward univariate AUC.

    Each symbol is walk-forward-foldied independently; per-fold AUC is computed
    via logistic regression on the standardised candidate. POOLED = stack of
    all OOF predictions across symbols, then single AUC.
    """
    from sklearn.metrics import roc_auc_score

    pooled_y = []
    pooled_pred = []
    per_sym_auc: dict[str, float] = {}

    for sym, df in df_per_sym.items():
        n = len(df)
        folds = walk_forward_folds(n)
        sym_y = []
        sym_pred = []
        for train_idx, test_idx in folds:
            X_train = df[col].to_numpy()[train_idx]
            X_test = df[col].to_numpy()[test_idx]
            y_train = df["label"].to_numpy()[train_idx]
            y_test = df["label"].to_numpy()[test_idx]

            # Standardise
            mu = float(np.nanmean(X_train))
            sigma = float(np.nanstd(X_train)) + 1e-12
            X_train_s = (X_train - mu) / sigma
            X_test_s = (X_test - mu) / sigma

            from sklearn.linear_model import LogisticRegression

            try:
                clf = LogisticRegression(
                    max_iter=200, random_state=RNG_SEED, solver="lbfgs"
                )
                clf.fit(X_train_s.reshape(-1, 1), y_train)
                pred = clf.predict_proba(X_test_s.reshape(-1, 1))[:, 1]
                sym_y.append(y_test)
                sym_pred.append(pred)
            except Exception:
                continue

        if sym_y:
            sym_y_arr = np.concatenate(sym_y)
            sym_pred_arr = np.concatenate(sym_pred)
            try:
                per_sym_auc[sym] = float(roc_auc_score(sym_y_arr, sym_pred_arr))
            except Exception:
                per_sym_auc[sym] = float("nan")
            pooled_y.append(sym_y_arr)
            pooled_pred.append(sym_pred_arr)
        else:
            per_sym_auc[sym] = float("nan")

    if pooled_y:
        pooled_y_arr = np.concatenate(pooled_y)
        pooled_pred_arr = np.concatenate(pooled_pred)
        try:
            pooled_auc = float(roc_auc_score(pooled_y_arr, pooled_pred_arr))
        except Exception:
            pooled_auc = float("nan")
    else:
        pooled_auc = float("nan")

    return pooled_auc, per_sym_auc


def _multivariate_walk_forward_auc(
    df_per_sym: dict[str, pd.DataFrame], feat_cols: list[str]
) -> tuple[float, dict[str, float], dict[str, dict[str, float]]]:
    """POOLED + per-symbol multivariate walk-forward AUC + per-symbol importance.

    Uses LightGBM (depth-4) at LightGbmStrategy default-like config.
    Returns (POOLED AUC, per-symbol AUC, per-symbol importance dict).
    """
    from sklearn.metrics import roc_auc_score

    try:
        import lightgbm as lgb
    except ImportError:
        raise RuntimeError("LightGBM not available")

    pooled_y = []
    pooled_pred = []
    per_sym_auc: dict[str, float] = {}
    per_sym_imp: dict[str, dict[str, float]] = {}

    for sym, df in df_per_sym.items():
        n = len(df)
        folds = walk_forward_folds(n)
        sym_y = []
        sym_pred = []
        agg_gain = {c: 0.0 for c in feat_cols}

        for train_idx, test_idx in folds:
            X_train = df[feat_cols].iloc[train_idx].to_numpy()
            X_test = df[feat_cols].iloc[test_idx].to_numpy()
            y_train = df["label"].to_numpy()[train_idx]
            y_test = df["label"].to_numpy()[test_idx]

            # Skip degenerate folds where label class is single-valued
            if len(np.unique(y_train)) < 2:
                continue

            params = {
                "objective": "binary",
                "metric": "auc",
                "max_depth": 4,
                "num_leaves": 15,
                "learning_rate": 0.05,
                "n_estimators": 100,
                "min_child_samples": 20,
                "verbosity": -1,
                "random_state": RNG_SEED,
                "n_jobs": 1,
            }
            try:
                clf = lgb.LGBMClassifier(**params)
                clf.fit(X_train, y_train, feature_name=list(feat_cols))
                pred = clf.predict_proba(X_test)[:, 1]
                sym_y.append(y_test)
                sym_pred.append(pred)
                # Aggregate gain importance across folds
                gain = clf.booster_.feature_importance(importance_type="gain")
                for c, g in zip(feat_cols, gain):
                    agg_gain[c] += float(g)
            except Exception:
                continue

        if sym_y:
            sym_y_arr = np.concatenate(sym_y)
            sym_pred_arr = np.concatenate(sym_pred)
            try:
                per_sym_auc[sym] = float(roc_auc_score(sym_y_arr, sym_pred_arr))
            except Exception:
                per_sym_auc[sym] = float("nan")
            pooled_y.append(sym_y_arr)
            pooled_pred.append(sym_pred_arr)
            per_sym_imp[sym] = agg_gain
        else:
            per_sym_auc[sym] = float("nan")
            per_sym_imp[sym] = {c: 0.0 for c in feat_cols}

    if pooled_y:
        pooled_y_arr = np.concatenate(pooled_y)
        pooled_pred_arr = np.concatenate(pooled_pred)
        try:
            pooled_auc = float(roc_auc_score(pooled_y_arr, pooled_pred_arr))
        except Exception:
            pooled_auc = float("nan")
    else:
        pooled_auc = float("nan")

    return pooled_auc, per_sym_auc, per_sym_imp


def step1_candidate_catalog(out_dir: Path) -> None:
    """T1 — catalog the 6 candidates with cycle-6 motivation + category."""
    rows = []
    for name in CANDIDATE_NAMES:
        rows.append(
            {
                "candidate": name,
                "category": CANDIDATE_CATEGORY[name],
                "motivation": CANDIDATE_MOTIVATION[name],
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "T1_candidate_catalog.csv", index=False)
    print("[T1] candidate catalog committed:", out_dir / "T1_candidate_catalog.csv")


def step2_linear_redundancy_pre_falsifier(
    df_per_sym: dict[str, pd.DataFrame], out_dir: Path
) -> pd.DataFrame:
    """T2 — Linear Redundancy Pre-Falsifier: R² of candidate on 14-feature
    anchor primitives, POOLED across symbols. Composed-feature carve-out
    applies (R²>0.50 PASS-CARVEOUT)."""
    from sklearn.linear_model import LinearRegression

    rows = []
    pooled = pd.concat(list(df_per_sym.values()), ignore_index=True)
    for cand in CANDIDATE_NAMES:
        y = pooled[cand].to_numpy()
        X = pooled[V3_FEATURE_COLUMNS].to_numpy()
        try:
            lr = LinearRegression()
            lr.fit(X, y)
            yhat = lr.predict(X)
            ss_res = float(np.sum((y - yhat) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1.0 - (ss_res / (ss_tot + 1e-12))
        except Exception:
            r2 = float("nan")

        # Max |corr| with any single anchor primitive
        corrs = []
        for prim in V3_FEATURE_COLUMNS:
            try:
                c = pooled[[cand, prim]].corr().iloc[0, 1]
                if not np.isnan(c):
                    corrs.append((prim, abs(c)))
            except Exception:
                pass
        corrs.sort(key=lambda t: t[1], reverse=True)
        top_prim, top_abs_corr = corrs[0] if corrs else ("nan", float("nan"))

        if r2 < 0.50:
            verdict = "PASS"
        else:
            verdict = "PASS-CARVEOUT"
        rows.append(
            {
                "candidate": cand,
                "pooled_R2": round(r2, 4),
                "top_primitive": top_prim,
                "top_abs_corr": round(top_abs_corr, 4),
                "verdict": verdict,
            }
        )
    df = pd.DataFrame(rows).sort_values("pooled_R2")
    df.to_csv(out_dir / "T2_linear_redundancy_pre_falsifier.csv", index=False)
    print("[T2] LR-PF committed:", out_dir / "T2_linear_redundancy_pre_falsifier.csv")
    print(df.to_string(index=False))
    return df


def step3_pooled_univariate_auc(
    df_per_sym: dict[str, pd.DataFrame], out_dir: Path
) -> pd.DataFrame:
    """T3 — walk-forward POOLED univariate OOF AUC with permutation null."""
    rng = np.random.default_rng(RNG_SEED)
    rows = []
    for cand in CANDIDATE_NAMES:
        pooled_auc, _ = _walk_forward_univariate_auc(df_per_sym, cand)
        # Permutation null: shuffle the labels within each symbol's folds
        null_aucs = []
        for _trial in range(N_PERM):
            df_shuffled = {}
            for sym, df in df_per_sym.items():
                d2 = df.copy()
                d2["label"] = rng.permutation(d2["label"].to_numpy())
                df_shuffled[sym] = d2
            null_auc, _ = _walk_forward_univariate_auc(df_shuffled, cand)
            null_aucs.append(null_auc)
        null_q95 = float(np.nanquantile(null_aucs, 0.95))
        # p-value = fraction of null AUCs >= observed
        p = float(np.mean([na >= pooled_auc for na in null_aucs if not np.isnan(na)]))
        rows.append(
            {
                "candidate": cand,
                "pooled_auc": round(pooled_auc, 4),
                "null_q95": round(null_q95, 4),
                "p_value": round(p, 3),
                "clears_q95": pooled_auc > null_q95,
            }
        )
    df = pd.DataFrame(rows).sort_values("pooled_auc", ascending=False)
    df.to_csv(out_dir / "T3_walkforward_pooled_auc.csv", index=False)
    print("[T3] POOLED univariate AUC committed:", out_dir / "T3_walkforward_pooled_auc.csv")
    print(df.to_string(index=False))
    return df


def step3b_per_symbol_univariate_auc(
    df_per_sym: dict[str, pd.DataFrame], out_dir: Path
) -> pd.DataFrame:
    """T4 — per-symbol univariate AUC (the /117 g1 hard gate)."""
    rows = []
    for cand in CANDIDATE_NAMES:
        _, per_sym = _walk_forward_univariate_auc(df_per_sym, cand)
        n_g1 = sum(1 for v in per_sym.values() if not np.isnan(v) and v > 0.50)
        rows.append(
            {
                "candidate": cand,
                "BCH_auc": round(per_sym.get("BCHUSDT", float("nan")), 4),
                "LDO_auc": round(per_sym.get("LDOUSDT", float("nan")), 4),
                "TRX_auc": round(per_sym.get("TRXUSDT", float("nan")), 4),
                "n_g1_pass": n_g1,
            }
        )
    df = pd.DataFrame(rows).sort_values("n_g1_pass", ascending=False)
    df.to_csv(out_dir / "T4_per_symbol_auc.csv", index=False)
    print("[T4] per-symbol univariate AUC committed:", out_dir / "T4_per_symbol_auc.csv")
    print(df.to_string(index=False))
    return df


def step4_multivariate_importance(
    df_per_sym: dict[str, pd.DataFrame], out_dir: Path
) -> pd.DataFrame:
    """T5 — multivariate (14+1) depth-4 LightGBM importance rank per symbol.

    The /025 PROMISING benchmark: rank ≤ 5 AND gain ≥ 30% of top-feature.
    Relaxed reading: rank ≤ 10 AND gain ≥ 30%.
    """
    rows = []
    for cand in CANDIDATE_NAMES:
        feat_cols = list(V3_FEATURE_COLUMNS) + [cand]
        _pooled_auc, _per_sym_auc, per_sym_imp = _multivariate_walk_forward_auc(
            df_per_sym, feat_cols
        )
        per_sym_summary: dict[str, str] = {}
        for sym in SYMBOLS:
            imp = per_sym_imp.get(sym, {c: 0.0 for c in feat_cols})
            # Sort by gain desc
            ranked = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)
            top_gain = ranked[0][1] if ranked else 0.0
            rank = None
            for idx, (n, g) in enumerate(ranked, 1):
                if n == cand:
                    rank = idx
                    gain_pct = (g / top_gain * 100.0) if top_gain > 0 else 0.0
                    per_sym_summary[sym] = f"rank{rank}/{len(feat_cols)}_gain{gain_pct:.0f}%"
                    break
            else:
                per_sym_summary[sym] = "missing"
        rows.append(
            {
                "candidate": cand,
                "BCH": per_sym_summary.get("BCHUSDT", "missing"),
                "LDO": per_sym_summary.get("LDOUSDT", "missing"),
                "TRX": per_sym_summary.get("TRXUSDT", "missing"),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "T5_importance_rank_multivariate.csv", index=False)
    print("[T5] multivariate importance committed:", out_dir / "T5_importance_rank_multivariate.csv")
    print(df.to_string(index=False))
    return df


def step5_multivariate_lift_screen(
    df_per_sym: dict[str, pd.DataFrame], out_dir: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """T7 — multivariate-LIFT screen (14 vs 14+1 OOF AUC), POOLED + per-symbol.
    T9 — NEW Single-Symbol-Carrier RISK gate: per-symbol asymmetry vs POOLED.
    """
    # Baseline AUCs (14 features)
    bl_pooled, bl_per_sym, _ = _multivariate_walk_forward_auc(
        df_per_sym, list(V3_FEATURE_COLUMNS)
    )
    lift_rows = []
    ssc_rows = []
    for cand in CANDIDATE_NAMES:
        feat_cols = list(V3_FEATURE_COLUMNS) + [cand]
        cand_pooled, cand_per_sym, _ = _multivariate_walk_forward_auc(
            df_per_sym, feat_cols
        )
        pooled_lift = cand_pooled - bl_pooled
        per_sym_lift = {
            sym: cand_per_sym.get(sym, float("nan")) - bl_per_sym.get(sym, float("nan"))
            for sym in SYMBOLS
        }
        lift_rows.append(
            {
                "candidate": cand,
                "baseline_pooled_auc": round(bl_pooled, 4),
                "cand_pooled_auc": round(cand_pooled, 4),
                "pooled_lift": round(pooled_lift, 4),
                "BCH_lift": round(per_sym_lift.get("BCHUSDT", float("nan")), 4),
                "LDO_lift": round(per_sym_lift.get("LDOUSDT", float("nan")), 4),
                "TRX_lift": round(per_sym_lift.get("TRXUSDT", float("nan")), 4),
            }
        )

        # SSC-RISK gate: max single-symbol |lift| vs |POOLED lift|
        ssc_max = max(
            abs(per_sym_lift.get(sym, float("nan"))) for sym in SYMBOLS
        )
        pooled_abs = abs(pooled_lift)
        if pooled_abs > 0:
            ssc_ratio = ssc_max / pooled_abs
        else:
            ssc_ratio = float("inf")
        ssc_carrier = max(SYMBOLS, key=lambda s: abs(per_sym_lift.get(s, 0.0)))
        ssc_risk = ssc_ratio > 2.0  # the gate threshold
        ssc_rows.append(
            {
                "candidate": cand,
                "pooled_lift": round(pooled_lift, 4),
                "pooled_abs": round(pooled_abs, 4),
                "max_single_sym_abs": round(ssc_max, 4),
                "max_carrier": ssc_carrier,
                "ssc_ratio": round(ssc_ratio, 2) if np.isfinite(ssc_ratio) else float("inf"),
                "ssc_risk": ssc_risk,
            }
        )
    lift_df = pd.DataFrame(lift_rows).sort_values("pooled_lift", ascending=False)
    ssc_df = pd.DataFrame(ssc_rows)
    lift_df.to_csv(out_dir / "T7_multivariate_lift_screen.csv", index=False)
    ssc_df.to_csv(out_dir / "T9_ssc_risk_gate.csv", index=False)
    print("[T7] multivariate lift screen committed:", out_dir / "T7_multivariate_lift_screen.csv")
    print(lift_df.to_string(index=False))
    print("[T9] SSC-RISK gate committed:", out_dir / "T9_ssc_risk_gate.csv")
    print(ssc_df.to_string(index=False))
    return lift_df, ssc_df


def step6_verdict_synthesis(
    t2: pd.DataFrame, t3: pd.DataFrame, t4: pd.DataFrame, t5: pd.DataFrame,
    t7: pd.DataFrame, t9: pd.DataFrame, out_dir: Path
) -> pd.DataFrame:
    """T6 — final GO/NO-GO verdict combining all upstream evidence."""
    # Merge per-candidate columns
    merged = t2[["candidate", "pooled_R2", "verdict"]].rename(
        columns={"verdict": "T2_verdict"}
    )
    merged = merged.merge(
        t3[["candidate", "pooled_auc", "p_value", "clears_q95"]], on="candidate"
    )
    merged = merged.merge(
        t4[["candidate", "n_g1_pass"]], on="candidate"
    )
    merged = merged.merge(
        t5[["candidate", "BCH", "LDO", "TRX"]].rename(
            columns={"BCH": "T5_BCH", "LDO": "T5_LDO", "TRX": "T5_TRX"}
        ),
        on="candidate",
    )
    merged = merged.merge(
        t7[["candidate", "pooled_lift"]].rename(
            columns={"pooled_lift": "T7_pooled_lift"}
        ),
        on="candidate",
    )
    merged = merged.merge(
        t9[["candidate", "ssc_ratio", "ssc_risk", "max_carrier"]],
        on="candidate",
    )

    # Decision: best-of-class on T7 POOLED lift (the production-relevant gate)
    # with secondary checks on T3 univariate, T5 importance, SSC-RISK
    verdicts = []
    for _, r in merged.iterrows():
        if r["T7_pooled_lift"] > 0.005 and not r["ssc_risk"]:
            v = "GO"
        elif r["T7_pooled_lift"] > 0.005 and r["ssc_risk"]:
            v = "GO-SSC-RISK"
        elif r["T7_pooled_lift"] > 0.000:
            v = "MARGINAL"
        elif r["clears_q95"] and r["T7_pooled_lift"] <= 0.000:
            v = "INERT-MULTIVARIATE"  # univariate signal collapses in multivariate
        else:
            v = "REJECT"
        verdicts.append(v)
    merged["verdict"] = verdicts
    merged = merged.sort_values("T7_pooled_lift", ascending=False)
    merged.to_csv(out_dir / "T6_go_nogo_verdict.csv", index=False)
    print("[T6] verdict synthesis committed:", out_dir / "T6_go_nogo_verdict.csv")
    print(merged.to_string(index=False))
    return merged


def main() -> None:
    out_dir = THIS_DIR
    print("=" * 78)
    print("iter-v3/119 — engineered-feature axis EDA (FINAL EXPLORATION of cycle 6)")
    print("=" * 78)

    # Load + label IS panels for all 3 symbols (cached panel-builder).
    df_per_sym: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        print(f"[load] {sym} ...")
        df = build_labeled_panel(sym)
        print(f"   rows={len(df)} (IS-only, label-valid, all-features-non-NaN)")
        df_per_sym[sym] = df

    step1_candidate_catalog(out_dir)

    t2 = step2_linear_redundancy_pre_falsifier(df_per_sym, out_dir)
    t3 = step3_pooled_univariate_auc(df_per_sym, out_dir)
    t4 = step3b_per_symbol_univariate_auc(df_per_sym, out_dir)
    t5 = step4_multivariate_importance(df_per_sym, out_dir)
    t7, t9 = step5_multivariate_lift_screen(df_per_sym, out_dir)
    t6 = step6_verdict_synthesis(t2, t3, t4, t5, t7, t9, out_dir)

    print("=" * 78)
    print("EDA COMPLETE — verdict synthesis:")
    print(t6.to_string(index=False))
    print("=" * 78)


if __name__ == "__main__":
    main()
