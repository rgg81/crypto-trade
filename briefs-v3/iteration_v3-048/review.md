# Phase 7.5 Critic Review — iter-v3/048

OVERALL: **EXPLORATION-NEGATIVE — clean PATH C** (IS Δ -0.43 < -0.10 AND OOS Δ -3.15 < -0.30 vs iter-v3/045 single-seed anchor; pre-registered Section 8 thresholds fire unambiguously); NEW universal engineered feature axis CLOSED for cycle 3 per saturation rule (5 attempts: iter-v3/035, /041 pruning, /043 efficiency_ratio, /044 reverted, /048). Material side-finding: iter-v3/047's "multi-run-stochasticity-contaminated" subtype attribution is FALSIFIED by iter-v3/048 single-process-clean evidence; memory rule revision recommended.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 3 #9 of 10; QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`)

## QR Response Considered (Round 2)

This iteration was dispatched as a single-round adversarial review (no PRELIMINARY-mode clarifications requested by orchestrator). All 8 + 4 optional checks were resolved on first read of the brief, engineering report, IC matrix, ADF table, importance CSVs, and source. No QR round-trip needed: the QE engineering report at SHA `a068edd` already addresses the iter-v3/047 misdiagnosis forensically (Section "n_trials=700 Investigation"), and the PATH C-clean firing is unambiguous on the locked Section 8 thresholds.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Single new function `compute_vol_normalized_ret_5d` in `engineered_v3.py:439-487`. Construction: `ret_5d = log(close) - log(close.shift(15))` (15 bars at 8h = 5 days; strictly past-only via shift), divided by `range_realized_vol_50` (which is itself past-only per `add_tail_risk_v3_features`; rolling 50-bar window terminating at `t-1`). The new feature at bar `t` uses only `close[t-15..t]` and `range_realized_vol_50[t]` (which depends on bars `t-50..t-1`). No future leakage. Test 1 (`test_vol_normalized_ret_5d_past_only_discipline`) explicitly verifies that appending a future bar does NOT alter prior-bar values — passes at setup commit `c69fdaa`. Brief Section 3 Sub-fix 1 docstring matches implementation byte-for-byte. PASS.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 88 = (timeout_candles 21 + 1) × n_symbols 4. Unchanged from iter-v3/034 onward. timeout_minutes = 7 days × 24h × 60min / 8h-cadence = 21 candles. López de Prado purge formula correctly applied in `validation_v3.py`. iter-v3/048 introduces no changes to the gap parameter; the new feature does not alter labeling horizon. PASS unchanged from iter-v3/045/047.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION; does NOT trigger BLOCK)
DSR = 0.000 (gate would be 0.95). PSR = 0.9971 (PASSES gate 0.95). PBO = 0.1339 (PASSES gate 0.4). n_trials = 700 = 4 syms × 5 ensemble × 35 trials per ensemble (CORRECT structural count for ENSEMBLE_SIZE=5; QE forensic Section "n_trials=700 Investigation" verifies 5x duplication is SCHEMA-driven not contamination — `optimization.py:425-430` writes per-ensemble-seed rows to a parquet with no `seed` column, producing 5 identical `(trial_id, ...)` namespaces). n_eff = 18 (acceptable; ≥10 floor). DSR=0 reflects E[max_SR] denominator inflated by N=700; per `feedback_v3_dsr_mode_artifact.md` EXPLORATION-mode DSR is INFORMATIONAL ONLY and does NOT trigger BLOCK. The PBO axis (only Check-3 axis with BLOCK power for EXPLORATION) PASSES at 0.1339. Per CONFIRMATION rule, all three axes would need to pass; this iteration is EXPLORATION, so Check 3 does not BLOCK.

### Check 4 — IC Correlation: FAIL strict-gate (|IC|<0.7 violated on 2 pairs); PASS engineered-feature carve-out
Per `ic_matrix.csv` row 16 (vol_normalized_ret_5d), the new feature shares the following pairwise Pearson correlations with EXISTING features in V3_FEATURE_COLUMNS_TOP_N:
- `regime_momentum_signed_5d`: **0.892** (BREACH; gate is 0.7)
- `vwap_dev_20`: **0.888** (BREACH; gate is 0.7)
- `ema_spread_atr_20`: 0.670 (within gate, marginal)
- `sym_vs_btc_ret_7d`: 0.537
- `btc_ret_14d`: 0.352
- `ret_skew_50`: 0.231

