# iter-v1/042 — Research Brief

**Iteration**: iter-v1/042
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 9 of 10
**Branch**: `iteration-v1/042`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

**iter-v1/042 — EXPLORATION cycle-5 #9/10**
- **Axis**: MODEL-ARCH — LightGBM → XGBoost head-to-head library swap. Pure
  swap of tree-growth library; ALL else equal (same V1_FEATURE_COLUMNS_PRUNED,
  same triple-barrier σ_t labels, same V1_BASELINE_UNIVERSE 5 cohorts, same
  R1/R2/R3 risk gates, same Sharpe Optuna objective, same abs_pnl sample
  weighting, same walk-forward 24m sacred).
- **Axis family**: `model-arch` — REPEAT after /024 (regime-conditional
  sub-models; cycle-3 #9) and /003 (cycle-1 per-symbol Model A split).
  JUSTIFIED — DIFFERENT MECHANISM CLASS: library swap (algorithmically
  parallel tree-growth + identical scaffolding) vs sub-model partitioning
  (/024) / per-symbol cohorting (/003). The 3 v1 `model-arch` axes test
  STRUCTURALLY ORTHOGONAL hypotheses.
- **Load-bearing purpose**: tests whether the v1 IS basin migration pattern
  observed across /037/038/040 (consistent `n_effective_trials=9` and basin
  reshuffling under single-seed n_trials=18) is library-specific to
  LightGBM's leaf-wise + GOSS growth, OR a property of the 44-col stack
  itself. XGBoost's depth-wise level-wise growth at `tree_method='hist'`
  with NO GOSS gradient sampling is the MOST CONSERVATIVE 1-knob change
  to the model-arch family available without modifying the data/labels/
  features pipeline.
- **Infrastructure**: XGBoost class + Optuna integration SHIPPED at iter-v3/016
  (commit `a20c54b`); only `--model xgboost` CLI dispatch + v1 runner wiring
  required (NO new algorithmic code in this iteration).

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION **9 of 10** (1 more EXPLORATION /043
  before /044 CONFIRMATION earliest). Prior 8 cycle-5 EXPLORATIONs:
  - /034 NEG-CLEAN LEARNED-NEG (feature-family basis_zscore_30)
  - /035 NEG-CAT-bundle bimodal (labeling trend-scanning 5-cohort)
  - /036 PROMISING-CLEAN (per-cohort-specialization LINK+DOT trend-scan;
    OOS Sharpe +1.7465 — single-seed v1 high)
  - /037 PROMISING-CLEAN (loss-function Sortino 5-cohort; OOS Sharpe +0.8388)
  - /038 NEG-CATASTROPHIC EDA-vindicated (risk-primitive symmetric vol-ceiling)
  - /039 NEG-CATASTROPHIC HYBRID (loss-function × per-cohort-specialization;
    universe-dependence empirical proof)
  - /040 (feature-family composed regime_momentum_signed_5d — in flight)
  - /041 (labeling triple-barrier tighten — in flight)
- **NO kill-switches** (user directive 2026-05-30 + cycle-5 discipline).
- **Wall-clock target**: see Section 6. **XGBoost is structurally 2-3× slower
  than LightGBM at matched walk-forward + ensemble + n_trials configuration**
  (no GOSS gradient sampling means every row enters every iteration). Modal
  ~100-130 min; CONSERVATIVE band 90-150 min; HARD CAP **2h** per cycle-5
  EXPLORATION discipline. **Wall-clock is the load-bearing risk for this
  axis** — see Section 6 for mitigation.

---

## Section 0.6 — Axis-Family Rotation (v1-only) — REPEAT (counter 3/5)

- **Axis family**: `model-arch` REPEAT
  - **Last `model-arch` use**: iter-v1/024 (regime-conditional sub-models),
    18 EXPLORATIONs ago.
  - **Total v1 `model-arch` history**: 2 prior usages — /003 cycle-1
    per-symbol Model A split (NEGATIVE) and /024 cycle-3 regime-conditional
    sub-models (NEGATIVE clean F3-auto-reject + F-AXIS #5 FAIL); /042 is
    counter 3 of 5 across the entire v1 history.
- **Prior 5 EXPLORATION families** (going INTO /042):
  - iter-v1/037: loss-function (PROMISING-CLEAN — Sortino)
  - iter-v1/038: risk-primitive (NEG-CATASTROPHIC — per-symbol vol ceiling)
  - iter-v1/039: loss-function × per-cohort-specialization HYBRID (NEG-CAT)
  - iter-v1/040: feature-family (composed regime_momentum_signed_5d — in flight)
  - iter-v1/041: labeling (triple-barrier tighten — in flight)
- **Rotation status**: **VALID**. None of the prior 5 was `model-arch`.
  The /024 model-arch was 18 iters ago; saturation rule (5+ same family
  must rotate) is NOT armed. Same-family-counter for `model-arch` at 3/5
  v1-wide.
- **STRUCTURALLY DIFFERENT mechanism from /003 + /024**:
  - /003 (cycle-1): SPLIT Model A pooled BTC+ETH into 2 per-symbol models.
    Mechanism: cohort-level partition of the pool. NEGATIVE.
  - /024 (cycle-3): PARTITIONED each cohort's training data by funding-regime
    extremity AND added 2 sub-models per cohort routed by STATELESS regime
    gate at signal-time. Mechanism: data-layer regime partition + wrapped
    multi-model dispatch. NEGATIVE clean (F-AXIS #5 gain-share recurrence
    FAIL 2/3 cohorts + F3 IS-CAT auto-reject).
  - /042 (cycle-5): SWAPS the underlying tree-growth library (LightGBM
    leaf-wise + GOSS → XGBoost depth-wise + `tree_method='hist'`). Same data
    pipeline, same labels, same features, same risk gates, same Optuna
    objective. Mechanism: tree-growth algorithm reorganization at fixed
    training cell. STRUCTURALLY ORTHOGONAL to /003 (cohort partitioning)
    and /024 (data-layer partition + multi-model wrapper) — /042 is a
    pure-library substitution at constant scaffolding.
- **One-sentence rationale**: /042 directly tests whether XGBoost's
  depth-wise + no-GOSS conservatism produces MORE STABLE per-cell trade
  rosters at the same Optuna budget than LightGBM's leaf-wise + GOSS
  greediness — the basin-migration hypothesis from /021/022/037/038/039
  predicts XGBoost's symmetric tree-growth narrows basin-to-basin distance
  under single-seed n_trials=18, which is testable via F-AXIS #5
  (Jaccard ≥ 0.20 with LightGBM anchor) AND F-AXIS #6 (importance Spearman
  ρ ∈ [0.40, 0.75]).

---

## Section 1 — Hypothesis

**H1 (PRIMARY, 3 sentences)**: At v1 EXPLORATION budget (n_trials=18,
ENSEMBLE_SIZE=3, single-seed=42, V1_FEATURE_COLUMNS_PRUNED 43-44 cols),
substituting XGBoost (depth-wise + `tree_method='hist'` + no GOSS) for
LightGBM at constant data/labels/features/risk-gates pipeline produces a
**MORE CONSERVATIVE per-cell trade roster** because depth-wise balanced
trees at `max_depth ∈ [3, 5]` cap per-leaf specialization symmetrically
(≤32 leaves at equal depth) whereas LightGBM's leaf-wise greedily reaches
31 leaves at unequal effective depths 4-7 — the bias-up / variance-down
swap. The direction-of-lift on F1 OOS Sharpe Δ vs baseline +0.6637 is
**regime-dependent**: on Pool A's 11k pooled BTC+ETH bars the variance-down
dominates (PROMISING tail); on LINK/LTC/DOT's ~5k single-symbol bars the
bias-up dominates (NEGATIVE tail). The net portfolio F1 OOS Sharpe Δ
therefore lands in **INERT** modal band [-0.10, +0.10] driven by Pool A's
~46% portfolio weight vs altcoin cohorts' ~54%.

**H1a (mechanism, basin-stability constraint — load-bearing)**:
v1's /021/022/037/038 + /024 single-seed iterations all show LightGBM
basin-migration under small input changes (Jaccard 0.10/0.09 OOS roster
overlap with anchor; `n_effective_trials=9` recurrence across /037/038).
The basin-migration hypothesis predicts that LightGBM's leaf-wise + GOSS
combination greedily relocates the basin to the highest-gain training cell
at each Optuna trial — a HIGH-VARIANCE growth pattern. XGBoost's depth-wise
+ no-GOSS produces symmetric expansion of the tree at each step + every row
contributes gradient at every iteration; this is a LOWER-VARIANCE search
geometry on the same Optuna space. The TESTABLE PREDICTION: Jaccard(XGB OOS
roster, LightGBM anchor OOS roster) ≥ 0.20 across 5 cohorts (F-AXIS #5);
importance Spearman ρ ∈ [0.40, 0.75] (F-AXIS #6, v3/016 observed ρ ≈ 0.56
on 13-feature stack). If both F-AXIS #5 and F-AXIS #6 PASS, XGBoost
delivers the basin-stability mechanism; the F1 outcome then tells us
whether basin-stability is signal-additive or signal-neutral.

**H1b (falsifiable)**: If F-AXIS #1 OOS Sharpe Δ < -0.45 (NEGATIVE-CATASTROPHIC
band) AND F-AXIS #7 OOS MaxDD inflation > 1.5× baseline 40.94% AND
F-AXIS #2 OOS trades < 130 (trade-rate floor), the library-swap axis is
REFUTED at v1 EXPLORATION budget — XGBoost's depth-wise conservatism
SHRINKS the signal-emission surface BELOW the v1 5-cohort universe's
required trade-rate floor, AND the resulting per-trade-weight concentration
inflates MaxDD. /043 does NOT re-attempt this mechanism; cycle-6 may
re-attempt only with (a) raised Optuna budget (n_trials ≥ 35) OR (b)
multi-seed CONFIRMATION budget OR (c) a different XGBoost growth policy
(e.g., `grow_policy='lossguide'` which mimics LightGBM's leaf-wise — but
that defeats the axis purpose).

---

## Section 2 — F-AXIS #1 — F1 OOS Sharpe Δ vs BASELINE_V1 anchor (+0.6637)

**Anchor**: BASELINE_V1 OOS monthly Sharpe **+0.6637** (
`v0.v1-baseline-corrected`, `f8bc12c`). IS Sharpe anchor +0.2829.

| Band | OOS Sharpe Δ vs BASELINE | Verdict subtype |
|---|---|---|
| Δ ≥ +0.30 | exceeds modal upside (OOS ≥ +0.96) | EXPLORATION-PROMISING-CLEAN-EXCEPTIONAL |
| +0.10 ≤ Δ < +0.30 | PROMISING band — variance-down dominates | EXPLORATION-PROMISING-CLEAN |
| +0.05 ≤ Δ < +0.10 | PROMISING-INERT-FAV — Pool A lift partial | EXPLORATION-PROMISING-INERT-FAV |
| -0.10 ≤ Δ < +0.05 | **INERT** (MODAL band) — library-swap basin balance | EXPLORATION-INERT-NO-EFFECT |
| -0.45 ≤ Δ < -0.10 | NEG-CLEAN — depth-wise underfit on altcoin cohorts | EXPLORATION-NEGATIVE |
| Δ < -0.45 | NEG-CAT — v3/016 catastrophic precedent partial transfer | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal band prior (QR-derived from /042 eda_findings.md §5 + recalibrated
for absence of LM Master Phase 4.5)**:

| Verdict class | EDA QR prior | **/042 ADOPTED** | Rationale |
|---|---|---|---|
| PROMISING-CLEAN-EXCEPTIONAL (Δ ≥ +0.30) | 10% | **10%** | LOW prior; published tabular benchmarks (Shwartz-Ziv 2022) show <5% MAE differences between LightGBM and XGBoost on structured data |
| PROMISING-CLEAN (+0.10, +0.30) | 25% | **25%** | Pool A's 11k bars allow depth-wise to outperform leaf-wise; mechanism plausible but cohort-uneven |
| PROMISING-INERT-FAV (+0.05, +0.10) | (combined) | **8%** | Marginal Pool A lift dilutes via altcoin cohorts |
| **INERT (-0.10, +0.05)** | 30% | **32% MODAL** | library-swap at same data/features often produces ≤0.1 Sharpe Δ; ENSEMBLE_SIZE=3 smooths single-trial lottery |
| NEG-CLEAN (-0.45, -0.10) | 20% | **15%** | depth-wise underfit on small altcoin cells dominates Pool A lift |
| NEG-CAT (Δ < -0.45) | 15% | **10%** | v3/016 fired NEG-CAT at -2.53 but v1 has 3 structural attenuators (ENSEMBLE_SIZE=3 vs 1, n_trials=18 vs 10, pooled Pool A vs all-per-symbol cells) |

**Modal band**: INERT (32%) > PROMISING-CLEAN (25%) > NEG-CLEAN (15%) >
NEG-CAT (10%) ≈ PROMISING-EXCEPTIONAL (10%) > PROMISING-INERT-FAV (8%).
Combined PROMISING tail 43% vs combined NEG tail 25%; net expected
E[Δ] ≈ +0.03 (slightly favorable centered near zero).

**Why model balanced** (vs v3/016's strong NEG prior): three regime
amplifiers from v3/016 are STRUCTURALLY ATTENUATED in v1: (a) ENSEMBLE_SIZE
1→3 reduces single-trial basin lottery; (b) n_trials 10→18 raises Optuna
n_eff from ~6 to ~10-12; (c) Pool A's 11k pooled bars are 1.9× v3/016's
largest single-cell — depth-wise's bias/variance tradeoff lands differently.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: Pure library swap. Does NOT change Optuna's training-objective
  domain *contents* (same Sharpe scalar returned per trial, same data, same
  labels, same features, same per-row weight vector, same fold splits, same
  walk-forward boundaries, same risk gates). The training-objective domain
  is "Optuna hyperparameter space → Sharpe scalar". The Optuna search
  dimension drops by 1 (num_leaves no-op under depthwise; 7 hp → 6 hp) but
  the OBJECTIVE remains the same scalar function structure. Per /024 NORMAL-
  vs-HIGH-RISK calibration (model-arch + multi-model + thin partition was
  HIGH-RISK), /042 lacks all three HIGH-RISK amplifiers:
  - No multi-model wrapping (single model class swap, same number of
    models = 4: A pool / C / D / E).
  - No data partitioning (all training rows in cohort feed the model).
  - No new feature, label, gate, or universe change.
  Library-swap is the SAFEST possible model-arch axis variation.
- **Mitigation (optional)**: F-AXIS #5 LOAD-BEARING basin-stability gate
  (Jaccard ≥ 0.20); F-AXIS #6 importance Spearman ρ band [0.40, 0.75] as
  defensive diagnostic.
- **Budget choice**: SINGLE-SEED=42 at v1 EXPLORATION standard
  (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42). No multi-seed opt-in. Per
  v1 EXPLORATION discipline — NORMAL-RISK + 2h cap + 9th of 10 cycle-5
  slots, the single-seed EXPLORATION budget is canonical. If verdict is
  PROMISING (≥ 25% prior), /044 multi-seed CONFIRMATION is mandatory.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Existing XGBoost infrastructure (NO new algorithmic code)

Per `eda_findings.md` §1 inventory: XGBoost strategy class + Optuna integration
SHIPPED at iter-v3/016 (commit `a20c54b`) and verified through Critic FINAL
review. Files already in place at v1 HEAD:

| Artifact | Path | Status |
|---|---|---|
| Strategy class | `src/crypto_trade/strategies/ml/xgb.py` (712 LOC) | SHIPPED, library-agnostic on feature_columns + ensemble_seeds |
| Optuna integration | `src/crypto_trade/strategies/ml/optimization_xgb.py` (396 LOC) | SHIPPED, re-exports label helpers |
| Smoke tests | `tests/strategies/ml/test_xgboost_strategy.py` (219 LOC) | PASSES at v1 HEAD |
| pyproject pin | `xgboost>=2.0,<3.0` | active dep since v3/016 |

**Pinned XGBoost configuration** (locked at iter-v3/016 Critic FINAL):
- `tree_method='hist'` (rules out GPU fallback / version drift)
- `grow_policy='depthwise'` (load-bearing architectural difference)
- `n_jobs=1` (determinism with fixed seed)
- `verbosity=0` (silent)
- `random_state=seed`
- `scale_pos_weight = n_neg / n_pos` (computed per-fit)

**Optuna search space (6 hp, 1 less than LightGBM's 7)**:
- `n_estimators ∈ [50, 500]`
- `max_depth ∈ [3, 5]`
- `learning_rate ∈ [0.01, 0.3]` (log)
- `subsample ∈ [0.5, 1.0]`
- `colsample_bytree ∈ [0.3, 1.0]`
- `min_child_weight ∈ [5, 100]` (replaces LightGBM `min_child_samples`)
- `reg_alpha`, `reg_lambda ∈ [1e-8, 10]` (log)
- `confidence_threshold ∈ [0.50, 0.85]`
- `training_days ∈ [10, 500]` step 10

### Section 3.2 — Code changes required for /042 (5 atomic edits)

**Decision**: NO axis-isolation dispatch elif branch needed. The library
swap is signaled by the existing `--model xgboost` CLI flag, which already
exists in `run_baseline_v3.py` (`run_baseline_v3.py:3149`). The v1 runner
`run_baseline_v1.py` currently has no `--model` flag — it implicitly uses
LightGbmStrategy. The minimal change is to add the `--model` flag + dispatch
in v1.

1. **EDIT** `run_baseline_v1.py` — add `--model` CLI flag (default `lgbm`)
   + `model_type` parameter routed through `run_model()` / `build_lgbm_strategy()`
   factory. Mirror v3 runner's pattern (lines 2243-2377, 3149-3156). When
   `model_type == "xgboost"` instantiate `XgboostStrategy` instead of
   `LightGbmStrategy`. All other parameters identical.
   - Top of file: `from crypto_trade.strategies.ml.xgb import XgboostStrategy`.
   - Argparse: add `--model` with choices `["lgbm", "xgboost"]`, default `"lgbm"`.
   - `build_lgbm_strategy()` (rename → `build_ml_strategy()` if needed, or
     introduce a tiny dispatch wrapper) selects strategy class by `model_type`.
   - Pre-flight dispatch banner when `model_type == "xgboost"`:
     `[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise n_jobs=1 / 44 features / ENSEMBLE_SIZE=3 / n_trials=18`.

2. **EDIT** `run_baseline_v1.py` — add `iteration_label == "v1-042"`
   dispatch branch (~50 lines mirroring /034 dispatch). Pre-flight asserts:
   - `assert args.model == "xgboost"` (this iteration REQUIRES the flag).
   - `assert "regime_momentum_signed_5d" in active_feature_columns OR "basis_zscore_30" in active_feature_columns` (/040 outcome conditional — feature stack must be at /040 post-state OR /040 still has basis_zscore_30 if /040 NEG; do not double-modify feature stack).
   - `assert args.label_mode == "triple_barrier"` (UNCHANGED from baseline).
   - `assert args.optuna_objective == "sharpe"` (UNCHANGED — Sharpe NOT Sortino).
   - `assert args.vol_ceiling_mode == "none"` (UNCHANGED).
   - **ADD `"v1-042"`** to BASELINE catch-all exclusion tuple
     (`feedback_v1_dispatch_baseline_catchall_exclusion.md` per /030 LESSON).

3. **EDIT** `run_baseline_v1.py` `run_model()` signature — accept
   `model_type: str = "lgbm"` kwarg and forward to factory. Default `"lgbm"`
   preserves backward compatibility with /034-/041 dispatch branches that
   do not pass this kwarg.

4. **EDIT** `src/crypto_trade/strategies/ml/xgb.py` (if needed) — verify
   that `feature_columns` parameter is honored (per
   `feedback_explicit_feature_columns.md` mandate). The existing v3
   implementation passes `feature_columns` through; spot-check after Phase
   6.0 Critic pre-flight that no None/empty defaults silently pick up
   columns. If any defect found, FIX BEFORE BACKTEST.

5. **NEW** `tests/test_iteration_v1_042.py` — ≥ 8 tests (Section 10.3).

### Section 3.3 — Feature regeneration

No new features for /042. Feature stack is V1_FEATURE_COLUMNS_PRUNED at
post-/040 state (44 cols if /040 swap merged; 44 cols including
basis_zscore_30 if /040 still in flight at /042 dispatch time — Phase 5.5
gate verifies the actual stack against pre-flight assert in §3.2.2). NO
feature regeneration required.

### Section 3.4 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features \
  --iteration-label v1-042 \
  --exploration \
  --model xgboost \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 42 \
  > logs/iter_v1_042_backtest.log 2>&1
```

### Section 3.5 — Symbols + universe + model config

| Item | Spec |
|---|---|
| Universe | V1_BASELINE_UNIVERSE (BTC/ETH/LINK/LTC/DOT) UNCHANGED |
| Models | A (BTC+ETH, atr_tp=2.9/sl=1.45, R1=OFF, R3=ON), C (LINK, atr_tp=3.5/sl=1.75, R1=ON, R3=ON), D (LTC, atr_tp=3.5/sl=1.75, R1=ON, R3=ON), E (DOT, atr_tp=3.5/sl=1.75, R1=ON, R2=ON, R3=ON) — IDENTICAL to baseline |
| Library | **XGBoost 2.x** (LightGBM substituted) |
| Labels | triple-barrier σ_t EWMA 14d UNCHANGED |
| Features | V1_FEATURE_COLUMNS_PRUNED 44 cols at post-/040 state |
| Sample weight | `abs_pnl` (baseline) |
| Optuna bounds | xgboost-default per `optimization_xgb.py` (6 hp) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE; first 3 of 42, 123, 456) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |

### Section 3.6 — File changes summary

| File | Change | Approx LOC |
|---|---|---|
| `run_baseline_v1.py` | INSERT `--model` flag + `model_type` plumbing + iter-v1/042 elif dispatch + catch-all exclusion add + factory dispatch | +180 |
| `tests/test_iteration_v1_042.py` | NEW | ~130 |
| `src/crypto_trade/strategies/ml/xgb.py` | Spot-check feature_columns plumbing (likely no edit; verify only) | 0 |

Total 2 files, ~310 LOC net (1 NEW, 1 EDIT).

---

## Section 4 — F-AXIS #2 through #7 (mechanism integrity gates)

**F-AXIS #2 — Wiring proof** (LOAD-BEARING):
- Dispatch banner `[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise n_jobs=1 / 44 features / ENSEMBLE_SIZE=3 / n_trials=18` emitted 100% cells.
- `xgb.XGBClassifier` class assertion in `logs/iter_v1_042_backtest.log`.
- `dsr.json` `model_type` tag = `"xgboost"`.
- 4 model cohorts produce trade rosters tagged `model_name ∈ {Model_A_xgboost_pool, Model_C_xgboost_LINK, Model_D_xgboost_LTC, Model_E_xgboost_DOT}` OR equivalent naming convention; engineering report MUST confirm 4 distinct `model_name` values.
- Falsifier: any cell silently falls back to LightGBM → BLOCK-PENDING-FIX (treat as wiring defect).

**F-AXIS #3 — Trade-count band**:
- **Anchor**: BASELINE_V1 IS 621 / OOS 189.
- IS band: **[420, 760]** (±35% — wider than feature-swap because XGBoost's depth-wise conservatism may shrink confidence-threshold-clearing predictions).
- OOS band: **[110, 260]** (±38% modal ~190; LOWER bound 110 is BELOW trade-rate floor 130 — if OOS < 130 BLOCK on trade-rate floor regardless of Sharpe).
- v3/016 precedent: 110 OOS at Top-symbol concentration 4× MaxDD inflation; documented in §6.5 v3/016 catastrophic-amplification.
- Falsifier: OOS trades < 130 → trade-rate floor BLOCK (per `feedback_trade_rate_floor.md`); OOS trades > 260 informational (XGBoost would be MORE aggressive than LightGBM — would falsify depth-wise conservatism mechanism).

**F-AXIS #4 — Per-cohort OOS Sharpe Δ direction**:

| cohort | predicted OOS Δ direction | mechanism rationale |
|---|---|---|
| Pool A (BTC+ETH, 11k pooled bars) | flat to + | depth-wise's variance-down dominates on the largest cell; LightGBM's leaf-wise may have over-specialized on BTC vs ETH cross-asset interactions |
| LINK (5.7k single-symbol) | flat to mild − | depth-wise's bias-up flattens favorable signal; counter-pressure with LightGBM's mid-cell ~180 per-leaf samples |
| LTC (5.7k single-symbol) | flat to mild − | same as LINK |
| DOT (5.0k single-symbol) | mild − | smallest cell; bias-up most likely to dominate |

- Falsifier: if 4/4 cohorts go NEGATIVE OOS Δ → depth-wise underfit mechanism CONFIRMED across all cohorts → reclassify INERT or NEG-CLEAN regardless of F1 magnitude. Per-cohort attribution at single-seed dissolves at multi-seed per `feedback_v3_single_seed_frozen_baseline.md` — single-seed per-symbol directions are diagnostic, not statistical, at EXPLORATION budget.

**F-AXIS #5 — Basin stability via OOS roster Jaccard** (LOAD-BEARING for mechanism):
- Jaccard(XGB OOS roster, LightGBM anchor OOS roster) **≥ 0.20** PASS (supports basin-stability mechanism).
- Jaccard ∈ [0.10, 0.20] → BORDERLINE; mechanism partially supported.
- Jaccard < 0.10 → BASIN-RELOCATION-ARTIFACT (per /039 pattern at 0.0878); the library swap relocated the basin completely, dissolving the mechanism story regardless of F1 magnitude.

**F-AXIS #6 — Feature importance Spearman ρ**:
- ρ(XGB feature_importance, LightGBM anchor feature_importance) ∈ **[0.40, 0.75]** PASS.
- v3/016 observed ρ ≈ 0.56 on 13-feature stack; v1 prediction extrapolates to [0.40, 0.75] band.
- ρ < 0.40 → IMPORTANCE-DIVERGENCE — XGBoost extracted different features; informs mechanism but does NOT BLOCK.
- ρ > 0.75 → IMPORTANCE-OVER-CONVERGENCE — XGBoost behaved exactly like LightGBM at feature-selection level; mechanism not differentiated.

**F-AXIS #7 — OOS MaxDD inflation**:
- **Anchor**: BASELINE_V1 OOS MaxDD = 40.94%.
- Predicted band: **[35%, 60%]** (modal ~45-50%; XGBoost's conservatism → fewer trades → per-trade-weight concentration → modest inflation).
- **Falsifier**: OOS MaxDD > 60% (inflation > 1.5×) → concentration-amplification fired per v3/016 4.26× pattern → reclassify NEG-CAT regardless of F1.

---

## Section 5 — Configuration locks + Risk Mitigation

### Section 5.1 — Configuration locks

- Library = **XGBoost 2.x** (`tree_method='hist'`, `grow_policy='depthwise'`, `n_jobs=1`, `random_state=42`).
- ENSEMBLE_SIZE = 3 inner (V1_EXPLORATION_ENSEMBLE_SIZE; 42, 123, 456 first 3).
- n_trials = 18 (v1 EXPLORATION standard).
- single outer seed = 42.
- training_months = 24 (sacred).
- OOS_CUTOFF = 2025-03-24 (sacred).
- bounds_profile = `v1_pruned` (XGBoost-specific Optuna search space per `optimization_xgb.py`; 6 hp NOT 7).
- Sample weight = `abs_pnl` baseline.
- Optuna objective = Sharpe baseline (NOT Sortino — orthogonal to /037).
- Label mode = triple_barrier (UNCHANGED).
- Vol-ceiling mode = none (UNCHANGED).

### Section 5.2 — Risk Mitigation (R1/R2/R3 UNCHANGED)

| Risk Layer | Status | Rationale |
|---|---|---|
| **R1 Consecutive-SL cool-down** | UNCHANGED (active C/D/E, off A) | Independent of library swap |
| **R2 Drawdown brake** (Model E) | UNCHANGED | Independent |
| **R3 OOD Mahalanobis** | UNCHANGED (active all 4 models, cutoff 0.70, 16 features) | OOD detection is feature-space level, not library-level — XGBoost predictions feed same OOD gate identically |
| **NEW concentration / sizing gate** | NONE | EXPLORATION single-axis; no new risk primitive |

XGBoost's deterministic single-thread execution + fixed `random_state=42` matches LightGBM's reproducibility profile.

---

## Section 6 — Wall-clock estimate (LOAD-BEARING — XGBoost is 2-3× slower)

**5-step scaling**:

- **Anchor**: /040 (matched config: n_trials=18, ENSEMBLE_SIZE=3, 5 syms, 44 cols, single-seed=42) compute ~50 min at LightGBM.
- **XGBoost overhead**: 2-3× LightGBM at matched n_trials × ENSEMBLE_SIZE × walk-forward × cohort cardinality. Reason: depth-wise growth's symmetric tree-expansion has higher per-iteration cost than leaf-wise's "best-split-first" + no GOSS gradient sampling means every row enters every iteration without low-gradient skip. v3/016 measured ~2.4× slowdown on 3-symbol per-cohort cells at n_trials=10.
- **/042 expected**: 50 min × **2.5× modal** = **125 min compute**.
- **Range**: 100-150 min depending on per-cohort cell density (Pool A's 11k bars amplify XGBoost's row-sweep cost more than altcoin 5k cells).
- **Composite scaling factor vs /040**: 2.5× modal, 2.0-3.0× range.

**Total wall-clock**:
- Data fetch: 0 min (klines already on disk).
- Feature regen: 0 min (no new features).
- Backtest compute: **~125 min modal** (range 100-150 min).
- Report layer: ~3 min.

**Modal total: ~130 min (2.17h)** — **EXCEEDS 2h soft EXPLORATION cap**.

**Wall-clock viability assessment**: AT-CAP modal. Conservative band 105-155 min.
**Mitigation options**:
1. **PREFERRED** — accept 2h soft cap overrun (cycle-5 has NO kill-switches per user directive 2026-05-30; 30-min overrun acceptable for first XGBoost run at v1 cell sizes).
2. **DEFENSIVE** — if Phase 5.5 wall-clock concern blocks dispatch, pre-commit to reducing ENSEMBLE_SIZE 3 → 2 (saves 33% compute → ~85 min modal) at cost of single-trial lottery exposure. NOT ADOPTED at brief authoring time; documented as fallback.
3. **REJECT** — reducing n_trials 18 → 10 would put XGBoost at v3/016 budget; matches the regime where v3/016 fired NEG-CAT at -2.53. Per `feedback_v3_inert_features_at_higher_budget.md` doctrine, downsizing budget on a NEW model class is NOT axis-clean. REJECTED.

**Per `feedback_split_engineer_dispatch.md`**: ~130 min wall-clock is well above 30 min threshold → Engineer does setup-only, orchestrator launches detached bash, Engineer writes report when complete.

Honest overrun acceptable; no runtime kill-switch.

---

## Section 7 — Expected report shape

After Phase 6 backtest, expected artifacts at `reports-v1/iteration_v1-042/`:

- `comparison.csv` — 4 model rows (Pool A / C / D / E) IS + OOS + per-symbol; portfolio aggregate row with IS Sharpe + OOS Sharpe + IS/OOS trade counts. Each row should carry `model_type='xgboost'` indicator (or implicit via runner banner).
- `in_sample/trades.csv` — IS trades (expected 420-760).
- `out_of_sample/trades.csv` — OOS trades (expected 110-260; floor 130).
- `feature_importance.csv` — per-cohort gain-based importance rankings for 44 features × 4 models × ~12 walk-forward months. Required for F-AXIS #6 Spearman computation.
- `dsr.json` — DSR + PSR + n_eff (informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`); `model_type` tag = `"xgboost"`.
- `jaccard_overlap.csv` (NEW post-hoc analysis) — Jaccard(XGB OOS roster, LightGBM anchor OOS roster) per cohort + portfolio. Required for F-AXIS #5 evaluation.
- `feature_importance_spearman.csv` (NEW post-hoc analysis) — Spearman ρ(XGB, LightGBM anchor) per cohort. Required for F-AXIS #6.
- Dispatch banner in `logs/iter_v1_042_backtest.log`: `[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise n_jobs=1 / 44 features / ENSEMBLE_SIZE=3 / n_trials=18`.

---

## Section 8 — Path Forward (conditional /043 routing per /042 verdict)

**Conditional routing on F1 verdict**:

- **PROMISING-CLEAN-EXCEPTIONAL (Δ ≥ +0.30)**: HIGHLY UNLIKELY (10% prior). /042 enters /044 CONFIRMATION substrate candidate list (multi-seed XGBoost validates the library swap on v1's 5-cohort universe). /043 = either complementary axis to test stacking with /042's gains OR sanity slot.
- **PROMISING-CLEAN (Δ ∈ [+0.10, +0.30))**: 25% prior. /042 enters /044 substrate as 4th candidate alongside /036 + /037 + (potential /040). Multi-seed CONFIRMATION at /044 verifies basin-stability mechanism survives multi-seed. /043 = NEW EXPLORATION (NOT model-arch; rotation discipline).
- **PROMISING-INERT-FAV (Δ ∈ [+0.05, +0.10))**: 8% prior. /042 axis informational; /043 = NEW EXPLORATION (NOT model-arch).
- **INERT (Δ ∈ [-0.10, +0.05)) MODAL**: 32% prior. XGBoost library-swap is mechanism-empty at v1 EXPLORATION budget; library choice does NOT change the v1 alpha at single-seed n_trials=18. Axis CLOSED at single-seed budget; cycle-6 may re-attempt only at multi-seed CONFIRMATION budget. /043 = NEW EXPLORATION from cycle-5 menu — labeling width asymmetry per LM Master /038 §6 Rec 2 (next-priority axis if /041 INERT/NEG) OR cross-symbol correlation gate (untouched).
- **NEG-CLEAN (Δ ∈ [-0.45, -0.10))**: 15% prior. depth-wise underfit on altcoin cohorts confirmed; XGBoost at v1 single-seed REFUTED. Axis CLOSED. /043 = NEW EXPLORATION.
- **NEG-CAT (Δ < -0.45)**: 10% prior. v3/016 catastrophic precedent partially transferred. Axis CLOSED PERMANENTLY for v1 single-seed; cycle-6 re-attempt requires multi-seed CONFIRMATION budget AND raised n_trials ≥ 35.

**Alternative axes from non-model-arch for cycle-5 slot #10** (per constructive-Critic Path Forward discipline — /043 candidates conditional on /042 outcome):

1. **LABELING** (last used /041 — but if /041 NEG, family CLOSED for cycle-5; if /041 INERT/PROMISING, /043 could explore per-cohort labeling asymmetry as orthogonal):
   - LM Master /038 §6 Rec 2 (LABELING width asymmetry — TP=1.5/SL=0.75) — but this is approximately what /041 tests; if /041 already in flight, family saturated.
2. **CROSS-SYMBOL-CORRELATION GATE** (untouched in v1 cycle-5):
   - Add a gate that filters trades when cross-symbol correlation regime is high (BTC-LTC corr_30 > 0.85), motivated by /024 cross-cohort overlap evidence (LINK+LTC 0.30 Pearson).
   - Family: `risk-primitive` REPEAT but DIFFERENT mechanism class (stateless cross-asset gate vs /038 per-symbol vol ceiling).
3. **SAMPLE-WEIGHTING isolation refresh** (/031 PROMISING-BASIN-RELOCATION-ARTIFACT revisit at multi-seed pre-CONFIRMATION — NOT currently scheduled; would require user authorization).
4. **METHODOLOGY-PIVOT** family — Conformal prediction calibration on top of XGBoost (if /042 PROMISING) — turns the basin-stability gain into a calibrated confidence interval. Defer to /044+ CONFIRMATION composition.

---

## Section 9 — Behavioral Predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted IS trade count change**: -10% to +20% from baseline 621 IS trades (range [560, 745], wider band [420, 760] including v3/016 trade compression at altcoin cohorts). XGBoost's depth-wise conservatism + 1-fewer Optuna dimension may produce a different basin near baseline confidence_threshold. Per /024 catalog evidence (sub-model architectures can both shrink and inflate IS trades), the direction is uncertain at single-seed.

**Predicted OOS trade count change**: -25% to +10% from baseline 189 OOS trades (range [140, 210], wider band [110, 260] documented for trade-rate-floor edge cases). XGBoost's conservatism is more visible at OOS where it manifests as fewer high-confidence emissions.

**Predicted OOS Sharpe Δ**: range [-0.45, +0.30], modal **+0.03** (INERT centered slightly positive per QR priors in F-AXIS #1). Probability of clearing trade-rate floor (OOS ≥ 130): ~85%.

**Predicted F-AXIS #4 per-symbol OOS Δ direction**:
- BTC (in Pool A): flat to mild +
- ETH (in Pool A): flat to +
- LINK: flat to mild −
- LTC: flat to mild −
- DOT: mild −

**Predicted F-AXIS #5 Jaccard(XGB, LightGBM)**: range [0.10, 0.35], modal **0.22**. Mechanism-supportive PASS at the 0.20 threshold is the modal outcome. Jaccard < 0.10 would empirically refute the basin-stability mechanism story.

**Predicted F-AXIS #6 importance Spearman ρ**: range [0.30, 0.80], modal **0.55** (close to v3/016's 0.56). Inside the band [0.40, 0.75] PASS.

**Predicted F-AXIS #7 OOS MaxDD inflation**: range [1.00×, 1.50×] baseline 40.94%, modal **1.15×** (i.e., 47% OOS MaxDD). Outside 1.5× → concentration-amplification fired.

**FALSIFIERS**:
1. If OOS trades < 130 → trade-rate floor BLOCK per `feedback_trade_rate_floor.md`; reclassify NEG-WIRING regardless of F1 magnitude.
2. If F-AXIS #5 Jaccard < 0.10 → BASIN-RELOCATION-ARTIFACT confirmed → mechanism story dissolved; reclassify INERT regardless of F1.
3. If F-AXIS #7 OOS MaxDD inflation > 1.5× → concentration-amplification confirmed → reclassify NEG-CAT regardless of F1.
4. If F-AXIS #2 wiring fails (banner missing OR `XGBClassifier` not used in any cell) → BLOCK-PENDING-FIX.
5. If wall-clock > 150 min (CONSERVATIVE upper bound) → soft alarm in diary; not a BLOCK criterion (no kill-switches per cycle-5 directive).

**Mechanism failure scenario (PREDICTED MOST PLAUSIBLE FAILURE MODE)**:
INERT-no-effect via library-swap basin balance. XGBoost's depth-wise produces
trade rosters that are ~25% disjoint from LightGBM at the same Optuna budget
(Jaccard ~0.25), but the new roster's OOS Sharpe lands within ±0.10 of
baseline because (a) Pool A's variance-down gain on pooled BTC+ETH cell is
offset by (b) altcoin cohorts' bias-up flattening of favorable signal.
F-AXIS #5 PASSES at 0.22, F-AXIS #6 PASSES at 0.55, F1 lands INERT at +0.02.
Mechanism is mildly supported (basin-stability gain present) but signal-
neutral → library swap is not a load-bearing edge ingredient.

---

## Section 10 — Symbol Exclusion + Reproducibility + Test Mandate

### Section 10.1 — Symbol exclusion

V1_BASELINE_UNIVERSE UNCHANGED (BTC/ETH/LINK/LTC/DOT). V1_EXCLUDED_SYMBOLS
unchanged.

### Section 10.2 — Reproducibility

- Single outer seed = 42 (baseline canonical)
- ENSEMBLE_SIZE = 3 inner seeds (42, 123, 456 first 3 per V1_EXPLORATION_ENSEMBLE_SIZE)
- XGBoost: `n_jobs=1` + `random_state=outer_seed` (deterministic per cell)
- Optuna sampler: TPE with random_state=outer_seed (deterministic per cell)
- Walk-forward: monthly retrain, training_months=24 (sacred), embargo via walk_forward.py:113 fix
- XGBoost 2.x pinned via `pyproject.toml` (`xgboost>=2.0,<3.0`)

Two re-runs from clean checkout must produce bit-identical trades.csv per
`feedback_deterministic_trade_match.md`.

### Section 10.3 — Test mandate (≥ 8 tests)

`tests/test_iteration_v1_042.py`:
1. `test_v1_042_runner_accepts_model_xgboost_flag` — argparse accepts `--model xgboost` and routes to XgboostStrategy.
2. `test_v1_042_dispatch_branch_exists` — runner code path `iteration_label == "v1-042"` is reachable (existence check via `inspect.getsource(run_baseline_v1)`).
3. `test_v1_042_in_baseline_catchall_exclusion` — runner BASELINE catch-all tuple contains `"v1-042"` per /030 LESSON.
4. `test_v1_042_dispatch_banner_emitted` — runner with `iteration_label="v1-042"` + `--model xgboost` prints `[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise n_jobs=1 / 44 features / ENSEMBLE_SIZE=3 / n_trials=18`.
5. `test_v1_042_xgboost_pinned_config` — instantiated XgboostStrategy carries `tree_method='hist'`, `grow_policy='depthwise'`, `n_jobs=1`, `random_state=42`.
6. `test_v1_042_xgboost_feature_columns_honored` — XgboostStrategy receives explicit `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` per `feedback_explicit_feature_columns.md`; raises if None/empty.
7. `test_v1_042_xgboost_optuna_search_space_6hp` — `optimize_and_train_xgb` Optuna search space has 6 hyperparameters (NOT 7; num_leaves dropped per depthwise no-op).
8. `test_v1_042_lgbm_path_unchanged` — passing `--model lgbm` (or omitting flag) preserves baseline LightGbmStrategy behavior bit-identically (regression-prevention for /034-/041 dispatch branches that DO NOT pass `model_type`).
9. *(stretch)* `test_v1_042_xgboost_smoke_run_one_cohort` — XgboostStrategy runs end-to-end on 1 cohort (Pool A) for 1 month walk-forward at n_trials=2 ENSEMBLE_SIZE=1 to verify no runtime error; ~10s test.

**ALL 8 tests (9 with stretch) must pass at Phase 6 before backtest launch.**

### Section 10.4 — Anti-cheating self-check

- IS-only window for ALL Phase 1-5 EDA work (EDA findings in `analysis/iteration_v1-042/` if any; XGBoost infrastructure pre-vetted at iter-v3/016 — no new EDA dependency on data).
- OOS data NOT inspected during Phases 1-5.
- IS window NOT trimmed.
- training_months = 24 sacred; OOS_CUTOFF_MS sacred.
- XGBoost configuration `tree_method='hist'`, `grow_policy='depthwise'`, `n_jobs=1` LOCKED at iter-v3/016 Critic FINAL; not tuned for /042.
- Optuna search space frozen at `optimization_xgb.py` defaults (NOT modified for /042).
- Single-axis isolation discipline: ONLY library swap changes. Feature stack, labels, universe, risk gates, sample weighting, Optuna objective all UNCHANGED.

### Section 10.5 — Phase 5.5 dispatch readiness

- Brief committed at HEAD.
- EDA findings committed at `briefs-v1/iteration_v1-042/eda_findings.md` (Phase 1 deliverable; XGBoost infrastructure pre-vetted).
- LM Master Phase 4.5 advisory NOT YET PRESENT at brief authoring time; Section 11 below pre-adopts the most-likely LM Master recommendations and will be UPDATED in a follow-up commit if the actual Phase 4.5 advisor diverges materially.
- BASELINE catch-all exclusion tuple ADD planned (Phase 6 first commit).
- Test suite mandate documented (8-9 tests).
- Wall-clock target ~130 min modal — AT-CAP against 2h soft cap; cycle-5 NO kill-switches per user directive accepts overrun.
- NORMAL-RISK declared; single-seed=42 at v1 EXPLORATION standard.

Ready for Phase 6.0 Critic pre-flight.

---

## Section 11 — LM Master Response Map (anticipated; will UPDATE if actual lgbm_advisor.md diverges)

**Status**: `briefs-v1/iteration_v1-042/lgbm_advisor.md` is NOT YET PRESENT at
brief authoring time. Phase 4.5 LM Master advisor is expected to fire
SEPARATELY at /042 dispatch. This Section 11 pre-adopts the four most-likely
LM Master recommendations based on the /024 + /037/038/040/041 model-arch
adjacency patterns and will be UPDATED in a follow-up commit if the actual
Phase 4.5 advisor diverges materially (per v1 skill discipline).

| # | Anticipated LM Master recommendation | QR pre-adjudication | Reason |
|---|---|---|---|
| 1 | Mechanism prediction — XGBoost depth-wise is bias-up / variance-down vs LightGBM leaf-wise; predict regime-dependent outcome — variance-down dominates on Pool A's 11k bars, bias-up dominates on altcoin 5k cells; net portfolio INERT modal | **ADOPTED** | Pre-registered as H1 + H1a + H1b in §1; F-AXIS #4 per-cohort attribution + F-AXIS #5 basin-stability + F-AXIS #6 importance Spearman are the load-bearing mechanism gates. |
| 2 | Budget — `n_trials=18` + `ENSEMBLE_SIZE=3` + single-seed=42 ADEQUATE; do NOT raise. XGBoost's slower per-trial cost (2-3×) makes raising n_trials wall-clock-prohibitive AND axis-impure (n_trials is a confounding variable on top of library swap). HOLD baseline EXPLORATION budget. | **ADOPTED** | Config locked at §3.5: n_trials=18, ENSEMBLE_SIZE=3, single-seed=42. |
| 3 | Pinned XGBoost configuration UNCHANGED from iter-v3/016 — `tree_method='hist'`, `grow_policy='depthwise'`, `n_jobs=1`, `scale_pos_weight=n_neg/n_pos` (per-fit). Do NOT swap to `grow_policy='lossguide'` (which mimics LightGBM's leaf-wise — defeats axis purpose). | **ADOPTED** | Config locked at §3.1: pinned XGBoost configuration UNCHANGED from iter-v3/016 Critic FINAL. |
| 4 | F-AXIS falsifier recommendations — keep F1 OOS Δ as primary, F-AXIS #5 Jaccard as LOAD-BEARING basin-stability mechanism gate, F-AXIS #6 importance Spearman as defensive diagnostic, F-AXIS #7 MaxDD inflation as concentration-amplification gate. | **ADOPTED** | F-AXIS #5 + #6 + #7 explicit in §4. |
| 5 *(potential)* | Wall-clock concern — recommend ENSEMBLE_SIZE 3 → 2 fallback to control 2h overrun risk | **CONDITIONAL ADOPT** | Documented in §6 as DEFENSIVE fallback; NOT ADOPTED at brief authoring time per cycle-5 NO-kill-switches directive accepting overrun. If LM Master flags this as a HARD recommendation, will revisit. |

If Phase 4.5 LM Master advisor surfaces a recommendation NOT in this set
(e.g., a specific alternative `grow_policy` calibration, or `tree_method='approx'`
exploration, or feature subset for XGBoost specifically), Section 11 will be
UPDATED in a separate commit BEFORE Phase 6 dispatch per v1 skill 4.5 → 5
reconciliation discipline.

---

## Section 11.5 — Pre-Registered Failure-Mode Prediction (per /039 lesson)

**Most plausible failure mode at single-seed=42 EXPLORATION budget**:
INERT-no-effect via library-swap basin balance (32% modal prior).

XGBoost's depth-wise + no-GOSS combination produces a per-cohort trade roster
that is ~25% disjoint from LightGBM (Jaccard ~0.22, mechanism-supportive
PASS at 0.20 threshold). On Pool A's 11k pooled BTC+ETH cell, the
variance-down gain produces a marginal IS Sharpe lift (+0.03 to +0.08) and
a similar OOS Sharpe lift. On LINK/LTC/DOT's ~5k single-symbol cells, the
bias-up cost flattens favorable signal — IS Sharpe contracts -0.05 to
-0.10 per cohort, OOS Sharpe similar. The portfolio-weighted net F1 OOS Δ
lands at ~+0.03 (INERT modal). F-AXIS #5 PASSES at 0.22 (basin-stability
mechanism supported); F-AXIS #6 PASSES at 0.55 (importance ρ near v3/016).
Mechanism is mildly supported but signal-neutral; library swap is NOT a
load-bearing edge ingredient.

**Second failure mode**: NEG-CAT via v3/016 partial transfer (10% prior).
If altcoin cohort bias-up dominates more than predicted AND Pool A's
variance-down does NOT compensate, F1 lands below -0.45 with OOS trades
near floor 130 and OOS MaxDD > 1.5× baseline. F-AXIS #7 inflation fires
(concentration-amplification per v3/016 4.26× pattern); F-AXIS #2 trade-
rate floor borderline. Diagnostic signature: per-symbol OOS Δ NEGATIVE in
4/4 cohorts including Pool A (no variance-down gain materialized).

**Third failure mode**: Wall-clock overrun > 150 min triggering Phase 6.0
re-evaluation of ENSEMBLE_SIZE fallback. NOT a BLOCK criterion per cycle-5
NO-kill-switches; but documented for honest accounting in Phase 8 diary.

**Diagnostic signatures**:
- INERT-no-effect: F-AXIS #5 PASS at ~0.22, F-AXIS #6 PASS at ~0.55, F1 ∈ [-0.10, +0.10), per-symbol OOS Δ direction mixed (Pool A + / altcoins flat-mild −), OOS trades inside [140, 210].
- NEG-CAT: F-AXIS #5 PASS or FAIL inconclusive, F1 < -0.45, OOS MaxDD > 60%, OOS trades borderline 110-140, per-symbol OOS Δ NEGATIVE 4/4.
- PROMISING-CLEAN: F-AXIS #5 PASS ≥ 0.25, F-AXIS #6 PASS ∈ [0.40, 0.75], F1 ∈ [+0.10, +0.30], OOS trades [170, 220], Pool A OOS Δ leads with +.

---

## Section 11.6 — Locked Numerical MERGE/NO-MERGE Thresholds (per /039 lesson)

EXPLORATION at single-seed = NO direct MERGE. MERGE eligibility requires
/044 multi-seed CONFIRMATION. Pre-registered thresholds for /042 routing
to /044 substrate selection:

| Outcome band | Threshold | /044 routing |
|---|---|---|
| **PROMISING-CLEAN-EXCEPTIONAL** | OOS Sharpe Δ ≥ +0.30 AND F-AXIS #2 PASS AND F-AXIS #5 Jaccard ≥ 0.20 AND F-AXIS #6 ρ ∈ [0.40, 0.75] AND F-AXIS #7 MaxDD inflation ≤ 1.5× | /042 enters /044 CONFIRMATION substrate candidate list (multi-seed XGBoost validation on 5-cohort universe) |
| **PROMISING-CLEAN** | +0.10 ≤ OOS Δ < +0.30 AND F-AXIS gates PASS | /042 enters /044 substrate list alongside /036 + /037 + (potential /040 + /041) PROMISING substrates |
| **PROMISING-INERT-FAV** | +0.05 ≤ OOS Δ < +0.10 AND F-AXIS gates PASS | /042 axis informational; /044 substrate uses other PROMISING candidates; /042 deferred to /045+ if /044 mass-merges |
| **INERT** | -0.10 ≤ OOS Δ < +0.05 | /042 axis CLOSED at single-seed EXPLORATION budget; library choice is mechanism-empty at v1 |
| **NEG-CLEAN** | -0.45 ≤ OOS Δ < -0.10 | /042 axis CLOSED for cycle-5; XGBoost depth-wise underfit on altcoins REFUTED at single-seed |
| **NEG-CAT** | OOS Δ < -0.45 OR F-AXIS #7 MaxDD inflation > 1.5× OR F-AXIS #2 OOS trades < 130 | /042 axis CLOSED for v1 PERMANENTLY at single-seed; cycle-6 may only re-attempt at multi-seed CONFIRMATION budget AND raised n_trials ≥ 35; add to dead-paths catalog "XGBoost depth-wise library swap at v1 single-seed EXPLORATION budget" → REFUTED |
| **NEG-WIRING / NEG-MECHANICAL** | F-AXIS #2 wiring banner missing OR `XGBClassifier` not used in any cell OR test suite FAIL | BLOCK-PENDING-FIX with ONE rerun chance per v1 skill |

**ABSOLUTE MERGE GATES** (apply at /044 CONFIRMATION only, NOT /042):
- IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- OOS/IS ratio ≥ 0.5
- OOS trades ≥ 130 total (≥ 10/month)
- DSR > 0.95 (CONFIRMATION-mode, n_trials ≥ 35)
- PBO < 0.40
- PSR > 0.95
- Top-symbol concentration ≤ 30% of OOS PnL
- 10-seed validation (mean Sharpe > 0, ≥ 7/10 profitable) per `feedback_seed_validation.md`

/042 EXPLORATION does NOT evaluate against these gates. Forward-declared
per pre-registration discipline to eliminate post-hoc rationalization at
/044 brief.

---

## Section 11.7 — Library Stack Declaration (XGBoost ≥ 2.0)

| Library | Version | Role | Available? |
|---|---|---|---|
| **xgboost** | **≥ 2.0, < 3.0** (pinned in `pyproject.toml`) | **PRIMARY model library — /042 axis** | YES (active dep since iter-v3/016) |
| lightgbm | ≥ 4.0 (installed in venv) | LightGBM baseline comparison anchor (NOT used in /042 backtest; used in BASELINE_V1 anchor only) | YES |
| optuna | ≥ 3.0 (installed in venv) | Hyperparameter search | YES |
| numpy | ≥ 1.24 (installed in venv) | Numerical computation | YES |
| pandas | ≥ 2.0 (installed in venv) | DataFrame manipulation | YES |
| pyarrow | ≥ 14 (installed in venv) | Parquet I/O | YES |
| scipy.stats | installed with scipy | ADF + statistical tests (reporting layer; not in runner) | YES |
| mlfinlab | N/A | NOT USED | N/A |
| mlfinpy | N/A | NOT USED | N/A |
| pypbo | N/A | NOT USED | N/A |
| fracdiff | N/A | NOT USED | N/A |

**XGBoost implementation**: pre-vetted at iter-v3/016 Critic FINAL (commit
`a20c54b`); 712 LOC `xgb.py` + 396 LOC `optimization_xgb.py` + 219 LOC
`test_xgboost_strategy.py`. The /042 axis does NOT modify any of these
files — only adds `--model xgboost` dispatch in `run_baseline_v1.py`.
**XGBoost 2.x pinned**: prevents version drift; `tree_method='hist'` rules
out GPU fallback ambiguity.

**No fallbacks required**: all libraries pre-installed in the project venv.
No mlfinlab licensing risk. No fracdiff version conflict. No new dependency
added.

**Determinism reproducibility**: XGBoost 2.x with `n_jobs=1` + `tree_method='hist'`
+ `random_state=seed` produces deterministic output across two re-runs from
clean checkout. Verified at iter-v3/016 + matched against
`feedback_deterministic_trade_match.md` requirement.

---

## Section 12 — Phase 5.5 Dispatch Readiness Checklist

- [x] Brief Section 0.0 banner declares EXPLORATION cycle-5 #9/10.
- [x] Brief Section 0.5 cadence position: 9/10 (1 to go before /044).
- [x] Brief Section 0.6 axis-family rotation: VALID; model-arch family last used /024 (18 iters ago); same-family counter 3/5; one-sentence rationale present.
- [x] Brief Section 1 hypothesis: 3-sentence (H1) + mechanism (H1a) + falsifier (H1b).
- [x] Brief Section 2 F-AXIS #1 verdict matrix with band probabilities + modal prediction.
- [x] Brief Section 2.5 NORMAL-RISK declared; rationale explicit; SINGLE-SEED budget choice justified.
- [x] Brief Section 3 implementation: CLI flags + dispatch elif + factory dispatch + 8 tests + catch-all exclusion.
- [x] Brief Section 3.4 CLI invocation: full command with all required flags including `--model xgboost`.
- [x] Brief Section 4 F-AXIS #2-#7 falsifiers (wiring, trade-count, per-cohort, basin Jaccard LOAD-BEARING, importance Spearman, MaxDD inflation).
- [x] Brief Section 5 + 6 configuration + wall-clock estimate (AT-CAP 130 min modal).
- [x] Brief Section 7 expected report shape inline.
- [x] Brief Section 8 Path Forward (conditional /043 routing per verdict).
- [x] Brief Section 9 BEHAVIORAL PREDICTOR per `feedback_v3_axis_saturation_predictor.md`.
- [x] Brief Section 10 anti-cheating self-check + test mandate (8-9 tests).
- [x] Brief Section 11 LM Master Response Map with 4-5 anticipated recs pre-adjudicated; update-commit discipline noted.
- [x] Brief Section 11.5 Pre-Registered Failure-Mode Prediction (per /039 lesson).
- [x] Brief Section 11.6 LOCKED NUMERICAL MERGE/NO-MERGE THRESHOLDS (per /039 lesson).
- [x] Brief Section 11.7 LIBRARY STACK DECLARATION (XGBoost ≥ 2.0 primary; per /039 lesson).
- [x] `/030 LESSON`: `"v1-042"` added to baseline catch-all exclusion tuple planned in §3.2.2.

Ready for Phase 5.5 gate review.

---

**END OF BRIEF**
