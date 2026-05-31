# Phase 5.5 Gate — iter-v1/040

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: feature-family (4th cycle-5 use; MECHANISM-JUSTIFIED — /034 was exogenous new-data-source [perp-spot basis from separate data feed]; /040 is endogenous composed-from-incumbents [ret_5d × sign(hurst_100 − 0.5), algebraically derived from in-stack primitives]. Different mechanism classes per Section 0.6.)
ROTATION_STATUS: VALID (prior 5 EXPLORATIONs: /034 feature-family, /035 labeling, /036 per-cohort-specialization, /037 loss-function, /038 risk-primitive — 5 distinct families, monoculture trigger NOT armed)

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK — pure feature swap DROP 1 + ADD 1; n_features constant at 44; does NOT change Optuna training-objective domain, labels, universe, model arch, loss function, risk gates, sample weighting, or n_features dimension)
Mitigation: N/A (NORMAL-RISK; F-AXIS #2 LOAD-BEARING importance rank gate catches RSI colsample-theft; F-AXIS #5 Spearman diagnostic for basin-relocation at EXPLORATION budget)

## LM Master Response Verification
- briefs-v1/iteration_v1-040/lgbm_advisor.md exists: PASS (file present with Phase 4.5 header; 3 HP recommendations + 1 FE recommendation across "Recommended Hyperparameter Direction" and "Recommended Feature-Engineering Direction" sections)
- Brief Section 3 addresses each LM Master recommendation: PASS

  Brief Section 11 (added via Step 1.5 remediation) contains a 4-row response map:
  - HP-1 (colsample_bytree upper bound 0.85→0.95): REJECTED — single-axis isolation discipline; second simultaneous variable violates cycle-5 one-variable-at-a-time doctrine; F-AXIS #2 gate handles colsample-theft detection
  - HP-2 (keep n_trials=18 + ENSEMBLE_SIZE=3): ADOPTED — unchanged from Section 5.1
  - HP-3 (hold LR bounds [0.01, 0.1]): ADOPTED — unchanged from Section 5.1
  - FE-1 (ADD regime_momentum_signed_5d, BYTE-FOR-BYTE copy from v3): ADOPTED — core of /040 axis

  All 4 recommendations addressed with adjudication + reason. Gate requirement satisfied.

## Cadence Check
- Wall-clock budget declared: ~1.0h modal (Section 0.5 and Section 6); EXPLORATION 2h cap satisfied: PASS
- EXPLORATION precedents since last CONFIRMATION: 7 of 10 (3 to go before /044 can launch): PASS (≥10 not yet required; CONFIRMATION not launching)
- CONFIRMATION-only checks: N/A (TYPE=EXPLORATION)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 confirmed sacred in Section 3.4 table and Section 10.4 anti-cheating self-check
- Section 0.5 (Iteration Type, v1/v3): PASS — TYPE: EXPLORATION declared, cadence 7/10 stated, wall-clock ~1.0h target in Section 0.5; 2h EXPLORATION cap satisfied
- Section 0.6 (Architecture-Family Justification, v1-only): PASS — feature-family REPEAT mechanism-justified (exogenous /034 vs endogenous /040 mechanism classes distinguished); prior 5 families enumerated (/034 feature-family, /035 labeling, /036 per-cohort-specialization, /037 loss-function, /038 risk-primitive); rotation status VALID (5 distinct families, no monoculture); one-sentence rationale present citing LM Master /038 §6 Rec 1 HIGH CONFIDENCE + v3 /025 PROMISING + /028 CONFIRMATION-MERGE precedent
- Section 1 (Hypothesis): PASS — hypothesis re-framed from regime-conditioning to 5-day (15-bar) log return primitive (Section 1.3 IMPORTANT FINDING: sign is +1 always); specific mechanism: v1 lacks a 15-bar momentum primitive (v1's longest is stat_log_return_5 at 5-bar=40h); v3 CONFIRMATION-MERGE precedent cited; |IC|=1.0 vs ret_5d documented (mechanical identity); F-AXIS #2 importance rank gate as binding falsifier
- Section 2 (IS-Only Evidence): PASS — Section 1.1: basis_zscore_30 3-consec INERT confirmed with 15 importance rank measurements across /034/037/038 (mean rank 27.67/44, min 25, max 32, all ≥ 25); Section 1.2: ADF stationarity table for all 5 symbols (p << 0.001); Section 1.3: hurst=+1 everywhere (100% trending) documented; Section 1.4: IC matrix vs incumbents (|IC|=1.0 vs ret_5d, 0.80 vs RSI, 0.58 vs stat_log_return_5); Section 1.5: per-cohort importance rank predictions; committed analysis/iteration_v1-040/eda.py script
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS — NORMAL-RISK declared; mechanism justification present (pure feature swap, n_features constant, no training-objective domain change); mirrors /034 (also NORMAL-RISK feature-add); DROP+ADD more conservative than /034's pure ADD; budget choice: single-seed=42 at v1 EXPLORATION standard
- Section 3 (Proposed Changes): PASS — Section 3.1 enumerates 5 atomic edits (composed_v1.py NEW, features/__init__.py EDIT, features_v1/__init__.py EDIT, run_baseline_v1.py EDIT, 2 test files NEW); Section 11 LM Master response map: 4 rows, all HP+FE recommendations addressed; Section 3.2 feature regen command documented; Section 3.4 universe/model/label/feature/Optuna config table; V1_OOD_FEATURE_COLUMNS decoupling documented (composed feature NOT added to OOD set)
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1 6-band OOS Δ verdict matrix with probability distribution (PROMISING-CLEAN 30%, PROMISING-INERT-FAV 35% MODAL, INERT 20%, NEGATIVE 15%); combined PROMISING 65%; modal E[Δ] ≈ +0.12; F-AXIS #2 LOAD-BEARING importance rank gate with PASS/PASS-CONDITIONAL/FAIL definitions; F-AXIS #3-#5 diagnostic falsifiers; F1/F2/F4/F5 joint verdict routing matrix in Section 4
- Section 5 (Risk Mitigation): PASS — R1 (consecutive-SL cool-down), R2 (drawdown brake Model E only), R3 (OOD Mahalanobis gate, cutoff 0.70, 16 OOD features) all documented as UNCHANGED; composed feature NOT added to V1_OOD_FEATURE_COLUMNS (explicitly justified — regime-conditional features destabilize OOD subspace); no new risk primitive per single-axis EXPLORATION doctrine
- Section 6 (Risk Management Design): PASS — Section 5 risk-layer table documents R1/R2/R3 gate status per model (ON/OFF per model); wall-clock estimate with 5-step scaling in Section 6; 8-primitive equivalents documented (R1 cool-down, R2 brake, R3 Mahalanobis, stateless gates per baseline); fire-rate predictions via /034 precedent (identical axis type, identical model config)
- Section 7 (Failure-Mode Prediction, v1/v3): PASS — Section 11.5 "Pre-Registered Failure-Mode Prediction" added: RSA colsample-theft INERT as modal failure (|IC|=0.80 with RSI, RSI ranks 1-3 across cohorts, composed feature displaces RSI in split-budget without net signal gain); Section 9 PREDICTED MOST PLAUSIBLE FAILURE MODE paragraph with mechanism detail; gates that catch failure (F-AXIS #2 importance rank < 30 in all 5 cohorts → INERT-LEARNED-NEG; F-AXIS #1 Δ < -0.10 → NEGATIVE); regime-decay NEG as second failure mode (15%)
- Section 8 (MERGE/NO-MERGE Criteria, v1/v3): PASS — Section 11.6 "Pre-Registered MERGE/NO-MERGE Numerical Criteria" added: 5-row routing table with specific OOS Δ thresholds per verdict band (PROMISING-CLEAN-EXCEPTIONAL ≥ +0.50, PROMISING-CLEAN +0.20 to +0.50, PROMISING-INERT-FAV +0.05 to +0.20, INERT -0.10 to +0.05, NEGATIVE < -0.10); forward-declared /044 CONFIRMATION MERGE gate (OOS ≥ +1.8, OOS/IS ≥ 0.50, trades ≥ 130, DSR > 0.95, PBO < 0.40, PSR > 0.95, top-symbol ≤ 30%); explicit note that /040 is EXPLORATION with no direct MERGE path
- Section 9 (Library Stack, v1/v3): PASS — Section 11.7 "Library Stack Declaration" added: 8-row table (lightgbm, optuna, numpy, pandas, scipy.stats, mlfinlab N/A, mlfinpy N/A, pypbo N/A, fracdiff N/A); Hurst R/S implementation documented (pure NumPy, BYTE-FOR-BYTE copy from regime_v3.py:34-75, no external library); no fallbacks required; no mlfinlab licensing risk

## Reasons (if BLOCK)
N/A — OVERALL: PASS.

Step 1.5 remediation applied: Sections 11, 11.5, 11.6, 11.7 added to research_brief.md before gate evaluation. All 4 lessons-from-/039 mandated sections now present.

Gate passed on first evaluation after Step 1.5 remediation. No prior BLOCK issued.
