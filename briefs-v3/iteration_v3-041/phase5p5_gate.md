# Phase 5.5 Gate — iter-v3/041

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed immutable; IS window 2023-03-24 to 2025-03-23; OOS 2025-03-24 onward.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #2 of 10, single-axis UNIVERSAL FEATURE PRUNING (V3_FEATURE_COLUMNS_TOP_N 14 → 11), PROMISING/PROMISING-INERT predicted; --seeds 1 EXPLORATION-spec; n_trials=35 default; colsample_bytree Optuna-tunable.
- Section 1 (Hypothesis): PASS — specific one-sentence hypothesis: dropping the 3 lowest-importance features (regime_momentum_signed_5d, sym_vs_btc_ret_7d, ret_skew_50) lifts IS Sharpe toward +1.0 by reducing Optuna search-space noise and maintains OOS Sharpe near anchor (+1.77) because dropped features carry only 17.6% of total split-importance.
- Section 2 (IS-Only Numerical Evidence): PASS — committed script: analysis/iteration_v3-041/bottom3_features_eda.py (SHA c2e2712, IS-only); full 14-feature ranking from iter-v3/028 portfolio importance CSV with KEEP/DROP labels; cross-verification table against iter-v3/040 single-seed importance (2/3 features agree at bottom); behavioral-effect predictor included (per feedback_v3_axis_saturation_predictor.md): predicted IS trade delta -3% to +5%; falsifier triggered if |IS trade delta| > 30 trades.
- Section 3 (Proposed Changes): PASS — 5 enumerated sub-fixes: (1) drop bottom-3 from V3_FEATURE_COLUMNS_TOP_N (14 → 11), (2) _verify_feature_columns rewrite (len==11 + 3 drops asserted absent + regime_momentum_signed_5d assertion INVERTED), (3) ITERATION_LABEL "v3-040" → "v3-041", (4) adversarial test rewrite for 11-feature stack, (5) inline tuple comments documenting drops with importance numbers + EDA SHA. KEEP V3_MODELS=4 (BCH+LDO+TRX+ALGO). KEEP V3_FEATURES_PER_SYMBOL={}. KEEP V3_ATR_MULTIPLIERS_PER_SYMBOL={}. REQUIRED_GAP=88 unchanged.
- Section 4 (Expected OOS Impact): PASS — IS predicted band [+0.85, +1.15] median +1.00; OOS predicted band [+1.50, +2.00] median +1.75; OOS falsifier (OOS < +1.55 = revert prune); three pathway thresholds locked: PATH A PROMISING (IS lift ≥ +0.10 AND OOS ≥ +1.55), PATH B PROMISING-INERT (|IS delta| ≤ 0.10 AND OOS ≥ +1.55), PATH C NEGATIVE (OOS < +1.55).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 all unchanged; OOD distribution shift risk noted (Mahalanobis covariance computed over 11 features instead of 14; gate threshold zscore=2.0 unchanged; expected firing rate comparable, escalate if >50% relative shift); concentration risk bounded (per-symbol PnL shift <±10%, escalate if any symbol > 50% OOS PnL); mandate-revocation risk for regime_momentum_signed_5d documented with 3-pathway resolution (PATH A/B falsifies mandate, PATH C upholds it).
- Section 6 (Risk Management Design): PASS — 7-primitive table with all gates listed; fire rates expected ~unchanged from iter-v3/040; only Gate 6 (OOD) feature subspace shrinks 14 → 11 (NOTE included), no gate threshold parameters modified.
- Section 7 (Failure-Mode Prediction): PASS — three plausible failure modes (PROMISING-INERT: 17.6% importance too small to lift IS at single-seed; NEGATIVE-real-signal-loss: regime_momentum_signed_5d carries deep-tree signal not captured by split-count importance; PROMISING-FALSE-LIFT: single-seed IS overfit, caught at next CONFIRMATION); what gates should catch (Gate 6 OOD firing rate shift, Gate 5 R2 brake earlier firing); behavioral effect predictor with falsifier (IS trade count change > 30 trades = investigate).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification thresholds pre-registered and LOCKED: PATH A PROMISING (IS lift ≥ +0.10 AND OOS ≥ +1.55), PATH B PROMISING-INERT (|IS delta| ≤ 0.10 AND OOS ≥ +1.55), PATH C NEGATIVE (OOS < +1.55); cannot be post-hoc renegotiated.
- Section 9 (Library Stack): PASS — full version table with all 8 packages pinned (lightgbm 4.6.0, numpy 2.2.6, optuna 4.8.0, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pytest 9.0.2); fracdiff PyPI unavailability and pure-numpy fallback documented (column still computed in parquets but not a model input — same as iter-v3/040 precedent); no new dependencies.

## Reasons (if BLOCK)

N/A — OVERALL=PASS. All 10 mandatory sections verified.

## Gate Verification Checklist

- [x] OOS_CUTOFF_DATE = 2025-03-24 confirmed in Section 0
- [x] training_months = 24 confirmed in Section 0
- [x] IS/OOS windows stated in absolute dates (Section 0)
- [x] Hypothesis is exactly ONE specific sentence with mechanism (Section 1)
- [x] IS-only numerical evidence with committed script SHA (Section 2)
- [x] Behavioral-effect predictor included with falsifier (Section 2.3, per feedback_v3_axis_saturation_predictor.md)
- [x] All proposed changes enumerated: labels, features, risk, tests (Section 3)
- [x] Single-axis change confirmed (drop bottom-3 features = one primary variable; per-symbol dicts unchanged)
- [x] IS Sharpe predicted band with median point estimate (Section 4)
- [x] OOS Sharpe predicted band with median point estimate (Section 4)
- [x] OOS falsifier with numerical threshold (Section 4)
- [x] R1/R2/R3 addressed (Section 5)
- [x] 7-primitive risk gate table (Section 6)
- [x] Pre-registered failure-mode prediction with ≥2 modes (Section 7 — has 3)
- [x] Pre-registered classification thresholds locked before backtest (Section 8)
- [x] Library stack with versions (Section 9)
- [x] fracdiff fallback documented (Section 9)
- [x] EXPLORATION spec confirmed (--seeds 1; wall-clock <= 2h; n_trials=35)
- [x] IS evidence derived from IS data only (analysis script reads only iter-v3/028 IS importance + iter-v3/040 IS importance)
- [x] Mandate-revocation risk for regime_momentum_signed_5d explicitly addressed (Section 5)
- [x] iter-v3/041 honors v3 cadence rule (EXPLORATION 2h cap, --seeds 1, single axis)
