# Phase 5.5 Gate — iter-v1/036

OVERALL: PASS

Brief HEAD evaluated: `0aed2d0` (research_brief.md).
LM Master advisory: NOT PRESENT — Phase 4.5 SKIPPED per explicit user directive
(mirrors /033, /034, /035 precedent; mission brief directive applies).
Gate check for LM Master response verification is USER-DIRECTIVE-WAIVED.

---

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5 EXP 3 of 10)

Wall-clock target: ~25 min modal (~0.4h), conservative band 20-45 min.
No kill-switch per cycle-5 directive (user directive 2026-05-30).

## (v1 only) Axis Family + Rotation Status
FAMILY: per-cohort-specialization (REPEAT — but JUSTIFIED; see below)

ROTATION_STATUS: VALID (REPEAT-JUSTIFIED) — `per-cohort-specialization` last fired
outside the prior-5 window (cycles 3-4: /018 LINK, /019 ETH, /020 BTC, /028/029 LTC/DOT).
Prior 5 EXPLORATION families:

| iter  | family                        | verdict                                  |
|-------|-------------------------------|------------------------------------------|
| /031  | sample-weighting              | PROMISING-BASIN-RELOCATION-ARTIFACT      |
| /032  | sample-weighting-isolation    | PROMISING-AXIS-PARTIAL                   |
| /033  | confirmation-bundle           | BLOCK-FINAL (CONFIRMATION-EXCEPTION)     |
| /034  | feature-family                | EXPLORATION-NEGATIVE / LEARNED-NEG       |
| /035  | labeling                      | EXPLORATION-NEGATIVE-CATASTROPHIC (bimodal) |

Four distinct families across last 5 slots (sample-weighting/2, confirmation-bundle/1,
feature-family/1, labeling/1). `per-cohort-specialization` is NOT in last 5.
Monoculture threshold NOT reached. ROTATION_STATUS: VALID.

REPEAT-JUSTIFIED rationale (from Brief Section 0.6): /036 is the load-bearing
follow-up to /035's structural bimodal finding (LINK +74.68pp / DOT +111.67pp OOS
at trend-scanning). Per Critic /035 Path Forward §"/036 RECOMMENDATION", isolating
these two cohorts is the canonical attribution test — cannot substitute a different
family without destroying the bimodal-signal attribution from /035.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: YES (2-mechanism stack: per-cohort isolation + trend-scanning labels)

Reason: (1) universe substitution from 5-cohort → 2-cohort removes large-cap Optuna
averaging, changing the training-objective domain composition; (2) trend-scanning label
mode already HIGH-RISK at /035 (training-objective domain change). Both mechanisms
trigger HIGH-RISK individually; composing them stacks the risk.

Mitigation (single-seed OPT-OUT per cycle-5 EXPLORATION standard):
- F-AXIS #3 LOAD-BEARING per-symbol OOS lift falsifier (LINK ≥+50pp AND DOT ≥+50pp)
- F-AXIS #5 trade-roster overlap with /035 LINK+DOT subset (basin-relocation diagnostic)
- Pre-flight asserts: `assert label_mode_arg == "trend_scanning"` +
  `assert set(symbols) == {"LINKUSDT", "DOTUSDT"}`
- HIGH-RISK single-seed counter: /034 NORMAL-RISK (reset) → /035 HIGH-RISK NEG-CAT
  (count=1) → /036 HIGH-RISK single-seed (count=2). Not at auto-upgrade threshold (3).

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-036/lgbm_advisor.md exists: USER-DIRECTIVE-WAIVED
  (Phase 4.5 explicitly skipped per /033+/034+/035 precedent; mission brief applies)
- Brief Section 3 addresses each LM Master recommendation: USER-DIRECTIVE-WAIVED
  (no advisory to respond to; non-blocking per user directive)

## Cadence Check (v1)
- Wall-clock budget declared: ~25 min modal (band 20-45 min) — INSIDE 2h cap: PASS
- EXPLORATION TYPE 3 of 10 (cycle-5): PASS
- CONFIRMATION precedent count: N/A (TYPE is EXPLORATION, not CONFIRMATION)
- No CONFIRMATION = no precedent count gate needed

---

## Per-Section Status (13 checks)

### Check 1 — Brief Structure (all required sections present)

