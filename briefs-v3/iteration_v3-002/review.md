# Phase 7.5 Critic Review — iter-v3/002

OVERALL: BLOCK — Section 3.5 fix #2 (per-Optuna-trial OOF return persistence) was not implemented; PBO remains structurally undefined (NaN) instead of producing the "meaningful number" Section 4.2 designated as the iteration's primary success criterion; n_eff_trials computation substitutes per-(symbol, month) grouping for the prescribed per-trial OOF matrix.

## Per-Check Status

### Check 1 — Look-Ahead Audit: WARN

Inherits the iter-v3/001 RiskV3Wrapper convention: `risk_v3.py:55-71` snapshots feature mean/std and Hurst quantiles using `is_mask = table["open_time"] < OOS_CUTOFF_MS` over the full IS window, then uses the same statistics at every OOS bar. No frank look-ahead (OOS_CUTOFF_MS bounds the IS mask), but the gate cannot adapt to rolling regime drift. Same demoted-from-FAIL judgment as iter-v3/001 since v2 inherited the convention. Trade-row spot-check on OOS row 2 (MKRUSDT, dir=+1, entry=1414.20, exit=1339.299738, weight=0.37): pnl_pct=(1339.299738-1414.20)/1414.20*100=-5.296%, net=-5.396%, weighted=-1.997% — math reproduces. No new look-ahead introduced this iteration.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88` candles. `validation_v3.REQUIRED_GAP = 88` (validation_v3.py:44). The runner's `_compute_cpcv_paths` at `run_baseline_v3.py:521-528` calls `combinatorial_purged_cv(gap=REQUIRED_GAP, expected_gap=REQUIRED_GAP)`. The `expected_gap` machinery in `validation_v3.combinatorial_purged_cv:96-102` raises AssertionError on mismatch. `_verify_label_leakage_gap` at runner startup (`run_baseline_v3.py:174-187`) re-verifies the formula and prints "Label-leakage gap: 88 [matches REQUIRED_GAP=88] PASS" (run.log:12). Three independent assertions across runner startup + CPCV call + library default — the iter-v3/001 silent-rescaling bug is now structurally prevented. Adversarial test `tests/strategies/ml/test_cpcv_embargo_assert.py` (7 tests, including degraded-gap regression) verifies the guard. PASS.

### Check 3 — Multiple-Testing Correction: FAIL

Three failures, with PBO being the methodology-killer:

- **DSR = 0.0 (numerical, not clamped).** `validation_v3.deflated_sharpe_ratio_v3` (validation_v3.py:346-418) genuinely removes the negative-SR clamp — `p_value = float(norm.cdf(dsr_z))` with no `if observed_sr < 0: return 0` branch. The reported 0.0 is `norm.cdf(z)` at z ≈ -18 with raw IS Sharpe = -0.0746 and expected_max_SR ≈ 3.09 from n_trials=1000, rounding to 0 at Python float precision. Mathematically correct per LdP formula. DSR fix shipped; threshold > 0.95 obviously fails by design (Section 7 prediction #4) but methodology is sound on this axis.

- **PSR = 1.0.** Computed from OOS trades only (run_baseline_v3.py:1170-1175) with raw OOS Sharpe = +2.205 over 83 trades; the formula returns ≈1 deterministically at this level. Real value but uninformative — same as iter-v3/001. Threshold > 0.95 nominally clears but is vacuous.

- **PBO = NaN. METHODOLOGY-CRITICAL FAIL.** `pbo_from_cpcv` correctly returns `PBOResult.pbo=None` for S=1 input (validation_v3.py:266-278) — that part of the algorithm is correct. The failure is upstream: `_compute_cpcv_paths` (run_baseline_v3.py:448-568) produces `path_metric_matrix` of shape `(45, 1)` because it feeds `combined["_ret"].to_numpy()` (a single per-candle return series) through CPCV. Brief Section 3.5 fix #2 explicitly mandated: **"The Engineer must persist per-Optuna-trial out-of-fold returns to enable the proper PBO computation."** That sentence is the structural prerequisite for S>1. The Engineer instead left the path matrix at S=1 and used the descriptive-stats fallback exit. Section 8 criterion 8 pre-registers `NaN with descriptive-stats fallback is acceptable` — but that fallback was designed for cases where S>1 is genuinely impossible (single-strategy run). Here S>1 was REQUIRED by Section 3.5 fix #2 and not implemented.

The runner's docstring at `_compute_cpcv_paths:464-466` admits this verbatim: *"Since the runner does not persist per-Optuna-trial OOF return sequences in this iteration, the strategy axis S=1 (one strategy per path)."* This is the Engineer documenting that they did not ship Section 3.5 fix #2. Brief Section 4.2 success criterion #1 ("PBO produces a meaningful number, not 0.0 by code bug") is NOT met — NaN is precisely "the test could not be run." The buggy iter-v3/001 returned 0.0 (lying that it ran); iter-v3/002 returns NaN (honestly admitting it didn't). Honesty is an improvement over the bug, but it does not constitute a successful methodology repair on the iteration's central goal.

### Check 4 — IC Correlation: PASS (informational)

`reports-v3/iteration_v3-002/ic_matrix.csv` is present, 34×34 Pearson on IS-data combined across BCH+MKR+LDO+TRX. No new feature families added in iter-v3/002 (brief Section 3.3 explicit). Highest pre-existing pair: `atr_pct_rank_200` ↔ `atr_pct_rank_500` ≈ 0.826; `vwap_dev_20` ↔ `vwap_dev_50` ≈ 0.794 — same v2-family pairs flagged in iter-v3/001's review, both above the 0.7 threshold but pre-existing and not introduced by this iteration. Informational only since no new families to test. PASS.

### Check 5 — ADF Stationarity: PASS (with criterion-formula caveat)

7242 rows in `reports-v3/iteration_v3-002/adf_test.csv` matching per-(symbol, feature, month) granularity (run.log:38, 40). Spot-check confirms shape: BCHUSDT × 34 features × month=2020-01...2020-02..., progressing through TRXUSDT × month=2025-03 at row 7243 (last data row). LDOUSDT/cusum_reset_count_200 secondary falsifier surfaces non-stationarity in 27/31 months (engineering_report.md:200-204; runner's `_verify_adf_row_count:402-411` re-checks at completion). The averaging-bias bug from iter-v3/001 is genuinely fixed — this is the iter-v3/002's most cleanly delivered methodology fix.

**Caveat for QR (not a Check 5 BLOCK):** Section 8 criterion #13's text says `adf_test.csv row count = n_symbols × n_features × n_retrain_months`. This formula assumes uniform `n_retrain_months` across symbols, but the implementation correctly varies per-symbol (LDO listed 2022-09 vs BCH listed earlier). The engineering report (lines 110-118) shows three failed attempts to reconcile 7242 against the formula (5882 → 6222 → admits "doesn't match"). The actual runner check at `_verify_adf_row_count:382-399` enforces only `total_actual >= expected_min` (n_syms × n_feats × MIN months), not equality. Criterion #13 as written cannot be literally verified; the runner's `>= expected_min` is the right operational test but does not match the brief's formula. Process defect logged for QR's brief revision in Recommendation #2.

### Check 6 — Pareto Dominance: FAIL

`pareto_front.csv` contains exactly **1 row** (seed 42 only). Brief Section 8 criterion 15 mandates "10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable" with vacuity allowed only when the LightGbmStrategy outer-seed is structurally ignored. Same failure mode as iter-v3/001: single seed, no Pareto front, no evidence of multi-seed stability. Engineering report (line 34) confirms `--seeds 1`. Even granting the methodology-repair-pilot rationale, criterion 15 was not vacated by re-running. Same-failure-as-last-iter is itself a process signal: the QR knew this was needed and the Engineer did not run it.

Additional concentration ambiguity surfaced: comparison.csv reports MKRUSDT concentration_pct = **53.21%**; seed_summary.json and pareto_front.csv report max_concentration_pct = **43.64%**. Two different computations of the same concept reported by the runner in the same execution. Criterion 6 (≤30%) fails on either reading, but the discrepancy is a Check 7 reproducibility defect.

### Check 7 — Reproducibility: WARN

Engineering report at SHA `8c5f15eea60a5abe78cba596e20902aff61ea84d` (line 6); committed. Runner at `run_baseline_v3.py:613` passes `feature_columns=list(V3_FEATURE_COLUMNS)` explicitly (matches iter-v3/001 fix). `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literal at `run_baseline_v3.py:78`, passed at line 612. Trade-row spot-check reproduces (Check 1).

