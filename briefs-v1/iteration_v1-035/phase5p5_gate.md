# Phase 5.5 Gate — iter-v1/035

OVERALL: PASS

Brief HEAD evaluated: `7166ad1` (research_brief.md).
LM Master advisory: NOT PRESENT — Phase 4.5 SKIPPED per explicit user directive
(mirrors /033 and /034 precedent; mission brief says "mirror /034's gate format").
Gate check for LM Master response verification is USER-DIRECTIVE-WAIVED.

---

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5 EXP 2 of 10)

Wall-clock target: ~1.0h modal (50-100 min band). No kill-switch per cycle-5 directive
(user directive 2026-05-30 + `docs/skill: no runtime kill-switches`).

## (v1 only) Axis Family + Rotation Status
FAMILY: labeling (structural replacement: triple-barrier → trend-scanning OLS Wald t-stat)

ROTATION_STATUS: VALID — `labeling` last fired at /014 (EWMA σ_t; ~21 EXPLORATIONs ago).
Prior 5 EXPLORATION families (from Brief Section 0.6):

| iter  | family                        | verdict                              |
|-------|-------------------------------|--------------------------------------|
| /030  | meta-labeling                 | NEG-CATASTROPHIC                     |
| /031  | sample-weighting              | PROMISING-BASIN-RELOCATION-ARTIFACT  |
| /032  | sample-weighting-isolation    | PROMISING-AXIS-PARTIAL               |
| /033  | confirmation-bundle           | BLOCK-FINAL (CONFIRMATION-EXCEPTION) |
| /034  | feature-family                | EXPLORATION-NEGATIVE / LEARNED-NEG   |

Three distinct families across last 5 slots (meta-labeling/1, sample-weighting/2,
confirmation-bundle/1, feature-family/1). `labeling` is NOT monoculture. VALID.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: YES

Reason (Brief Section 2.5): label-mode change replaces path-dependent triple-barrier
binary (TP/SL-first-hit) with regression-significance OLS label (Wald t-stat, grid 5/8/13/21).
Changes per-row sample weights from TP/SL-magnitude (~8% modal) to forward-return magnitude
(~2% modal) — 3.3-4.6× scale shift. This is the canonical HIGH-RISK case: Optuna's
training-objective domain is changed.

Mitigation (opt-out at single-seed per cycle-5 EXPLORATION standard):
- F-AXIS #5 cross-seed Spearman diagnostic (informational at single-seed)
- F-AXIS #3 sign-agreement runtime verification
- Pre-flight assert in dispatch branch: `assert label_mode_arg == "trend_scanning"`
- PROMISING outcome triggers multi-seed CONFIRMATION at /044 per HIGH-RISK rule.

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-035/lgbm_advisor.md exists: USER-DIRECTIVE-WAIVED
  (Phase 4.5 explicitly skipped per /033+/034 precedent; mission brief directive applies)
- Brief Section 3 addresses each LM Master recommendation: USER-DIRECTIVE-WAIVED
  (no advisory to respond to; non-blocking per user directive)

## Cadence Check (v1)
- Wall-clock budget declared: ~1.0h modal EXPLORATION (no kill-switch): PASS
- EXPLORATION TYPE 2 of 10 (cycle-5): PASS
- CONFIRMATION precedent count: N/A (this is an EXPLORATION, not CONFIRMATION)
- No CONFIRMATION = no precedent count gate needed

---

## Per-Section Status (13 checks)

### Check 1 — Brief Structure (all required sections present)

- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 confirmed at Brief Section 3.4 Table row "OOS_CUTOFF"
  and Section 10.2 (training_months=24 UNCHANGED). Anti-cheating check at Section 10.4
  confirms `OOS_CUTOFF_MS = 1742774400000` used in EDA script. Sacred constants confirmed.
  IS window = 2020-01 → 2025-03-23; OOS window = 2025-03-24 onward. PASS

- Section 0.5 (Iteration Type, v1): PASS
  TYPE: EXPLORATION declared. Cycle-5 EXP 2 of 10 (renumbered pivot per /034 NEGATIVE).
  Wall-clock modal 1.0h (~60 min), band 50-100 min. No kill-switch per cycle-5 directive.
  Cadence rationale stated (pivot from feature-addition monoculture). PASS

