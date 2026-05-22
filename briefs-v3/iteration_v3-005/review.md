# Phase 7.5 Critic Review — iter-v3/005

OVERALL: BLOCK — Check 3 FAIL on DSR threshold (0.0 < 0.95) inherited unchanged from iter-v3/003-004 plus Check 6 STRUCTURAL FAIL (10-row pareto_front.csv has zero variation on five of six metric axes — the "10-seed" run does not vary the model RNG and therefore cannot satisfy the spirit of the project memory's seed-validation rule), with a contributing Check 8 FAIL on Falsifier #5 / verifier #14 (PBO mean 0.0163 outside the brief's pre-registered [0.05, 0.30] range).

## Per-Check Status

### Check 1 — Look-Ahead Audit: WARN (carried forward)

The model is byte-for-byte unchanged from iter-v3/003 — `analysis/iteration_v3-005/recompute_10seed.py:357-365` copies `in_sample/` and `out_of_sample/` from iter-v3/003 verbatim. No new feature code was introduced. The inherited RiskV3Wrapper IS-mask convention (snapshot at fit-time using `is_mask = table["open_time"] < OOS_CUTOFF_MS`, computed across the FULL IS window) carries forward; iter-v3/002 / iter-v3/003 / iter-v3/004 all registered this as WARN, not FAIL, on the basis that the strict OOS boundary is preserved. The labeling pipeline's triple-barrier ATR uses past-only NATR_21 (no leak). The OOF parquet's `candle_open_time_ms < OOS_CUTOFF_MS` filter is applied at consumer time (`recompute_10seed.py:408`). No NEW look-ahead introduced.

### Check 2 — Embargo Width: PASS

Two CSCV pathways with two distinct purge gaps, both methodologically grounded and inherited unchanged. Global axis: `gap = REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 4 = 88`. Verified at `run_baseline_v3.py:172-184` via `_verify_label_leakage_gap()` startup check and `combinatorial_purged_cv(...expected_gap=REQUIRED_GAP)` AssertionError at `run_baseline_v3.py:539-541`. Per-cell axis (within-symbol variant): `PER_CELL_GAP = 22 = timeout_candles + 1`, confirmed at `recompute_10seed.py:65` and used at line 202 (`gap=PER_CELL_GAP`). The `× n_symbols` multiplier is correctly omitted because each per-cell tile is single-symbol. Both invariants preserved from iter-v3/004; this iteration does not modify the gap configuration.

### Check 3 — Multiple-Testing Correction: FAIL

- **DSR = 0.0 (threshold > 0.95): FAIL.** Computed correctly per `validation_v3.deflated_sharpe_ratio_v3` from raw IS Sharpe ≈ -0.034 (monthly Sharpe = -0.0746 over 225 trades). With `n_trials = 1000`, `expected_max_SR ≈ 3.09`, and `DSR_z ≈ -18`, `norm.cdf(z)` rounds to 0 at Python float precision. The clamp-free implementation is sound; DSR=0.0 is the right answer for this strategy on this universe. Identical numerator and denominator as iter-v3/003 / iter-v3/004 (model unchanged). Per iter-v3/003 / iter-v3/004 Critic precedent: "Any single threshold missed = FAIL." The skill rule is unconditional. The QR's split-merge clause exists at the brief level, but Critic's per-check thresholds are not partitioned in the current skill definition.

- **PBO = 0.0163 (threshold strict (0,1) per Section 8 criterion 21; auto-NO-MERGE threshold < 0.4): PASS.** Methodologically defensible. Per `validation_v3.py:302-345`, the iter-v3/005 modification adds `rng` to `pbo_from_cpcv`; when `rng is not None and n_total_splits > max_splits`, the function draws 5000 IS/OOS combinations uniformly at random (without replacement) via `rng.choice(n_paths, size=half, replace=False)` rather than enumerating the first 5000 from `itertools.combinations`. With C(45, 22) ≈ 6.5e12 total possible splits, the random-sampling estimate has Monte Carlo std ≈ √(0.0163 × 0.9837 / 5000) ≈ 0.0018, consistent with the observed cross-seed std of 0.0001 averaged over 173 cells. The implementation is correct; PASS in form.

- **PSR = 1.0 (threshold > 0.95): PASS** in form, vacuous. Identical to iter-v3/002 / iter-v3/003 / iter-v3/004 (computed deterministically from OOS Sharpe ≈ 2.205 over 83 trades).

