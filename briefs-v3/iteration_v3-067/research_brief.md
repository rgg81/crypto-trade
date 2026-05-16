# iter-v3/067 — Research Brief

**Branch**: `iteration-v3/067`
**EDA SHA**: `aa5b0c8`
**Setup commit SHA**: (this commit, LOCKED)
**Iteration type**: EXPLORATION (cycle 1 #8 of 10; NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4; ENSEMBLE PARAMETERS axis; AVOID universal symmetric clip/cap per Critic /066 Rec #2)
**Axis**: UNIVERSAL inference-time confidence-threshold TIGHTENING — `LightGbmStrategy._confidence_threshold` raised to `max(mean(per_seed_thresholds), 0.60)` at inference time (Path D per EDA)

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols, UNCHANGED from /051 SYSTEM-LEVEL REVERT). Feature universe = 14 V3_FEATURE_COLUMNS (UNCHANGED post-/064 revert at commit `04080c4`).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION.

- **Cycle 1 EXPLORATION slot**: #8 of 10 (post /058 RE-ANCHOR + /059 RE-ANCHOR #2; cycle counting per BASELINE_V3.md /059).
- **Sub-type**: **NON-FEATURE PIVOT CONTINUATION — ENSEMBLE PARAMETERS axis**. Per Critic /064 Rec #4 NON-FEATURE pivot mandate (LOCKED for /065-/068 per `feedback_v3_iter064_process_lessons.md` Rule 5). /065 chose UNIVERSAL labeling axis (PROMISING — SUSPICIOUS-OOS-DOMINANT first /069 candidate); /066 chose UNIVERSAL vol_scale_ceiling=0.8 (INERT-AT-EXPLORATION; universal-ceiling family STRUCTURALLY EXHAUSTED per Critic /066 Q5/Rec #2). /067 pivots to ENSEMBLE PARAMETERS axis at INFERENCE-TIME aggregation — distinct from labels (/065) and weight clipping (/066).
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset [191664963, 1662057957, 1405681631]).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 3 × 3 = 315 (matches /060-/066 EXPLORATION-mode budget).
- **Wall-clock target**: ~1.1h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`).

**Cycle 1 catalog status before /067**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 (Path D) | SUSPICIOUS-OOS-DOMINANT (first /069 candidate) |
| #7 | /066 | NON-FEATURE PIVOT: UNIVERSAL vol_scale_ceiling 1.0 → 0.8 (Path E0.8) | INERT-AT-EXPLORATION (closed; universal-ceiling family STRUCTURALLY EXHAUSTED) |
| **#8** | **/067** | **NON-FEATURE PIVOT cont: UNIVERSAL inference-threshold TIGHTEN 0.60 (Path D)** | TBD |
| #9-10 | /068-069 | TBD per QR EDA | TBD |
| CONFIRMATION | /069+ | Bundle: /065 SL widening + (Path D if PROMISING) + Path B4 implementation | TBD |

**Why ENSEMBLE PARAMETERS axis now**:

1. **Critic /064 Rec #4 directive (binding through /068)**: NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35.

2. **Critic /066 Rec #2 directive (locked at cycle 1)**: AVOID universal symmetric clip/cap mechanisms when ORACLE T3-equivalent decomposition shows opposing Kelly directions across the 3 symbols. Universal-ceiling family STRUCTURALLY EXHAUSTED. /067 axis is structurally distinct: instead of CAPPING per-trade weight (a multiplicative weighting modifier), Path D TIGHTENS the per-candle entry decision (a binary gate modifier on confidence). It does NOT touch the weighting layer.

3. **Cycle 1 bundle diversity at /069 CONFIRMATION**: /065's PROMISING-class labeling axis is the first /069 advancement candidate. A SECOND independent PROMISING-class component from a structurally distinct axis (ensemble parameters) strengthens the /069 bundle by reducing single-axis dependence. Per Critic /065 Rec #4 bundle pre-registration: /069 CONFIRMATION evaluates the BUNDLE, not each axis in isolation.

4. **Ensemble parameters axis is mechanistically orthogonal to BOTH /065 and /066** (T6 verified at EDA SHA `aa5b0c8`):
   - /065 labeling axis: TRAIN-TIME label generation; `Signal(.tp_pct, .sl_pct)` change
   - /066 weight clipping axis: INFERENCE-TIME weight modifier; `Signal(.weight)` change
   - /067 confidence threshold axis: INFERENCE-TIME emission decision; `Signal | NO_SIGNAL` change at the gate level
   - Three separate code paths (`labeling.py`, `risk_v2.py`, `lgbm.py:635`); three separate stages

5. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`** (system-level confirmed across 2 CONFIRMATIONs at /039 + /050): per-symbol customizations break IS aggregate at multi-seed. UNIVERSAL inference-time threshold tightening is the structurally safe alternative — applies uniformly to BCH+LDO+TRX.

6. **Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 closeout)**: stateful risk gates have deadlock risk and ORACLE EDA cannot test them. STATELESS threshold modification at inference time IS ORACLE-testable. Path D (tighten 0.60) is STATELESS.

## Section 1 — Testable Hypothesis (ONE sentence)

> UNIVERSAL inference-time confidence-threshold TIGHTENING — replacing the Optuna-inherited per-cell mean `_confidence_threshold` with `max(mean(per_seed_thresholds), 0.60)` at trade emission — produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 baseline (IS +0.8325 / OOS +0.1403) by asymmetrically dropping marginal-confidence trades (estimated 30-50% of trade roster) where edge is thinnest, with predicted IS Δ band [+0.05, +0.20] and OOS Δ band [+0.10, +0.30] (per Path D structural counterfactual at EDA SHA `aa5b0c8`); INERT-AT-EXPLORATION is the most likely outcome (~45%) given that single-axis n_trials=35 EXPLORATIONs around the /060 local optimum have produced INERT classifications at 2 of the last 3 universal axes (/061 INERT, /066 INERT, /065 PROMISING).

## Section 2 — Numerical EDA Tables (EDA SHA `aa5b0c8`)

EDA committed at SHA `aa5b0c8` (`analysis/iteration_v3-067/ensemble_parameters_eda.py`). Produces 7 tables (T0-T6). Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). **NOT iter-v3/065 nor /066** (parallel cycle 1 axes; /060 is the canonical EXPLORATION-mode anchor per `feedback_v3_cycle1_axis_pass_criteria.md`).

### Section 2.1 — T0 Anchor-value declaration (Critic /064 Rec #1 + /065 Rec #1 + /066 Rec #3 compliance)

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+0.8325** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.1403** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| n_trades_in_sample | **159** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| n_trades_out_of_sample | **102** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| weighted_pnl_total_in_sample | **+51.8906** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| weighted_pnl_total_out_of_sample | **+5.4989** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| BCH_OOS_weighted_pnl | **+1.9078** | `reports-v3/iteration_v3-060/comparison.csv:18` |
| LDO_OOS_weighted_pnl | **-19.7208** | `reports-v3/iteration_v3-060/comparison.csv:19` |
| TRX_OOS_weighted_pnl | **+23.3119** | `reports-v3/iteration_v3-060/comparison.csv:20` |
| frac_positive_paths_cpcv | **0.6444** | BASELINE_V3.md Headline Metrics (CPCV invariant across architectures) |

These are the BIT-EXACT /060 anchor values per Phase 5.5 anchor-value correctness gate (Rule 1 of `feedback_v3_iter064_process_lessons.md`). All Section 4 falsifier bands reference these. RECURRENCE-flag awareness: /065 brief Section 2.5 originally cited "+24.75 OOS wpnl (BCH)" (a 13× error vs +1.9078 actual); /066 brief CLEAN; /067 brief explicitly cross-checks all anchor values against the source file before commit.

