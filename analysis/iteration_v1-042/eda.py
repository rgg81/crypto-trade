"""iter-v1/042 EDA — XGBoost head-to-head theoretical analysis.

This iteration is a MODEL-ARCH library swap (LightGBM → XGBoost) with NO new
features and NO new data slicing. The "EDA" therefore reduces to:

  1. Document existing XGBoost infrastructure (already shipped at iter-v3/016).
  2. Quantify the architectural delta on the v1 5-cohort 8h 43-feature regime.
  3. Compare per-cohort training-cell sizes to XGBoost's depth-wise capacity
     envelope (vs LightGBM leaf-wise) — predict where bias/variance shifts.
  4. Predict F1 modal verdict band using v3/016 precedent + v1 regime delta.

NO new feature columns introduced. NO src/ change.

Run:
  uv run python analysis/iteration_v1-042/eda.py
"""
from __future__ import annotations

import json
from pathlib import Path

# Hard-coded constants from BASELINE_V1.md / V1_FEATURE_COLUMNS_PRUNED / v1 cohort spec
N_FEATURES_V1 = 43           # V1_FEATURE_COLUMNS_PRUNED post /034 basis_zscore_30 addition
N_FEATURES_V3 = 13           # iter-v3/013 baseline (cf. iter-v3/016 review.md Check 8)
N_FEATURES_V3_016 = 13       # XGBoost was head-to-head on this stack
N_COHORTS_V1 = 4             # Model A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT)
N_COHORTS_V3 = 3             # BCH, LDO, TRX (per-symbol)
TRAINING_MONTHS = 24         # SACRED CONSTANT; walk-forward window
BARS_PER_8H_MONTH = 90       # ~30 days * 3 bars/day at 8h
# Per /024 brief Section 0.7 numbers; carry over for v1 cell sizing.
IS_BARS_POOL_A = 5727 * 2    # Pool A pools BTC+ETH (~11k bars per training cell)
IS_BARS_LINK = 5727          # single-symbol cohort
IS_BARS_LTC = 5727
IS_BARS_DOT = 4975           # listed late; fewer bars

# v3/016 outcomes (Critic FINAL `a20c54b`)
V3_016_IS_SHARPE = 0.5524    # Δ -0.46 vs v3/013 +1.0088 (PATH B fired)
V3_016_OOS_SHARPE = 0.171
V3_016_OOS_MAXDD = 0.4062    # 40.62% (4.26× inflation vs v3/013 12.47%)
V3_013_OOS_MAXDD = 0.1247
V3_016_PORTFOLIO_CONCENTRATION = 2.58  # 258% — single-seed degenerate

# BASELINE_V1 anchor numbers (per BASELINE_V1.md `f8bc12c`)
V1_ANCHOR_IS_SHARPE = 0.2829
V1_ANCHOR_OOS_SHARPE = 0.6637
V1_ANCHOR_OOS_TRADES = 189
V1_ANCHOR_IS_TRADES = 621