- Section 0.6 (Architecture-Family Justification, v1): PASS
  Family: `labeling`. Prior 5 EXPLORATION families enumerated (3 distinct families across
  5 slots). Rotation VALID with one-sentence rationale (labeling last at /014 σ_t EWMA,
  ~21 EXPLORATIONs ago; trend-scanning is canonical AFML Ch.5 §5.5 next-priority axis).
  Monoculture threshold NOT reached. PASS

- Section 1 (Hypothesis): PASS
  H1 PRIMARY: specific signal (trend-scanning OLS Wald t-stat, grid 5/8/13/21),
  specific mechanism (regression-significance labels vs path-dependent TP/SL-first-hit),
  specific threshold (≥+0.20 OOS Sharpe lift over BASELINE_V1 +0.6637). H1a mechanistic
  elaboration (different supervised target, 24-36% sign-disagreement vs triple-barrier).
  H1b explicit falsifier (F1 OOS Δ < +0.20 AND no per-symbol OOS ≥ +0.10 → INERT-or-worse,
  axis CLOSED). Specific and falsifiable. PASS

- Section 2 (IS-Only Evidence): PASS
  Committed analysis script at HEAD `7166ad1`:
    analysis/iteration_v1-035/trend_scanning_eda.py
    analysis/iteration_v1-035/trend_scanning_label_distribution.csv
  Sections 1.2-1.4 cite IS-only numbers from committed CSV:
  - Label distribution table: n_cand, TS ±1 pct, TB ±1 pct (fixed σ_t comparison), mean
    weights, horizon-share, sign-agreement per symbol (5 symbols × 8 columns).
  - Sign-agreement 64-76% across symbols — direct evidence of different supervised target.
  - Horizon share ~47-49% h=21 (dominant), ~22-24% h=13, ~28% h=5/8.
  - Weight-scale shift: TS mean ~1.8-2.6% vs TB mean ~8.4-8.5% (3.3-4.6× smaller).
  OOS data NOT inspected during Phases 1-5 (Section 10.4 confirms OOS_CUTOFF_MS gate).
  Category-matching NOT used; concrete numbers present. PASS

- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS
  HIGH-RISK declared explicitly. Reason: label-mode change shifts training-objective domain
  (path-dependent binary → regression-significance label; per-row weight distribution 3.3-4.6×
  smaller scale shift). Mitigation: F-AXIS #5 informational + F-AXIS #3 sign-agreement +
  pre-flight assert + multi-seed CONFIRMATION at /044 if PROMISING. Single-seed OPT-OUT
  per cycle-5 EXPLORATION standard acknowledged. PASS

- Section 3 (Proposed Changes): PASS
  2 atomic edits enumerated with file paths and LOC estimates:
  (1) EDIT `run_baseline_v1.py`: CLI flag `--label-mode` + `run_model()` kwarg + dispatch
      branch for v1-035 + dispatch banner + exclusion-tuple add at line 3492.
  (2) CONFIRM `lgbm.py` already supports the kwarg (no edit needed; audited at Section 1.0).
  LM Master responses: USER-DIRECTIVE-WAIVED (no advisory existed). PASS

- Section 4 (Expected OOS Impact / Verdict Matrix): PASS
  8-row verdict matrix maps F1 OOS Δ bands × F-AXIS #3/#4/#5/#6 conditions to explicit
  verdict cells: PROMISING-CLEAN / PROMISING / PROMISING-BASIN-RELOCATION-ARTIFACT /
  INERT / NEGATIVE-no-effect / NEGATIVE-CATASTROPHIC / TECHNICAL-FAILURE-LABEL-DISPATCH /
  TECHNICAL-FAILURE-SILENT-FALLBACK. Each row has explicit numerical bands. Pre-committed
  before backtest. PASS

- Section 5 (Risk Mitigation): PASS
  4-row risk table: R1 (unchanged, independent of label-mode), R2 (unchanged, Model E),
  R3 (unchanged, feature set unchanged so OOD subspace identical), HORIZON-GUARD
  (DESIGN-ONLY, deferred to /044 if PROMISING). PASS

- Section 6 (Risk Management Design): PASS
  6-row risk management table with likelihood, severity, mitigation columns covering:
  label_mode threading failure, catch-all silent-fallback, look-ahead in trend-scanning
  forward window (NONE confirmed), single-seed basin lottery, weight-scale mismatch,
  selected-horizon degenerate, forming-candle leak. IS-calibrated thresholds referenced
  as UNCHANGED. PASS

