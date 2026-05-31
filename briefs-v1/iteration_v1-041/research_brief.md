# iter-v1/041 — Research Brief

**Iteration**: iter-v1/041
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 8 of 10
**Branch**: `iteration-v1/041`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

**iter-v1/041 — EXPLORATION cycle-5 #8/10**
- **Axis**: LABELING — TIGHTEN-WITHIN-TRIPLE-BARRIER (uniform shrink across all 4 cohorts to `atr_tp = 1.5 × NATR_21 × close`, `atr_sl = 0.75 × NATR_21 × close`; ratio 2.0 preserved); paired with `min_data_in_leaf` Optuna lower-bound floor bump 20 → 50 (defensive mitigation).
- **Axis family**: `labeling` — REPEAT (last used /035 trend-scanning 5-cohort, 6 iters ago)
- **Load-bearing purpose**: resolves the bold central question for cycle-5 labeling family — does denser, shorter-horizon triple-barrier labeling lift Optuna's training-signal density enough to translate into OOS Sharpe lift, or does the median forward-window compression into chop-noise territory dominate?

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION **8 of 10** (2 EXPLORATIONs to go before /044 CONFIRMATION can launch). Prior 6 cycle-5 EXPLORATIONs:
  - /034 NEG-CLEAN LEARNED-NEG (feature-family basis_zscore_30)
  - /035 NEG-CAT-bundle bimodal (labeling trend-scanning 5-cohort)
  - /036 PROMISING-CLEAN (per-cohort-specialization LINK+DOT trend-scan; OOS Sharpe +1.7465 — single-seed v1 high)
  - /037 PROMISING-CLEAN (loss-function Sortino 5-cohort; OOS Sharpe +0.8388)
  - /038 NEG-CATASTROPHIC EDA-vindicated (risk-primitive symmetric vol-ceiling)
  - /039 (hybrid loss-function × per-cohort — substrate-stacking probe)
  - /040 (feature-family composed regime_momentum_signed_5d)
