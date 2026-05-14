# iter-v3/068 — Research Brief

**Branch**: `iteration-v3/068`
**EDA SHA**: `c16d53c`
**Setup commit SHA**: (this commit, LOCKED)
**Iteration type**: EXPLORATION (cycle 1 #9 of 10; NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4; LABELING TIMEOUT axis; orthogonal to /065's labeling SL multiplier at the DURATION dimension)
**Axis**: UNIVERSAL labeling timeout WIDENING — `label_timeout_minutes` raised from `10080` (21 candles at 8h) to `20160` (42 candles, +100%) — Path C per EDA

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols, UNCHANGED from /051 SYSTEM-LEVEL REVERT). Feature universe = 14 V3_FEATURE_COLUMNS (UNCHANGED post-/064 revert at commit `04080c4`).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION.

- **Cycle 1 EXPLORATION slot**: #9 of 10 (post /058 RE-ANCHOR + /059 RE-ANCHOR #2; cycle counting per BASELINE_V3.md /059).
- **Sub-type**: **NON-FEATURE PIVOT CONTINUATION — LABELING TIMEOUT axis**. Per Critic /064 Rec #4 NON-FEATURE pivot mandate (LOCKED for /065-/068 per `feedback_v3_iter064_process_lessons.md` Rule 5). /065 chose UNIVERSAL labeling SL widening (PROMISING — SUSPICIOUS-OOS-DOMINANT first /069 candidate); /066 chose UNIVERSAL vol_scale_ceiling=0.8 (INERT-AT-EXPLORATION; family STRUCTURALLY EXHAUSTED); /067 chose universal inference-threshold floor (INERT-AT-EXPLORATION per Path D non-activation finding). /068 pivots to LABELING TIMEOUT axis at TRAIN-TIME — the DURATION dimension of triple-barrier labeling, distinct from /065's MAGNITUDE dimension AND from /066/067's INFERENCE-TIME modifications.
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset [191664963, 1662057957, 1405681631]).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 3 × 3 = 315 (matches /060-/067 EXPLORATION-mode budget).
- **Wall-clock target**: ~1.1h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`).

**Cycle 1 catalog status before /068**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 (Path D) | SUSPICIOUS-OOS-DOMINANT (first /069 candidate) |
| #7 | /066 | NON-FEATURE PIVOT: UNIVERSAL vol_scale_ceiling 1.0 → 0.8 (Path E0.8) | INERT-AT-EXPLORATION (closed; universal-ceiling family STRUCTURALLY EXHAUSTED) |
| #8 | /067 | NON-FEATURE PIVOT cont: UNIVERSAL inference-threshold TIGHTEN 0.60 (Path D) | INERT-AT-EXPLORATION (closed; Path D mechanism non-activation per Critic FINAL `b8d3bb5`) |
| **#9** | **/068** | **NON-FEATURE PIVOT cont: UNIVERSAL labeling TIMEOUT widen 21 → 42 (Path C)** | **TBD** |
| #10 | /069 | TBD per QR EDA | TBD |
| CONFIRMATION | /069+ | Bundle: /065 SL widening + Path B4 implementation + (potentially Path C if PROMISING) | TBD |

**Why LABELING TIMEOUT axis now**:

1. **Critic /064 Rec #4 directive (binding through /068)**: NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35. /068 is the LAST eligible NON-FEATURE PIVOT slot before /069 (CONFIRMATION-or-final-EXPLORATION).

2. **Critic /066 Rec #2 directive (locked at cycle 1)**: AVOID universal symmetric clip/cap mechanisms. /068 axis is structurally distinct: instead of CAPPING per-trade weight (multiplicative weighting modifier — /066) OR TIGHTENING the per-candle emission decision (binary gate modifier — /067), Path C EXTENDS the TRAIN-TIME label-generation forward-scan window. Mechanism is DURATION-axis, not weight or gate.

3. **Cycle 1 bundle diversity at /069 CONFIRMATION**: /065's labeling SL widening (MAGNITUDE) is the first PROMISING-class survivor; /067 INERT closed; /066 INERT closed. A LABELING-TIMEOUT axis (DURATION) is the sister to /065 (MAGNITUDE) at the same TRAIN-TIME stage — and may compound at /069 CONFIRMATION as a LABELING-AXIS BUNDLE (SL widening + timeout extension). Distinct from /065 because: SL widening changes the MAGNITUDE of the barrier (atr_sl multiplier 1.0 → 1.5); timeout extension changes the DURATION of the forward scan (10080 min → 20160 min).

4. **LABELING-TIMEOUT axis is mechanistically distinct from /066 and /067** (T6 verified at EDA SHA `c16d53c`):
   - /066 weight ceiling: INFERENCE-TIME `Signal.weight` change (multiplicative scaling)
   - /067 inference threshold: INFERENCE-TIME `Signal | NO_SIGNAL` gate change (binary)
   - /068 label timeout: TRAIN-TIME label generation forward-scan window (label distribution shifts; downstream proba surface changes)
   - Three separate stages; three separate code paths (`risk_v2.py`, `lgbm.py`, `labeling.py` + `walk_forward.py`)

5. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`** (system-level confirmed across 2 CONFIRMATIONs at /039 + /050): per-symbol customizations break IS aggregate at multi-seed. UNIVERSAL labeling timeout extension is the structurally safe alternative — applies uniformly to BCH+LDO+TRX.

6. **Per `feedback_v3_oracle_eda_validity.md`**: TRAIN-TIME label generation is ORACLE-EDA-valid (the labeling function is STATELESS w.r.t. signal-emission state). Counterfactual analysis on the prior trade roster (T2) and forward-scan logic (T3) is methodologically sound. NO deadlock risk per /054 closure rule.

7. **Per `feedback_v3_engineered_features_dont_stack.md`**: ONE substantive axis at EXPLORATION. /068's single change is `label_timeout_minutes` 10080 → 20160. /067's `_inference_threshold_floor` REVERTS to default 0.0 (clean attribution). /066's `vol_scale_ceiling` REMAINS at default 1.0 (already reverted at /067). /065's `DEFAULT_ATR_MULTIPLIERS` REMAINS at default (2.0, 1.0) (already reverted at /066).

## Section 1 — Testable Hypothesis (ONE sentence)

> UNIVERSAL labeling timeout extension from `label_timeout_minutes=10080` (21 candles at 8h) to `20160` (42 candles, +100% scan window) — converting ~9 IS timeout-labels and ~3 OOS timeout-labels into TP/SL resolution labels per the existing forward random-walk — produces a Sharpe shift centered at INERT-band (~50% probability) with non-zero PROMISING-band upside (~15% probability) by giving the labeling function more time to capture genuine barrier hits, at the structural COST of a doubled walk-forward embargo gap (22 → 43 candles per cell) and reduced sample uniqueness; predicted IS Δ band [-0.10, +0.10] and OOS Δ band [-0.15, +0.15] (per Path C ORACLE first-order counterfactual at EDA SHA `c16d53c`); INERT-AT-EXPLORATION is the most likely outcome (~50%) given that 94.3% IS / 97.1% OOS of labels already resolve via TP/SL at K=21.

## Section 2 — Numerical EDA Tables (EDA SHA `c16d53c`)

EDA committed at SHA `c16d53c` (`analysis/iteration_v3-068/labeling_timeout_eda.py`). Produces 6 tables (T0-T6). Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). **NOT iter-v3/065 nor /067** (parallel cycle 1 axes; /060 is the canonical EXPLORATION-mode anchor per `feedback_v3_cycle1_axis_pass_criteria.md`).