def architectural_delta_table() -> list[dict]:
    """Side-by-side architectural deltas LightGBM vs XGBoost (depthwise/hist)."""
    rows = [
        {
            "axis": "Tree growth",
            "LightGBM": "leaf-wise (best-first)",
            "XGBoost (pinned)": "depth-wise (level-wise)",
            "bias-variance effect": "depth-wise → LOWER variance per cell (more conservative); LightGBM leaf-wise greedier on small training cells",
        },
        {
            "axis": "Bin algorithm",
            "LightGBM": "histogram + GOSS",
            "XGBoost (pinned)": "histogram (tree_method='hist')",
            "bias-variance effect": "neutral; both bin to 255 buckets; GOSS gradient sampling absent in XGB → no early-stop on low-gradient rows → slower convergence at same n_estimators",
        },
        {
            "axis": "Class imbalance",
            "LightGBM": "is_unbalance=True (auto)",
            "XGBoost (pinned)": "scale_pos_weight = n_neg / n_pos (per-fit)",
            "bias-variance effect": "v1 triple-barrier labels ~symmetric; effect SMALL on portfolio attribution",
        },
        {
            "axis": "Optuna search dim",
            "LightGBM": "num_leaves + max_depth (7 hp)",
            "XGBoost (pinned)": "max_depth only (6 hp; num_leaves dropped — no-op under depthwise)",
            "bias-variance effect": "1 fewer dim → faster Optuna convergence at same n_trials; v3/016 n_eff dropped 7→6 (one dim collapsed)",
        },
        {
            "axis": "Default leaf cap",
            "LightGBM": "num_leaves=31 (~depth 5)",
            "XGBoost (pinned)": "max_depth ∈ [3,5] strict",
            "bias-variance effect": "XGBoost CAPPED at depth 5; LightGBM with num_leaves=31 + max_depth=5 can reach 31-leaf complex trees on a tight depth budget — XGBoost's depth-5 ceiling is 32 leaves but typically grows fewer because depth-wise is balanced not greedy",
        },
        {
            "axis": "Determinism",
            "LightGBM": "n_jobs=1 + seed",
            "XGBoost (pinned)": "n_jobs=1 + seed",
            "bias-variance effect": "both deterministic at single-thread",
        },
        {
            "axis": "Library version",
            "LightGBM": ">=4.0",
            "XGBoost (pinned)": ">=2.0,<3.0 (already in pyproject from iter-v3/016)",
            "bias-variance effect": "infrastructure ready; pyproject pin already at right semver",
        },
    ]
    return rows


def v1_v3_regime_delta_table() -> list[dict]:
    """How v1's regime differs from v3/016's tested regime."""
    rows = [
        {
            "dim": "Feature count",
            "v3/016 (XGB tested here)": f"{N_FEATURES_V3_016}",
            "v1/042 (XGB to be tested)": f"{N_FEATURES_V1}",
            "expected XGB sensitivity": "+ : XGBoost's depth-wise growth scales well with feature count; LightGBM leaf-wise more prone to per-leaf over-specialization on small training cells — relative advantage SHIFTS toward XGB at higher d/n ratio",
        },
        {
            "dim": "Universe / cohorts",
            "v3/016 (XGB tested here)": f"{N_COHORTS_V3} per-symbol",
            "v1/042 (XGB to be tested)": f"{N_COHORTS_V1} (Pool A pooled + 3 single-sym)",
            "expected XGB sensitivity": "+ : Pool A (BTC+ETH pooled) = larger training cell ~11k bars favoring depth-wise's bias/variance tradeoff; v3 per-symbol cells were ~5-6k bars where leaf-wise's greediness fits noise faster",
        },
        {
            "dim": "Candle frequency",
            "v3/016 (XGB tested here)": "8h",
            "v1/042 (XGB to be tested)": "8h",
            "expected XGB sensitivity": "neutral; same frequency = same per-cell trade density",
        },
        {
            "dim": "n_trials Optuna budget",
            "v3/016 (XGB tested here)": "10",
            "v1/042 (XGB to be tested)": "18 (v1 EXPLORATION standard)",
            "expected XGB sensitivity": "+ : 80% more trials → less under-explored region; v3/016 n_eff=6 was already low — at n_trials=18 XGBoost should reach n_eff~10-12 reducing single-seed lottery",
        },
        {
            "dim": "ENSEMBLE_SIZE",
            "v3/016 (XGB tested here)": "1 (single inner seed)",
            "v1/042 (XGB to be tested)": "3 (v1 EXPLORATION standard)",
            "expected XGB sensitivity": "+ : 3-seed inner ensemble averages out depth-wise's slightly different basin locations — reduces single-trial variance on top of n_trials lift",
        },
        {
            "dim": "Class distribution",
            "v3/016 (XGB tested here)": "triple-barrier 8h",
            "v1/042 (XGB to be tested)": "triple-barrier 8h EWMA-σ_t (same)",
            "expected XGB sensitivity": "neutral; same labeling discipline",
        },
        {
            "dim": "Risk gates",
            "v3/016 (XGB tested here)": "RiskV3Wrapper (vol/ADX/Hurst/OOD/low-vol/hit-rate/BTC-trend)",
            "v1/042 (XGB to be tested)": "R1 cooldown + R2 DD-scaling (DOT only) + R3 OOD Mahalanobis",
            "expected XGB sensitivity": "+ : v1's risk gates are SOFTER post-prediction; v3's 7-gate stack chops more aggressively → XGB's more-conservative predictions had less surface to express in v3, more surface in v1",
        },
    ]
    return rows


