# Phase 5.5 Gate — iter-v3/042

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly stated and flagged IMMUTABLE. IS window 2023-03-24 → 2025-03-23 and OOS window 2025-03-24 onward named in absolute dates.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific mechanism: universal (1.5, 0.75) ATR multipliers lift IS Sharpe by reducing trade-duration variance via tighter barriers, analogous to iter-v3/032 LDO-specific improvement.
- Section 2 (IS-Only Evidence): PASS — Cites committed analysis script `analysis/iteration_v3-032/per_symbol_atr_eda.py` (SHA `9834e84`). IS-only natr_21_raw distribution table with per-symbol medians (LDOUSDT 5.01 vs peer 3.70, ratio 1.35×). Effective barrier width table at (2.0,1.0) vs (1.5,0.75) for all 4 symbols. Behavioral-effect predictor: +15% to +35% IS trade count change, with falsifier (< 10% or > 60%). No OOS data used.
- Section 3 (Proposed Changes): PASS — 7 enumerated sub-fixes: (1) restore V3_FEATURE_COLUMNS_TOP_N to 14, (2) change DEFAULT_ATR_MULTIPLIERS to (1.5, 0.75), (3) keep V3_ATR_MULTIPLIERS_PER_SYMBOL empty, (4) keep V3_FEATURES_PER_SYMBOL empty, (5) update ITERATION_LABEL, (6) update _verify_feature_columns, (7) update adversarial tests. Bundle state verification table with PASS assertions.
- Section 4 (Expected OOS Impact): PASS — IS predicted band [+0.40, +1.00] median +0.65; OOS predicted band [+1.20, +2.00] median +1.60. Three pre-registered paths (A/B/C) with explicit IS and OOS thresholds. OOS falsifier: OOS < +1.57 triggers NEGATIVE.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly called out as unchanged. Barrier-tightening noise risk analyzed (BCH/TRX natr at 3.23/3.37 gives SL barrier ~2.42%/2.53%). IS SL rate escalation threshold stated (> 75% per symbol). Concentration risk acknowledged with per-symbol audit commitment.
- Section 6 (Risk Management Design): PASS — 7-primitive gate table present with all gates listed (BTC trend, hit-rate, ADX, Hurst, R2 drawdown, OOD z-score, liquidity floor). Gate parameter changes all "None" except OOD feature space noted as RESTORED to 14. ATR multiplier distinction from gates explained (labeling layer only).
- Section 7 (Failure-Mode Prediction): PASS — Three forward-looking failure modes: (1) BCH/TRX regime mismatch NEGATIVE/INERT; (2) single-seed lottery false IS lift; (3) ALGO+LDO concentration shift. Gate efficacy predictions stated (OOD firing rate return to iter-v3/040 baseline, R2 brake timing). Behavioral effect predictor with falsifier included.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Explicitly labeled EXPLORATION (no MERGE gates). Three classification paths A/B/C with locked numerical thresholds: PATH A (IS >= +0.89 AND OOS >= +1.57), PATH B (IS in [+0.59, +0.89] AND OOS >= +1.57), PATH C (OOS < +1.57). "Locked and cannot be post-hoc renegotiated" stated explicitly.
- Section 9 (Library Stack): PASS — 8 packages with explicit versions listed (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). No mlfinlab/mlfinpy/pypbo/fracdiff. No fallbacks needed.

## Reasons (if BLOCK)

None — all 10 sections PASS.

## Gate Notes

- Single-axis discipline CONFIRMED: Part A (14-feature restore) is a mandatory pre-commit revert triggered by iter-v3/041 Path C outcome; Part B (DEFAULT_ATR change) is the single new variation. Both are atomic and inseparable — restoring features without changing ATR would merely reproduce iter-v3/040 bit-identically, which is not a valid EXPLORATION axis.
- Section 2 analysis script SHA `9834e84` (iter-v3/032) is the canonical IS-only evidence. No new analysis script required because the natr_21_raw EDA universe (BCH+LDO+TRX+ALGO) has not changed since iter-v3/032.
- `feedback_v3_engineered_features_proven.md` mandate for `regime_momentum_signed_5d` is REINSTATED per iter-v3/041 Path C. The _verify_feature_columns positive assertion is required.
- EXPLORATION spec (--seeds 1, n_trials=35) is correctly declared in Section 0.5.
