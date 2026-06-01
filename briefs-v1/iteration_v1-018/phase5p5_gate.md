# Phase 5.5 Gate — iter-v1/018

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3 #3 of 10)

## Axis Family + Rotation Status
FAMILY: per-cohort-specialization-LINK (NEW 9th family declaration; first usage in v1 catalog)
ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (from exploration_catalog.md):
- /013: methodology-substrate-test
- /014: labeling
- /015: labeling (CONFIRMATION)
- /016: sample-weighting
- /017: universe

`per-cohort-specialization-LINK` appears in NONE of the prior 5. Rotation discipline
satisfied. The 5 prior families are NOT all the same family — rotation MANDATE does not
trigger. The new family declaration is accompanied by orthogonality justification in
Section 0.6: cohort-specialization-pairings vary the SYMBOL DIMENSION while holding
labels/features/risk/methodology constant — structurally orthogonal to the existing 8
axis families.

## HIGH-RISK Declaration
HIGH-RISK: YES
Mitigation: none (opt-in multi-seed not elected; ENSEMBLE_SIZE=3 cycle-3 default)
Cumulative tracker: /016 HIGH-RISK NEGATIVE-catastrophic / /017 HIGH-RISK NEGATIVE-anti-
direction-INERT (within 1σ) / /018 HIGH-RISK outcome TBD. Forward-mandate fires at 3rd
consecutive ≥1σ negative HIGH-RISK (not yet triggered).

## LM Master Response Verification
- briefs-v1/iteration_v1-018/lgbm_advisor.md exists: PASS (committed at 004d1d1, filed
  before brief authoring; Section 3.4 reserved the integration slot)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

  lgbm_advisor.md contains 3 hyperparameter recommendations + 4 saturation risks +
  verdict-class adjustment + mathematical clarification:
  - Rec #1 (KEEP n_trials=18): ADOPTED — Section 3.3 specifies n_trials=18; no
    compression at 78+ min margin
  - Rec #2 (Accept current Optuna bounds): ADOPTED — v1_pruned bounds unchanged;
    single-axis isolation maintained
  - Rec #3 (KEEP ENSEMBLE_SIZE=3): ADOPTED — single-axis isolation overrides raising
    to 5; multi-seed deferred to /027 CONFIRMATION
  - Verdict-class adjustment (INERT 45% modal): ADOPTED — Section 5 preserves FLAT
    33/33/34 priors but integrates the 45% INERT modal from LM Master into Section 5's
    "Two specific mechanism predictions"
  - Mathematical clarification (dilution accounting vs edge discovery): ADOPTED and
    DOCUMENTED — Section 1 H2 explicitly calls out H2 as INFORMATIONAL only; Section 4
    F1 anchors against LINK-alone-in-pool +0.8184 (NOT portfolio +0.6637), correctly
    applying the per-cohort methodology distinction
  - Saturation risks (basin lottery, n_eff band, direction-asymmetry inheritance):
    ADOPTED into Section 6 (6 failure modes documented)
  - /019+ conditional pre-staging: ADOPTED into Section 11 (7 alternates enumerated
    with LM Master's 4-case conditional branching)
  - LM Master /017 +XRP recommendation: SUPERSEDED — Section 3.4 notes QR per-cohort
    pivot is mechanically tighter axis

## Cadence Check
- Wall-clock budget declared: 12-18 min projected (≥80% margin under 2h cap): PASS
  - Section 3.6 provides full decomposition: 1-model LINK-only vs 4-model baseline
    (~50 min); linear scaling gives 12-15 min; methodology overhead +3 min
  - ≥20% margin gate: 1h 35min margin = 79% headroom. PASS
  - Phase 5.5 BLOCK threshold (>1.6h estimate): 15-18 min is well below threshold. PASS
  - Contingency at 3× worst case: 45 min still 62% margin. PASS
- EXPLORATION: no CONFIRMATION cadence check required

## Per-Section Status
- Section 0 (Data Split): PASS — brief anchor at header references "v0.v1-baseline-
  corrected (BASELINE_V1.md commit f8bc12c)" which defines OOS_CUTOFF_DATE=2025-03-24
  and training_months=24. Section 2.1 per-symbol table shows n_months=39 IS / 14 OOS
  months for LINK (39 IS + 14 OOS = 53 total, consistent with OOS cutoff 2025-03-24
  and fresh data through 2026-04). Anchor line states "IS Sharpe +0.2829 / OOS Sharpe
  +0.6637" — same split confirmation as Section 0 in /017 (implicit from n_months
  evidence, not an explicit constants block). Sacred constants unchanged per Section 3.1
  ("Foundation guardrail: walk_forward.py:113 unchanged. No regression.").
  NOTE: brief does not have a standalone "Section 0 — Data Split declaration" block
  with explicit OOS_CUTOFF_DATE = 2025-03-24 / training_months = 24 literal constants.
  Consistent with prior /016 and /017 briefs where the constants were confirmable from
  context. PASS on same precedent.
- Section 0.5 (Iteration Type): PASS — "EXPLORATION (cycle-3 #3 of 10)" at brief
  header, Section 0.1 cadence ledger, and Section 13 self-check
