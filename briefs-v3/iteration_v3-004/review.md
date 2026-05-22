# Phase 7.5 Critic Review — iter-v3/004

OVERALL: BLOCK — Check 3 FAIL on DSR threshold (0.0 < 0.95) per literal skill enforcement, plus Check 6 FAIL on single-seed Pareto front (1 row); both failures inherited unchanged from iter-v3/003 and pre-acknowledged by the brief, but the Critic's per-check thresholds are unconditional.

## Per-Check Status

### Check 1 — Look-Ahead Audit: WARN (carried forward)

The RiskV3Wrapper at `src/crypto_trade/strategies/ml/risk_v3.py:56-71` snapshots feature mean/std and Hurst quantile bands using a global IS-mask (`is_mask = table["open_time"] < OOS_CUTOFF_MS`) at fit-time, computed across the FULL IS window. This is not strict look-ahead within the IS window itself (the OOS data is properly masked off), but the per-month calibration uses statistics that include observations from later months within IS. iter-v3/002 and iter-v3/003 reviews registered this as WARN. iter-v3/004 makes no model-side changes (model is byte-identical to iter-v3/003 per the alternative-path recompute), so the inherited convention is unchanged. The labeling and OOF-persistence pipelines (`labeling.py`, `optimization.py:298-319`) are clean: triple-barrier ATR uses past-only NATR_21, OOF candles are inner-CV folds of the training window only, candle_open_time_ms < OOS_CUTOFF_MS filter is applied at consumer time (run_baseline_v3.py:646). No new look-ahead introduced.

### Check 2 — Embargo Width: PASS

Two CSCV pathways with two distinct gaps, both methodologically grounded.

Global axis: gap = REQUIRED_GAP = `(timeout_candles + 1) × n_symbols = (21 + 1) × 4 = 88`. Asserted at `run_baseline_v3.py:541` via `combinatorial_purged_cv(...expected_gap=REQUIRED_GAP)` and verified at startup by `_verify_label_leakage_gap()`. This is the López de Prado purge requirement for the cross-symbol pooled candle stream that `cpcv_paths.csv` is computed on.