- **n_eff = 25 (threshold > 4 per Section 8 criterion 22): PASS.** Per-cell median across 173 informative cells. CSV spot-check confirms a healthy right-tail distribution (`per_cell_pbo.csv` quartiles match iter-v3/004 because the seed only affects PBO, not n_eff).

- **n_trials = 1000**: same understatement as iter-v3/003 / iter-v3/004 (excludes the 25 walk-forward retraining months). DSR fails at 1000 already, so the documentation gap is moot for this iteration.

Aggregate verdict on Check 3: **FAIL** because the DSR threshold is missed (0.0 < 0.95), per literal skill spec and iter-v3/003 / iter-v3/004 precedent. The PBO methodology axis PASSes.

### Check 4 — IC Correlation: PASS (vacuous)

`reports-v3/iteration_v3-005/ic_matrix.csv` present, 34 features × 34 features pairwise Pearson on IS-pooled BCH+MKR+LDO+TRX (file copied byte-for-byte from iter-v3/003 by `recompute_10seed.py:372-377`). No new feature families added; brief Section 3.3 declares `V3_FEATURE_COLUMNS UNCHANGED, len=34`. Pre-existing cross-family pairs above 0.7 (`atr_pct_rank_200` ↔ `atr_pct_rank_500` ≈ 0.826) were already flagged in iter-v3/001 / iter-v3/002 / iter-v3/003 / iter-v3/004 reviews and are not introduced by this iteration. Vacuous PASS, same precedent.

### Check 5 — ADF Stationarity: PASS

`reports-v3/iteration_v3-005/adf_test.csv` has 7242 data rows, identical to iter-v3/003 / iter-v3/004 (file copied verbatim by `recompute_10seed.py:372-377`). Per-(symbol, feature, retraining month) granularity; ~83.6% stationary at p<0.05 unchanged. ADF rows are not affected by the iter-v3/005 consumer-side modification.

### Check 6 — Pareto Dominance: FAIL (STRUCTURAL — false-positive PASS appearance)

`pareto_front.csv` contains 10 rows. Headline numbers say "PASS": mean monthly Sharpe = +1.0955, 10/10 seeds profitable. **This is a false-positive PASS.** Inspection of the 10 rows reveals a structural defect in what "10 seeds" means in this iteration.

Verbatim from `reports-v3/iteration_v3-005/pareto_front.csv`: every single seed produces `monthly_sharpe=1.0955`, `max_drawdown=22.0437`, `calmar=1.7477`, `n_trades=83`, `max_concentration_pct=43.64`, `n_eff=25`. The ONLY axis that varies is `pbo`, and its cross-seed std is 0.0001 — pure Monte Carlo sampling noise from the 5000-split random sampler.

Mechanism (verified by reading `recompute_10seed.py:339-528` and `validation_v3.py:193-345`): the iter-v3/005 "outer seed" is fed only into `np.random.default_rng(seed)` at `recompute_10seed.py:427` and then passed via `rng=rng` to `pbo_from_cpcv` at `recompute_10seed.py:218`. The seed has zero effect on the LightGBM training trajectory, the inner ensemble, the Optuna TPESampler, the RNG state of `optimize_and_train`, or the trades — the trades CSVs are copied byte-for-byte from iter-v3/003 (`recompute_10seed.py:357-365`). The headline metrics are read directly from `comparison.csv` at `recompute_10seed.py:392`, which itself was copied from iter-v3/003. The "10-seed Pareto" varies a downstream consumer-side PBO sampler only.

The project memory rule (`feedback_seed_validation.md`: "Before MERGE: run 10 seeds, mean Sharpe > 0, ≥ 7/10 profitable") was designed to test cross-seed *model* stability — different inner ensemble seeds → different TPE trajectories → different LightGBM ensembles → different OOS PnL distributions. iter-v3/005 does not test that; it tests cross-seed PBO sampling stability, which is a different (and much weaker) property. With 10 IDENTICAL Sharpe rows, the "10/10 profitable" outcome is mechanically equivalent to "1/1 profitable" — the seed dimension contributes zero information about model robustness. Pareto non-dominance is also vacuous: every row has the same metric vector for {Sharpe, MaxDD, Calmar, n_trades, concentration}, so "non-dominated" is a tautology unless one tie-breaks on PBO, in which case all 10 are co-optimal.

This is a FAIL on Check 6's stated purpose. The chosen seed (42) is "non-dominated" but there is no Pareto front to dominate. The single-metric tunnel-vision criterion (winning on ≥2 of {Sharpe, MaxDD, n_trades}) cannot be applied because all 10 rows tie.

