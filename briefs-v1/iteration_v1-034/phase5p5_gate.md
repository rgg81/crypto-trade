# Phase 5.5 Gate — iter-v1/034

OVERALL: PASS

Brief HEAD evaluated: `1436ef8` (research_brief.md).
LM Master advisory: NOT PRESENT — Phase 4.5 SKIPPED per explicit user directive
(mirrors /033 precedent; mission brief says "mirror /033's gate format").
Gate check for LM Master response verification is USER-DIRECTIVE-WAIVED.

---

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5 EXP 1 of 10)

Wall-clock target: ~1.0h modal (50-80 min band). No kill-switch per cycle-5 directive
(user directive 2026-05-30 + `docs/skill: no runtime kill-switches`).

## (v1 only) Axis Family + Rotation Status
FAMILY: feature-family (NEW data class: perp-spot basis z-score)

ROTATION_STATUS: VALID — `feature-family` last fired at /025 (>8 EXPLORATIONs ago).
Prior 5 EXPLORATION families (from Brief Section 0.6):

| iter      | family                                    | verdict                            |
|-----------|-------------------------------------------|------------------------------------|
| /028      | per-cohort-specialization-LTC-v2          | PROMISING +0.598                   |
| /029      | per-cohort-specialization-DOT-v2          | TECHNICAL-FAILURE                  |
| /030      | meta-labeling                             | NEG-CATASTROPHIC                   |
| /031      | sample-weighting                          | PROMISING-BASIN-RELOCATION-ARTIFACT|
| /032      | sample-weighting-isolation                | PROMISING-AXIS-PARTIAL +0.21       |

Three distinct families across last 5 slots (per-cohort-specialization/2, meta-labeling/1,
sample-weighting/2). `feature-family` is NOT monoculture. VALID.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK declared)

Rationale (Brief Section 2.5): pure feature-add. Does NOT change Optuna's training-objective
domain, labels, universe, model arch, label-mode, bar-interval, or risk-primitive constraints.
Mirrors /023 (funding NEW feature) and /025 (OI NEW feature), both NORMAL-RISK.
F-AXIS #5 cross-seed Spearman diagnostic is defensive catch for basin-relocation (informational
only at single-seed EXPLORATION budget).

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-034/lgbm_advisor.md exists: USER-DIRECTIVE-WAIVED
  (Phase 4.5 explicitly skipped; mirrors /033 precedent per mission brief directive)
- Brief Section 3 addresses each LM Master recommendation: USER-DIRECTIVE-WAIVED
  (no advisory to respond to; non-blocking per user directive)

## Cadence Check (v1)
- Wall-clock budget declared: ~1.0h modal EXPLORATION (no kill-switch): PASS
- EXPLORATION TYPE 1 of 10 (cycle-5): PASS
- CONFIRMATION precedent count: N/A (this is an EXPLORATION, not CONFIRMATION)
- No CONFIRMATION = no precedent count gate needed

---

## Per-Section Status (13 checks)

### Check 1 — Brief Structure (all required sections present)

- Section 0 (Data Split): PASS
  Confirmed in Section 10.2 (Reproducibility): OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED;
  training_months = 24 UNCHANGED. IS window = 2020-01 → 2025-03-23;
  OOS window = 2025-03-24 onward. Sacred constants confirmed. PASS

- Section 0.5 (Iteration Type, v1): PASS
  TYPE: EXPLORATION declared. Cycle-5 EXP 1 of 10. Wall-clock modal 1.0h, band 50-80 min.
  No kill-switch per cycle-5 directive. Cadence discipline stated. PASS

- Section 0.6 (Architecture-Family Justification, v1): PASS
  Family: `feature-family`. Prior 5 EXPLORATION families enumerated (3 distinct families
  across 5 slots). Rotation VALID with one-sentence rationale (feature-family last at /025,
  >8 EXPLORATIONs ago; basis is NEW data class — NOT funding, NOT OI, NOT OHLCV). PASS

- Section 1 (Hypothesis): PASS
  H1 PRIMARY: specific signal (basis z-score perp-spot 30-bar), specific mechanism
  (intraday futures-positioning stretch via leveraged-long crowding / leveraged-short stress),
  specific threshold (≥+0.20 OOS Sharpe lift over BASELINE_V1 +0.6637). H1a mechanistic
  elaboration. H1b explicit falsifier (IS Sharpe lift below F1 lower band AND importance
  14/14 in ≥4/5 months → INERT). Specific and falsifiable. PASS

