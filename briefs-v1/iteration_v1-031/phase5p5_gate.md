# Phase 5.5 Gate — iter-v1/031

OVERALL: PASS

Brief HEAD evaluated: `d96dc71` (research_brief.md).
LM Master advisory evaluated: `f07c494` (lgbm_advisor.md).

---

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION-WITH-BUDGET-EXCEPTION

Declared in brief Section 0.5 with explicit justification: /030 §8 BINDING mandate requires
5-seed × 50-trials INNER ensemble; 2h soft cap superseded by the harder constraint. Wall-clock
modal 3.60h, inside CONFIRMATION-mode 6h hard cap. Kill-switch armed at 5.0h. Non-blocking.

## (v1 only) Axis Family + Rotation Status
FAMILY: sample-weighting (NINTH family in v1; previously closed at /016 for `uniform` +
`uniqueness_only`; REVIVED via orthogonal `inv_concurrency_only` pivot per LM Master §1)

ROTATION_STATUS: VALID

Verification — prior 5 EXPLORATIONs (per Section 0.6; /026 sanity slot + /027 CONFIRMATION-TF
exempt from Axis Rotation Discipline):

| iter | family                              | verdict            |
|------|-------------------------------------|--------------------|
| /024 | model-arch (regime-conditional)     | NEG-clean          |
| /025 | feature-family (OI delta z-score)   | LEARNED-NEG-CAT    |
| /028 | per-cohort-specialization-LTC-v2    | PROMISING +0.598   |
| /029 | per-cohort-specialization-DOT-v2    | TECHNICAL-FAILURE  |
| /030 | meta-labeling (M2 binary A/C/D)     | NEG-CATASTROPHIC   |

Three distinct families across 5 slots — NOT a 5-of-5 monoculture. Additionally,
`sample-weighting` was last attempted at /016 (cycle-3), with ≥15 EXPLORATIONs in other
families since then. Rotation discipline honored. VALID by dual criteria (family diversity
in prior-5 + prior-family-gap of ≥15 iterations in other families since /016).

LM Master §1 three load-bearing distinctions establishing /031 ≠ /016:
(1) Distributional std 0.33 vs 0.003 (100× wider); (2) Kish ratio 0.899 vs ~1.0 (alive vs
vacuous); (3) pooled Spearman vs uniqueness_only 0.034 (totally distinct ordering). /016
closure does NOT extend per LM Master §1 verdict "PIVOT LEGITIMATE."

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: YES — sample-weighting reshapes Optuna's training-objective domain (loss-surface
gradient via per-row weight inversion). Basin-shift-vulnerable per /016 precedent. /030
root-cause was M1 budget-downshift basin relocation — sample-weighting is the OTHER mechanism
class that can produce basin relocation.

Mitigation: LM Master §3 3 basin-stability validations MANDATORY (not opt-in):
  1. Cross-seed Optuna best-trial Sharpe std/mean ≤ 0.25 PASS threshold
  2. Per-cell best-param Spearman across 5 seeds ≥ 0.50 PASS threshold
  3. Trade-roster overlap baseline ↔ /031 OOS per symbol within [35%, 75%]

Multi-seed opt-in: PATH A 5-seed inner ensemble IS the multi-seed validation configuration
per /030 §8 BINDING mandate. Single outer seed (=42) acknowledged; basin-stability
Validation 1 cross-seed measurement catches single-outer-seed basin lottery.

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-031/lgbm_advisor.md exists: PASS (commit `f07c494`)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

LM Master §1-§9 + Q1-Q7 cross-check (brief Section 3.4):
- §1 Mechanism Pivot Adjudication: ADOPTED — inv_concurrency_only pivot endorsed on three
  load-bearing distinctions; literal AFML uniq×inv_conc REJECTED per EDA 2.1-2.2 degeneracy
- §2 Hyperparameter Region: ADOPTED — STRICT REPLICATION bounds_profile="v1_pruned_axis016"
  for attribution cleanliness; 6-tweak exploitation alternative REJECTED
- §3 Basin-Stability Validations: ADOPTED VERBATIM — all 3 validations with exact thresholds;
  forensic log emission requirement specified in Section 3.3 + Section 2.6
