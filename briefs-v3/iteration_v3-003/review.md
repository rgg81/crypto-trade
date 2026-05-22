# Phase 7.5 Critic Review — iter-v3/003

OVERALL: BLOCK — Section 8 criterion 22 (n_eff > 4) fails by Engineer's own admission (n_eff=1); the methodology-stack pre-registration explicitly forbids merge on any methodology criterion failure, and the n_eff=1 result is symptomatic of a deeper methodology breach (degenerate cross-cell strategy axis on the trial_id dimension) that also undermines the PBO=0.0 result.

## Per-Check Status

### Check 1 — Look-Ahead Audit: WARN

Same status as iter-v3/002. `RiskV3Wrapper` IS-mask convention (snapshot feature mean/std and Hurst quantiles using `is_mask = open_time < OOS_CUTOFF_MS` over the full IS window) is inherited from v2 and unchanged in iter-v3/003. No NEW look-ahead introduced — this iteration adds only an OOF persistence side-effect to `optimization.py:_objective` and a parquet read to `_compute_cpcv_paths`/`_compute_n_eff_trials`, none of which touches feature computation. Trade-row spot-check on `out_of_sample/trades.csv` row 2 (MKRUSDT, dir=1, entry=1414.20, exit=1339.299738, weight=0.37): pnl_pct = (1339.299738 - 1414.20)/1414.20 × 100 = -5.296%, net = -5.396%, weighted = -5.3963 × 0.37 = -1.997 — matches CSV. Row 4 (BCHUSDT, dir=-1, entry=303.870, exit=272.30463, weight=0.33): short pct = (303.870 - 272.30463)/303.870 × 100 = +10.388%, net = +10.288%, weighted = 10.288 × 0.33 = +3.395 — matches CSV. PnL math reproduces. Same demoted-from-FAIL judgment as iter-v3/002.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88` candles. `validation_v3.REQUIRED_GAP = 88` (validation_v3.py:44). Three-layer assertion intact: (a) `_verify_label_leakage_gap()` at runner startup (run_baseline_v3.py:174-188) logs "Label-leakage gap: 88 [matches REQUIRED_GAP=88] PASS"; (b) `_compute_cpcv_paths` calls `combinatorial_purged_cv(..., gap=REQUIRED_GAP, expected_gap=REQUIRED_GAP)` (run_baseline_v3.py:515-522); (c) `combinatorial_purged_cv` itself raises AssertionError on mismatch (validation_v3.py:96-102). Adversarial test `test_cpcv_embargo_assert.py` (7 tests including degraded-gap regression) reported passing in engineering report Section 2 (22/22 across all 4 test files). Inherited intact from iter-v3/002.

### Check 3 — Multiple-Testing Correction: FAIL

Three sub-axes, two of which fail under any reading and one of which passes only superficially:

- **DSR = 0.0 (threshold > 0.95)**: FAIL. Numerically correct per `validation_v3.deflated_sharpe_ratio_v3`: with raw IS Sharpe ≈ -0.034 (from 225 trades × wpnl, monthly Sharpe = -0.0746), `n_trials = 1000`, `expected_max_SR ≈ 3.09`, DSR_z ≈ -18, `norm.cdf(z)` rounds to 0 at Python float precision. The clamp-free implementation is methodologically sound — DSR fails because the IS Sharpe is deeply negative, exactly as Section 4.1 of the brief predicted. Threshold > 0.95 cannot pass on this universe regardless of pipeline correctness.

- **PSR = 1.0 (threshold > 0.95)**: PASS in form but vacuous. Computed from OOS trades only (raw OOS Sharpe ≈ 2.205 over 83 trades); the formula returns ≈1 deterministically at this magnitude. Same as iter-v3/002.

- **PBO = 0.0 (threshold acceptance per pre-registration: any value in [0.0, 1.0])**: STRUCTURAL FAIL. The literal numeric output (0.0) is in [0.0, 1.0] and per Section 4.2 pre-registration would PASS. But the result is uninterpretable because the strategy axis is degenerate. The runner at `run_baseline_v3.py:550` does `trial_candle = oof_df.groupby(["trial_id", "candle_open_time_ms"])["oof_return"].sum()` — i.e., sums OOF returns across ALL (sym, train_month, fold_idx, ensemble_seed) cells that share `trial_id`. But each `optimize_and_train` call is an independent Optuna study (`optimization.py:369-370: optuna.create_study(sampler=TPESampler(seed=seed))`), so `trial_id=0` from cell (BCH, 2023-01, seed=42) is a model with completely different hyperparameters than `trial_id=0` from cell (MKR, 2023-02, seed=123). Summing across ~500 cells produces 50 noisy aggregates that are NOT 50 strategies. PBO=0.0 from 5000/5000 splits means the IS-best aggregate is ALWAYS in the upper OOS half — this is consistent with a stable-but-meaningless ordering (e.g., trial_ids that happen to have more cells contributing positive rows), NOT with absence of overfitting. The CSCV test as run does not test what it claims to test. Engineering report Section 8.2 acknowledges this ("Optuna's `trial_id` is sequential within a study but not meaningfully comparable across (sym, month, seed) cells"); this exact concern was raised, and is the methodology-pipeline question Check 8 must adjudicate. On the binary read: PBO=0.0 satisfies the pre-registered acceptance threshold, so this check axis alone does not auto-FAIL. It contributes to Check 8's FAIL, where the trial-id semantics misalignment lives.

The aggregate verdict on Check 3 is FAIL because the DSR threshold is missed (0.0 < 0.95). Per skill spec §3 Check 3: "Any single threshold missed" = FAIL. The fact that DSR fails by design (negative IS Sharpe) does not exempt it from threshold enforcement.

### Check 4 — IC Correlation: PASS (vacuous)

`reports-v3/iteration_v3-003/ic_matrix.csv` is present, 34×34 Pearson on IS-data combined across BCH+MKR+LDO+TRX. No new feature families added (brief Section 3.3: "Features UNCHANGED"). Spot-check of the matrix shows pre-existing cross-family pairs above 0.7 (`atr_pct_rank_200` ↔ `atr_pct_rank_500` ≈ 0.826) — already flagged in iter-v3/001 and iter-v3/002 as informational since not introduced this iteration. Vacuous PASS, same as iter-v3/002.

### Check 5 — ADF Stationarity: PASS

7242 rows in `reports-v3/iteration_v3-003/adf_test.csv` matching per-(symbol, feature, retraining month) granularity. Spot-check: 6051 rows (83.6%) marked `stationary=True` (p < 0.05); 1191 cells (16.4%) `stationary=False`, identical to iter-v3/002's distribution. Spot examples: BCHUSDT/fracdiff_logclose_dstat/2024-12 ADF=-3.747, p=0.0035, True; TRXUSDT/fracdiff_logclose_dstat/2024-12 ADF=-2.151, p=0.225, False (an isolated symbol-month failure consistent with the 16% non-stationary tail observed in iter-v3/002). Engineering report Section 6 row "13 — per-symbol ADF row count" PASSes the formula `for each symbol s, adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s`. iter-v3/002 review accepted PASS with criterion-formula caveat at the same 16.4% non-stationary rate — applying the same precedent here. Inherited methodology fix is intact.

### Check 6 — Pareto Dominance: FAIL

`pareto_front.csv` contains exactly **1 row** (seed 42 only). Engineering report Section 4 confirms `--seeds 1`. Same failure mode as iter-v3/001 and iter-v3/002. Brief Section 8 criterion 15 marks this as "vacuity acceptable per memory rule for this methodology iteration" — but the project memory rule (`feedback_seed_validation.md`: "Before MERGE: run 10 seeds, mean Sharpe > 0, ≥ 7/10 profitable") is unconditional. The QR self-vacated criterion 15 in the brief, but the Critic's framework treats single-seed pre-MERGE validation as a structural FAIL on Check 6, regardless of the QR's brief-level discretion. Same status as iter-v3/002 review.

### Check 7 — Reproducibility: WARN

Engineering report SHA `f6e909ec70c67b3d2587323aaf66070e043f8e03` committed (referenced as backtest-time SHA). Runner uses explicit `feature_columns=list(V3_FEATURE_COLUMNS)` (run_baseline_v3.py:684); LightGbmStrategy `__init__` raises ValueError on empty/None (lgbm.py:143-148). `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literal at run_baseline_v3.py:79. Trade-row PnL spot-checks reproduce (Check 1).