Note: the iteration's implementation matches the brief's spec — the brief explicitly stated in Section 3.5 sub-fix #1 "Headline IS/OOS metrics MATCH iter-v3/004 EXACTLY for the seed=42 row (model unchanged)" and Section 4.1 predicted EXACT seed-invariance. The brief honestly disclosed the structure. But disclosure does not convert a structurally-vacuous Pareto into a meaningful one.

### Check 7 — Reproducibility: PASS

- Code commit SHA stamped: `591d1cd0bfe503777a3cb31e15f343b1eac4b687` (engineering report Header line 7).
- Runner uses explicit `feature_columns=list(V3_FEATURE_COLUMNS)` at `run_baseline_v3.py:830`; LightGbmStrategy raises on None/empty per project conventions. Inherited from iter-v3/004, unchanged.
- `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literal verified at `recompute_10seed.py:441`.
- Pareto file consistency: `dsr.json["pbo"] = 0.016298` matches `pareto_front.csv` row[seed=42]["pbo"] = 0.016298, matches `seed_summary.json[0]["mean_pbo"] = 0.016298`. Three persistence files agree on the seed=42 PBO value (iter-v3/003 / iter-v3/004 PBO field divergence WARN remains closed).
- Library versions stamped: numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1.
- Pre-flight `--seeds 1` (98.2s) and `--seeds 2` (180.0s) confirmed linear scaling; full `--seeds 10` ran in 837.8s, well under the 60-min budget.

### Check 8 — Hypothesis-Implementation Alignment: FAIL

The brief's hypothesis ("running the iter-v3/004 per-cell PBO consumer pipeline across 10 outer seeds will produce a 10-row pareto_front.csv that satisfies project memory's seed-validation rule") is implemented as written, AND verifier #14's pre-registered range was missed.

- Verifier #14 explicitly states: `per-seed PBO mean across 10 seeds in [0.05, 0.30]`. Actual: 0.01639 < 0.05. **Verifier #14 FAILS**, triggering brief Section 4.3 Falsifier #5 ("the headline aggregator drifts under cross-seed noise").
- Section 8 criterion 19 ("Brief-vs-code reconciliation table has no empty cells AND every row's verifier command exits 0") is therefore PARTIAL FAIL by the Engineer's own report (table line 224, "PARTIAL FAIL — verifier #14 fails").
- The Engineer's defense ("brief's [0.05, 0.30] range was calibrated against biased deterministic PBO, not unbiased random-sample PBO; methodological finding, not a code bug") is logically coherent but does not exempt the iteration from criterion 19. The brief's predicted range was wrong; the predicted falsifier triggered. This is exactly what falsifiers are for. The QR pre-registered the range; the Engineer's run falsified it.
- More importantly, the Engineer's defense REOPENS a methodology question about iter-v3/004 ("iter-v3/004's PBO of 0.1305 was biased upward by ~8x"). The Critic does not retroactively re-open closed reviews, but flags this for the QR's diary: if the iter-v3/005 random-sampling PBO of 0.0163 is the correct unbiased estimate, then iter-v3/004's PBO=0.1305 was systematically biased — meaning iter-v3/004's headline methodology number was wrong. This does not change iter-v3/004's diary outcome (BLOCK on DSR), but it should be recorded as a methodology calibration finding. The QR should not silently advance the methodology with iter-v3/004's number quoted as "ground truth" when iter-v3/005's evidence shows it was 8x biased.

Two QR-level concerns embedded in the brief's design:

1. **Brief Section 1's "10-seed pareto_front satisfies the seed-validation rule" hypothesis is satisfied trivially.** Section 4.1 predicted EXACT seed-invariance ("EXACT" in the prediction column for monthly_sharpe / max_drawdown / calmar / n_trades / concentration). When the brief predicts that the seed dimension does nothing, satisfying the seed-validation rule with such a setup is structurally meaningless. This is a Check 8 design issue, not an implementation issue, but it materially affects whether Check 6's PASS counts.

2. **Verifier #14 prediction error.** The QR's brief Section 2.2 acknowledged the synthetic 10-seed PBO std was 0.0205 from path-permutation but predicted the true 10-seed run would lie in [0.05, 0.30] from "outer-seed model retraining". The Engineer's run does NOT retrain the model — the brief itself specified parquet REUSE with no rebacktest. The QR's range was incompatible with the QR's own design from Phase 5; this should have been caught at Phase 5.5. The Phase 5.5 gate signed off on this brief; the gate did not detect the inconsistency between Section 2.2's "true 10-seed run varies the OUTER seed driving model training" and Section 3.7's "NO model change" / Section 4.1's "EXACT match on headline metrics".

## Optional Checks 9–12

- **Check 9 — Symbol Exclusion Enforcement**: PASS. `run_baseline_v3.py:_verify_symbols()` (lines 130-137) raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` is non-empty.