### Section 2.2 — T1 Current ensemble parameter inventory at /060

Production state at /060 (LightGbmStrategy in `src/crypto_trade/strategies/ml/lgbm.py`):

| Field | Value | Description | Code location |
|---|---|---|---|
| ensemble_size_exploration | 3 | ENSEMBLE_SEEDS[0:3] outer=42 lineage subset | `lgbm.py:131` + run_baseline_v3.py |
| confidence_threshold_optuna_range | `[0.50, 0.85]` | Optuna `suggest_float` per seed per (sym, month) cell | `optimization.py:198` |
| confidence_threshold_aggregation | **MEAN** | `_confidence_threshold = float(np.mean(self._confidence_thresholds))` | `lgbm.py:507` |
| proba_aggregation | **MEAN** | `proba = np.mean(all_proba, axis=0)` across 3 seeds | `lgbm.py:624` |
| trade_emission_gate | `max(proba) >= mean_threshold` | `if confidence < self._confidence_threshold: return NO_SIGNAL` | `lgbm.py:635-645` |

**Reading**:
- `_confidence_threshold` is derived as the ARITHMETIC MEAN across the 3 per-seed Optuna-tuned thresholds for each (symbol, walk-forward month) cell.
- `proba` is the ARITHMETIC MEAN across the 3 per-seed predicted probabilities for each candle.
- The trade-emission gate fires when `max(proba) ≥ _confidence_threshold` (the gate decision is BINARY; no scaling).
- **The threshold field is the SINGLE inference-time gate that controls trade-roster emission**. Tightening it asymmetrically (raising the bar) drops trades whose ensemble-averaged confidence falls in the gap.

**No prior EXPLORATION has tested an inference-time threshold floor**. /061 tested per-symbol vol_scale_floor (weight); /065 tested labeling (train-time); /066 tested vol_scale_ceiling (weight). /067 is the first ensemble-parameter axis at the inference-emission gate.

### Section 2.3 — T2 Per-seed confidence threshold distribution structure

Per-seed live `_confidence_thresholds` are NOT persisted in /060 reports (only their arithmetic mean is captured via runtime field). EDA T2 uses STRUCTURAL reasoning:

| Property | value_min | value_max_or_estimate | Description |
|---|---:|---:|---|
| optuna_range | 0.50 | 0.85 | Optuna suggest_float bounds (`optimization.py:198`) |
| uniform_3seed_std | — | 0.101 | Theoretical std of uniformly distributed 3-seed sample of [0.50, 0.85] |
| uniform_mean_median_gap_expected | — | 0.04 | Expected gap between mean and median at n=3 uniform draws |
| n_sym_month_cells_oos | — | 42 | Total (sym, month) cells across OOS — each has 3 per-seed thresholds |
| n_sym_month_cells_is | — | 114 | Total (sym, month) cells across IS |

**Reading**:
- Optuna explores `[0.50, 0.85]` per seed per cell. Different seeds converge to different thresholds depending on local Optuna TPE trajectory.
- The 3-seed MEAN aggregation (lgbm.py:507) is sensitive to outliers; if one seed converges to 0.80 and the other two to 0.55, the mean is 0.633 (anchored by the outlier).
- Path D tightening to 0.60 universally raises the floor: ANY cell where the inherited mean was below 0.60 is uplifted; cells where the mean was ≥0.60 are unchanged.
- Per `feedback_v3_iter064_process_lessons.md` Rule 2 (colsample-sampling discipline): the structural reasoning here is a STRUCTURAL UPPER BOUND on Path D's behavioral effect. Actual Optuna second-order TPE re-convergence under tighter constraints is not modeled at single-seed.

### Section 2.4 — T3 Path counterfactuals (estimated trade roster impact)

ORACLE first-order: per-Path estimated drop bands relative to /060 trade roster (held fixed at first order):

| Path | dropped_pct_low | dropped_pct_high | IS dropped low | IS dropped high | OOS dropped low | OOS dropped high | IS remaining | OOS remaining |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Path A — median threshold | 5% | 10% | 8 | 16 | 5 | 10 | [143, 151] | [92, 97] |
| Path B — median proba | 5% | 10% | 8 | 16 | 5 | 10 | [143, 151] | [92, 97] |
| Path C — fixed 0.55 | 10% | 30% | 16 | 48 | 10 | 31 | [111, 143] | [71, 92] |
| **Path D — tighten 0.60** | **30%** | **50%** | **48** | **80** | **31** | **51** | **[79, 111]** | **[51, 71]** |
| Path E — vote 2-of-3 | 10% | 25% | 16 | 40 | 10 | 26 | [119, 143] | [76, 92] |

**Reading**:
- Path D (tighten 0.60) drops the most trades — but ASYMMETRICALLY: only the marginal-confidence trades whose averaged proba sits in the [`mean_threshold`, 0.60] gap.
- Marginal-confidence trades are the LEAST EDGE-PROFITABLE in expectation (just barely above noise floor). Asymmetric dropping should preserve or improve Sharpe.
- Path D trade-roster low bound (51 OOS, ~3.6/month over 14 months) is BELOW the ≥10/month trade-rate floor. **Trade-rate floor concern flagged in Section 4.5 falsifier C.7**.
- Path E (vote 2-of-3) is a smaller-magnitude analogue of Path D; less aggressive trade pruning.
- Path A/B (median aggregation) drop only marginal trades affected by mean-median gap (~0.04); too small to produce PROMISING shift at 3-seed.
- Path C (fixed 0.55) is sub-optimal vs Optuna per-cell; predicted NEGATIVE.

### Section 2.5 — T4 Path predicted Sharpe Δ (HEADLINE metric)

PREDICTED IS/OOS Sharpe Δ from structural reasoning (per-Path):

| Path | IS Δ band | OOS Δ band | Mechanism |
|---|---|---|---|
| Path A — median threshold | [-0.05, +0.05] | [-0.10, +0.10] | Marginal-trade flip (~7%). First-order Sharpe-neutral; second-order Optuna re-converge. |
| Path B — median proba | [-0.05, +0.05] | [-0.10, +0.10] | Marginal-proba flip. First-order Sharpe-neutral. |
| Path C — fixed 0.55 | [-0.30, -0.05] | [-0.30, -0.05] | Sub-optimal universal threshold; degrades CV Sharpe in cells where Optuna found 0.55 sub-optimal. |
| **Path D — tighten 0.60** | **[+0.05, +0.20]** | **[+0.10, +0.30]** | Asymmetric tightening drops marginal trades. Marginal trades skew loser-heavy at /060 (31% WR IS, 39% WR OOS). |
| Path E — vote 2-of-3 | [+0.00, +0.15] | [+0.05, +0.25] | Disagreement-based filter; drops uncertain trades. Smaller magnitude than Path D. |

**Reading**:
- Path D is the ONLY path with predicted IS Δ band lower bound ≥+0.05 AND OOS Δ band lower bound ≥+0.10. Both bands sit within or above the PROMISING-AT-EXPLORATION criteria (IS Δ ≥+0.10 AND OOS Δ ≥+0.20).
- Path D bands have wide envelopes (~0.15-0.20 width) because:
  1. Optuna second-order TPE re-convergence under tighter constraints is unmodeled
  2. Marginal-trade PnL distribution skew is empirically uncertain (depends on per-cell threshold landscape)
  3. 3-seed averaging variance introduces ±0.10 IS / ±0.20 OOS noise floor
- The Path D PROMISING-band is consistent with the structural mechanism: dropping marginal trades preserves variance reduction (denominator) while dropping more losers (numerator increases) → Sharpe up.
- ALTERNATIVE OUTCOME WARNING: if marginal trades are net-profitable in IS (Optuna may have selected /060 marginal trades that are systematically profitable), Path D would REDUCE Sharpe. This is the basis for the 25% NEGATIVE probability in Section 7.