Per-cell axis (NEW in iter-v3/004): gap = 22 = `timeout_candles + 1`. Brief Section 0 documents this as the within-symbol variant: each cell is a single (symbol, train_month) tuple, so the `× n_symbols` multiplier is irrelevant (only one symbol's labels can overlap within the cell). The 21-bar timeout requires 22 candles of purge to prevent label leakage, which is exactly what the per-cell pathway uses (`run_baseline_v3.py:605`). Both invariants preserved.

### Check 3 — Multiple-Testing Correction: FAIL

- **DSR = 0.0 (threshold > 0.95): FAIL.** Computed correctly per `validation_v3.deflated_sharpe_ratio_v3` from raw IS Sharpe ≈ -0.034 (monthly Sharpe = -0.0746 over 225 trades), `n_trials = 1000`. Negative observed IS Sharpe with non-trivial trial budget → DSR_z deeply negative → `norm.cdf(z) → 0`. The FAIL is identical to iter-v3/003 (same numerator, same denominator, model unchanged). Per iter-v3/003 review precedent: "The fact that DSR fails by design (negative IS Sharpe) does not exempt it from threshold enforcement." The skill's rule "Any single threshold missed = FAIL" is unconditional.

- **PBO = 0.1305 (threshold strict (0,1) per Section 8 criterion 21; auto-NO-MERGE threshold < 0.4): PASS.** This is the iteration's headline result. The per-cell consumer pipeline (`run_baseline_v3.py:608-782`) iterates over 173 (sym, train_month) cells, runs 45-path CSCV on each, aggregates the cell-level PBOs via cross-cell mean. Verified: 0.0 < 0.1305 < 1.0, and 0.1305 < 0.40. The methodology degeneracy that BLOCKed iter-v3/003 (PBO=0.0 from `groupby("trial_id").sum()` over independent Optuna studies) is genuinely fixed.

- **PSR = 1.0 (threshold > 0.95): PASS** in form but vacuous, identical to iter-v3/002 and iter-v3/003 (computed deterministically from OOS Sharpe ≈ 2.205 over 83 trades).

- **n_eff = 25 (threshold > 4 per Section 8 criterion 22): PASS.** Per-cell median across 173 informative cells; CSV spot-check (q25=23, q75=27, min=12, max=31) confirms a healthy right-tail distribution. The rank-1 tautology that BLOCKed iter-v3/003 (n_eff=1 from a degenerate (50 × 5359) PCA) is fixed.

- **n_trials = 1000**: same understatement as iter-v3/003. Per-cell pathway technically uses 50 × 173 ≈ 8650 distinct (cell, trial_id) configurations; the runner still reports the headline `args.n_trials × len(ENSEMBLE_SEEDS) × len(V3_MODELS) × args.seeds = 1000` (run_baseline_v3.py:1386). Documentation concern only since DSR fails at 1000 already.

Aggregate verdict on Check 3: **FAIL** because the DSR threshold is missed (0.0 < 0.95), per literal skill spec and iter-v3/003 precedent. The methodology axes (PBO, n_eff) — which were the iter-v3/003 BLOCK drivers — have been correctly repaired and now PASS.

### Check 4 — IC Correlation: PASS (vacuous)

`reports-v3/iteration_v3-004/ic_matrix.csv` present, 34 features × 34 features pairwise Pearson on IS-pooled BCH+MKR+LDO+TRX. No new feature families added (brief Section 3.3: V3_FEATURE_COLUMNS UNCHANGED, len=34 verified at runtime by `_verify_feature_columns()`). Pre-existing cross-family pairs above 0.7 (`atr_pct_rank_200` ↔ `atr_pct_rank_500` ≈ 0.826; `bb_width_pct_rank_100` ↔ `volume_mom_ratio_20` ≈ 0.530; `ret_skew_50` ↔ `ret_skew_100` ≈ 0.662) are not introduced by this iteration. Vacuous PASS, same precedent as iter-v3/002 and iter-v3/003.

### Check 5 — ADF Stationarity: PASS

`reports-v3/iteration_v3-004/adf_test.csv` has 7242 data rows, identical to iter-v3/003 (file copied verbatim by `recompute_metrics.py:84-88`). Per-(symbol, feature, retraining month) granularity; spot-check distribution unchanged from iter-v3/002/003 (~83.6% stationary at p<0.05). The ADF rows are not affected by the methodology repair.

### Check 6 — Pareto Dominance: FAIL

`pareto_front.csv` contains exactly **1 row** (seed 42 only). Engineering report Section "Recompute Method" confirms single-seed run; brief Section 8 criterion 15 self-vacates the 10-seed requirement as "vacuity acceptable per memory rule for this methodology iteration". But the project memory rule (`feedback_seed_validation.md`: "Before MERGE: run 10 seeds, mean Sharpe > 0, ≥ 7/10 profitable") is unconditional. Single-seed pre-MERGE validation is a structural FAIL on Check 6 regardless of QR's brief-level discretion. Same FAIL status as iter-v3/001/002/003 reviews. The chosen seed (42) cannot be Pareto-checked against alternatives because no alternatives were run.

### Check 7 — Reproducibility: PASS

- Code commit SHA stamped: `63b82f2` (engineering report header).
- Reports commit SHA stamped: `439a9f7` (engineering report header).
- Runner uses explicit `feature_columns=list(V3_FEATURE_COLUMNS)` at `run_baseline_v3.py:830`; LightGbmStrategy raises on None/empty per project conventions.
- `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literal at `run_baseline_v3.py` (verified inherited from iter-v3/003 unchanged).
- **iter-v3/003 PBO field divergence WARN is now FIXED (sub-fix #5).** `seed_summary.json[0]["pbo"] = 0.130525` is a numeric float (not literal "NaN" string); same value also appears in `dsr.json["pbo"]` and `pareto_front.csv` row. The hardcoded literal at run_baseline_v3.py:1162 (iter-v3/003) was replaced with a `pbo_result.pbo` consultation at lines 1551-1553. Verified consistency across all three persistence files.
- Library versions stamped: numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1.

The recompute path (`analysis/iteration_v3-004/recompute_metrics.py`) reuses iter-v3/003's `trial_oof_returns.parquet` and `in_sample/`/`out_of_sample/` directories byte-for-byte; the metrics that change (PBO, n_eff, dsr.json, comparison.csv pbo/n_eff rows, seed_summary.json pbo, pareto_front.csv pbo) are all functions of the new consumer pipeline. The "model unchanged" claim is reproducibility-correct.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis: "Modifying `_compute_cpcv_paths` and `_compute_n_eff_trials` ... will produce an aggregated PBO strictly in (0.0, 1.0) AND a median n_eff > 4". Implementation at `run_baseline_v3.py:446-782` (sub-fix #1: `_compute_cpcv_paths` rewrite with per-cell mean) and `run_baseline_v3.py:1432-1469` (sub-fix #2: per-cell median n_eff via `per_cell_pbo.csv`). Both produce the predicted result: PBO=0.1305 ∈ (0.0, 1.0), n_eff=25 > 4. The four predicted-falsifier conditions (Section 4.2 primary/secondary/tertiary/quaternary/quinary) all return PASS per the engineering report's Section 3.6 reconciliation table (12/12 verifiers exit 0).

Two QR deviations from the iter-v3/003 diary's Next Iteration Idea #1 are documented and justified:

1. **Cell key collapsed from `(sym, month, seed)` to `(sym, month)`**: brief Section 2.1 provides the empirical observation that the iter-v3/003 OOF parquet has `nunique(oof_return) == 1` for every group of 5 ensemble-seed-duplicate rows — i.e., the seed dimension is degenerate in this parquet. This is itself an interesting finding (the "5-seed ensemble" in iter-v3/003 produced identical OOF rows; either the ensemble's randomness is downstream of OOF computation or the writer overwrote rather than appended-with-distinction). The dedup-by-natural-key consumer-side fix loses no statistical signal because there is no signal in the seed dimension to lose. This is acceptable for iter-v3/004 (consumer-side fix) but flags a producer-side question: should the writer be fixed (next iteration), or is the 5-seed ensemble structurally unable to produce per-seed OOF distinctness?

2. **Aggregator changed from Fisher's method (diary prescription) to cross-cell mean (this brief)**: brief Section 2.3 + Section 9 provide both empirical justification (Fisher chi²=2052.7 at df=346 saturates to numerical zero, confirmed in `aggregated_pbo.json`: `"fisher_pbo_aggregated": 8.94e-240`) and mathematical justification (chi² = -2 · Σ ln(p_i) is dominated by 173 × -2 · ln(ε) ≈ +5900 at this scale). Mean is the only aggregator returning a value strictly inside (0, 1) on the observed bimodal cell-level distribution; it has the natural interpretation "fraction of cells showing overfit signature" (here ~13%). Fisher retained as supplementary diagnostic in `aggregated_pbo.json`. This is a legitimate empirical departure from the diary plan, properly disclosed in brief Section 2.3 with the §2 IS-only demo committed at SHA 23bb5be BEFORE the brief was authored — the Phase 5.5 reproducibility chronology is intact.

The new consumer-preserves-signal adversarial test `tests/strategies/ml/test_per_cell_pbo_synthetic.py` (4 functions: `test_overfit_cells_high_pbo`, `test_clean_cells_low_pbo`, `test_pairwise_separation_overfit_vs_clean`, `test_mixed_cells_mean_pbo_between_extremes`) addresses iter-v3/003's Critic Recommendation #2 directly; pairwise separation (synthetic overfit min=1.0 > synthetic clean max=0.358) is verified per `aggregated_pbo.json["synthetic_validation"]`. 26/26 adversarial tests pass (4 inherited × 4 = 22 + 4 new = 26).

Headline metrics (IS Sharpe, OOS Sharpe, trade count, MaxDD, MKR concentration) match iter-v3/003 EXACTLY to 4 decimal places per `comparison.csv` line-by-line diff — confirming Prediction P5 (model byte-identical, no RNG state corruption from the consumer-side modification).

## Optional Checks 9–12

- **Check 9 — Symbol Exclusion Enforcement**: PASS. `run_baseline_v3.py:_verify_symbols()` (line 130-137) raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` is non-empty; called at startup (line 1200) and per-symbol in `_run_single_seed` (line 1137). V3_EXCLUDED_SYMBOLS imported at line 46.

- **Check 10 — Feature Isolation**: PASS. `run_baseline_v3.py:_verify_track_isolation()` (line 188-209) explicitly greps `^from crypto_trade\.features` and `^from crypto_trade\.features_v2` in `src/crypto_trade/features_v3/` and raises on any match. Called at startup (line 1204).

- **Check 11 — Forming-Candle Audit**: PASS. `_verify_data_freshness()` (line 140-157) hard-fails at startup if any symbol's `close_time` lag exceeds 16h. Per the engineering report, the run completed at SHA 439a9f7 on 2026-05-05; the 8h kline data was fetched as part of the iter-v3/003 base, so the same staleness guard applies.

- **Check 12 — Library Version Pinning**: PASS. Engineering report stamps numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1; brief Section 9 declares the same packages as "already installed". No version mismatch.

## Recommendations to QR

This iteration's METHODOLOGY axes (PBO, n_eff, consumer-pipeline correctness) are correctly repaired and would PASS strict review. The OVERALL=BLOCK is driven by two structural threshold failures inherited from iter-v3/003 and not addressable within iter-v3/004's no-rebacktest scope: (a) DSR=0 from negative IS Sharpe; (b) single-seed pre-MERGE validation. Phase 8 may resolve via the brief's pre-registered split-merge clause. Process-level recommendations for future iterations:

1. **Decouple DSR from negative-IS-Sharpe iterations or define a methodology-MERGE pathway in skill.** The DSR threshold > 0.95 cannot be cleared on a strategy with negative IS Sharpe regardless of pipeline correctness (it is a direct function of the observed Sharpe and the trial count, not the methodology). When the iteration's purpose is methodology repair, the skill should formally separate "edge thresholds (DSR, OOS Sharpe)" from "methodology thresholds (PBO, n_eff, ADF, IC)" and allow methodology-MERGE to proceed independently. Currently the QR's split-merge clause does this work in the brief, but the Critic's framework treats all thresholds uniformly. Submit a `quant-iteration-v3.md` skill PR clarifying that DSR/PSR/Sharpe are edge-axis metrics and Check 3 should be split into Check-3a (methodology, PBO + n_eff) and Check-3b (edge, DSR + PSR).

2. **Investigate the 5-seed ensemble OOF-duplicate finding as a producer-side bug or design choice.** Brief Section 2.1 documents that every group of 5 rows for the same `(sym, month, trial, fold, candle)` has `nunique(oof_return) == 1`. This means the iter-v3/003 ensemble generated identical OOF returns across its 5 ensemble seeds — either (a) the ensemble's randomness is downstream of inner-CV OOF computation (producer-side design quirk), or (b) the writer is overwriting rather than appending-with-seed-distinction (producer-side bug). Either way, the per-seed PBO/n_eff dimension promised by `ensemble_seeds=[42, 123, 456, 789, 1001]` is not actually reflected in the OOF parquet. iter-v3/005 should diagnose this in `optimization.py:298-319` (the `oof_buffer` append) and either (a) verify the seed propagates into the model fit such that OOF returns differ across seeds, or (b) drop the seed dimension from the parquet schema honestly.

3. **Add the 10-seed pre-MERGE validation to a non-vacuous path even on methodology iterations.** Single-seed runs cannot Pareto-check; the project memory rule is unconditional. iter-v3/005 should run 10 seeds even when the model is unchanged from a prior iteration (since random subsampling of `colsample_bytree` and Optuna TPE sampler trajectories vary with seed; the per-cell PBO mean and n_eff distributions across 10 seeds would also empirically validate whether the per-cell aggregate is stable across model realizations). The expected wall-clock for 10 seeds on the existing parquet is just 10 × 89s ≈ 15 minutes — trivially affordable.