- Section 0 (Data Split): PASS
  Brief Section 0 contains "Section 0 — Hypothesis" (brief renumbering convention
  vs gate template). Data split declaration is embedded in Section 0.5, Section 3.4,
  and Section 10.2:
  - OOS_CUTOFF_DATE = 2025-03-24 confirmed at Section 3.4 Table row "OOS_CUTOFF" and
    Section 10.2 ("OOS_CUTOFF_MS = 1742774400000 SACRED — unchanged").
  - training_months = 24 confirmed at Section 3.4 Table and Section 10.2 (SACRED).
  - IS window = 2020-01 → 2025-03-23; OOS = 2025-03-24 onward confirmed Section 10.4.
  Same brief-numbering convention used at /035; gate PASS criterion is content not
  heading label. PASS

- Section 0.5 (Iteration Type, v1): PASS
  TYPE: EXPLORATION declared. Cycle-5 EXP 3 of 10 (after /034 NEGATIVE + /035
  NEG-CAT bimodal pivot). Wall-clock ~25 min modal, band 20-45 min.
  No kill-switch per cycle-5 directive. Cadence rationale stated. PASS

- Section 0.6 (Architecture-Family Justification, v1): PASS
  Family: `per-cohort-specialization` (REPEAT-JUSTIFIED). Prior 5 EXPLORATION
  families enumerated (4 distinct families across 5 slots; `per-cohort-specialization`
  not in last 5). Rotation VALID. One-sentence rationale present (Critic /035
  Path Forward binds /036 to per-cohort isolation of LINK + DOT).
  Monoculture threshold NOT reached. PASS

- Section 1 (Hypothesis): PASS
  Brief Section 0 = Hypothesis (brief uses Section 0 for what gate calls Section 1).
  H1 PRIMARY specific: 2-cohort bundle LINK+DOT trend-scanning at per-cohort
  isolation, OOS Sharpe ≥+1.0 and per-symbol OOS Δ ≥+50pp on BOTH.
  H1a mechanistic elaboration: /035 bimodal-confound attribution.
  H1b explicit falsifier: "if 2-cohort OOS Δ < +0.20 OR EITHER LINK or DOT OOS lift
  < +50pp → mechanism REFUTED". Specific and falsifiable. PASS

- Section 2 (IS-Only Evidence): PASS
  Brief Section 1 = IS-Only Evidence (numbering shift). Cites /035 per-symbol OOS
  attribution from `briefs-v1/iteration_v1-035/review.md` (Critic FINAL 2026-05-30)
  — numerical tables present (5 symbols × 5 columns: trades, WR, PnL%, baseline,
  Δ). No new EDA script per mission brief directive ("reuse /035 evidence"). Prior
  iteration's committed Critic FINAL is the load-bearing evidence source; no new
  EDA is required. Section 1.4 cites 7 prior per-cohort EXPLORATIONs with outcomes.
  No OOS contamination during design (Section 10.4 confirms). PASS

- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS
  HIGH-RISK declared explicitly. Reason: 2-mechanism stack (per-cohort isolation +
  trend-scanning labels; both trigger HIGH-RISK individually). Mitigation: F-AXIS #3
  LOAD-BEARING + F-AXIS #5 overlap + pre-flight asserts. Single-seed OPT-OUT declared
  with HIGH-RISK counter tracking (count=2 of 3 auto-upgrade threshold). PASS