- **NO kill-switches** (cycle-5 directive).
- **Wall-clock target**: anchored on /014 σ_t labeling baseline (~75-95 min) + density lift overhead (no, density doesn't change per-trial cost; only label volume per cell). Modal **~60-80 min**; conservative **90 min**; **2h hard cap**.

---

## Section 0.6 — Axis-Family Rotation (v1-only) — REPEAT (counter 2/5)

- **Axis family**: `labeling` REPEAT
  - **Last `labeling` use**: iter-v1/035 (trend-scanning 5-cohort), 6 EXPLORATIONs ago
  - **Honest correction to task header**: the task brief framed this as "labeling family REPEAT (last /035/036)". /036 was **per-cohort-specialization** family, NOT labeling — the prior 5 families distribute across 5 distinct families (see table below). The labeling family was therefore last used 6 EXPLORATIONs ago, NOT 1.
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md` + /039 + /040 closeouts in flight):
  - iter-v1/036: per-cohort-specialization
  - iter-v1/037: loss-function
  - iter-v1/038: risk-primitive
  - iter-v1/039: loss-function × per-cohort-specialization (hybrid)
  - iter-v1/040: feature-family
- **Rotation status**: **VALID**. None of the prior 5 was `labeling`. Same-family-counter for `labeling` across the entire v1 history = **2** (/014 σ_t source change + /035 trend-scanning), well within the 5+ saturation rule. /041 lifts the counter to 3.
- **STRUCTURALLY DIFFERENT mechanism from /014 + /035**:
  - /014 changed the σ_t **source** (NATR_21 → past-only EWMA at 14-day half-life); the barrier *type* and *width-multiplier intent* were unchanged.
  - /035 replaced triple-barrier with **trend-scanning Wald-test forward-window labels** at horizon grid (5, 8, 13, 21) — different label *family* entirely.
  - /041 **stays within triple-barrier σ_t-source** but TIGHTENS the per-cell ATR multiplier from `2.9/3.5` (Pool A / C/D/E) × NATR to a uniform `1.5/0.75 × NATR` — same family, same source, same TP/SL ratio (2.0), **shorter forward horizon via tighter barriers**. This is the first TIGHTEN-direction triple-barrier intervention in v1 history.
- **One-sentence rationale**: /041 directly tests whether the LightGBM training signal benefits from denser short-horizon labels (predicted 2.55× – 3.00× IS density lift per EDA §3 GBM-scaling argument) at the cost of compressed forward-window resolution; the experiment is structurally orthogonal to /014 (source change) and /035 (family change), and the labeling family has cooled for 6 EXPLORATIONs since its last use.

---

## Section 1 — Hypothesis

**H1 (PRIMARY, 3 sentences)**: At v1 EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3, single-seed=42, V1_FEATURE_COLUMNS_PRUNED 43-44 cols), shrinking the triple-barrier ATR multipliers uniformly to `atr_tp_mult=1.5, atr_sl_mult=0.75` produces a **2.55×–3.00× IS density lift** (~1582-1863 labeled trades vs baseline 621) which raises Optuna's training-signal density per (cohort, training-window) cell; the same TP/SL ratio (2.0) preserves the directional-magnitude structure of trade expectancy so per-trade Sharpe-in-expectation stays roughly constant; the net portfolio OOS Sharpe Δ therefore lands in the **PROMISING-INERT-FAV modal band [+0.05, +0.10]** under the dual influence of √N count lift (~1.6×) and shorter-horizon noise dilution. The `min_data_in_leaf` Optuna lower-bound floor bump 20 → 50 defensive mitigation guards against over-fit on noisier shorter-horizon labels by forcing larger leaf populations that average out per-leaf noise.

**H1a (mechanism, EDA prior — load-bearing constraint)**: EDA §5 shows mean absolute per-trade PnL shrinks from baseline 5.70% to 3.03% under the tighten (0.53×), and at 0.1% per-side fees the fee-to-edge ratio nearly **doubles** (1.8% → 3.3%). The Sharpe-after-fees is therefore more sensitive than before. EDA §6 modal prior is NEG-CAT 30% MODAL with 44% combined NEG mass — the strongest NEG-leaning EDA prior produced in cycle-5. My H1 modal-band is more optimistic than the EDA prior on grounds that (a) the `min_data_in_leaf=50` floor is a structural mitigation specifically targeted at the noise-dilution mechanism, and (b) /036's per-cohort lift demonstrates that label-distribution interventions CAN produce single-seed PROMISING outcomes at v1 EXPLORATION budget. The EDA-author honestly notes /035 trend-scanning shorter-horizon labels collapsed bimodal; /041 is family-adjacent but mechanism-different.

**H1b (falsifiable)**: If F-AXIS #1 OOS Sharpe Δ lands < −0.05 vs baseline +0.6637 AND F-AXIS #5 OOS win-rate < 35% AND F-AXIS #4 mean |net_pnl_pct| OOS within [2.5%, 3.5%], the tighten axis is REFUTED — chop-noise dominance is empirically confirmed and the v1 LightGBM does NOT benefit from denser-but-noisier short-horizon labels. /042/043 do NOT re-attempt this mechanism; cycle-6 may re-attempt only with an orthogonal substrate (e.g., per-cohort or per-regime tighten rather than uniform).

---

## Section 2 — F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1 anchor (+0.6637)

**Anchor**: BASELINE_V1 OOS Sharpe +0.6637 (the sacred anchor; /041 is single-axis variation off baseline, not off /036 or /037).

| Band | OOS Sharpe Δ vs BASELINE | Verdict subtype |
|---|---|---|
| Δ ≥ +0.30 | exceeds modal upside (OOS ≥ +0.96) | EXPLORATION-PROMISING-CLEAN-EXCEPTIONAL |
| +0.10 ≤ Δ < +0.30 | PROMISING band — density lift outweighs noise | EXPLORATION-PROMISING-CLEAN |
| +0.05 ≤ Δ < +0.10 | **PROMISING-INERT-FAV** — density lift marginally additive | EXPLORATION-PROMISING-INERT-FAV |
| −0.05 ≤ Δ < +0.05 | INERT — √N count gain canceled by chop noise | EXPLORATION-INERT-NO-EFFECT |
| −0.30 ≤ Δ < −0.05 | NEG-OVER-FILTER — min_data_in_leaf=50 mitigation under-shoots | EXPLORATION-NEGATIVE-CLEAN |
| Δ < −0.30 | NEG-CAT — win-rate collapses below 35%, basin migrates to IS over-fit | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal band prior (QR-tightened from EDA NEG-MODAL given min_data_in_leaf=50 mitigation)**:

| Outcome | EDA prior | QR final prior | Rationale for adjustment |
|---|---|---|---|
| PROMISING-CLEAN-EXCEPTIONAL (Δ ≥ +0.30) | — | **3%** | Possible only if density lift + noise mitigation jointly fire |
| PROMISING-CLEAN (Δ ∈ [+0.10, +0.30)) | 18% (combined CLEAN) | **15%** | √N scaling caps near +0.30; ceiling enforced by R3 OOD gate |
| **PROMISING-INERT-FAV (Δ ∈ [+0.05, +0.10))** | 16% | **22% MODAL** | min_data_in_leaf=50 lifts the noise floor enough to nudge marginal positive |
| INERT-NO-EFFECT (Δ ∈ [−0.05, +0.05)) | 22% | **22%** | Unchanged; the chop-vs-√N balance lives here |
| NEG-OVER-FILTER (Δ ∈ [−0.30, −0.05)) | 14% | **16%** | Mitigation partially helps but doesn't fully arrest noise capture |
| NEG-CATASTROPHIC (Δ < −0.30) | **30%** | **22%** | min_data_in_leaf=50 floor moves catastrophe mass into NEG-CLEAN |

**Combined PROMISING (CLEAN + EXCEPTIONAL + INERT-FAV) = 40%** vs EDA 34%. **Combined NEG (CLEAN + CAT) = 38%** vs EDA 44%. The min_data_in_leaf=50 floor is the load-bearing reason for the upward shift; if it is silently overridden by Optuna lower-bound bypass, the EDA's NEG-MODAL 30% reasserts.

**Modal band**: PROMISING-INERT-FAV [Δ ∈ +0.05, +0.10) at 22% weight, OOS Sharpe absolute ~ **+0.72** (Δ +0.06 vs baseline).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason (per v1 skill HIGH-RISK definition — changes Optuna's training-objective domain)**: /041 DOES change the LightGBM training-objective domain in a literal sense — the per-cell labels are different (TP vs SL vs timeout reroute under tighter barriers per EDA §4) and the per-sample weights (`abs_pnl`) shift in proportion to the new barrier distance. **However**, the change is a SCALAR shrink of barrier widths (factor 1.5/2.9 = 0.52 for Pool A; 1.5/3.5 = 0.43 for C/D/E) within the same σ_t source (NATR_21) and same TP/SL ratio (2.0) — it does NOT replace the labeling primitive, swap the σ_t source, or introduce a new gradient surface. The Optuna search space (hyperparameter bounds) is unchanged except for the deliberately-paired `min_data_in_leaf` lower bound 20 → 50, which is a defensive mitigation against noise capture not an exploratory expansion.
- Per v1 skill HIGH-RISK threshold criteria:
  - Risk-primitive constraint change: NO
  - Universe substitution: NO
  - Label-mode change: NO (still triple-barrier σ_t, just narrower band)
  - Feature-set replacement: NO
  - Bar-interval change: NO
- **Comparable precedent**: /014 σ_t source change (NATR → EWMA) WAS declared HIGH-RISK because the σ_t **source** changed, introducing a structurally different per-row barrier-distance signal. /041 does NOT change the source — it shrinks the width-multiplier within the same source. This is more analogous to a width-knob change than a source-swap.
- **Budget choice**: SINGLE-SEED=42 at v1 EXPLORATION standard (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42). NORMAL-RISK declaration permits single-seed without multi-seed validation opt-in. If F-AXIS #1 lands PROMISING-CLEAN or PROMISING-CLEAN-EXCEPTIONAL, /044 multi-seed CONFIRMATION inherits the axis.
- **NORMAL-RISK guardrail**: F-AXIS #2 + F-AXIS #4 + F-AXIS #5 all serve as MECHANICAL falsifiers — if any fires FAIL, the axis is treated as MISCALIBRATED-or-CHOP-DOMINATED rather than EDGE-FOUND, and /044 routing closes the axis regardless of F1 magnitude.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (SMALL — CLI flags + dispatch)

Per the AXIS specification, the existing `LightGbmStrategy` already accepts `atr_tp_multiplier` and `atr_sl_multiplier` constructor parameters (used for both label-time barrier distance via `labeling.py` AND execution-time barrier via `backtest.py:799`). The dispatch path needs CLI flag plumbing + a `--label-mode triple_barrier` (default) compatibility check:

1. **EDIT `run_baseline_v1.py`**:
   - **Add CLI flags**:
     - `--atr-tp-mult <float>` (single value applied uniformly to all 4 cohorts; default None = use per-cohort baseline)
     - `--atr-sl-mult <float>` (same; default None)
     - `--min-data-in-leaf-min <int>` (default None = use Optuna default 20; iter-v1/041 will pass 50)
   - **Add `iteration_label == "v1-041"` dispatch branch** (~60 lines):
     - Pre-flight assert: `atr_tp_mult_arg == 1.5 and atr_sl_mult_arg == 0.75` (enforces axis fidelity)
     - Pre-flight assert: `min_data_in_leaf_min_arg == 50` (enforces paired mitigation)
     - Pre-flight assert: `label_mode_arg == "triple_barrier"` (axis isolation — no trend-scanning collision)
     - Pre-flight assert: `set(symbols) == set(V1_BASELINE_UNIVERSE)` (5-cohort baseline universe; full v1 attribution surface)
     - Dispatch banner: `[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE: uniform atr_tp_mult=1.5/atr_sl_mult=0.75 (was Pool A 2.9/1.45, C/D/E 3.5/1.75); min_data_in_leaf_lower_bound=50 (was 20); ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1, features={len(active_feature_columns)} cols`
     - Dispatch all 4 models (A pool BTC+ETH, C LINK, D LTC, E DOT) each constructed with `atr_tp_multiplier=1.5, atr_sl_multiplier=0.75` (overriding per-cohort baseline values).
   - **Plumb `min_data_in_leaf_min_arg` to `LightGbmStrategy.__init__()` and through to Optuna's `objective()` via a new `min_child_samples_lower_bound` constructor parameter**.
   - **Add `"v1-041"` to BASELINE catch-all exclusion tuple** at line ~3686 (per `/030 LESSON`).

2. **EDIT `src/crypto_trade/strategies/ml/lgbm.py`**:
   - Add `min_child_samples_lower_bound: int | None = None` to `LightGbmStrategy.__init__()` (alongside `atr_tp_multiplier`, `atr_sl_multiplier`).
   - Propagate to `_run_optuna_search()` → `objective()` so that when `min_child_samples_lower_bound is not None`, the Optuna `trial.suggest_int("min_child_samples", LOWER, 100)` uses LOWER = `min_child_samples_lower_bound` instead of the v1_pruned default 20.
   - When `min_child_samples_lower_bound is None`: BIT-IDENTICAL behavior to current code. Backward compatibility preserved.

3. **EDIT `src/crypto_trade/strategies/ml/optimization.py:298`**:
   - Replace the hard-coded `20 if _pruned else 5` lower bound with a `_min_child_samples_lower or (20 if _pruned else 5)` pattern threaded from the strategy constructor.

### Section 3.2 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --label-mode triple_barrier \
  --atr-tp-mult 1.5 \
  --atr-sl-mult 0.75 \
  --min-data-in-leaf-min 50 \
  --pruned-features \
  --iteration 41 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  > logs/iter_v1_041_backtest.log 2>&1
```

Flag breakdown:
- `--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT` = V1_BASELINE_UNIVERSE (full 5-cohort).
- `--label-mode triple_barrier` = baseline labeling primitive (NOT trend-scanning).
- `--atr-tp-mult 1.5 --atr-sl-mult 0.75` = uniform tighten across all cohorts (ratio 2.0).
- `--min-data-in-leaf-min 50` = paired mitigation against noise capture.
- `--pruned-features` = V1_FEATURE_COLUMNS_PRUNED (43-44 cols).
- `--iteration 41` triggers the v1-041 dispatch branch with pre-flight asserts.
- `--exploration --n-trials 18 --ensemble-size 3 --seeds 1` = v1 EXPLORATION standard.

### Section 3.3 — Symbols + models + config

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE (BTC, ETH, LINK, LTC, DOT) — 5 cohorts |
| Models | Model A (BTC+ETH pool), Model C (LINK), Model D (LTC), Model E (DOT) — atr_tp=1.5 / atr_sl=0.75 UNIFORM (override per-model baseline values) |
| Labels | `triple_barrier` σ_t = NATR_21 × close × multiplier; same source as baseline; uniform multipliers; timeout = 21 candles (unchanged) |
| Optuna objective | `sharpe` baseline (NOT sortino — axis isolation from /037) |
| Features | V1_FEATURE_COLUMNS_PRUNED (43-44 cols incl. /034 basis_zscore_30 if still active per /040 closeout state) — UNCHANGED |
| Sample weight | `abs_pnl` — UNCHANGED (auto-shifts in magnitude due to tighter barriers; mechanism documented in §H1a) |
| Optuna bounds | `v1_pruned` with `min_child_samples` lower bound = 50 (paired mitigation; all other bounds UNCHANGED) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates | R1 ON A/C/D/E (where applicable per baseline); R2 ON E only; R3 ON all 4 (cutoff 0.70, 16 features) |

### Section 3.4 — Test mandate (10+ tests per `/030 LESSON`)

`tests/test_iteration_v1_041.py` MUST include:

1. `test_v1_041_dispatch_branch_exists` — `iteration_label == "v1-041"` path reachable.
2. `test_v1_041_pre_flight_atr_tp_assert` — `--atr-tp-mult 2.9` raises AssertionError.
3. `test_v1_041_pre_flight_atr_sl_assert` — `--atr-sl-mult 1.45` raises AssertionError.
4. `test_v1_041_pre_flight_min_data_in_leaf_assert` — `--min-data-in-leaf-min 20` raises AssertionError.
5. `test_v1_041_pre_flight_label_mode_assert` — `--label-mode trend_scanning` raises AssertionError.
6. `test_v1_041_pre_flight_universe_assert` — wrong symbol set raises AssertionError.
7. `test_v1_041_in_baseline_catchall_exclusion` — `"v1-041"` in exclusion tuple.
8. `test_v1_041_dispatch_banner_emitted` — banner contains `atr_tp_mult=1.5`, `atr_sl_mult=0.75`, `min_data_in_leaf_lower_bound=50`.
9. `test_v1_041_atr_multipliers_threaded_to_all_models` — real-instance Model A/C/D/E all have `.atr_tp_multiplier == 1.5` and `.atr_sl_multiplier == 0.75`.
10. `test_v1_041_min_child_samples_lower_bound_threaded` — real-instance all 4 models have `._min_child_samples_lower_bound == 50`.
11. `test_v1_041_min_child_samples_lower_bound_default_unchanged` — when `--min-data-in-leaf-min` flag absent, BIT-IDENTICAL to baseline (Optuna lower bound = 20 for pruned).
12. `test_v1_041_label_time_barrier_uses_new_multiplier` — synthetic master row with `NATR_21=2.0`, close=100 yields label TP distance `1.5 × 2.0 × 100 / 100 = 3.0%` not baseline 5.8% (Pool A) or 7.0% (C/D/E).

All 12 tests + existing v1 test corpus MUST pass at Phase 6 closeout.

---

## Section 4 — F-AXIS #2-#5 mechanism falsifiers (diagnostic)

### F-AXIS #2 — Wiring assert (mechanical sanity)

**PASS criterion**: Phase 6 backtest log contains:
- `[iter-v1/041] TRIPLE-BARRIER TIGHTEN ACTIVE` banner (1 line at dispatch).
- Per-model Optuna best_params show `min_child_samples ≥ 50` for ≥ 95% of cells (~100%).
- Per-model labeled trade roster shows label-time barrier distances within ±10% of `1.5 × NATR_21 × close` (sample 20 rows per model, manual or programmatic check).
- IS total trade count between [1300, 2000] (calibrated EDA §3 band ±15%).

**FAIL** = silent fallback to baseline multipliers OR `min_child_samples` lower bound stuck at 20 OR label-time barrier inconsistent with new multipliers → **BLOCK-PENDING-FIX**.

### F-AXIS #3 — Cell-rate density (mechanism check)

**PASS criterion**: per-(cohort, training-window) label count median ≥ 1000 (vs baseline ~360). This proves the density-lift mechanism actually fired at the cell level, not just at the IS aggregate.

**FAIL** (median < 800): the GBM-scaling assumption is violated — barrier resolution is not accelerating proportional to barrier-width² as predicted. Verdict downgrades to NEG-MECHANICAL: the density lift didn't bite; whatever F1 outcome surfaces is attributable to a different mechanism than the EDA proposed.

### F-AXIS #4 — PnL magnitude band (chop-noise dominance check)

**PASS criterion**: OOS mean |net_pnl_pct| ∈ [2.5%, 3.5%] (predicted by EDA §5 from 0.53× scaling: baseline 5.70% × 0.53 = 3.02%).

**FAIL HIGH** (mean > 4.0%): the per-trade PnL didn't shrink as predicted — barrier-distance compression weaker than barrier-width compression implies; investigate exit logic.

**FAIL LOW** (mean < 2.0%): per-trade PnL collapsed below noise floor — fees dominate; F1 result is fee-drag artifact NOT mechanism-edge.

### F-AXIS #5 — Win-rate floor (chop-noise dominance check, LOAD-BEARING)

**PASS criterion**: OOS WR ≥ 35% portfolio (baseline OOS WR ~40%; band allows 5pp degradation while preserving favorable TP-cluster structure).

**FAIL** (OOS WR < 35%): chop-noise dominance EMPIRICALLY confirmed — tighter barriers convert directional-signal trades into random-walk trades. Verdict downgrades regardless of F1: axis **CLOSED for v1**, /042/043 do NOT re-test triple-barrier tighten in any per-cohort or per-regime variant; cycle-6 may re-attempt only with structurally different substrate (e.g., volatility-conditional barrier widths or `--label-timeout-candles` reduction paired with width preservation).

### F-AXIS #6 — Wall-clock ~70 min

**PASS criterion**: total wall-clock ≤ 90 min. Anchored on /014 σ_t labeling baseline (~75-95 min) + small Optuna overhead from `min_child_samples` lower bound bump (per-trial cost negligible).

**FAIL** = > 120 min → hardware anomaly OR label-generation regression (density lift × per-row cost interaction); investigate.

### F-AXIS #7 — Trade-count bands (sanity)

- IS trades ∈ [1300, 2000] (EDA §3 predicted [1582, 1863]; band widened ±15% for cohort-level variance)
- OOS trades ∈ [400, 700] (EDA §3 predicted [480, 567]; band widened ±15%)
- IS < 1300 OR OOS < 400 → density lift didn't fire as predicted → cross-check F-AXIS #2 + F-AXIS #3
- IS > 2200 OR OOS > 800 → over-saturation of R3 OOD gate cap; investigate R3 retention rate

---

## Section 5 — Configuration

(See §3.3 table above.) All other settings: BASELINE_V1 defaults. The only two parameter changes from BASELINE are:
1. `atr_tp_multiplier = 1.5` and `atr_sl_multiplier = 0.75` uniformly across all 4 models (override per-model baselines 2.9/1.45 Pool A, 3.5/1.75 C/D/E).
2. Optuna `min_child_samples` lower bound = 50 (override default 20 for pruned config).

---

## Section 6 — Wall-clock estimate

| Phase | Cost | Anchor |
|---|---|---|
| Data fetch | 0 min | 5-cohort 8h klines on disk |
| Feature regen | 0 min | V1_FEATURE_COLUMNS_PRUNED parquets on disk |
| Backtest compute | ~60-80 min modal | /014 σ_t labeling ~75-95 min baseline; tighter barriers don't change per-trial Optuna cost |
| Report layer (DSR/PSR/etc) | ~3 min | standard |
| **Total modal** | **~65-85 min** | |
| **Conservative band** | 60-100 min | |
| **Hard cap** | 2h (skill default) | |

Honest overrun acceptable; no runtime kill-switch.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (per /039 lesson — inline, not deferred)

**Most plausible failure scenario at single-seed=42 EXPLORATION budget**: Tighter barriers compress the median forward-window from baseline 8-13 candles to ~3-6 candles (estimated from `(barrier_distance)²` scaling and EDA §5 PnL magnitude shrink). At BTC NATR_21 p50 = 2.46% and the proposed `1.5 × NATR_21` TP = 3.69%, the TP is well within typical single-candle 8h BTC range — meaning many "TP hits" become near-immediate single-candle resolutions driven by intra-candle volatility NOT by the LightGBM-predicted direction. The labels then encode noise rather than signal. The `min_data_in_leaf=50` floor mitigates this in the LEAF averaging direction but does NOT prevent the LABEL itself from being noise-contaminated. Optuna at n_trials=18 single-seed lands on a basin that overfits the noisy short-horizon labels — IS Sharpe rises moderately (denser labels = lower variance estimator in-sample) but OOS Sharpe falls because the noise pattern doesn't generalize.

**Gates that should catch the failure**:
- F-AXIS #4 (PnL magnitude): OOS mean |net_pnl_pct| at the low end of [2.5%, 3.5%] band or below — indicates fees dominate the edge.
- F-AXIS #5 (OOS WR): below 35% — direct evidence of chop-noise dominance.
- F-AXIS #1 OOS Δ ∈ [−0.30, −0.05) modal NEG-CLEAN with high probability mass on combined NEG (38%).

**Failure metrics signature**: IS Sharpe Δ moderately positive (+0.05 to +0.30; denser labels naturally lift in-sample variance estimator), OOS Sharpe Δ negative (−0.05 to −0.30), OOS WR < 38%, OOS mean |net_pnl_pct| ~ 2.5-3.0% (at fee-drag boundary), per-symbol OOS attribution spreads losses approximately uniformly across cohorts (NOT concentrated on one symbol — chop-noise is universal).

**Distinct from /035 NEG-CAT-bundle failure mode**: /035 trend-scanning produced bimodal IS Sharpe lift + OOS Sharpe collapse on specific cohorts via label-FAMILY change. /041 tighten-within-triple-barrier produces broader, smaller-magnitude noise capture spread across cohorts via label-WIDTH change. The two are mechanism-distinct.

---

## Section 8 — Locked Numerical MERGE/NO-MERGE Thresholds (per /039 lesson)

EXPLORATION at single-seed = NO direct MERGE. MERGE eligibility requires /044 multi-seed CONFIRMATION. Pre-registered thresholds for /041 routing to /044 substrate selection:

| Outcome band | Threshold | /044 routing |
|---|---|---|
| **PROMISING-CLEAN** | OOS Sharpe Δ vs baseline ≥ +0.10 AND IS Sharpe Δ ≥ +0.05 AND OOS trades ≥ 400 AND F-AXIS #2 PASS AND F-AXIS #5 OOS WR ≥ 38% AND F-AXIS #4 PASS | /041 enters /044 CONFIRMATION substrate candidate list (multi-seed validation alongside /036 + /037 + /040 candidates per /044 brief composition decision) |
| **PROMISING-INERT-FAV** | OOS Δ ∈ [+0.05, +0.10) AND F-AXIS #2 + #4 + #5 all PASS | /041 axis informational; /044 substrate uses /036 + /037 + /040 candidates; /041 deferred to /045+ if /044 mass-merges |
| **INERT** | OOS Δ ∈ [−0.05, +0.05) | /041 axis CLOSED for cycle-5; uniform tighten is mechanism-empty at v1 EXPLORATION budget |
| **NEG-CLEAN** | OOS Δ ∈ [−0.30, −0.05) | /041 axis CLOSED for cycle-5; uniform tighten REFUTED |
| **NEG-CAT** | OOS Δ < −0.30 OR F-AXIS #5 OOS WR < 35% | /041 axis CLOSED for v1 PERMANENTLY; cycle-6 may only re-attempt with orthogonal substrate (per-cohort or per-regime variants); add to dead-paths catalog: "uniform triple-barrier TIGHTEN at multiplier ratio preserved" → REFUTED at v1 EXPLORATION budget |
| **NEG-WIRING / NEG-MECHANICAL** | F-AXIS #2 FAIL OR F-AXIS #3 FAIL | BLOCK-PENDING-FIX with ONE rerun chance per v1 skill |

ABSOLUTE MERGE GATES (apply at /044 CONFIRMATION only, not /041): IS Sharpe > 1.0 AND OOS Sharpe > 1.0 AND OOS/IS ratio ≥ 0.5 AND OOS trades ≥ 130 AND DSR > 0.95 AND PBO < 0.40 AND PSR > 0.95 AND top-symbol concentration ≤ 30% of OOS PnL. /041 EXPLORATION does NOT evaluate against these.

---

## Section 9 — Behavioral-effect predictor + LIBRARY STACK DECLARATION (per /039 lesson)

### Section 9.1 — Behavioral-effect predictor

Per `feedback_axis_saturation_predictor.md`: predict observable behavioral effects with falsifier triggers.

**Predicted IS trade count**: range [1300, 2000], modal ~1700 (EDA §3 capped band [1582, 1863]; band widened ±15% for cohort-level variance and R3 OOD gate retention).

**Predicted OOS trade count**: range [400, 700], modal ~520 (EDA §3 [480, 567]; same widening).

**Predicted per-symbol IS trade count distribution** (anchored to EDA §3 per-symbol projection):
- BTC: [288, 339]
- ETH: [369, 435]
- LINK: [372, 438]
- LTC: [316, 372]
- DOT: [237, 279]

**Predicted bundle OOS Sharpe Δ vs baseline**: range [−0.55, +0.30], modal **+0.06** (OOS Sharpe ~+0.72 absolute; bundle in PROMISING-INERT-FAV band).

**Predicted F-AXIS #4 mean |net_pnl_pct| OOS**: 3.03% modal (EDA §5 anchor), band [2.5%, 3.5%].

**Predicted F-AXIS #5 OOS WR**: modal ~38% (baseline ~40%; 2pp degradation from shorter-horizon noise but min_data_in_leaf=50 mitigates leaf-level noise), band [33%, 42%].

**Predicted exit-mix reroute** (EDA §4):
- Aggregate: TP/SL acceleration; ~1-9% of baseline timeouts flip to TP; 0.7-4.8% flip to SL; "still timeout" share shrinks 24.5% → ~16-22%.
- LINK + DOT + LTC: highest reroute (their baseline timeout shares 22-32% have most room to compress).
- BTC: smallest reroute (already 13.3% timeout share).

**Falsifier triggers**:
1. IS < 1000 OR OOS < 300 → density lift didn't fire; TECHNICAL-FAILURE-SILENT-FALLBACK → BLOCK-PENDING-FIX.
2. F-AXIS #2 wiring fails (banner missing OR `min_child_samples` lower bound stuck at 20 OR baseline multipliers in dispatch) → BLOCK-PENDING-FIX.
3. F-AXIS #5 OOS WR < 35% → chop-noise dominance EMPIRICALLY confirmed → axis CLOSED for v1 regardless of F1 magnitude.
4. F-AXIS #4 OOS mean |net_pnl_pct| > 4.0% OR < 2.0% → PnL scaling assumption violated; revisit F1 interpretation.

### Section 9.2 — LIBRARY STACK DECLARATION

NO external ML-finance libraries used in this iteration. Standard stack only:
- **LightGBM** 4.x (existing project dependency, no version change)
- **Optuna** ≥3.5 (existing, no version change)
- **NumPy** ≥1.24 / **Pandas** ≥2.0 / **PyArrow** ≥14 (existing, no version change)
- **scipy.stats** (existing; used by existing `optimization.py` Sharpe-with-threshold path; no new import)
- **statsmodels** ≥0.14 (existing; ADF used by reporting layer; no new import)

NOT used in /041: mlfinlab, mlfinpy, pypbo, fracdiff, financial-machine-learning. No new dependency added.

The triple-barrier label-generation path at `src/crypto_trade/strategies/ml/labeling.py:label_trades()` is the existing path (shipped pre-/014); /041 modifies only the `atr_tp_multiplier` and `atr_sl_multiplier` constructor parameters passed to `LightGbmStrategy` and the `min_child_samples` Optuna lower bound. No new code paths in `labeling.py` or `optimization.py` beyond the lower-bound threading.

---

## Section 10 — Anti-Cheating Self-Check

- [x] EDA reads IS-only (`analysis/iteration_v1-041/eda.py` reads `reports-v1/iteration_v1-baseline/in_sample/trades.csv`; baseline OOS metrics consulted only as reference anchor for F-AXIS #1 band).
- [x] No parameter tuning on OOS data — `atr_tp_mult=1.5, atr_sl_mult=0.75` and `min_data_in_leaf_min=50` are pre-registered in this brief BEFORE Phase 6 backtest.
- [x] OOS_CUTOFF_DATE = 2025-03-24 SACRED — unchanged.
- [x] training_months = 24 SACRED — unchanged.
- [x] IS window NOT trimmed; full 2020-01 → 2025-03-23 used at backtest.
- [x] No new EDA scripts beyond `analysis/iteration_v1-041/eda.py` (Phase 1 deliverable, IS-only by file path; OOS reads are reference-anchor only).
- [x] Hypothesis falsifiers F1-F7 pre-registered above Phase 6 dispatch.
- [x] No symbol re-screening on IS+OOS or post-hoc — V1_BASELINE_UNIVERSE used unchanged.
- [x] No feature engineering response to /040 closeout — V1_FEATURE_COLUMNS_PRUNED frozen at /040 state; if /040 closes with feature-set change adopted, /041 re-runs with the updated stack; otherwise the /040 baseline feature stack applies.

---

## Section 11 — Phase 4.5 LM Master Response Map

**Status**: `briefs-v1/iteration_v1-041/lgbm_advisor.md` is NOT YET PRESENT at brief authoring time. Phase 4.5 LM Master advisor is expected to fire SEPARATELY at /041 dispatch. This Section 11 pre-adopts the four most-likely LM Master recommendations based on /037+/038+/039+/040 pattern and will be UPDATED in a follow-up commit if the actual Phase 4.5 advisor diverges materially (per v1 skill discipline).

| # | Anticipated LM Master recommendation | QR pre-adjudication | Reason |
|---|---|---|---|
| 1 | Mechanism prediction — tighter barriers compress forward-window into chop-noise territory; predict 2-regime outcome distribution (PROMISING-INERT-FAV if min_data_in_leaf mitigation bites; NEG-CLEAN/CAT if it doesn't) | **ADOPTED** | Pre-registered as H1 + H1a + H1b in §1; F-AXIS #5 OOS WR is the load-bearing chop-noise mechanism falsifier. |
| 2 | Per-cohort attribution prediction (decisive diagnostic) — uniform tighten will hit cohorts with highest baseline timeout share hardest in BOTH directions (best lift on reroute success; worst regression on chop-noise dominance); BTC has lowest sensitivity (timeout share 13.3%), LINK/LTC/DOT highest | **ADOPTED** | Pre-registered as F-AXIS #4 / #5 / #7 per-symbol bands in §4 and §9.1 reroute prediction. /044 routing in §8 implicitly accounts for cohort-uneven response. |
| 3 | Budget — `n_trials=18` + `ENSEMBLE_SIZE=3` + single-seed=42 ADEQUATE; do NOT raise. The denser-label regime increases per-cell training data so the Optuna budget is RELATIVELY tighter per-effective-label than baseline; raising n_trials only invites the v3 INERT-at-higher-budget pattern (`feedback_v3_inert_features_at_higher_budget.md`) | **ADOPTED** | Config locked at §3.3: n_trials=18, ENSEMBLE_SIZE=3, single-seed=42. |
| 4 | F-AXIS falsifier recommendations — keep F1 OOS Δ as primary, but elevate F-AXIS #5 OOS WR to LOAD-BEARING because chop-noise dominance is the dominant failure mode; F-AXIS #4 PnL magnitude band as fee-drag interpretation gate. Add cell-level density check as F-AXIS #3 to validate the GBM-scaling claim mechanistically. | **ADOPTED** | F-AXIS #5 elevated to LOAD-BEARING in §4 and §8 (NEG-CAT verdict triggers axis CLOSURE regardless of F1). F-AXIS #4 + F-AXIS #3 explicit. |

If Phase 4.5 LM Master advisor surfaces a recommendation NOT in this set (e.g., a specific alternative `atr_tp_mult / atr_sl_mult` calibration based on per-cohort EDA analysis, or a different `min_child_samples` lower bound), Section 11 will be UPDATED in a separate commit BEFORE Phase 6 dispatch per v1 skill 4.5 → 5 reconciliation discipline.

---

## Section 12 — Path Forward Predictions (/044 routing implications per outcome quadrant)

| /041 outcome | /044 routing | Rationale |
|---|---|---|
| **PROMISING-CLEAN-EXCEPTIONAL** (Δ ≥ +0.30) | /041 enters /044 CONFIRMATION substrate AS A NEW CANDIDATE alongside /036 + /037 + /040 PROMISING substrates; multi-seed validates 4-cohort uniform tighten + min_data_in_leaf=50 | Density-lift mechanism CONFIRMED at single-seed; multi-seed validation determines compoundability vs /036/037/040 |
| **PROMISING-CLEAN** (Δ ∈ [+0.10, +0.30)) | /041 enters /044 candidate list (same as above) | Density lift > noise penalty; consistent with H1 modal prior |
| **PROMISING-INERT-FAV** (Δ ∈ [+0.05, +0.10)) MODAL | /041 informational ONLY; /044 substrate uses /036 + /037 + /040 candidates; /041 deferred to /045+ if /044 produces a merge ingredient | Marginal additive lift not strong enough to bundle at /044 budget |
| **INERT** (Δ ∈ [−0.05, +0.05)) | /041 axis CLOSED; uniform tighten is mechanism-empty | √N count gain canceled by noise — labeling family REFUTED in TIGHTEN direction at uniform width |
| **NEG-CLEAN** (Δ ∈ [−0.30, −0.05)) | /041 axis CLOSED; uniform tighten REFUTED | min_data_in_leaf=50 mitigation under-shoots; cycle-6 may re-attempt only with per-cohort or per-regime variants |
| **NEG-CAT** (Δ < −0.30) OR F-AXIS #5 < 35% | /041 axis CLOSED for v1 PERMANENTLY; add to dead-paths catalog | Chop-noise dominance empirically confirmed; uniform triple-barrier TIGHTEN at v1 8h cadence is structurally CLOSED |
| **NEG-WIRING / NEG-MECHANICAL** | BLOCK-PENDING-FIX one rerun chance | Defect resolution then re-evaluate per /041 spec |

**Prediction for /041's role in /044 substrate**: combined PROMISING-tail probability 40% (15% CLEAN + 22% INERT-FAV + 3% EXCEPTIONAL). The MODAL prediction is INERT-FAV (22%) — meaning /041's most likely outcome is **NOT adding to /044 substrate but filling the 8/10 cadence slot WITHIN scope**. Density-lift mechanism is structurally plausible but the chop-noise mitigation is the binding constraint, and at single-seed=42 EXPLORATION budget the basin draw is more likely to land in the marginal-positive INERT-FAV band than the bundleable PROMISING-CLEAN band. If /041 lands NEG-CAT (22% probability), the labeling family has 2 consecutive NEG outcomes in cycle-5 (/035 NEG-CAT + /041 NEG-CAT) and is effectively CLOSED for cycle-5; /042/043 must rotate to NON-labeling axes.

---

## Section 13 — Phase 5.5 Dispatch Readiness Checklist

- [x] Brief Section 0.0 banner declares EXPLORATION cycle-5 #8/10.
- [x] Brief Section 0.5 cadence position: 8/10 (2 to go before /044).
- [x] Brief Section 0.6 axis-family rotation: VALID; labeling family last used 6 iters ago at /035; same-family counter 2/5; one-sentence rationale present.
- [x] Brief Section 1 hypothesis: 3-sentence (H1) + mechanism (H1a) + falsifier (H1b).
- [x] Brief Section 2 F-AXIS #1 verdict matrix with band probabilities + modal prediction.
- [x] Brief Section 2.5 NORMAL-RISK declared; rationale explicit (width-knob within same source/family vs HIGH-RISK threshold criteria); SINGLE-SEED budget choice justified.
- [x] Brief Section 3 implementation: CLI flags + dispatch elif + min_child_samples lower-bound threading + 12 tests + catch-all exclusion.
- [x] Brief Section 3.2 CLI invocation: full command with all required flags.
- [x] Brief Section 4 F-AXIS #2-#7 falsifiers (wiring, cell-rate density, PnL magnitude, OOS WR LOAD-BEARING, wall-clock, trade-count).
- [x] Brief Section 5 + 6 configuration + wall-clock estimate.
- [x] Brief Section 7 PRE-REGISTERED FAILURE-MODE PREDICTION inline (per /039 lesson — NOT "Expected Report Shape").
- [x] Brief Section 8 LOCKED NUMERICAL MERGE/NO-MERGE THRESHOLDS (per /039 lesson).
- [x] Brief Section 9 BEHAVIORAL PREDICTOR + LIBRARY STACK DECLARATION (per /039 lesson).
- [x] Brief Section 10 anti-cheating self-check.
- [x] Brief Section 11 LM Master Response Map with 4 anticipated recs pre-adjudicated; update-commit discipline noted.
- [x] Brief Section 12 Path Forward predictions per outcome quadrant with /044 routing implication.
- [x] `/030 LESSON`: `"v1-041"` added to baseline catch-all exclusion tuple planned in §3.1.

Ready for Phase 5.5 gate review.

---

**END OF BRIEF**