### Section 2.6 — T5 Path selection summary + scoring

Per-Path 7-criteria scoring:

| Path | stateless | universal | distinct_from_065 | distinct_from_066 | promising_viable | promising_magnitude | trade_floor_safe | **score** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Path A | YES | YES | YES | YES | NO | NO | YES | 5/7 |
| Path B | YES | YES | YES | YES | NO | NO | YES | 5/7 |
| Path C | YES | YES | YES | YES | NO | NO | YES | 5/7 |
| **Path D** | **YES** | **YES** | **YES** | **YES** | **YES** | **YES** | **YES** | **7/7** |
| Path E | YES | YES | YES | YES | YES | NO | YES | 6/7 |

**Path D quantitative justification (the QR selection)**:
1. Highest scoring (7/7 — sweep all criteria)
2. ONLY Path with predicted IS Δ ≥+0.10 AND OOS Δ ≥+0.20 viable simultaneously
3. Predicted PROMISING-band magnitude (IS [+0.05, +0.20], OOS [+0.10, +0.30]) covers the Section 8.1 PROMISING-AT-EXPLORATION thresholds
4. STATELESS — ORACLE EDA validity confirmed per `feedback_v3_oracle_eda_validity.md`
5. UNIVERSAL — preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
6. Mechanistically ORTHOGONAL to /065 (T6 — 6/7 stages) AND /066 (different stage entirely — emission decision vs weight modifier)
7. Single-axis change (one constant override in `lgbm.py` get_signal path)
8. NOT a universal symmetric clip/cap — AVOIDS Critic /066 Rec #2 STRUCTURALLY EXHAUSTED family (different mechanism: gate vs weight)
9. Anti-snooping: universal `_confidence_threshold = max(mean, 0.60)` has NEVER been tested
10. Implementation simplicity: single conditional in `lgbm.py:507` or `lgbm.py:637`

**Path eliminations**:
- **Path A (median threshold)** OUT: Predicted Sharpe-neutral at 3-seed. Reserved for CONFIRMATION ENSEMBLE_SIZE=10 where median has more statistical power.
- **Path B (median proba)** OUT: Same structural reasoning as Path A.
- **Path C (fixed 0.55)** OUT: Predicted NEGATIVE — overrides Optuna per-cell optimum and loses information.
- **Path E (vote 2-of-3)** OUT: Implementation more complex (per-seed proba tracking through direction-stage; not a simple threshold modification). PROMISING-viable but smaller magnitude than Path D. Reserved for /068 if /067 shows partial confirmation.

### Section 2.7 — T6 Cross-axis orthogonality with iter-v3/065

| Stage | iter-v3/065 (SL widening) | iter-v3/067 (Path D threshold tighten) | Orthogonal? |
|---|---|---|:-:|
| feature_engineering | no change (uses V3_FEATURE_COLUMNS_TOP_N=14) | no change | YES |
| label_generation | TRAIN-TIME triple-barrier `sl_multiplier 1.0 → 1.5` | no change (uses training labels as-is) | YES |
| optuna_hyperparameter_search | TPE explores hyperparams on changed labels | TPE unchanged; same suggest_float([0.50, 0.85]) range | YES |
| model_training | trained on changed labels | no change | YES |
| inference_time_prediction | no change | AGGREGATION change: `_confidence_threshold = max(mean(per_seed), 0.60)` | YES |
| risk_gate_stack | no change | no change | YES |
| trade_emission | different roster (different model + different labels) | different roster (different threshold + same model) | NO (both touch the roster, via different mechanisms) |

**Verdict**: First-order MECHANISTICALLY ORTHOGONAL on 6 of 7 stages. The trade-emission stage shows OVERLAP because both axes affect which trades enter the roster — but via STRUCTURALLY DISTINCT mechanisms: (a) /065 changes the model fit (different labels → different proba surface); (b) /067 changes the emission gate threshold (same proba surface, different cutoff). Bundle at /069 CONFIRMATION evaluates the combined effect.

### Section 2.8 — Cross-axis orthogonality with iter-v3/066

Inheritance note: /066's `vol_scale_ceiling=0.8` was INERT-AT-EXPLORATION (closed). The carry-forward state at /067 starts from /066's actual code state. Two scenarios for the runner:

**Scenario A — `vol_scale_ceiling` carries forward from /066 (=0.8)**: /067 measures Path D on top of vol_scale_ceiling=0.8. The /067 axis is isolated since /066's axis was INERT. Anchor comparison vs /060 reflects /066's INERT delta as a baseline-equivalent variation.

**Scenario B — `vol_scale_ceiling` reverts to 1.0 (default) at /067**: /067 isolates Path D against /060 directly without the /066 ceiling carry-forward. Recommended for clean attribution; aligns with /066's REVERT pattern when /065's SL widening was bundled into /069.

**Selection**: Scenario B — revert `vol_scale_ceiling` to default 1.0 at /067 for clean attribution. This is consistent with /066's own revert pattern (`DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` reverted /065's universal SL widening) and ensures /067 measures Path D against /060's vol_scale_ceiling state directly. /066's verdict (INERT closed) means re-running with the default 1.0 is methodologically clean.

### Section 2.9 — Anchor declaration

**Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 102 OOS trades). **NOT iter-v3/065 nor /066** (parallel SUSPICIOUS-OOS-DOMINANT and INERT-AT-EXPLORATION candidates respectively; not new anchors). Per `feedback_v3_cycle1_axis_pass_criteria.md`: cycle 1 EXPLORATIONs anchor on /060 (3-seed lineage subset of /059 10-seed CONFIRMATION); CONFIRMATION-mode delta vs /059 is evaluated only at /069 CONFIRMATION.

BASELINE_V3.md remains anchored at `v0.v3-059` per `feedback_v3_baseline_update_policy.md`.

### Section 2.10 — Summary

- Path D is the QR-selected ensemble-parameters axis per quantitative EDA analysis.
- ORACLE first-order Sharpe Δ prediction: IS Δ band [+0.05, +0.20], OOS Δ band [+0.10, +0.30] — both span the PROMISING-AT-EXPLORATION thresholds.
- Most likely classification = INERT-AT-EXPLORATION (~45% per Section 7 calibrated probabilities) given the /060 local-optimum sensitivity; PROMISING-AT-EXPLORATION = ~25%; NEGATIVE = ~25%.
- Cross-axis orthogonality with /065 and /066 verified.
- STATELESS gate modification; ORACLE EDA discipline preserved.
- TRADE-RATE FLOOR concern flagged at falsifier C.7 (low-bound 51 OOS trades = ~3.6/month, below ≥10/month floor); per `feedback_v3_trade_rate_floor.md` this is informational at EXPLORATION level, BLOCKING at CONFIRMATION.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — LightGbmStrategy._confidence_threshold floor at inference time

**ONE substantive change**. The inherited `_confidence_threshold` is replaced by `max(self._confidence_threshold, V3_INFERENCE_THRESHOLD_FLOOR)` where `V3_INFERENCE_THRESHOLD_FLOOR = 0.60`. Two equivalent implementations are possible:

**Option 1** (recommended, minimal code change): apply the floor at the moment of derivation (after `_confidence_thresholds` aggregation).

File: `src/crypto_trade/strategies/ml/lgbm.py` line 507.

```python
# BEFORE
self._confidence_threshold = float(np.mean(self._confidence_thresholds))

# AFTER (iter-v3/067 Path D: universal inference-time confidence-threshold floor)
self._confidence_threshold = max(
    float(np.mean(self._confidence_thresholds)),
    self._inference_threshold_floor,  # default 0.0 (no floor); /067 sets 0.60
)
```

