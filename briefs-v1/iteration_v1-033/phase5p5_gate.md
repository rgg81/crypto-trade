# Phase 5.5 Gate — iter-v1/033

OVERALL: PASS

Brief HEAD evaluated: `c075457` (research_brief.md).
LM Master advisory: NOT PRESENT — Phase 4.5 SKIPPED per explicit user directive (2026-05-29
"Let's go A"). Gate check for LM Master response verification is USER-DIRECTIVE-WAIVED.

---

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION (cycle-4 first CONFIRMATION since /027 TF)

CONFIRMATION-EXCEPTION declared for wall-clock: 12h hard cap / 10h kill-switch.
Budget: `--seeds 1` outer × `ENSEMBLE_SIZE=10` inner × `n_trials=35`.
Modal wall-clock projection ~9-10h. User directive 2026-05-29 ("Let's go A") explicitly
authorizes breach of 6h skill default. Non-blocking.

## (v1 only) Axis Family + Rotation Status
FAMILY: confirmation-bundle (CONFIRMATION — exempt from Axis Rotation Discipline per
quant-iteration-v1 skill §"Axis Rotation Discipline"; CONFIRMATIONs bundle PROMISING
ingredients across multiple families, not single-axis EXPLORATIONs)

ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (per Brief Section 0.6):
| iter      | family                                | verdict                       |
|-----------|---------------------------------------|-------------------------------|
| /028      | per-cohort-specialization-LTC-v2      | PROMISING +0.598              |
| /029      | per-cohort-specialization-DOT-v2      | TECHNICAL-FAILURE             |
| /030      | meta-labeling                         | NEG-CATASTROPHIC              |
| /031      | sample-weighting                      | PROMISING-BASIN-RELOCATION-ARTIFACT (closure REVOKED by /032) |
| /032      | sample-weighting-isolation            | PROMISING-AXIS-PARTIAL +0.21  |

Three distinct families across last 5 slots. confirmation-bundle is not on the
rotation-restricted list. VALID.

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: YES

Rationale (Brief Section 2.5): Option B stacks 4 axis changes that each change Optuna's
training-objective domain:
  1. Pool A composition — BTC+ETH → BTC-only via Model G replacement
  2. Label space — LTC atr_sl=1.0 narrows triple-barrier window
  3. Training loss surface — composite_inv_concurrency reshapes weight distribution
  4. Per-symbol model dispatch — Model C' / D' / G replace baseline equivalents

Mitigation: CONFIRMATION-standard at `--seeds 1` outer × `ENSEMBLE_SIZE=10` inner ×
`n_trials=35` per `V1_CONFIRMATION_ENSEMBLE_SIZE = 10`. Brief Section 2.5 cites
`feedback_v1_seed_count_non_negotiable.md` — CONFIRMATION = 10 inner seeds always.
/033 ALIGNS with spec. HIGH-RISK mitigation = full inner-ensemble width at CONFIRMATION.

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-033/lgbm_advisor.md exists: USER-DIRECTIVE-WAIVED
  (Phase 4.5 explicitly skipped per user directive 2026-05-29 "Let's go A")
- Brief Section 3 addresses each LM Master recommendation: USER-DIRECTIVE-WAIVED
  (no advisory to respond to; Brief Section 3.4 contains 10 open questions
  which the QR acknowledges will not be answered pre-run; non-blocking per directive)

## Cadence Check (v1)
- Wall-clock budget declared: CONFIRMATION-EXCEPTION 12h hard cap, 10h kill-switch: PASS
- CONFIRMATION precedent count (cumulative EXPLORATIONs across cycles 3+4):
  Cycle-3: /016-/025 = 10 EXPLORATIONs
  Cycle-4: /028 PROMISING + /029 TF + /030 NEG-CAT + /031 PROMISING-BRA + /032 PROMISING-AP = 5
  TOTAL = 15 EXPLORATION precedents. Brief declares 16 (includes /026 sanity slot).
  Skill requires ≥10. 15 (conservative count) SATISFIES the 10:1 rule: PASS
  Exception rationale: cycle-3 produced 10 EXPLORATIONs + /027 CONFIRMATION-TF consumed
  cycle-3 CONFIRMATION slot without verdict. Cycle-4 inherits cycle-3 substrate (/018 LINK +
  /019 ETH+gate carried forward as PROMISING). 16:1 ratio across cycle pair sharing substrate
  satisfies 10:1 per brief Section 0.5 reasoning. PASS
