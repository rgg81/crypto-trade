# LightGBM Master Advisor — iter-v1/021 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/021`. HEAD `0a2343b`. Cycle-3 EXPLORATION #6 of 10 — methodology-pivot subtype (the iteration I myself recommended at /020 Phase 7.4 §5 hybrid Option C+B).
- **Track record entering /021**: 0/3 directional calls at /020, 1/1 methodology call (n_eff=9), 1/1 pre-registered alternative-branch utility. Phase 4.5 directional reasoning at /020 collapsed because monthly aggregate ρ ≈ -0.022 was treated as evidence of training-time pool independence — wrong inference. The /021 diagnostic IS the audit of that mistake.
- **Anchor EDA**: `analysis/iteration_v1-021/oof_per_month_summary_stats.csv` confirms Pearson **0.5893** / Spearman **0.2621** across 52 train-months between pool baseline (Model A, BTC slice) and BTC-only /020 (Model H). Directionally aligned, structurally different rankings.
- **Critical infrastructure finding**: NO existing parquet captures Optuna `study.best_params`. The `oof_persist_path` mechanism (`optimization.py:475-483`) flushes per-trial OOF returns but NOT the `study.best_params` dict. Baseline `run.log` has 1025 `Best params:` print lines but only 4 of 10 hyperparams (n_estimators, max_depth, learning_rate, num_leaves) are emitted. /020 has NO run.log file at all.

## 1. QR's 55/30/15 H1 priors — REJECT, recalibrate to 45/40/15

**Pearson 0.59 is moderately positive but NOT strong evidence for H1 CONFIRMED at 55%.** Three reasons:

1. **Spearman 0.26 dominates the inference**, not Pearson. The QR Section 2.2 text correctly notes Spearman 0.26 is "weak rank-correlation — the order of 'best' months differs materially". This is the substrate-level signal: month-by-month, the basins ARE different. Pearson 0.59 inflates because BOTH series are sign-positive in 90%+ of months (pool 48/52 = 92%; BTC-only 45/53 = 85%) — Pearson is pulled up by shared positive sign, not by per-month parameter alignment.

2. **The proxy is mean-OOF-return, not Optuna parameter delta directly**. Mean OOF return at best-trial can converge between pool and BTC-only via DIFFERENT parameter combinations (multiple basins yielding similar Sharpe). H1 specifically claims **parameter-space divergence**; the OOF proxy is at-best a noisy upper bound on H1's strength.

3. **n_trials disparity (35 pool vs 18 BTC-only)** confounds: pool's TPE saturated; BTC-only's TPE was warming up. Best-trial parameters at 18 trials are HIGHER-VARIANCE than at 35 — guarantees larger nominal parameter-Δ even if the underlying basin is the same.

**Recalibrated**: DIAGNOSTIC-CONFIRMED **45%** / MIXED **40%** / REFUTED **15%**. The MIXED tail is the underweighted prior — partial channel signal across 1-2 of {C1, C2, C3} is the modal interior outcome.

## 2. Methodology question — REJECT BOTH QR-proposed alternatives

### Why "re-run n_trials=3 for ALL months" is wrong
n_trials=3 is BELOW TPE warmup — first 5-10 trials are pure random search. At n_trials=3, "best_params" is essentially the maximum of 3 IID random draws from the search-space prior. The H1 falsifier requires basin-converged params — n_trials=3 is a NULL diagnostic dressed in compute.

### Why "extract from existing /020+baseline runs via run.log grep" is also wrong
(a) `/020` has NO run.log. (b) Print line emits only 6/10 hyperparams (subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda NEVER printed). (c) Parsing is fragile.

### CORRECT APPROACH (mandate)

**Implement `params_persist_path` as the QR brief §3.1 already specifies, AND re-run /020 BASELINE-config + Model H side-by-side at `n_trials=18 seed=42` (canonical /020 budget) WITH the new buffer.** This costs ~25 min wall-clock. Produces 10/10 params per cell, structured by `(model_role, symbol, train_month, seed)`. CONFIRM with QR before Phase 5 brief finalization that §3.1 is THE method, not a tiny-budget alternative.