- Section 7 (Pre-registered Failure Modes, v1): PASS
  Section 7 as Failure-mode Prediction provides behavioral-effect predictor per
  `feedback_v3_axis_saturation_predictor.md` mandate:
  - IS trade count change predicted: -5% to +20% from 621 baseline (range [560, 740])
  - OOS trade count change predicted: ±25% from 189 baseline (range [140, 240])
  - Basin-shift F-AXIS #5 cross-seed Spearman: >0.50 modal prediction
  - Per-symbol OOS Δ direction predicted per symbol (§1.4 table)
  - Sign-agreement at runtime: 64-76% ±5pp tolerance [60%, 81%]
  Explicit FALSIFIER for 3 technical-failure triggers (sign-agreement outside [50%, 90%],
  trade count IS < 350 or OOS < 100, LINK OOS Δ < +0.10 AND F1 ≤ 0). Forward-looking. PASS

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria, v1): PASS
  Section 8 provides explicit numerical decision tree (Python pseudo-code):
    IF sign-agreement F-AXIS #3 ∉ [50%, 90%]: TECHNICAL-FAILURE-LABEL-DISPATCH
    ELIF OOS trades < 100 OR IS trades < 350: TECHNICAL-FAILURE-SILENT-FALLBACK
    ELIF OOS Δ ≥ +0.20 AND IS Δ ≥ +0.10 AND OOS trades ∈ [120, 260] AND ≥3/5 syms +OOS
         (LINK MUST BE +): EXPLORATION-PROMISING [or PROMISING-CLEAN if Δ ≥ +0.50]
    ELIF OOS Δ ∈ [-0.15, +0.20]: EXPLORATION-INERT
    ELIF OOS Δ < -0.15: EXPLORATION-NEGATIVE (band per F1 table)
  Pre-committed before backtest. Eliminates post-hoc rationalization. PASS

- Section 9 (Library Stack, v1): PASS
  Libraries declared: numpy (OLS/t-stat math), pandas (DataFrame ops), lightgbm (UNCHANGED),
  optuna (UNCHANGED), pyarrow (UNCHANGED), scipy.stats (EDA only, NOT runtime).
  No new dependencies required. mlfinlab/mlfinpy/fracdiff: NOT used. PASS

- Section 10 (Symbol Exclusion + Reproducibility + Test Suite Mandate):
  Section 10.1 (Symbol Exclusion): PASS — V1_BASELINE_UNIVERSE unchanged (BTC/ETH/LINK/
    LTC/DOT). V1_EXCLUDED_SYMBOLS unchanged. PASS
  Section 10.2 (Reproducibility): PASS — OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED;
    training_months = 24 UNCHANGED; outer seed = 42; ENSEMBLE_SIZE = 3 inner seeds
    (42, 123, 456); n_trials = 18; trend_scan_grid = (5, 8, 13, 21) default;
    walk-forward embargo via walk_forward.py:113 fix confirmed. PASS
  Section 10.3 (Test Suite Mandate, 9 tests): PASS — All 9 tests enumerated with names.
    MANDATORY items verified (per mission brief + /030 LESSON):
    - BASELINE CATCH-ALL EXCLUSION: test_v1_035_in_baseline_catchall_exclusion (test 6) ✓
    - DISPATCH BANNER: test_v1_035_dispatch_banner_emitted (test 4) ✓
    - PRE-FLIGHT ASSERT (mismatch case): test_v1_035_dispatch_branch_pre_flight_assert (test 5) ✓
    - label_mode threaded to LightGbmStrategy (real instance per /027 LESSON):
      test_v1_035_run_model_threads_label_mode (test 3) ✓
    - label_mode=trend_scanning CLI wiring: test_v1_035_label_mode_cli_flag_parses (test 1) ✓
    - label_mode=triple_barrier preserves baseline: test_v1_035_label_mode_default_unchanged (test 2) ✓
    - trend_scan_grid default pass-through: test_v1_035_trend_scan_grid_default (test 8) ✓
    - dispatch branch existence: test_v1_035_dispatch_branch_exists (test 7) ✓
    - label_mode isolation (no leak to catch-all): test_v1_035_label_mode_does_not_leak_outside_dispatch (test 9) ✓
  Section 10.4 (Anti-cheating): PASS — OOS_CUTOFF_MS = 1742774400000 used in EDA;
    IS-only window confirmed; OOS NOT inspected during Phases 1-5. PASS

OVERALL CHECK 1: PASS

### Check 2 — Numerical Evidence
analysis/iteration_v1-035/ directory exists with 2 committed files at HEAD `7166ad1`:
  trend_scanning_eda.py + trend_scanning_label_distribution.csv