- CONFIRMATION Section 3 lists imported variations from prior EXPLORATIONs: PASS
  Brief Section 3.1 architecture table explicitly assigns: /018 → Model C' LINK specialist,
  /019 → Model G ETH+BTC-gate, /028 → Model D' LTC atr_sl=1.0, /031//032 → composite_inv_
  concurrency wrapper on all models. Traceability from prior EXPLORATIONs to bundle components
  is explicit. PASS

---

## Per-Section Status (13 checks)

### Check 1 — Brief Structure (all required sections present)

- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 confirmed in Section 10.2
  (Reproducibility). IS window = 24 months before 2025-03-24; OOS window = 2025-03-24 onward.
  Same format accepted at /031 gate. Non-blocking.

- Section 0.5 (Iteration Type, v1): PASS
  TYPE: CONFIRMATION explicitly declared. CONFIRMATION-EXCEPTION wall-clock declared with
  rationale (ENSEMBLE_SIZE=10 inner is CONFIRMATION standard; user directive authorizes 12h cap;
  5-step wall-clock scaling produces 9.8h modal). PASS

- Section 0.6 (Architecture-Family Justification, v1): PASS
  Family: confirmation-bundle. Prior 5 EXPLORATION families enumerated. Rotation status VALID
  with rationale. One-sentence axis justification: 4 PROMISING ingredients from 3 distinct
  families across cycles 3+4. PASS

- Section 1 (Hypothesis): PASS
  H1 (PRIMARY): specific mechanism (4 PROMISING bundle + composite_inv_concurrency), specific
  threshold (+1.0 OOS Sharpe hard merge floor), specific config (--seeds 1 × ES=10 × n_trials=35),
  specific falsifier (H3 REFUTED if +0.21 axis-only lift dissolves). Three falsifiable hypotheses
  H1/H1a/H2/H3. Specific and falsifiable. PASS

- Section 2 (IS-Only Evidence): PASS
  Committed analysis scripts + CSVs at `f433f6b`:
    analysis/iteration_v1-033/bundle_eda.py
    analysis/iteration_v1-033/specialist_pairwise_corr.csv
    analysis/iteration_v1-033/bundle_sharpe_projection.csv
    analysis/iteration_v1-033/specialist_per_symbol_pnl.csv
    + 5 additional CSVs
  Sections 1.1-1.4 cite IS-sourced numbers from committed CSVs. Per-symbol OOS attribution
  (Section 1.2) correctly sources from single-seed EXPLORATION reports, not from OOS inference.
  Pairwise correlation (Section 1.3) sourced from committed specialist_pairwise_corr.csv.
  Bundle Sharpe projection (Section 1.4) committed in bundle_sharpe_projection.csv. PASS

- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS
  HIGH-RISK declared with four specific reasons (pool composition, label space, loss surface,
  dispatch architecture). Mitigation path through CONFIRMATION-standard 10 inner seeds cited.
  `feedback_v1_seed_count_non_negotiable.md` referenced. PASS

- Section 3 (Proposed Changes): PASS
  Section 3.1 architecture table: 5-model architecture with explicit symbol routing, TP/SL
  params, R-gate configuration, sample weight mode per model. Enumerated changes clear.
  LM Master responses: USER-DIRECTIVE-WAIVED (no advisory existed). Section 3.3 implementation
  specifics: per-symbol dispatch routing, BTC-trend gate config, atr_sl=1.0 upstream label
  shift, composite_inv_concurrency formula + mean-normalization, mandatory hard-asserts with
  lessons from /027. All proposed changes enumerated. PASS

- Section 4 (Expected OOS Impact / Verdict Matrix): PASS
  7-row verdict matrix with F1/F2/F3/F4/F5 conditions per row. Each row maps to explicit
  verdict cell: CONFIRMATION-MERGE / CONFIRMATION-PARTIAL / CONFIRMATION-INERT /
  CONFIRMATION-NEGATIVE / BLOCK-PENDING-FIX / BLOCK-FINAL. Explicit falsifier in F1 with
  OOS Δ = +0.336 threshold above baseline +0.6637. Pre-registered before backtest. PASS

- Section 5 (Risk Mitigation): PASS
  6-row risk table with likelihood, mitigation per risk. Pool-A collapse, LTC interaction,
  multi-seed lottery, wall-clock breach, /027-style defect, n_eff collapse all enumerated
  with explicit mitigations. PASS

- Section 6 (Risk Management Design): PASS
  4-gate table: R1 (Models C'/D'/G/E), R2 (Model E only), R3 (all models), sample-weighting
  (all models). IS-calibrated thresholds confirmed UNCHANGED from baseline for R1/R2/R3.
  Concentration cap exception declared with explicit rationale (60% relaxation from 30% strict).
  PASS