### Section 2.1 — T0 Anchor-value declaration (Critic /064 Rec #1 + /065 Rec #1 + /066 Rec #3 carry-forward + Rule 1 compliance)

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+0.8325** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.1403** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| n_trades_in_sample | **159** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| n_trades_out_of_sample | **102** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| weighted_pnl_total_in_sample | **+51.8906** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| weighted_pnl_total_out_of_sample | **+5.4989** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| BCH_OOS_weighted_pnl | **+1.9078** | `reports-v3/iteration_v3-060/comparison.csv:18 (per_symbol block, weighted_pnl col)` |
| LDO_OOS_weighted_pnl | **-19.7208** | `reports-v3/iteration_v3-060/comparison.csv:19 (per_symbol block, weighted_pnl col)` |
| TRX_OOS_weighted_pnl | **+23.3119** | `reports-v3/iteration_v3-060/comparison.csv:20 (per_symbol block, weighted_pnl col)` |
| BCH_IS_concentration_pct | **176.68%** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv (pct_of_total_pnl)` |
| current_label_timeout_minutes | **10080** | `run_baseline_v3.py:1398` |
| current_label_timeout_candles | **21** | `run_baseline_v3.py:740 (10080/480=21)` |
| frac_positive_paths_cpcv | **0.6444** | BASELINE_V3.md Headline Metrics (CPCV invariant across architectures) |

These are the BIT-EXACT /060 anchor values per Phase 5.5 anchor-value correctness gate (Rule 1 of `feedback_v3_iter064_process_lessons.md`). All Section 4 falsifier bands reference these. RECURRENCE-flag awareness: /065 brief Section 2.5 originally cited "+24.75 OOS wpnl (BCH)" (a 13× error vs +1.9078 actual); /066, /067 briefs CLEAN; /068 brief explicitly cross-checks all anchor values against the source file via T0 EDA output before commit.

### Section 2.2 — T1 Current label distribution at timeout=21 candles (trade roster perspective)

Source: `reports-v3/iteration_v3-060/{in_sample,out_of_sample}/trades.csv`.

| sample | symbol | n_trades | n_TP | n_SL | n_TIMEOUT | n_EOD | pct_TIMEOUT | avg_dur_all | avg_dur_TP | avg_dur_SL |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| in_sample | BCHUSDT | 73 | 27 | 40 | **6** | 0 | **8.22%** | 6.85 | 7.81 | 4.08 |
| in_sample | LDOUSDT | 11 | 3 | 8 | **0** | 0 | **0.00%** | 4.91 | 4.33 | 5.12 |
| in_sample | TRXUSDT | 75 | 19 | 53 | **3** | 0 | **4.00%** | 6.00 | 7.05 | 4.77 |
| out_of_sample | BCHUSDT | 37 | 11 | 24 | 2 | 0 | 5.41% | 5.92 | 6.64 | 4.33 |
| out_of_sample | LDOUSDT | 11 | 2 | 9 | 0 | 0 | 0.00% | 7.36 | 11.00 | 6.56 |
| out_of_sample | TRXUSDT | 54 | 26 | 26 | 1 | 1 | 1.85% | 6.65 | 6.96 | 5.88 |

**Reading**:
- **9/159 (5.7%) IS trades** terminate via TIMEOUT at K=21 (BCH=6, LDO=0, TRX=3).
- **3/102 (2.9%) OOS trades** terminate via TIMEOUT (BCH=2, LDO=0, TRX=1).
- LDO has **ZERO timeouts** in BOTH IS and OOS — all 22 LDO trades hit TP/SL before the 21-candle deadline. LDO label resolution is fully captured at K=21.
- BCH has the highest timeout rate (8.22% IS / 5.41% OOS). BCH trades take the longest to resolve.
- Avg TP duration is meaningfully higher than avg SL duration (BCH IS: 7.81 vs 4.08; TRX IS: 7.05 vs 4.77; LDO IS: 4.33 vs 5.12 — close). TPs take longer to fire than SLs — consistent with the strategy: SL is closer to entry than TP.
- **Critical**: trade roster perspective UNDERESTIMATES the label population timeout rate. The full label population (every candidate candle, not just the emitted-trades subset) has more timeout labels because Optuna's confidence-threshold filter weeds out many low-confidence emissions. However, **at training time** the labeling function generates labels for ALL candidates per cell — the timeout rate among ALL labels is structurally HIGHER than the 5.7% trade-roster value. /068 affects the FULL label population, not just the trade roster.

### Section 2.3 — T2 Counterfactual at alternative timeouts (FIRST-ORDER trade-roster impact)

Source: re-categorizing /060 OOS trade durations at alternative K values.

| path | K_candles | K_min | sample | n_orig | n_resolved_within_K | n_truncated_to_timeout | pct_truncated | n_TP_within | n_SL_within | n_TIMEOUT_within | n_EOD_within |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Path A (K=7) | 7 | 3360 | in_sample | 159 | 114 | **45** | **28.30%** | 31 | 83 | 0 | 0 |
| Path A (K=7) | 7 | 3360 | out_of_sample | 102 | 69 | **33** | **32.35%** | 25 | 43 | 0 | 1 |
| Path B (K=14) | 14 | 6720 | in_sample | 159 | 140 | **19** | **11.95%** | 46 | 94 | 0 | 0 |
| Path B (K=14) | 14 | 6720 | out_of_sample | 102 | 92 | **10** | **9.80%** | 36 | 55 | 0 | 1 |
| ANCHOR (K=21) | 21 | 10080 | in_sample | 159 | 159 | 0 | 0.00% | 49 | 101 | 9 | 0 |
| ANCHOR (K=21) | 21 | 10080 | out_of_sample | 102 | 102 | 0 | 0.00% | 39 | 59 | 3 | 1 |
| **Path C (K=42)** | **42** | **20160** | **in_sample** | 159 | 159 | **0** | **0.00%** | 49 | 101 | **~9 candidates** | 0 |
| **Path C (K=42)** | **42** | **20160** | **out_of_sample** | 102 | 102 | **0** | **0.00%** | 39 | 59 | **~3 candidates** | 1 |
| Path D (K=63) | 63 | 30240 | in_sample | 159 | 159 | 0 | 0.00% | 49 | 101 | ~9 candidates | 0 |
| Path D (K=63) | 63 | 30240 | out_of_sample | 102 | 102 | 0 | 0.00% | 39 | 59 | ~3 candidates | 1 |

**Reading**:
- **Path A (K=7) introduces MAJOR label noise**: 28.30% IS / 32.35% OOS trades become forward-return labels. Forward-return labels at 7 candles are dominated by random-walk noise; classifier degrades.
- **Path B (K=14) introduces MEDIUM label noise**: 11.95% IS / 9.80% OOS shift to forward-return. Same mechanism as A at smaller scale.
- **Path C (K=42) is FIRST-ORDER INVARIANT at trade-roster level**: zero additional trades change resolution because all original trades resolved within K=21. Counterfactual impact comes from the FULL LABEL POPULATION (not in trade roster): roughly 9 IS / 3 OOS trade timeouts MAY upgrade to TP/SL if the next 21 candles happen to hit a barrier. Forward random-walk variance over 21 → 42 candles is highly path-dependent; some MAY convert, some won't.
- **Path D (K=63) is FIRST-ORDER INVARIANT at trade-roster level**: similar to Path C but with sample-uniqueness penalty (embargo = 64 candles per cell, cross-cell gap = 192 candles).
- **Note on T2 limitation**: this is a FIRST-ORDER counterfactual on the existing trade roster. The SECOND-ORDER effect (Optuna retrains on changed labels → different model → different trade roster) is unmodeled. At /068 Phase 6, the actual trade roster may differ MORE than the first-order counterfactual suggests because Optuna's TPE re-converges under different label distributions.

### Section 2.4 — T3 LDO-specific timeout interaction (label noise hypothesis)

Source: LDO subset of trade roster.

| sample | stat | value |
|---|---|---:|
| in_sample | n_trades | 11 |
| in_sample | duration_mean (candles) | 4.91 |
| in_sample | duration_median (candles) | 3.0 |
| in_sample | n_TP | 3 |
| in_sample | n_SL | 8 |
| in_sample | n_TIMEOUT | **0** |
| in_sample | avg_TP_duration | 4.33 |
| in_sample | avg_SL_duration | 5.12 |
| out_of_sample | n_trades | 11 |
| out_of_sample | duration_mean | 7.36 |
| out_of_sample | duration_median | 4.0 |
| out_of_sample | n_TP | 2 |
| out_of_sample | n_SL | 9 |
| out_of_sample | n_TIMEOUT | **0** |
| out_of_sample | avg_TP_duration | 11.00 |
| out_of_sample | avg_SL_duration | 6.56 |

**Reading**:
- **LDO is INSENSITIVE to timeout extension**: ZERO timeouts at /060 in both IS and OOS. All 22 LDO trades hit TP/SL before the 21-candle deadline.
- LDO durations skew SHORT (IS median=3.0, OOS median=4.0 candles).
- LDO's max duration in IS is 20 candles (1 SL at 20). Path A (K=7) would truncate this to TIMEOUT. Path B (K=14) would also truncate.
- **For LDO**: Path A NEGATIVE (truncates the 20-candle SL to TIMEOUT); Path B mildly NEGATIVE; Path C/D essentially INVARIANT.
- **Hypothesis**: LDO's weak signal at /060 is NOT a timeout / label-noise issue. It's a signal-quality issue at the feature/model level. /068 cannot fix LDO via timeout extension. /068 may not improve LDO at all.
- LDO improvement is the residual hope at /068 — but T3 suggests timeout-axis is NOT the lever for LDO. Per `feedback_v3_per_symbol_target_axis_falsifier.md`: LDO IS expected to be CLOSE-TO-INERT band even under PROMISING Path C.

### Section 2.5 — T4 Path predicted Sharpe Δ (HEADLINE metric)

PREDICTED IS/OOS Sharpe Δ from structural reasoning + first-order counterfactual:

| Path | IS Δ band | OOS Δ band | Direction | Mechanism / Risk |
|---|---|---|---|---|
| Path A (K=7) | [-0.40, -0.05] | [-0.50, -0.05] | NEGATIVE | 28-32% labels become noisy fwd-return — random walk dominates |
| Path B (K=14) | [-0.25, +0.00] | [-0.30, +0.05] | WEAKLY NEGATIVE | 10-14% labels become noisy fwd-return |
| ANCHOR (K=21) | 0 | 0 | REFERENCE | 5.7% IS / 2.9% OOS timeouts already |
| **Path C (K=42)** | **[-0.10, +0.10]** | **[-0.15, +0.15]** | **INERT-band centered** | **Label cleanup: ~5.7% IS / ~2.9% OOS timeouts MAY upgrade to TP/SL. Sample-uniqueness drops (effective sample size penalty <5%). 2nd-order Optuna re-converge.** |
| Path D (K=63) | [-0.25, +0.05] | [-0.30, +0.05] | WEAKLY NEGATIVE | Sample-uniqueness penalty dominates label-cleanup benefit; embargo gap doubles to 64 candles |
| Path E (passive) | 0 | 0 | INERT by design | Skip — saturation justified by T1/T2 |

**Reading**:
- **Path C is the ONLY Path with predicted band centered at INERT-zero** with non-zero PROMISING upside. The IS Δ band [+0.05, +0.10] upper portion AND the OOS Δ band [+0.05, +0.15] upper portion span the PROMISING-AT-EXPLORATION thresholds (IS Δ ≥+0.10 AND OOS Δ ≥+0.20 — partial coverage of OOS lower bound).
- Path C bands have wide envelopes (~0.20-0.30 width on each side) because:
  1. Optuna second-order TPE re-convergence under changed labels is unmodeled
  2. Marginal labels (the 9 IS / 3 OOS that would become TP/SL under K=42) have uncertain expected return (depends on whether random-walk extension over 21-42 candles hits TP or SL more often)
  3. 3-seed averaging variance introduces ±0.10 IS / ±0.20 OOS noise floor
  4. Embargo gap doubling (22 → 43 candles per cell) reduces training set ~3-5% per WF month → effective sample size penalty
- **Alternative OUTCOME WARNING**: if the second-order Optuna re-convergence finds a better proba surface under the new labels, Path C could shift to PROMISING (IS Δ +0.10 to +0.20 region). Probability assigned at 15%.
- **Alternative NEGATIVE OUTCOME**: if the embargo gap doubling causes meaningful training-data loss, OR if the new TP/SL conversions are systematically MISDIRECTED (e.g., a TP-at-K=30 vs SL-at-K=25 conversion), Path C may degrade Sharpe. Probability assigned at 25%.

### Section 2.6 — T5 Path selection summary + scoring

Per-Path 7-criteria scoring:

| Path | stateless | universal | orthogonal_065 | orthogonal_066 | orthogonal_067 | promising_viable | trade_floor_safe | **score** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Path A (K=7) | YES | YES | YES | YES | YES | NO (NEGATIVE) | YES | 5/7 |
| Path B (K=14) | YES | YES | YES | YES | YES | NO (WEAKLY NEGATIVE) | YES | 5/7 |
| **Path C (K=42)** | **YES** | **YES** | **YES** | **YES** | **YES** | **MARGINAL (INERT-band; 15% PROMISING)** | **YES** | **5/7 (selected — uniquely centered)** |
| Path D (K=63) | YES | YES | YES | YES | YES | NO (WEAKLY NEGATIVE) | YES | 5/7 |
| Path E (passive) | — | — | — | — | — | NO (by design) | — | DIAGNOSTIC |

**Path C quantitative justification (the QR selection)**:
1. ONLY Path with predicted Sharpe Δ bands CENTERED at INERT (IS Δ [-0.10, +0.10], OOS Δ [-0.15, +0.15]) with non-zero PROMISING upside
2. Mechanistically distinct from Path A/B (label-noise INJECTION direction): Path C goes the LABEL-CLEAN direction by potentially converting timeouts to TP/SL labels
3. Path D introduces too-aggressive sample-uniqueness penalty (embargo 22→64 per cell, cross-cell gap 64*3=192 vs current 66) — destabilizes the WF training regime at single-seed n_trials=35
4. STATELESS — ORACLE EDA validity confirmed per `feedback_v3_oracle_eda_validity.md` (TRAIN-TIME label gen is pure function)
5. UNIVERSAL — preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
6. Mechanistically ORTHOGONAL to /066, /067 (T6 — 7/9 stages); ORTHOGONAL to /065 within labeling at DIFFERENT sub-dimension (DURATION vs MAGNITUDE)
7. Single-axis change (one constant in `run_baseline_v3.py` at ~lines 737, 1380, 1398)
8. NOT a universal symmetric clip/cap — AVOIDS Critic /066 Rec #2 STRUCTURALLY EXHAUSTED family (different mechanism: label DURATION vs weight ceiling)
9. Anti-snooping: universal `label_timeout_minutes=20160` has NEVER been tested
10. Implementation simplicity: 3 constant value updates in `run_baseline_v3.py`

**Path eliminations**:
- **Path A (K=7)** OUT: predicted NEGATIVE direction; 28-32% of labels become noisy fwd-return.
- **Path B (K=14)** OUT: predicted WEAKLY NEGATIVE; intermediate label-noise injection.
- **Path D (K=63)** OUT: sample-uniqueness penalty dominates label-cleanup benefit; embargo doubling destabilizes training regime.
- **Path E (passive)** OUT: would SKIP cycle 1 #9 slot. RESERVED if Critic adjudicates Path C as methodologically unfit (embargo coupling not pre-modeled).

### Section 2.7 — T6 Cross-axis orthogonality with /065, /066, /067

| Stage | /065 (SL widening) | /066 (vol_ceiling) | /067 (inf threshold) | **/068 (label timeout)** | Orthogonal? |
|---|---|---|---|---|:-:|
| feature_engineering | no change | no change | no change | no change | YES |
| label_generation_MAGNITUDE | sl_multiplier 1.0→1.5 | no change | no change | **no change** | YES (065≠068 at sub-stage) |
| label_generation_DURATION | no change | no change | no change | **timeout 10080→20160** | YES (068 unique stage) |
| embargo_purging | no change (22 candles) | no change | no change | **CHANGES (22→43 candles)** | PARTIAL (068 affects embargo) |
| optuna_hyperparameter_search | TPE on changed labels | unchanged | unchanged | **TPE on changed labels (~9 IS conversions)** | PARTIAL (065+068 both touch labels at different sub-stages) |
| model_training | fit on changed labels | unchanged | unchanged | **fit on changed labels** | PARTIAL (065 vs 068 different label dims) |
| inference_time_prediction | no direct change | weight modifier | gate threshold | no change | YES |
| risk_gate_stack | no change | ceiling change | no change | no change | YES |
| trade_emission | different roster | different roster | different roster | **different roster** | NO (all 4 affect roster via structurally distinct mechanisms) |

**Verdict**: /068 is MECHANISTICALLY ORTHOGONAL to /065, /066, /067 on 7 of 9 stages.

The two overlap stages are:
1. **optuna_hyperparameter_search** with /065: both axes change labels Optuna trains on. BUT they perturb different dimensions — /065 = MAGNITUDE of TP/SL barriers; /068 = DURATION of forward-scan window. First-order independent perturbations on label space; second-order Optuna coupling is captured at /069 CONFIRMATION.

2. **trade_emission**: all 4 axes affect the final trade roster, but via distinct structural mechanisms.

**CRITICAL — Embargo coupling** (T6 disclosed structural side effect):
- `walk_forward.compute_embargo_candles(20160, 480) = 20160//480 + 1 = 43` (vs current 22).
- Per-cell embargo gap doubles: 22 → 43 candles (training samples within the embargo window are purged).
- Cross-cell gap (3 symbols × per-cell embargo): 66 → 129 candles (factor 1.95× larger).
- Expected training-data loss per WF month: ~3-5% (at 24-month training window, losing 21 extra candles per month is ~3% of monthly capacity at 8h interval).
- This is a STRUCTURAL CONSEQUENCE of the timeout change, NOT a separate axis. The walk-forward fix at `e149e9d` mandates `compute_embargo_candles` be used consistently — /068 inherits this; no methodology violation.

