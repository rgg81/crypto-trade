# Phase 5.5 Gate — iter-v3/044

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS windows in absolute dates, OOS_CUTOFF_MS=1742774400000 declared.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #5 of 10, wall-clock ≤2h, spec=`--exploration --seeds 1 --model xgboost`, two-part axis (revert ER + model swap) clearly enumerated.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: XGBoost on 14-feature 4-sym stack with regime_momentum_signed_5d may learn a different decision surface than iter-v3/016 (3-sym/13-feature). Falsifier stated (IS Sharpe < +0.40).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed engineering reports (iter-v3/016 SHA `1aa3eb3`, iter-v3/040). No new analysis script needed: evidence = prior-iteration IS metrics, which are IS-only training-fold data. No category-matching.
- Section 3 (Proposed Changes): PASS — 3 enumerated sub-fixes: (1) remove efficiency_ratio_50 from V3_FEATURE_COLUMNS_TOP_N (15→14), (2) ITERATION_LABEL v3-043→v3-044, (3) update _verify_feature_columns for 14-feature assertions. Unchanged items enumerated. Run-command change (--model xgboost) noted as CLI flag, not code change.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.30, +0.90], OOS [+0.50, +1.80], median IS +0.60 / OOS +1.15). Explicit falsifier stated (OOS < +0.50 → axis CLOSED).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated thresholds (ADX 20.0, z-score 2.0, BTC trend 15.0) stated unchanged from iter-v3/040 baseline. Simulated effect on prior iterations noted.
- Section 6 (Risk Management Design): PASS — 8-primitive table with config, estimated IS fire rate, enabled/disabled status for each gate. Regime coverage noted.
- Section 7 (Failure-Mode Prediction): PASS — Paragraph predicts primary failure mode (IS/OOS polarity inversion for 2-3 symbols, IS MaxDD >35%), diagnostic indicator (IS MaxDD >35%), and metric signature (IS Sharpe < +0.50, OOS Sharpe < +0.50).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered EXPLORATION outcome classification (PROMISING/PROMISING-MARGINAL/NEGATIVE/DISASTROUS) with numerical thresholds. Model-architecture axis closure rule stated. Non-applicable MERGE criteria correctly noted (EXPLORATION spec).
- Section 9 (Library Stack): PASS — All versions pinned. XGBoost 2.1.4 identified as primary. mlfinlab/mlfinpy: not used (CPCV native). No license risk. XgboostStrategy fallback declaration: none needed (installed since iter-v3/016).

## One-Variable Check

Single primary variable: model architecture (LightGBM → XGBoost). The efficiency_ratio_50 REVERT is a pre-condition restoration (removing iter-v3/043's DISASTROUS addition), not an independent variation axis — same classification pattern as iter-v3/016 tbr_zscore_30 pre-condition drop. ITERATION_LABEL update is cosmetic. PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight.