Sections 1.2-1.4 cite IS-only numbers from committed CSV. 5-symbol table with 8 columns
per symbol (n_cand, TS ±1%, TB ±1%, TS weight mean, TB weight mean, horizon shares, sign-agreement).
Category-matching NOT used; concrete numbers present. No OOS data contamination detected.
EDA script line 64 confirms `master[master["open_time"] < OOS_CUTOFF_MS]` gate. PASS

### Check 3 — LM Master Integration
USER-DIRECTIVE-WAIVED. Phase 4.5 skipped per explicit user directive (mirrors /033+/034 precedent).
No lgbm_advisor.md exists; no Section 3 responses required. Non-blocking per directive. PASS

### Check 4 — Axis Rotation Discipline
`labeling` last used at /014 (EWMA σ_t, ~21 EXPLORATIONs ago). Prior 5 EXPLORATIONs span
3 distinct families (meta-labeling/1, sample-weighting/2, confirmation-bundle/1, feature-family/1).
Monoculture threshold (5 consecutive same-family) NOT reached. VALID. PASS

### Check 5 — HIGH-RISK Declaration
HIGH-RISK declared explicitly. Label-mode change = training-objective domain change:
- path-dependent binary TP/SL-first-hit → regression-significance OLS label (Wald t-stat)
- per-row sample weight distribution 3.3-4.6× scale shift (TB ~8.5% modal → TS ~2.5% modal)
- tighter weight distribution (std 1.0-1.3 vs 2.0-2.2) changes LightGBM loss surface.
Mitigation declared: F-AXIS #5 informational + F-AXIS #3 sign-agreement check + pre-flight
assert + multi-seed CONFIRMATION mandate if PROMISING. Single-seed OPT-OUT for cycle-5
EXPLORATION per `feedback_axis_saturation_predictor.md`. PASS

### Check 6 — Falsifier Pre-Registration (F-AXIS #1-#6)
F-AXIS #1: OOS Δ bands: ≥+0.50 PROMISING-CLEAN / [+0.20, +0.50) PROMISING /
  [-0.15, +0.20) INERT (wider than feature-add ±0.10 — justified for HIGH-RISK labeling)
  / [-0.40, -0.15) NEGATIVE / <-0.40 NEG-CAT. PASS
F-AXIS #2: IS [430, 800] (±30%) / OOS [120, 260] (±35%). TECHNICAL-FAILURE-SILENT-FALLBACK
  at IS < 350 OR OOS < 100. PASS
F-AXIS #3: Sign-agreement runtime check [60%, 81%] tolerance band. <50% or >90% →
  TECHNICAL-FAILURE-LABEL-DISPATCH. Enforces label-dispatch correctness. PASS
F-AXIS #4: Per-symbol OOS Δ direction prediction table (LINK + highest; ETH +; LTC + mild;
  DOT mixed; BTC flat). Falsifier: 4/5 syms NEGATIVE AND LINK NEGATIVE → mechanism REFUTED. PASS
F-AXIS #5: Cross-seed best-learning_rate Spearman >0.50 → basin-stable; <0.30 → basin-relocated
  (informational at single-seed EXPLORATION). PASS
F-AXIS #6: Horizon distribution sanity [40%, 60%] for h=21 expected. >70% or >20% h=5 →
  degenerate basin (informational at EXPLORATION budget). PASS
All 6 falsifiers present with explicit bands. PASS

### Check 7 — Test Mandate
Section 10.3 lists 9 tests (exceeds 8-test minimum in mission brief). All MANDATORY
items from mission brief present:
- BASELINE CATCH-ALL EXCLUSION per /030 LESSON: test_v1_035_in_baseline_catchall_exclusion ✓
- DISPATCH BANNER: test_v1_035_dispatch_banner_emitted ✓
- PRE-FLIGHT ASSERT against mismatch (triple_barrier + v1-035 → AssertionError): test_v1_035_dispatch_branch_pre_flight_assert ✓
- label_mode threaded to real LightGbmStrategy instance per /027 LESSON: test_v1_035_run_model_threads_label_mode ✓
- label_mode=trend_scanning CLI flag: test_v1_035_label_mode_cli_flag_parses ✓
- trend_scan_grid default pass-through: test_v1_035_trend_scan_grid_default ✓
- dispatch branch existence: test_v1_035_dispatch_branch_exists ✓
- label_mode isolation (catch-all does NOT receive label_mode kwarg): test_v1_035_label_mode_does_not_leak_outside_dispatch ✓
- label_mode default unchanged (triple_barrier): test_v1_035_label_mode_default_unchanged ✓
Existing 8 trend-scanning tests at tests/strategies/ml/test_trend_scanning_label_mode.py
must also pass. PASS