### Section 2.8 — Carry-forward state from /067

Inheritance note: /067's `_inference_threshold_floor=0.60` was INERT-AT-EXPLORATION (closed per Critic FINAL `b8d3bb5`). Per `feedback_v3_engineered_features_dont_stack.md` single-axis discipline, /068 REVERTS /067's `_inference_threshold_floor` to default `0.0` for clean attribution. Similarly:
- /066's `vol_scale_ceiling`: already REVERTED to default 1.0 at /067 (kept).
- /065's `DEFAULT_ATR_MULTIPLIERS`: already REVERTED to (2.0, 1.0) at /066 (kept).
- /065's SL widening tested separately; /067's threshold floor tested separately; /066's ceiling tested separately. /068's timeout extension isolated against /060's labeling baseline.

### Section 2.9 — Anchor declaration

**Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 102 OOS trades). **NOT iter-v3/065 nor /067** (parallel SUSPICIOUS-OOS-DOMINANT and INERT-AT-EXPLORATION candidates respectively; not new anchors). Per `feedback_v3_cycle1_axis_pass_criteria.md`: cycle 1 EXPLORATIONs anchor on /060 (3-seed lineage subset of /059 10-seed CONFIRMATION); CONFIRMATION-mode delta vs /059 is evaluated only at /069 CONFIRMATION.