- §4 Mechanism Recommendation + Prior Table: ADOPTED VERBATIM — 5-row verdict matrix with
  exact probabilities (17/23/30/18/12%) and OOS Δ bands; modal INERT-NO-EFFECT 30%
- §5 Falsifier Pre-Registration: ADOPTED VERBATIM — F-AXIS #1-#5 all in brief Section 2;
  F-AXIS #5 OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING transferred from /028/030
- §6 Track-Record Commentary: ACKNOWLEDGED — MEDIUM directional confidence; 4/10 directional;
  1/1 NEG-CAT prior at sample-weighting family acknowledged
- §7 Routing Recommendation /032: ADOPTED PRE-COMMIT — 5-cell routing table with explicit
  /031 verdict → /032 axis determination pre-registered; NO third sample-weighting variant
- §8 Wall-Clock + Budget Exception: ADOPTED — PATH A endorsed; EXPLORATION-WITH-BUDGET-
  EXCEPTION declared; kill-switch at 5.0h; no mid-run n_trials compression permitted
- §9 Seven adjudication questions Q1-Q7: ALL ADOPTED — Q1 composite formula, Q2 hyperparameter
  region, Q3 per-model differential, Q4 verdict priors, Q5 basin-stability variance threshold,
  Q6 wall-clock risk, Q7 /032 routing prior

Brief Section 0.2 explicitly states: "QR ADOPTS all 9 of 9 LM Master adjudications."
All 9 LM Master sections and 7 Q's explicitly addressed. PASS.

## Cadence Check (v1)
- Wall-clock budget declared: 3.60h modal (Section 3.6 + 0.5); EXPLORATION-WITH-BUDGET-
  EXCEPTION at 6h CONFIRMATION-mode hard cap with 5.0h kill-switch: PASS
- Cycle-4 EXPLORATION 4/10 declared in brief header and Section 0.1: PASS
- CONFIRMATION precedent count: N/A (this is EXPLORATION)
- CONFIRMATION imports prior EXPLORATION variations: N/A

---

## Per-Section Status (13 checks)

### Check 1 — Brief Structure (all required sections present)
- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 in Section 10.1 (Reproducibility).
  IS/OOS absolute window implicit in training_months=24 anchor. Consistent with /028/030
  brief format; content unambiguous. Non-blocking.
- Section 0.5 (Iteration Type, v1): PASS
  EXPLORATION-WITH-BUDGET-EXCEPTION declared explicitly in Section 0.5 with justification.
  Budget exception endorsed by LM Master §8. Wall-clock at CONFIRMATION-mode hard cap.
- Section 0.6 (Architecture-Family Justification, v1): PASS
  Section 0.6 + Section 3.8 provide: family = sample-weighting; prior 5 EXPLORATIONs table;
  rotation status VALID with dual-criterion rationale; /016 closure non-extension per LM
  Master §1 three load-bearing distinctions; full axis family orthogonality argument.
