# Phase 7.5 Critic Review — iter-v1/021 — FINAL (post-BLOCK-PENDING-FIX)

OVERALL: EXPLORATION-PROMISING-METHODOLOGY — H1 CONFIRMED BORDERLINE × H2 REFUTED (joint cell row 3 — "Pool-conferred edge despite same features; basin-level interaction effect")

## Iteration Type
TYPE: EXPLORATION — cycle-3 #6 of 10 — METHODOLOGY PIVOT subtype (diagnostic)

## Prior Verdict (Round 3)
OVERALL: BLOCK-PENDING-FIX — Pool Model_A feature_importance write defect rendered H2 falsifier non-evaluable.

## Fix Applied (commit 502d66e)

- **Defect**: `_write_feature_importance` read stale `_strat_a.inner._models` post-dispatch (re-assigned each walk-forward month at `lgbm.py:723`).
- **Fix**: Added `_per_month_fi_log` accumulator in `lgbm.py:303` populated in `_train_for_month` lines 797-800; `run_baseline_v1.py:573-599` reads from accumulator with empty-state defensive warning.
- **Tests**: 4-test `TestPerMonthFILog` class added; 23/23 pass.
- **New artifacts**: `feature_importance_POOL_Model_A.csv` total_gain=49,699 (was 0); `feature_importance_BTC_Model_H.csv` total_gain=46,517 (unchanged).
- **Headline determinism**: IS Sharpe -0.8313 / OOS Sharpe +0.3338 UNCHANGED → params_persist_path + per_month_fi_log are true no-ops on Optuna training-objective domain.

## H2 Falsifier Evaluation (Brief Section 4.2)

| Top-5 comparison | Pool A rank | BTC H rank |
|---|---|---|
| vol_atr_14 | 1 | 2 |
| trend_aroon_osc_50 | 2 | 1 |
| stat_autocorr_lag5 | 3 | 5 |
| stat_kurtosis_20 | 4 | 10 |
| mom_macd_line_12_26_9 | 5 | 8 |

Σd² across all 40 features = 588.

**Spearman ρ = 1 − 6·588 / (40·1599) = 0.9448**

Per brief Section 4.2: ρ > 0.8 → **DIAGNOSTIC-REFUTED-H2**. Same features dominate per cohort — NO cohort signature divergence at feature-importance granularity. Top-2 bit-identical (just rank-swapped). Bottom-2 bit-identical. Only middle-rank features drift (stat_skew_20, vol_bb_bandwidth_20, vol_taker_buy_ratio).

## Joint H1 × H2 Verdict (Brief Section 4.3 — 9-cell matrix)

| Axis | Verdict | Evidence |
|---|---|---|
| H1 | CONFIRMED BORDERLINE | 4/10 params shifted on ≥50% months; 1/4 key params; HIGH-CONFIDENCE gate NOT met |
| H2 | REFUTED | Spearman ρ = 0.9448 |

**Joint cell** = row 3: **CONFIRMED × REFUTED** → "Pool-conferred edge despite same features — basin-level interaction effect."

Per Section 11.7 routing table row 4 (BORDERLINE × REFUTED): **/022 = LTC-only + orthogonal mechanism; /023 = DOT-only similar**. Cadence preserved (/027 at end of cycle-3).

## Per-Check Status (Re-evaluation post-fix)

### Check 1 — Look-Ahead Audit (re-verified): PASS
Foundation embargo invariant at `walk_forward.py:113` intact. Fix touches `lgbm.py:303,797-800` (accumulator) + `run_baseline_v1.py:573-599` (read path). NEITHER touches boundary logic, label generation, or feature computation.

### Check 13 — Anti-Pattern Static Scan (re-scanned fix diff): PASS
- A1 clean. A5, A7, A8, A12, A13 unaffected. Empty-state warning logic at `run_baseline_v1.py:592-599` forestalls recurrence of /021 defect class.

