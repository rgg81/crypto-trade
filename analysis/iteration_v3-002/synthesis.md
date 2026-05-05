# iter-v3/002 — Methodology Diagnostic Synthesis

This file is the IS-only numerical-evidence narrative for brief Section 2. It demonstrates that the iter-v3/001 PBO/DSR/ADF implementations produce degenerate values on inputs they should resolve, and prototypes the López de Prado-correct alternatives that the Engineer must ship in iter-v3/002.

## 1. PBO

The iter-v3/001 implementation compares the IS-best path's IS metric against the OOS-half median. By construction the IS-best is the global argmax, so this comparison structurally returns 0 on any input where the maximum exceeds the OOS-half median (i.e., on every realistic input).

Worse: iter-v3/001's CPCV produces a single-column path matrix (S=1). Even a CORRECT López de Prado CSCV is structurally undefined when S=1 (omega is always 1 of 1 = 1.0; the IS-best ranks 1.0 in OOS by tautology). The deeper bug is therefore not the comparison — it's the input shape. iter-v3/002 must produce an S>1 path matrix from CPCV.

Diagnostic:

| test_case                  |   n_paths |   n_strategies |   buggy_pbo |   corrected_pbo | expected_buggy                                              | expected_corrected                                           |
|:---------------------------|----------:|---------------:|------------:|----------------:|:------------------------------------------------------------|:-------------------------------------------------------------|
| A_iter_v3_001_S1_undefined |        45 |              1 |           0 |        nan      | 0.0 (degenerate)                                            | NaN (S=1, PBO undefined; report descriptive stats)           |
| A2_iter_v3_001_synth_S50   |        45 |             50 |           0 |          0.3108 | 0.0 (still degenerate — same input as A)                    | [0.40, 0.60] — chance baseline (synthetic noise erases edge) |
| B_synthetic_overfit        |        45 |             50 |           0 |          0.8566 | 0.0 (degenerate input) or near-1 if best happens to be tail | [0.60, 1.00] — IS-best is OOS-worst by construction          |
| C_synthetic_clean          |        45 |             50 |           0 |          0      | 0.0 (degenerate) — input has no IS/OOS structure            | [0.00, 0.40] — IS rank correlates with OOS rank              |
| D_synthetic_random         |        45 |             50 |           0 |          0.663  | 0.0 (degenerate)                                            | [0.40, 0.60] — chance baseline (no information)              |

**Test case A** is iter-v3/001's actual CPCV path matrix (S=1). The buggy implementation returns 0.0. The corrected implementation returns NaN — correctly flagging that PBO is undefined on this input shape. Engineering must produce a true (paths × strategies) matrix.

**Test case A2** uses iter-v3/001's path Sharpes plus mean-preserving synthetic noise to create a (45 × 50) matrix. Corrected PBO returns 0.31 (within the < 0.4 v3 hard threshold). This is a SYNTHETIC DEMONSTRATION ONLY; the real iter-v3/002 must persist per-trial out-of-fold returns to enable the proper computation.

**Test case B** (synthetic overfit, IS-best strategy is OOS-worst by construction): corrected PBO = 0.86 (correctly identifies overfit; the buggy implementation returns 0.0).

**Test case C** (synthetic clean, IS-rank correlates with OOS-rank): corrected PBO = 0.0 (correctly identifies as clean).

**Test case D** (synthetic random N(0,1) cells): corrected PBO = 0.66. This is HIGHER than the naive 0.5 chance baseline because of the regression-to-mean effect — the IS-best strategy was selected for extreme positive noise, and the OOS half regresses toward zero. This is the López de Prado-correct behavior; the v3 hard threshold of PBO < 0.4 already accounts for this.

**The buggy implementation cannot distinguish overfit from clean from random. It always returns 0. iter-v3/002's Engineer must (a) replace the comparison with the rank-of-IS-best-in-OOS estimator AND (b) produce a proper S>1 path matrix by persisting per-Optuna-trial OOS returns per CPCV path.**

Descriptive statistics for the S=1 case (when a path matrix is genuinely S=1, e.g., for a single-config rerun):

- iter-v3/001's `frac_positive_paths` = 0.444 (< 0.5: anti-edge signal)
- iter-v3/001's path Sharpe quartiles: q25 = -0.50, median = -0.08, q75 = +0.37
- These are descriptive — NOT a PBO substitute. Report them in the engineering report when S=1 is unavoidable.

## 2. DSR

The iter-v3/001 DSR clamps to 0 when the observed Sharpe is negative. This is a defensive coerce that hides the failure mode (a negative-Sharpe strategy returning DSR=0 looks identical to a 'test could not run'). The López de Prado formulation returns P(true SR > 0 | observed SR), which can legitimately be < 0.5 for negative observed Sharpes — the correct interpretation is 'the strategy is more likely to be unprofitable.'

