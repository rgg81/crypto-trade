# Phase 5.5 Gate — iter-v1/013

OVERALL: PASS

---

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION
Declared: cycle-2 EXPLORATION #8 of 10. Earliest CONFIRMATION at /015 (after /014 completes the 10th EXPLORATION).

## Axis Family + Rotation Status

FAMILY: methodology-substrate-test
ROTATION_STATUS: VALID

Rotation check (last 5 EXPLORATIONs from exploration_catalog.md):
- iter-v1/008: methodology
- iter-v1/009: feature-family
- iter-v1/010: risk-primitive
- iter-v1/011: risk-primitive (binary-kill subtype)
- iter-v1/012: methodology-substrate-test (first usage)

/013 is the 3rd consecutive at this family (3 of last 6, 1 of last 5). The saturation threshold is 5-of-5 same family. Last 5 spans 4 distinct families. 5-of-5 rule does NOT fire. `methodology-substrate-test` is a PRE-EXISTING 8th catalog family (established at /012 Critic Phase 7.5 PASS-WITH-NOTE); /013 is NOT a new family declaration.

Orchestrator flag (non-blocking): 3rd consecutive at same family noted per brief Section 0.6 per Critic /012 Rec #3 process flag.

## HIGH-RISK Declaration

HIGH-RISK: NO (NORMAL-RISK)
Rationale: /013 changes only the RNG initialization (inner seeds offset 3→6). Training-objective domain (data rows, labels, weights, features, bounds, ENSEMBLE_SIZE, n_trials) is BIT-IDENTICAL to /011 AND /012. Optuna's training-objective domain is unchanged.
Multi-seed mitigation: N/A (NORMAL-RISK does not require mitigation; single-seed-window EXPLORATION is appropriate for this axis).

## LM Master Response Verification

- briefs-v1/iteration_v1-013/lgbm_advisor.md exists: PASS
- Brief Section 3.3 addresses LM Master anticipated recommendations: PASS

Detail: lgbm_advisor.md §5 provides /014 conditional recommendations based on /013 outcome (not /013 config recommendations). The advisor explicitly states "No hyperparameter or feature changes recommended. Brief Section 3 axis isolation is mechanically clean." Brief Section 3.3 pre-adopts all 4 anticipated advisory recs (FLAT 30/30/40 priors adopted per LM Master Phase 7.4 §2 commitment; exhaustive Section 8.1 matrix pre-registered per LM Master §§7+8; offset=6 adherence confirmed per LM Master Phase 7.4 §7; no UNUSED-family pivot per pre-registration discipline). No rec in lgbm_advisor.md is unaddressed or contradicted.

## Cadence Check

