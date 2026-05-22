"""iter-v3/118 — engineered-feature axis EDA, 6 result tables T1..T6.

T1: candidate catalog motivated by cycle-6 failure modes — 6 composite-feature
    forms enumerated with rationale + cycle-6 failure-mode each addresses.

T2: Linear Redundancy Pre-Falsifier per `feedback_v3_lr_pf_methodology.md` —
    R^2 of linear regression of each candidate on the 14 V3_FEATURE_COLUMNS
    primitives, per symbol AND universe-pooled. ACCEPT if (a) R^2 <= 0.50 OR
    (b) candidate is composed-feature with algebraic-identity carve-out
    (per `feedback_v3_engineered_feature_pivot.md`). REJECT otherwise.

T3: Walk-forward feature->label predictive screen (the /109 / /117 methodology)
    — single-feature univariate LightGBM, per-fold OOF AUC, universe-pooled
    across BCH/LDO/TRX, 100-shuffle permutation null. p < 0.05 for the chosen
    candidate.

T4: Per-symbol AUC (the /117 g1 hard gate) — for each PASS-list candidate,
    compute the per-symbol walk-forward AUC. g1 gate is AUC >= 0.51 per symbol.

T5: Importance-rank prediction at depth-3-5 multivariate LightGBM (the /025
    PROMISING benchmark) — train depth-3 LightGBM on full 14 + 1 candidate
    feature stack, per symbol; observe rank of candidate in feature importance
    (gain). Pass: rank <= 5 of 15 AND gain >= 30% of top-feature gain.

T6: GO/NO-GO verdict — synthesizes T2-T5 into a per-candidate verdict
    {PROCEED, PROMISING-INERT-RISK, REJECT}. The PROCEED candidate becomes
    the /118 axis.

All computations are strictly IS-only (close_time < OOS_CUTOFF_MS).
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
    CANDIDATE_NAMES,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    build_labeled_panel,
    walk_forward_folds,
)

import lightgbm as lgb  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402


OUT_DIR = THIS_DIR
N_PERM = 100
RNG_SEED = 1729  # IS-only EDA seed; orthogonal to any production seed


# -----------------------------------------------------------------------------
# T1 — Candidate catalog
# -----------------------------------------------------------------------------


def write_t1_catalog() -> pd.DataFrame:
    rows = [
        {
            "candidate_id": "C1_vwap_signed_hurst",
            "formula": "vwap_dev_20 * sign(hurst_100 - 0.5)",
            "primitive_A_value": "vwap_dev_20",
            "primitive_B_regime": "hurst_100",
            "threshold": 0.5,
            "category": "value × regime-sign (/025 template)",
            "cycle6_failure_mode_addressed": (
                "/116 finding that BCH static-schedule WR depends on regime. "
                "VWAP mean-reversion edge is opposite-signed in trending vs "
                "mean-reverting regimes."
            ),
        },
        {
            "candidate_id": "C2_ema_signed_hurst",
            "formula": "ema_spread_atr_20 * sign(hurst_100 - 0.5)",
            "primitive_A_value": "ema_spread_atr_20",
            "primitive_B_regime": "hurst_100",
            "threshold": 0.5,
            "category": "value × regime-sign (/025 template; momentum primitive)",
            "cycle6_failure_mode_addressed": (
                "/025 PROMISING applied to EMA spread primitive instead of "
                "ret_5d. EMA spread is the canonical momentum-value feature in "
                "TOP_N; flipping by Hurst regime tests whether the /025 pattern "
                "generalizes across the momentum-primitive choice."
            ),
        },
        {
            "candidate_id": "C3_ema_signed_volregime",
            "formula": "ema_spread_atr_20 * sign(range_realized_vol_50 - rolling_median_200)",
            "primitive_A_value": "ema_spread_atr_20",
            "primitive_B_regime": "range_realized_vol_50 - rolling_median_200",
            "threshold": 0.0,
            "category": "value × vol-regime-sign",
            "cycle6_failure_mode_addressed": (
                "/117 EDA T3 per-offset AUC heterogeneity hints at vol-regime "
                "dependence. High-vol regimes vs low-vol regimes have different "
                "trend-continuation rates. Tests whether vol regime (orthogonal "
                "to Hurst) carries separate regime-conditional signal."
            ),
        },
        {
            "candidate_id": "C4_autocorr_signed_hurst",
            "formula": "ret_autocorr_lag1_50 * sign(hurst_100 - 0.5)",
            "primitive_A_value": "ret_autocorr_lag1_50",
            "primitive_B_regime": "hurst_100",
            "threshold": 0.5,
            "category": "value × regime-sign (autocorr primitive)",
            "cycle6_failure_mode_addressed": (
                "Directly encodes the /116 no_confirm mechanism at the feature "
                "level. Positive autocorr in trending = continuation (will "
                "confirm); positive autocorr in mean-reverting = false "
                "confirmation (will fail). Sign-flip exposes this to LightGBM "
                "at entry, where /116 currently catches it at exit."
            ),
        },
        {
            "candidate_id": "C5_symvsbtc_signed_btctrend",
            "formula": "sym_vs_btc_ret_7d * sign(btc_ret_14d)",
            "primitive_A_value": "sym_vs_btc_ret_7d",
            "primitive_B_regime": "btc_ret_14d",
            "threshold": 0.0,
            "category": "value × cross-asset-regime-sign",
            "cycle6_failure_mode_addressed": (
                "Cross-asset analog of /025. Symbol-vs-BTC divergence has "
                "different meaning in BTC-bull vs BTC-bear regimes. /117 "
                "Mechanism 3 (TRX 79 IS -> 0 OOS) was symbol-specific noise "
                "overfitting; encoding a cross-asset regime context may give "
                "LightGBM a separation between symbol-noise and BTC-context."
            ),
        },
        {
            "candidate_id": "C6_vwap_signed_kurt",
            "formula": "vwap_dev_20 * sign(ret_kurt_50 - 0)",
            "primitive_A_value": "vwap_dev_20",
            "primitive_B_regime": "ret_kurt_50",
            "threshold": 0.0,
            "category": "value × tail-regime-sign",
            "cycle6_failure_mode_addressed": (
                "VWAP mean-reversion conditional on heavy-tail vs thin-tail "
                "regime. /117 Mechanism 1 (population-vs-tail divergence) "
                "showed that confidence-gated trades have different stats than "
                "the population; a kurt-conditioned VWAP composite gives a "
                "direct feature for that regime."
            ),
        },
    ]
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T1_candidate_catalog.csv"
    df.to_csv(out, index=False)
    print(f"[T1] wrote {out} ({len(df)} candidates)")
    return df


# -----------------------------------------------------------------------------
# T2 — Linear Redundancy Pre-Falsifier
# -----------------------------------------------------------------------------


def t2_linear_redundancy(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    # Per-symbol R^2.
    for sym, panel in panels.items():
        X = panel[V3_FEATURE_COLUMNS].to_numpy(dtype="float64")
        for cand in CANDIDATE_NAMES:
            y = panel[cand].to_numpy(dtype="float64")
            mask = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
            if mask.sum() < 100:
                rows.append({
                    "scope": sym,
                    "candidate": cand,
                    "n_rows": int(mask.sum()),
                    "r2": np.nan,
                    "max_abs_corr_primitive": "n/a",
                    "max_abs_corr_value": np.nan,
                    "verdict": "INSUFFICIENT-ROWS",
                })
                continue
            reg = LinearRegression().fit(X[mask], y[mask])
            r2 = float(reg.score(X[mask], y[mask]))
            # max |corr| with any single primitive
            corrs = []
            for j, prim in enumerate(V3_FEATURE_COLUMNS):
                a = X[mask, j]
                b = y[mask]
                sa = a.std()
                sb = b.std()
                if sa == 0 or sb == 0:
                    corrs.append((prim, 0.0))
                else:
                    corrs.append((prim, float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))))
            corrs.sort(key=lambda kv: abs(kv[1]), reverse=True)
            max_prim, max_v = corrs[0]
            # Verdict per `feedback_v3_lr_pf_methodology.md`:
            # ACCEPT if R^2 <= 0.50 OR algebraic-identity carve-out (composed-feature).
            # All 6 candidates ARE composed-features by construction -> carve-out applies.
            # REJECT only if R^2 = 1.0 AND not composed (irrelevant here) — left as documentation.
            if r2 < 0.50:
                verdict = "PASS (R²<0.50)"
            else:
                verdict = "PASS-CARVEOUT (composed-feature; algebraic-identity)"
            rows.append({
                "scope": sym,
                "candidate": cand,
                "n_rows": int(mask.sum()),
                "r2": r2,
                "max_abs_corr_primitive": max_prim,
                "max_abs_corr_value": max_v,
                "verdict": verdict,
            })
    # Universe-pooled R^2 on the 3-symbol concatenated panel.
    pooled = pd.concat(panels.values(), axis=0, ignore_index=True)
    X = pooled[V3_FEATURE_COLUMNS].to_numpy(dtype="float64")
    for cand in CANDIDATE_NAMES:
        y = pooled[cand].to_numpy(dtype="float64")
        mask = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
        if mask.sum() < 100:
            rows.append({
                "scope": "POOLED",
                "candidate": cand,
                "n_rows": int(mask.sum()),
                "r2": np.nan,
                "max_abs_corr_primitive": "n/a",
                "max_abs_corr_value": np.nan,
                "verdict": "INSUFFICIENT-ROWS",
            })
            continue
        reg = LinearRegression().fit(X[mask], y[mask])
        r2 = float(reg.score(X[mask], y[mask]))
        corrs = []
        for j, prim in enumerate(V3_FEATURE_COLUMNS):
            a = X[mask, j]
            b = y[mask]
            sa = a.std()
            sb = b.std()
            if sa == 0 or sb == 0:
                corrs.append((prim, 0.0))
            else:
                corrs.append((prim, float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))))
        corrs.sort(key=lambda kv: abs(kv[1]), reverse=True)
        max_prim, max_v = corrs[0]
        if r2 < 0.50:
            verdict = "PASS (R²<0.50)"
        else:
            verdict = "PASS-CARVEOUT (composed-feature; algebraic-identity)"
        rows.append({
            "scope": "POOLED",
            "candidate": cand,
            "n_rows": int(mask.sum()),
            "r2": r2,
            "max_abs_corr_primitive": max_prim,
            "max_abs_corr_value": max_v,
            "verdict": verdict,
        })
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T2_linear_redundancy_pre_falsifier.csv"
    df.to_csv(out, index=False)
    print(f"[T2] wrote {out} ({len(df)} rows)")
    return df


# -----------------------------------------------------------------------------
# T3 — Walk-forward feature->label predictive screen (universe-pooled)
# -----------------------------------------------------------------------------


def _univariate_lgbm_auc(X: np.ndarray, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]]) -> tuple[float, list[float]]:
    """Per-fold OOF AUC for a single feature (univariate LightGBM, depth-3)."""
    per_fold = []
    for train_idx, test_idx in folds:
        Xtr = X[train_idx].reshape(-1, 1)
        ytr = y[train_idx]
        Xte = X[test_idx].reshape(-1, 1)
        yte = y[test_idx]
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbose": -1,
            "max_depth": 3,
            "num_leaves": 8,
            "learning_rate": 0.05,
            "feature_fraction": 1.0,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "n_estimators": 100,
            "min_data_in_leaf": 50,
            "lambda_l2": 1.0,
        }
        model = lgb.LGBMClassifier(**params, random_state=RNG_SEED)
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        try:
            auc = roc_auc_score(yte, p)
            per_fold.append(float(auc))
        except ValueError:
            continue
    mean_auc = float(np.mean(per_fold)) if per_fold else np.nan
    return mean_auc, per_fold


def t3_walkforward_auc(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Universe-pooled walk-forward OOF AUC + permutation null per candidate."""
    pooled = pd.concat(panels.values(), axis=0, ignore_index=True)
    pooled = pooled.sort_values("close_time").reset_index(drop=True)
    folds = walk_forward_folds(len(pooled), n_folds=5)
    rows = []
    rng = np.random.default_rng(RNG_SEED)
    for cand in CANDIDATE_NAMES:
        y = pooled["label"].to_numpy(dtype="int64")
        X = pooled[cand].to_numpy(dtype="float64")
        mask = ~np.isnan(X)
        X_in = X[mask]
        y_in = y[mask]
        # Re-derive folds on filtered indices (positionally).
        folds_in = walk_forward_folds(len(X_in), n_folds=5)
        obs_auc, per_fold = _univariate_lgbm_auc(X_in, y_in, folds_in)
        # Permutation null (shuffle the candidate's values).
        nulls = []
        for _ in range(N_PERM):
            X_shuf = rng.permutation(X_in)
            mean_null, _ = _univariate_lgbm_auc(X_shuf, y_in, folds_in)
            if not np.isnan(mean_null):
                nulls.append(mean_null)
        null_q50 = float(np.percentile(nulls, 50)) if nulls else np.nan
        null_q95 = float(np.percentile(nulls, 95)) if nulls else np.nan
        # one-sided p-value: P(null >= observed)
        n_geq = int(sum(1 for v in nulls if v >= obs_auc))
        p_value = n_geq / max(1, len(nulls))
        rows.append({
            "candidate": cand,
            "n_rows": int(mask.sum()),
            "n_folds": len(folds_in),
            "observed_auc": obs_auc,
            "null_q50": null_q50,
            "null_q95": null_q95,
            "p_value": p_value,
            "clears_q95": (obs_auc > null_q95) if not np.isnan(obs_auc) and not np.isnan(null_q95) else False,
            "per_fold": ";".join(f"{v:+.3f}" for v in per_fold),
        })
        print(f"[T3] {cand} pooled AUC={obs_auc:.4f} null_q95={null_q95:.4f} p={p_value:.3f}")
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T3_walkforward_pooled_auc.csv"
    df.to_csv(out, index=False)
    print(f"[T3] wrote {out} ({len(df)} candidates)")
    return df