- Section 1 (Hypothesis): PASS
  Section 1 / Section 0 H1 is one-sentence with specific mechanism (inv_concurrency_only),
  OOS Δ band ([-0.40, +0.55] modal +0.04), budget config (5-seed × 50-trials × PRUNED-43),
  and causal link (reshaping Optuna's training-objective domain). LM Master §4 net expected
  OOS Δ +0.04 cited. Specific and falsifiable.
- Section 1.5 (/016 PRIOR — MANDATORY per LM §1 Fact 2): PASS
  Section 1.5 provides: /016 setup (3-seed × 18-trials; uniform + uniqueness_only; NEG-CAT);
  three load-bearing distinctions vs /031 per LM Master §1; conditional closure acknowledgment;
  budget comparison (4.32× compute at /031); mechanism activity comparison (Kish 0.899 vs ~1.0);
  Section 1.5 prior calibration with /016 closure conditional framing. MANDATORY section present.
- Section 2 (IS-Only Evidence): PASS
  analysis/iteration_v1-031/composite_variants_portfolio.csv + spearman_orthogonality.csv +
  per_month_kish.csv + weight_distribution.csv + concurrency_profile.csv committed `0cff4b8`.
  Scripts: sample_weighting_composite_eda.py + composite_variants_eda.py committed `0cff4b8`.
  Sections 1.1-1.6 cite IS-only numerical tables from committed CSVs. No OOS data in EDA.
- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS
  HIGH-RISK declared with explicit rationale (loss-surface reshape via per-row weight
  inversion; basin-shift-vulnerable per /016; /030 root-cause analogy). Three mandatory
  mitigations from LM Master §3 cited. Multi-seed opt-in mechanism explained (PATH A 5-seed
  inner IS the opt-in configuration per /030 §8 mandate).
- Section 2.6 (Basin-stability Validations — MANDATORY per LM Master §3): PASS
  Section 2.6 present with all 3 validations: Validation 1 (cross-seed Sharpe std/mean ≤
  0.25), Validation 2 (per-cell best-param Spearman ≥ 0.50), Validation 3 (trade-roster
  overlap [35%, 75%]). Timing: Phase 7. Forensic log emission requirement for per-cell inner-
  seed best-trial Sharpe and hyperparameters explicitly stated. Fail thresholds for each
  (> 0.40 / < 0.30 / < 25% or > 80%) clearly enumerated.
- Section 3 (Proposed Changes): PASS
  Subsections 3.1 (universe UNCHANGED), 3.2 (labels UNCHANGED), 3.3 (sample-weight formula
  + implementation path + look-ahead audit + DO NOT modify baseline path), 3.4 (LM Master
  Response Map §1-§9 all addressed), 3.5 (configuration locks), 3.6 (5-step wall-clock
  scaling), 3.7 (code changes enumerated), 3.8 (axis family declaration for Critic Check 14).
  - Section 3.4 LM response map (§1-§9 + Q1-Q7): PASS (all 9 + 7 addressed; ADOPTED/
    MODIFIED/REJECTED tags applied; all marked ADOPTED)
- Section 4 (Verdict Matrix / Expected OOS Impact): PASS
  5-row verdict matrix with OOS Δ bands, prior probabilities (from LM Master §4 ADOPTED),
  mechanism interpretation per verdict cell. F-AXIS override caps explicitly enumerated.
  Explicit falsifier: OOS Δ band with caps at Row 1 (technical failure), Row 2/3 (F5 Model D
  cap), Rows 4-6 (Validation override reclassification). Pre-committed modal INERT-NO-EFFECT
  30% per LM Master §4 net expected OOS Δ +0.04.
- Section 5 (Risk Mitigation): PASS
  R1 (ON for C/D/E, OFF for A), R2 (OFF), R3 (ON, 70th pctl Mahalanobis). Basin-stability
  monitoring as risk-mitigation layer for HIGH-RISK declaration. Wall-clock kill-switch at
  5.0h. F-AXIS forensic log emission requirement for per-cell inner-seed best-trial data.
  IS-calibrated thresholds in Section 6.2 (Kish ratio 0.899; pooled ρ -0.093; LM Master §4
  net expected OOS Δ +0.04).
- Section 6 (Risk Management Design): PASS
  4-row gate-stack table with IS/OOS fire-rate predictions, regime coverage, gate-attribution
  estimate. NEW inv_concurrency_only weight row included. Section 6.1 regime coverage
  narrative + 6.2 IS-calibrated gate-effect attribution + 6.3 verdict-capping reminders.
  Structured format mirrors /030 §6 (per brief self-reference at Section 6 opening).
- Section 7 (Failure-Mode Prediction, v1): PASS
  3 pre-registered failure modes: 7.1 WIRING SILENT FALLBACK (most likely; metric signature
  F-AXIS #1/#3 + BIT-IDENTICAL trade roster); 7.2 BASIN-RELOCATION /030 MIRROR (second-most-
  likely; Validations 1-3 metric signatures); 7.3 ABS_PNL STRUCTURAL EDGE DISPLACEMENT
  (NEG-CAT; Validations 1-3 PASS but OOS Δ < -0.40). Critic Phase 6.0 pre-flight check
  requirement noted in 7.1 (catch-all exclusion + dispatch banner). Forward-looking for
  Phase 8 diary verification. STRUCTURED.
- Section 8 (Verdict Cell Determination Table — MERGE/NO-MERGE Criteria, v1): PASS
  12-row pre-committed verdict determination table with explicit (F1, F2, F3, F5, V1, V2, V3)
  tuples per condition. Explicit tuple-determination examples (9 tuples resolved). F-AXIS
  override caps (Row 1: tech-failure; Rows 2-3: F5 caps; Rows 4-6: Validation reclassification;
  Rows 7-12: F1 OOS Δ bands). Pre-registered before backtest runs. Numerical thresholds
  locked. STRUCTURED.
- Section 9 (Library Stack, v1): PASS
  lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, statsmodels 0.14.6 declared.
  Invocation status per library: lightgbm LOAD-BEARING (sample_weight at training-row level);
  optuna LOAD-BEARING (n_trials=50 single-outer-seed=42; 5 inner seeds); numpy/pandas LOAD-
  BEARING (per-bar weight vector + per-symbol mean-renormalization). mlfinlab/mlfinpy NOT
  INSTALLED with in-tree fallback path. fracdiff NOT INSTALLED. pypbo N/A for EXPLORATION.
  Sections 9.1 (invocation status), 9.2 (NEW module path), 9.3 (no version bumps) present.
- Section 10 (Reproducibility + Symbol Exclusion + Test Suite Mandate):
  - Section 10.1 (Reproducibility): PASS — outer seed=42, ENSEMBLE_SIZE=5, n_trials=50,
    sample_weight_mode=composite_inv_concurrency, bounds_profile=v1_pruned_axis016 LOCKED;
    OOS_CUTOFF_DATE=2025-03-24 UNCHANGED; training_months=24 UNCHANGED; persist paths declared.
  - Section 10.2 (Symbol Exclusion): PASS — V1_EXCLUDED_SYMBOLS unchanged; V1_BASELINE_UNIVERSE
    5-symbol unchanged.
  - Section 10.3 (Test Suite Mandate): PASS — 4 regression tests (10.3.1 incl. NEW concurrency
    look-ahead test) + 11 iteration-specific tests (10.3.2). MANDATORY items verified:
    - BASELINE CATCH-ALL EXCLUSION: test_v1_iter031_baseline_catchall_exclusion (test 5) ✓
    - DISPATCH BANNER: test_v1_iter031_dispatch_banner (test 6) ✓
    - Sample-weight wiring to LightGBM: test_v1_iter031_weight_wiring_to_lightgbm (test 4) ✓
    - /027 lesson hardened at 10.3.3 (hard-assert must include sample-instance unit test)
    - 10.3.4 NO HARD-ASSERT on graceful fallback paths

OVERALL CHECK 1: PASS

### Check 2 — Numerical Evidence
Analysis scripts composite_variants_portfolio.csv + spearman_orthogonality.csv +
per_month_kish.csv + weight_distribution.csv + concurrency_profile.csv committed `0cff4b8`.
sample_weighting_composite_eda.py + composite_variants_eda.py confirmed committed. Sections
1.1-1.6 cite IS-only numerical tables. No OOS-data contamination. PASS

### Check 3 — LM Master Integration
All 9 LM Master sections + 7 adjudication questions addressed in Section 3.4 + Section 0.2
with ADOPTED tag on all 9. No recommendation unaddressed. PASS

### Check 4 — Axis Rotation Discipline
sample-weighting: prior 5 disperse across 3 distinct families (model-arch, feature-family,
per-cohort-specialization, meta-labeling). NOT 5-of-5 monoculture. Additionally /016 closure
is >15 EXPLORATIONs in the past. VALID by family diversity + prior-family-gap criteria. PASS

### Check 5 — HIGH-RISK Declaration
HIGH-RISK declared with rationale: loss-surface reshape via per-row weight inversion changes
Optuna's training-objective domain. Three mandatory mitigations from LM Master §3.
Multi-seed mitigation opt-in: PATH A 5-seed inner ensemble IS the opted-in configuration. PASS

### Check 6 — Falsifier Pre-Registration
F-AXIS #1-#5 in Section 2 with explicit bands per LM §5 ADOPTED VERBATIM:
- F-AXIS #1: ≥ 95% of (model, month) cells emit [sample_weight_mode=composite_inv_concurrency]
  print (265 expected cells = 53 months × 5 models); FAIL < 80% → tech-failure
- F-AXIS #2: IS [560, 690] modal 621; OOS [165, 215] modal 190; FAIL < 150 OOS → tech-failure
- F-AXIS #3: cross-seed best-param Spearman < 0.90 PASS; > 0.95 → tech-failure-silent-no-op
- F-AXIS #4: median n_eff per cell [14, 22]; FAIL < 8 → basin-collapse
- F-AXIS #5: OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING (verdict-capping)
All 5 present with bands. Validation 1-3 override conditions enumerated in Section 4 and 8.
PASS

### Check 7 — Test Mandate
Section 10.3 lists 4 regression tests (10.3.1) + 11 iteration-specific tests (10.3.2) = 15+
total (exceeds 10-test minimum). MANDATORY items per /030 LESSONS verified:
- BASELINE CATCH-ALL EXCLUSION: test_v1_iter031_baseline_catchall_exclusion (test 5) ✓
- DISPATCH BANNER: test_v1_iter031_dispatch_banner (test 6) ✓
- sample_weight wiring to LightGBM: test_v1_iter031_weight_wiring_to_lightgbm (test 4) ✓
- /027 lesson: 10.3.3 every hard-assert must include sample-instance unit test ✓
- 10.3.4 no hard-assert on graceful fallback paths ✓
PASS

### Check 8 — Cadence Position
Brief header: "Cycle: 4, EXPLORATION 4 of 10". Section 0.1 confirms precedents:
/028 PROMISING, /029 TF, /030 NEG-CAT, /031 = THIS. 6 EXPLORATIONs remain. PASS

### Check 9 — No OOS Leakage in Design
Sections 1-6 cite IS data only (concurrency_profile.csv, composite_variants_portfolio.csv,
per_month_kish.csv, spearman_orthogonality.csv, weight_distribution.csv — all IS-only per
brief header). Verdict matrix (Section 4/8) is forward-looking. Phase 7 failure-mode
prediction (Section 7) is prospective. PASS

### Check 10 — CONFIRMATION Precedent Count
N/A — this is EXPLORATION. PASS

### Check 11 — Reproducibility Section
Section 10.1: outer seed=42, ENSEMBLE_SIZE=5, n_trials=50, sample_weight_mode=
composite_inv_concurrency, bounds_profile=v1_pruned_axis016 ALL LOCKED. OOS_CUTOFF_DATE=
2025-03-24, training_months=24, embargo at walk_forward.py:113 UNCHANGED. Persist paths
declared: oof_persist_path, params_persist_path, optuna_trials_log_path (NEW for Validation
1+2). HEAD commit placeholder "TBD at Phase 5.5 PASS commit" — expected at gate time. PASS

### Check 12 — Wall-clock Estimate (5-step label-rate scaling)
Section 3.6: 5-step scaling per feedback_v1_label_rate_wall_clock_scaling.md:
Step 1: /016 precedent = ~50 min (3-seed × 18-trials × PRUNED × 5-sym × 8h)
Step 2: /016 label rate = baseline labels
Step 3: /031 label rate = SAME (M1 UNCHANGED; ratio = 1.0)
Step 4: config scaling = (5/3)^0.85 × (50/18) × 1.0 = 1.554 × 2.778 × 1.0 = 4.32×
Step 5: axis overhead = c_at_entry precompute ~10 min total
Total: 50 min × 4.32 + 10 min ≈ 226 min = 3.77h modal (brief cites 3.60h without overhead).
Cross-check via baseline anchor also provided. Inside 6h hard cap (EXPLORATION-WITH-BUDGET-
EXCEPTION framing). Kill-switch armed at 5.0h. PASS

### Check 13 — Library Stack (Section 9)
lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, statsmodels 0.14.6 declared.
Invocation status per library. mlfinlab/mlfinpy NOT INSTALLED with in-tree fallback.
fracdiff NOT INSTALLED. pypbo N/A. Sections 9.1/9.2/9.3 present. No version bumps required. PASS

---

## Summary

All 13 checks PASS. LM Master §1-§9 + Q1-Q7 fully integrated with all 9 ADOPTED.
HIGH-RISK axis declaration present with 3 mandatory mitigations (LM Master §3 verbatim).
Axis rotation VALID. Numerical evidence committed at `0cff4b8`. 15+ tests in mandate
(catch-all exclusion + dispatch banner mandatory items both present). 5-step wall-clock
scaling within EXPLORATION-WITH-BUDGET-EXCEPTION 6h hard cap. /016 PRIOR section (1.5)
present and mandatory. Basin-stability validations (Section 2.6) present with exact thresholds
and forensic log emission requirement.

OVERALL: PASS

Phase 6.0 Critic pre-flight dispatch is authorized.