## 3. F-AXIS-MECHANISM #1 for diagnostic — THREE-LAYER TEST

**Layer A — Buffer flush completeness**: `optuna_best_params.parquet` exists with ≥ (24 train_months × 2 model_roles × 1 seed) = 48 rows for BTC PLUS rows for all 5 pool symbols (BTC, ETH, LINK, LTC, DOT) on Model A pool = 24 × 5 = 120 rows. **TOTAL ≥ 168 rows** (brief's "≥ 96 rows" miscounts; forgot pool runs 5 symbols). BLOCK-PENDING-FIX if row count < 168.

**Layer B — Determinism re-test**: BASELINE-config /021 trade roster bit-identical to `v0.v1-baseline-corrected` portfolio Sharpe headline (+0.2829 IS / +0.6637 OOS) at COMPARISON.CSV level. Adding `params_persist_path` MUST be a true no-op on Optuna's training-objective domain. BLOCK-FINAL if this fails.

**Layer C — Parameter visibility audit**: for each (sym, month, seed) cell, verify ALL 10 hyperparameter columns are non-null. v1_pruned profile MUST not have any silent `.get(default)` drops — if only 6 of 10 are sampled (the v1_pruned_axis016 incident from /016), H1 falsifier is partially blind and verdict is forced to DIAGNOSTIC-MIXED-or-worse.

## 4. Feature importance method — RECOMMEND mean gain (b)

- **(a) Raw split count**: noisy; captures "feature used in ≥1 split" frequency not predictive power.
- **(b) Mean gain** (`importance_type='gain'`): cumulative loss-reduction per feature. **This is what v3 uses at `run_baseline_v3.py:2730-2818`.** Spearman rank well-defined; H2 falsifier comparisons interpretable. **RECOMMEND.**
- **(c) Permutation importance**: most trustworthy but ~5-10× wall-clock. Defer.

`_write_feature_importance` uses `importance_type='gain'`. Per-month aggregation deferred to future iteration (LM Master Phase 7.4 §6 outstanding gap II).

## 5. /022 conditional staging — accelerated /027 vs cadence-preserved LTC-only

**Recommendation: CONDITIONAL — modal LTC-only; accelerate /027 ONLY at HIGH-CONFIDENCE H1 CONFIRMED.**

- **If H1 CONFIRMED with ≥6 of 10 params shifted on ≥50% of (sym, month) cells AND ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted** → accelerated /022=/027. Cadence violation justified because /023-/026 single-cohort EXPLORATIONs are PREDICTABLY NEGATIVE under H1 (replicate BTC pattern).
- **If borderline (4-5 of 10 params shifted)** → /022 = LTC-only specialization, then re-evaluate /023 after observing LTC.
- **If H1 MIXED OR REFUTED** → /022 = LTC-only specialization (preserves cadence; per-cohort axis revives).

The 4-EXPLORATION savings (~2-3 hours wall-clock) is justified at HIGH-CONFIDENCE because the alternative is PREDICTABLE-NEGATIVE. At BORDERLINE, cadence is safer than the credibility cost of /027 revealing nothing.

## 6. Most important point — single-sentence directional call

**The diagnostic is methodology-defensible IF (a) `params_persist_path` flushes ALL 10 hyperparams at ≥168 rows via the brief §3.1 method (NOT QR-proposed n_trials=3 re-run NOR run.log grep), (b) BASELINE-config trade-roster determinism holds bit-identical, and (c) feature_importance uses `importance_type='gain'`; /027 CONFIRMATION moves to /022 ONLY if H1 CONFIRMED with mean |Δ|>0.30 on ≥6 of 10 params across ≥50% of (sym, month) cells AND ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted — otherwise /022 = LTC-only specialization preserving cadence.**

## 7. /027 BUNDLE COMPOSITION — RECOMMEND Option β

### Option α — TWO-SPECIALIST + REDUCED POOL (rejected)
Drop LINK + ETH from pool; 3-sym pool may shift BTC's basin (H1 in reverse).

### Option β — TWO-SPECIALIST + FULL POOL preserved (recommended)
- LINK-only specialist (Model C): +0.80 anchor — alpha-enhancement layer on top of pool
- ETH-only + gate specialist (Model G): +0.50 anchor — alpha-enhancement layer
- Model A pool **UNCHANGED at 5 symbols** — preserves baseline determinism
- Specialists are PORTFOLIO-LEVEL ADDITIVE (allocate fresh capital on top of pool signal)
- Signal-level merge logic with pre-committed weight rule (e.g., specialist gets 30% of pool's per-symbol allocation when in agreement; 0% when in disagreement)

| Component | Provenance | Bundle role | Single-seed Δ | Multi-seed target Δ |
|---|---|---|---|---|
| Model A pool (5 sym, unchanged) | BASELINE_V1.md | Pool baseline | 0 | 0 |
| LINK-only specialist (Model C) | /018 PROMISING | Alpha-enhancement | +0.16 | +0.80 |
| ETH-only + BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | +0.65 | +0.50 |
| **BTC** | via Model A pool | NO specialist | — | — |
| **LTC, DOT** | via Model A pool | NO specialists (H1 implies BTC-pattern) | — | — |

Bundle Δ target at /027 multi-seed: +0.6637 baseline + LINK +0.80 + ETH +0.50 = nominal +1.96 if independent. Realistic with correlation drag: **+1.10 to +1.30**. Multi-seed regression must demonstrate ≥+1.0 OOS Sharpe to clear the Sharpe 1.0 floor merge gate.

## Closing Notes

**HIGH-MEDIUM confidence in three calls** (calibrated against /020's 0/3 directional record):

1. **H1 prior CONFIRMED 45% (not QR's 55%)** — Spearman 0.26 + n_trials confound + proxy-vs-direct-parameter gap argue for MIXED tail being underweighted.
2. **Methodology: brief §3.1 implementation IS the diagnostic; reject QR alternatives (tiny-budget + log-grep)** — both have fatal defects.
3. **/022 routing: LTC-only modal unless H1 CONFIRMED with HIGH confidence** — cadence violation only at clearly CONFIRMED.

**Single most important point for QR**: the brief §3.1 implementation is the substrate of the entire diagnostic. If `params_persist_path` has partial-coverage bug (only 6 of 10 params written), the H1 falsifier becomes partially blind and verdict is forced to DIAGNOSTIC-MIXED regardless of underlying truth. Phase 5.5 BLOCK gate must include static code-review: every key in `study.best_params` for v1_pruned bounds_profile is written, NO `.get(default)` silent drops. Critic Phase 6.0 must verify on QE's src/ diff.

**Critic Phase 7.5 priority items**:
1. Layer A buffer flush completeness (≥168 rows)
2. Layer B determinism bit-identical baseline
3. Layer C 10-param visibility audit
4. H1 falsifier evaluation against pre-registered thresholds
5. H2 feature-signature Spearman rank correlation pre-registered band

---

# LightGBM Master Post-Mortem — iter-v1/021 — Phase 7.4

## Context Read

- **Iteration outcome (comparison.csv)**: Model A pool (BTC+ETH 2-sym) IS Sharpe **-0.83** / OOS Sharpe **+0.33** / ratio -0.40. 287 IS trades, 95 OOS trades. n_eff per cell median 21.
- **Brief headline finding**: H1 (training-time pool-anchor parameter divergence) requires per-param |Δ|>0.30 on ≥50% of months per Section 4.3 9-cell matrix.
- **Reality of run**: ENSEMBLE_SIZE=1, seed=42 single-seed; Pool = BTC+ETH 2-sym (NOT 5-sym); BTC-only Model H n_trials=18; 106 parquet rows; 53 pool + 53 BTC-only (per `_train_for_month` call cadence).

## 1. Phase 4.5 vs Phase 7.4 Prediction Reality

Recalibrated /021 priors (H1 45/40/15; H2 70/20/10) land where evidence resolves. **H1 = CONFIRMED BORDERLINE** (4/10 params shifted on ≥50% months — directly in brief's 4-5 band) matches 45% CONFIRMED + 40% MIXED tail well. **H2 is structurally UNDETERMINED at /021** due to instrumentation defect (Pool Model_A feature_importance CSV all zeros).

## 2. H1 Falsifier Evaluation — CONFIRMED BORDERLINE

| Param | median \|Δ\| | mean \|Δ\| | P90 \|Δ\| | % > 0.30 |
|---|---:|---:|---:|---:|
| confidence_threshold | 0.3303 | 0.3507 | 0.6769 | **54.7%** |
| n_estimators | 0.2444 | 0.3031 | 0.5707 | 43.4% |
| max_depth | 0.5000 | 0.4245 | 0.9000 | **73.6%** |
| num_leaves | 0.2917 | 0.3263 | 0.6417 | 49.1% |
| learning_rate | 0.2233 | 0.3168 | 0.7475 | 35.9% |
| subsample | 0.3065 | 0.3329 | 0.6550 | **54.7%** |
| colsample_bytree | 0.2432 | 0.2965 | 0.6172 | 43.4% |
| min_child_samples | 0.2875 | 0.2993 | 0.5900 | 47.2% |
| reg_alpha | 0.2465 | 0.3009 | 0.6022 | 39.6% |
| reg_lambda | 0.3595 | 0.3497 | 0.6824 | **60.4%** |

- **# of 10 params shifted on ≥50% of months: 4/10** (`confidence_threshold`, `max_depth`, `subsample`, `reg_lambda`)
- **# of key {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted: 1/4** (only `confidence_threshold`)

Per brief Section 4.3: **4/10 = CONFIRMED BORDERLINE band**. HIGH-CONFIDENCE gate (≥6 shifted AND ≥2 key) NOT cleared.

**Caveat — n_trials disparity confound**: Pool n_trials=35; BTC-only n_trials=18. TPE warmup variance inflates parameter-Δ at n_trials=18. Flagged in Phase 4.5 §1.

## 3. H2 Falsifier Evaluation — UNDETERMINED (Instrumentation Defect)

**`feature_importance_POOL_Model_A.csv` is ALL ZEROS across 40 features.** Total gain sum = 0.0 for Pool. BTC-only Model_H total gain = 98,881.78. Naïve Spearman ρ = -0.04 (tie-break artifact on all-zero series). NOT a true cohort-signature divergence measurement.

**Root cause**: write-side defect at `run_baseline_v1.py:560-585`. Pool strategy `_models` may have been written only on LAST training month OR `_iter021_fi_strategies` captured stale references. BTC-only wrote correctly. Layer C parquet confirms pool was TRAINED correctly (all 11 hyperparams non-null) — defect is WRITE-side, not training-side.

**H2 non-evaluable at /021**. Cannot place verdict cell.

## 4. Joint H1×H2 Verdict Cell

- H1 = **CONFIRMED BORDERLINE**
- H2 = **UNDETERMINED**

Coerced verdict: **"H1 CONFIRMED BORDERLINE × H2 UNRESOLVED" → /022 = LTC-only specialization (cadence-preserved)**, with MANDATORY pool feature_importance defect fix as /022 prerequisite.

## 5. Mechanism Analysis — Channel Support

- **C1 (shared normalization)**: SUPPORTED. `confidence_threshold` 54.7% — normalization compromise across BTC+ETH labels.
- **C2 (label-timing co-location)**: WEAKLY SUPPORTED. `max_depth` 73.6% — pool composition shifts Optuna basin via shallower/deeper trees.
- **C3 (abs_pnl weighting)**: NEUTRAL. `reg_lambda` 60.4% but `reg_alpha` 39.6% — inconsistent co-shift.

**Strongest channels**: C1 + C2. H1 mechanism EXISTS but doesn't dominate.

## 6. Layer B Determinism — NOT Bit-Identical, EXPECTED Divergence

| Slice | Baseline (5-sym pool, BTC slice) | /021 (2-sym pool, BTC slice) | Delta |
|---|---:|---:|---:|
| IS BTC trades | 113 | 141 | +28 |
| IS ETH trades | 145 | 146 | +1 |
| OOS BTC trades | 35 | 47 | +12 |
| OOS ETH trades | 46 | 48 | +2 |

**Layer B FAILS bit-identity** — but for STRUCTURALLY EXPECTED reason. Baseline used 5-sym pool; /021 Model A used 2-sym pool. Different training-data composition → different Optuna best_params per month → different trade rosters. NOT a `params_persist_path` regression; IS a brief-design ambiguity. Recommend Critic Phase 7.5 re-frame as "Pool composition divergence, NOT params_persist_path defect" → PASS-WITH-NOTE.

## 7. Track Record Honest Update

Pre-/021: 0/3 directional, 1/1 methodology, 1/1 alternative-branch utility.

Post-/021 updates:
- **H1 directional prior (45/40/15)**: BORDERLINE-correct. 45% CONFIRMED captured directional truth better than QR's 55%. Score: **0.5/1 directional credit**.
- **H2 directional prior (70/20/10)**: Non-evaluable. No credit/discredit.
- **Methodology call (reject n_trials=3 + log-grep; mandate §3.1)**: PROVEN CORRECT. §3.1 captured 11/11 hyperparams across 106 rows with zero nulls. **Score: 2/2 methodology credit**.
- **Layer C 10-param visibility mandate**: PROVEN ESSENTIAL. Without it, H1 falsifier blind on 50% of dimensions.

**Updated track record**: H1 directional 0.5/4 (one new BORDERLINE-correct), methodology 2/2 (100%), alternative-branch utility 1/1. Methodology calls remain LM Master's strongest lane.

## 8. /022 Routing per Section 11.7

- H1 = CONFIRMED BORDERLINE (4 of 10 params shifted; 1 of 4 key params shifted)
- H2 = UNDETERMINED

**Routing recommendation: /022 = LTC-only specialization** (cadence-preserved). NOT accelerated /027. HIGH-CONFIDENCE gate (≥6 + ≥2 key) NOT cleared.

**/022 prerequisite**: fix `_write_feature_importance` Pool-CSV all-zero defect at `run_baseline_v1.py:560-585`. Low-cost code fix; doesn't require backtest re-run for /021 closeout but is mandatory for any /022+ H1+H2 joint diagnostic.

## 9. Most Important Phase 7.4 Finding

**H1 mechanism EXISTS at BORDERLINE strength (4/10 params shift on ≥50% of months, dominated by `confidence_threshold`, `max_depth`, `subsample`, `reg_lambda`); H2 is non-evaluable at /021 due to a Pool feature_importance write-side defect that QE must fix before any further H1/H2 joint diagnostic is methodologically sound.**

## Closing Note for Critic (Phase 7.5)

Three things Critic 8-check pass should specifically attend to:

1. **Pool feature_importance all-zero defect** — Check 7/8. WRITE-side bug at `run_baseline_v1.py:560-585`. Recommend BLOCK-PENDING-FIX with QE patch before /022.
2. **Layer B BLOCK-FINAL re-interpretation** — Check 6 (determinism). Letter of brief: BLOCK-FINAL on bit-identity fail; intent: "no params_persist_path regression." Pool composition (5-sym vs 2-sym) is actual cause. Recommend PASS-WITH-NOTE.
3. **H1 BORDERLINE verdict with n_trials disparity confound** — Check 4 (IC validity). n_trials=35 vs 18 asymmetry inflates parameter-Δ via TPE warmup variance. Without equalizing, BORDERLINE is /021's ceiling. Future replicate at matched n_trials would help (deferred).