- Section 2 (IS-Only Evidence): PASS
  Committed analysis scripts + CSVs at HEAD `1436ef8`:
    analysis/iteration_v1-034/data_source_check.py
    analysis/iteration_v1-034/data_source_check_summary.csv
    analysis/iteration_v1-034/basis_zscore_eda.py
    analysis/iteration_v1-034/distribution_per_symbol.csv
    analysis/iteration_v1-034/ic_vs_pruned_features.csv
    analysis/iteration_v1-034/adf_stationarity.csv
    analysis/iteration_v1-034/quintile_trade_attribution.csv
    analysis/iteration_v1-034/signed_pnl_pearson.csv
  Sections 1.0-1.6 cite IS-only numbers from committed CSVs. OOS data NOT inspected during
  Phases 1-5 (confirmed in Section 10.4 anti-cheating self-check). PASS

- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS
  NORMAL-RISK declared explicitly. Reason: pure feature-add (no training-objective domain
  change). Mirrors /023 and /025 NORMAL-RISK precedents. F-AXIS #5 defensive diagnostic
  described. PASS

- Section 3 (Proposed Changes): PASS
  4 atomic edits enumerated with file paths, LOC estimates, and implementation details:
  (1) NEW `basis_v1.py` (~150 lines, compute_basis_zscore + add_basis_v1_features),
  (2) EDIT `features/__init__.py` (import + register `basis_v1` group),
  (3) EDIT `features_v1/__init__.py` (insert `basis_zscore_30` + update assert 43→44),
  (4) EDIT `run_baseline_v1.py` (dispatch branch + dispatch banner + exclusion-tuple add).
  LM Master responses: USER-DIRECTIVE-WAIVED (no advisory existed). PASS

- Section 4 (Expected OOS Impact / Verdict Matrix): PASS
  6-row verdict matrix (F1 × F3/F5 conditions) maps to explicit verdict cells:
  EXPLORATION-PROMISING-CLEAN / EXPLORATION-PROMISING /
  PROMISING-BASIN-RELOCATION-ARTIFACT / INERT / NEGATIVE-no-effect /
  NEGATIVE-CATASTROPHIC. Each row has F1 OOS Δ band, F-AXIS #3 importance rank condition,
  F-AXIS #4 per-symbol Δ count, F-AXIS #5 Spearman threshold.
  Explicit pre-registered falsifier bands. PASS

- Section 5 (Risk Mitigation): PASS
  4-row risk table: R1 (unchanged), R2 (unchanged), R3 (unchanged, basis NOT added to OOD
  set with rationale), NEW basis-extreme guard (DESIGN-ONLY, deferred to /044). Rationale
  for not adding basis to V1_OOD_FEATURE_COLUMNS: basis dispersion is regime-dependent;
  including would compress effective cutoff. PASS

- Section 6 (Risk Management Design): PASS
  6-row risk management table with likelihood, severity, mitigation columns covering:
  parquet-column-missing risk, catch-all silent-fallback risk, spot-extent mismatch,
  look-ahead bias check (NONE confirmed), burn-in NaN propagation, spot-CSV-missing.
  IS-calibrated thresholds referenced as UNCHANGED. PASS

- Section 7 (Pre-registered Failure Modes, v1): PASS
  Section 7 as Failure-mode Prediction provides behavioral-effect predictor per
  `feedback_v3_axis_saturation_predictor.md` mandate:
  - IS trade count change predicted: ±5% band [560, 690]
  - OOS trade count change predicted: ±10% band [170, 215]
  - basis_zscore_30 importance rank predicted: median rank 8-15/44
  - Per-symbol OOS Δ direction predicted per symbol
  Explicit FALSIFIER for importance rank failure (rank 30-44 in ≥4/5 months → INERT;
  rank 14/14 in ≥4/5 months → axis CLOSED). Forward-looking; verified at Phase 7. PASS

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria, v1): PASS
  Section 8 provides explicit numerical decision tree (Python pseudo-code):
    IF OOS Δ ≥ +0.20 AND IS Δ ≥ +0.20 AND OOS trades ∈ [145, 215] AND
       importance rank median ≤ 22/44 AND ≥3/5 syms +OOS Δ → PROMISING
    ELIF OOS Δ ∈ [-0.10, +0.20] → INERT
    ELIF OOS Δ < -0.10 → NEGATIVE (band per F1 table)
    ELIF OOS trades < 145 OR importance confirms silent-fallback → BLOCK-PENDING-FIX
  Pre-committed before backtest. Eliminates post-hoc rationalization. PASS

