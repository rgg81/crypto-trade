# Phase 5.5 Gate — iter-v3/008

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` present (two-space alignment in code block), `training_months = 24` confirmed UNCHANGED. IS window named as `[listing-date floor 2022-09-24, 2025-03-23 23:59:59 UTC]`; OOS window named as `[2025-03-24 00:00:00 UTC, data-extent]`. Walk-forward unit (monthly retrain, 24-month rolling, 1-month OOS window) UNCHANGED. `ENSEMBLE_SIZE=5`, `n_trials=50`, Optuna-sampled `colsample_bytree` declared as PRODUCTION config (no `--exploration`).
- Section 0.5 (Iteration Type Declaration): PASS — `TYPE: CONFIRMATION` declared in first line. Justification paragraph names iter-v3/007 `EXPLORATION-PROMISING` per Critic FINAL SHA `a544621` as the forwarded result. Mechanical threshold table (IS Sharpe > 0.5, OOS Sharpe > 1.0, OOS/IS ≥ 0.5, PBO < 0.4, DSR > 0.95, PSR > 0.95, concentration ≤ 30%) is inline in Section 0.5 with explicit "no discretion" statement. All three Critic FINAL pre-conditions addressed by reference.
- Section 1 (Hypothesis): PASS — single sentence: drops `vwap_dev_50` (14 → 13 features) on full v3 universe at production config (`--seeds 5 --n-trials 50`) and targets IS monthly Sharpe > +0.5 AND OOS monthly Sharpe > +1.0. Mechanism stated (redundancy removal + full-ensemble variance reduction). Not vague.
- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v3-008/ic_redundancy_drop_demo.py` at SHA `003a21e` (2026-05-06 03:12:56 +0200), which predates the brief at SHA `f2c0ece` (2026-05-06 03:19:18 +0200). Five output artifacts committed alongside script. Script reads ONLY `reports-v3/iteration_v3-007/ic_matrix.csv` (IS-only matrix — no OOS contact). Tables in §2.1–2.3 are numerically consistent with the committed artifacts: two redundant pairs (`vwap_dev_50 × ema_spread_atr_20 = 0.8746`, `vwap_dev_50 × vwap_dev_20 = 0.7938`); 13-feature retained subset has max off-diagonal |IC| = 0.6602 (verified independently against `ic_matrix_13.csv`); zero residual pairs above 0.70 threshold confirmed.
- Section 3 (Proposed Changes): PASS — symbols UNCHANGED (BCH+MKR+LDO+TRX; disjoint from `V3_EXCLUDED_SYMBOLS` stated). Labeling UNCHANGED (triple-barrier ATR-scaled, timeout=21 candles, gap=88). Features REDUCED 14 → 13 with `vwap_dev_50` explicitly named as the drop. Risk gates UNCHANGED (7-primitive table carried). Three sub-fixes decomposed in §3.5 with per-fix specs and verifier commands. Section 3.6 reconciliation table has 15 rows each with code path, file artifact, and executable verifier — zero empty cells. Rows 7–10 are designated as mechanical Section 8 enforcers. Inheritance plan in §3.8 names three precondition tests (`test_outer_seed_propagation.py`, `test_per_cell_pbo_synthetic.py`, `test_ensemble_seed_propagation.py`). One variable at a time: only `V3_FEATURE_COLUMNS_TOP_N` contents change.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe range [+0.4, +0.9] with median +0.6; OOS Sharpe range [+0.5, +1.5]. Six falsifiers pre-registered (§4.3): four mechanical (falsifiers 1–4 map to Section 8 rows 3, 4, 6, 10) and two process-level (falsifiers 5–6). CONFIRMATION pathway (all 12 criteria must pass) enumerated in §4.4. MERGE prior probability pre-registered as ~15%.
- Section 5 (Risk Mitigation): PASS — three NEW structural safeguards in §5.1 explicitly address Critic FINAL Recommendations 1 (drop `vwap_dev_50`), 2 (mechanical Section 8 thresholds, no escape hatch), and 3 (per-symbol concentration ≤ 30% as mechanical gate). Three methodology-pipeline safeguards in §5.2 (35 adversarial tests, reconciliation table, pre-flight len/name-check). Concentration gate detail in §5.4 includes tightening rule for iter-v3/009 if gate fires.
- Section 6 (Risk Management Design): PASS — 7-primitive table identical to iter-v3/006–007 with fire-rate predictions and regime coverage. Gate-feature-column independence argued in §6.1: `atr_pct_rank_200` dropped from `V3_FEATURE_COLUMNS_TOP_N` but gates read parquet directly via the iter-v3/007 fix at SHA `849c4a6`. `vwap_dev_50` confirmed as NOT a gate input, so the drop has zero gate side effects. Engineer pre-flight step 5 added to re-verify.
- Section 7 (Failure-Mode Prediction): PASS — 5 predictions: 3 process-level (P1: hardcoded-14 downstream breakage, P2: wall-clock overshoot, P3: BCH concentration blocks good run) and 2 model-level (P4: IS Sharpe stays ≤ +0.4, P5: IS Sharpe lifts but OOS fails). Minimum of ≥3 process-level predictions met. Each prediction names a detection signal and mitigation. Bayesian-calibrated priors with explicit MERGE pathway probability ≈ 15%.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 12 CONFIRMATION criteria enumerated in table. Explicit CONFIRMATION-MERGE / CONFIRMATION-NO-MERGE / NO-MERGE-PROCESS pathways. IS Sharpe > 0.5, OOS Sharpe > 1.0, OOS/IS ratio ≥ 0.5, PBO < 0.4, DSR > 0.95, PSR > 0.95, and concentration ≤ 30% are all present as mechanical thresholds. Explicit "NO discretionary judgment permitted" clause per Critic FINAL Rec 2.
- Section 9 (Library Stack): PASS — eight packages declared (numpy, scipy, statsmodels, scikit-learn, lightgbm, pytest, pandas, pyarrow) with license, usage, and fallback columns. No new external dependencies. Aggregator strategy UNCHANGED from iter-v3/006–007. Reproducibility stamp spec includes git SHAs, library versions, 13-feature list, wall-clock minutes, and mechanical Section 8 PASS/FAIL grid.