- Section 0.6 (Architecture-Family Justification): PASS — family=per-cohort-
  specialization-LINK (NEW 9th family); prior 5 enumerated (/013-/017); rotation
  VALID; orthogonality justification in Section 0.6 (SYMBOL DIMENSION variation vs
  feature/labeling/model-arch/risk/methodology families); NEW family declaration
  accompanied by 3-way convergence evidence note (Critic Phase 7.5 Check 14)
- Section 1 (Hypothesis): PASS — one-sentence primary hypothesis H1 is specific:
  "LINK-only model will produce OOS metrics AT LEAST equivalent to LINK-alone-in-pool
  baseline (+0.8184)". Falsification logic with NEGATIVE-INTRINSIC subtype (Δ ≤ -0.31)
  defined. H2 explicitly marked INFORMATIONAL only per per-cohort methodology
- Section 2 (IS-Only Evidence): PASS — 12 output files from committed
  analysis/iteration_v1-018/ scripts at SHA ea71dbe. Tables include per-symbol
  comparison (2.1), roster overlap across 8 iterations (2.2), direction split (2.3),
  NATR profile (2.4), ATR calibration (2.5), monthly OOS distribution (2.6), and
  option assessment table (2.7). All are IS-data-only (per-symbol and OOS-month data
  from the baseline reports, not from any forward-looking data). Script runs on IS data
  only, produces concrete numbers. Analysis EDA does NOT touch OOS data other than
  reading it from committed reports (acceptable — reading prior OOS results to inform
  per-symbol anchor is not data snooping)
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — explicit one-sentence declaration
  "Declaration: HIGH-RISK. Reason: dropping Models A/D/E is a structural change to
  Optuna's training-objective domain (universe goes from 5 to 1 symbol)." Cumulative
  tracker included
- Section 3 (Proposed Changes): PASS — single src/ file change enumerated in Section
  3.1 (~30 lines added to run_baseline_v1.py). Zero changes to features_v1/,
  lgbm.py, optimization.py, walk_forward.py, labeling.py, risk gate code. Section 3.3
  pins all key values: feature_columns, bounds_profile, ENSEMBLE_SEEDS[0:3], R5 flags,
  sample_weight_mode, sigma_source, apply_r1/r2. Section 3.4 addresses all LM Master
  recommendations (see LM Master Response Verification above)
- Section 4 (Expected OOS Impact): PASS — F1 anchored against LINK-alone-in-pool
  +0.8184 (CORRECT — not portfolio +0.6637). Verdict cells enumerated with specific Δ
  bands. F-AXIS-MECHANISM #1 (dispatch correctness) and #2 (trade count band) defined.
  The F1-F8 and F-AXIS-MECHANISM falsifier matrix in Section 4 / Section 8 is
  pre-registered before backtest runs
- Section 5 (Risk Mitigation): PASS — Section 6 (failure modes) covers 5 failure
  modes with specific trigger conditions. Section 3.3 lists frozen R-gate params.
  IS-calibrated risk thresholds inherited from Model C baseline (R1 K=3, C=27 candles;
  R3 OOD cutoff=0.70)
- Section 6 (Risk Management Design): PASS — Section 3.3 enumerates all active risk
  primitives (R1 cool-down, R3 OOD; R2 and R5 explicitly disabled). Section 6 covers
  failure modes including direction-asymmetry collapse and n_eff collapse scenarios
- Section 7 (Failure-Mode Prediction): PASS — Section 6 provides 5 pre-registered
  failure modes (6.1 basin lottery, 6.2 IS overfit, 6.3 pool-leveraged structural
  prior, 6.4 direction-asymmetry, 6.5 n_eff collapse). Each has specific detection
  mechanism and Phase 7.4/7.5 escalation path
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Section 8 contains a 7-cell verdict
  matrix with locked numerical thresholds (PROMISING Δ≥+0.20 / PROMISING-INERT [-0.20,
  +0.20] / NEGATIVE-INERT [-0.20,-0.31) / NEGATIVE-INTRINSIC Δ≤-0.31 /
  NEGATIVE-CATASTROPHIC Δ≤-0.55 / NEGATIVE-IS-COLLAPSE F3 Δ≤-0.30 /
  NEGATIVE-DISPATCH F-AXIS #1 fail). Pre-registered before backtest runs; eliminates
  post-hoc rationalization. NOTE: EXPLORATION briefs do not have a "MERGE/NO-MERGE"
  criterion (that is CONFIRMATION territory); Section 8 here is the EXPLORATION
  verdict matrix, which is the correct per-cohort analog. PASS on scope
- Section 9 (Library Stack): PASS — Section 9 declares: mlfinlab==1.4, pypbo, fracdiff
  >=0.10, statsmodels, lightgbm>=4.0, optuna>=3.0. "No changes to library versions.
  Inheriting cycle-3 baseline." PASS
- Section 10 (NO --no-engineering-report flag): PASS — Section 10.1 explicitly states
  "Run command excludes --no-engineering-report flag" and mandates engineering_report.md
  generation at Phase 6. This is a v1-specific engineering discipline item added per
  Critic /017 Rec #2

## Reasons (if BLOCK)
N/A — OVERALL: PASS