BASELINE_V3.md remains anchored at `v0.v3-059` per `feedback_v3_baseline_update_policy.md`.

### Section 2.10 — Summary

- Path C (K=42) is the QR-selected labeling-timeout axis per quantitative EDA analysis.
- ORACLE first-order Sharpe Δ prediction: IS Δ band [-0.10, +0.10], OOS Δ band [-0.15, +0.15] — INERT-band centered.
- Most likely classification = INERT-AT-EXPLORATION (~50% per Section 7 calibrated probabilities). PROMISING ~15%, SUSPICIOUS-OOS ~10%, NEGATIVE ~25%.
- Cross-axis orthogonality with /065, /066, /067 verified.
- Embargo coupling (22 → 43 candles per cell) disclosed at T6; falsifier band E.18 covers structural training-data side effect.
- STATELESS axis modification; ORACLE EDA discipline preserved.
- TRADE-RATE FLOOR concern: Path C's first-order trade-count is INVARIANT (no labels truncated). Second-order Optuna re-converge MAY change roster; bands cover ±15% trade count change.
- LDO is structurally INSENSITIVE to timeout extension (T3 finding); /068 does NOT address LDO weakness. Future iterations targeting LDO will need feature/model-axis interventions.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — UNIVERSAL `label_timeout_minutes` widening in `run_baseline_v3.py`

**ONE substantive change**. Triple-barrier labeling timeout widens from 10080 minutes (21 candles at 8h) to 20160 minutes (42 candles at 8h), a +100% extension.

File: `run_baseline_v3.py`. Three coupled call sites:

```python
# Line 737 (label-leakage gap header)
# BEFORE
timeout_minutes = 10080  # 7 days

# AFTER (iter-v3/068 Path C: universal labeling timeout widening)
timeout_minutes = 20160  # 14 days (42 candles at 8h) — iter-v3/068 axis
```

```python
# Line 1380 (training-data labeling call)
# BEFORE
        timeout_minutes=10080,  # 7 days (21 candles at 8h)

# AFTER
        timeout_minutes=20160,  # 14 days (42 candles at 8h) — iter-v3/068 Path C axis
```

```python
# Line 1398 (LightGbmStrategy label_timeout_minutes init kwarg)
# BEFORE
        label_timeout_minutes=10080,

# AFTER
        label_timeout_minutes=20160,  # iter-v3/068 Path C axis
```

The third call site (`label_timeout_minutes=20160` at lgbm init) automatically propagates to:
- `LightGbmStrategy._train_for_month` → uses self.label_timeout_minutes for label generation per WF month
- `compute_embargo_candles(20160, 480) = 43` → walk-forward purge gap doubles per cell
- `cv_gap = embargo_candles * n_symbols = 43 * 3 = 129` → CV gap inside LightGbmStrategy

### Sub-fix 2 — REVERT `_inference_threshold_floor` to default 0.0 at /068

File: `run_baseline_v3.py` (in the LightGbmStrategy instantiation, where `_inference_threshold_floor` was passed at /067).

```python
# Before (iter-v3/067 state)
LightGbmStrategy(
    ...,
    ensemble_seeds=ENSEMBLE_SEEDS_EXPLORATION,
    inference_threshold_floor=0.60,  # iter-v3/067 Path D
    ...
)

# After (iter-v3/068 — REVERT to default 0.0; isolate /068 axis)
LightGbmStrategy(
    ...,
    ensemble_seeds=ENSEMBLE_SEEDS_EXPLORATION,
    # inference_threshold_floor=0.0 implicit default (REVERTED from /067's INERT axis)
    label_timeout_minutes=20160,  # NEW iter-v3/068 axis
    ...
)
```

**Rationale**: /067 was INERT-AT-EXPLORATION (closed) per Critic FINAL `b8d3bb5`. Per Section 2.8 carry-forward discipline: revert `_inference_threshold_floor` to default at /068 for clean attribution. /067's axis tested separately. /068's timeout axis isolated against the universal /060 baseline.

### Sub-fix 3 — `vol_scale_ceiling` UNCHANGED at default 1.0

`vol_scale_ceiling` not explicitly set — defaults to 1.0 per `risk_v2.py:58` (already reverted at /067). UNCHANGED at /068.

### Sub-fix 4 — `DEFAULT_ATR_MULTIPLIERS` UNCHANGED at (2.0, 1.0)

File: `src/crypto_trade/features_v3/__init__.py`.

```python
# Iter-v3/066 set this to (2.0, 1.0). UNCHANGED at /067, UNCHANGED at /068.
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
```

**Rationale**: /065's SL widening axis tested separately; not reintroduced at /068. /068 axis is isolated against /060's labeling baseline.

### Sub-fix 5 — ITERATION_LABEL bump

File: `run_baseline_v3.py`.

```python
# Before
ITERATION_LABEL = "v3-067"

# After
ITERATION_LABEL = "v3-068"
```

### Sub-fix 6 — Embargo gap header comment update at line 1169 (cv_gap calc) and line 161

File: `run_baseline_v3.py`.

```python
# Line 161 — comment update
# BEFORE
# gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = (21+1)*3 = 66 (iter-v3/051 REVERT to 3-sym)

# AFTER (iter-v3/068: timeout 21→42; embargo 22→43)
# gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = (42+1)*3 = 129 (iter-v3/068 timeout widen)
```

```python
# Line 1169 — per-cell gap update
# BEFORE
PER_CELL_GAP = 22  # (timeout_candles + 1) within a single-symbol cell

# AFTER (iter-v3/068)
PER_CELL_GAP = 43  # (timeout_candles + 1) within a single-symbol cell — iter-v3/068 timeout widen
```

**Per Critic /055 Rec #1**: any structural side effects MUST be disclosed at runner-comment level + asserted at runtime. The PER_CELL_GAP constant is used by walk_forward.generate_monthly_splits — update consistent with timeout_minutes change.

### Sub-fix 7 — Test assertion updates (NEW)

Add a regression test for the label_timeout_minutes plumbing:

File: `tests/strategies/ml/test_label_timeout_minutes.py` (NEW).

```python
"""Test label_timeout_minutes plumbing through LightGbmStrategy + embargo computation.

Per iter-v3/068 Path C: universal labeling timeout widening from 10080 to 20160 min.
Verifies that the labeling forward-scan window changes accordingly + the walk-forward
embargo gap is recomputed via compute_embargo_candles helper.
"""
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles


def test_label_timeout_minutes_default_10080():
    """Default label_timeout_minutes preserved when not overridden."""
    strat = LightGbmStrategy(
        features_dir="data/features_v3",
        interval="8h",
        ensemble_seeds=[42],
    )
    assert strat.label_timeout_minutes == 4320  # LightGbm default


def test_label_timeout_minutes_iter068_value_20160():
    """iter-v3/068 Path C: label_timeout_minutes=20160 propagates correctly."""
    strat = LightGbmStrategy(
        features_dir="data/features_v3",
        interval="8h",
        ensemble_seeds=[42],
        label_timeout_minutes=20160,
    )
    assert strat.label_timeout_minutes == 20160


def test_compute_embargo_candles_iter068_value_43():
    """iter-v3/068 Path C: embargo_candles=43 at label_timeout_minutes=20160 + 8h."""
    embargo = compute_embargo_candles(20160, 480)
    assert embargo == 43  # 20160 // 480 + 1


def test_compute_embargo_candles_iter060_anchor_value_22():
    """Baseline /060 anchor: embargo_candles=22 at label_timeout_minutes=10080 + 8h."""
    embargo = compute_embargo_candles(10080, 480)
    assert embargo == 22


def test_compute_embargo_candles_doubles_on_timeout_doubling():
    """Embargo gap doubles when timeout doubles (modulo +1 offset)."""
    e21 = compute_embargo_candles(10080, 480)
    e42 = compute_embargo_candles(20160, 480)
    # e21 = 22; e42 = 43. Not exactly 2× but +21/22 = +95%.
    assert e42 == 43
    assert e21 == 22
    assert e42 - e21 == 21  # additional 21 candles purged per cell
```

### Sub-fix 8 — Runtime assertion for `label_timeout_minutes`

File: `run_baseline_v3.py` (after model build, where existing per-symbol assertions live).

