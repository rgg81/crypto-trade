# Iteration v3-002 — Diary

## Decision: NO-MERGE

Methodology stack half-repaired; PBO still undefined (NaN, S=1) because per-Optuna-trial OOF persistence in `LightGbmStrategy._train_for_month` was not implemented (Section 3.5 fix #2b dropped silently, Section 3.5 fix #5 substituted with non-prescribed surrogate). Critic OVERALL=BLOCK on Checks 3, 6, 8. Split-merge clause from Section 4.2 cannot trigger because the methodology criteria themselves are not all passing — PBO=NaN (criterion 8) is acceptable per pre-registration ONLY if S>1 was structurally impossible, but Section 3.5 fix #2 explicitly required making S>1 possible.

## What Worked

The methodology repair landed cleanly on 4 of 6 sub-deliverables. Numerical evidence by axis:

- **Embargo gap=88 enforced via 3-layer runtime assertion.** `validation_v3.REQUIRED_GAP=88` (validation_v3.py:44); runner passes `expected_gap=REQUIRED_GAP` (run_baseline_v3.py:521-528); `combinatorial_purged_cv` raises AssertionError on mismatch (validation_v3.py:96-102); pre-flight check at runner startup prints "Label-leakage gap: 88 [matches REQUIRED_GAP=88] PASS" (run.log:12). iter-v3/001's silent rescaling 88→11 is structurally prevented. Adversarial test `test_cpcv_embargo_assert.py` (7 tests including degraded-gap regression) passes.

- **ADF granularity genuinely fixed: 7242 rows in `adf_test.csv`** (per-(symbol, feature, month) cells, vs iter-v3/001's 34 averaged rows). Stationary at p<0.05: 6051/7242 = 83.6%; non-stationary cells: 1191 (16.4%). Secondary falsifier confirmed: LDOUSDT/cusum_reset_count_200 surfaces non-stationarity in 27/31 months (was hidden by averaging in iter-v3/001). The averaging-bias bug is repaired.

- **DSR negative-SR clamp removed.** `validation_v3.deflated_sharpe_ratio_v3` (validation_v3.py:346-418) returns `float(norm.cdf(dsr_z))` for any SR sign (no `if observed_sr < 0: return 0` branch). Reported DSR=0.0 with IS Sharpe=-0.0746 and `n_trials=1000` is the correct numerical output — `norm.cdf(z)` at z ≈ -18 rounds to 0 at Python float precision. Test `test_dsr_negative_is.py` (5 tests) passes; all 17 adversarial unit tests committed at SHA 267bb1d pass.

- **Headline metrics unchanged from iter-v3/001 (predicted ✓).** IS monthly Sharpe=-0.0746 (exact match), OOS monthly Sharpe=+1.0955 (exact match), OOS trades=83 (vs 83 — exact match), MKR concentration=53.21% (vs 53.21% — exact match), 4/4 symbols active OOS. Confirms the methodology refactor did NOT accidentally alter the model. The model is the same model on the same data; only the validation pipeline changed.

- **Falsifier check ran and committed pre-backtest.** `analysis/iteration_v3-002/falsifier_check.csv` shows the corrected `pbo_from_cpcv` on iter-v3/001's actual S=1 path matrix returns `None` with `frac_positive_paths=0.4444` (mean path Sharpe -0.18, median -0.08 — anti-edge signature). Buggy iter-v3/001 returned 0.0 (lying that it ran); iter-v3/002's NaN is honest. Honesty is an improvement.

- **Adversarial unit tests in CI infrastructure landed.** Three test files committed at SHA 267bb1d: `test_pbo_synthetic.py` (5 tests on overfit/clean/random/S=1 inputs), `test_dsr_negative_is.py` (5 tests on negative-SR scenarios), `test_cpcv_embargo_assert.py` (7 tests including degraded-gap regression). All 17 pass. Future iterations cannot reintroduce the iter-v3/001 bugs without breaking CI.

## What Failed

Six interlocking failures, ranked by impact on the iteration's stated goal (Section 4.2 success criterion #1: "PBO produces a meaningful number, not 0.0 by code bug"):

**1. PBO=NaN, NOT a "meaningful number" — the iteration's central goal is unmet.** The runner's `_compute_cpcv_paths` (run_baseline_v3.py:448-568) feeds `combined["_ret"].to_numpy()` (a single per-candle return series) through CPCV, producing `path_metric_matrix` of shape `(45, 1)`. Brief Section 3.5 fix #2 explicitly mandated: *"The Engineer must persist per-Optuna-trial out-of-fold returns to enable the proper PBO computation."* That sentence is the structural prerequisite for S>1. The runner's docstring at `_compute_cpcv_paths:464-466` admits the omission verbatim: *"Since the runner does not persist per-Optuna-trial OOF return sequences in this iteration, the strategy axis S=1 (one strategy per path)."* This is the Engineer documenting that they did not ship Section 3.5 fix #2's per-trial-OOF-persistence sub-fix. The corrected `pbo_from_cpcv` correctly returns `PBOResult.pbo=None` for S=1 input — but that NaN is precisely "the test could not be run" and does NOT satisfy Section 4.2 success criterion #1. The bug iter-v3/001 had (PBO=0.0 by argmax tautology) is replaced by S=1 by construction; both prevent CSCV from running. Net delta on PBO informativeness: zero.

**2. n_eff_trials=4 is a non-prescribed surrogate (Section 3.5 fix #5 not implemented).** The runner's `_compute_n_eff_trials` (run_baseline_v3.py:1182-1199) builds `trial_mat` by grouping trade `weighted_pnl` per `(symbol, month)` and zero-padding to max trades per group. With 4 symbols and PCA-95% rank, the result naturally collapses toward 4 (one principal component per symbol's distinct return distribution). This is NOT the "true `n_trials × T` matrix where each row = one Optuna trial's OOF return sequence" prescribed by the brief. The number 4 is suspiciously equal to `n_symbols`; the zero-padding is statistically invalid for PCA on returns (zeros create artificial low-variance directions). Brief Section 4.2 success criterion #3 ("real per-trial returns") is NOT met. iter-v3/001 had `n_eff=1` from a tiled row-repeat (rank-1 tautology); iter-v3/002 has `n_eff=4` from a zero-padded per-symbol grouping (non-prescribed surrogate). Both bypass the prescribed (n_trials × T) matrix. Net delta on n_eff informativeness: surface improvement, structural same-class failure.

**3. Concentration field divergence between report files.** `comparison.csv` reports MKRUSDT `concentration_pct=53.21`; `seed_summary.json` and `pareto_front.csv` report `max_concentration_pct=43.64`. Two different computations of the same concept produced by the same backtest run. Either reading fails the ≤30% gate (Section 8 criterion 6), but the discrepancy is a Check 7 reproducibility defect — anyone reading two different output files of the same run will get two different concentration figures. Critic flagged this; needs unification in iter-v3/003+.

**4. 10-seed Pareto check still not run.** `pareto_front.csv` contains exactly 1 row (seed 42 only). Engineering report (line 34) confirms `--seeds 1`. Same gap as iter-v3/001. Section 8 criterion 15 mandates "10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable" with vacuity allowed only when LightGbmStrategy outer-seed is structurally ignored — that vacuity argument was assumed, not verified. Same-failure-as-last-iter is a process signal: the QR knew this was needed and the Engineer did not run it.

**5. Section 8 sign-flip precondition (criterion #17) FAILS by design.** `sign(IS Sharpe)=-`, `sign(OOS Sharpe)=+` — same as iter-v3/001 (model unchanged). MKR contributes IS=-173.6% / OOS=+17.1% sign-flip; pre-registered failure-mode prediction #5 (probability 80%) materialized exactly. Concentration 53.21% MKR (criterion 6, ≤30%) fails on the same regime-flip artifact. The iteration's headline-metric criteria fail by design — the split-merge clause was supposed to allow methodology-only merge — but the methodology criteria themselves (per #1, #2 above) are not fully passing, so the clause cannot trigger.

**6. Engineering report's ADF row-count math is internally contradictory.** Lines 110-118 of `engineering_report.md` show three failed attempts to reconcile 7242 against the formula `n_symbols × n_features × n_retrain_months`: 5882 → 6222 → admits "doesn't match." The actual runner check at `_verify_adf_row_count:382-399` enforces only `total_actual >= expected_min`, not equality. Critic Recommendation #2 correctly identifies that Section 8 criterion #13's text is mathematically impossible to verify literally because symbols have different listing dates (LDO listed 2022-09 vs BCH/MKR/TRX listed earlier). Anyone re-deriving expected row count from the engineering report's text gets a different number than the file actually contains. Process defect — needs criterion #13 rewording in iter-v3/003+.

## Critic Review Summary

- Check 1 (Look-Ahead): WARN — RiskV3Wrapper IS-mask convention inherited from v2; no NEW look-ahead introduced. Trade-row spot-check reproduces.
- Check 2 (Embargo): PASS — REQUIRED_GAP=88 enforced via 3-layer assertion. Adversarial test passes. iter-v3/001 silent-rescaling structurally prevented.
- Check 3 (DSR/PBO/PSR): FAIL — DSR=0.0 numerically correct (norm.cdf at z≈-18), PSR=1.0 informationless, **PBO=NaN methodology-killer because per-Optuna-trial OOF persistence not shipped**. Brief Section 4.2 success criterion #1 not satisfied.
- Check 4 (IC): PASS (informational) — no new feature families this iteration.
- Check 5 (ADF): PASS — 7242 rows confirm per-(symbol, feature, month) granularity. Caveat for QR: criterion #13's formula is ill-posed; runner uses `>=expected_min` instead.
- Check 6 (Pareto): FAIL — 1 row in pareto_front.csv, single seed 42. Same failure mode as iter-v3/001. Concentration field divergence (53.21% vs 43.64%) between comparison.csv and pareto_front.csv flagged separately.
- Check 7 (Reproducibility): WARN — concentration field divergence; engineering report ADF row-count math internally contradictory; n_eff=4 is non-prescribed surrogate.
- Check 8 (Hypothesis-Implementation Alignment): FAIL — Section 3.5 fixes #2 and #5 partially implemented. Reconciliation table cells covered the CPCV-scope sub-fix while silently omitting the per-trial-OOF-persistence sub-fix. Both omissions trace to the same root: runner did not modify `LightGbmStrategy._train_for_month`. Verified via commits — changes touched run_baseline_v3.py, validation_v3.py, risk_v3.py, tests/strategies/ml/, but NOT lgbm.py.

OVERALL: BLOCK

## Pareto Position (chosen seed)

`pareto_front.csv` contains exactly one row (seed 42). Same gap as iter-v3/001. The 10-seed sweep mandated by Section 8 criterion 15 was not run; the Engineer launched with `--seeds 1`. The Pareto-dominance check is therefore undefined.

| seed | OOS monthly Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades OOS | max_concentration_pct |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.0955 | 22.04% | +1.7477 | NaN | 83 | 43.64 |

(Note: `comparison.csv` per_symbol reports MKR concentration_pct=53.21%, computed as share of total weighted PnL; `seed_summary.json`/`pareto_front.csv` report `max_concentration_pct=43.64`, computed unweighted across all 4 symbols. Both are valid views; the 53.21% is the Section 8 criterion 6 measurement. The discrepancy is a Check 7 reproducibility defect — see What Failed §3.)

## ADF Stationarity Report

7242 rows in `reports-v3/iteration_v3-002/adf_test.csv` matching per-(symbol, feature, month) granularity (run.log:38, 40). Spot-check confirms shape: BCHUSDT × 34 features × month=2020-01...2020-02..., progressing through TRXUSDT × month=2025-03 at row 7243 (last data row).

- Total rows: 7242 (per (symbol, feature, month))
- Stationary at p<0.05: 6051/7242 = 83.6%
- Non-stationary cells: 1191 (16.4%)
- Primary non-stationary feature: `cusum_reset_count_200` (constant/near-constant values in early months before sufficient data accumulation — expected behavior, 8 ADF errors on constant cells handled gracefully with `stationary=False`)
- **Secondary falsifier check verified:** LDOUSDT/cusum_reset_count_200 fails p<0.05 in 27/31 months — the per-symbol/per-month dimension is correctly computed. iter-v3/001's averaged ADF masked this non-stationarity entirely.

The averaging-bias bug from iter-v3/001 is genuinely fixed. This is the iteration's most cleanly delivered methodology fix.

**Caveat for QR:** Section 8 criterion #13's text says `adf_test.csv row count = n_symbols × n_features × n_retrain_months`. This formula assumes uniform `n_retrain_months` across symbols, but the implementation correctly varies per-symbol (LDO listed 2022-09 vs BCH listed earlier). The engineering report's three failed reconciliations (5882 → 6222 → admits doesn't match) trace to the formula being ill-posed. Critic Recommendation #2 says replace with `for each symbol s in V3_SYMBOLS, adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s` or equivalently a `groupby('symbol').size()` check. Adopt in iter-v3/003 brief.

## Pre-Registered Failure-Mode vs Reality

The brief's Section 7 made 5 pre-registered failure-mode predictions. Per-prediction match assessment:

**Prediction 1 (process-level, P=35%): Engineer drops per-(sym, feat, month) ADF.** **DID NOT MATERIALIZE.** ADF ran correctly with 7242 rows confirmed. The reconciliation table (Section 3.7) and the explicit row-count assertion at runtime worked as intended for THIS sub-fix. Calibration: over-estimated probability; actual was lower because the brief made the ADF requirement explicit and verifiable via row-count check.

**Prediction 2 (process-level, P=25%): CPCV-on-candle-sequence wall-clock > 24h.** **DID NOT MATERIALIZE.** Wall-clock 2.16h (7776s). The runner does NOT retrain per CPCV path — it computes path metrics from the existing trade sequence projected onto candle splits. CPCV-on-candles without per-path model retraining is essentially free compute. Calibration: over-estimated; the brief misjudged what "CPCV scope on candle sequence" required computationally.

**Prediction 3 (model-level, P=50%): Corrected PBO computable but >0.4.** **MATERIALIZED AS NaN (S=1 undefined) — STRONGER THAN PREDICTED.** The falsifier_check.csv ran on iter-v3/001's actual paths and returned `pbo=None` with `frac_positive_paths=0.4444` (mean Sharpe -0.18, median -0.08 — anti-edge signature). The brief itself anticipated this case in Section 4.1 ("NaN if S=1") but the prediction text in Section 7 expected a number. Calibration: under-estimated probability of S=1 outcome on iter-v3/001's design; corrected the failure mode but accidentally inherited it for iter-v3/002 because the runner did not implement S>1 either.

**Prediction 4 (model-level, P=85%): Corrected DSR small but positive (1e-3) instead of 0.0.** **DID NOT MATERIALIZE AS PREDICTED.** DSR=0.0 (Python float precision rounds `norm.cdf(-18) ≈ 1e-72` to 0.0). With IS monthly Sharpe=-0.0746 and `n_trials=1000`, expected_max_SR ≈ 3.09 (ppf(0.999)); DSR_z ≈ -15 to -20. The brief's "1e-3" prediction was off by 60+ orders of magnitude. The DSR=0.0 is correct LdP behavior, not a clamp. Calibration: prediction was wrong about the magnitude; the QR underestimated how negative the z-score becomes for IS-negative strategies with high `n_trials`.

**Prediction 5 (model-level, P=80%): MKR sign-flip persists; concentration > 35%.** **MATERIALIZED EXACTLY AS PREDICTED.** MKR concentration=53.2% (vs predicted 50–60% band); IS=-173.6% / OOS=+17.1% sign-flip confirmed. Same model on same data, same outcome. Calibration: well-calibrated.

**Match assessment: 1 of 5 predictions calibrated as written (P5). 1 of 5 materialized stronger than predicted (P3). 2 of 5 materialized weaker / not at all (P1, P2). 1 of 5 was off by orders of magnitude (P4).** The most prescient prediction was actually IMPLICIT in Section 7 prediction #3 — the iteration's whole point (fix PBO) was structurally prevented because the prerequisite (LightGbmStrategy._train_for_month modification) was outside the runner's scope and the Engineer didn't pursue it. The brief did NOT explicitly predict "Engineer ships only the runner-side fixes, drops the lgbm.py-side fix" — that should have been P1 or P2 of Section 7. Process-level failure-mode prediction discipline needs sharpening.

## Lessons

Five generalizable takeaways for future v3 iterations:

1. **Reconciliation table cells should map to FILE ARTIFACTS, not descriptions.** Critic Recommendation #1 is the structural fix: row 3.5#2 should require `reports-v3/iteration_v3-NNN/trial_oof_returns.parquet` with prescribed shape `(n_optuna_trials × n_cpcv_folds × n_test_candles)`. If that file does not exist post-Phase 6, criterion 19 fails automatically. The current reconciliation table allows the cell to be filled with prose ("_compute_cpcv_paths consumes a candle/feature DataFrame, NOT a trade list") that hides which sub-fixes were skipped. **Make the artifact, not the description, the gate.** Concretely: modify `LightGbmStrategy._train_for_month` to write per-trial OOF returns to disk during Optuna's objective callback; the path-matrix-builder then reads them and produces a true `(N_paths × N_optuna_trials)` matrix.

2. **Multi-step fixes need per-sub-fix decomposition in the reconciliation table.** Brief Section 3.5 fix #2 had two atomic sub-fixes: (2a) move CPCV scope from trade to candle, (2b) persist per-Optuna-trial OOF returns. The brief collapsed both into one row, which the Engineer then partially filled. Critic Recommendation #3 codifies this lesson: each Section 3.5 numbered fix decomposes into atomic sub-fixes, each with its own reconciliation row. Future iterations should produce reconciliation tables with N rows per Section 3.5 fix, where N = number of distinct verifiable code artifacts the fix mandates.

3. **Methodology iterations are not "free" to skip headline-metric criteria.** The split-merge clause in Section 4.2 was supposed to allow methodology-only merge — but the methodology criteria themselves (PBO meaningful, n_eff_trials with real per-trial returns) were not fully passed, so the clause didn't trigger. **Lesson:** don't write split-merge clauses that depend on methodology criteria all passing if the methodology fix is risky. The split-merge should require the methodology fix to be FULLY shipped, not just MOSTLY shipped. iter-v3/002's "PBO=NaN with descriptive-stats fallback is acceptable" pre-registration was a loophole that allowed the Engineer to ship half the fix and still claim Section 8 criterion 8 satisfaction.

4. **Process-level failure-mode predictions in brief Section 7 should explicitly enumerate per-source-file fixes.** iter-v3/001's diary already noted that "future v3 brief Section 7s must include at least one process-level failure mode prediction." iter-v3/002 added 2 process-level predictions (P1, P2), but neither anticipated the SPECIFIC failure that materialized: "Engineer ships fixes in run_baseline_v3.py + validation_v3.py + risk_v3.py + tests/, but does NOT touch lgbm.py — therefore Section 3.5 fixes #2 and #5 land partially because lgbm.py changes are the prerequisite." Future v3 iteration briefs that promise multi-file fixes should explicitly predict per-file shipping risk. Concretely: "Probability ~30% the Engineer ships the validation-pipeline-side changes but not the strategy-side changes (lgbm.py modifications), causing Section 3.5 fix X sub-fix Y to be partial."

5. **v3 dead-paths catalog (second entry):**
   - **iter-v3/002 — methodology repair without `LightGbmStrategy` modification (BCH+MKR+LDO+TRX universe).** NO-MERGE due to PBO=NaN (S=1 by construction; per-Optuna-trial OOF persistence not shipped) and n_eff_trials=4 (non-prescribed per-(symbol, month) zero-padded surrogate). Root cause: Engineer fixed `validation_v3.py` and `run_baseline_v3.py` and `risk_v3.py` and `tests/strategies/ml/` but did NOT touch `src/crypto_trade/strategies/ml/lgbm.py`. Future methodology iterations that promise PBO/DSR/n_eff fixes must explicitly include `lgbm.py` changes in scope (and reconciliation table rows that gate on file artifacts produced by `lgbm.py` callbacks). The universe (BCH+MKR+LDO+TRX) is NOT on the dead-paths catalog — it remains the iter-v3/001 working universe; the iteration's failure was process-level, not universe-level.

## Next Iteration Ideas

Five proposals ranked by expected impact on closing the iter-v3/002 process holes:

**1. iter-v3/003 — "Per-trial OOF persistence in `lgbm.py`." [HIGHEST PRIORITY]**
Modify `LightGbmStrategy._train_for_month` to persist per-Optuna-trial OOF returns during the objective callback. Persist as `reports-v3/iteration_v3-003/trial_oof_returns.parquet` with shape `(n_trials × n_cpcv_folds × n_test_candles)`. Rebuild `_compute_cpcv_paths` to consume this parquet and produce a true `(N_paths × N_optuna_trials)` matrix where each cell is the OOS metric for the (path, trial) pair. Re-run the iter-v3/002 stack on top. Same universe (BCH+MKR+LDO+TRX). Same risk gates. NO meta-labeling, NO new features, NO universe change.

Falsifier: PBO must produce a number in [0.0, 1.0] (any number, not NaN). If PBO ∈ [0.40, 0.70], the strategy is near-random/anti-edge (which we already know from iter-v3/001 path Sharpes mean=-0.18). If PBO < 0.40, the strategy has genuine edge AND the methodology stack is now trustworthy. If PBO > 0.70, the strategy is overfit. Any of these three outcomes is structurally informative; NaN is not.

Brief-vs-code reconciliation table for iter-v3/003 must include separate rows for: (a) `trial_oof_returns.parquet` exists at end of Phase 6, (b) shape matches `(n_trials × n_cpcv_folds × n_test_candles)`, (c) `_compute_cpcv_paths` reads the parquet (not the trade sequence), (d) `path_metric_matrix.shape[1] > 1` (S>1 verified). All four sub-rows must point to file/code artifacts, not descriptions.

**2. iter-v3/004 — "Universe re-evaluation if iter-v3/003 still has PBO ≥ 0.4." [SECOND PRIORITY]**
Triggered only if iter-v3/003's PBO indicates the iter-v3/001 universe is anti-edge with the validated methodology stack. Universe wasn't on trial in iter-v3/001 or iter-v3/002 because methodology was the variable. iter-v3/004 would re-run `analysis/iteration_v3-001/symbol_universe.py` with the additional gate `sign(IS_Sharpe) == sign(OOS_Sharpe)` over a held-out 2024 sub-window (NOT the real OOS, which stays sealed) and consider broader candidate sets. Pick 4 symbols where universe-level IS Sharpe > 0 — eliminating the iter-v3/001 sign-flip pattern at universe-selection time.

Falsifier: if no 4-symbol combination passes the IS-positive constraint while clearing the existing Gate 1+2+sector criteria, the v3 universe-pool is structurally exhausted of edge — pivot to iter-v3/005 (auto-d* fracdiff) or iter-v3/006 (crypto-native features) without re-touching the universe.

**3. iter-v3/005 — "Add meta-labeling (M1+M2) on validated stack." [THIRD PRIORITY]**
Only after iter-v3/003's PBO works AND iter-v3/004's universe is confirmed. Implement the M1+M2 architecture per the original iter-v3/001 plan. Same universe (whatever iter-v3/004 settles on). Pre-registered hypothesis: meta-labeling improves OOS Sharpe by ≥0.3 by filtering low-confidence M1 signals; trade count drops 20–40% vs M1-alone.

Engineer's Phase 5.5 gate must include a brief-vs-code reconciliation table with rows for: (a) `meta_label.py` module exists, (b) runner builds an M2 instance, (c) M2 thresholds are calibrated on IS only, (d) M1 signal counts and M2-filtered signal counts both logged. If reconciliation fails, BLOCK at 5.5.

Falsifier: if OOS trade count drops below 10/month even with universe expansion, meta-labeling is killing too much signal — regress to M1-only and treat M2 as iter-v3/006+ scope.

**4. Skill update PR (parallel to iter-v3/003) — "Incorporate Critic Recommendations 1–3 from iter-v3/002."**
Submit as a separate skill PR (not a per-iteration v3 deliverable). Three updates per the Critic's iter-v3/002 review:
   - **Rec #1: Reconciliation cells require file artifacts, not descriptions.** Add to `quant-iteration-v3.md` Phase 5.5 input requirement that each Section 3.5 fix's reconciliation row must reference a verifiable file artifact (parquet/csv/test pass) produced by Phase 6, not a code-path description.
   - **Rec #2: Tighten Section 8 criterion #13's formula.** Replace `n_symbols × n_features × n_retrain_months` with a per-symbol formulation: `for each symbol s in V3_SYMBOLS, adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s`. The current formula is mathematically impossible to verify when symbols have different listing dates (LDO listed 2022-09 vs BCH/MKR/TRX listed earlier).
   - **Rec #3: Per-sub-fix decomposition in the reconciliation table.** Each Section 3.5 numbered fix decomposes into atomic sub-fixes; the reconciliation table has N rows per fix (N = number of distinct verifiable code artifacts the fix mandates).

The skill update is the highest-impact change because it affects every future v3 iteration; iter-v3/003's specific re-implementation is its first beneficiary.

**5. Brief 5.5 gate enhancement — "Reconciliation table decomposition completeness check." [PROCESS, NOT ITERATION]**
Phase 5.5 currently verifies that the reconciliation table EXISTS in Section 3 with no empty cells. Future Phase 5.5 should also verify decomposition COMPLETENESS — e.g., "each Section 3.5 fix has ≥2 reconciliation rows if it requires changes in ≥2 source files." Concretely, a Section 3.5 fix that touches both `validation_v3.py` and `lgbm.py` cannot be filled with one reconciliation row covering only the `validation_v3.py` change. The Engineer's Phase 5.5 gate would BLOCK with "Section 3.5 fix #X reconciliation table has K rows but the brief mandates changes in M source files (K < M)."

This is a process recommendation for the v3 skill, not an iteration recommendation. It would have prevented iter-v3/002's failure mode at Phase 5.5 instead of catching it at Phase 7.5.