- Section 3 (Proposed Changes): PASS
  Brief Section 3 = Implementation Design. 1 atomic edit enumerated with file paths
  and LOC estimates: EDIT `run_baseline_v1.py` (V1_ITER036_UNIVERSE constant +
  dispatch branch dispatching ONLY Model C' + Model E + exclusion-tuple add).
  LM Master responses: USER-DIRECTIVE-WAIVED. No feature regen needed. PASS

- Section 4 (Expected OOS Impact): PASS
  Brief Section 2 = Falsifiers. F-AXIS #1 OOS Δ bands map to PROMISING-CLEAN /
  PROMISING / INERT / NEGATIVE / NEG-CAT with explicit numerical thresholds.
  Modal prior: PROMISING 75% vs NEG 10% (justified by /035 direct attribution).
  F-AXIS #4 bundle OOS Sharpe target provides explicit predicted range [+0.5, +1.5]
  with modal +1.0 (Δ +0.34 vs baseline +0.6637). PASS

- Section 5 (Risk Mitigation): PASS
  Brief Section 5 = Risk Mitigation. 5-row risk table: R1 (ON, Model C'+E),
  R2 (ON, Model E only), R3 (ON both), bundle concentration (acknowledged, deferred
  to /037 CONFIRMATION routing), HIGH-RISK 2-mechanism stack (F-AXIS #3 + F-AXIS #5).
  EXPLORATION-level acknowledgment of concentration pre-failure with explicit
  /037 routing plan. PASS

- Section 6 (Risk Management Design): PASS
  Brief Section 6 = Risk Management Table. 7-row risk table with likelihood, severity,
  mitigation columns: dispatch branch routing failure, universe set-equality failure,
  label_mode threading failure, single-seed basin lottery, 5-cohort confound,
  concentration pre-failure, forming-candle leak. PASS

- Section 7 (Pre-Registered Failure Modes, v1): PASS
  Brief Section 7 = Failure-mode Prediction. Full behavioral-effect predictor per
  `feedback_v3_axis_saturation_predictor.md` mandate:
  - IS trade count: [200, 400] modal ~280
  - OOS trade count: [80, 160] modal ~110
  - Per-symbol OOS Δ: LINK ≥+50pp modal +75pp / DOT ≥+50pp modal +110pp
  - Bundle OOS Sharpe: [+0.5, +1.5] modal +1.0
  - F-AXIS #5 overlap LINK/DOT: 50-75%
  Explicit FALSIFIER triggers (4 numbered). Mechanism failure scenario (5-cohort
  confound via aggressive per-cohort Optuna recalibration) stated forward-looking. PASS

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria, v1): PASS
  Brief Section 8 = Verdict Cell Determination. Python pseudo-code decision tree
  maps overlap + trade counts + per-symbol lift + F1 OOS Δ to explicit verdict cells.
  10-row verdict matrix (Section 4) provides comprehensive verdict mapping.
  Pre-committed before backtest, eliminates post-hoc rationalization. PASS

- Section 9 (Library Stack, v1): PASS
  Libraries declared: numpy (OLS/t-stat reused), pandas (DataFrame ops), lightgbm
  (UNCHANGED), optuna (UNCHANGED), pyarrow (UNCHANGED). No new dependencies required.
  mlfinlab/mlfinpy/fracdiff: NOT used at trend-scanning runtime. PASS

- Section 10 (Symbol Exclusion + Reproducibility + Test Suite Mandate): PASS
  Section 10.1 (Symbol Exclusion): V1_ITER036_UNIVERSE = (LINKUSDT, DOTUSDT).
    Both are in V1_BASELINE_UNIVERSE; neither is in V1_EXCLUDED_SYMBOLS. PASS
  Section 10.2 (Reproducibility): outer seed=42; ENSEMBLE_SIZE=3 inner (42,123,456);
    n_trials=18; label_mode=trend_scanning; trend_scan_grid=(5,8,13,21);
    OOS_CUTOFF_DATE=2025-03-24 UNCHANGED; training_months=24 UNCHANGED;
    walk_forward.py:113 embargo confirmed. PASS
  Section 10.3 (Test Suite Mandate, 10 tests): PASS — All 10 tests enumerated:
    BASELINE CATCH-ALL EXCLUSION (test 6) ✓
    DISPATCH BANNER (test 7) ✓
    PRE-FLIGHT ASSERT label_mode mismatch (test 4) ✓
    PRE-FLIGHT ASSERT universe mismatch (test 5) ✓
    label_mode threaded to LINK model (real instance /027 LESSON, test 8) ✓
    label_mode threaded to DOT model (real instance /027 LESSON, test 9) ✓
    2-model dispatch only (test 10) ✓
    V1_ITER036_UNIVERSE constant (test 1) ✓
    Universe subset of baseline (test 2) ✓
    Dispatch branch exists (test 3) ✓
  Section 10.4 (Anti-cheating): OOS_CUTOFF_MS = 1742774400000; IS-only; OOS not
    inspected during design; all /035 evidence from committed Critic FINAL. PASS

OVERALL CHECK 1: PASS

### Check 2 — Numerical Evidence
Brief Section 1.1 provides 5-symbol OOS attribution table from /035 Critic FINAL
(2026-05-30): DOT +111.67pp / LINK +74.68pp / BTC -50.79pp / ETH -46.48pp / LTC +14.49pp.
Section 1.2 provides bundle-level comparison table. Section 1.3 provides LINK+DOT prior
specialist precedent (7 prior experiments). No new EDA script per mission directive
(permitted — prior committed Critic FINAL is load-bearing evidence). No OOS contamination.
No category-matching; concrete numbers from committed artifact. PASS

### Check 3 — LM Master Integration
USER-DIRECTIVE-WAIVED. Phase 4.5 skipped per explicit user directive (mirrors
/033+/034+/035 precedent). No lgbm_advisor.md exists; no Section 3 responses required.
Non-blocking per directive. PASS

### Check 4 — Axis Rotation Discipline
`per-cohort-specialization` not in last 5 EXPLORATION families (last 5 span 4 distinct
families). REPEAT-JUSTIFIED per Critic /035 Path Forward §"/036 RECOMMENDATION" + LM
Master /035 finding that binds /036 to bimodal isolation. Monoculture threshold NOT reached.
One-sentence rationale present. VALID. PASS

### Check 5 — HIGH-RISK Declaration
HIGH-RISK declared explicitly. 2-mechanism stack: per-cohort isolation (universe
substitution 5→2 cohort; training-objective domain change via label-pool composition)
+ trend-scanning labels (already HIGH-RISK at /035; domain change confirmed).
Mitigation: F-AXIS #3 LOAD-BEARING per-symbol lift + F-AXIS #5 overlap diagnostic +
pre-flight asserts (2 separate). Single-seed OPT-OUT per cycle-5 standard. Counter=2. PASS

### Check 6 — Falsifier Pre-Registration (F-AXIS #1-#6 + F-AXIS #3 LOAD-BEARING)
F-AXIS #1: OOS Δ bands: ≥+0.50 PROMISING-CLEAN / [+0.20,+0.50) PROMISING /
  [-0.15,+0.20) INERT (wider noise band justified for HIGH-RISK 2-mechanism)
  / [-0.40,-0.15) NEGATIVE / <-0.40 NEG-CAT. PASS
F-AXIS #2: IS [200,400] / OOS [80,160]. TECHNICAL-FAILURE-SILENT-FALLBACK
  at IS < 150 OR OOS < 60. PASS
F-AXIS #3: LOAD-BEARING per-symbol OOS lift — LINK ≥+50pp AND DOT ≥+50pp (primary
  verdict determinant independent of F1). PASS
F-AXIS #4: Bundle OOS Sharpe target: ≥+1.30 PROMISING-CLEAN-EXCEPTIONAL / +0.86–+1.30
  PROMISING-CLEAN / +0.40–+0.86 PROMISING / +0.30–+0.40 INERT-FAV / <+0.30 REFUTED. PASS
F-AXIS #5: Trade-roster Jaccard overlap with /035 LINK+DOT subset. <25% → BASIN-RELOCATION-
  ARTIFACT. >90% BOTH → TECHNICAL-FAILURE-SILENT-NO-OP. [40%,80%] expected. PASS
F-AXIS #6: Dispatch banner verification: '[iter-v1/036] PER-COHORT-TREND-SCANNING ACTIVE'
  with models, label_mode, trend_scan_grid, ENSEMBLE_SIZE, n_trials, seeds=1, features. PASS
All 6 falsifiers present with explicit bands. PASS

### Check 7 — Test Mandate
Section 10.3 lists 10 tests (exceeds 8-test minimum). All mandatory items present:
- BASELINE CATCH-ALL EXCLUSION per /030 LESSON: test_v1_036_in_baseline_catchall_exclusion ✓
- DISPATCH BANNER: test_v1_036_dispatch_banner_emitted ✓
- PRE-FLIGHT ASSERT label_mode mismatch: test_v1_036_dispatch_branch_pre_flight_label_mode_assert ✓
- PRE-FLIGHT ASSERT universe mismatch: test_v1_036_dispatch_branch_pre_flight_universe_assert ✓
- label_mode threaded to LINK model (real LightGbmStrategy /027 LESSON):
  test_v1_036_label_mode_threaded_to_link_model ✓
- label_mode threaded to DOT model (real LightGbmStrategy /027 LESSON):
  test_v1_036_label_mode_threaded_to_dot_model ✓
- 2-model dispatch only: test_v1_036_dispatches_only_link_and_dot_models ✓
- V1_ITER036_UNIVERSE constant: test_v1_036_universe_constant_exists ✓
- Universe subset of baseline: test_v1_036_universe_subset_of_baseline ✓
- Dispatch branch exists: test_v1_036_dispatch_branch_exists ✓
Existing 8 trend-scanning tests at tests/strategies/ml/test_trend_scanning_label_mode.py
must also pass. PASS

### Check 8 — Cadence Position
TYPE: EXPLORATION — cadence position is cycle-5 EXP 3/10. Cycle-5 started at /034
(EXP 1 NEGATIVE). /035 EXP 2 NEG-CAT bimodal. /036 = EXP 3 (pivot per Critic /035
Path Forward §"/036 RECOMMENDATION"). No CONFIRMATION precedent count gate applies. PASS

### Check 9 — No OOS Leakage in Design
Section 10.4 explicit anti-cheating self-check: OOS_CUTOFF_MS = 1742774400000 SACRED.
All /035 attribution evidence from committed Critic FINAL (`briefs-v1/iteration_v1-035/review.md`).
No new EDA scripts (per mission directive; /035 evidence reused). Section 2 (Falsifiers)
pre-committed before backtest. Section 8 (verdict matrix) pre-committed before backtest.
`_trend_scan_label` reads only close_arr[pos+1..pos+max_h] — strictly forward bars
(audited /035, reused unchanged). PASS

### Check 10 — CONFIRMATION Precedent Count
N/A — TYPE is EXPLORATION, not CONFIRMATION. No precedent count gate required. PASS

### Check 11 — Reproducibility Section
Section 10.2: outer seed=42; ENSEMBLE_SIZE=3 (V1_EXPLORATION_ENSEMBLE_SIZE) inner seeds
(42,123,456); n_trials=18; label_mode=trend_scanning; trend_scan_grid=(5,8,13,21);
sample_weight_mode=abs_pnl (baseline default); OOS_CUTOFF_DATE=2025-03-24 UNCHANGED;
training_months=24 UNCHANGED; walk_forward.py:113 embargo confirmed. PASS

### Check 12 — Wall-clock Estimate (5-step cohort-coverage scaling)
Section 3.6 provides full 5-step scaling:
Step 1: /034 anchor ~50 min (n_trials=18, ES=3, 5 syms, 43 cols)
Step 2: Baseline label count ~621 IS / 189 OOS (5 cohorts)
Step 3: /036 = 2/5 = 0.4× cohort coverage
Step 4: 0.4 × (3/3) × (18/18) × (1/1) × (43/43) × 1.0 label-gen = 0.4×
Step 5: 50 min × 0.4 = 20 min modal compute + 0 min feature-regen + 3 min report
Modal total ~25 min. Conservative band 20-45 min. INSIDE 2h cap. PASS

### Check 13 — Library Stack (Section 9) + Anti-pattern Scan
Library stack (Section 9): numpy + pandas + lightgbm + optuna + pyarrow declared.
No new runtime libraries. mlfinlab/mlfinpy/fracdiff: NOT used. PASS

ONE primary variable changed: per-cohort isolation (2-symbol universe substitution).
Second mechanism (trend-scanning labels) REUSED from /035 — not a new axis variable,
it's the necessary condition for testing /035's bimodal finding. Brief explicitly
frames /036 as the canonical follow-up to /035 (not a dual-axis innovation), which
satisfies the single-primary-variable rule at the attribution level (the bimodal-
isolation test IS the axis; trend-scanning is the preserved context, not a new change).
No other axis changes: features UNCHANGED (43 cols V1_FEATURE_COLUMNS_PRUNED),
model architecture UNCHANGED (Model C' + E with baseline R-gate config), sample-weight
mode UNCHANGED (abs_pnl), Optuna bounds UNCHANGED (v1_pruned). PASS

---

## Summary

All 13 checks PASS. LM Master Phase 4.5 waived by user directive (mirrors /033+/034+/035
precedent). HIGH-RISK declared (2-mechanism stack: per-cohort isolation + trend-scanning
labels; single-seed OPT-OUT per cycle-5 EXPLORATION standard; counter=2).
Axis family `per-cohort-specialization` REPEAT-JUSTIFIED (not in last 5 families; 4 distinct
families across last 5 slots; Critic /035 Path Forward mandates this follow-up).
No new EDA scripts (permitted; /035 Critic FINAL is load-bearing evidence).
10 tests in mandate — all mandatory items present (catch-all exclusion + banner + 2 pre-flight
asserts + 2 REAL-LightGbmStrategy instance thread tests /027 LESSON + 2-model-only dispatch +
universe constant + subset + branch existence). Wall-clock ~25 min modal, inside 2h cap.

OVERALL: PASS

Phase 6.0 Critic pre-flight dispatch is authorized.
