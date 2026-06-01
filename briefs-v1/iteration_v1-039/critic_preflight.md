# Phase 6.0 Critic Pre-Flight — iter-v1/039 (RETRY)

OVERALL: PASS

## Pre-Flight Checks

### Check A (mini) — Brief Look-Ahead Audit: PASS
Brief Section 3 specifies NO new src/ code. Composition reuses /035 trend_scanning + /037 Sortino + /036 2-cohort dispatch, all production-shipped. Section 3.3 anchors training_months=24, OOS_CUTOFF=2025-03-24. Section 10 self-check confirms IS-only EDA. No forward-window descriptions in feature plan.

### Check B (mini) — Anti-Pattern Static Scan on QE's src/ diff: PASS
Diff localized to `run_baseline_v1.py:4035-4140` (dispatch elif) + `src/crypto_trade/features_v1/__init__.py:230` (V1_ITER039_UNIVERSE constant) + catch-all exclusion at line 4157. Grep for A1 (`train_end_ms = test_start_ms` without subtraction), A2 (forward-window std), A3 (combined fit_transform): zero matches. A12/A13: not applicable (no methodology axis added). Dispatch enforces 4 pre-flight asserts (label_mode/optuna_objective/universe/vol_ceiling).

### Check C — Foundation Regression: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` unchanged. Regression test `test_v1_039_walk_forward_embargo_regression` codifies the exact-string check.

### Check D — Cadence + Axis Sanity: PASS
Phase 5.5 OVERALL=PASS confirmed. Section 0.6 declares `loss-function × per-cohort-specialization` DOUBLE-REPEAT COMBO with explicit stacking-interaction justification (counter 2/5 each axis, 5+ rule not violated; prior 5 EXPLORATIONs disperse across 5 distinct families). Section 2.5 HIGH-RISK declared per rotation rule + NORMAL-RISK by mechanism + SINGLE-SEED counter 1/3.

### Check E — Falsifier Presence: PASS
Section 11.6 locks numerical thresholds (PROMISING-CLEAN OOS Δ vs /036 ≥ +0.10; NEG-CLEAN ∈ [-0.45, -0.20); NEG-CAT < -0.45). Section 4 F-AXIS #1-#7 explicit. Section 9 falsifier triggers list 4 BLOCK-PENDING-FIX conditions.

### Check F — Process Integrity (BLOCK→PASS justification): PASS
`lgbm_advisor.md` line 1 header reads "Phase 4.5 (Pre-Design, RETARGETED AXIS)" — reissue confirmed. All 4 prior BLOCK reasons remediated: Section 11 (7-row LM Master response map), Section 11.5 (Pre-Registered Failure-Mode Prediction), Section 11.6 (Locked Numerical MERGE/NO-MERGE Thresholds), Section 11.7 (Library Stack Declaration — standard stack only). Transition is genuine remediation.

### Check K — Axis Family Validation (double-REPEAT 2/5 counter): PASS
Counter at 2/5 for both `loss-function` (last /037, 1 iter ago) and `per-cohort-specialization` (last /036, 2 iters ago). Justified as direct compoundability test of two PROMISING axes (not knob-tuning monoculture). 5+ rule cleanly clear.

### Check L — Implementation/Hypothesis Alignment: PASS
Dispatch at `run_baseline_v1.py:4035-4140` matches brief Section 3.1 verbatim: 4 pre-flight asserts (label_mode/optuna_objective/universe/vol_ceiling), banner with both axes visible, Model C' LINK-only + Model E DOT-only, per-cohort isolation post-asserts, catch-all exclusion at 4157. Test file 13 + 1 foundation = 14 tests covering all wiring assertions.

## Approved Launch Invocation

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --symbols LINKUSDT,DOTUSDT \
  --label-mode trend_scanning \
  --optuna-objective sortino \
  --pruned-features \
  --iteration 39 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  > logs/iter_v1_039_backtest.log 2>&1
```
Phase 6 backtest cleared to launch.