- Wall-clock budget declared: ≤2h (EXPLORATION cap). Predicted 75-90 min per /011/012 reference: PASS
- CONFIRMATION not yet applicable: cycle-2 has 8 EXPLORATIONs after /013 (need 10; next CONFIRMATION eligible at /015 earliest): PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 confirmed via baseline anchor in Section 0.1. IS window = 24 months ending 2025-03-24; OOS window = 2025-03-24 to present. UNCHANGED per Section 0.1 explicit statement.
- Section 0.5 (Iteration Type): PASS — EXPLORATION declared (cycle-2 #8/10; explicit cadence position with prior 7 iterations listed).
- Section 0.6 (Architecture-Family Justification): PASS — methodology-substrate-test family, PRE-EXISTING 8th catalog family from /012. Prior 5 families enumerated. Rotation status VALID with explicit reasoning. 3rd-consecutive same-family flag issued to orchestrator (non-blocking). Pre-registration discipline justification for continuing vs. pivoting documented.
- Section 1 (Hypothesis): PASS — Specific, testable one-sentence hypothesis ("shifting inner-seeds window from [789, 1001, 2002] to [3003, 4004, 5005] validates or refutes the 2-PROPERTY DECOMPOSITION"). Includes 3 testable falsifier bands with explicit numerical conditions (IS Δ [+0.38, +0.58]; LTC IS overlap with /011 [15%, 40%]; LTC IS overlap with /012 [25%, 50%]). Pre-committed /015 CONFIRMATION conditional stated.
- Section 2 (IS-Only Evidence): PASS — Substrate-magnitude table from committed comparison.csv artifacts (/010, /011, /012). Roster overlap from committed f6_roster_overlap.csv (/011 reports) and f7_roster_overlap.csv (/012 reports). General-purpose analysis script at analysis/iteration_v1-012/f6_roster_overlap.py (committed at /012 commit 360650f). OOS-amplification fraction trajectory table. Numerical evidence is concrete; category-matching absent.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared with full rationale. HIGH-RISK criteria (training-objective domain change) explicitly checked and confirmed absent. /012 precedent cited.
- Section 3 (Proposed Changes): PASS — Explicitly states NO src/ changes. Three Critic /012 process recommendations adopted explicitly with Rec text quoted and adoption statement. LM Master Phase 4.5 anticipated recommendations pre-adopted (Recs 1-4). Runner invocation specified with all flags. Wall-clock budget estimated.
- Section 4 (Expected OOS Impact + Falsifiers F1-F9): PASS — F1 through F9 all present with explicit numerical pass-band and fire conditions. F8 (NEW: LTC IS overlap with /012 [25%, 50%]) and F9 (NEW: IS Δ [+0.38, +0.58]) are pre-registered. F1 is the load-bearing /015 conditional trigger (sign determines CONFIRMATION axis). Confidence intervals via flat-prior outcome table in Section 5.
- Section 5 (Risk Mitigation — PASS via inheritance): PASS — All risk gates (R1/R2/R3/R5) are BIT-IDENTICAL to /011 AND /012 (no changes). Fire rates from /011/012 provided as calibrated IS baseline (R5-BINARY-KILL IS 18.34%/17.38%, OOS 21.69%/22.84%). No IS-calibrated threshold changes and no simulated effect required since no risk gate parameters change.
- Section 6 (Risk Management Design — PASS via inheritance): PASS — R5-BINARY-KILL config (kill_low @ NATR_14 < 2.0%, BIT-IDENTICAL to /011/012) documented throughout. R1/R2/R3 inherited unchanged. Fire rate predictions given (F2 falsifier: IS and OOS [10%, 60%]; predicted within ±2pp of /011/012 reference). Regime coverage unchanged.
- Section 7 (Failure-Mode Prediction): PASS — Section 6 of the brief pre-registers the tripwire failure modes: F9 outside [+0.38, +0.58] → substrate-magnitude lock REFUTED (halt and reassess per LM Master Phase 7.4 §7); F7 > 70% AND F8 > 70% → roster substrate-locked (decomposition REFUTED); F2 outside [10%, 60%] → data integrity failure (BLOCK-PENDING-FIX). lgbm_advisor.md §3 adds per-symbol catastrophic reversal risk and denominator-effect on pct_of_total_pnl. Section 8.1 pre-registers all 8 outcome cells with failure-mode routing.
- Section 8 (MERGE/NO-MERGE Numerical Criteria): PASS — Section 8.3 explicitly states /013 verdict will be EXPLORATION-NEGATIVE or EXPLORATION-PROMISING (never MERGE — EXPLORATION never merges to trunk). Section 8.5 codifies the pre-committed /015 CONFIRMATION conditional with exact F1 sign thresholds. Section 8.1 provides the 8-row F1×F3×F7×F8×F9 deterministic verdict matrix with boundary cells explicitly handled. No discretion at verdict time.
- Section 9 (Library Stack): PASS — Full library stack declared: LightGbmStrategy, optimize_and_train, run_backtest, validation_v1, reporting_v1, pandas 2.3.3, numpy 2.3.4, lightgbm 4.6.0, optuna 4.5.0, statsmodels 0.14.4 (pinned in uv.lock). No new libraries required.

## Setup Verification Items (per dispatch)

1. --ensemble-seeds-offset CLI flag accepts value 6: PASS — run_baseline_v1.py line 793+ wires the flag; _derive_ensemble_seeds(size=3, offset=6) produces [3003, 4004, 5005] (confirmed by ENSEMBLE_SEEDS tuple inspection; offset+size=9 ≤ len=10, within bounds).
2. F6 join script at analysis/iteration_v1-012/f6_roster_overlap.py accepts multiple --reference args: PASS — script header confirms repeatable --reference NAME=PATH pattern; Section 10.2 invocation uses 4 references (baseline, iter010, iter011, iter012).
3. R5-BINARY-KILL wiring at backtest.py:430+: PASS — grep confirms risk_r5_kill_low_natr_enabled logic at backtest.py:430 (from /011 commit b788d4f); BIT-IDENTICAL to /011 AND /012.
4. Comparison.csv R5-BINARY-KILL row appender: PASS — run_baseline_v1.py line 665+ wires the R5-BINARY-KILL fire-rate rows into comparison.csv (from /011 commit b788d4f); labels confirmed correct per F4 falsifier.
5. Engineering report deliverable spec: PASS — brief Section 10.2 Deliverable #4 explicitly mandates engineering_report.md as Phase 6 QE deliverable (not Phase 7 carry-forward), per Critic /012 Rec #2.

## src/ Changes Required

NONE — brief Section 3.1 and Section 10.1 both confirm no src/ changes. No feat commit needed before Phase 6.0 Critic pre-flight. Phase 6.0 Critic pre-flight can proceed directly on the current HEAD.

## Reasons

N/A — OVERALL=PASS. All mandatory sections present and substantively complete.

---

Gate written by QE (claude-sonnet-4-6) on 2026-05-25.
Branch: iteration-v1/013. HEAD at gate evaluation: 5c1e5a4.
