# Phase 7.5 Critic Review — iter-v3/130

OVERALL: EXPLORATION-NEGATIVE-catastrophic — Criterion 1 fires IS Sharpe −1.3028 < +0.91 (Δ −2.61 vs /121 — WORST IS in v3 history); production IS observation 8.4σ below T3b 4h-proxy simulator predicted mean (0.391±0.20); BAR-INTERVAL axis CLOSED for cycle-7; /121 architecture confirmed cohort-AND-frequency-shaped.

## Iteration Type
TYPE: EXPLORATION (cycle-7 slot #9 of 10; BAR-INTERVAL axis class; 4h base candles)

## QR Response Considered (Round 2 only)
N/A — single-round emit FINAL. Zero clarifications: brief Section 8 first-match-wins C1 fires unambiguously; production IS 8.4σ below T3b 4h-proxy simulator predicted mean exactly confirms brief Section 2 + Section 10 pre-disclosed proxy limitation. No QR response can override pre-registered C1 fire at this magnitude.

## Per-Check Status

### Check 1 — Look-Ahead: PASS
ZERO new features. 14-feature stack UNCHANGED from /121-canonical. Bar-interval discretization only.

### Check 2 — Embargo: PASS
REQUIRED_GAP=66=(21+1)×3 in candle-count terms (Lopez de Prado purge is candle-count-based). /058 walk-forward fix preserved.

### Check 3 — Multiple-Testing: FAIL informational (EXPLORATION)
PBO 0.0978 PASS (trivially — IS doesn't outperform OOS when IS is catastrophic). DSR=0 degenerate. PSR 0.9999 PASS misleading (formula doesn't consult IS magnitude). frac_pos 0.600 PASS. Per EXPLORATION protocol non-BLOCK.

### Check 4 — IC: PASS (carry-forward)

### Check 5 — ADF: PASS

### Check 6 — Pareto: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
Setup `e77e2b6`. **run.log PERSISTS at `reports-v3/iteration_v3-130/run.log` — 5-occurrence instrumentation gap FIXED via `_TeeLogger` wrap.** Feature columns explicit. Trade math verified.

### Check 8 — Hypothesis-Implementation: PASS
Brief Section 1 disjunction "lift OR falsify" — falsification branch fires unambiguously at C1.

## Mechanism Forensic Summary

T3b 4h-proxy simulator predicted IS mean 0.391 ± 0.20. Production IS = **−1.3028 is 8.4σ below predicted mean** — far outside ±3σ prediction band. Brief Section 2 pre-disclosed exactly this outcome: "bootstrap upsampling of /121's 8h trade roster cannot capture Optuna's response to actual 4h-density training (different (depth, colsample, reg_lambda) search regions that trade-level resampling cannot reproduce)."

The simulator methodology IS OPERATIONALLY VALIDATED — gave HIGH-RISK signal at G1 (frac ≥ 0.91 = 0.0%). **Simulator was RIGHT that axis was unfavorable; wrong only about magnitude — predicting flat where production produced catastrophic collapse.**

**Cohort-AND-frequency-shape finding (TERMINAL for cycle-7)**: at 4h, the same lookback windows cover halved absolute time. The 14-feature stack was implicitly calibrated for 8h periodicity. Optuna at 4h-density explored a qualitatively different region producing ANTI-predictive 32% WR signals against (2.0, 1.0)-ATR structure (breakeven WR = 66.7%). /121 architecture is cohort-AND-frequency-shaped — changing EITHER the symbol set OR the bar interval destroys its IS behavior.

This is the THIRD axis class category (RISK-PRIMITIVE binary at /127, UNIVERSE at /128, RISK-PRIMITIVE continuous at /129, BAR-INTERVAL at /130) where /121's architecture proves fragile to perturbation. **/121's lift is not a generalizable mechanism — it is a hyperparameter-region-locked solution at the specific (3-symbol cohort, 8h bar interval, 14-feature stack) combination.**

## Cycle-7 State

**9/9 NEGATIVE consecutive** (1 INERT + 8 catastrophic incl. /130). Cycle structurally exhausted on declared axis menu. PROMISING-class prior probability at /131 empirically depressed to ~5-10%.

## Recommendations to QR

1. **/131 = formal cycle-7 closure-reconciliation diary, NOT EXPLORATION axis.** 9/9 NEGATIVE with last four (/127-/130) catastrophic across structurally distinct axis classes. Cohort-AND-frequency-shape finding is terminal. /131 documents the finding as structural feedback memo + prepares /132 CONFIRMATION baseline-re-validation spec. 10:1 cadence rule does NOT require slot #10 to be EXPLORATION on new axis — closure-reconciliation pre-CONFIRMATION is valid.

2. **/132 CONFIRMATION = MULTI-SEED VALIDATION of /121-canonical, NOT bundle assembly.** Cycle-7 produced no ingredient for accretion. /132 spec: default CONFIRMATION mode (ENSEMBLE_SIZE=10), n_trials=35, bit-identical to /121 architecture (BCH/LDO/TRX, 14-feature stack, ATR (2.0,1.0), 7-gate RiskV2 with /127+/129 disabled, K=21 at 8h). Acceptance: multi-seed mean IS ≥ +1.0 AND OOS ≥ +0.8 (loose tolerance vs /121 +1.31/+0.97 for code-state drift). If reproduces, BASELINE_V3.md UNCHANGED at /121. If fails, file CONFIRMATION-RE-ANCHOR diary.

3. **Cycle-8 axis menu must structurally reformulate post-/132.** Cohort-AND-frequency-shape is terminal finding (analogous to /105-/109 representational-capacity FALSIFICATION). Cycle-8 should NOT propose further axes in /121's parameter neighborhood. Pivot to: (a) WHOLLY-NEW model architecture, (b) WHOLLY-NEW labeling architecture, or (c) explicit acknowledgment /121 is practical edge ceiling and pivot research workflow. At minimum, cycle-8 first EXPLORATION brief must include Section 0.6 "Architecture-Family Justification" arguing why proposed axis is NOT in cohort-shape OR frequency-shape OR Optuna-trajectory-shift channel families.

## Clarifications Requested from QR — NONE