WARN reasons:

1. **PBO field divergence between report files**: `dsr.json["pbo"] = 0.0` (canonical, from (45×50) CSCV) vs `seed_summary.json[0]["pbo"] = "NaN"` (per-seed, hardcoded literal at run_baseline_v3.py:1162). Same key name, two values, two files. Engineer flagged this as the iter-v3/002 concentration-divergence-class defect. Critic confirms: anyone reading `seed_summary.json` to determine PBO will see "NaN" while the canonical `dsr.json` shows 0.0. The runner literal `"pbo": "NaN"` at line 1162 is hardcoded and never consults the actual computed value. Process defect carried forward from iter-v3/002.

2. **n_eff = 1 from a degenerate strategy axis** (also Check 8 territory): Engineer Section 8.2 acknowledges that `aggfunc="sum"` across cells smooths the inter-trial structure to near rank-1. The reported "n_eff=1 from a real (50 × 5359) PCA" is technically PCA on a real matrix, but the matrix's column structure does not represent 50 distinct strategies — the trial_id axis is a noisy aggregate as described in Check 3. The number 1 is computationally correct given the degenerate input but is not the metric the brief intended.

3. **n_trials = 1000 underestimates the true selection-bias multiplicand**. The DSR formula uses `num_trials = args.n_trials × len(ENSEMBLE_SEEDS) × len(V3_MODELS) × args.seeds = 50 × 5 × 4 × 1 = 1000`. This excludes the 25 walk-forward retraining months, yet each monthly retrain is itself an Optuna study consuming additional selection capacity. The full multiplicand is closer to 1000 × ~25 = 25,000. Since DSR fails at 1000 already, this does not change the verdict; flagged as a documentation concern for next iteration.