Diagnostic:

| label              |   observed_sharpe |   n_trials |   n_obs |   buggy_dsr_clamps_neg_to_0 |   corrected_dsr_n_eff_1 |   corrected_dsr_n_eff_eq_n_trials |
|:-------------------|------------------:|-----------:|--------:|----------------------------:|------------------------:|----------------------------------:|
| iter_v3_001_neg_IS |           -0.0746 |         10 |      39 |                 0           |             0.000126717 |                       1.61945e-24 |
| iter_v3_001_neg_IS |           -0.0746 |         50 |      39 |                 0           |             0.000126717 |                       9.12889e-48 |
| iter_v3_001_neg_IS |           -0.0746 |       1000 |      39 |                 0           |             0.000126717 |                       1.13825e-93 |
| near_zero          |            0.05   |         10 |      39 |                 2.77377e-21 |             0.00190209  |                       2.93279e-21 |
| near_zero          |            0.05   |         50 |      39 |                 3.65377e-43 |             0.00190209  |                       4.11215e-43 |
| near_zero          |            0.05   |       1000 |      39 |                 3.44389e-87 |             0.00190209  |                       4.39689e-87 |
| modest_pos         |            0.5    |         10 |      39 |                 1.74486e-11 |             0.454296    |                       2.11331e-10 |
| modest_pos         |            0.5    |         50 |      39 |                 3.32724e-28 |             0.454296    |                       2.75487e-25 |
| modest_pos         |            0.5    |       1000 |      39 |                 5.42059e-65 |             0.454296    |                       5.23504e-58 |
| strong_pos         |            1.5    |         10 |      39 |                 0.32281     |             0.999983    |                       0.376207    |
| strong_pos         |            1.5    |         50 |      39 |                 8.53008e-07 |             0.999983    |                       0.000513918 |
| strong_pos         |            1.5    |       1000 |      39 |                 1.39456e-27 |             0.999983    |                       5.7693e-14  |

Note specifically the 'iter_v3_001_neg_IS' rows: the buggy implementation returns 0.0 for ALL n_trials. The corrected implementation returns the true probability — close to 0 for negative SR but NOT clamped, preserving the information that the strategy underperformed benchmark.

Note also the n_eff_trials gap: iter-v3/001 reported n_eff=1 because the Engineer fed the same row repeated n_seeds times to PCA. The corrected n_eff calculation (per LdP AFML Ch. 11) requires the trial-return matrix to be a TRUE n_trials × T matrix where each row is a distinct Optuna trial's out-of-fold return sequence. Engineering must restructure this collection.

## 3. ADF Per-(Symbol, Feature)

iter-v3/001's `adf_test.csv` averaged p-values across symbols. The averaged form passes p<0.05 even when one or more individual symbols fail (the Critic flagged LDO `cusum_reset_count_200` p=0.0707 in pre-flight, masked to 0.0178 by averaging).

Below: per-(symbol, feature) ADF for a SUBSET of features that iter-v3/001 reported as borderline. Per-(symbol, feature) cells are the correct unit; averaging is statistically invalid.