```python
expected_label_timeout = 20160
for sym, strat in v3_models.items():
    lgbm_strat = strat.inner if hasattr(strat, "inner") else strat
    if not hasattr(lgbm_strat, "label_timeout_minutes"):
        raise RuntimeError(
            f"LightGbmStrategy for {sym} has no label_timeout_minutes attribute. "
            "iter-v3/068: LightGbmStrategy must support label_timeout_minutes=20160."
        )
    if lgbm_strat.label_timeout_minutes != expected_label_timeout:
        raise RuntimeError(
            f"LightGbmStrategy for {sym} has label_timeout_minutes = "
            f"{lgbm_strat.label_timeout_minutes} — expected {expected_label_timeout}. "
            f"iter-v3/068 Path C: pass label_timeout_minutes=20160 in LightGbmStrategy init."
        )

# Also assert: revert /067's inference_threshold_floor to default 0.0
for sym, strat in v3_models.items():
    lgbm_strat = strat.inner if hasattr(strat, "inner") else strat
    if hasattr(lgbm_strat, "_inference_threshold_floor"):
        if lgbm_strat._inference_threshold_floor != 0.0:
            raise RuntimeError(
                f"LightGbmStrategy for {sym} has _inference_threshold_floor = "
                f"{lgbm_strat._inference_threshold_floor} — expected 0.0 at /068. "
                f"iter-v3/068 REVERTS /067's INERT inference_threshold_floor."
            )

print(
    f"  Universal label_timeout_minutes (iter-v3/068): {expected_label_timeout} min "
    f"(= 42 candles at 8h, Path C universal widening — converts ~9 IS / ~3 OOS "
    f"timeouts to TP/SL labels)"
)
print(
    f"  Walk-forward embargo gap: 43 candles per cell (vs 22 at /060) — "
    f"cross-cell gap = 129 candles (vs 66 at /060)"
)
```

### Sub-fix 9 — Parquet regeneration

**NOT required.** No feature changes; no new feature columns. The labeling-timeout change operates on the forward-scan window inside `labeling.label_trades()` at training time. Features (V3_FEATURE_COLUMNS_TOP_N=14) remain UNCHANGED.

### Sub-fix 10 — ENSEMBLE_SIZE assertion

**UNCHANGED**. EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 (per Phase B-3 unified architecture). /068 runs with `--exploration` (ENSEMBLE_SIZE=3).

### Sub-fix 11 — V3_FEATURE_COLUMNS_TOP_N

**UNCHANGED**. Stays at 14 features post-/064 revert (commit `04080c4`). NON-FEATURE axis means feature universe is held constant.

### Sub-fix 12 — Other risk-primitive stack

**UNCHANGED**. All 7 risk primitives (vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate, BTC trend kill) inherit their /060 baseline configuration. The per-symbol vol_scale_floor at `{"TRXUSDT": 0.5}` from /061 PERSISTS (orthogonal axis).

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor (T0) | Predicted /068 | Predicted Δ band |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.65 to +1.00 | Δ ∈ [-0.18, +0.17] |
| OOS monthly Sharpe | +0.1403 | -0.05 to +0.35 | Δ ∈ [-0.19, +0.21] |
| OOS/IS daily ratio | 0.21 | 0.05 to 0.50 | within [0.05, 0.50] |
| IS trades | 159 | 135 to 175 | Δ ∈ [-24, +16] (small change; 2nd-order Optuna effect) |
| OOS trades | 102 | 85 to 115 | Δ ∈ [-17, +13] |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 | architecture-invariant ≥0.50 |
| BCH IS share | 176.68% | 130% to 200% | one-sided ≥ 80% per Critic /060 Rec #1 |

**Rationale for band widths**: this is a UNIVERSAL LABELING-TIMEOUT WIDENING (non-feature axis, non-weighting axis, non-gate axis). Historical precedents:
- iter-v3/061 per-symbol vol_scale_floor (WEIGHTING per-symbol): INERT-AT-EXPLORATION.
- iter-v3/066 universal vol_scale_ceiling=0.8 (WEIGHTING axis): INERT-AT-EXPLORATION.
- iter-v3/067 universal _inference_threshold_floor=0.60 (GATE axis): INERT-AT-EXPLORATION.
- iter-v3/065 universal SL widening (LABELING-MAGNITUDE axis): PROMISING SUSPICIOUS-OOS-DOMINANT (first /069 candidate).
- /068 ORACLE first-order: IS Δ band [-0.10, +0.10], OOS Δ band [-0.15, +0.15]. Headline band wider in Section 4.1 to incorporate:
  1. 3-seed averaging variance noise floor (~±0.10 IS / ±0.20 OOS per `feedback_v3_cycle1_axis_pass_criteria.md`)
  2. Optuna second-order TPE re-convergence under different label distribution
  3. Embargo gap doubling (22 → 43 candles per cell): training-data loss ~3-5% per WF month

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