## CONFIRMATION Pre-Conditions Audit (Critic FINAL SHA a544621)

**Pre-condition 1 (IC redundancy — Critic Rec 1)**: PASS
- Section 3.3 specifies dropping `vwap_dev_50` (14 → 13 features). Section 2.3 confirms maximum off-diagonal |IC| in the 13-feature subset = 0.6602, headroom +0.0398. Zero residual pairs above 0.70. Verified independently against committed `ic_matrix_13.csv` artifact.

**Pre-condition 2 (Mechanical thresholds — Critic Rec 2)**: PASS
- Section 8 lists IS Sharpe > 0.5, OOS Sharpe > 1.0, OOS/IS ≥ 0.5, PBO < 0.4, DSR > 0.95, PSR > 0.95 as mechanical gates. Section 3.6 rows 7–10 are executable verifiers. Section 0.5 table states these inline. Explicit "NO discretionary judgment permitted" clause present.

**Pre-condition 3 (Per-symbol concentration — Critic Rec 3)**: PASS
- Section 8 criterion 10: per-symbol max concentration ≤ 30% of OOS PnL as mechanical NO-MERGE gate. Section 3.6 row 10 is an executable verifier. Section 5.4 details the gate semantics and tightening rule for iter-v3/009 if the gate fires on iter-v3/008.

## Section 3.6 Reconciliation Cells Status

All 15 rows have non-empty code paths, file artifacts, and executable verifier commands. Rows 7–10 are designated as mechanical Section 8 enforcers (non-zero exit = NO-MERGE). Zero prose-only rows. PASS.

## Commit-Ordering Audit

- SHA `003a21e` (analysis script + 5 artifacts, 2026-05-06 03:12:56) precedes brief SHA `f2c0ece` (2026-05-06 03:19:18) by 6 minutes 22 seconds. Phase 5.5 reproducibility requirement SATISFIED.
- Critic FINAL SHA `a544621` (2026-05-06 03:03:48) predates analysis and brief: CONFIRMED.

## Pre-Phase-6 Preconditions (Engineer must verify before code edits)

1. `uv run pytest tests/strategies/ml/ -v` → 35/35 PASS at HEAD (inherited from iter-v3/007 at SHA `849c4a6`)
2. `git log --oneline iteration-v3/008 -- run_baseline_v3.py | wc -l` ≥ 3 (iter-v3/006 + iter-v3/007 commits)
3. `test -f tests/strategies/ml/test_outer_seed_propagation.py` exists
4. `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` exists
5. `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` exists
6. Pre-flight: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0 (post sub-fix #1 only)
7. Gate-feature independence check: confirm `risk_v3.py:_build_lookups()` still loads `atr_pct_rank_200` independently of `V3_FEATURE_COLUMNS`. Confirm `vwap_dev_50` is NOT a gate input. Verify the risk_v3 fix at SHA `849c4a6` is present on this branch.

## Reasons

None — OVERALL is PASS.