Two |IC| ≥ 0.7 pairs would normally trigger automatic FAIL. However, brief Section 2.7 + `feedback_v3_engineered_feature_pivot.md` (established iter-v3/025 closeout) explicitly carve-out Category 2 composed features from the |IC|<0.5/0.7 gate: composed features like `ret_5d / (range_realized_vol_50 + ε)` MECHANICALLY correlate with their primitives, and the high IC with `regime_momentum_signed_5d` (which is `ret_5d × sign(hurst_100 - 0.5)`) reflects shared `ret_5d` numerator — by construction. The binding gate per the carve-out is **importance ≥30 in at least 2 of 4 symbols**: vol_normalized_ret_5d hits 53/56/82/97 importance for BCH/LDO/TRX/ALGO, all > 30 — Falsifier 4 PASSES the relaxed gate. The high IC=0.892 with regime_momentum_signed_5d does, however, OBJECTIVELY answer one diagnostic question: the two engineered features are near-collinear in the feature space, and LightGBM's depth-3-5 trees see them as redundant (importance ranks 13-15/15 across all symbols — confirmed). Carve-out PASS; collinearity-redundancy hypothesis SUPPORTED by the importance data.

### Check 5 — ADF Stationarity: PASS
`adf_test.csv` reports vol_normalized_ret_5d ADF p-value < 0.05 in essentially every monthly window after the warmup period: BCH stationary 2020-05+ onward (p<0.05); LDO stationary 2022-12+ onward; TRX stationary 2020-04+ onward; ALGO stationary 2020-12+ onward. Pre-warmup NaN entries (first 1-2 months per symbol) are mechanical (50-bar realized-vol denominator + 15-bar return-numerator warmup). The training window IS=2023-03-24 onward, so all training bars are well past warmup. By IS-window start, all 4 symbols pass ADF at p<0.001. PASS.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
`pareto_front.csv` records a single row (seed=42, OOS_Sharpe=+0.3746, OOS_MaxDD=19.62%, max_concentration=44.88%). Per `feedback_v3_outer_seed_cap_2_v3.md`, single-seed EXPLORATION runs do not perform Pareto-dominance gating; that gate is reserved for CONFIRMATION multi-seed runs. Per pre-registered classification, single-seed EXPLORATION verdicts are PATH-fire decisions on the brief's locked Section 8 thresholds. N/A.

### Check 7 — Reproducibility: PASS
- Setup commit SHA `c69fdaa` exists; brief backfill SHA `4c7ff26` (HEAD at report time) confirmed.
- Runner uses explicit `feature_columns=V3_FEATURE_COLUMNS_TOP_N` (15 features verified by `_verify_feature_columns` assertion at `run_baseline_v3.py:583-590`).
- `_derive_ensemble_seeds(outer_seed, size=ENSEMBLE_SIZE)` produces deterministic seed list for the inner ensemble (literal seed function at `run_baseline_v3.py:94`).
- 5 adversarial tests in `tests/features_v3/test_vol_normalized_ret_5d.py` PASS at setup commit (95/95 regression tests confirmed).
- Random spot-check of `out_of_sample/trades.csv` row 2: BCH SHORT, entry 309.95, exit 323.62, weight 0.65; computed `pnl_pct = (323.617761 - 309.950000) / 309.950000 × -1.0 × 100 = -4.4097%` matches CSV's `pnl_pct=-4.4097`. Fee model `0.10%` applied correctly: `net_pnl_pct = -4.4097 - 0.10 = -4.5097` matches CSV. weighted_pnl = -4.5097 × 0.65 = -2.9313 matches.
- The iter-v3/047 "multi-run-stochasticity contamination" hypothesis is FALSIFIED by iter-v3/048 evidence: single PID 38365 with `--clean-oof` produced n_trials=700 identical to iter-v3/047. The 5x parquet duplication is structural (per-ensemble-seed write to a no-seed-column parquet), not run-pollution. PASS — no silent dependency, run is reproducible from `c69fdaa` head + the same `--seeds 1 --clean-oof` invocation.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1: "Adding `vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)` as a 15th feature in V3_FEATURE_COLUMNS_TOP_N gives the LightGBM models a risk-normalized momentum signal they cannot represent at depth-3-5 splits." Implementation `engineered_v3.py:439-487` matches: function defined exactly as specified; epsilon 1e-6; ret_5d via `log(close) - log(close.shift(15))`; division by `range_realized_vol_50 + 1e-6`. `add_engineered_v3_features` dispatches it (line 594). `V3_FEATURE_COLUMNS_TOP_N` updated to 15 entries with vol_normalized_ret_5d at the end (`features_v3/__init__.py:269`). Runner assertions at `run_baseline_v3.py:583-590` enforce presence. Setup commit `c69fdaa` git diff vs iter-v3/047 head shows: 1 new function, 1 line in dispatch, 1 entry in V3_FEATURE_COLUMNS_TOP_N, ITERATION_LABEL "v3-047" → "v3-048", verification assertion added. Zero scope creep. Carry-forward state from iter-v3/047 (primitive 10 BCH LONG block, ALGO+LDO ATR overrides) preserved verbatim. PASS.