- **Check 10 — Feature Isolation**: PASS. `_verify_track_isolation()` greps for `from crypto_trade.features` / `features_v2` in `features_v3/` and raises on any match. Confirmed via Grep: no cross-track imports found in `src/crypto_trade/features_v3/`.

- **Check 11 — Forming-Candle Audit**: PASS. `_verify_data_freshness()` hard-fails at startup if any symbol's `close_time` lag exceeds 16h. Inherited from iter-v3/003-004 unchanged.

- **Check 12 — Library Version Pinning**: PASS. Engineering report stamps numpy==2.2.6, scipy==1.17.0, statsmodels==0.14.6, scikit-learn==1.8.0, lightgbm==4.6.0, pytest==9.0.2, pandas==3.0.0, pyarrow==23.0.1; identical to iter-v3/004 versions.

## Recommendations to QR

OVERALL=BLOCK is final for this iteration. Three process-level recommendations for FUTURE iterations:

1. **Stop using consumer-side `rng` permutations as a substitute for true 10-seed model validation.** The project memory rule (`feedback_seed_validation.md`) is unambiguous: 10 seeds means 10 different LightGBM training trajectories with 10 different inner ensemble configurations producing 10 different OOS trade distributions. iter-v3/005's "10 seeds" varies only the per-cell PBO bootstrap sampler — a downstream methodology knob with no model-side effect. The fact that all 10 rows of `pareto_front.csv` have identical Sharpe / MaxDD / n_trades is structural proof that the seed dimension is being misused. The Pareto check has now been "PASSed" once in v3 history — but PASSed structurally vacuously, which is worse than the iter-v3/001-004 single-row FAILs (those at least did not pretend to be 10-seed). For iter-v3/006 onwards, "10-seed pre-MERGE" must mean retraining the model (or at minimum re-running the inner ensemble's OOF construction) under each outer seed, even if expensive. If the wall-clock cost is prohibitive on the full universe, scope the validation to a 2-symbol subset or a 6-month window — ANY model-side variation beats consumer-side variation that produces tied metrics.

2. **The verifier #14 calibration miss exposes a Phase 5.5 gate gap: the gate does not check internal consistency of the brief's Section 2 assumptions against Section 3 implementation constraints.** Brief Section 2.2 stated "the true 10-seed outer variation is larger" and predicted PBO std in [0.05, 0.20]. Brief Section 3.7 stated "NO model change". These are mathematically inconsistent — if the model does not change, the PBO variation is bounded by the consumer-side sampler's Monte Carlo variance only. The Phase 5.5 gate should have demanded the QR reconcile these two sections OR reject the brief. Skill update: add to `quant-iteration-v3.md` Phase 5.5 a check "Verifier predicted ranges in Section 4.x must be consistent with the model-change scope declared in Section 3.7 / 3.5 (e.g., consumer-only changes can only produce Monte Carlo-bounded variance)".

3. **iter-v3/004's PBO of 0.1305 should be re-examined in the iter-v3/005 diary.** The Engineer's report claims iter-v3/004's deterministic-first-5000 enumeration produced a systematically biased estimate (8x inflated relative to random-sample). If true, this is a methodology finding worth investigating: was the iter-v3/004 PBO of 0.1305 actually right (because deterministic-first-5000 happens to be "good enough" given the cell distribution) or actually wrong (because lexicographic-order combinations cluster around small-IS / large-OOS indices and bias the estimator)? Construct a synthetic test in `tests/strategies/ml/`: generate a known-PBO matrix (e.g., the synthetic overfit / clean cells from iter-v3/004's `test_per_cell_pbo_synthetic.py`), compare deterministic-first-5000 PBO to random-sample PBO to enumeration-PBO (when N is small enough). If deterministic-first-5000 is systematically biased, replace it with random-sample as the default in `pbo_from_cpcv` (independent of the `rng` parameter being supplied) — and document this as a methodology fix in iter-v3/006's brief, not buried in iter-v3/005's anomaly notes.
