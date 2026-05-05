# Iteration v3-005 — Diary

## Decision: NO-MERGE

Critic OVERALL=BLOCK on Check 3 DSR=0<0.95 (inherited unchanged from iter-v3/003-004) + Check 6 STRUCTURAL FAIL + Check 8 verifier #14 calibration miss. All Section 8 methodology axes pass in form, but criterion 15's PASS is structurally vacuous: the 10-row `pareto_front.csv` has IDENTICAL Sharpe / MaxDD / Calmar / n_trades / concentration on every row because the outer seed only varies the per-cell PBO bootstrap sampler — a downstream methodology knob with no model-side effect. The trades CSVs are byte-for-byte copies of iter-v3/003's. Mechanically, "10/10 profitable" is equivalent to "1/1 profitable". Per Critic: "PASSing Check 6 trivially is worse than the iter-v3/001-004 single-row FAILs (those at least did not pretend to be 10-seed)." Section 8 criterion 16 (Critic OVERALL=MERGE) FAILS = NO-MERGE; criterion 19 (reconciliation, all verifiers exit 0) PARTIAL FAIL on verifier #14 (`pbo_mean=0.0163 ∉ [0.05, 0.30]`) = NO-MERGE.

## What Worked

- **10-seed wall-clock budget**: 13m 57s for 10 seeds (vs the brief's 30-min Phase 6 budget; Engineer's pre-flight at 1-seed=98s and 2-seed=180s confirmed linear scaling).
- **Per-cell PBO methodology pipeline runs deterministically across 10 seeds with std=0.0001** (Monte Carlo floor noise √(p(1-p)/5000) ≈ 0.0018 at p=0.016). The `rng`-parameterised random-sample modification in `pbo_from_cpcv` is correct and well-conditioned.
- **`tests/strategies/ml/test_ensemble_seed_propagation.py` adversarial test landed and PASSes on iter-v3/003 parquet at 76.55% nunique-fraction (≥50% threshold)** — confirms the QR's Phase 5 analysis script finding that the seed dimension carries real signal in 76.55% of natural-key groups. **iter-v3/004's "100% degenerate" claim was REFUTED.** Actual breakdown: 23.45% degenerate, 76.55% variable. The producer-side fix in iter-v3/006 should ADD a `seed` column to `optimization.py:400-421`, not drop the dimension.
- **PBO field divergence WARN stays closed**: 3 persistence files (`dsr.json`, `pareto_front.csv` row[seed=42], `seed_summary.json[0]`) all agree on 0.016298.
- **Engineer's pre-flight (1-seed, 2-seed scaling) caught no regressions** — Section 7 Prediction P1 (single-seed pathway regression) did not materialize.
- **27/27 adversarial unit tests pass** — engineer-reported actual count is 26 inherited + 3 new = 29 (richer than the 1-test spec; brief predicted 27, actual 29). All pass.

## What Failed

1. **Check 6 STRUCTURAL FAIL — the deepest finding of this iteration.** The brief's Section 1 hypothesis was implemented as written, but the implementation produced a Pareto front where all 10 rows have IDENTICAL Sharpe / MaxDD / Calmar / n_trades / concentration. The "10 seeds" only varies the per-cell PBO bootstrap sampler — a downstream methodology knob with no model-side effect. The trades CSVs are copied byte-for-byte from iter-v3/003 (`recompute_10seed.py:357-365`). The project memory rule (`feedback_seed_validation.md`) was designed to test cross-seed *model* stability — different inner ensemble seeds → different TPE trajectories → different LightGBM ensembles → different OOS PnL distributions. iter-v3/005 does not test that; it tests cross-seed PBO sampling stability, which is a different (and much weaker) property. iter-v3/005's "PASS" on criterion 15 is FALSE-POSITIVE — mechanically equivalent to 1-seed validation.

2. **Verifier #14 (Check 8 FAIL).** Brief Section 2.2 predicted PBO std in [0.05, 0.20] from "outer-seed model retraining". Brief Section 3.7 / 4.1 explicitly specified NO model change. These are mathematically inconsistent — if the model doesn't change, PBO variation is bounded by the Monte Carlo variance of the consumer-side sampler (≈0.0018 at p=0.016). The QR's range was incompatible with the QR's own design. **Phase 5.5 gate signed off on this brief; the gate did not detect the inconsistency.** Per Critic Recommendation #2: skill update should add a Phase 5.5 check "Verifier predicted ranges in Section 4.x must be consistent with the model-change scope declared in Section 3.7 / 3.5".