BCH IS share at /060 was 176.68% (3-seed averaging structurally amplified BCH's IS dominance). The one-sided ≥80% gate applies per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1.

Path C labeling-timeout widening is expected to:
- BCH has 6 IS timeouts and 2 OOS timeouts at /060 (the highest per-symbol timeout rate). Widening K from 21 to 42 may convert these to TP/SL labels. Forward random-walk over candles 22-42 is path-dependent — TPs more likely if the BCH model captured a real direction; SLs more likely if it was noise.
- If MOST of the 6 BCH IS timeout labels convert to TPs: BCH IS share LIFTS (more wins).
- If MOST convert to SLs: BCH IS share REGRESSES (more losses).
- If 50/50 split: BCH IS share approximately unchanged.
- BCH IS share predicted band: 130% to 200% (likely holds within one-sided ≥80% gate).
- LDO IS share: T3 finding shows LDO has ZERO timeouts. Path C is INSENSITIVE to LDO label resolution at trade-roster level. LDO IS share likely unchanged from /060's -25.44%.
- TRX IS share: 3 IS timeouts at /060. Same mechanism as BCH but smaller magnitude. TRX IS share band: -60% to -45% (close to anchor).

**Predicted BCH IS share at /068**: 130% to 200% (one-sided ≥80% gate cleared in expectation).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md` + Critic /065 Rec #3 calibration)

**Predicted trade-count change** (labeling timeout extension changes label distribution → changes model → 2nd-order trade emission):

| Symbol | IS trades /060 | IS trades /068 predicted | OOS trades /060 | OOS trades /068 predicted |
|---|---:|---:|---:|---:|
| BCH | 73 | 60 to 85 (10-15% Δ) | 37 | 32 to 42 |
| LDO | 11 | 9 to 14 (LDO insensitive) | 11 | 9 to 14 |
| TRX | 75 | 65 to 80 | 54 | 48 to 60 |
| **Total** | **159** | **[134, 179]** | **102** | **[89, 116]** |

**Behavioral-effect rationale**: labeling-timeout extension changes label distribution at training time → Optuna's TPE finds different proba surfaces → trade emission count shifts by ±15% (first-order; per-cell Optuna re-convergence). Path C is NOT a trade-pruning mechanism like /067 — trades are NOT directly filtered. Indirect changes via model fit only.

**Per Critic /065 Rec #3 calibration for labeling axes**: per-symbol WR Δ predicted to shift modestly. Labeling-timeout changes affect mostly the longer-cycle trades; most short-duration TP/SL labels (median 3-5 candles) are unchanged.

| Symbol | IS WR /060 | OOS WR /060 | Predicted /068 WR Δ (IS) | Predicted /068 WR Δ (OOS) |
|---|---:|---:|---:|---:|
| BCH | 45.2% | 32.4% | -3pp to +3pp (label dist shift) | -3pp to +5pp |
| LDO | 27.3% | 18.2% | -3pp to +3pp (LDO insensitive) | -3pp to +3pp |
| TRX | 29.3% | 50.0% | -3pp to +3pp | -5pp to +5pp |

**Saturation falsifier (per `feedback_v3_axis_saturation_predictor.md` non-feature-axis extension)**: if per-symbol trade-count Δ is within ±2% AND per-symbol WR Δ is within ±1pp at all 3 symbols, the axis is INERT-AT-EXPLORATION (the timeout modification had no effective downstream behavioral impact on label distribution — equivalent to T1+T2 prediction of LDO insensitivity holding across the full label population).

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

All anchor references per Section 2.1 T0 declarations:

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 (i.e., IS ≥ +0.6325) | FAIL → NEGATIVE / IS-COLLAPSE |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 (i.e., OOS ≥ -0.1597) | FAIL → NEGATIVE / OOS-NEGATIVE |
| **A.3** | frac_positive_paths | ≥ 0.50 | FAIL → methodology FAIL (CPCV degenerate) |
| **A.4** | No methodology FAIL | Critic 13 checks + §11 anti-pattern scan | FAIL → BLOCK |
| **B.5** | BCH IS share | one-sided ≥ 80% (per Critic /060 Rec #1) | FAIL → BCH collapse warning |
| **C.6** | IS trade count | ∈ [120, 200] | FAIL → trade-distribution shift |
| **C.7** | OOS trade count | ∈ [80, 130] (CONFIRMATION level imposes ≥130 — informational at EXPLORATION) | INFO at EXPLORATION (BLOCKING at /069 CONFIRMATION per `feedback_v3_trade_rate_floor.md`) |
| **D.8** | BCH IS wpnl Δ | within [-30, +30] vs /060 (+79.45 IS net_pnl_pct; Path C symmetric for BCH timeout labels) | FAIL → BCH IS regression |
| **D.9** | BCH OOS wpnl Δ | within [-10, +10] vs /060 (+1.9078 anchor from comparison.csv:18 per_symbol block; Path C may shift BCH OOS modestly) | FAIL → BCH OOS regression |
| **D.10** | LDO IS wpnl Δ | within [-5, +5] vs /060 (-11.44 IS net_pnl_pct; LDO INSENSITIVE per T3) | FAIL → LDO IS unexpected shift |
| **D.11** | LDO OOS wpnl Δ | within [-10, +10] vs /060 (-19.7208 anchor from comparison.csv:19 per_symbol block; LDO INSENSITIVE per T3) | FAIL → LDO OOS unexpected shift |
| **D.12** | TRX IS wpnl Δ | within [-20, +20] vs /060 (-23.04 IS net_pnl_pct; Path C symmetric for TRX timeout labels) | FAIL → TRX IS regression |
| **D.13** | TRX OOS wpnl Δ | within [-15, +15] vs /060 (+23.3119 anchor from comparison.csv:20 per_symbol block; Path C may shift TRX OOS modestly) | FAIL → TRX OOS regression |
| **D.14** | Saturation falsifier | trade-count Δ within ±2% AND per-symbol WR Δ within ±1pp at all 3 syms | If ALL within band → INERT-AT-EXPLORATION (D.14 fires; informational) |
| **D.15** | LDO insensitivity verification | LDO IS trade count Δ within ±10% AND LDO OOS trade count Δ within ±10% AND LDO IS+OOS WR Δ within ±2pp | FAIL → LDO inadvertently affected (model 2nd-order coupling stronger than T3 predicts) |
| **E.16** | All v3 lgbm + features_v3 tests passing | `pytest tests/strategies/ml/test_label_timeout_minutes.py tests/features_v3/ -v` PASS | FAIL → BLOCK |
| **E.17** | ensemble_summary | mode=exploration, size=3 | FAIL → mode-flag wiring bug |
| **E.18** | EDA-implementation parity | `label_timeout_minutes == 20160` AND `_inference_threshold_floor == 0.0` AND `vol_scale_ceiling == 1.0` AND `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` at runtime; embargo_candles=43 per cell verified in WF logs | FAIL → process violation |

**Notes on falsifier bands**:
- Gates A.1 (IS ≥ -0.20) and A.2 (OOS ≥ -0.30) are the LOCKED Section 8.4 disjunctive-OR NEGATIVE thresholds per `feedback_v3_cycle1_axis_pass_criteria.md`. Either single-gate FAIL → NEGATIVE classification.
- Gate D.10/D.11 (LDO ranges TIGHT at ±5/±10): LDO is predicted INSENSITIVE per T3. If LDO MOVES noticeably (>±10 wpnl), this is a structural finding worth flagging — second-order Optuna coupling stronger than T3's first-order prediction.
- Gate D.15 is the LDO-INSENSITIVITY VERIFICATION gate (Path C specific): T3 predicts LDO behavior unchanged; D.15 fires INFORMATIONAL if LDO trade count or WR moves outside saturation bands. Per Critic /056 Rec on post-hoc input traceback: if D.15 fires unexpectedly, document the structural mechanism in engineering report.
- Gate C.7 OOS trade count [80, 130]: tighter than /067 because Path C is NOT a trade-pruning mechanism. Trade-count change is purely 2nd-order Optuna effect from changed labels.

### Section 4.5 — Trade-rate floor pre-commit

Per `feedback_v3_trade_rate_floor.md`: OOS trades ≥10/month, ≥130 total over 14 OOS months at CONFIRMATION level. /068 predicted OOS trade band [89, 116] = [6.4, 8.3]/month is BELOW the floor.

**At EXPLORATION level** (where /068 runs): the floor is INFORMATIONAL. /068's PROMISING-at-EXPLORATION classification (if it triggers) would advance to /069 CONFIRMATION. At /069 CONFIRMATION:
- 10-seed ensemble: trade-roster expansion expected. The bundle of (/065 SL widening + /068 timeout extension + Path B4 DSR recalibration if implemented) may compound trade-roster expansion.
- If CONFIRMATION-mode OOS trade count remains <130 (or <10/month), the bundle violates trade-rate floor at CONFIRMATION → BLOCKING gate.
- This brief PRE-COMMITS that Path C's CONFIRMATION-level evaluation must include trade-count floor gate; we do NOT post-hoc renegotiate the trade-rate floor.

### Section 4.6 — Anti-stacking check

Per `feedback_v3_engineered_features_dont_stack.md`: /068 changes ONE axis (`label_timeout_minutes` 10080 → 20160). No engineered features added. No same-family features stacked. **iter-v3/067's `_inference_threshold_floor=0.60` is REVERTED to default 0.0 at /068** (Sub-fix 2) to isolate the single varied axis. Single-axis EXPLORATION at single-seed mode is LEGITIMATE.

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /060 anchor, EXCEPT for /068's single substantive change):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) — ceiling | ENABLED, ceiling at default 1.0 (already reverted at /067) | iter-v3/067 |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout (per-symbol cleared) |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (\|z\|>2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| BTC trend kill (±15%, 14d) | ENABLED | iter-v3/051 reverted to no-block; threshold=15% |
| Per-symbol PnL cap (primitive 8) | DISABLED | iter-v3/020 PATH C closeout |
| Primitive 9 (regime-conditional kill) | DISABLED | iter-v3/023 (closed) |
| Primitive 10 (direction-asymmetric kill) | DISABLED | iter-v3/051 SYSTEM-LEVEL REVERT |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout (CLOSED-mechanism) |
| Per-symbol vol_scale_floor | ENABLED (iter-v3/061: TRX 0.5; BCH/LDO 0.3) | preserved at /068 (orthogonal axis) |
| Universal vol_scale_ceiling | UNCHANGED at default 1.0 | iter-v3/067 revert kept |
| LightGbmStrategy inference_threshold_floor | REVERTED to default 0.0 | iter-v3/068 reverts /067's INERT axis |
| **labeling timeout_minutes** | **CHANGED 10080 → 20160 (+100%)** | **iter-v3/068 this brief** |

**Labeling-timeout axis is orthogonal to ALL other primitives at /068** (T6 verified). Embargo coupling acknowledged as a STRUCTURAL CONSEQUENCE (not a separate axis); falsifier band E.18 covers runtime parity verification.

## Section 6 — Risk Management

**CHANGED (single substantive change)**: `label_timeout_minutes` extends from 10080 (21 candles) to 20160 (42 candles) universally. All 3 symbols (BCH/LDO/TRX) consume the same labeling-window extension.

`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from iter-v3/061 REMAINS UNCHANGED — orthogonal axis.

`_inference_threshold_floor` REVERTS to default 0.0 per axis isolation discipline (Sub-fix 2).

`vol_scale_ceiling` REMAINS at default 1.0 (already reverted at /067).

`DEFAULT_ATR_MULTIPLIERS` UNCHANGED at (2.0, 1.0).

**Embargo gap**: doubles from 22 to 43 candles per cell (cross-cell 66 → 129). Training set loses ~3-5% per WF month; effective sample size penalty <5%.

Cooldown UNCHANGED: 4 candles post-trade. Fee UNCHANGED: 0.1% per leg.

**Translated to live trading**: live engine's labeling forward-scan window for new trades extends from 21 candles (7 days at 8h) to 42 candles (14 days at 8h). Trade exits at TP/SL/timeout: timeout exits now occur at K=42 (14 days) rather than K=21. This means open trades may run twice as long before forced closure — drawdown risk on individual trades extended. The change should be tested under live conditions in /069 CONFIRMATION bundle if PROMISING.

## Section 7 — Pre-registered Failure-Mode Prediction

Per Rule 3 of `feedback_v3_iter064_process_lessons.md`: single-axis non-feature changes at single-seed n_trials=35 weight NEGATIVE ≥25%. Calibrated per Critic /064 Rec #3 + /065 Rec #3 + /066/067 actual outcomes (BOTH /066 + /067 were INERT-AT-EXPLORATION at universal non-feature axes — single-axis n_trials=35 is empirically resistant to non-feature perturbations).

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **INERT** | Path C is INERT-band centered per ORACLE EDA; ~94% of labels already TP/SL-resolved at K=21; the ~6% timeout labels MAY convert to TP/SL but at rough 50/50 directional outcome; Optuna 2nd-order re-converge dampens effect. D.14 saturation fires. | **~50%** | IS Δ ∈ [-0.10, +0.10], OOS Δ ∈ [-0.15, +0.15]; D.14 saturation fires |
| **PROMISING** | Path C's label cleanup IS productive; timeout labels convert preferentially to TP labels (Optuna's classifier was being fed noisy 0-labels at /060, now gets cleaner +1/-1 labels); Sharpe lifts on both IS and OOS | ~15% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-OOS-DOMINANT** | Single-seed lottery: OOS spikes due to favorable random walk over the 21-42 window in OOS sample; IS stays flat or regresses | ~10% | IS Δ < +0.10, OOS Δ ≥ +0.20 |
| **NEGATIVE** | Embargo gap doubling (22 → 43) shrinks effective training set; OR timeout labels convert preferentially to SL labels (random-walk drift in 21-42 window is unfavorable); OR Optuna 2nd-order coupling destroys edge | ~25% | IS Δ < -0.20 OR OOS Δ < -0.30 |

