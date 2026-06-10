# Phase 5.5 Gate — iter-v1/086

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST

## (v1 only) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-TRB
ROTATION_STATUS: VALID (rotation suspended under per-symbol regime-specialist mandate;
TRB is distinct from all 5 prior cohorts: BTC, AAVE, FIL, CRV, UNI)

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: YES, mitigation = 50-inner-seed ensemble (seeds 42..91); multi-outer-seed
CONFIRMATION permanently dropped per user directive

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-086/lgbm_advisor.md exists: PASS
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - Rec 1 (HP landing predictions): NOTED — within-lock prediction; no action required
  - Rec 2 (50-seed mean IS ≈ +0.48 [+0.38,+0.62]): ADOPTED as modal anchor; folded into F2
  - Rec 3 (feature-importance prediction): ADOPTED as Phase 7.4 pre-registered check + F5
  - Rec 4 (R5 cold-start telemetry): ADOPTED as Phase 7.4 telemetry; Section 6 R5 note
  - Rec 5 (diversification CONDITIONAL, return-corr proxy caveat): ADOPTED, promoted to F5 + bundle-assembly precondition
  - (implicit) "add a feature": REJECTED by design (the /085 crater mechanism)

## Cadence Check (v1)
- Wall-clock budget declared: ~6h for SPECIALIST (within 9h BUNDLE cap; the 50-inner-seed
  budget mirrors AAVE/078 + UNI/085 methodology-lock; the 2h EXPLORATION-knob cap does not
  apply to per-cohort SPECIALIST mines under the cycle-6/7 mandate): PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared
  unchanged; IS window 2020-09→2025-03-23; OOS window 2025-03-24 onward stated explicitly
- Section 0.5 (Iteration Type, v1): PASS — TYPE: SPECIALIST (single-coin cohort, SYMBOL axis)
- Section 0.6 (Architecture-Family Justification, v1-only): PASS — axis family
  per-cohort-specialization-TRB; 5 prior cohorts listed (BTC/065, AAVE/078, FIL/083, CRV/084,
  UNI/085); ROTATION_STATUS=VALID declared with rationale; TRB ∉ BUNDLE-002,
  ∉ failed-mine set, ∉ V1_EXCLUDED_SYMBOLS
- Section 1 (Hypothesis): PASS — one specific H1 (IS monthly Sharpe ≥ +0.30, probe-consistent)
  + H2 (lowest-correlation diversifier thesis); specific falsifiers named; NOT vague
- Section 2 (IS-Only Evidence): PASS — committed scripts at
  analysis/iteration_v1-086/bundle_diversification_corr.{py,csv} and
  analysis/iteration_v1-086/probe_TRBUSDT.{py,csv}; tables with concrete numbers;
  GATE 0 corr table, GATE 1 trivial baseline, GATE 2 IS Sharpe +0.4930, max|IC| 0.3863;
  all series IS-only (open_time < OOS_CUTOFF verified in-code per no-cheating rule)
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS — HIGH-RISK declared; reason:
  new-symbol substitution changes Optuna training-objective domain; mitigation: 50-inner-seed
  ensemble (seeds 42..91); multi-outer-seed CONFIRMATION permanently dropped noted
- Section 3 (Proposed Changes): PASS — cohort TRBUSDT; feature_columns=V1_FEATURE_COLUMNS_PRUNED
  (48 cols, STOCK, NO new features); R1=OFF, R2=OFF, R3=ON-shared 0.70, R5=ON 0.3;
  atr_tp=2.9, atr_sl=1.45; 50 inner seeds × 30 trials; one-variable discipline stated
- Section 3.5 (LM Master Responses, v1-only): PASS — all 5 explicit LM recs plus the implicit
  "add a feature" covered; disposition table present with rationale for each; F5 promoted
  from LM Rec 3 + Rec 5
- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1 through F5 enumerated with specific
  numerical bands; Section 8 pre-registers SPECIALIST candidacy bands with IS Sharpe thresholds
- Section 5 (Risk Mitigation): PASS — covered under Section 6 (labeled "Section 6 — Risk
  Mitigation" in brief, contains R1–R5 recap with IS-calibrated thresholds and historical
  context); no new risk primitive
- Section 6 (Risk Management Design): PASS — R1/R2/R3/R5 primitives each addressed with
  on/off state and rationale; R5 cold-start flag documented; gate efficacy notes present
- Section 7 (Failure-Mode Prediction, v1): PASS — Section 7 explicitly predicts modal outcome
  ([+0.30, +0.55] band, cross_seed_std <0.30), documents what would surprise
  (IS < +0.00 = probe-inconsistent) and why (basin-translation gap), notes cycle-6/7 basin-
  lottery context
- Section 8 (MERGE/NO-MERGE / SPECIALIST Candidacy Criteria, v1): PASS — pre-registered
  VALIDATED/PROMISING-TENTATIVE/NEGATIVE/NEGATIVE-PROBE-INCONSISTENT bands with explicit
  IS Sharpe thresholds; bundle-accretion carve-out pre-registered; NO MERGE this iteration
  stated; conditions for BUNDLE-003 candidacy pre-registered
- Section 9 (Library Stack, v1): PASS — LightGBM (locked head), statsmodels adfuller
  (informational ADF), scipy spearman (GATE-2 IC); no new libraries declared; no licensing
  risk

## Reasons (if BLOCK)
None — OVERALL=PASS