- Section 7 (Pre-registered Failure Modes, v1): PASS
  5 pre-registered failure mechanisms with mechanism signatures:
  1. POOL-A-COLLAPSE (F3 BTC negative + n_eff < 8 + IS BTC trades > 100)
  2. LTC-INTERACTION-NEGATIVE (F3 LTC negative + OOS LTC trades < 30)
  3. SPECIALIST-CANNIBALIZATION (F2 OOS trades < 600 + F3 multiple marginal)
  4. SAMPLE-WEIGHTING-DISSOLVES (F4 n_eff ≥ 20 + F1 ≈ baseline)
  5. BASIN-LOTTERY-DOMINATES (F1 outside [-0.10, +0.40] + per-seed Sharpe std > 0.40)
  Forward-looking; each has metric signatures for Phase 7 verification. PASS

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria, v1): PASS
  Section 8 (Verdict-Cell Determination Mechanics) provides explicit table mapping each
  falsifier (F1-F5 + Hard Gates) to report artifact (comparison.csv row, per_symbol.csv,
  trades.csv column). Pre-committed numerical thresholds locked before backtest.
  Section 4 verdict matrix provides the 7-row MERGE/NO-MERGE decision grid. PASS

- Section 9 (Library Stack, v1): PASS
  Brief Section 9: lightgbm ≥ 4.0, optuna, pandas, numpy, scipy.stats, statsmodels listed.
  mlfinlab/mlfinpy: brief notes "mlfinlab==1.4 (or mlfinpy MIT fallback)" — fallback declared.
  fracdiff ≥ 0.10 listed as not used in /033. NO new library introduced. PASS

- Section 10 (Symbol Exclusion + Reproducibility + Test Suite Mandate):
  Section 10.1 (Symbol Exclusion): PASS — V1_EXCLUDED_SYMBOLS unchanged (8 symbols);
    V1_BASELINE_UNIVERSE 5-symbol unchanged.
  Section 10.2 (Reproducibility): PASS — OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED;
    training_months = 24 UNCHANGED; inner seeds = first 10 of canonical roster;
    outer seed = 42; n_trials = 35; walk-forward embargo discipline confirmed.
  Section 10.3 (Test Suite Mandate, 14 tests): PASS — all 14 tests enumerated with
    specific test names. MANDATORY items verified:
    - BASELINE CATCH-ALL EXCLUSION: test_bundle_iter33_catchall_exclusion (test 7) ✓
    - DISPATCH BANNER: test_bundle_iter33_dispatch_banner_print (test 13) ✓
    - F-AXIS #1 REAL-TradeResult hard-assert: test_bundle_iter33_real_trade_result_assertion
      (test 8) uses trade.symbol NOT trade.model_name per /027 LESSON ✓
    - Per-model sample weight wiring: test_bundle_iter33_sample_weight_composite_inv_
      concurrency_active (test 11) ✓

OVERALL CHECK 1: PASS

### Check 2 — Numerical Evidence
analysis/iteration_v1-033/ directory exists with committed scripts and CSVs at `f433f6b`.
bundle_eda.py + specialist_pairwise_corr.csv + bundle_sharpe_projection.csv + 5 other CSVs
confirmed present. Sections 1.1-1.4 cite IS-only numbers from committed artifacts.
OOS attribution in Section 1.2 sourced from prior single-seed EXPLORATION reports, not
forward-looking OOS inference. No OOS-data contamination detected. PASS

### Check 3 — LM Master Integration
USER-DIRECTIVE-WAIVED. Phase 4.5 skipped per explicit user directive 2026-05-29.
No lgbm_advisor.md exists; no Section 3 responses required. Non-blocking per directive.

### Check 4 — Axis Rotation Discipline
TYPE: CONFIRMATION — exempt from Axis Rotation Discipline per skill definition.
Rotation check does not apply to CONFIRMATIONs. PASS (N/A)

### Check 5 — HIGH-RISK Declaration
HIGH-RISK declared with four enumerated reasons. Mitigation via CONFIRMATION-standard
10 inner seeds per `V1_CONFIRMATION_ENSEMBLE_SIZE = 10` non-negotiable. PASS

### Check 6 — Falsifier Pre-Registration
F1-F5 in Section 2 with explicit bands:
- F1: OOS Sharpe Δ ≥ +0.336 (≥ +1.00 absolute); bands [-0.10, +0.10] / [+0.10, +0.336) /
  ≥ +0.336 / < -0.10 mapped to verdict cells
