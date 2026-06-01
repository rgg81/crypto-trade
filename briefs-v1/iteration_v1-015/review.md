# Phase 7.5 Critic Review — iter-v1/015

OVERALL: CONFIRMATION-NEGATIVE catastrophic — F1-MULTI Δ=-1.6117 (32× the -0.05 catastrophic floor); F-AXIS-MECHANISM HARD-FALSIFIER FAIL (n_eff=3 vs predicted ≥17); BASELINE_V1 NOT updated; cycle-2 closes NO-MERGE.

## Iteration Type
TYPE: CONFIRMATION (cycle-2 #10 of 10; FIRST cycle-2 CONFIRMATION; ENSEMBLE_SIZE=10, n_trials=35; full 8-check pass with strict threshold enforcement)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Foundation re-audited. `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. 4 mandated regression tests present. `labeling.py:341-374` σ_t path uses past-only `_sqrt_timeout_lbl × sigma_values[idx]` from EWMA `.shift(1)` upstream. `lgbm.py:932-944` execution path identical formula reading from `_month_sigma` cache populated from same `_label_sigma_values` array. RuntimeError raised on NaN/None σ_t (LM Master Rec #3 mandatory). C1 closure complete and structurally guaranteed.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 110 (22 × 5 symbols). Centralized helper. Symmetric application.

### Check 3 — Multiple-Testing Correction: FAIL (binding at TYPE=CONFIRMATION)

DSR_IS=-87.69, DSR_OOS=-38.77 (FAIL × orders of magnitude). PSR_monthly_vs_0 IS=0.450 / OOS=0.118 (FAIL both halves at 0.95 threshold). PSR_monthly_vs_1 effectively zero. **n_eff_per_cell_median = 3 across all symbols** (BTC=4, DOT=3, ETH=4, LINK=3, LTC=3) — 6.3× drop from /014's 19.

**n_eff=3 collapse is structural mechanism for negative OOS**: each Optuna cell decides on ~3 effective labels; hyperparameter search becomes 3-dim projection of 35-dim objective; Optuna selects on noise. Per Brief Section 8.3 Gate 6 (PSR_monthly_vs_0 OOS > 0.95) and Gate 9 (10-seed mean Sharpe > 0), cannot clear hard-block gates for BASELINE_V1 update.

### Check 4 — IC Correlation: PASS

No new feature family added; baseline IC structure inherited unchanged.

### Check 5 — ADF Stationarity: PASS (with forward-mandate)

Active features bonferroni_pass=True. LM Master Phase 7.4 closing-note concern about label-distribution stationarity at n_eff=3 (labels become near-fwd_return-sign at 7.82% barriers over 21-candle horizon) is informational for cycle-3, not /015-blocking.

### Check 6 — Pareto Dominance: N/A (artifact MISSING)

No `pareto_front.csv` produced. Gate 10 (both Pareto seeds OOS Sharpe > 0) cannot be evaluated from artifacts. Per-symbol OOS shows LINK 285% concentration (Gate 7 violation by wide margin). Without per-seed dispersion, cannot rule basin-rotation but F1-MULTI -1.6117 magnitude makes any seed positive at meaningful magnitude implausible. Gate 10 effectively FAILs by inference. F1-MULTI scalar decisive at Section 8.1.

### Check 7 — Reproducibility: WARN

- Engineering report at `reports-v1/iteration_v1-015/engineering_report.md`: **DOES NOT EXIST**. Iteration ran with `--no-engineering-report` flag (procedurally legal opt-out path codified at QE commit `aaa5e6b`), bypassing the HARD-STOP.
- The advisory file `lgbm_advisor.md` Phase 7.4 sits in for the engineering report — acceptable as one-time exception but recurs the same forensic gap. F-AXIS-C1 and F-AXIS-MECHANISM pre-registered as BLOCKING deliverables but not attached to a structured engineering artifact.
- PnL math reproducibility verified via spot-checks (LINK long row 1 IS; ETH short row 1 OOS).
- Explicit `feature_columns=active_feature_columns` wiring (no auto-discovery). Inner ensemble seeds derived from canonical roster.

Acceptable for NEGATIVE-headline outcome where verdict determined by F1-MULTI. Would be hard FAIL if PROMISING claimed.

### Check 8 — Hypothesis-Implementation Alignment: PASS for registered hypothesis

Brief Section 1 hypothesis: "multi-seed mean OOS Sharpe Δ within band [-0.30, +0.30]; 55/20/25 NULL/PROMISING/NEGATIVE." Observed: F1-MULTI = **-1.6117** — **far below the brief's -0.55 NEGATIVE-catastrophic floor**. Outcome falls outside LM Master /014 §6 calibration's prior band entirely.

LM Master Phase 7.4 §3 self-critique applies: "Path 1 was METHODOLOGICALLY correct but EMPIRICALLY WRONG." The /015 brief, LM Master Rec #5, and Phase 6.0 pre-flight all certified the experiment as well-posed at 7.82% labels, but the 7.82% × 21-candle combination produced timeout-dominated labels that collapsed n_eff from 19 to 3.

**F-AXIS-MECHANISM HARD-FALSIFIER FAIL** is the cleanest evidence: predicted "n_eff_per_cell_median ≥ 17 across at least 7 of 10 outer seeds" at >95%; observed n_eff=3 across all per-symbol cells. Single largest miss in LM Master credibility-stake ledger. Mechanism is real; directionality was inverted from prediction — **n_eff is a CURVE in barrier-magnitude space**, NOT a monotone-increasing function as Rec #4 implicitly assumed.

NOT a code defect. The src/ implementation correctly executes the brief's spec. The brief's spec was empirically wrong.

### Check 13 — Anti-Pattern Static Scan: PASS

A1/A2/A3/A4-A11/A12/A13/A14 all PASS. The n_eff collapse is NOT an anti-pattern; it is a mechanism finding within a clean implementation.

### Check 14 — Axis Family Validation: PASS

`labeling` family declared; src/ diff exclusively within labeling.py + lgbm.py σ_t paths. Infrastructure changes (engineering report HARD-STOP) are non-axis. Declared family matches observed change. Rotation N/A at CONFIRMATION.

## Verdict Cell Assignment (binding from Brief Section 7.5)

| F1-MULTI Δ | F1-IS Δ | F-AXIS-MECHANISM | Verdict-class |
|---|---|---|---|
| -1.6117 | -0.3474 | FAIL (3/10 vs ≥7/10) | **CONFIRMATION-NEGATIVE-catastrophic** |

Brief Section 8.4 verdict class binding: multi-seed mean OOS Δ < -0.05 → CONFIRMATION-NEGATIVE. With Δ=-1.6117 (32× the NEGATIVE boundary), catastrophic subclass fires.

**BASELINE_V1 update: NO.** Axis CLOSED at multi-seed. Cycle-2 closes NO-MERGE.

NOT BLOCK-PENDING-FIX. The F-AXIS-C1 programmatic falsifier did not fire (no NaN RuntimeError raised; σ_t cache correctly populated). The implementation was correct. The hypothesis was empirically refuted at the mechanism layer (F-AXIS-MECHANISM FAIL) and the headline layer (F1-MULTI catastrophic) simultaneously.

## Recommendations to QR (cycle-3 process-level fixes)

1. **n_eff vs barrier-magnitude EDA mandate**: before any future labeling sub-axis EXPLORATION, run the calibration sweep — test {1.5%, 2.5%, 3.5%, 5.0%, 7.82%} barriers at single-seed and chart n_eff per magnitude. Establish n_eff ≥ 15 preservation band BEFORE selecting CONFIRMATION magnitude. Codifies what Path 1 should have included pre-implementation.

2. **F-AXIS-MECHANISM as label-distribution falsifier**: /015 brief's prediction "n_eff bound by label-distribution SHAPE; seed-INDEPENDENT" was structurally true but DIRECTIONALLY WRONG. Tighten future falsifier to pre-register a label-distribution histogram (count `tp_hit` / `sl_hit` / `timeout_fallback` per cell) with threshold (e.g., `timeout_fallback_share < 0.6`). At /015, share was almost certainly > 0.85.

3. **Engineering report HARD-STOP enforcement**: `--no-engineering-report` opt-out was exercised on the very first iteration with the HARD-STOP in place. Either remove the opt-out OR require orchestrator to create minimal stub `engineering_report.md` with F-AXIS evaluations attached. As-is, the opt-out makes the HARD-STOP cosmetic.

## Path Forward (cycle-3 EXPLORATION axes; mandatory for CONFIRMATION-NEGATIVE)

Cycle-2 closes: 10 iterations, 1 PROMISING-METHODOLOGY (/008), 9 NEGATIVE, ZERO merges. BASELINE_V1 unchanged. **Cycle-3 begins at /016 under NEW 2h EXPLORATION wall-clock cap** (skill update at `4cb8972`).

Prior 5 EXPLORATION families: risk-primitive ×2 (/010, /011), methodology-substrate-test ×2 (/012, /013), labeling (/014). EXCLUDED from cycle-3 first 5 EXPLORATIONs per rotation discipline.

Proposed cycle-3 axes from UNUSED families:

1. **Sample-weighting by past-realized vol** — `sample-weighting` (NEW family, never used in v1). López de Prado AFML Ch. 4: weight-by-uniqueness OR weight-by-realized-vol. Replace `abs(labeled_pnl)` sample weighting with weights inversely proportional to 30-day realized vol. **Wall-clock fit**: V1_FEATURE_COLUMNS_PRUNED at 193, ENSEMBLE_SIZE=3, n_trials=20, full 5-symbol universe → ≈ 1.5-1.8h (2h cap achievable). **Mechanism**: directly addresses /015's mechanism finding (timeout-dominated cells dominate loss surface; weighting these down should restore n_eff diversification at any barrier magnitude).

2. **XGBoost head-to-head** — `model-arch` (UNUSED in v1 cycle-2). Depth-wise growth (XGBoost) vs leaf-wise (LightGBM) on v1's 193-feature pruned stack. **Wall-clock fit**: keep V1_FEATURE_COLUMNS_PRUNED, ENSEMBLE_SIZE=3, n_trials=20, single-symbol-pair Model-A only (BTC+ETH pooled) — halves wall-clock; ≈ 1.5h. **Mechanism**: substrate-test on model-arch family at single-seed lottery resolution.

3. **Universe expansion to 7-symbol with per-symbol drawdown brake** — `universe` (UNUSED in v1 since /006). Add 2 symbols (SOLUSDT, NEARUSDT, or AVAXUSDT from V1_EXCLUDED_SYMBOLS) + per-symbol drawdown brake (NOT proportional cap — v3/020 closed that family). Brake fires hard-off when per-symbol cumulative drawdown crosses -X%; resets at calendar-month boundary (avoids /054-style deadlock). **Wall-clock fit**: 7 symbols × ENSEMBLE_SIZE=3 × n_trials=20 ≈ 2.0h; compress to 6 if tight. **Mechanism**: denominator expansion attenuates LINK-monopoly-of-OOS-PnL pattern; brake provides time-based escape.

Each axis from UNUSED family; each includes explicit wall-clock fit per NEW discipline (skill `4cb8972`). QR's first cycle-3 brief should EDA-justify one and propose remaining two as alternates per Section 11 template.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is CONFIRMATION-NEGATIVE catastrophic. The implementation was correct; the hypothesis was empirically refuted. No isolated defect to fix. /015 closes labeling axis at calibrated 7.82% magnitude; cycle-3 advances per Path Forward.