WARN reasons:
1. **Concentration field divergence between comparison.csv (53.21%) and pareto_front.csv / seed_summary.json (43.64%)** — same backtest run produces inconsistent concentration figures depending on which output file you read.
2. **Engineering report's ADF row-count math is internally contradictory** (lines 110-118) — three attempted reconciliations of 7242, none correct. Anyone re-deriving expected row count from the engineering report's text gets a different number than the file actually contains.
3. **n_eff_trials = 4 is suspiciously equal to n_symbols.** The runner at `run_baseline_v3.py:1184-1199` builds `trial_mat` by grouping trade `weighted_pnl` per `(symbol, month)` and zero-padding to max trades per group. With 4 symbols, the PCA-95% rank of this grouping naturally collapses toward 4 (one principal component per symbol's distinct return distribution). This is NOT the "true `n_trials × T` matrix where each row = one Optuna trial's OOF return sequence" prescribed by Section 3.5 fix #5. The number 4 is not a recurrence of the iter-v3/001 row-tile=1 bug, but it is a different non-prescribed surrogate. Zero-padding for PCA is itself statistically invalid (the zeros create artificial low-variance directions).

### Check 8 — Hypothesis-Implementation Alignment: FAIL

The brief-vs-code reconciliation table in research_brief.md Section 3.7 nominally has 8 filled rows, satisfying Section 8 criterion #19 mechanically. But the actual code reconciliation reveals **two of the eight Section 3.5 fixes are partially implemented**:

1. **Section 3.5 fix #2 — "persist per-Optuna-trial OOF returns"** — NOT IMPLEMENTED. The reconciliation cell says only "_compute_cpcv_paths consumes a candle/feature DataFrame, NOT a trade list" — covering the CPCV-scope sub-fix while silently omitting the per-trial-OOF-persistence sub-fix. The runner's `_compute_cpcv_paths` docstring (run_baseline_v3.py:464-466) explicitly admits: *"Since the runner does not persist per-Optuna-trial OOF return sequences in this iteration, the strategy axis S=1."* This is hypothesis-faking on a fix the brief explicitly mandated. The reconciliation cell is misleading because it covers half the requirement and presents that half as the whole.

2. **Section 3.5 fix #5 — "true `n_trials × T` matrix (each row = one Optuna trial's out-of-fold return sequence across all CPCV test folds)"** — NOT IMPLEMENTED. The runner's `n_eff_trials` construction at `run_baseline_v3.py:1182-1199` substitutes per-(symbol, month) trade groupings for the prescribed per-trial OOF matrix. The reconciliation cell says "trial-return matrix shape is (n_trials, T) with T > 1" — true only by replacing "trial" with "symbol-month group". The padding-to-max-len at line 1195 is itself a methodology smell (zero-padding is invalid for PCA on returns).

Both omissions trace to the same root: the runner did not modify `LightGbmStrategy._train_for_month` (in `src/crypto_trade/strategies/ml/lgbm.py`) to persist per-trial OOF returns. Verified via the iter-v3/002 commits — changes touched `run_baseline_v3.py`, `validation_v3.py`, `risk_v3.py`, `tests/strategies/ml/`, but NOT `lgbm.py`. Fixes #2 and #5 both depend on this LightGbmStrategy modification; both are therefore structurally incomplete.

These are hypothesis-implementation misalignments on the iteration's CENTRAL methodology fixes. The reconciliation table's "filled" status is misleading because the cells describe what was done (CPCV moved to candles, n_eff matrix has T>1) without flagging what was NOT done (per-trial OOF persistence). Brief Section 4.2 success criteria #1 ("PBO produces a meaningful number") and #3 ("n_eff_trials > 1 with real per-trial returns") are not satisfied: the first because PBO is NaN (not a number); the third because n_eff=4 is from grouped trade pnls with zero-padding, not "real per-trial returns."

The headline-metric mechanical failures persist by design (per Section 4.2 split-merge plan, listed for completeness):
- Criterion 1: IS monthly Sharpe = -0.0746 (threshold > 1.0) — FAIL
- Criterion 2: OOS monthly Sharpe = +1.0955 (threshold > 1.0) — FAIL
- Criterion 4: OOS total trades = 83 (threshold ≥ 130) — FAIL
- Criterion 5: Trades/month OOS = 5.5 (threshold ≥ 10) — FAIL
- Criterion 6: Top-symbol OOS concentration = 53.21% / 43.64% (threshold ≤ 30%) — FAIL
- Criterion 17: sign(IS) = -, sign(OOS) = +, mismatch — FAIL

Section 8's discretionary split-merge clause permits methodology-only merge when "Critic OVERALL = MERGE on the methodology criteria" AND criteria 13, 18, 19 ALL pass. Here, the methodology criteria themselves are partially failed (PBO is NaN by Engineer omission of fix #2, n_eff_trials uses non-prescribed surrogate per omission of fix #5), so the split-merge precondition cannot be cleared regardless of how generously the brief's letter is read.

## Recommendations to QR

(For BLOCK iterations; process-level fixes for FUTURE iterations.)

1. **Promote "per-trial OOF return persistence" to a Phase 5.5 hard input artifact.** The reconciliation table's row 3.5#2 cell should require a code reference to a NEW persistence file (e.g., `reports-v3/iteration_v3-NNN/trial_oof_returns.parquet`) with shape `(n_optuna_trials × n_cpcv_folds × n_test_candles)`. If that file does not exist post-Phase 6, criterion 19 fails automatically. The current reconciliation table allows the cell to be filled with a description that hides which sub-fixes were dropped — make the artifact, not the description, the gate. Concretely: modify `LightGbmStrategy._train_for_month` to write per-trial OOF returns to disk during Optuna's objective callback; the path-matrix-builder then reads them and produces a true `(N_paths × N_optuna_trials)` matrix.

2. **Tighten Section 8 criterion #13's formula.** The current text `n_symbols × n_features × n_retrain_months` is mathematically impossible to verify when symbols have different listing dates. Replace with: "for each symbol s in V3_SYMBOLS, `adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s`." Or equivalently: `adf_test.groupby('symbol').size() == n_features × per_symbol_n_months_series`. The engineering report's confusion (lines 110-118) traces directly to the formula being ill-posed.

3. **Add a "methodology-fix completeness" Critic check via per-sub-fix decomposition.** Currently Check 8 verifies that brief promises map to code, but cannot detect when a code path implements only HALF of what the brief promised. Add a Phase 5.5 input requirement: each Section 3.5 numbered fix decomposes into atomic sub-fixes, each with its own reconciliation row. For example, the iter-v3/002 brief's Section 3.5 fix #2 has two atomic sub-fixes — (2a) move CPCV scope to candle sequence; (2b) persist per-Optuna-trial OOF returns to enable S>1. The brief collapsed both into one row, which the Engineer then partially filled. The Critic's structural escape from this trap requires per-sub-fix granularity; future iterations should produce reconciliation tables with N rows per Section 3.5 fix, where N = number of distinct verifiable code artifacts the fix mandates.