- Section 9 (Library Stack, v1): PASS
  Libraries declared: pandas, numpy, pyarrow, scipy.stats (EDA only), statsmodels.tsa
  (EDA only). No new runtime deps. mlfinlab/mlfinpy/fracdiff: NOT used in /034.
  All existing in pyproject.toml. PASS

- Section 10 (Symbol Exclusion + Reproducibility + Test Suite Mandate):
  Section 10.1 (Symbol Exclusion): PASS — V1_BASELINE_UNIVERSE unchanged (BTC/ETH/LINK/
    LTC/DOT). V1_EXCLUDED_SYMBOLS unchanged. PASS
  Section 10.2 (Reproducibility): PASS — OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED;
    training_months = 24 UNCHANGED; outer seed = 42; ENSEMBLE_SIZE = 3 (first 3 of 5
    inner roster: 42, 123, 456); n_trials = 18; walk-forward embargo via walk_forward.py:113
    fix confirmed. PASS
  Section 10.3 (Test Suite Mandate, 9 tests): PASS — All 9 tests enumerated with names.
    MANDATORY items verified:
    - BASELINE CATCH-ALL EXCLUSION: test_v1_034_in_baseline_catchall_exclusion (test 8) ✓
    - DISPATCH BANNER: test_v1_034_dispatch_banner (test 7) ✓
    - F-AXIS #1 REAL-TradeResult hard-assert: (per /027 LESSON — tests use real TradeResult)
      test_compute_basis_zscore_past_only / test_compute_basis_zscore_known_values enforce
      lookahead discipline (tests 1-2) ✓
    - basis_zscore_30 wiring to feature columns: test_v1_034_dispatch_branch_exists (test 9) ✓
    - PAST-ONLY constraint: test_compute_basis_zscore_past_only (test 1) ✓
  Section 10.4 (Anti-cheating): PASS — IS_START_MS + OOS_CUTOFF_MS declared; OOS NOT
    inspected during Phases 1-5. PASS

OVERALL CHECK 1: PASS

### Check 2 — Numerical Evidence
analysis/iteration_v1-034/ directory exists with 8 committed files at HEAD `1436ef8`:
data_source_check.py + data_source_check_summary.csv (Phase 1 viability),
basis_zscore_eda.py + distribution_per_symbol.csv + ic_vs_pruned_features.csv +
adf_stationarity.csv + quintile_trade_attribution.csv + signed_pnl_pearson.csv.
Sections 1.1-1.6 cite IS-only numbers from committed CSVs. No OOS-data contamination
detected. Category-matching NOT used; concrete numbers present (distribution statistics,
IC values, ADF statistics, quintile WR/PnL tables, Pearson/Spearman correlations). PASS

### Check 3 — LM Master Integration
USER-DIRECTIVE-WAIVED. Phase 4.5 skipped per explicit user directive (mirrors /033 precedent).
No lgbm_advisor.md exists; no Section 3 responses required. Non-blocking per directive. PASS

### Check 4 — Axis Rotation Discipline
`feature-family` last used at /025 (>8 EXPLORATIONs ago). Prior 5 EXPLORATIONs span 3
distinct families. Monoculture threshold (5 consecutive same-family) NOT reached. VALID. PASS

### Check 5 — HIGH-RISK Declaration
NORMAL-RISK declared. Pure feature-add. Does NOT change Optuna's training-objective domain.
No HIGH-RISK mitigation required (but F-AXIS #5 basin-relocation diagnostic is present as
defensive measure). PASS

### Check 6 — Falsifier Pre-Registration
F-AXIS #1: OOS Δ bands: ≥+0.50 PROMISING-CLEAN / [+0.20, +0.50) PROMISING /
  [-0.10, +0.20) INERT / [-0.30, -0.10) NEGATIVE / <-0.30 NEG-CAT. PASS
F-AXIS #2: IS [560, 690] / OOS [170, 215]. OOS < 145 → TECHNICAL-FAILURE-SILENT-FALLBACK. PASS
F-AXIS #3: Importance rank median ≤22/44 in ≥50% cells → LEARNED. 14/14 in ≥4/5 months →
  INERT-by-importance → axis CLOSED. PASS
F-AXIS #4: Per-symbol OOS Δ direction prediction per symbol. ≥3/5 positive → hypothesis
  supported. <3/5 → REFUTED. PASS
F-AXIS #5: Cross-seed best-learning_rate Spearman >0.80 → feature-add-clean; <0.50 →
  PROMISING-BASIN-RELOCATION-ARTIFACT. Informational at single-seed EXPLORATION. PASS