### Check 8 — Cadence Position
TYPE: EXPLORATION — cadence position is cycle-5 EXP 2/10. Cycle-5 started at /034
(EXP 1 NEGATIVE-LEARNED-NEG). /035 is EXP 2. No CONFIRMATION precedent count gate
applies for EXPLORATION type. PASS

### Check 9 — No OOS Leakage in Design
Section 10.4 explicit anti-cheating self-check: OOS_CUTOFF_MS = 1742774400000 confirmed
in EDA script at line 64. All EDA uses IS-only window. Section 2 (Falsifiers) pre-committed
before backtest. Section 8 (MERGE/NO-MERGE decision tree) pre-committed before backtest.
`_trend_scan_label` reads only close_arr[pos+1..pos+max_h] — strictly forward bars.
Hard-causality test at tests/strategies/ml/test_trend_scanning_label_mode.py proves
forward-only access. PASS

### Check 10 — CONFIRMATION Precedent Count
N/A — TYPE is EXPLORATION, not CONFIRMATION. No precedent count gate required. PASS

### Check 11 — Reproducibility Section
Section 10.2: outer seed = 42; ENSEMBLE_SIZE = 3 (V1_EXPLORATION_ENSEMBLE_SIZE);
n_trials = 18; label_mode = trend_scanning; trend_scan_grid = (5, 8, 13, 21);
sample_weight_mode = abs_pnl (baseline default).
OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED. training_months = 24 UNCHANGED.
Walk-forward embargo at walk_forward.py:113 confirmed. V1_FEATURE_COLUMNS_PRUNED 43 cols
UNCHANGED (no new feature columns required for trend-scanning). PASS

### Check 12 — Wall-clock Estimate (5-step label-rate scaling)
Section 3.6 provides full 5-step scaling:
Step 1: iter-v1/034 anchor ~55 min (closest comparable: n_trials=18, ES=3, 5 syms, 43 cols)
Step 2: Baseline label count ~621 IS / 189 OOS trades
Step 3: TS label generation cost ~1.0× triple-barrier (constant-time per bar, 4 horizons)
Step 4: (3/3) × (18/18) × (1/1) × (43/43) × 1.0 label-gen = 1.0×
Step 5: 55 min × 1.0 = 55 min modal compute + 0 min feature-regen + 3 min report = ~58 min
Modal total ~60 min. Conservative band 50-100 min. INSIDE 1.8h target. PASS

### Check 13 — Library Stack (Section 9) + Anti-pattern Scan
Library stack (Section 9): numpy + pandas + lightgbm + optuna + pyarrow declared.
scipy.stats for EDA only (already in deps). No new runtime libraries. mlfinlab/mlfinpy/
fracdiff: NOT used. PASS

One primary variable changed: label_mode (triple_barrier → trend_scanning).
No other axis changes: features UNCHANGED (43 cols V1_FEATURE_COLUMNS_PRUNED),
universe UNCHANGED (V1_BASELINE_UNIVERSE), model architecture UNCHANGED (4 models A/C/D/E),
risk-primitive UNCHANGED (R1/R2/R3 per-model baseline), sample-weight mode UNCHANGED
(abs_pnl default). Execution-side TP/SL barriers remain ATR-driven. ONE primary variable. PASS

---

## Summary

All 13 checks PASS. LM Master Phase 4.5 waived by user directive (mirrors /033+/034 precedent).
HIGH-RISK declared (label-mode change = training-objective domain change; single-seed OPT-OUT
per cycle-5 EXPLORATION standard; multi-seed CONFIRMATION at /044 mandatory if PROMISING).
Axis family `labeling` rotation VALID (last at /014 ~21 EXPLORATIONs ago; 5 prior slots span
3 distinct families). Analysis scripts committed at `7166ad1` (2 files: EDA script + distribution
CSV). 9 tests in mandate — all mandatory items present (catch-all exclusion + banner +
pre-flight assert mismatch + REAL-LightGbmStrategy instance thread discipline + CLI flag +
trend_scan_grid pass-through + branch existence + isolation + default preservation).
Wall-clock ~60 min modal, inside 1.8h EXPLORATION target.

OVERALL: PASS

Phase 6.0 Critic pre-flight dispatch is authorized.