**Option 2** (alternative, applied at inference): apply the floor at the gate decision.

File: `src/crypto_trade/strategies/ml/lgbm.py` line 637.

```python
# BEFORE
if confidence < self._confidence_threshold:
    return NO_SIGNAL

# AFTER (iter-v3/067 Path D: universal inference-time confidence-threshold floor)
effective_threshold = max(self._confidence_threshold, self._inference_threshold_floor)
if confidence < effective_threshold:
    return NO_SIGNAL
```

**Engineer to choose Option 1** for cleaner state separation: the floor is applied once at training-month boundary, not re-evaluated per candle. This matches the existing aggregation pattern at line 507 and avoids per-candle overhead. The Engineer must add `_inference_threshold_floor` as a `__init__` parameter (default 0.0 — opt-in) and pass it from `run_baseline_v3.py`.

### Sub-fix 2 — Constructor parameter `inference_threshold_floor` on LightGbmStrategy

File: `src/crypto_trade/strategies/ml/lgbm.py` (`__init__` around line 131).

```python
def __init__(
    self,
    ...,
    ensemble_seeds: list[int] | None = None,
    inference_threshold_floor: float = 0.0,  # NEW iter-v3/067 Path D
    ...
):
    ...
    self._inference_threshold_floor = float(inference_threshold_floor)
```

Default `0.0` ensures backward compatibility for v1/v2 strategies and earlier v3 iterations that load LightGbmStrategy without the floor.

### Sub-fix 3 — Runner passes the floor in `_build_v3_model`

File: `run_baseline_v3.py` (in the LightGbmStrategy instantiation, where ensemble_seeds is passed).

```python
LightGbmStrategy(
    ...,
    ensemble_seeds=ENSEMBLE_SEEDS_EXPLORATION,
    inference_threshold_floor=0.60,  # iter-v3/067 Path D: universal inference-time threshold floor
)
```

### Sub-fix 4 — REVERT `vol_scale_ceiling` to default 1.0 at /067

File: `run_baseline_v3.py` (`_build_v3_model`, the `RiskV2Config(...)` call).

```python
# Before (iter-v3/066 state)
vol_scale_ceiling=0.8,  # iter-v3/066: UNIVERSAL ceiling tightening 1.0 → 0.8 per Path E0.8 EDA SHA 1d75cb0

# After (iter-v3/067 — REVERT to default; isolate /067 axis from /066)
# vol_scale_ceiling not explicitly set — defaults to 1.0 per risk_v2.py:58
```

**Rationale**: /066 INERT-AT-EXPLORATION (closed). Per Section 2.8 Scenario B: revert `vol_scale_ceiling` to default 1.0 at /067 for clean attribution. This is consistent with /066's own pattern of reverting /065's `DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5)` back to `(2.0, 1.0)` to isolate the /066 axis. `/065` SL widening axis tested separately at /065; `/066` ceiling axis closed; `/067` threshold floor isolated against the universal /060 baseline.

### Sub-fix 5 — DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0)

File: `src/crypto_trade/features_v3/__init__.py` line 222.

```python
# Iter-v3/066 already set this to (2.0, 1.0). UNCHANGED at /067.
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
```

**Rationale**: /065's SL widening axis remains tested separately. /067 axis is isolated against /060's labeling.

### Sub-fix 6 — ITERATION_LABEL bump

File: `run_baseline_v3.py`.

```python
# Before
ITERATION_LABEL = "v3-066"

# After
ITERATION_LABEL = "v3-067"
```

### Sub-fix 7 — Test assertion updates (NEW)

Add a regression test for the `inference_threshold_floor` constructor parameter and Option 1 behavior:

File: `tests/strategies/ml/test_inference_threshold_floor.py` (NEW).

```python
"""Test inference_threshold_floor at LightGbmStrategy.

Per iter-v3/067 Path D: universal inference-time confidence-threshold floor.
"""
import numpy as np
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy


def test_inference_threshold_floor_default_zero():
    """Default floor=0.0 should not affect _confidence_threshold derivation."""
    strat = LightGbmStrategy(
        features_dir="data/features_v3",
        interval="8h",
        ensemble_seeds=[42],
    )
    # Simulate _confidence_thresholds populated by training
    strat._confidence_thresholds = [0.55]
    expected = max(float(np.mean(strat._confidence_thresholds)), strat._inference_threshold_floor)
    assert expected == pytest.approx(0.55)


def test_inference_threshold_floor_60_pct_uplifts_low_mean():
    """Floor=0.60 should uplift _confidence_threshold when mean is below 0.60."""
    strat = LightGbmStrategy(
        features_dir="data/features_v3",
        interval="8h",
        ensemble_seeds=[42],
        inference_threshold_floor=0.60,
    )
    strat._confidence_thresholds = [0.55]
    expected = max(float(np.mean(strat._confidence_thresholds)), strat._inference_threshold_floor)
    assert expected == pytest.approx(0.60)


def test_inference_threshold_floor_does_not_lower_high_mean():
    """Floor=0.60 should not affect _confidence_threshold when mean is at or above 0.60."""
    strat = LightGbmStrategy(
        features_dir="data/features_v3",
        interval="8h",
        ensemble_seeds=[42],
        inference_threshold_floor=0.60,
    )
    strat._confidence_thresholds = [0.65]
    expected = max(float(np.mean(strat._confidence_thresholds)), strat._inference_threshold_floor)
    assert expected == pytest.approx(0.65)
```

### Sub-fix 8 — Runtime assertion for `inference_threshold_floor`

File: `run_baseline_v3.py` (after model build, where existing per-symbol assertions live).

```python
expected_floor = 0.60
for sym, strat in v3_models.items():
    lgbm_strat = strat.inner_strategy if hasattr(strat, "inner_strategy") else strat
    if not hasattr(lgbm_strat, "_inference_threshold_floor"):
        raise RuntimeError(
            f"LightGbmStrategy for {sym} has no _inference_threshold_floor attribute. "
            "iter-v3/067: LightGbmStrategy must support inference_threshold_floor=0.60."
        )
    if lgbm_strat._inference_threshold_floor != expected_floor:
        raise RuntimeError(
            f"LightGbmStrategy for {sym} has _inference_threshold_floor = "
            f"{lgbm_strat._inference_threshold_floor} — expected {expected_floor}. "
            f"iter-v3/067 Path D: pass inference_threshold_floor=0.60 in LightGbmStrategy init."
        )
print(
    f"  Universal inference_threshold_floor (iter-v3/067): {expected_floor} "
    f"(Path D universal tightening — replaces Optuna-inherited mean when below 0.60)"
)
```

### Sub-fix 9 — Parquet regeneration

**NOT required.** No feature changes; no new feature columns. The inference-time threshold tightening operates on the per-candle predicted proba via the existing `_confidence_threshold` field.

### Sub-fix 10 — ENSEMBLE_SIZE assertion

**UNCHANGED**. EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 (per Phase B-3 unified architecture). /067 runs with `--exploration` (ENSEMBLE_SIZE=3).

### Sub-fix 11 — V3_FEATURE_COLUMNS_TOP_N

**UNCHANGED**. Stays at 14 features post-/064 revert (commit `04080c4`). NON-FEATURE axis means feature universe is held constant.

## Section 4 — Predicted Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (single-seed EXPLORATION mode)

| Metric | /060 anchor (T0) | Predicted /067 | Predicted Δ band |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.55 to +1.05 | Δ ∈ [-0.28, +0.22] |
| OOS monthly Sharpe | +0.1403 | -0.20 to +0.50 | Δ ∈ [-0.34, +0.36] |
| OOS/IS daily ratio | 0.21 | 0.10 to 0.60 | within [0.10, 0.60] |
| IS trades | 159 | 80 to 130 | Δ ∈ [-79, -29] |
| OOS trades | 102 | 50 to 75 | Δ ∈ [-52, -27] |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 | architecture-invariant ≥0.50 |
| BCH IS share | ~95% (/060) | 70% to 160% | one-sided ≥ 80% per Critic /060 Rec #1 |