- F2: OOS trades [600, 1100]; FAIL < 600 OR > 1100
- F3: ≥ 3/5 symbols positive net OOS PnL; FAIL ≤ 2
- F4: median n_eff ∈ [10, 25]; FAIL < 10 → BLOCK-PENDING-FIX
- F5: OOS TP-exit count ≥ 15; FAIL < 15 → BLOCK-FINAL
All 5 falsifiers present with bands. Verdict matrix Row 1-7 in Section 4. PASS

### Check 7 — Test Mandate
Section 10.3 lists 14 tests (exceeds 12-test minimum). All 4 MANDATORY items present:
- BASELINE CATCH-ALL EXCLUSION (test 7): PASS ✓
- DISPATCH BANNER (test 13): PASS ✓
- REAL TradeResult assertion using trade.symbol (test 8): PASS ✓ (per /027 LESSON)
- Per-model sample weight wiring (test 11): PASS ✓
Additional tests: 5-model dispatch routing (tests 1-5), no-double-dispatch (test 6),
gate config (tests 9-10), ENSEMBLE_SIZE/n_trials locks (tests 8-9), reproducibility
(test 10), wall_clock logging (test 12), foundation regression (test 12),
baseline-non-corruption (test 14). PASS

### Check 8 — Cadence Position
15 confirmed EXPLORATION precedents (cycle-3 /016-/025 = 10; cycle-4 /028+/029+/030+
/031+/032 = 5). Brief claims 16 (including /026 sanity). Satisfies 10:1 skill requirement.
CONFIRMATION-EXCEPTION rationale: /027 TF consumed cycle-3 CONFIRMATION slot; cycle-4
inherits cycle-3 substrate; 16:1 cross-cycle ratio satisfies the rule. PASS

### Check 9 — No OOS Leakage in Design
Section 1.1 specialist OOS Sharpe numbers sourced from prior single-seed EXPLORATION
reports (committed in reports-v1/). Section 1.2 per-symbol OOS attribution sourced from
prior iteration reports. Section 1.3 pairwise correlations computed on monthly PnL series
from prior iterations (ALREADY OOS at time of that iteration's production; cited as
historical fact, not forward-looking OOS inference). Verdict matrix (Section 4/8)
pre-committed before backtest. Section 7 failure-mode prediction is prospective.
PASS

### Check 10 — CONFIRMATION Precedent Count
15 confirmed EXPLORATIONs preceding /033. Satisfies ≥10. PASS

### Check 11 — Reproducibility Section
Section 10.2: outer seed = 42, ENSEMBLE_SIZE = 10, n_trials = 35,
sample_weight_mode = composite_inv_concurrency, V1_FEATURE_COLUMNS_PRUNED 43 cols.
OOS_CUTOFF_DATE = 2025-03-24 UNCHANGED. training_months = 24 UNCHANGED.
Walk-forward embargo at walk_forward.py:113 confirmed. Foundation discipline. PASS

### Check 12 — Wall-clock Estimate (5-step label-rate scaling)
Section 0.5 provides full 5-step scaling:
Step 1: BASELINE_V1 precedent = 7h 0m (5-seed × 50-trials × 5-sym)
Step 2: Baseline label count = ~810 total
Step 3: /033 label count ≈ 1.0× (net ~5% reduction; modeled conservatively at 1.0)
Step 4: (10/5) × (35/50) × (1/1) × 1.0 = 2.0 × 0.7 × 1.0 × 1.0 = 1.40×
Step 5: 7h × 1.40 = 9.8h modal — EXCEEDS 6h cap → CONFIRMATION-EXCEPTION declared
Kill-switch at 10.0h (CONFIRMATION-EXCEPTION; 2h safety margin before 12h hard cap). PASS

### Check 13 — Library Stack (Section 9)
lightgbm ≥ 4.0, optuna, pandas, numpy, scipy.stats, statsmodels listed.
mlfinlab/mlfinpy fallback declared. fracdiff not used. No new libraries. PASS

---

## Summary

All 13 checks PASS. LM Master Phase 4.5 waived by explicit user directive (2026-05-29).
CONFIRMATION cadence: 15 confirmed EXPLORATION precedents across cycles 3+4 satisfies ≥10
rule. HIGH-RISK declared with CONFIRMATION-standard 10 inner seeds as mitigation. Numerical
evidence committed at `f433f6b`. 14 tests in mandate — all 4 mandatory items present
(catch-all exclusion + banner + REAL-TradeResult assert + sample-weight wiring). Wall-clock
9.8h modal with CONFIRMATION-EXCEPTION 12h hard cap / 10h kill-switch.

OVERALL: PASS

Phase 6.0 Critic pre-flight dispatch is authorized.