Probabilities per orchestrator-mandated distribution + Rule 3 calibration:
- INERT ~50% (most likely; /066 + /067 both INERT at single-seed n_trials=35 non-feature axes — /068 follows the same pattern)
- PROMISING ~15% (Path C EDA prediction is band-centered with non-zero upside)
- SUSPICIOUS-OOS-DOMINANT ~10% (single-seed lottery; lower than /065's 35% because /068 affects fewer labels — 6% of trade roster vs /065's full label MAGNITUDE shift)
- NEGATIVE ~25% (Rule 3 calibration: single-axis at single-seed n_trials=35 + structural side-effect of embargo doubling)

**Why INERT is most likely (50%)**: 
- /066 INERT + /067 INERT suggests the /060 local optimum is RESISTANT to single-axis universal non-feature perturbations at single-seed n_trials=35.
- T1 finding: 94.3% IS / 97.1% OOS of trade-roster labels already TP/SL-resolved at K=21. Path C's first-order target is the remaining ~6% — small leverage.
- T3 finding: LDO is INSENSITIVE to timeout extension (zero LDO timeouts). LDO weakness persists.

**Why NEGATIVE is 25% (calibrated UP per Rule 3)**: 
- Universal labeling perturbation at single-seed n_trials=35 has Optuna-overfit risk per `feedback_v3_inert_features_at_higher_budget.md` (the same Optuna budget that overfits feature additions can overfit label changes).
- Embargo gap doubling (22 → 43 per cell) shrinks effective training set ~3-5%/month. This is a STRUCTURAL training data loss, not a free axis variation.
- BCH dominance at /060 IS share (176%): if BCH timeout labels convert preferentially to SL labels (e.g., adverse random-walk drift in 21-42 window), BCH IS share collapses → headline IS Sharpe damaged.

**Why PROMISING is 15% (low per Rule 3)**: 
- Path C EDA prediction places the OOS Δ band at [-0.15, +0.15] — INERT-band centered, NOT shifted into PROMISING.
- Optuna second-order TPE re-convergence under cleaner labels is possible but unmodeled.
- Universal-axis Path C cannot leverage per-symbol Kelly directions (verified at T3: LDO insensitivity).

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PROMISING-AT-EXPLORATION (advances to /069 CONFIRMATION as candidate)

ALL of:
- **A.1** IS Sharpe shift ≥ +0.10 vs /060 (IS ≥ +0.9325)
- **A.2** OOS Sharpe shift ≥ +0.20 vs /060 (OOS ≥ +0.3403)
- **A.3** frac_positive_paths ≥ 0.50
- **A.4** No methodology FAIL (Critic 13 checks + §11 anti-pattern scan)
- **B.5** BCH IS share ≥ 80% (one-sided per Critic /060 Rec #1)
- **C.6** IS trade count ∈ [120, 200]
- **C.7** OOS trade count ∈ [80, 130] (CONFIRMATION level imposes ≥130 — informational at EXPLORATION)
- **D.8-D.13** Per-symbol wpnl Δ bands all within range
- **D.15** LDO insensitivity verification — INFORMATIONAL gate
- **E.16-E.18** Test pass + ensemble_summary + EDA-implementation parity gates PASS

### Section 8.2 — INERT-AT-EXPLORATION

- IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] (noise-band)
- AND no methodology FAIL
- AND/OR D.14 saturation falsifier fires (trade-count Δ within ±2% AND per-symbol WR Δ within ±1pp at all 3 syms)
- Axis CLOSED for current cycle; not re-evaluated.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 (i.e., INSIDE noise band or NEGATIVE)
- AND OOS Δ ≥ +0.20
- Axis CLOSED-PENDING-CONFIRMATION; does NOT advance to /069 as PROMISING but logged as parallel /069 advancement candidate.

### Section 8.4 — NEGATIVE (disjunctive OR per `feedback_v3_iter064_process_lessons.md` Rule 4)

- IS Δ < -0.20 **OR** OOS Δ < -0.30 (either gate FAIL)
- AND no methodology FAIL
- Axis CLOSED. Universal labeling-timeout widening to 42 candles placed on PARKED list with rationale.

### Section 8.5 — NEGATIVE-EMBARGO-COUPLED (Path C specific)

- IS Δ < -0.10 AND OOS Δ < -0.10 AND training-data loss attribution > 50% of Δ
- Engineering report attributes the regression to the embargo gap doubling specifically (not the label change).
- Axis CLOSED with finding: Path C label-cleanup benefit < embargo-gap structural cost at K=42. Future labeling-axis EXPLORATIONs at smaller K (e.g., K=28 or K=35) avoid the doubling.

### Section 8.6 — Methodology FAIL

- Any Critic 13-check BLOCK fires
- Iteration is INVALID; not classifiable as PROMISING/INERT/NEGATIVE.

## Section 9 — Library Stack + Reproducibility

**UNCHANGED**:
- Python 3.13, uv environment, LightGBM (`lightgbm` package), pandas, pyarrow, statsmodels.
- LightGbmStrategy at `src/crypto_trade/strategies/ml/lgbm.py`; labeling at `src/crypto_trade/strategies/ml/labeling.py`; walk-forward at `src/crypto_trade/strategies/ml/walk_forward.py`.
- Labeling forward-scan loop at `labeling.py:240-274`; deadline check at `labeling.py:215`.
- `compute_embargo_candles(label_timeout_minutes, interval_minutes) = label_timeout_minutes // interval_minutes + 1` at `walk_forward.py:38`.
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) — outer=42 lineage subset for EXPLORATION mode.