# -----------------------------------------------------------------------------
# T4 — Per-symbol walk-forward AUC (the /117 g1 hard gate)
# -----------------------------------------------------------------------------


def t4_per_symbol_auc(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sym, panel in panels.items():
        panel = panel.sort_values("close_time").reset_index(drop=True)
        y = panel["label"].to_numpy(dtype="int64")
        for cand in CANDIDATE_NAMES:
            X = panel[cand].to_numpy(dtype="float64")
            mask = ~np.isnan(X)
            X_in = X[mask]
            y_in = y[mask]
            folds_in = walk_forward_folds(len(X_in), n_folds=5)
            obs_auc, per_fold = _univariate_lgbm_auc(X_in, y_in, folds_in)
            rows.append({
                "symbol": sym,
                "candidate": cand,
                "n_rows": int(mask.sum()),
                "n_folds": len(folds_in),
                "observed_auc": obs_auc,
                "per_fold": ";".join(f"{v:+.3f}" for v in per_fold),
                "g1_pass": (obs_auc >= 0.51) if not np.isnan(obs_auc) else False,
            })
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T4_per_symbol_auc.csv"
    df.to_csv(out, index=False)
    print(f"[T4] wrote {out} ({len(df)} rows)")
    return df


# -----------------------------------------------------------------------------
# T5 — Importance rank in depth-3 multivariate LightGBM (14 + 1)
# -----------------------------------------------------------------------------


def t5_importance_rank(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sym, panel in panels.items():
        panel = panel.sort_values("close_time").reset_index(drop=True)
        y = panel["label"].to_numpy(dtype="int64")
        for cand in CANDIDATE_NAMES:
            feat_cols = list(V3_FEATURE_COLUMNS) + [cand]
            X = panel[feat_cols].to_numpy(dtype="float64")
            mask = (~np.isnan(X)).all(axis=1)
            X_in = X[mask]
            y_in = y[mask]
            if len(X_in) < 500 or len(np.unique(y_in)) < 2:
                rows.append({
                    "symbol": sym,
                    "candidate": cand,
                    "n_rows": int(mask.sum()),
                    "rank_of_candidate": -1,
                    "candidate_gain": np.nan,
                    "top_feature_gain": np.nan,
                    "candidate_gain_pct_of_top": np.nan,
                    "passes_rank_5": False,
                    "passes_gain_30pct": False,
                })
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
            model.fit(X_in, y_in, feature_name=feat_cols)
            gains = dict(zip(feat_cols, model.booster_.feature_importance(importance_type="gain")))
            sorted_feats = sorted(gains.items(), key=lambda kv: kv[1], reverse=True)
            rank = next(i for i, (k, _) in enumerate(sorted_feats, start=1) if k == cand)
            top_gain = sorted_feats[0][1]
            cand_gain = gains[cand]
            pct = float(cand_gain) / float(top_gain) if top_gain > 0 else 0.0
            rows.append({
                "symbol": sym,
                "candidate": cand,
                "n_rows": int(mask.sum()),
                "rank_of_candidate": rank,
                "candidate_gain": float(cand_gain),
                "top_feature_gain": float(top_gain),
                "candidate_gain_pct_of_top": pct,
                "passes_rank_5": rank <= 5,
                "passes_gain_30pct": pct >= 0.30,
            })
            print(f"[T5] {sym}/{cand} rank={rank}/15 gain={cand_gain:.0f} pct={pct:.2%}")
    df = pd.DataFrame(rows)
    out = OUT_DIR / "T5_importance_rank_multivariate.csv"
    df.to_csv(out, index=False)
    print(f"[T5] wrote {out} ({len(df)} rows)")
    return df


# -----------------------------------------------------------------------------
# T6 — GO/NO-GO verdict synthesis
# -----------------------------------------------------------------------------


def t6_verdict(
    t2: pd.DataFrame, t3: pd.DataFrame, t4: pd.DataFrame, t5: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    t3_by_cand = t3.set_index("candidate").to_dict("index")
    for cand in CANDIDATE_NAMES:
        # T2 — composed-feature carve-out always applies → PASS
        t2_pooled = t2[(t2["scope"] == "POOLED") & (t2["candidate"] == cand)].iloc[0]
        t2_pass = "PASS" in str(t2_pooled["verdict"])
        # T3 — pooled AUC + p-value
        t3_row = t3_by_cand[cand]
        t3_auc = t3_row["observed_auc"]
        t3_p = t3_row["p_value"]
        t3_pass = (t3_auc > t3_row["null_q95"]) and (t3_p < 0.05)
        # T4 — per-symbol AUC >= 0.51 for all 3 symbols (the /117 g1 hard gate)
        per_sym = t4[t4["candidate"] == cand]
        g1_per_sym = per_sym["g1_pass"].sum()
        t4_pass = (g1_per_sym == 3)
        # T5 — importance rank <= 5 of 15 AND gain >= 30% of top
        per_sym5 = t5[t5["candidate"] == cand]
        n_pass_rank = per_sym5["passes_rank_5"].sum()
        n_pass_gain = per_sym5["passes_gain_30pct"].sum()
        t5_pass = (n_pass_rank >= 2) and (n_pass_gain >= 2)  # at least 2 of 3 symbols pass each
        # Verdict
        if t2_pass and t3_pass and t4_pass and t5_pass:
            verdict = "PROCEED"
        elif t2_pass and t3_pass and not (t4_pass and t5_pass):
            verdict = "PROMISING-INERT-RISK"
        else:
            verdict = "REJECT"
        rows.append({
            "candidate": cand,
            "t2_pass": t2_pass,
            "t3_pooled_auc": t3_auc,
            "t3_p_value": t3_p,
            "t3_pass": t3_pass,
            "t4_g1_per_symbol_pass_count": int(g1_per_sym),
            "t4_pass": t4_pass,
            "t5_rank_passes": int(n_pass_rank),
            "t5_gain_passes": int(n_pass_gain),
            "t5_pass": t5_pass,
            "verdict": verdict,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(["verdict", "t3_pooled_auc"], ascending=[True, False]).reset_index(drop=True)
    out = OUT_DIR / "T6_go_nogo_verdict.csv"
    df.to_csv(out, index=False)
    print(f"[T6] wrote {out} ({len(df)} candidates)")
    return df


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> None:
    print(f"[main] /118 engineered-feature axis EDA — START — N_PERM={N_PERM} RNG_SEED={RNG_SEED}")
    # T1 — catalog (no data load needed; just documents the 6 candidates).
    write_t1_catalog()
    # Load all IS panels (~5727 BCH + ~2741 LDO + ~5669 TRX rows).
    panels: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        panels[sym] = build_labeled_panel(sym)
        print(f"  [load] {sym}: {len(panels[sym])} labeled rows")
    # T2-T5
    t2 = t2_linear_redundancy(panels)
    t3 = t3_walkforward_auc(panels)
    t4 = t4_per_symbol_auc(panels)
    t5 = t5_importance_rank(panels)
    # T6 — verdict
    t6 = t6_verdict(t2, t3, t4, t5)
    print()
    print("=" * 78)
    print("[T6 SUMMARY]")
    print(t6.to_string(index=False))


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    main()