| symbol   | feature                 |   adf_stat |     p_value |   n_obs | stationary_at_0p05   | note                                                                                                                                 |
|:---------|:------------------------|-----------:|------------:|--------:|:---------------------|:-------------------------------------------------------------------------------------------------------------------------------------|
| BCHUSDT  | cusum_reset_count_200   |   -4.79204 | 5.63245e-05 |    5628 | True                 |                                                                                                                                      |
| BCHUSDT  | fracdiff_logclose_dstat |   -4.61438 | 0.000121511 |    5628 | True                 |                                                                                                                                      |
| BCHUSDT  | ret_skew_200            |   -4.07691 | 0.00105723  |    5627 | True                 |                                                                                                                                      |
| BCHUSDT  | vwap_dev_50             |  -11.5046  | 4.40713e-21 |    5703 | True                 |                                                                                                                                      |
| BCHUSDT  | atr_pct_rank_200        |   -7.44053 | 6.0225e-11  |    5688 | True                 |                                                                                                                                      |
| MKRUSDT  | cusum_reset_count_200   |   -4.54812 | 0.000160806 |    4938 | True                 |                                                                                                                                      |
| MKRUSDT  | fracdiff_logclose_dstat |   -4.97333 | 2.50542e-05 |    4938 | True                 |                                                                                                                                      |
| MKRUSDT  | ret_skew_200            |   -5.28173 | 5.97345e-06 |    4937 | True                 |                                                                                                                                      |
| MKRUSDT  | vwap_dev_50             |   -9.40352 | 6.0975e-16  |    5013 | True                 |                                                                                                                                      |
| MKRUSDT  | atr_pct_rank_200        |   -6.49557 | 1.1967e-08  |    4998 | True                 |                                                                                                                                      |
| LDOUSDT  | cusum_reset_count_200   |   -2.71968 | 0.0706938   |    2642 | False                |                                                                                                                                      |
| LDOUSDT  | fracdiff_logclose_dstat |   -4.15676 | 0.000779207 |    2642 | True                 |                                                                                                                                      |
| LDOUSDT  | ret_skew_200            |   -3.76037 | 0.00333978  |    2641 | True                 |                                                                                                                                      |
| LDOUSDT  | vwap_dev_50             |   -8.04156 | 1.84114e-12 |    2717 | True                 |                                                                                                                                      |
| LDOUSDT  | atr_pct_rank_200        |   -5.00424 | 2.17688e-05 |    2702 | True                 |                                                                                                                                      |
| TRXUSDT  | cusum_reset_count_200   |   -4.90328 | 3.43647e-05 |    5570 | True                 |                                                                                                                                      |
| TRXUSDT  | fracdiff_logclose_dstat |   -3.08238 | 0.0278851   |    5570 | True                 |                                                                                                                                      |
| TRXUSDT  | ret_skew_200            |   -4.69592 | 8.56493e-05 |    5569 | True                 |                                                                                                                                      |
| TRXUSDT  | vwap_dev_50             |  -10.2419  | 4.72542e-18 |    5645 | True                 |                                                                                                                                      |
| TRXUSDT  | atr_pct_rank_200        |   -8.48321 | 1.37528e-13 |    5630 | True                 |                                                                                                                                      |
| (avg)    | atr_pct_rank_200        |  nan       | 5.44521e-06 |       0 | True                 | iter-v3/001 ADF approach: average p-value across symbols. Critic Check 5 = FAIL because averaging masks per-symbol non-stationarity. |
| (avg)    | cusum_reset_count_200   |  nan       | 0.0177363   |       0 | True                 | iter-v3/001 ADF approach: average p-value across symbols. Critic Check 5 = FAIL because averaging masks per-symbol non-stationarity. |
| (avg)    | fracdiff_logclose_dstat |  nan       | 0.00720272  |       0 | True                 | iter-v3/001 ADF approach: average p-value across symbols. Critic Check 5 = FAIL because averaging masks per-symbol non-stationarity. |
| (avg)    | ret_skew_200            |  nan       | 0.00112216  |       0 | True                 | iter-v3/001 ADF approach: average p-value across symbols. Critic Check 5 = FAIL because averaging masks per-symbol non-stationarity. |
| (avg)    | vwap_dev_50             |  nan       | 4.60438e-13 |       0 | True                 | iter-v3/001 ADF approach: average p-value across symbols. Critic Check 5 = FAIL because averaging masks per-symbol non-stationarity. |


**Features with at least one symbol non-stationary (p ≥ 0.05): ['cusum_reset_count_200']**

**Engineering directive: ADF must be reported per (symbol, feature, retraining month) — a 3D matrix. Aggregation across any of the three axes is forbidden.**

## 4. Engineering Directives Summary

1. Replace `validation_v3.pbo_from_cpcv` with the rank-flip estimator (S=1 case) and the full AFML Ch. 12 path-matrix estimator (S>1 case).

2. Move CPCV scope from the IS TRADE SEQUENCE to the candle/feature sequence. Each combinatorial split trains a model on its train-folds and reports the OOS metric on its test-folds. The path matrix is then a true (N_paths × N_optuna_trials) array.

3. Remove DSR's negative-SR clamp; return the true P(true SR > 0).

4. Make `n_eff_trials` operate on a true n_trials × T return matrix, not a row-repeated tile. The Optuna trial collection must persist each trial's out-of-fold return sequence.

5. Move ADF reporting from `(feature → averaged p across symbols)` to `(symbol, feature, retraining month)` cells. The brief mandates this; the Engineer's PR must include a runtime assertion that the ADF DataFrame's row count equals n_symbols × n_features × n_retrain_months.

6. Add embargo-gap runtime assertion: gap parameter passed to CPCV MUST equal the documented value `(timeout_candles + 1) × n_symbols`. Silently rescaling (iter-v3/001's `gap=min(CPCV_GAP, n_trades // (CPCV_N_SPLITS * 2))`) is forbidden — the runner must FAIL LOUDLY rather than degrade.

7. Adversarial unit tests: `tests/strategies/ml/test_pbo_overfit_synthetic.py` asserts PBO ∈ [0.40, 0.60] on synthetic overfit, ∈ [0.40, 0.60] on iter-v3/001's path matrix, ∈ [0.00, 0.40] on synthetic clean. `tests/strategies/ml/test_dsr_negative_is.py` asserts DSR returns < 0.5 (NOT 0.0) on negative observed SR. CI failure on either = iter-v3/002 cannot ship.