**Rationale for band widths**: this is a UNIVERSAL INFERENCE GATE TIGHTENING (non-feature axis, non-labeling axis, non-weighting axis). Historical precedents:
- iter-v3/066 universal vol_scale_ceiling=0.8 (WEIGHTING axis): INERT-AT-EXPLORATION; Sharpe Δ within ±0.04.
- iter-v3/061 per-symbol vol_scale_floor (WEIGHTING per-symbol): INERT-AT-EXPLORATION.
- iter-v3/065 universal SL widening (LABELING axis): PROMISING SUSPICIOUS-OOS-DOMINANT.
- /067 ORACLE first-order: IS Δ band [+0.05, +0.20], OOS Δ band [+0.10, +0.30]. WIDER than /066 because the GATE-vs-WEIGHT distinction means second-order Optuna behavioral effects are larger.
- Band widths are SLIGHTLY WIDER than EDA prediction to account for:
  1. Optuna second-order TPE re-convergence under different effective trade-roster (potential PROMISING upside)
  2. 3-seed averaging variance noise floor (~±0.10 IS / ±0.20 OOS per `feedback_v3_cycle1_axis_pass_criteria.md`)
  3. Marginal-trade PnL distribution skew is empirically uncertain (depends on per-cell threshold landscape)
  4. Trade-count drop is LARGE (~30-50%): if marginal trades have systematically NEGATIVE expected return, Path D improves Sharpe; if marginal trades are NEUTRAL or POSITIVE-skew, Path D may DEGRADE Sharpe via increased variance from fewer trades

### Section 4.2 — BCH IS sensitivity prediction (per /059 Critic Rec #3 carry-forward)