### Check 8 — Hypothesis-Implementation Alignment (post-fix): PASS
Fix preserves `importance_type='gain'` (matches v3 convention). DIVERGENCE from brief Section 3.2 last-month convention → per-month aggregate. Methodologically STRICTLY BETTER (n=53 IS months × averaging vs n=1). No scope creep.

### Engineering Report Presence: PASS
`engineering_report.md` committed at `502d66e`. **3-strike cycle-3 incident RESOLVED**.

### Other Checks (carry-forward PASS unchanged)
- Check 2 (Embargo Width): PASS
- Check 3 (Multiple-Testing): FAIL informational only (EXPLORATION-mode DSR/PSR artifacts)
- Check 4 (IC Correlation): PASS (vacuous)
- Check 5 (ADF Stationarity): PASS
- Check 6 (Pareto Dominance): N/A
- Check 7 (Reproducibility): PASS — HEAD `26e9473`
- Check 14 (Axis Family Validation): PASS — `methodology-pivot` purely additive instrumentation

## Structural Finding (load-bearing for cycle-3+)

**Cohort isolation successes at /018 LINK and /019 ETH+gate were NOT explained by feature-level specialization (ρ=0.9448 across 40 features between Pool BTC-slice and BTC-only Model H).** The H2 refutation means future per-cohort axes CANNOT rely on "this cohort needs different features" as a mechanism story. Cohort-isolation effects must be attributed to **parameter-basin level interaction** (max_depth × subsample × reg_lambda interaction with label distribution per cohort), NOT feature-shift.

This explains the /020 catastrophic failure: BTC-only isolation moved to a DIFFERENT parameter basin (4/10 hyperparams shifted on ≥50% months — H1 CONFIRMED BORDERLINE), and the new basin sampled a structurally adverse OOS trade subset. The mechanism is basin-relocation under universe composition change, not feature-rediscovery.

## /022 Routing Recommendation

Per brief Section 11.7 row 6 (BORDERLINE × REFUTED): **/022 = LTC-only specialization + orthogonal mechanism**; /023 = DOT-only similar; /027 at end of cycle-3.

**/022 brief MUST**:
1. Pre-classify LTC prior class (POSITIVE_EVERYWHERE / NEGATIVE_EVERYWHERE / ASYMMETRIC_ROTATION) using baseline per-month BTC-slice analogue analysis.
2. Frame H2 REFUTED as SUBSTANTIVE prior — cohort-isolation effects must be attributed to basin-shift, not feature-shift.
3. If LTC is ASYMMETRIC_ROTATION (like BTC), orthogonal mechanism (gate / risk-primitive) is REQUIRED (mirror /019 ETH+BTC-trend-gate pattern). If POSITIVE_EVERYWHERE (like LINK), isolation alone may suffice.

## Recommendations to QR

1. **/022 brief Section 0.4** — pre-classify LTC prior class.
2. **/022 brief Section 4** — frame H2 REFUTED as substantive prior; mechanism stories MUST be at parameter-basin level not feature-level.
3. **Per-month FI accumulation now on trunk** — methodologically superior to v3's last-month-snapshot. Update `feedback_v1_methodology_probe_discipline.md` to reflect new convention. Consider v3 backport.

## Cycle-3 Cadence Status (post-/021)

- /021 closes as 6th of 10 cycle-3 EXPLORATIONs.
- /022, /023, /024, /025 remain before /027 CONFIRMATION.
- Cycle-3 ledger: 2 PROMISING (LINK /018 + ETH+gate /019) + 1 PROMISING-METHODOLOGY (/021) / 3 NEGATIVE (sample-weighting /016 + universe /017 + BTC-only /020) / 0 merges.
- /027 bundle architecture pre-committed to Option β (FULL POOL + specialists as alpha-enhancement; LM Master Rec #7 ADOPTED).

## BLOCK-PENDING-FIX Protocol — RESOLVED

N/A — verdict is PASS. /021 closes EXPLORATION-PROMISING-METHODOLOGY with substantive structural finding for cycle-3 /022+ direction.
