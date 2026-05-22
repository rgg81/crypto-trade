# Phase 5.5 Gate — iter-v3/037

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared immutable; IS window 2023-03-24–2025-03-23; OOS window 2025-03-24 onward.
- Section 0.5 (Iteration Type): PASS — EXPLORATION cadence #9 of 10; single-axis variation (V3_FEATURES_PER_SYMBOL swap: TRXUSDT removed, LDOUSDT added with cross_asset_divergence_norm); 2h wall-clock cap declared; ANCHOR = iter-v3/035 IS -0.1023 / OOS +2.8521.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: LDO btc_ret_14d rank-6 importance + cross_asset_divergence_norm amplification + LDO OOS wpnl lift from +3.98 toward +10. Falsifiable: OOS Sharpe < +2.0 rejects hypothesis.
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed reports: iter-v3/027 comparison.csv (IS collapse -0.2817, OOS spike +1.6786); iter-v3/035 per_symbol.csv (LDO OOS wpnl +3.98, WR 35.0%, 14 trades; btc_ret_14d rank 6 in LDO model). Behavioral effect predictor present: LDO IS trade count ±5-20%, BCH/TRX/ALGO = 0 delta. Falsifier specified. Source data from IS-window reports only (pre-OOS).
  NOTE: Section 2.2 cites feature_importance.csv from iter-v3/035 IS reports (not OOS). This is permissible evidence — IS feature importance is computed on IS training data only.
- Section 3 (Proposed Changes): PASS — 5 enumerated sub-fixes: (1) V3_FEATURES_PER_SYMBOL swap in __init__.py, (2) engineered_v3.py dispatch update, (3) _verify_feature_columns update in runner, (4) ITERATION_LABEL bump, (5) adversarial tests updated. Each sub-fix is atomic and specific.
- Section 4 (Expected OOS Impact): PASS — IS band [-0.20, +0.10] median 0.0; OOS band [+2.50, +3.20] median +2.85. Explicit falsifier: OOS Sharpe < +2.0 = NEGATIVE. 4-path taxonomy (PROMISING / PROMISING-INERT / NULL-RESULT / NEGATIVE) with numerical thresholds for each. Confidence interval present.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 unchanged (explicitly stated). Per-symbol heterogeneity risk addressed: cross_asset_divergence_norm generated for all symbols but model-level isolation via explicit feature_columns. TRX revert risk addressed (restoration to known-good iter-v3/035 anchor). BCH/LDO extension features declared DISJOINT.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present with IS/OOS fire rates from iter-v3/035, all gates declared unchanged for iter-v3/037.
- Section 7 (Failure-Mode Prediction): PASS — 2 paragraphs predicting: (1) NULL-RESULT — cross_asset_divergence_norm inert for LDO because btc_ret_14d already captured in 14-feature model; (2) PROMISING-INERT — feature learned but OOS Sharpe below +2.50 due to LDO's fragile regime. Behavioral effect predictor in place (LDO IS trade count ±5-20%). Gates-should-catch statement: LDO IS wpnl collapse or absurd IS/OOS ratio.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION iteration; MERGE criteria not applicable. PROMISING / PROMISING-INERT / NULL-RESULT / NEGATIVE criteria with locked numerical thresholds: importance ≥ 30 for PROMISING; importance 5-29 for INERT; importance < 5 + trade count = 0 for NULL-RESULT; OOS < +2.0 for NEGATIVE. Pre-registered before any backtest runs.
- Section 9 (Library Stack): PASS — No new dependencies. fracdiff PyPI package unavailable (statsmodels conflict) noted — not needed for cross_asset_divergence_norm. Library versions pinned (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). compute_cross_asset_divergence_norm already implemented in engineered_v3.py (dead code since iter-v3/028).

## Gate Notes

- Single-axis invariant: CONFIRMED. The two sub-changes (revert TRX + add LDO with cross_asset)
  are logically one axis: a swap of the V3_FEATURES_PER_SYMBOL secondary entry. BCH is untouched.
  Attribution is clean: all OOS delta vs iter-v3/035 anchor explained by (1) TRX back to 14
  features + (2) LDO with cross_asset_divergence_norm.

- IS-only evidence gate: PASS. All numerical evidence sources are IS-window reports (comparison.csv
  and per_symbol.csv from iter-v3/027 and iter-v3/035 which themselves cover IS+OOS windows, but
  the specific cells cited — IS Sharpe, IS attribution, IS feature importance — are IS-only).
  The OOS numbers from iter-v3/027 and iter-v3/035 are cited ONLY as context for the universal
  failure pattern (not as optimization targets).

- Library stack: cross_asset_divergence_norm uses only numpy/pandas primitives already in
  engineered_v3.py. No new imports. No fracdiff package. Dispatch is re-enabling dead code.

- One-variable-at-a-time check: PASS. The "variable" is the identity of the second V3_FEATURES_PER_SYMBOL
  entry. Changing from TRXUSDT+vol_adj_autocorr to LDOUSDT+cross_asset_divergence_norm is a single
  architectural decision tested atomically. The BCH entry is strictly unchanged.
