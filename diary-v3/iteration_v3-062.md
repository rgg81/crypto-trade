# iter-v3/062 — Cycle 1 #3 PASSIVE-DIAGNOSTIC / EXPLORATION-MERGE / Path B4 deferred to /069

**Date**: 2026-05-13
**Type**: EXPLORATION (cycle 1 #3 of 10; NEW subtype PASSIVE-DIAGNOSTIC — first in v3 history)
**Path**: C (passive retrospective + defer methodology change to /069 CONFIRMATION)
**Verdict**: EXPLORATION-MERGE per Critic FINAL `e713c2f`
**BASELINE_V3.md**: UNCHANGED (still anchors `v0.v3-059`)
**Branch**: `iteration-v3/062`

## 1. What was done

iter-v3/062 was the cycle 1 EXPLORATION slot dedicated to addressing the DSR_relative threshold/benchmark recalibration concern raised by Critic /059 Rec #1 and re-flagged at /061 as 3-iteration-stale. Through EDA-driven analysis (T1-T7 numerical tables at `analysis/iteration_v3-062/`), the QR identified that:

1. The runner's `psr()` call at `run_baseline_v3.py:2296-2302` passes **trade-level annualized Sharpe** as `observed_sharpe` and **candle-level annualized Sharpe** as `benchmark_sharpe` — a √n_trades vs √n_test scale gap of structurally ≈3.6× (using √1296 reference) or ≈6× (using √3833 full-OOS reference; presentational inconsistency noted by Critic but doesn't affect Path B4 specification).

2. Three candidate paths were evaluated:
   - **Path A** (recalibrate threshold 0.95 → 0.50-0.60): partial fix; /059 still FAILs at 0.55 (observed dsr_relative=0.113); /060/061 EXPLORATION-mode dsr_relative=0.0 unchanged at ANY threshold.
   - **Path B** (reformulate input granularity, e.g. annualize both inputs to daily scale): correct root-cause fix; B4 sub-variant (annualized-both-sides) produces dsr_relative=1.0 at /058 and /059 (positive OOS edge correctly recognized) and ≈0 at /060/061 (weak EXPLORATION-mode OOS correctly rejected). Arithmetic independently verified by Critic for all 4 iterations.
   - **Path C** (passive retrospective + defer to CONFIRMATION): EXPLORATION-mode DSR is informational only per `feedback_v3_dsr_mode_artifact.md`, AND Path B integration test surface (mandated by `feedback_v3_methodology_axis_integration_test.md` + `feedback_v3_methodology_post_hoc_input_traceback.md`) doesn't fit within the 2h EXPLORATION cap.

3. **Path C selected** with quantitative justification at EDA T6-T7. ZERO code change at /062; ITERATION_LABEL stays "v3-061"; no backtest produced.

4. Brief Section 3 contains the complete Path B4 specification for iter-v3/069 cycle 1 CONFIRMATION to implement: file path (`run_baseline_v3.py:2257-2305` replacement block), function calls, input variable granularity normalizations, integration test file (`tests/strategies/ml/test_dsr_relative_b4.py`), smoke test template, backward-compat validation (re-run /058 + /059 under Path B4).

5. **Predicted /069 dsr_relative_B4 band: ≈0.999+ (PASS at 0.95 threshold)** at /059 anchor data — narrow falsifier band intentional. If /069 produces dsr_relative_B4 outside [0.95, 1.0], Path B4 methodology is suspect.

## 2. Key EDA findings

| Iter | dsr_relative | cpcv_q75 | observed_sharpe (trade-level annualized) | Path B4 (annualized-both-sides) |
|---|---|---|---|---|
| /058 | 0.998164 | 0.838 | 2.0759 | 1.0 (PASS) |
| /059 | 0.113363 | 0.838 | 1.4359 | 1.0 (PASS) |
| /060 | 0.0 | 0.838 | 0.3659 | 2e-6 (FAIL — correctly rejects weak OOS) |
| /061 | 0.0 | 0.838 | 0.4051 | 3.7e-5 (FAIL — correctly rejects weak OOS) |

Granularity mismatch: trade-level √n_trades vs candle-level √n_test scale factor produces structurally suppressed dsr_relative when OOS Sharpe is small. Path B4 annualizes both sides to daily-equivalent scale via √252, side-stepping the candle-count ambiguity.

## 3. Path A/B/C comparison + Path C selection rationale