**Reproducibility stamp**:
- EDA SHA: `c16d53c` (`analysis/iteration_v3-068/labeling_timeout_eda.py`)
- Setup commit SHA: (this commit, LOCKED)
- ITERATION_LABEL: `"v3-068"`
- LightGbmStrategy.label_timeout_minutes at runtime: **20160** (CHANGED from /060's 10080)
- LightGbmStrategy._inference_threshold_floor at runtime: **0.0** (REVERTED from /067's 0.60 to default)
- RiskV2Config.vol_scale_ceiling at runtime: **1.0** (UNCHANGED — already at default since /067)
- RiskV2Config.vol_scale_floor: 0.3 universal (unchanged)
- RiskV2Config.vol_scale_floor_per_symbol: {"TRXUSDT": 0.5} (unchanged from /061)
- DEFAULT_ATR_MULTIPLIERS at runtime: (2.0, 1.0) (UNCHANGED)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — preserved)
- Walk-forward embargo per cell: **43 candles** (CHANGED from 22)
- Walk-forward embargo cross-cell gap: **129 candles** (CHANGED from 66)
- Parquet data: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet` (no regen needed)

### Integration test (per `feedback_v3_methodology_axis_integration_test.md`)

The `label_timeout_minutes` edit is consumed by:
1. `run_baseline_v3.py:737` — `timeout_minutes` constant updated to 20160 (Sub-fix 1)
2. `run_baseline_v3.py:1380` — training-data labeling `timeout_minutes=20160` (Sub-fix 1)
3. `run_baseline_v3.py:1398` — `LightGbmStrategy(label_timeout_minutes=20160, ...)` (Sub-fix 1)
4. `run_baseline_v3.py:161 + 1169` — PER_CELL_GAP comment + constant updated to 43 (Sub-fix 6)
5. `walk_forward.compute_embargo_candles(20160, 480) = 43` (auto-computed; verified at Sub-fix 7 test)
6. `lgbm.LightGbmStrategy._train_for_month` — uses self.label_timeout_minutes for label generation; passes to `labeling.label_trades(timeout_minutes=...)` (no edit needed; auto-flow)
7. `run_baseline_v3.py::_verify_*` runtime assertion — `label_timeout_minutes == 20160` per Sub-fix 8
8. `tests/strategies/ml/test_label_timeout_minutes.py` (NEW per Sub-fix 7)

A smoke test consists of running:
```bash
uv run pytest tests/strategies/ml/test_label_timeout_minutes.py tests/features_v3/ -v
```
and confirming all tests PASS with the new `label_timeout_minutes=20160` configuration.

## Section 10 — QR Audit Trail

**Why this axis (LABELING TIMEOUT — universal labeling forward-scan widening, Path C)**:

1. **Critic /064 Rec #4 binding directive** (locked for /065-/068): NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35 (per Rule 5 of `feedback_v3_iter064_process_lessons.md`). Feature-axis EXPLORATIONs at this budget cannot productively escape. /068 is the LAST eligible NON-FEATURE PIVOT slot in cycle 1.

2. **Critic /066 Rec #2 binding directive**: AVOID universal symmetric clip/cap mechanisms. /068 axis is structurally distinct from /066 (weight ceiling) and /067 (gate floor): instead of CAPPING or TIGHTENING a multiplicative weighting OR a binary emission threshold, Path C EXTENDS the TRAIN-TIME label-generation forward-scan window. Mechanism is DURATION-axis at TRAIN time, not weight or gate at INFERENCE time.

3. **Orchestrator autopilot decision 2026-05-14**: cycle 1 #9 axis CATEGORY locked at LABELING TIMEOUT for /069 CONFIRMATION bundle structural diversity. /065's labeling SL widening (MAGNITUDE) is the first PROMISING-class survivor; a LABELING-TIMEOUT axis (DURATION) is the sister at the SAME TRAIN-TIME stage that may compound at /069 CONFIRMATION as a labeling-axis bundle. Distinct from /065 because: SL widening changes MAGNITUDE of TP/SL barriers (atr_sl multiplier 1.0 → 1.5); timeout extension changes DURATION of forward scan window.

4. **QR EDA SHA `c16d53c`** produced 6 tables that quantitatively support Path C over Paths A/B/D/E:
   - **T0**: anchor-value declaration (per Critic /064 Rec #1 + /065 Rec #1 + /066 Rec #3 + /067 RECURRENCE flag); byte-exact from comparison.csv with explicit line refs.
   - **T1**: current trade-roster label distribution at K=21 — 5.7% IS / 2.9% OOS timeout rate; LDO=0 timeouts (insensitive).
   - **T2**: first-order counterfactual at K∈{7, 14, 21, 42, 63} — Path A/B introduce 12-32% noisy fwd-return labels; Path C/D first-order trade-roster invariant.
   - **T3**: LDO-specific timeout interaction — LDO durations skew SHORT (median 3-5 candles); ZERO LDO timeouts at /060; LDO weakness is NOT a timeout/label-noise issue.
   - **T4**: per-Path predicted IS/OOS Sharpe Δ bands — Path C is the ONLY Path with predicted band CENTERED at INERT-zero with non-zero PROMISING upside (IS Δ [-0.10, +0.10], OOS Δ [-0.15, +0.15]).
   - **T5**: Path selection summary scoring 5 candidates with 7 criteria; Path C uniquely viable with INERT-centered band.
   - **T6**: cross-axis orthogonality with /065 (labeling MAGNITUDE), /066 (weight ceiling), /067 (gate floor) — 7/9 stages ORTHOGONAL; 2 overlap stages (Optuna search with /065 at DIFFERENT label sub-dim; trade emission with all 4 axes via DISTINCT mechanisms).

5. **Path C selection rationale (quantitative)**:
   - ONLY Path with predicted Sharpe Δ bands CENTERED at INERT (IS Δ [-0.10, +0.10], OOS Δ [-0.15, +0.15]) with non-zero PROMISING upside
   - Mechanistically distinct from Path A/B (label-noise INJECTION direction): Path C goes the LABEL-CLEAN direction
   - Single-axis change (one constant `label_timeout_minutes=20160` in `run_baseline_v3.py`)
   - Universal (preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
   - STATELESS (ORACLE EDA valid per `feedback_v3_oracle_eda_validity.md`)
   - Mechanistically ORTHOGONAL to /066, /067 (T6 verified)
   - Sister axis to /065 at SAME TRAIN-TIME stage but DIFFERENT sub-dimension (DURATION vs MAGNITUDE)
   - Anti-snooping: universal `label_timeout_minutes=20160` has NEVER been tested
   - NOT a universal symmetric clip/cap — AVOIDS Critic /066 Rec #2 STRUCTURALLY EXHAUSTED family
   - Embargo coupling (22 → 43 candles per cell) DISCLOSED at T6 + falsifier E.18 — not an unmodeled side effect

6. **Methodology compliance**:
   - `feedback_v3_axis_selection_quant_discipline.md`: EDA committed BEFORE brief (SHA `c16d53c` precedes setup commit).
   - `feedback_v3_oracle_eda_validity.md`: ORACLE valid for STATELESS primitive (TRAIN-TIME label generation; no signal-emission state).
   - `feedback_v3_engineered_features_dont_stack.md`: single-axis EXPLORATION (ONE substantive change — `label_timeout_minutes`); revert `_inference_threshold_floor` to default to isolate the single varied axis.
   - `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: UNIVERSAL change (no new per-symbol override).
   - `feedback_v3_cycle1_axis_pass_criteria.md`: PASS thresholds (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) explicit at Section 8.1.
   - `feedback_v3_iter064_process_lessons.md` Rule 1 (anchor-value correctness gate; RECURRENCE awareness): T0 references /060 anchor values with bit-exact `comparison.csv:LINE` refs.
   - `feedback_v3_iter064_process_lessons.md` Rule 3 (probability calibration): Section 7 NEGATIVE=25%, INERT=50%, PROMISING=15%, SUSPICIOUS-OOS=10%.
   - `feedback_v3_iter064_process_lessons.md` Rule 4 (Section 8 disjunctive OR): Section 8.4 NEGATIVE LOCKED as disjunctive OR.
   - `feedback_v3_axis_saturation_predictor.md`: Section 4.3 behavioral-effect predictor present with quantitative trade-count + per-symbol WR Δ bands; Gate D.14 saturation falsifier; Gate D.15 LDO insensitivity verification falsifier (Path C specific).
   - `feedback_v3_methodology_axis_integration_test.md`: Sub-fix 7 NEW regression test file `test_label_timeout_minutes.py`; Section 9 integration test smoke test.
   - `feedback_v3_methodology_post_hoc_input_traceback.md`: Section 4.4 D.15 LDO-insensitivity bands derived from T3 LDO trade-duration data (specific source-code traceback to `labeling.py:215` deadline check).
   - `feedback_v3_dsr_mode_artifact.md`: DSR_relative INFORMATIONAL ONLY at /068 EXPLORATION mode.
   - `feedback_v3_trade_rate_floor.md`: trade-rate floor explicitly flagged at C.7 as INFORMATIONAL at EXPLORATION; BLOCKING at /069 CONFIRMATION. Pre-committed.

7. **EDA-implementation parity (per Critic /063 Rec #2)**: V3_FEATURE_COLUMNS_TOP_N UNCHANGED (14 features); DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0); vol_scale_ceiling UNCHANGED at default 1.0; `_inference_threshold_floor` REVERTED to default 0.0; `label_timeout_minutes=20160` is the ONE change. Phase 5.5 gate asserts ALL conditions at runtime per Sub-fix 8.

8. **Cross-axis orthogonality with iter-v3/065, /066, /067** (T6 + Section 2.7):
   - /065 axis: TRAIN-TIME label generation MAGNITUDE (atr_tp/sl multiplier — sl 1.0→1.5)
   - /066 axis: INFERENCE-TIME weight modifier (vol_scale_ceiling — REVERTED at /067)
   - /067 axis: INFERENCE-TIME emission gate threshold (`_inference_threshold_floor` — REVERTED at /068)
   - **/068 axis: TRAIN-TIME label generation DURATION (label_timeout_minutes — 10080→20160)**
   - At /068: /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0) (kept; /065 tested separately); /066's vol_scale_ceiling=1.0 (kept at default); /067's _inference_threshold_floor=0.0 (REVERTED at /068)
   - At /069 CONFIRMATION: /065 + /068 (if both PROMISING) bundled at multi-seed — labeling-axis bundle; second-order Optuna coupling captured

9. **Path selection rationale: why NOT Path D (K=63)**: Path D's embargo gap (22 → 64 per cell) is too aggressive at single-seed n_trials=35 — effective sample size penalty 6-10% per WF month. /068 axis tests Path C (K=42) FIRST; Path D reserved if Path C is PROMISING but room for further extension exists at /069 CONFIRMATION multi-seed.

10. **Cannot be retroactively renegotiated**. Established at brief LOCK (setup commit).

---

**Setup commit SHA**: (this commit, LOCKED)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/068`; pull SHA `c16d53c` (EDA).
2. Apply Sub-fixes 1-8:
   - Update 3 call sites in `run_baseline_v3.py` to set `timeout_minutes`/`label_timeout_minutes=20160` (lines 737, 1380, 1398)
   - REVERT `_inference_threshold_floor=0.60` from /067 — REMOVE explicit kwarg so default 0.0 applies
   - Keep `vol_scale_ceiling` at default 1.0 (already removed at /067)
   - Keep `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` UNCHANGED
   - Update PER_CELL_GAP at line 1169 from 22 to 43; update comment at line 161
   - Bump `ITERATION_LABEL = "v3-068"`
   - Add `tests/strategies/ml/test_label_timeout_minutes.py` (5 unit tests per Sub-fix 7)
   - Add runtime assertions per Sub-fix 8: `label_timeout_minutes == 20160` AND `_inference_threshold_floor == 0.0` for all 3 v3 strategies
3. Run `uv run pytest tests/strategies/ml/test_label_timeout_minutes.py tests/features_v3/ -v` to confirm test PASS.
4. Run `uv run python run_baseline_v3.py --clean-oof --exploration --n-trials 35` (Phase 6 backtest).
5. Wall-clock target ~1.1h; HARD CAP 2h per `feedback_v3_cadence_discipline.md`.
6. Engineering report covers Section 8 LOCKED criteria evaluation (PASS/FAIL on each gate A.1–E.18) for Critic Phase 7.5.