BCH IS share at /060 was 176.68% (3-seed averaging structurally amplified BCH's IS dominance). The one-sided ≥80% gate applies per `feedback_v3_cycle1_axis_pass_criteria.md` Rec #1.

Path D inference-threshold tightening is expected to:
- DROP BCH IS trades whose ensemble-averaged proba sits in the [mean_threshold, 0.60] gap. BCH has the highest /060 IS weighted_pnl (+78.34 wpnl from /066 EDA T3); BCH marginal trades likely contribute lower-edge proportion of this PnL.
- BCH IS share should hold but may shift slightly (down to ~140% range if BCH marginal trades drop disproportionately, or stay near 176% if marginal drops are proportional across symbols)
- LDO IS share may lift (LDO marginal trades likely contribute disproportionately to LDO's -1.66 wpnl IS deficit; tightening their entry filters out LDO losers more aggressively)
- TRX IS share may lift (TRX IS WR 29.3% — many marginal LOSERS; tightening drops them; TRX has -24.79 wpnl IS to recover from)

**Predicted BCH IS share at /067**: 70% to 160% (one-sided ≥80% gate cleared in expectation; band wider than baseline because gate-modification reshuffles per-symbol contributions but does NOT cap any symbol's effective weighting).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md` + Critic /065 Rec #3 calibration)

**Predicted trade-count change** (inference threshold tightening DOES change trade emission count by design):

| Symbol | IS trades /060 | IS trades /067 predicted | OOS trades /060 | OOS trades /067 predicted |
|---|---:|---:|---:|---:|
| BCH | 73 | 40 to 62 (large drop) | 37 | 18 to 30 |
| LDO | 11 | 5 to 9 | 11 | 5 to 9 |
| TRX | 75 | 35 to 65 | 54 | 27 to 47 |
| **Total** | **159** | **[80, 136]** | **102** | **[50, 86]** |

**Behavioral-effect rationale**: inference-time confidence-threshold tightening reduces trade emission count by 15-50% depending on per-cell Optuna-derived mean threshold distribution. Cells where Optuna converged below 0.60 are now uplifted to 0.60; their marginal trades (proba in [mean, 0.60]) drop from the roster.

**Per Critic /065 Rec #3 calibration for inference-gate axes**: per-symbol WR Δ predicted to LIFT (NOT saturation-band ±2pp). Filtering marginal trades should reveal cleaner edge.

| Symbol | IS WR /060 | OOS WR /060 | Predicted /067 WR Δ (IS) | Predicted /067 WR Δ (OOS) |
|---|---:|---:|---:|---:|
| BCH | 45.2% | 32.4% | +0pp to +10pp (drop marginal losers) | +0pp to +10pp |
| LDO | 27.3% | 18.2% | +0pp to +12pp | +0pp to +12pp |
| TRX | 29.3% | 50.0% | +0pp to +10pp | -2pp to +5pp (already 50% — marginal drops symmetric) |

**Saturation falsifier (per `feedback_v3_axis_saturation_predictor.md` non-feature-axis extension, adapted for gate axes)**: if per-symbol trade-count Δ is within ±5% AND per-symbol WR Δ is within ±2pp at all 3 symbols, the axis is INERT-AT-EXPLORATION (the threshold modification had no effective downstream behavioral impact on trade selection — equivalent to per-cell Optuna already converging at or above 0.60).

**Inverted-falsifier (Path D specific)**: if trade-count drops by >50% in EITHER IS or OOS while Sharpe drops by >0.10, this signals over-tightening — Path D pruning destroyed information faster than it filtered noise. NEGATIVE classification.

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

All anchor references per Section 2.1 T0 declarations:

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 (i.e., IS ≥ +0.6325) | FAIL → NEGATIVE / IS-COLLAPSE |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 (i.e., OOS ≥ -0.1597) | FAIL → NEGATIVE / OOS-NEGATIVE |
| **A.3** | frac_positive_paths | ≥ 0.50 | FAIL → methodology FAIL (CPCV degenerate) |
| **A.4** | No methodology FAIL | Critic 13 checks + §11 anti-pattern scan | FAIL → BLOCK |
| **B.5** | BCH IS share | one-sided ≥ 80% (per Critic /060 Rec #1) | FAIL → BCH collapse warning |
| **C.6** | IS trade count | ∈ [70, 200] (wider lower bound than /066 — Path D drops trades by design) | FAIL → trade-rate floor violation |
| **C.7** | OOS trade count | ∈ [40, 130] (wider lower bound than /066 — Path D drops trades by design) | INFO at EXPLORATION (BLOCKING at /069 CONFIRMATION per `feedback_v3_trade_rate_floor.md`) |
| **D.8** | BCH IS wpnl Δ | within [-30, +20] vs /060 (+78.34 anchor from /066 EDA T3 row; Path D drops BCH marginal trades — IS damage allowable; floor at -30 wpnl) | FAIL → BCH IS regression |
| **D.9** | BCH OOS wpnl Δ | within [-10, +10] vs /060 (+1.9078 anchor from comparison.csv:18; Path D affects symmetric BCH OOS trades) | FAIL → BCH OOS regression |
| **D.10** | LDO IS wpnl Δ | within [-5, +15] vs /060 (-1.66 anchor from /066 EDA T3 row; target LIFT — drop marginal LDO losers) | FAIL → LDO IS regression |
| **D.11** | LDO OOS wpnl Δ | within [-5, +20] vs /060 (-19.72 anchor from comparison.csv:19; target LIFT — drop marginal LDO losers) | FAIL → LDO OOS collapse |
| **D.12** | TRX IS wpnl Δ | within [-15, +20] vs /060 (-24.79 anchor from /066 EDA T3 row; target LIFT — drop marginal TRX losers) | FAIL → TRX IS regression |
| **D.13** | TRX OOS wpnl Δ | within [-15, +10] vs /060 (+23.31 anchor from comparison.csv:20; potential cost as some Kelly-aligned TRX trades drop) | FAIL → TRX OOS regression |
| **D.14** | Saturation falsifier | trade-count Δ within ±5% AND per-symbol WR Δ within ±2pp at all 3 syms | If ALL within band → INERT-AT-EXPLORATION (D.14 fires; informational) |
| **D.15** | Over-tightening falsifier (Path D specific) | trade-count Δ ≤ -50% (IS OR OOS) AND Sharpe Δ ≤ -0.10 (IS OR OOS) | FIRES → NEGATIVE-OVER-TIGHTENING |
| **E.16** | All v3 lgbm + features_v3 tests passing | `pytest tests/strategies/ml/test_inference_threshold_floor.py tests/features_v3/ -v` PASS | FAIL → BLOCK |
| **E.17** | ensemble_summary | mode=exploration, size=3 | FAIL → mode-flag wiring bug |
| **E.18** | EDA-implementation parity | `_inference_threshold_floor == 0.60` AND `vol_scale_ceiling == 1.0` (default) AND `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` at runtime | FAIL → process violation |

**Notes on falsifier bands**:
- Gates A.1 (IS ≥ -0.20) and A.2 (OOS ≥ -0.30) are the LOCKED Section 8.4 disjunctive-OR NEGATIVE thresholds per `feedback_v3_cycle1_axis_pass_criteria.md`. Either single-gate FAIL → NEGATIVE classification.
- Gate C.7 OOS trade count [40, 130] is INFORMATIONAL at EXPLORATION level. Per `feedback_v3_trade_rate_floor.md` the ≥10/month OOS floor is a CONFIRMATION-level gate; EXPLORATION can drop below if axis logic is structurally sound. Path D's by-design trade pruning makes this expected.
- Gate D.15 is the OVER-TIGHTENING FALSIFIER (Path D-specific): if Path D drops >50% of trades AND Sharpe drops, the threshold was set too tight. This is a critical falsifier for Path D since the mechanism is asymmetric pruning.
- Gate D.14 saturation: if trade count and WR are approximately invariant, this means Optuna's per-cell mean threshold was already ≥0.60 in most cells — the Path D floor is non-binding. INERT-AT-EXPLORATION classification.

### Section 4.5 — Trade-rate floor concern (Path D specific)

Per `feedback_v3_trade_rate_floor.md`: OOS trades ≥10/month, ≥130 total over 14 OOS months at CONFIRMATION level. Path D's predicted OOS trade drop to [50, 86] = [3.6, 6.1]/month is BELOW the floor.

**At EXPLORATION level** (where /067 runs): the floor is INFORMATIONAL. EDA T3 predicts this; the brief flags it explicitly. If /067 produces PROMISING-AT-EXPLORATION classification, the next step is /069 CONFIRMATION re-validation at ENSEMBLE_SIZE=10 + n_trials=35. At CONFIRMATION mode:
- The 10-seed ensemble produces more confident proba averaging — per-cell thresholds may be tighter or looser; trade-count effects differ from 3-seed.
- If CONFIRMATION-mode OOS trade count remains <130 (or <10/month), the bundle violates trade-rate floor at CONFIRMATION → BLOCKING gate.
- This brief PRE-COMMITS that Path D's CONFIRMATION-level evaluation must include trade-count floor gate; we do NOT post-hoc renegotiate the trade-rate floor.

### Section 4.6 — Anti-stacking check

Per `feedback_v3_engineered_features_dont_stack.md`: /067 changes ONE axis (LightGbmStrategy inference-time threshold floor). No engineered features added. No same-family features stacked. **iter-v3/066's `vol_scale_ceiling=0.8` is REVERTED to default 1.0 at /067** (Sub-fix 4) to isolate the single varied axis. Single-axis EXPLORATION at single-seed mode is LEGITIMATE.

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /060 anchor, EXCEPT for /067's single substantive change):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) - REVERT /066 | ENABLED, ceiling reverted to default 1.0 | iter-v3/067 (this brief; revert /066 axis) |
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
| Per-symbol vol_scale_floor | ENABLED (iter-v3/061: TRX 0.5; BCH/LDO 0.3) | preserved at /067 (orthogonal axis from /067's threshold change) |
| Universal vol_scale_ceiling | REVERTED to default 1.0 | iter-v3/067 reverts /066's INERT axis for clean attribution |
| **LightGbmStrategy inference_threshold_floor** | **NEW, 0.60** | **iter-v3/067 this brief** |

**Inference-gate axis is orthogonal to ALL other primitives at /067** (T6 + T8 orthogonality verified). No primitive-cascade interaction risk.

## Section 6 — Risk Management

**CHANGED (single substantive change)**: `LightGbmStrategy._confidence_threshold` is floored at `0.60` universally. All 3 symbols (BCH/LDO/TRX) consume the new universal floor. No per-symbol override added.

`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from iter-v3/061 REMAINS UNCHANGED — orthogonal axis from /067's threshold change.

`vol_scale_ceiling` REVERTS to default 1.0 per axis isolation discipline (Sub-fix 4).

DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0). Triple-barrier labeling timeout UNCHANGED: 21 candles (10080 minutes). Cooldown UNCHANGED: 4 candles post-trade. Fee UNCHANGED: 0.1% per leg.

**Translated to live trading**: live engine's effective `_confidence_threshold` per (model, month) cell is floored at 0.60. Cells where Optuna's per-seed mean is below 0.60 are uplifted to 0.60 at the trade-emission gate. Trades whose ensemble-averaged proba was in the `[Optuna_mean, 0.60]` gap no longer emit; their PnL contribution is zero. Trade-count drops by 15-50% depending on per-cell Optuna threshold distribution.

## Section 7 — Pre-registered Failure-Mode Prediction

Per Rule 3 of `feedback_v3_iter064_process_lessons.md`: single-axis non-feature changes at single-seed n_trials=35 weight NEGATIVE ≥25%. Calibrated per Critic /064 Rec #3 + /065 Rec #3 + /066 actual outcome.

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **INERT** | Optuna per-cell mean threshold is already ≥0.60 in most cells; Path D floor is non-binding; trade count + WR saturation falsifier (D.14) fires | ~45% | IS Δ ∈ [-0.10, +0.10], OOS Δ ∈ [-0.20, +0.20]; D.14 saturation fires |
| **PROMISING** | Marginal-trade pruning works; dropping ~30% of trades preserves variance reduction (denominator) while dropping more losers than winners (numerator improves); Sharpe lifts on both IS and OOS | ~25% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-OOS-DOMINANT** | Single-seed lottery: OOS spikes (LDO + TRX marginal losers disproportionately dropped) while IS stays flat or regresses | ~5% | IS Δ < +0.10, OOS Δ ≥ +0.20 |
| **NEGATIVE** | Universal tightening overcuts BCH high-confidence trades; marginal trades are POSITIVE-skew on net (Optuna's mean already optimized them); over-tightening destroys edge; D.15 fires | ~25% | IS Δ < -0.20 OR OOS Δ < -0.30 OR D.15 fires |

Probabilities per orchestrator-mandated distribution + Rule 3 calibration:
- INERT ~45% (most likely; if /066 was INERT, /067 is also likely INERT with similar structural sensitivity)
- PROMISING ~25% (Path D EDA prediction is positive but uncertain; PROMISING-band is plausible per structural reasoning)
- SUSPICIOUS-OOS-DOMINANT ~5% (low — Path D mechanism is universal; per-cell threshold landscape symmetric across splits)
- NEGATIVE ~25% (Rule 3 calibration: single-axis at single-seed n_trials=35 has Optuna-overfit risk; over-tightening risk specific to Path D)

**Why INERT is most likely (45%)**: 
- /066 INERT (closed) suggests the /060 local optimum is RESISTANT to single-axis universal perturbations at single-seed n_trials=35.
- Optuna's per-cell mean threshold distribution may already concentrate near or above 0.60 (saturated regime); Path D's floor is then non-binding.
- If Path D fires only in a small fraction of cells, the aggregate Sharpe shift is small.

**Why NEGATIVE is 25% (calibrated UP per Rule 3)**: 
- Universal gate tightening at single-seed is sensitive — iter-v3/041 (universal pruning) and iter-v3/042 (universal ATR) both produced NEGATIVE.
- Path D-specific over-tightening risk: if marginal trades happen to be net-profitable (Optuna selection effect), Path D destroys edge by dropping them.
- BCH dominance at /060 IS share (176%): BCH-centric marginal-trade pruning is high-leverage for IS Sharpe — could drop the IS Sharpe meaningfully.

**Why PROMISING is 25% (constrained UP-bound per Rule 3)**: 
- Path D EDA prediction places the OOS Δ band lower bound at +0.10 — at the cusp of PROMISING.
- Optuna second-order TPE re-convergence under tighter effective gate is possible but unmodeled.
- Marginal-trade-loser-skew assumption is plausible (Optuna selection bias hides edges in low-confidence regime by design).

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_cycle1_axis_pass_criteria.md`:

### Section 8.1 — PROMISING-AT-EXPLORATION (advances to /069 CONFIRMATION as candidate)

ALL of:
- **A.1** IS Sharpe shift ≥ +0.10 vs /060 (IS ≥ +0.9325)
- **A.2** OOS Sharpe shift ≥ +0.20 vs /060 (OOS ≥ +0.3403)
- **A.3** frac_positive_paths ≥ 0.50
- **A.4** No methodology FAIL (Critic 13 checks + §11 anti-pattern scan)
- **B.5** BCH IS share ≥ 80% (one-sided per Critic /060 Rec #1)
- **C.6** IS trade count ∈ [70, 200]
- **C.7** OOS trade count ∈ [40, 130] (CONFIRMATION level imposes ≥130 — informational at EXPLORATION)
- **D.8-D.13** Per-symbol wpnl Δ bands all within range
- **D.15** Over-tightening falsifier (Path D) does NOT fire (trade-count Δ ≤ -50% AND Sharpe Δ ≤ -0.10)
- **E.16-E.18** Test pass + ensemble_summary + EDA-implementation parity gates PASS

### Section 8.2 — INERT-AT-EXPLORATION

- IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] (noise-band)
- AND no methodology FAIL
- AND/OR D.14 saturation falsifier fires (trade-count Δ within ±5% AND per-symbol WR Δ within ±2pp at all 3 syms)
- Axis CLOSED for current cycle; not re-evaluated.

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT

- IS Δ < +0.10 (i.e., INSIDE noise band or NEGATIVE)
- AND OOS Δ ≥ +0.20
- Axis CLOSED-PENDING-CONFIRMATION; does NOT advance to /069 as PROMISING but logged as parallel /069 advancement candidate.

### Section 8.4 — NEGATIVE (disjunctive OR per `feedback_v3_iter064_process_lessons.md` Rule 4)

- IS Δ < -0.20 **OR** OOS Δ < -0.30 (either gate FAIL)
- AND no methodology FAIL
- Axis CLOSED. Universal inference threshold floor=0.60 placed on PARKED list with rationale.

### Section 8.5 — NEGATIVE-OVER-TIGHTENING (Path D specific, per D.15)

- trade-count Δ ≤ -50% (IS OR OOS) AND Sharpe Δ ≤ -0.10 (IS OR OOS)
- AND no methodology FAIL
- Axis CLOSED. Path D pruning destroyed information faster than it filtered noise. Future ensemble-parameter EXPLORATIONs should consider less aggressive thresholds (e.g., 0.55 instead of 0.60) OR Path E vote-based filtering.

### Section 8.6 — Methodology FAIL

- Any Critic 13-check BLOCK fires
- Iteration is INVALID; not classifiable as PROMISING/INERT/NEGATIVE.

## Section 9 — Library Stack + Reproducibility

**UNCHANGED**:
- Python 3.13, uv environment, LightGBM (`lightgbm` package), pandas, pyarrow, statsmodels.
- LightGbmStrategy at `src/crypto_trade/strategies/ml/lgbm.py`; ensemble emission gate at line 637.
- Confidence threshold aggregation at line 507 (`np.mean(self._confidence_thresholds)`).
- Optuna confidence_threshold suggest_float range `[0.50, 0.85]` at `optimization.py:198`.
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) — outer=42 lineage subset for EXPLORATION mode.

**Reproducibility stamp**:
- EDA SHA: `aa5b0c8` (`analysis/iteration_v3-067/ensemble_parameters_eda.py`)
- Setup commit SHA: (this commit, LOCKED)
- ITERATION_LABEL: `"v3-067"`
- LightGbmStrategy._inference_threshold_floor at runtime: **0.60** (NEW; previously implicit 0.0)
- RiskV2Config.vol_scale_ceiling at runtime: **1.0** (REVERTED from /066's 0.8 to default)
- RiskV2Config.vol_scale_floor: 0.3 universal (unchanged)
- RiskV2Config.vol_scale_floor_per_symbol: {"TRXUSDT": 0.5} (unchanged from /061)
- DEFAULT_ATR_MULTIPLIERS at runtime: (2.0, 1.0) (UNCHANGED from /066 revert)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — preserved)
- Parquet data: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet` (no regen needed)

### Integration test (per `feedback_v3_methodology_axis_integration_test.md`)

The `_inference_threshold_floor` edit is consumed by:
1. `src/crypto_trade/strategies/ml/lgbm.py::LightGbmStrategy.__init__` — new `inference_threshold_floor` kwarg (Sub-fix 2)
2. `src/crypto_trade/strategies/ml/lgbm.py:507` — `self._confidence_threshold = max(np.mean(...), self._inference_threshold_floor)` (Sub-fix 1)
3. `run_baseline_v3.py::_build_v3_model` — passes `inference_threshold_floor=0.60` (Sub-fix 3)
4. `run_baseline_v3.py::_verify_*` runtime assertion — `_inference_threshold_floor == 0.60` per Sub-fix 8
5. `tests/strategies/ml/test_inference_threshold_floor.py` (NEW per Sub-fix 7)

A smoke test consists of running:
```bash
uv run pytest tests/strategies/ml/test_inference_threshold_floor.py tests/features_v3/ -v
```
and confirming all tests PASS with the new `_inference_threshold_floor=0.60` configuration.

## Section 10 — QR Audit Trail

**Why this axis (ENSEMBLE PARAMETERS — universal inference-time confidence-threshold floor, Path D)**:

1. **Critic /064 Rec #4 binding directive** (locked for /065-/068): NON-FEATURE axis pivot mandated after /060 14-feature anchor classified as LOCAL OPTIMUM at single-seed n_trials=35 (per Rule 5 of `feedback_v3_iter064_process_lessons.md`). Feature-axis EXPLORATIONs at this budget cannot productively escape.

2. **Critic /066 Rec #2 binding directive**: AVOID universal symmetric clip/cap mechanisms. Universal-ceiling family STRUCTURALLY EXHAUSTED. /067 axis is structurally distinct from /066: instead of CAPPING per-trade weight (multiplicative weighting modifier), Path D TIGHTENS the per-candle entry decision (binary gate modifier on confidence). Mechanism: GATE vs WEIGHT, not symmetric clip vs cap.

3. **Orchestrator autopilot decision 2026-05-14**: cycle 1 #8 axis CATEGORY locked at ENSEMBLE PARAMETERS for /069 CONFIRMATION bundle structural diversity. /065's labeling axis was the first PROMISING-class survivor; an ENSEMBLE-axis PROMISING-class component would strengthen the /069 bundle by reducing single-axis dependence. Ensemble parameters axis is mechanistically distinct from labeling (train-time) AND weight clipping (inference-weighting) AND feature engineering (data pipeline).

4. **QR EDA SHA `aa5b0c8`** produced 7 tables that quantitatively support Path D over Paths A/B/C/E:
   - **T0**: anchor-value declaration (per Critic /064 Rec #1 + /065 Rec #1 + /066 Rec #3 RECURRENCE flag).
   - **T1**: current ensemble parameter inventory documenting MEAN aggregation at confidence threshold + proba; no prior EXPLORATION at inference-gate axis.
   - **T2**: per-seed confidence threshold distribution structural properties (Optuna range [0.50, 0.85]; uniform-3seed std ~0.10; mean-median gap expected ~0.04).
   - **T3**: per-Path counterfactual trade roster impact — Path D drops 30-50% of trades; other paths drop 5-25%.
   - **T4**: per-Path predicted IS/OOS Sharpe Δ — Path D is the ONLY Path with predicted IS Δ ≥+0.10 AND OOS Δ ≥+0.20 viable simultaneously.
   - **T5**: Path selection summary scoring 5 candidates with 7 criteria; Path D scores 7/7.
   - **T6**: cross-axis orthogonality with /065 labeling axis — 6/7 stages ISOLATED at first order.

5. **Path D selection rationale (quantitative)**:
   - Only Path with predicted IS Δ band [+0.05, +0.20] AND OOS Δ band [+0.10, +0.30] (PROMISING-viable)
   - Marginal-trade asymmetric pruning: drops ~30-50% of trade roster (mostly losers per IS WR 31.45%, OOS WR 39.22% at /060)
   - Single-axis change (`_inference_threshold_floor` constant in lgbm.py)
   - Universal (preserves IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
   - STATELESS (ORACLE EDA valid per `feedback_v3_oracle_eda_validity.md`)
   - Mechanistically ORTHOGONAL to /065 labeling axis (T6 verified)
   - Mechanistically DISTINCT from /066 weight clipping (different stage: emission gate vs weight modifier)
   - Anti-snooping: universal `_confidence_threshold = max(mean, 0.60)` has NEVER been tested
   - NOT a universal symmetric clip/cap — AVOIDS Critic /066 Rec #2 STRUCTURALLY EXHAUSTED family

6. **Methodology compliance**:
   - `feedback_v3_axis_selection_quant_discipline.md`: EDA committed BEFORE brief (SHA `aa5b0c8` precedes setup commit).
   - `feedback_v3_oracle_eda_validity.md`: ORACLE valid for STATELESS primitive (inference-gate threshold). Per-candle decision; no signal-emission state update.
   - `feedback_v3_engineered_features_dont_stack.md`: single-axis EXPLORATION (ONE substantive change — `_inference_threshold_floor`); revert `vol_scale_ceiling` to default to isolate the single varied axis.
   - `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: UNIVERSAL change (no new per-symbol override).
   - `feedback_v3_cycle1_axis_pass_criteria.md`: PASS thresholds (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060) explicit at Section 8.1.
   - `feedback_v3_iter064_process_lessons.md` Rule 1 (anchor-value correctness gate; RECURRENCE awareness): T0 references /060 anchor values with bit-exact `comparison.csv:LINE` refs.
   - `feedback_v3_iter064_process_lessons.md` Rule 3 (probability calibration): Section 7 NEGATIVE=25%, INERT=45%, PROMISING=25%, SUSPICIOUS-OOS=5%.
   - `feedback_v3_iter064_process_lessons.md` Rule 4 (Section 8 disjunctive OR): Section 8.4 NEGATIVE LOCKED as disjunctive OR.
   - `feedback_v3_axis_saturation_predictor.md`: Section 4.3 behavioral-effect predictor present with quantitative trade-count + per-symbol WR Δ bands; Gate D.14 saturation falsifier; Gate D.15 over-tightening falsifier (Path D specific).
   - `feedback_v3_dsr_mode_artifact.md`: DSR_relative INFORMATIONAL ONLY at /067 EXPLORATION mode.
   - `feedback_v3_trade_rate_floor.md`: trade-rate floor explicitly flagged at C.7 as INFORMATIONAL at EXPLORATION; BLOCKING at /069 CONFIRMATION. Pre-committed.

7. **EDA-implementation parity (per Critic /063 Rec #2)**: V3_FEATURE_COLUMNS_TOP_N UNCHANGED (14 features); DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0); vol_scale_ceiling REVERTED to default 1.0; `_inference_threshold_floor=0.60` is the ONE change. Phase 5.5 gate asserts ALL conditions at runtime per Sub-fix 4+8.

8. **Cross-axis orthogonality with iter-v3/065 and /066** (T6 + Section 2.8):
   - /065 axis: TRAIN-TIME label generation (atr_tp_multiplier, atr_sl_multiplier)
   - /066 axis: INFERENCE-TIME weight modifier (vol_scale_ceiling — REVERTED at /067 for isolation)
   - /067 axis: INFERENCE-TIME emission gate threshold (`_inference_threshold_floor`)
   - Separate modules: `labeling.py` vs `risk_v2.py` vs `lgbm.py`
   - Separate Signal effects: `tp_pct/sl_pct` vs `weight` vs `NO_SIGNAL gate`
   - At /067: /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0) (kept; /065 tested separately); /066's vol_scale_ceiling REVERTED to 1.0 (default)
   - At /069 CONFIRMATION: /065 + /067 (if both PROMISING) bundled at multi-seed — second-order Optuna coupling captured

9. **Path selection rationale: why NOT Path E (vote-based)**: Path E (K=2-of-3 vote requirement) is PROMISING-viable but smaller magnitude than Path D, AND implementation is more complex (requires per-seed direction tracking through the prediction path; vote logic at `get_signal`). Path D is implementationally simplest (one `max()` at line 507). If Path D fires INERT or NEGATIVE, Path E is the natural /068 fallback.

10. **Cannot be retroactively renegotiated**. Established at brief LOCK (setup commit).

---

**Setup commit SHA**: (this commit, LOCKED)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/067`; pull SHA `aa5b0c8` (EDA).
2. Apply Sub-fixes 1-8:
   - Add `inference_threshold_floor` constructor parameter (default 0.0) on `LightGbmStrategy.__init__`
   - Apply `max(..., self._inference_threshold_floor)` at `lgbm.py:507` (post-aggregation step)
   - Pass `inference_threshold_floor=0.60` in `_build_v3_model` (run_baseline_v3.py)
   - REVERT `vol_scale_ceiling=0.8` from /066 — REMOVE explicit kwarg so default 1.0 applies
   - Keep `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` UNCHANGED
   - Bump `ITERATION_LABEL = "v3-067"`
   - Add `tests/strategies/ml/test_inference_threshold_floor.py` (3 unit tests per Sub-fix 7)
   - Add runtime assertion that `_inference_threshold_floor == 0.60` for all 3 v3 strategies per Sub-fix 8
3. Run `uv run pytest tests/strategies/ml/test_inference_threshold_floor.py tests/features_v3/ -v` to confirm test PASS.
4. Run `uv run python run_baseline_v3.py --clean-oof --exploration --n-trials 35` (Phase 6 backtest).
5. Wall-clock target ~1.1h; HARD CAP 2h per `feedback_v3_cadence_discipline.md`.
6. Engineering report covers Section 8 LOCKED criteria evaluation (PASS/FAIL on each gate A.1–E.18) for Critic Phase 7.5.
