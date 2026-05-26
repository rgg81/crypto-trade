# Phase 7.5 Critic Review — iter-v1/016

OVERALL: EXPLORATION-NEGATIVE — sample-weighting axis catastrophic (F1 OOS Δ -1.67, F3 IS Δ -0.59); axis CLOSED at v1

## Iteration Type
TYPE: EXPLORATION (CYCLE-3 #1, sample-weighting axis, HIGH-RISK declared)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
No code change touches labeling.py, walk_forward.py, or feature pipeline. Only lgbm.py sample_weight branch + bounds_profile pin. Mini-Check 1 cleared at Phase 6.0.

### Check 2 — Embargo Width: PASS
Foundation untouched. walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms`. 4 regression tests present.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR_IS=-62.30, DSR_OOS=-38.24, PSR_monthly_vs_0 IS=0.289/OOS=0.125. All below thresholds. Per Section 0.5 TYPE=EXPLORATION, informational only. **n_effective_trials = 9** (BELOW LM Master predicted [10, 20] band — see Check 14 note).

### Check 4 — IC Correlation: PASS
No feature change. Identical to /015.

### Check 5 — ADF Stationarity: PASS
No feature change.

### Check 6 — Pareto Dominance: N/A
Single-seed EXPLORATION. Pareto check is multi-outer-seed gate.

### Check 7 — Reproducibility: WARN
`reports-v1/iteration_v1-016/engineering_report.md` MISSING via `--no-engineering-report` opt-out (**5th strike**). Brief §10.2 explicitly stated "engineering_report.md MUST exist" — this iteration violates the explicit brief mandate, repeating /015 process defect. NOT FAIL because comparison.csv + f_axis_mechanism.csv artifacts present and consistent; HEAD `4e797e8` stable; feature_columns + ensemble_seeds explicit. Re-flagged for QR Recommendation #1 as cycle-3 forward fix.

### Check 8 — Hypothesis-Implementation Alignment: PASS-by-construction-WITH-CRITICAL-NOTE

F-AXIS-MECHANISM compound falsifier PASSes all three sub-checks by mathematical construction: Kish=1.0000 across all 205 cells, Model A balance 0.500/0.500, timeout_fallback_share=0.0. Wiring fired as designed.

**BUT**: this is the **canonical "wiring test ≠ edge test" exemplar** — LM Master Phase 4.5 Risk #1 + Phase 7.4 §3 vindicated. Hypothesis Section 1 ("uniform weighting will eliminate per-symbol asymmetry") implemented correctly; the hypothesis was simply WRONG — `abs(labeled_pnl)` weighting is structural to v1's edge per LM Master Phase 7.4 §2. Implementation matches brief; brief's mechanism prediction was refuted by data. **Add to Check 8 catalog as v1 reference case.**

### Check 13 — Anti-Pattern Static Scan: PASS
A1/A2/A3/A4-A11/A12/A13/A14 all PASS. Foundation untouched. No new anti-patterns.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares `sample-weighting` NEW family. src/ diff shows only lgbm.py sample_weight branch + optimization.py v1_pruned_axis016 bounds pin. Exactly matches declared axis family. Rotation VALID (prior 5: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1).

## Per-symbol Pattern (Critical Forward Concern)

**ETH OOS catastrophic STRUCTURAL across 3 axes**:
- /014 labeling -41.18 (single-seed)
- /015 multi-seed labeling -23.29
- /016 sample-weighting **-51.46**

LM Master Phase 7.4 §5 flagged; Critic confirms. **Basin property, not iteration-specific.** /017+ briefs MUST explicitly acknowledge ETH structural drag in Section 2 EDA.

## Recommendations to QR

1. **Engineering report opt-out is recurring process defect (5th strike)**. The `--no-engineering-report` flag was proscribed in /015 LESSON closure AND brief §10.2 — used anyway. Cycle-3 cannot tolerate continued opt-out. Propose: skill update `feedback_v1_engineering_report_blocking.md` making the flag an error, not a warning.

2. **ETH catastrophic OOS structural across 3 axes**. /017+ briefs MUST acknowledge in Section 2 EDA and pre-register either (a) universe-expansion-as-dilution test OR (b) ETH-specific kill switch.

3. **n_eff_per_cell has TWO drivers, not one**. /015 collapse was label-shape-bound; /016 collapse (9 < predicted [10,20]) added weight-distribution as second driver. Update LM Master substrate model: n_eff_per_cell ← f(label_shape, weight_distribution). Future "uniform-anything" axes should pre-register n_eff_per_cell as F-AXIS-MECHANISM sub-check.

## Path Forward

Per cycle-3 §0.6 rotation discipline (prior 5: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1):

1. **Universe expansion** — `universe` family (UNUSED since /006; never tested in cycle-2 or cycle-3). Add 1-2 symbols from V1_EXCLUDED_SYMBOLS (SOLUSDT preferred for cycle-2 OOS-rich profile non-correlated-with-BTC; XRPUSDT alternate). 6-symbol universe at ENSEMBLE_SIZE=3 + n_trials=18 estimated 1.7-1.8h. Mechanism: dilute ETH's catastrophic weight in portfolio Sharpe denominator AND test whether basin-lock is universe-bound vs regime-bound. **PRIMARY** per LM Master Phase 7.4 §6.

2. **Model architecture (XGBoost)** — `model-arch` family (UNUSED in v1; matches v3/016 axis priority precedent). Head-to-head LightGBM vs XGBoost on identical V1_FEATURE_COLUMNS_PRUNED + abs_pnl weighting baseline. **Deferred to /018+** per user XGBoost-slower flag; needs wall-clock smoke test characterization first. SECONDARY.

3. **ETH-specific regime kill switch / per-symbol drawdown brake** — `risk-primitive` family-variant. IF /017 universe expansion does NOT reshape ETH drag, /018 pivots to ETH-conditional kill (regime-bound gate, not threshold-tuning). TERTIARY — conditional on /017 outcome.

## Wall-Clock Discipline — First Cycle-3 Empirical Validation

/016 ran ~50min total with 2h cap → **75% margin**. Prediction band 1.50-1.75h overstated actual wall-clock by ~2-3×. **Empirical anchor confirms ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 5-symbol + 8h is CONSERVATIVE**. Headroom available for 6-7 symbol universe expansion at /017 without n_trials further compression. Informational; propose skill amend with empirical datapoint.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE catastrophic. Defects (engineering report opt-out, ETH structural drag) are forward-looking lessons. /016 closes; /017 advances per Path Forward.
