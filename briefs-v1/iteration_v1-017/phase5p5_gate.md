# Phase 5.5 Gate — iter-v1/017

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: universe
ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (from exploration_catalog.md):
- /012: methodology-substrate-test
- /013: methodology-substrate-test
- /014: labeling
- /015: labeling (CONFIRMATION)
- /016: sample-weighting

`universe` appears in NONE of the prior 5. Rotation discipline satisfied.

## HIGH-RISK Declaration
HIGH-RISK: YES
Mitigation: none (opt-in multi-seed not elected; ENSEMBLE_SIZE=3 cycle-3 default; /017
is 1st cycle-3 HIGH-RISK; forward-mandate accumulates across 3 per feedback_v1_n_eff_barrier_magnitude_curve.md)

## LM Master Response Verification
- briefs-v1/iteration_v1-017/lgbm_advisor.md exists: PASS (committed at 7294b58)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

  LM Master lgbm_advisor.md "Closing Note" contains three staked calls:
    1. ETH regime-lock probability 75% — /018 must pivot to ETH-specific kill
    2. KEEP n_trials=18 — pre-emptive compression to 15 false economy
    3. 6-symbol over 7-symbol — single-axis isolation preserves attribution

  Brief Section 3.4 (committed at a145ee0) explicitly labels all three:
    - Rec #1 (ETH regime-lock / /018 ETH kill): ADOPTED — Section 11.3 mandates /018
      PRIMARY = ETH-specific kill switch if /017 OOS ETH ≤ -0.30
    - Rec #2 (KEEP n_trials=18): ADOPTED — Section 3.6 keeps n_trials=18; contingency
      compression to 15 only if QE pre-flight projects >72 min at 50% completion
    - Rec #3 (6-sym over 7-sym): ADOPTED — Section 3.1 implements 6-sym
      V1_ITER017_UNIVERSE (SOL only); XRP deferred to /018 alternate A per Section 11.2

  The prior BLOCK (50f8a31) was issued because Section 3.4 was marked
  "Reserved/Pending" with no explicit disposition labels. That defect is corrected
  at a145ee0. PASS.

## Cadence Check
- Wall-clock budget declared: 60 min linear estimate (2h EXPLORATION cap); 50% margin >= 20%: PASS
- Sub-linear realistic estimate: 42 min; 65% margin >= 20%: PASS
- Compression decision: NONE declared (no compression needed); contingency plan at Section 3.6.4: PASS
- EXPLORATION: no CONFIRMATION cadence check required

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF=2025-03-24 and training_months=24 confirmed;
  training start 2023-04-04 = OOS_CUTOFF minus 24mo stated at Section 2.1; sacred
  constants unchanged; IS/OOS windows named in absolute dates
- Section 0.5 (Iteration Type): PASS — "CYCLE-3 EXPLORATION #2 of 10" explicit at
  brief header and Section 0.5
- Section 0.6 (Architecture-Family Justification): PASS — family=universe; prior 5
  enumerated (methodology-substrate-test ×2, labeling ×2, sample-weighting ×1);
  VALID rotation status declared with one-sentence rationale; UNUSED since /006
- Section 1 (Hypothesis): PASS — one-sentence hypothesis with mechanism + FLAT 33/33/34
  prior stated; mechanism-level predictions explicit (not vague "explore universe");
  3 sub-predictions (F-AXIS-MECHANISM, ETH regime-vs-universe, LINK dilution)
- Section 2 (IS-Only Evidence): PASS — 4 committed EDA scripts under
  analysis/iteration_v1-017/ with 11 CSV outputs; Tables A-H produced from IS data;
  A14 dead-feed screen (Table B: SOL max_consec_flat=1, zero_vol=0); BTC-correlation
  table (Table G: SOL ρ=0.6164 below all baseline symbols); ETH 3-axis drag trajectory
  table (Table C); regime-vs-universe scenarios (Table D); dilution math (Table E)
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared with explicit
  reason (universe expansion adds new training data via Model F, changes Optuna
  training-objective domain); mitigation choice stated (none opt-in; ENSEMBLE_SIZE=3
  cycle-3 default); forward-mandate accumulation rule cited
- Section 3 (Proposed Changes): PASS — axis changes fully specified: 6-sym
  V1_ITER017_UNIVERSE (LOCAL runner constant); Model F SOL config explicit (atr_tp=2.9,
  atr_sl=1.45, R3-only, bounds_profile=v1_pruned); no other axis changes (abs_pnl
  reverted, ATR labeling unchanged, V1_FEATURE_COLUMNS_PRUNED unchanged); Section 3.4
  LM Master responses PASS (3 staked calls ADOPTED at a145ee0)
- Section 4 (Expected OOS Impact): PASS — F1-F8 + F-AXIS-MECHANISM-NEW compound
  falsifier (3 sub-checks: dispatch fires, SOL share ∈ [5%, 40%], n_eff ∈ [10,18]);
  FLAT prior Δ bands; catastrophic floor Δ ≤ -0.55; explicit falsifier thresholds
- Section 5 (Predicted Outcomes): PASS — 33%/33%/34% PROMISING/NULL/NEGATIVE table;
  mechanism-level confidence percentages per sub-check; E[F1 OOS Δ] ≈ -0.001
- Section 6 (Risk Mitigation): PASS — 7 failure modes (A-G) with forward paths;
  regime-vs-universe diagnostic scenarios (A/B/C) pre-registered; per-model risk gates
  unchanged (R1 C/D/E, R2 E only, R3 all including new Model F); no new risk primitives
- Section 7 (Failure-Mode Prediction): PASS — Section 6 covers 7 pre-registered failure
  modes with forward paths; regime-bound vs universe-bound diagnostic explicit in both
  Section 2.4 and Section 6.7; BASELINE never updated by EXPLORATION explicitly stated
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 9-cell verdict matrix with F1/F3/F7/F8/
  F-AXIS-MECHANISM gating; Cells 8/9 mechanical failures checked first; EXPLORATION
  never updates BASELINE_V1 explicitly stated (Section 7)
- Section 9 (Library Stack): PASS — numpy/pandas/lightgbm/optuna declared; no new
  third-party dependencies; implementation described (LOCAL constant + elif branch in
  run_baseline_v1.py only; no src/ changes required per Section 10.1)

## Reason for PASS
The only defect from the prior BLOCK (50f8a31) was Section 3.4 missing explicit
"Adopted/Modified/Rejected" disposition labels for the LM Master's 3 staked calls.
That defect is corrected at a145ee0: all 3 staked calls carry explicit "ADOPTED"
labels with per-recommendation rationales. All other 13 sections were PASS at the
prior gate and remain unchanged. OVERALL=PASS.

## QE Dispatch Note
- Feature regeneration MANDATORY before backtest: `uv run crypto-trade features
  --symbols SOLUSDT --interval 8h --track v1 --format parquet --workers 1`
- Verify SOL parquet: last_open >= 2025-04-24 AND all 40 V1_FEATURE_COLUMNS_PRUNED cols
- No --no-engineering-report flag (Section 10.3 prohibition; /016 5th-strike rule)
- Runner invocation must include --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT,SOLUSDT