| Path | Effectiveness | Implementation cost | Fits EXPLORATION 2h cap? | Selected? |
|---|---|---|---|---|
| A (threshold recalibration) | Partial (doesn't fix /059) | Low (1 constant) | Yes | NO |
| B (input granularity reformulation) | Full (correct root cause) | High (4 input renormalizations + integration test surface + backward-compat) | No (integration test surface mandated) | NO |
| C (passive defer to /069 CONFIRMATION) | N/A at /062; binding spec for /069 | Zero code change | Yes (no backtest, no integration test) | **YES** |

Path C rationale: (1) EXPLORATION-mode DSR is informational anyway per `feedback_v3_dsr_mode_artifact.md`; (2) the methodology axis is structurally a CONFIRMATION-mode concern; (3) Path B4 specification is fully written in brief Section 3 — /069 QR/QE can implement without re-research; (4) binding pre-registration (narrow 0.999+ band) puts the QR on the hook for falsification.

## 4. Critic verdict summary

Critic FINAL `e713c2f`: **OVERALL=EXPLORATION-MERGE; PASSIVE-DIAGNOSTIC certified clean**.

- 13/13 Checks PASS (1 PASS-with-DEFERRAL on A12 to /069; granularity gap persists as the diagnosed axis)
- §11 Anti-Pattern Static Scan: 13/13 PASS
- Foundation Audit (Boot Steps 9-11): walk_forward, labeling, lgbm, validation_v3, runner — ALL unmodified between /061..062
- EDA T4 Path B4 arithmetic INDEPENDENTLY VERIFIED for all 4 iterations
- Path B4 specification completeness verified (file path, function calls, integration tests, backward-compat plan, predicted falsifier band)
- Minor PASS-with-NOTE: T2 presentational inconsistency (√1296 vs √3833 candle-side denominator); both defensible; doesn't affect Path B4 spec

## 5. PATH classification

**PASSIVE-DIAGNOSTIC** — NEW path category (first in v3 history). See `feedback_v3_passive_diagnostic_path.md` for the canonicalized rule.

Methodology-only axes where (a) EXPLORATION-vs-CONFIRMATION architectural scales produce non-transferable results AND (b) Path B integration test surface doesn't fit within the EXPLORATION 2h hard cap may select Path C: zero code change + EDA + brief + Path B4 specification for the deferred CONFIRMATION iteration.

## 6. Path B4 specification handoff to /069

iter-v3/069 cycle 1 CONFIRMATION inherits the following BINDING pre-registration from brief Section 3:

1. **Code change site**: `run_baseline_v3.py:2257-2305` replacement block (full code spec in brief Section 3)
2. **Input variable normalizations**:
   - `daily_sharpe_oos_annualized` = mean(oos_daily_pnl) / std(oos_daily_pnl) × √252
   - `cpcv_q75_annualized` = cpcv_path_sharpe_q75 / √1296 × √756 (de-annualize-then-re-annualize to √756)
   - `n_daily_obs_oos` = len(oos_daily_pnl)
   - `daily_skew_oos`, `daily_kurt_oos` = scipy.stats.skew/kurtosis on daily series
3. **Integration test**: `tests/strategies/ml/test_dsr_relative_b4.py` (6th integration test per `feedback_v3_methodology_axis_integration_test.md`)
4. **Smoke test**: single-symbol single-month at --confirmation mode with new methodology; verify dsr_relative_b4 output
5. **Backward-compat validation**: re-run /058 + /059 with Path B4 active; record new dsr_relative_b4 values in BASELINE_V3.md as informational comparison
6. **Predicted /069 band**: dsr_relative_B4 ∈ [0.95, 1.0] at /059 anchor data (PASS at 0.95 threshold). If outside band → Path B4 methodology is suspect → fallback to Path B1/B2/B3

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at tag `v0.v3-059`. Cycle 1 EXPLORATIONs (including PASSIVE-DIAGNOSTIC) do not update BASELINE_V3.md per `feedback_v3_baseline_update_policy.md`. Only the cycle 1 CONFIRMATION at /069 (or /070) can update the baseline, and only if BOTH IS Sharpe AND OOS Sharpe improve vs /059.

## 8. Critic Recommendations carried forward

1. **iter-v3/063 = MASS FEATURE EXPANSION** (cycle 1 #4 per `feedback_v3_mass_feature_expansion.md`). V3_FEATURE_COLUMNS_TOP_N from 14 → TARGET 100 (50 minimum). QR mandated to research papers/internet/domain literature for production-grade features (TA-lib, microstructure, cross-asset, regime, statistical). Engineer pre-work should be initiated in parallel with /062 closeout.

2. **iter-v3/069 CONFIRMATION inherits Path B4 specification as BINDING pre-registration**. Adversarial flag: if /069 brief Section 2.2 doesn't reconcile the √1296 vs √3833 candle-side denominator presentational inconsistency from /062 EDA T2, that should be addressed.

3. **NEW memory rule canonicalized**: PASSIVE-DIAGNOSTIC path category (`feedback_v3_passive_diagnostic_path.md`).

## 9. Next Iteration Ideas

- **iter-v3/063** = cycle 1 #4 EXPLORATION axis = **MASS FEATURE EXPANSION** (mandate per `feedback_v3_mass_feature_expansion.md`). Target 100 features (minimum 50). QR research path: papers, TA-lib, microstructure, cross-asset, regime indicators, statistical features, engineered composed features per `feedback_v3_engineered_features_proven.md`.
- **iter-v3/064-068** = cycle 1 #5-9 TBD per cycle 1 findings; axis selection per `feedback_v3_axis_selection_quant_discipline.md` (EDA-driven QR axis selection mandatory).
- **iter-v3/069** = cycle 1 CONFIRMATION (separate slot per `feedback_v3_strict_10_to_1_cadence.md`). Inherits Path B4 spec as binding pre-registration; multi-seed (ENSEMBLE_SIZE=10) re-validation against /059 baseline (IS +1.0894 / OOS +0.5791); MERGE gate per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH IS AND OOS must improve to update BASELINE_V3.md).

## Cycle 1 progress

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (axis CLOSED) |
| **#3** | **/062** | **DSR_relative recalibration (Path C passive)** | **PASSIVE-DIAGNOSTIC (Path B4 deferred to /069)** |
| #4 | /063 | MASS FEATURE EXPANSION (target 100, min 50) | TBD |
| #5-9 | /064-068 | TBD | TBD |
| CONFIRMATION | /069 | Bundle + Path B4 implementation | TBD |
