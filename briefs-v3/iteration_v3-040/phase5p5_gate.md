# Phase 5.5 Gate — iter-v3/040

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed immutable; IS window 2023-03-24 to 2025-03-23; OOS 2025-03-24 onward.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #1 of 10, single-axis REVERT (two empty dicts), PROMISING-MECHANICAL predicted; --seeds 1 EXPLORATION-spec.
- Section 1 (Hypothesis): PASS — specific one-sentence hypothesis: clearing V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL restores the iter-v3/029 IS Sharpe anchor (~+0.79) because per-symbol customizations were the IS degradation source; predicts cycle 3 anchor establishment.
- Section 2 (IS-Only Numerical Evidence): PASS — committed script: analysis/iteration_v3-039/is_pbo_strategy_axis_analysis.py (SHA 9294855, IS-only); iter-v3/029 single-seed anchor tabulated (~+0.79 IS / ~+1.77 OOS); per-symbol cumulative IS swing quantified (-0.55 from customizations); behavioral-effect predictor included (per feedback_v3_axis_saturation_predictor.md): predicted IS trade delta -5% to -10%.
- Section 3 (Proposed Changes): PASS — 5 enumerated sub-fixes: (1) clear V3_FEATURES_PER_SYMBOL, (2) clear V3_ATR_MULTIPLIERS_PER_SYMBOL, (3) ITERATION_LABEL "v3-039" → "v3-040", (4) _verify_feature_columns rewrite, (5) test suite rewrite. Architecture (dicts + helpers) KEPT. KEEP V3_MODELS=4 (BCH+LDO+TRX+ALGO). KEEP V3_FEATURE_COLUMNS_TOP_N=14. REQUIRED_GAP=88 unchanged.
- Section 4 (Expected OOS Impact): PASS — IS predicted band [+0.50, +0.95] median +0.75; OOS predicted band [+1.50, +2.10] median +1.80; OOS falsifier (IS < +0.30 after full revert = escalate); PROMISING-MECHANICAL threshold locked (IS >= +0.50 AND OOS >= +1.50).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 all unchanged; LDO wider-barrier mechanical effect noted; BCH concentration expected to decrease; explicit falsifiers for unexpected concentration or trade count behavior.
- Section 6 (Risk Management Design): PASS — 7-primitive table with all gates listed; fire rates unchanged from iter-v3/028/039; no gate parameters modified.
- Section 7 (Failure-Mode Prediction): PASS — two plausible failure modes (NEGATIVE-unexpected: IS < +0.30 despite revert; PROMISING-MECHANICAL-partial: IS in [+0.30, +0.50)); what gates should catch (BCH OOD rate shift); behavioral effect predictor with falsifier (IS trade count change > 20 trades = investigate).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification thresholds pre-registered: PROMISING-MECHANICAL (IS >= +0.50 AND OOS >= +1.50); PROMISING-MECHANICAL-partial (IS in [+0.30, +0.50)); NEGATIVE-unexpected (IS < +0.30); thresholds locked before backtest.
- Section 9 (Library Stack): PASS — full version table with all 8 packages pinned; fracdiff PyPI unavailability and pure-numpy fallback documented (same as iter-v3/034-039 precedent); no new dependencies.

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
- [x] Per-symbol architecture KEPT (only dict contents cleared) (Section 3)
- [x] IS Sharpe predicted band with median point estimate (Section 4)
- [x] OOS Sharpe predicted band with median point estimate (Section 4)
- [x] OOS falsifier with numerical threshold (Section 4)
- [x] R1/R2/R3 addressed (Section 5)
- [x] 7-primitive risk gate table (Section 6)
- [x] Pre-registered failure-mode prediction with 2 modes (Section 7)
- [x] Pre-registered classification thresholds locked before backtest (Section 8)
- [x] Library stack with versions (Section 9)
- [x] fracdiff fallback documented (Section 9)
- [x] Single-axis change confirmed (REVERT = one primary variable)
- [x] EXPLORATION spec confirmed (--seeds 1; wall-clock <= 2h)
- [x] IS evidence derived from IS data only (IS window 2023-03-24 to 2025-03-23)