3. **iter-v3/004's PBO=0.1305 was likely 8x biased upward** (per Engineer's claim, supported by iter-v3/005's 0.0163 random-sample value: ratio 0.1305 / 0.0163 ≈ 8). The deterministic-first-5000 enumeration via `itertools.combinations(range(45), 22)` generates combinations in lexicographic order — the first 5000 cluster around "small IS indices vs. large OOS indices", creating systematic bias in which paths are evaluated as IS vs. OOS. If true, this is a methodology finding affecting iter-v3/004's headline number; iter-v3/006 should investigate via synthetic test and consider replacing deterministic-first-5000 as the default.

4. **Inherited Check 3 (DSR=0 < 0.95)**: same as iter-v3/003-004; not addressable on this universe with this model. The skill rule "Any single threshold missed = FAIL" applies regardless of the QR's split-merge clause being a brief-level construct.

## Critic Review Summary

| Check | Verdict | Note |
|---|---|---|
| 1 — Look-Ahead Audit | WARN (carried) | Inherited RiskV3Wrapper IS-mask convention; no NEW look-ahead introduced |
| 2 — Embargo Width | PASS | Both global (88) and per-cell (22) gaps preserved |
| 3 — Multiple-Testing Correction | **FAIL** | DSR=0.0 < 0.95 (inherited); PBO=0.0163 PASS in form; PSR=1.0 PASS vacuous; n_eff=25 PASS |
| 4 — IC Correlation | PASS (vacuous) | ic_matrix.csv copied verbatim; pre-existing 0.826 family pair already flagged |
| 5 — ADF Stationarity | PASS | 7242 rows, 83.6% stationary, copied verbatim |
| **6 — Pareto Dominance** | **FAIL (STRUCTURAL)** | 10 rows all identical on 5 of 6 metric axes; only PBO varies (std=0.0001 = MC noise floor) |
| 7 — Reproducibility | PASS | SHA stamped, libs pinned, 3-file PBO concordance, pre-flight clean |
| **8 — Hypothesis-Implementation Alignment** | **FAIL** | Verifier #14 falsified (pbo_mean=0.0163 ∉ [0.05, 0.30]); Section 2.2 / 3.7 / 4.1 internally inconsistent |
| 9 — Symbol Exclusion | PASS | `_verify_symbols()` enforced |
| 10 — Feature Isolation | PASS | No cross-track imports in features_v3/ |
| 11 — Forming-Candle Audit | PASS | 16h staleness guard inherited |
| 12 — Library Version Pinning | PASS | numpy 2.2.6, scipy 1.17.0, statsmodels 0.14.6, sklearn 1.8.0, lgbm 4.6.0 |

**OVERALL: BLOCK.**

## Pareto Position (chosen seed)

10-row `pareto_front.csv` BUT all rows IDENTICAL on 5 of 6 metric axes (Sharpe, MaxDD, Calmar, n_trades, concentration). The single-row FAIL precedent of iter-v3/001-004 was technically broken in form, but the form is structurally vacuous. The chosen "non-dominated" seed (42) is non-dominated only because every other seed has the same metric vector — a tautology, not a Pareto-front signal.

| Seed | Sharpe | MaxDD | Calmar | PBO | n_trades | max_conc% | n_eff |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 1.0955 | 22.0437 | 1.7477 | 0.016298 | 83 | 43.64 | 25 |
| 17 | 1.0955 | 22.0437 | 1.7477 | 0.016191 | 83 | 43.64 | 25 |
| 100 | 1.0955 | 22.0437 | 1.7477 | 0.016506 | 83 | 43.64 | 25 |
| 999 | 1.0955 | 22.0437 | 1.7477 | 0.016415 | 83 | 43.64 | 25 |
| 8675309 | 1.0955 | 22.0437 | 1.7477 | 0.016273 | 83 | 43.64 | 25 |
| 0 | 1.0955 | 22.0437 | 1.7477 | 0.016320 | 83 | 43.64 | 25 |
| 12345 | 1.0955 | 22.0437 | 1.7477 | 0.016563 | 83 | 43.64 | 25 |
| 67890 | 1.0955 | 22.0437 | 1.7477 | 0.016410 | 83 | 43.64 | 25 |
| 314159 | 1.0955 | 22.0437 | 1.7477 | 0.016326 | 83 | 43.64 | 25 |
| 271828 | 1.0955 | 22.0437 | 1.7477 | 0.016562 | 83 | 43.64 | 25 |