## Optional Checks (9-12)

### Check 9 — Symbol Exclusion Enforcement: PASS
V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT) — 4 symbols UNCHANGED. `_verify_symbols` at `run_baseline_v3.py:163-170` asserts symbol overlap with V3_EXCLUDED_SYMBOLS is empty. PASS.

### Check 10 — Feature Isolation Enforcement: PASS
Per `phase5p5_gate.md` Track Isolation section: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` and `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` both EMPTY (only docstring mentions; no actual cross-track imports). PASS.

### Check 11 — Forming-Candle Audit: N/A
Data ingest unchanged from iter-v3/047. The 16h staleness guard (`_verify_data_freshness` at `run_baseline_v3.py:173-190`) hard-fails on stale data; runner did not raise.

### Check 12 — Library Version Pinning: PASS
Brief Section 9 stack identical to iter-v3/045/046/047 (lightgbm 4.6.0, numpy 2.2.6, optuna 4.8.0, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6). No version drift. PASS.

## iter-v3/047 Misdiagnosis — Adjudication

The QE engineering report (SHA `a068edd`) Section "n_trials=700 Investigation — iter-v3/047 Misdiagnosis Resolved" provides the dispositive forensic evidence:
- iter-v3/048 ran in a single PID 38365 with `--clean-oof` (parquet truncated at start; verified no prior file);
- The same single PID grew the parquet monotonically 25MB → 49MB → 73MB → 89MB → 110MB during the in-process loop;
- Final parquet 110MB / 55.78M rows / 5x duplicate-by-(trial_id,symbol,train_month,fold_idx,candle_open_time_ms) — IDENTICAL to iter-v3/047's parquet shape;
- Root cause: `optimization.py:425-430` writes per-ensemble-seed rows to a shared parquet with no `seed` column; 5 ensemble seeds (ENSEMBLE_SIZE=5) produce 5 namespace-collisions on `trial_id 0-34` per symbol per month per fold per candle.

**This falsifies the iter-v3/047 Critic FINAL (SHA `785500f`) attribution that "5 separate process invocations + LightGBM OpenMP non-determinism caused ALGO/LDO/TRX cross-run drift"**. The actual root cause of the iter-v3/047 OOS regression is **single-seed Optuna lottery variance on per-symbol independent searches** — exactly the same mechanism as ordinary single-seed EXPLORATION. The trades.csv was the result of one process, not the LAST of 5.

**Implications for memory and catalog**:

1. **iter-v3/047 catalog row label**: should be retroactively re-classified from `NEGATIVE-multi-run-stochasticity-contaminated` to **`NEGATIVE-clean (single-seed Optuna lottery variance, primitive 10 IS-validated)`**. The PATH C verdict stands (OOS Δ -2.36 fires the bundle-regression threshold); only the SUBCATEGORY label needs correction. The NEW catalog subtype `NEGATIVE-multi-run-stochasticity-contaminated` introduced at iter-v3/047 closeout has NO supporting cases and should be RETIRED from the taxonomy.

2. **`feedback_v3_single_seed_frozen_baseline.md` cross-process qualifier (added 2026-05-09)**: REVERT or REVISE. The "CRITICAL QUALIFIER" paragraph attributes iter-v3/020/021/022 bit-identity dissolution to "LightGBM OpenMP non-determinism + 5-process accumulation" — this attribution is FALSIFIED. The frozen-baseline pattern at single-seed=42 is a property of identical Optuna trajectories on per-symbol-independent searches when feature set + data are unchanged; ANY change to V3_FEATURE_COLUMNS_TOP_N (e.g., adding vol_normalized_ret_5d at iter-v3/048) breaks per-symbol Optuna determinism for ALL 4 symbols (because feature_columns is in the Optuna seed input). The qualifier as currently written conflates two distinct mechanisms: (a) feature-change-breaks-frozen-baseline (legitimate, well-supported); (b) cross-process-OpenMP-non-determinism (NOT supported by iter-v3/048 evidence — same single PID reproduces 5x parquet from a single seed=42 run). RECOMMEND: revise paragraph to remove the cross-process-OpenMP attribution and replace with "frozen-baseline pattern dissolves whenever feature_columns or data input changes; same-feature-same-data invocations of seed=42 are bit-reproducible whether in 1 process or 5 sequential processes."

3. **Primitive 10 carry-forward decision for iter-v3/050 CONFIRMATION**: The QE engineering report Section "Recommendations to QR" item 3 correctly states "the primitive 10 mechanism itself is NOT re-evaluated by this correction — it remains carry-forward in iter-v3/048 and should carry into iter-v3/049 and iter-v3/050 CONFIRMATION." I CONCUR. The iter-v3/047 OOS regression -2.36 is now correctly attributable to single-seed Optuna lottery on non-target symbols (ALGO/LDO/TRX), NOT primitive 10 cross-symbol contagion. The IS-side evidence stands (BCH IS net_pnl +42pp lift; 0 LONG leakage). The IS-only validation basis remains the original premise; the corrected attribution does not weaken or strengthen primitive 10's bundle-ingredient candidacy. The CONFIRMATION QR brief at iter-v3/050 must still note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 is the first multi-seed OOS test." The cleaner attribution simply removes a spurious confound from the historical record.

4. **iter-v3/045 anchor reliability**: iter-v3/047 (BCH-only primitive 10 added; no feature-set change) and iter-v3/048 (15th feature added; same primitive 10) both regressed substantially OOS vs iter-v3/045. iter-v3/045's IS +0.7459 / OOS +3.5259 may itself be a single-seed lottery winner that's hard to reproduce — note the OOS Calmar 7.31 is a strong outlier vs the v3 catalog distribution (median ~1-2). This is informational for the CONFIRMATION QR brief at iter-v3/050: the bundle composition's OOS edge needs to be tested against multi-seed compression (iter-v3/039 multi-seed showed 49% OOS compression on the iter-v3/035 bundle). DOES NOT change the iter-v3/048 verdict.

## Recommendations to QR (process-level for next iterations)

1. **Memory rule revision**: REVISE `feedback_v3_single_seed_frozen_baseline.md` to remove the 2026-05-09 cross-process-OpenMP qualifier and replace with the corrected attribution above. RETIRE the `NEGATIVE-multi-run-stochasticity-contaminated` catalog subtype from the taxonomy — it has zero supporting cases after iter-v3/048's forensic correction. Update iter-v3/047 catalog row label to `NEGATIVE-clean (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated)`.

2. **iter-v3/049 axis selection (cycle 3 #10 of 10)**: NEW universal engineered feature axis is now CLOSED (5 attempts: iter-v3/035, /041, /042, /043, /044+/048). Per `feedback_v3_axis_selection_quant_discipline.md`, QR must commit EDA at `analysis/iteration_v3-049/*.py` BEFORE the brief. Suggested EDA priorities: (a) NEW labeling architecture variant (universal triple-barrier with adaptive horizon by per-symbol vol regime) — different from iter-v3/017 meta-labeling that already failed; (b) NEW model architecture (CatBoost head-to-head with LightGBM at the 14-feature stack; iter-v3/016 closed XGBoost specifically but not CatBoost) — gradient boosters with monotone-constraint capability are categorically different; (c) per-symbol features that pass IS-axis pre-validation gate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — e.g., TRX-specific ret_kurt_50 sign-momentum since TRX has flat importance distribution and the IS-axis bottleneck; (d) drawdown-brake risk primitive (orthogonal-to-existing per `feedback_v3_concentration_is_signal.md`); (e) ADX-conditional regime gate variant (regime gate axis is open; iter-v3/048 EDA falsified TRX regime gate but did not test ADX-conditional). All 5 candidates are categorically distinct from the closed engineered-feature axis. EDA must rank with quantitative evidence and EDA-falsify the weak candidates.

3. **vol_normalized_ret_5d MUST be DROPPED at iter-v3/049 setup**: revert V3_FEATURE_COLUMNS_TOP_N from 15 → 14. Per `feedback_v3_inert_features_at_higher_budget.md`, bottom-ranked features at n_trials=35 actively HARM OOS by enlarging the Optuna search space without adding signal. Keeping it would compound damage. The cycle 3 saturation rule fires.

## Catalog Row

`| iter-v3/048 | 2026-05-09 | NEW universal engineered feature: vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6); 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven cycle 3 #9; primitive 10 BCH LONG block carry-forward; ALGO+LDO per-symbol ATR carry-forward; --clean-oof guardrail | -0.43 (vs iter-v3/045 anchor +0.7459 → +0.3118; PATH C IS regression fires) | -3.15 (vs iter-v3/045 anchor +3.5259 → +0.3746; PATH C OOS regression fires; LDO -34.85 + ALGO -36.82 + TRX -11.09 + BCH -3.43; no symbol improved OOS; vol_normalized_ret_5d ranks 13-15/15 ALL 4 syms = bottom-2; IS-OOS daily Sharpe ratio 0.96 within band so NOT NEGATIVE-SUSPICIOUS; n_trials=700 confirmed STRUCTURAL not contamination per QE forensic) | EXPLORATION-NEGATIVE (clean) | NO — drop vol_normalized_ret_5d at iter-v3/049 setup; NEW universal engineered feature axis CLOSED for cycle 3 (saturation rule fires: 5 attempts iter-v3/035, /041, /042, /043, /044+/048); iter-v3/049 = different axis category per `feedback_v3_axis_selection_quant_discipline.md` (QR EDA at analysis/iteration_v3-049/*.py BEFORE brief); MATERIAL FORENSIC FINDING: iter-v3/047 misdiagnosis confirmed — n_trials=700 is structural OOF parquet schema artifact (per-ensemble-seed namespace collision in shared parquet at optimization.py:425-430), NOT 5-run process pollution; iter-v3/047 catalog row should be re-labeled NEGATIVE-clean (single-seed Optuna lottery); `NEGATIVE-multi-run-stochasticity-contaminated` subtype retired from taxonomy; `feedback_v3_single_seed_frozen_baseline.md` cross-process qualifier (2026-05-09) revision recommended; primitive 10 carry-forward to iter-v3/050 CONFIRMATION decision UNCHANGED (IS-only validation basis remains the original premise) |`

## Files Audited

- `briefs-v3/iteration_v3-048/research_brief.md` (SHA `81af783`)
- `briefs-v3/iteration_v3-048/phase5p5_gate.md` (SHA `34c97c5`)
- `briefs-v3/iteration_v3-048/engineering_report.md` (SHA `a068edd`; setup `c69fdaa`; backfill `4c7ff26`)
- `reports-v3/iteration_v3-048/comparison.csv` + `dsr.json` + `seed_summary.json` + `pareto_front.csv` + `per_cell_pbo.csv` + `cpcv_paths.csv` + `ic_matrix.csv` + `adf_test.csv`
- `reports-v3/iteration_v3-048/in_sample/trades.csv` + `model_importance_last_month_*.csv`
- `reports-v3/iteration_v3-048/out_of_sample/trades.csv` (spot-checked row 2 PnL math)
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 436-487, dispatch line 594)
- `src/crypto_trade/features_v3/__init__.py` (V3_FEATURE_COLUMNS_TOP_N expanded 14 → 15)
- `tests/features_v3/test_vol_normalized_ret_5d.py` (5 adversarial tests)
- `run_baseline_v3.py` (lines 583-590 assertion; 1322-1333 primitive 10 carry-forward)
- `analysis/iteration_v3-048/synthesis.md` + `candidate_axes_ranking.md` (SHA `a230cd1`)
- `briefs-v3/iteration_v3-047/review.md` + `engineering_report.md` (n_trials=700 attribution falsified)
- `diary-v3/iteration_v3-047.md` (catalog subtype attribution that needs correction)
- `reports-v3/iteration_v3-045/comparison.csv` (anchor)
- `feedback_v3_single_seed_frozen_baseline.md` (cross-process qualifier needing revision)