def per_cohort_capacity_table() -> list[dict]:
    """Per-cohort capacity analysis for depth-wise vs leaf-wise on training cells."""
    cells = [
        ("Pool A (BTC+ETH)", IS_BARS_POOL_A, "pooled"),
        ("LINK", IS_BARS_LINK, "single-symbol"),
        ("LTC", IS_BARS_LTC, "single-symbol"),
        ("DOT", IS_BARS_DOT, "single-symbol"),
    ]
    rows = []
    for name, n_bars, kind in cells:
        # Trees capacity: at max_depth=5, max 32 leaves
        # Per-leaf samples: n_bars / 32 = effective per-leaf training count
        per_leaf_samples = n_bars / 32
        # LightGBM's leaf-wise can reach 31 leaves at num_leaves=31 with much less depth (effectively depth ~5-8)
        # XGBoost depth-wise at max_depth=5 has SYMMETRIC tree; typically grows 16-32 leaves on real data
        rows.append({
            "cohort": name,
            "kind": kind,
            "IS bars/cell (~24m)": n_bars,
            "per-leaf samples at 32 leaves": int(per_leaf_samples),
            "leaf-wise risk (LightGBM)": "MEDIUM" if per_leaf_samples < 200 else "LOW",
            "depth-wise verdict (XGB)": "stable: symmetric growth caps per-leaf overfit",
        })
    return rows


def predicted_band() -> dict:
    """F1 verdict band prediction per axis spec (sums to 1.0)."""
    band = {
        "INERT_30%_MODAL": {
            "weight": 0.30,
            "definition": "OOS Sharpe Δ within ±0.10 of v1 anchor +0.6637",
            "rationale": "library-swap on same data + same features + same labels often produces ≤0.1 Sharpe Δ when both libraries are converged to similar regions of CV-Sharpe surface; v3/016 hit -2.53 because per-symbol cell sizes were ~5k bars + n_trials=10 + ENSEMBLE_SIZE=1 (worst-case lottery); v1's 11k Pool A bars + n_trials=18 + ENSEMBLE_SIZE=3 makes the +0.5σ lottery less likely",
        },
        "PROMISING_INERT_FAV_25%": {
            "weight": 0.25,
            "definition": "OOS Sharpe Δ ∈ (+0.10, +0.30) — modest favorable",
            "rationale": "if Pool A's 11k bars allow XGBoost depth-wise to outperform LightGBM leaf-wise on the pooled cell (where leaf-wise greediness can over-specialize on BTC vs ETH cross-asset interactions that don't generalize), portfolio Δ would lift +0.10 to +0.30",
        },
        "NEG_CLEAN_20%": {
            "weight": 0.20,
            "definition": "OOS Sharpe Δ ∈ [-0.45, -0.10]",
            "rationale": "v3/016 precedent strongly suggests negative; if v3's mechanism (XGB depth-wise more conservative → fewer signals → weaker OOS) transfers to v1 we land here",
        },
        "NEG_CAT_15%": {
            "weight": 0.15,
            "definition": "OOS Sharpe Δ < -0.45",
            "rationale": "v3/016 fired exactly NEG-CAT at -2.53; if v1's 43-feature stack triggers similar single-seed lottery on small altcoin cohorts (LINK/LTC/DOT) we replicate the pattern — risk is LOWER than v3 by ~50% due to ENSEMBLE_SIZE=3 and n_trials=18",
        },
        "PROMISING_CLEAN_10%": {
            "weight": 0.10,
            "definition": "OOS Sharpe Δ > +0.30",
            "rationale": "tail: XGB significantly outperforms LightGBM. Requires (a) depth-wise meaningfully beats leaf-wise on this regime AND (b) basin migration favors OOS rather than IS over-fit. LOW prior because both libraries have been benchmarked equivalent on tabular structured data in published benchmarks (LightGBM Tabular Survey, Shwartz-Ziv 2022) with at-best ~5% MAE diff",
        },
    }
    assert abs(sum(b["weight"] for b in band.values()) - 1.0) < 1e-9
    return band


