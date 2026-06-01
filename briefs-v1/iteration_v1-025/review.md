# Phase 7.5 Critic Review — iter-v1/025 — FINAL (post-BLOCK-PENDING-FIX)

OVERALL: EXPLORATION-NEGATIVE-CATASTROPHIC (LEARNED-NEGATIVE-CATASTROPHIC subtype)

## Iteration Type
TYPE: EXPLORATION (cycle-3 #10/10 — LAST before /027 CONFIRMATION)

## Prior Verdict (Round 3)
BLOCK-PENDING-FIX — engineering_report.md + 4 mandated CSV deliverables missing (6th cycle-3 incident)

## Fix Applied (449ab6e)

5 artifacts committed. NO backtest re-run.

1. `briefs-v1/iteration_v1-025/engineering_report.md` — 11 sections, Section 10.4 8-item template
2. `reports-v1/iteration_v1-025/oi_coverage_check.csv` — 5/5 PASS HARD BLOCK
3. `reports-v1/iteration_v1-025/in_sample/feature_importance_per_fold.csv` — DEFERRED with documented reason (runner doesn't emit per-fold; aggregate ranks documented)
4. `reports-v1/iteration_v1-025/out_of_sample/oos_ic_matrix.csv` — Spearman IC(oi, funding_30)=0.117, IC(oi, funding_90)=0.202; both << 0.5 PASS
5. `reports-v1/iteration_v1-025/oracle_q4_oos_attribution.csv` — 5-quintile trade attribution

**Critical correction from #5**: LM Master Phase 7.4 §1(B) claim of Q1 OOS -30.78 sign-flip was INCORRECT. Actual:
- Q1 +24.63 (POSITIVE, no sign-flip) / 46 trades
- Q3 mid -57.44 / 55 trades ← DOMINANT loss channel
- Q5 -54.84 / 52 trades
- Q4 ORACLE +25.97 / 44 trades / 43.2% WR — SURVIVED as LM noted

Mechanism: realized-trade attribution differs from distribution-level Sharpe-proxy. EDA must be discounted ~50% for non-trade-attributed bands.

## Re-Evaluation

### Defect Axis: PASS
All 5 artifacts at correct paths. Engineering report complete; 4 CSVs present (or DEFERRED with valid reason).

### Check 8 Re-Check: PASS
NO scope creep. Pure documentation; no src/ changes. Hypothesis-implementation unchanged.

### Other Checks
All PRELIMINARY PASS verdicts carry forward unchanged.

## Final Verdict Rationale

Empirical outcome LOCKED:
- **F1 OOS Δ = -1.40** → NEGATIVE-CATASTROPHIC per Section 8 Row 7 (≤ -0.55)
- F-AXIS #1 DUAL GATE PASS 4/4 cohorts (OI rank 4-5, gain 6.4-8.0%); per pre-registered hierarchy F1 magnitude OVERRIDES
- Classification: **LEARNED-NEGATIVE-CATASTROPHIC** (NEW v1 subtype — feature learned above parity AND OOS catastrophic; not in catalog before /025)
- Companion to /023 LEARNED-NEGATIVE-clean (Δ -0.20); /025 amplifies pattern at rank-4 basin-pull

**/023 + /025 n=2 STRUCTURAL VERDICT established**: NEW feature families ADDED TO POOL MODEL A at single-seed n_trials=18 EXPLORATION budget = STRUCTURALLY LEARNED-NEGATIVE.

## Recommendations to QR

1. **Phase 5.5 gate checklist** must cross-reference Section 10.4 artifacts as literal path checklist. 6th cycle-3 incident is structural not random.

2. **Per-fold importance logging** — add `feature_importance_per_fold_*.csv` emission to runner.

3. **ORACLE EDA pivot** — brief Phase 1-2 should require BOTH distribution-level Sharpe-proxy AND post-hoc IS-trade-attribution Q-band PnL projection.

## /027 BUNDLE LOCKED

Per LM Master §4:
1. BASELINE_V1 pool (FROZEN, 14-feature anchor; NO new features)
2. LINK specialist +0.80 OOS Δ
3. ETH+gate specialist +0.50 OOS Δ

EXCLUDED with mechanism evidence: OI delta (/025 LEARNED-NEG-CAT), funding rate (/023 LEARNED-NEG), regime-conditional (/024 non-specialization).

Multi-seed mandate: `--seeds 2`, `n_trials=35`, cross-corr pre-validation MANDATORY (Pearson(pool×LINK) < 0.50 AND Pearson(pool×ETH+gate) < 0.50).

Target: **+1.10 to +1.30 OOS Sharpe at multi-seed**.

## Path Forward (cycle-4 axis candidates, post-/027)

3 candidates from NON-recent families:

1. **DOT/LTC-specialist with NEW risk gate** — `per-cohort-specialization` (extend LINK/ETH+gate proven architecture). Avoid Pool A joint-loss-surface trap.

2. **Sample-weighting** — `sample-weighting` UNUSED cycle-3. AFML Ch.4 inverse-concurrency + sample-uniqueness. Mechanism: reduce basin formation around overlapping windows.

3. **XGBoost head-to-head with regularized leaf size** — `model-arch` REPEAT (different instance vs /024 partition). Level-wise growth + min_child_weight + reg_alpha NOT tested in /024.

## Cycle-3 EXPLORATIONs COMPLETE (10/10)

Final ledger:
- 2 PROMISING: /018 LINK +0.80, /019 ETH+gate +0.50
- 1 PROMISING-METHODOLOGY: /021 H2 REFUTED basin-interaction
- 7 NEGATIVE: /016, /017, /020 NEG-CAT, /022 NEG-CAT, /023 LEARNED-NEG, /024 regime non-specialization, /025 LEARNED-NEG-CAT

/027 CONFIRMATION ready. NO further EXPLORATION before /027.