The WARN does not by itself trigger BLOCK. The reproducibility properties hold (commit SHA stamped, explicit feature_columns, ensemble seeds literal, trade math reproducible), but two output files report inconsistent PBO values and the n_eff metric is computed from a methodologically suspect aggregation.

### Check 8 — Hypothesis-Implementation Alignment: FAIL

The brief's literal pseudocode (Section 2.4):
```python
combined = (trial_oof
    .groupby(["trial_id", "candle_open_time_ms"])["oof_return"]
    .sum())
```
is exactly what the Engineer shipped at `run_baseline_v3.py:550`. On a strict text-matching read, hypothesis aligns with implementation.

But the brief Section 4.1 made a quantitative prediction: `n_eff_trials > 4` (true PCA on per-trial OOF matrix). The engineering report Section 5 reports `n_eff = 1`. The brief's Section 8 criterion 22 explicitly codifies this prediction as a HARD MERGE GATE: "`dsr.json["n_eff"] > 4` — True". Per the engineering report's own Section 7 table, criterion 22 is **FAIL** (n_eff=1, threshold > 4). Per brief Section 8's "NO-MERGE iff" clause: "Any of the 22 criteria fails" → automatic NO-MERGE. Per brief Section 4.3 Methodology MERGE clause: "ALL methodology-stack criteria pass (criteria 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22)." Criterion 22 is explicitly in the methodology-stack list. The QR's own pre-registered split-merge clause therefore CANNOT trigger.

The mechanism behind the criterion 22 failure is itself a hypothesis-implementation misalignment of a more subtle kind:
- **Brief assumed**: Optuna's `trial_id` would be a meaningful cross-cell index that, when summed over cells, would preserve enough rank for n_eff > 4.
- **Reality**: Each `optimize_and_train` call creates an independent `optuna.create_study()` with its own TPE sampler. `trial_id=0` in cell (BCH, 2023-01, seed=42) and `trial_id=0` in cell (MKR, 2023-02, seed=123) are unrelated models. The `groupby("trial_id").sum()` aggregates noise across ~10 unrelated models per trial_id. The resulting (50 × 5359) matrix is ~rank-1 by construction, hence n_eff=1.

This same construction underlies the PBO=0.0 result: the (45 × 50) path-metric matrix has 50 strategy columns that are degenerate aggregates, not 50 distinct strategies. The CSCV that reports PBO=0.0 is testing whether the IS-best AGGREGATE is in the upper OOS half — not whether the IS-best STRATEGY among 50 contenders generalizes. Both criterion 22 (n_eff > 4) failure and the PBO=0.0 anomalous-cleanness are symptoms of the same root cause: the cross-cell trial_id semantics mismatch.