Mean PBO 0.01639, std 0.0001 — pure Monte Carlo sampling-noise floor.

## ADF Stationarity Report

7242 rows, inherited byte-for-byte from iter-v3/003 (file copied verbatim by `recompute_10seed.py:372-377`). Same 83.6% stationary rate at p<0.05 across (symbol, feature, retraining month). No new findings.

## Pre-Registered Failure-Mode vs Reality

| Pred | Type | P | Outcome | Note |
|---|---|---:|---|---|
| P1 | process | 15% | DID NOT MATERIALIZE | Single-seed pre-flight clean (98.2s); reconciliation row 10 PASSes |
| P2 | process | 10% | DID NOT MATERIALIZE | Test exists, runs, PASSes; documented at 76.55% in engineering report |
| P3 | process | 15% | DID NOT MATERIALIZE | Wall-clock 13m 57s, well under 60-min budget; parquet read once + shared |
| P4 | model | 30% | DID NOT MATERIALIZE | Mean Sharpe = +1.0955 ≥ +0.5; **but trivially because all 10 seeds tied to seed=42 trades** |
| P5 | model | 70% | MATERIALIZED EXACTLY | std=0.0001 < 0.05 ✓; headline EXACT match ✓ |

**Match assessment**: 5/5 predictions correct in literal form. **But P5's "low cross-seed std" should have been a flag during Phase 5** — if the std is structurally bounded by Monte Carlo noise, then P4's "mean Sharpe across 10 seeds" can't be a meaningful statistic. The QR's process-level prediction discipline missed the deeper question: **is the brief's design even capable of falsifying the project memory's seed-validation rule?** The answer is no — by Phase 5 design, the seed dimension was orthogonal to the model. P4 was structurally unfalsifiable given the design.

## Lessons

1. **The "10-seed" rule means RETRAINING THE MODEL, not just resampling the PBO Monte Carlo.** This is the Critic's headline lesson and supersedes iter-v3/004 lesson #1. iter-v3/006 must vary the inner ensemble RNG (or at minimum re-run `optimize_and_train` under each outer seed) to produce 10 distinct LightGBM ensembles with 10 distinct OOS trade distributions. If the wall-clock cost is prohibitive on the full universe (10 × 3.6h ≈ 36h), scope to a 2-symbol subset OR a 6-month window. **ANY model-side variation beats consumer-side variation that produces tied metrics.** Add to dead-paths catalog: "consumer-side rng substitution for model-side rng = false-positive Pareto PASS, structurally worse than single-row FAIL."

2. **Phase 5.5 gate must check internal consistency of brief Sections 2/3/4.** The QR's Section 2.2 prediction range [0.05, 0.30] for cross-seed PBO std was incompatible with Section 3.7 / 4.1 "NO model change" + EXACT headline-metric match. The Phase 5.5 gate signed off without catching this. Per Critic Recommendation #2: skill update should add a Phase 5.5 check "Verifier predicted ranges in Section 4.x must be consistent with the model-change scope declared in Section 3.7 / 3.5 (e.g., consumer-only changes can only produce Monte Carlo-bounded variance ≈ √(p(1-p)/N_samples))".

3. **iter-v3/004's PBO=0.1305 was deterministic-first-5000 biased.** The Engineer claims 8x bias relative to random-sample (0.1305 / 0.0163 ≈ 8). If correct, this is a methodology finding worth investigating in iter-v3/006 via synthetic test. The current `pbo_from_cpcv` defaults to deterministic-first-5000 enumeration; iter-v3/006 should consider making random-sample the default (or at least documenting the bias direction in the docstring). The mechanism is plausible: `itertools.combinations(range(45), 22)` generates combinations in lexicographic order, and the first 5000 cluster around "small IS indices vs. large OOS indices" — a non-uniform sample of the C(45, 22) ≈ 6.5e12 population.

4. **The 76.55% non-degenerate finding for ensemble seeds is genuine but unlabeled.** iter-v3/004's brief Section 2.1 stated "100% degenerate" — wrong. Actual is 23.45% degenerate / 76.55% variable. The producer-side fix is to ADD a `seed` column to `optimization.py:400-421` (preserving information that already exists in the parquet's row-level data), NOT drop the dimension. iter-v3/006 should ship this — it is a low-risk, high-value schema fix that unlocks correct per-seed consumer pipelines downstream.