def main() -> dict:
    output = {
        "iteration": "iter-v1/042",
        "axis_family": "model-arch (REPEAT — 2nd in v1 history; first since /024)",
        "axis_description": "LightGBM → XGBoost head-to-head library swap; depth-wise + tree_method='hist' pinned; max_depth ∈ [3,5]; n_trials=18; ENSEMBLE_SIZE=3; single outer seed=42; same V1_FEATURE_COLUMNS_PRUNED (43 cols); same 4 cohorts (Pool A pooled, LINK, LTC, DOT); same R1/R2/R3 baseline; same triple-barrier EWMA-σ_t labels",
        "infrastructure_status": {
            "src_module_xgb_py_loc": 712,
            "src_module_optimization_xgb_py_loc": 396,
            "test_smoke_loc": 219,
            "xgboost_in_pyproject": True,
            "xgboost_version_pin": ">=2.0,<3.0",
            "shipped_at": "iter-v3/016 (commit `a20c54b`); fully reusable",
            "v1_wiring_needed": "ONLY: --model xgboost CLI flag dispatch in v1 runner; XgboostStrategy already library-agnostic on feature_columns and ensemble_seeds",
        },
        "architectural_deltas": architectural_delta_table(),
        "v1_v3_regime_deltas": v1_v3_regime_delta_table(),
        "per_cohort_capacity": per_cohort_capacity_table(),
        "predicted_band_F1": predicted_band(),
        "v3_precedent_context": {
            "v3_016_verdict": "EXPLORATION-NEGATIVE (clean) — OOS Sharpe +0.171 vs v3/013 +2.697",
            "v3_016_is_sharpe_delta": V3_016_IS_SHARPE - 1.0088,
            "v3_016_oos_maxdd_inflation": V3_016_OOS_MAXDD / V3_013_OOS_MAXDD,
            "v3_016_concentration_artifact": V3_016_PORTFOLIO_CONCENTRATION,
            "v3_to_v1_transfer_strength": "MEDIUM-LOW per LM Master /038 Rec 3 — different feature stack (13 vs 43), different cohort structure (3 per-sym vs 4 with Pool A pooled), different Optuna budget (10 vs 18), different ENSEMBLE_SIZE (1 vs 3)",
            "key_caveat": "v3/016's NEG-CAT was DRIVEN BY single-seed lottery on small altcoin cells (per Critic Clarification 2 — 'importance-divergence finding NOT structurally validated'); v1 mitigates this by ENSEMBLE_SIZE=3",
        },
        "top_concerns": [
            "C1: Optuna n_eff=6 at n_trials=10 in v3/016 was already low; even with n_trials=18 at 6/7 dim ratio (n_eff~12) v1 single-seed Pareto MAY land in a different basin than LightGBM and outcome is regime-dependent on which basin",
            "C2: XGBoost depth-wise's MORE CONSERVATIVE predictions translate to FEWER trades downstream; F-AXIS #2 should monitor OOS trade-count: predicted band is [110, 240] vs anchor 189 — outside this band signals architectural divergence",
            "C3: v3/016 produced 4.26× MaxDD inflation — single-symbol concentration of XGB's output can SPIKE drawdown even when Sharpe is comparable; v1's Pool A pooling MAY mitigate (BTC+ETH pooling = built-in diversifier within the pooled-model cell)",
        ],
    }
    out_path = Path(__file__).parent / "eda_output.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"[iter-v1/042 EDA] wrote {out_path}")
    print(f"  Predicted modal: INERT 30% / PROMISING-INERT-FAV 25% / NEG-CLEAN 20% / NEG-CAT 15% / PROMISING-CLEAN 10%")
    print(f"  Combined PROMISING: 35% / Combined NEG: 35%")
    print(f"  Top concern: single-seed-lottery basin sensitivity (C1) mitigated 50% by ENSEMBLE_SIZE=3 vs v3/016's 1")
    return output


if __name__ == "__main__":
    main()