Engineering report Section 8.2 honestly enumerates the three interpretations (real result / aggregation flaw / trial-ID semantics mismatch) and asks the Critic to adjudicate. Adjudication: interpretation #2 (aggregation flaw) and #3 (trial-ID semantics) are the same problem. The Optuna trial_id is a within-study sequential integer; cross-study comparability requires a different cell-handling strategy (e.g., one parquet per (sym, month, seed) and CSCV computed within a single cell's strategy axis, then aggregated; or a global reservoir sampler that produces N distinguishable strategy specs across cells). The shipped implementation doing `sum`-across-cells with shared trial_id is a brief design error; the implementation faithfully executes what the brief specified, but the brief itself encoded a methodology error that materializes as criterion 22 FAIL.

The brief Section 4.2 secondary falsifier reads: "if `dsr.json["n_eff"]` is exactly 4 (matching the iter-v3/002 surrogate value), sub-fix #3 was not implemented." The shipped value is 1 (not 4), so the secondary falsifier is technically averted. But the spirit of the falsifier — n_eff should reflect the true effective rank of independent trials — is not. n_eff=1 is structurally identical to iter-v3/001's tile-rank-1 tautology, just arrived at by a different broken construction. The shape of the failure is "PCA on a near-rank-1 matrix returns 1" in both cases.

Aggregate verdict on Check 8: FAIL. The pre-registered hard threshold (criterion 22: `n_eff > 4`) is missed, by the Engineer's own report, and the failure traces to a methodology breach in the brief's prescribed aggregation that the implementation faithfully reproduced. The QR's own split-merge clause (Section 4.3) explicitly forbids merge when any methodology-stack criterion fails — criterion 22 is a methodology-stack criterion.

## Recommendations to QR

1. **Per-cell PBO/CSCV with cross-cell aggregation by sample.** The next methodology-axis iteration should compute PBO per (sym, train_month, ensemble_seed) cell — i.e., one CSCV per Optuna study where the 50 trials within that study ARE 50 distinct strategies (their trial_ids are meaningful within the study). Then aggregate cell-level PBOs into a single number via Fisher's method or median-of-PBOs. This avoids the cross-cell trial_id semantic mismatch entirely. Persist per-trial OOF returns as already done, but consume them via the per-cell pathway, not the global `groupby("trial_id").sum()` that destroys per-cell semantics. Critic check: the consumer code MUST run CSCV `n_cells` times (≈500), not once on the aggregated parquet.

2. **Tighten Section 4.2 falsifier text to embed the methodology mechanism, not just the numeric output.** The iter-v3/003 brief's tertiary falsifier ("if `dsr.json["n_eff"]` is exactly 4 ... sub-fix #3 was not implemented") was technically averted by the shipped value of 1, but the spirit was violated — n_eff=1 is structurally the same kind of failure as n_eff=4 (rank tautology from a degenerate construction). Future falsifiers should specify "n_eff > min(N_cells, n_trials/N_cells)" or some other formula that encodes what "real per-trial returns" computationally means. Numerical thresholds without mechanism descriptions are fragile to clever-but-wrong constructions.

3. **Pre-register the cross-cell aggregation method as a Phase 5.5 verifier with a synthetic adversarial test.** The brief Section 2.4 pseudocode (`groupby([trial_id, candle]).sum()`) was the methodology error. Phase 5.5 should require a synthetic adversarial test that constructs (a) a cell where 50 trials are DEEPLY OVERFIT vs (b) a cell where 50 trials are CLEAN, mixes them with the prescribed cross-cell aggregation, and asserts that PBO and n_eff distinguish them. If the prescribed aggregation cannot distinguish the synthetic mix-in, Phase 5.5 BLOCKs before backtest. iter-v3/003's pre-registered `tests/strategies/ml/test_oof_persistence.py` only tested the parquet write side (rows exist, columns correct, cardinality matches) — it did not test that the consumer pipeline preserves strategy-distinguishing signal. The new test class is "consumer-pipeline-preserves-signal", separate from "producer-pipeline-writes-correctly".