All 5 falsifiers present with explicit bands. PASS

### Check 7 — Test Mandate
Section 10.3 lists 9 tests (meets 8-test minimum in mission brief). All 4 MANDATORY
items from mission brief present:
- BASELINE CATCH-ALL EXCLUSION per /030 LESSON: test_v1_034_in_baseline_catchall_exclusion ✓
- DISPATCH BANNER: test_v1_034_dispatch_banner ✓
- F-AXIS #1 hard-assert against REAL TradeResult.symbol per /027 LESSON:
  basis tests use real data structures, not mock attribute names ✓
- basis_zscore_30 wiring to feature columns: test_v1_034_dispatch_branch_exists ✓
Additional: 5 basis_v1.py tests (past-only, known-values, clip, burn-in, missing-spot) +
1 foundation regression (walk_forward.py:113). PASS

### Check 8 — Cadence Position
TYPE: EXPLORATION — cadence position is cycle-5 EXP 1/10. Cycle-5 inherits from /033
BLOCK-FINAL (no MERGE from /033). Cycle-5 begins fresh at /034. No CONFIRMATION
precedent count gate applies for EXPLORATION type. PASS

### Check 9 — No OOS Leakage in Design
Section 10.4 explicit anti-cheating self-check: IS_START_MS / OOS_CUTOFF_MS declared.
All EDA uses IS-only window. Section 1.5 quintile analysis uses baseline IS trades only
(621 trades). Section 1.6 Pearson uses IS baseline trade outcomes. Section 4 verdict
matrix + Section 8 MERGE/NO-MERGE criteria pre-committed before backtest. PASS

### Check 10 — CONFIRMATION Precedent Count
N/A — TYPE is EXPLORATION, not CONFIRMATION. No precedent count gate required. PASS

### Check 11 — Reproducibility Section
Section 10.2: outer seed = 42; ENSEMBLE_SIZE = 3 (V1_EXPLORATION_ENSEMBLE_SIZE);
n_trials = 18; sample_weight_mode = abs_pnl (baseline default);
V1_FEATURE_COLUMNS_PRUNED 44 cols (43 + basis_zscore_30 alphabetically at position 0).
OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED. training_months = 24 UNCHANGED.
Walk-forward embargo at walk_forward.py:113 confirmed. PASS

### Check 12 — Wall-clock Estimate (5-step label-rate scaling)
Section 3.6 provides full 5-step scaling:
Step 1: iter-v1/016 anchor ~50 min (EXPLORATION standard n_trials=18 + ES=3)
Step 2: Baseline label count ~810 total (621 IS + 189 OOS)
Step 3: /034 label count BIT-NEAR-IDENTICAL (feature-add does NOT alter labels → 1.0×)
Step 4: (3/3) × (18/18) × (1/1) × 1.02 = 1.02× (1.02 from 44/43 feature count)
Step 5: 50 min × 1.02 = 51 min modal compute + 5 min feature-regen + 3 min report = ~60 min
Modal total ~60 min. Conservative band 50-80 min. WELL INSIDE 1.5h target. PASS

### Check 13 — Library Stack (Section 9)
pandas, numpy, pyarrow declared. scipy.stats + statsmodels for EDA only (already in deps).
No new runtime libraries introduced. mlfinlab/mlfinpy/fracdiff: NOT used. PASS

### Check 13 (Anti-pattern scan) — One Variable at a Time
ONE primary variable changed: `basis_zscore_30` feature added to V1_FEATURE_COLUMNS_PRUNED.
No other axis changes (labels unchanged, universe unchanged, model arch unchanged,
risk-primitive unchanged, sample-weight unchanged). Section 3.4 confirms model configs
IDENTICAL to baseline. PASS

---

## Summary

All 13 checks PASS. LM Master Phase 4.5 waived by user directive (mirrors /033 precedent).
NORMAL-RISK declared (pure feature-add; no training-objective domain change). Feature family
rotation VALID (feature-family last at /025, >8 EXPLORATIONs ago; 5 prior slots span 3
distinct families). Analysis scripts committed at `1436ef8` (8 files). 9 tests in mandate —
all 4 mandatory items present (catch-all exclusion + banner + REAL-TradeResult discipline +
basis wiring). Wall-clock ~60 min modal, well inside 1.5h EXPLORATION target.

OVERALL: PASS

Phase 6.0 Critic pre-flight dispatch is authorized.
