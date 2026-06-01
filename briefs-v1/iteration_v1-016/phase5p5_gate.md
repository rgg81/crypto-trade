# Phase 5.5 Gate — iter-v1/016

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (CYCLE-3 EXPLORATION #1)

## Axis Family + Rotation Status
FAMILY: sample-weighting (NEW family; never used in v1 catalog)
ROTATION_STATUS: VALID

Last 5 EXPLORATION families (from exploration_catalog.md):
- iter-v1/010: risk-primitive
- iter-v1/011: risk-primitive
- iter-v1/012: methodology-substrate-test
- iter-v1/013: methodology-substrate-test
- iter-v1/014: labeling

(iter-v1/015 was CONFIRMATION, not counted in prior-5 EXPLORATION rotation check.)
`sample-weighting` appears zero times in the last 5 EXPLORATIONs. VALID.

## HIGH-RISK Declaration
HIGH-RISK: YES
Reason: sample-weighting changes Optuna's training-objective domain (per-row weight ratios
change the loss surface gradient; per feedback_v1_n_eff_barrier_magnitude_curve.md LESSON #2).
Mitigation: NONE opted-in (single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 fixed cycle-3 default;
opt-in multi-seed not triggered).

## LM Master Response Verification
- briefs-v1/iteration_v1-016/lgbm_advisor.md exists: PASS (committed at a273c94)
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - Rec #1 (compress n_trials 20→18): ADOPTED
  - Rec #2 (pin feature_fraction=bagging_fraction=1.0, conditional on QE check): ADOPTED-CONDITIONAL
  - Rec #3 (n_eff_per_cell stays [10,20] range; uniform does NOT restore /015 collapse): ADOPTED
  - Rec #4 (min_data_in_leaf upper bound unchanged): ADOPTED
  - 5 risks flagged by LM Master: ADOPTED into Sections 6/7

## Wall-Clock Budget Check
Iteration type: EXPLORATION — 2h HARD CAP applies.
Declared predicted range: 1.50–1.75h (Section 3.6.3); per LM Master Rec #1 ADOPTED (n_trials=18
pre-emptively), revised upper bound ~1.58h (lgbm_advisor.md: "upper bound 1.58h → 21% margin").

NOTE on brief internal inconsistency: Section 3.3 declares n_trials=20 but Section 3.5 (Rec #1
ADOPTED) and the QR/orchestrator dispatch both confirm n_trials=18. The definitive runtime value
is 18. Section 13 self-check margin note (12.5% at 1.75h upper bound) is stale relative to Rec #1
adoption. With n_trials=18 and LM Master's upper bound 1.58h: margin = (2.0 - 1.58) / 2.0 = 21%,
which PASSES the ≥20% margin requirement.

Wall-clock budget: PASS (21% margin declared; ≥20% required)
≥20% margin requirement: PASS (21% margin via n_trials=18 adoption)

## Cadence Check
- Wall-clock budget declared (EXPLORATION ≤ 2h): PASS (1.58h upper bound per n_trials=18)
- EXPLORATION type — no CONFIRMATION cadence check required

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 declared
  unchanged; IS window (24 months preceding 2025-03-24) and OOS window (post-2025-03-24) confirmed.
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION, CYCLE-3 #1, wall-clock cap declared.
- Section 0.6 (Architecture-Family Justification): PASS — family=sample-weighting (NEW, never used),
  prior 5 EXPLORATIONs enumerated, ROTATION_STATUS=VALID, one-sentence rationale provided.
- Section 1 (Hypothesis): PASS — single clear hypothesis: replacing abs(labeled_pnl) with uniform
  weights eliminates per-symbol asymmetry in Model A, restores Kish n_eff toward 1.0, reduces
  outlier overfit. Specific predicted mechanism (BTC share 0.451→0.500, Kish ratio 0.85→1.0).
- Section 2 (IS-Only Evidence): PASS — committed scripts at analysis/iteration_v1-016/:
  eda_weighting_schemes.py, eda_per_symbol_weight_concentration.py, eda_uniqueness_predicted_effect.py.
  Tables A-D with concrete numbers (BTC share 0.451±0.036, Kish ratios 0.86-0.88, max abs_pnl
  74.70% LINK). No category-matching without numbers.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared with reason (loss-surface
  gradient change via per-row weight ratios); opt-in mitigation explicitly declined; forward mandate
  documented (3 consecutive HIGH-RISK negatives trigger multi-seed requirement).
- Section 3 (Proposed Changes): PASS — enumerated: sample_weight_mode parameter
  (abs_pnl/uniform/uniqueness_only), no other axis changes, Optuna params specified, LM Master
  Rec #1-4 and 5 risks addressed. NOTE: internal n_trials inconsistency (3.3 says 20; 3.5 says 18
  ADOPTED) — definitive value is 18 per Rec #1 ADOPTED. QE must use --n-trials 18.
- Section 4 (Expected OOS Impact): PASS — F1-F8 + F-AXIS-MECHANISM-NEW falsifiers with specific
  numerical bands. F-AXIS-MECHANISM compound falsifier (Kish>0.95, |BTC_share-0.5|≤0.02,
  timeout_share<0.6). Pre-registered failure modes in Section 6. FLAT 33/33/34 verdict priors.
- Section 5 (Risk Mitigation): PASS — FLAT 33/33/34 priors documented; R1/R2/R3 gates unchanged;
  IS-calibrated thresholds unchanged (no new gate changes introduced).
- Section 6 (Risk Management Design): PASS — 5 pre-registered failure modes (NULL, NEGATIVE,
  PROMISING+FAIL, PROMISING+PASS, PROMISING-MECHANICAL). Risk gate wiring unchanged.
- Section 7 (Pre-Registered Failure-Mode Prediction): PASS — Section 6 pre-registers 5 failure
  modes with predicted mechanism, catalog row, and forward axis for each. Forward mandate on
  3-consecutive-HIGH-RISK documented.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 8-cell verdict gate matrix pre-registered with
  specific F1/F3/F7/F8/F-AXIS-MECHANISM thresholds for each verdict class. Mechanical failures
  (Cell 7/8) checked first per /014 override rule.
- Section 9 (Library Stack): PASS — numpy, pandas, lightgbm, optuna declared. No new
  third-party dependencies. Implementation is parameter + 5-line branch only.

## Reasons for PASS

All 9 mandatory sections present and complete. LM Master advisory exists and all 4 recommendations
are addressed in Section 3.5. Rotation is VALID (sample-weighting = NEW family). HIGH-RISK
declaration is present with reason and forward mandate. Wall-clock margin PASSES at 21% with
n_trials=18 (LM Master Rec #1 adopted). No sacred constants changes.

QE NOTE — n_trials inconsistency: Section 3.3 says 20; Rec #1 ADOPTED says 18. The launch
invocation in the dispatch header uses --n-trials 18. QE MUST use --n-trials 18 (not 20) to
satisfy the ≥20% margin requirement. Brief Section 3.6.3 amendment confirms this.

QE NOTE — Rec #2 conditional: QE must check whether subsample/colsample_bytree are tuned in
v1_pruned Optuna search (they ARE — subsample suggest_float(0.5,1.0) at optimization.py:227;
colsample_bytree suggest_float(0.5,1.0) at optimization.py:230 for v1_pruned). Per Rec #2
ADOPTED-CONDITIONAL: pin both to 1.0 for /016 axis isolation.
