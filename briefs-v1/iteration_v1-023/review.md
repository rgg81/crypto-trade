# Phase 7.5 Critic Review — iter-v1/023 — FINAL (post-BLOCK-PENDING-FIX)

OVERALL: EXPLORATION-NEGATIVE — F1 OOS Sharpe Δ -0.2031 maps to Section 8 Row 6 NEGATIVE clean; LEARNED-mechanism catalogued as diary sub-classifier (NOT verdict elevation)

## Iteration Type
TYPE: EXPLORATION — cycle-3 #8/10 — family `feature-family` (NEW 15th)

## Prior Verdict (Round 3)
BLOCK-PENDING-FIX — engineering_report.md ABSENT.

## Fix Applied (c9471ee)
263-line retrospective engineering report at `reports-v1/iteration_v1-023/engineering_report.md`. NO src/ changes, NO backtest re-run.

## Re-Evaluation

### Defect Axis: PASS
All 6 brief Section 10.4 items verified:
1. **Implementation summary** — funding_v1.py, V1_FEATURE_COLUMNS_PRUNED 40→42, _post_dispatch_fi_strategies refactor (/022 Rec #2 carry-forward)
2. **Backtest config** — single-seed=42, ENSEMBLE_SIZE=3, n_trials=18, 42 cols, 5 syms
3. **Wall-clock + timing** — ~58 min total; per-model breakdown present
4. **F-AXIS-MECHANISM #1-4 measurements** — DUAL GATE per-cohort table; trade counts; n_eff=9; IC pair coverage
5. **Test outputs** — 19 funding + 11 regression = 30 PASS
6. **Anomaly notes** — 5 documented (parquet regen, ic_matrix gap, RuntimeWarning, OOS trade band overshoot, spot-check)

### DUAL GATE Gain Shares Reported Correctly: PASS
Pool A 6.88%, LINK C 5.65%, LTC D 3.66%, DOT E 5.49%, portfolio 5.40%. Spot-check matches PRELIMINARY review. Portfolio above uniform parity 4.76% by +0.64pp (first NEW cycle-3 family).

### LEARNED-NEGATIVE Sub-Classifier Framing: PASS
Engineering report explicitly frames LEARNED-NEGATIVE as catalogued sub-classifier, NOT verdict elevation. Pre-registered Row 6 honored per `feedback_no_cheating.md`.

### Empirical Verdict: PASS
F1 OOS Δ -0.2031 ∈ [-0.55, -0.10) → Row 6 NEGATIVE clean. n_eff median 9 ∈ [5, 10]. Pre-registration honored.

### Check 8 Re-Check: PASS
Zero src/ changes (documentation only). Hypothesis-Implementation alignment unchanged.

### Other Checks
All Round 3 PASS verdicts carry forward unchanged (Checks 1, 2, 4, 5, 7, 13, 14). Check 3 FAIL-informational (EXPLORATION-mode degenerate). Check 6 WARN (single-seed; LTC -57.68% PnL drag documented).

## Final Verdict

**EXPLORATION-NEGATIVE.** /023 closes with NEGATIVE clean per pre-registered Section 8 Row 6. LEARNED-NEGATIVE sub-classifier (v1 LEARNS funding above uniform parity; v3 DID NOT) catalogued in diary as observational finding, NOT verdict-class elevation.

## Recommendations to QR (for /024+)

1. **Catalog LEARNED-mechanism in /023 diary + memory** — create `feedback_v1_learned_negative_subtype.md` documenting v1-vs-v3 architectural distinction (pool Model A joint loss surface ≠ v3 per-symbol). Apply LEARNED-NEGATIVE explicitly as sub-classifier in /024+ matrices.

2. **/024 axis selection** — Path Forward ordered: 
   - #1 Per-cohort drawdown brake (risk-primitive, brief pre-commit)
   - #2 Regime-conditional sub-models (model-arch, LM Master + user directive)
   - #3 Open-interest delta (feature-family REPEAT, borderline rotation)

3. **Orchestrator-layer engineering_report dispatch gate** — 5th cycle-3 incident. Skill-maintainer scope; pre-Phase-7.5 existence check needed.

## Path Forward (for /024 axis selection)

Three candidates honoring axis-rotation discipline:

1. **Per-cohort drawdown brake** — family `risk-primitive` — STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054. Brief Section 11.4 pre-committed default.

2. **Regime-conditional sub-models** — family `model-arch` — Train 2 sub-models per cohort (|funding_z30|>1.5 vs ≤1.5); STATELESS regime gate. DUAL GATE evidence supports 3/4 cohorts. HIGH-RISK MANDATORY.

3. **Open-interest delta family** — `feature-family` REPEAT — non-OHLCV, non-funding sister primitive. Borderline rotation but Section 11.7 permits.

QR Phase 8 selects.