5. **dead-paths catalog (fifth entry):** iter-v3/005 — 10-seed Pareto with consumer-side rng substitution. NO-MERGE due to Critic OVERALL=BLOCK. **Method failure**: outer seed only varied per-cell PBO bootstrap sampler, NOT model RNG. All 10 trades CSVs are byte-for-byte copies of iter-v3/003's. Pareto check is structurally vacuous (10 identical rows on 5 of 6 metric axes). Producer-side ensemble seed propagation finding (76.55% non-degenerate) is genuine and refutes iter-v3/004's stale "100% degenerate" claim. iter-v3/006 must do TRUE 10-seed model retraining, even if expensive (scope-down to 2-symbol or 6-month subset acceptable).

## Next Iteration Ideas

**1. iter-v3/006 — "TRUE 10-seed model retraining + iter-v3/004 PBO bias investigation + ensemble seed column" [HIGHEST PRIORITY]**
   - **(a)** Run TRUE 10-seed Pareto by varying the inner ensemble RNG. Each outer seed produces 10 distinct LightGBM ensembles with 10 distinct OOS trade distributions. Wall-clock budget: 10 × 3.6h = 36h on full universe. **Scope-down to 1-symbol BCH-only OR 6-month 2024 sub-window** to fit in 4-6h budget. Falsifier: if scoped 10-seed shows std < 0.10 on Sharpe AND mean Sharpe > 0 AND ≥7/10 profitable, the methodology PASS is genuine.
   - **(b)** Synthetic test for iter-v3/004 PBO bias: generate a known-PBO matrix (use the synthetic overfit/clean cells from iter-v3/004's `test_per_cell_pbo_synthetic.py`), compare deterministic-first-5000 PBO vs random-sample PBO vs enumeration-PBO (when N small). Document bias direction in `tests/strategies/ml/test_pbo_sampling_bias.py`. If deterministic-first-5000 is systematically biased, replace as default in `pbo_from_cpcv`.
   - **(c)** Ship the producer-side `seed` column fix in `optimization.py:400-421` so the parquet preserves per-seed-distinct OOF returns natively (the 76.55% signal already exists; just add the label).

**2. iter-v3/007 — "Universe re-evaluation if iter-v3/006 (a) shows mean Sharpe < 0 or ≥4/10 unprofitable" [SECOND PRIORITY]**
   Triggered only if iter-v3/006's true 10-seed scoped run shows the BCH+MKR+LDO+TRX universe is anti-edge under model variance. Re-run `analysis/iteration_v3-001/symbol_universe.py` with the additional gate `sign(IS Sharpe) == sign(OOS Sharpe)` over a held-out 2024 sub-window.

**3. iter-v3/008 — "Add meta-labeling on validated stack" [THIRD PRIORITY]**
   Only after iter-v3/006 confirms a non-anti-edge methodology stack. Implement M1+M2 architecture per the original iter-v3/001 plan. With per-cell PBO methodology now BIAS-CORRECTED (iter-v3/006 sub-fix b), the M1+M2 evaluation has a trustworthy diagnostic.

**4. Skill update PR (parallel to iter-v3/006).**
   Per Critic Recommendation #2: update `quant-iteration-v3.md` Phase 5.5 to require internal-consistency check between brief Sections 2/3/4. Per iter-v3/004 Critic Rec #1 (still pending): split Check 3 into 3a (methodology: PBO/n_eff thresholds) + 3b (edge: DSR/PSR thresholds). Both updates are cheap and unblock future iterations.

**5. Brief Section 4.x calibration discipline.**
   iter-v3/005's verifier #14 calibration miss exposes a recurring v3 issue: pre-registered numerical ranges that are wrong make the iteration "fail" even when the methodology works. Future briefs should:
   - State the deterministic baseline FIRST (e.g., "if model is unchanged, expected PBO = X")
   - Then state the predicted range with EXPLICIT mechanism (e.g., "with outer-seed retraining, expected std in [0.05, 0.20] from inner-ensemble RNG variation")
   - Reconcile against the design scope (e.g., "if scope is consumer-only, std bound is √(p(1-p)/5000) ≈ 0.005")
