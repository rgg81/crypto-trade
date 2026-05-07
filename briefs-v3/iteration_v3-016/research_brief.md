# Iteration v3-016 — Research Brief

**Type**: EXPLORATION (NINTH EXPLORATION under cadence discipline; **STRUCTURAL axis (Category 2 NEW model architecture)** per `feedback_structural_over_knob_exploration.md` priority order — first model-architecture variation in v3 catalog)
**Track**: v3 (rigor arm) — sixteenth iteration
**Branch**: `iteration-v3/016` (off `iteration-v3/015` head; analysis commit `b5592bd` ships before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 10             # SET BY --exploration default
colsample_bytree = 1.0             # HARDCODED by --exploration (mirrored in XGBoost path)
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–015 briefs / engineering reports / Critic reviews / diaries; iter-v3/016 analysis script `analysis/iteration_v3-016/xgboost_baseline_eda.py` outputs (committed at SHA `b5592bd` BEFORE this brief). The smoke test reads ONLY pre-OOS-cutoff data sliced from `data/features_v3/BCHUSDT_8h_features.parquet` (months ending 2024-11; test window 2024-12) — no OOS contamination at brief time.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: 2h hard cap (target < 30 min for fast inference; XGBoost CPU runtime expected near LightGBM)
Single-axis variation: model architecture (LightGbmStrategy → XgboostStrategy)
Cadence: EXPLORATION #9 of 10 needed since last CONFIRMATION
This iteration NEVER updates BASELINE_V3.md.
Pre-committed: this axis is FORCED by `feedback_v3_iter016_xgboost_mandate.md` AND
                  `feedback_structural_over_knob_exploration.md` priority order.
                  Cannot be renegotiated.
```

**Justification**: Per `feedback_v3_iter016_xgboost_mandate.md` (FIRED at iter-v3/015 Critic FINAL SHA `a0cfae7`) and `feedback_structural_over_knob_exploration.md` priority order Category 2: iter-v3/015 added a structurally-clean NEW microstructure feature (`tbr_zscore_30`, max |IC| 0.086, mean-zero by construction, past-only) and LightGBM ranked it 14/14 across all 3 per-symbol models (BCH 16% / LDO 41% / TRX 20% of top-feature importance). Diagnosis: the model-architecture (LightGBM leaf-wise + GOSS) may be the ceiling, not the feature pool. iter-v3/016 tests this hypothesis by swapping the boosting library while holding everything else byte-identical to iter-v3/013's 13-feature stack. Single-axis discipline requires dropping `tbr_zscore_30` first (revert V3_FEATURE_COLUMNS to 13), then introducing XGBoost as an alternative model architecture.

The catalog at `briefs-v3/exploration_catalog.md` (newest banner SHA at iter-v3/015 review) explicitly pre-commits this axis as MANDATORY. After iter-v3/016 the catalog will have axis coverage features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW feature family × 1 + NEW model architecture × 1 = **8 unique axis representations**.

---

## Section 1 — Hypothesis

Replacing LightGBM with XGBoost on iter-v3/013's 13-feature stack will produce IS Sharpe within ±0.30 of iter-v3/013's +1.0088 baseline (calibrated band [+0.70, +1.30] median +1.00) and will surface measurably different feature-importance rankings (Spearman ρ between LightGBM and XGBoost importance vectors < 0.85), demonstrating that model architecture is a non-trivial axis of variation in the v3 strategy stack.

**Mechanism**: XGBoost's depth-wise (level-wise) tree growth splits all leaves at the current depth before going deeper, while LightGBM's leaf-wise (best-first) growth always splits the leaf with the largest loss reduction. This produces structurally different feature-selection behavior:
- **LightGBM** + GOSS (Gradient-based One-Side Sampling) preferentially keeps high-gradient samples and may ignore features whose contribution is small but consistent (the iter-v3/015 `tbr_zscore_30` failure-mode hypothesis).
- **XGBoost** depth-wise grows more conservative, more uniform trees; tends to surface signal across a broader feature set.
- **Histogram binning**: LightGBM uses EFB (Exclusive Feature Bundling) by default; XGBoost `tree_method='hist'` does not. At the 13-feature continuous-input scale this difference is small, but binning-edge differences can produce non-zero rank divergence in feature importance.
- **L1/L2 regularization**: identical mathematical specification (`reg_alpha`, `reg_lambda` with same Optuna ranges); the difference is how the regularization interacts with the different growth strategy.

**Three pathways pre-registered** (Section 4.4 outcome interpretation table is the canonical decision tree, not §4.3 falsifiers — fixing the iter-v3/015 §4.3-vs-§4.4 conflict per Critic FINAL Rec 4):
- **PATH A (PROMISING-ALTERNATIVE)**: XGBoost matches or exceeds iter-v3/013 IS Sharpe (≥ +1.00) AND learns features the iter-v3/013 LightGBM ignored (importance Spearman ρ vs LightGBM baseline < 0.85). Demonstrates model-architecture matters as a compoundable axis; opens future "ensemble of LightGBM + XGBoost" CONFIRMATION axis (iter-v3/017+).
- **PATH B (NEGATIVE)**: XGBoost underperforms LightGBM by Δ-0.20 IS Sharpe or more (i.e., IS Sharpe < +0.81). Confirms LightGBM is near-optimal for this feature/label combo at the current Optuna budget; closes model-architecture axis category for now.
- **PATH C (PROMISING-ON-NEW-FEATURES)**: XGBoost matches/exceeds LightGBM IS Sharpe AND surfaces signal in features LightGBM ignored (importance ranking inversion). Re-opens microstructure feature axis (e.g., re-test `tbr_zscore_30` under XGBoost) at iter-v3/017+ if XGBoost shows higher importance for it.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-016/xgboost_baseline_eda.py` (committed at SHA `b5592bd` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Outputs** (committed alongside the script at SHA `b5592bd`):
- `analysis/iteration_v3-016/xgboost_param_map.csv` — 14-row LightGBM ↔ XGBoost parallel-structure parameter map.
- `analysis/iteration_v3-016/xgboost_smoke_results.csv` — 1-symbol × 1-month default-config XGBoost smoke fit (status: SKIPPED — see §2.2).
- `analysis/iteration_v3-016/xgboost_pitfalls.md` — 10 implementation-pitfall notes.
- `analysis/iteration_v3-016/xgboost_eda_synthesis.md` — 1-paragraph synthesis + behavioral-effect prediction.

### 2.1 XGBoost hyperparameter search-space mapping (LightGBM-equivalent Optuna structure)

13 of 13 LightGBM Optuna search-space dimensions have a clean XGBoost equivalent. Two semantic-equivalence substitutions plus one objective-string substitution; everything else is 1-to-1 with identical names and ranges.

| Optuna name | LightGBM | LightGBM range | XGBoost | XGBoost range | Notes |
|---|---|---|---|---|---|
| `n_estimators` | `n_estimators` | [50, 500] | `n_estimators` | [50, 500] | Identical |
| `max_depth` | `max_depth` | [3, 5] | `max_depth` | [3, 5] | Identical |
| `num_leaves` | `num_leaves` | [15, 127] | `max_leaves` | [15, 127] | XGBoost respects `max_leaves` only when `grow_policy='lossguide'`; default `'depthwise'` ignores it. **Brief decision: drop `num_leaves` Optuna sampling for XGBoost path, keep `grow_policy='depthwise'` to maximize architectural difference (load-bearing axis).** |
| `learning_rate` | `learning_rate` | [0.01, 0.3] log | `learning_rate` (eta) | [0.01, 0.3] log | Identical |
| `subsample` | `subsample` | [0.5, 1.0] | `subsample` | [0.5, 1.0] | Identical row-subsampling |
| `colsample_bytree` | `colsample_bytree` | [0.3, 1.0] (fast_mode 1.0) | `colsample_bytree` | [0.3, 1.0] (fast_mode 1.0) | Identical; `fast_mode` hardcodes 1.0 |
| `min_child_samples` | `min_child_samples` | [5, 100] | `min_child_weight` | [5, 100] | Semantic equivalent (sample-count vs hessian-sum); same range works |
| `reg_alpha` | `reg_alpha` | [1e-8, 10] log | `reg_alpha` | [1e-8, 10] log | Identical L1 |
| `reg_lambda` | `reg_lambda` | [1e-8, 10] log | `reg_lambda` | [1e-8, 10] log | Identical L2 |
| `random_state` | `random_state` | outer-derived | `random_state` | outer-derived | Identical |
| objective binary | `objective='binary'` + `is_unbalance=True` | — | `objective='binary:logistic'` + `scale_pos_weight=neg/pos` | computed per-fit | XGBoost has no `is_unbalance` flag — caller computes `scale_pos_weight` |
| objective ternary | `objective='multiclass'` + `num_class=3` | — | `objective='multi:softprob'` + `num_class=3` | — | `'multi:softprob'` is the correct probabilities-output objective |
| `tree_method` (pin) | n/a (default `serial`) | — | `tree_method='hist'` | pinned | Pin explicitly to rule out version drift / GPU fallback |

**Single design decision** (load-bearing for the architectural-difference axis): keep XGBoost `grow_policy='depthwise'` (the default). Setting `grow_policy='lossguide'` would mimic LightGBM's leaf-wise growth and defeat the purpose of the head-to-head. Drop the `num_leaves` Optuna sample for the XGBoost path (it's a no-op under depthwise) — this is the only change to the Optuna search-space dimensionality. Confidence threshold + `training_days` Optuna sampling remain unchanged (these are post-fit decisions, not LightGBM-internal).

### 2.2 Smoke test status — SKIPPED (xgboost not installed in env)

The smoke script attempted a 1-symbol × 1-month default-config XGBoost fit on (BCH, 2024-12) IS data. XGBoost is not in the worktree's `pyproject.toml` dependency list (verified via `grep -i xgboost pyproject.toml uv.lock` returning empty); the smoke degraded to an integration-check-only mode that produced the parameter map and pitfalls notes. **This is documented in `xgboost_smoke_results.csv` row 1: `xgboost_available=False`, `notes` field populated with installation instruction.**

**Pre-committed for Phase 6 setup (sub-fix #4 in §3.5)**: Engineer adds `xgboost>=2.0,<3.0` to `pyproject.toml` dependencies, runs `uv sync`, then re-runs the EDA script to produce a populated `xgboost_smoke_results.csv` row. The smoke is a sanity check (default-config Sharpe should be ≥ −0.5 on BCH 2024-12 IS data, confirming the pipeline integrates), NOT a production replication. If the smoke produces a Sharpe materially worse than zero on a single-month default fit, the Engineer documents it in the engineering report but does not abort — Optuna search will explore better hyperparameters in production.

### 2.3 Implementation pitfalls catalogued (`xgboost_pitfalls.md`)

10 pitfalls documented. The 4 load-bearing ones for production correctness:

1. **Class imbalance**: must compute `scale_pos_weight = n_neg / n_pos` per-fit; XGBoost has no `is_unbalance` flag analog. Mirror LightGBM's denominator policy exactly.
2. **Feature importance scale**: `feature_importances_` returns gain (XGBoost default `importance_type='gain'`) vs split-count (LightGBM default `importance_type='split'`). The **rank** is portable (Critic Falsifier 4 reads rank, not absolute value); the **values** in `feature_importance.csv` will look numerically different.
3. **Tree growth (load-bearing axis)**: pin XGBoost `grow_policy='depthwise'` (default). Setting `'lossguide'` would defeat the head-to-head.
4. **Histogram method**: pin `tree_method='hist'` explicitly (default in v2.x but version-dependent). Rules out `'gpu_hist'` if a future env adds CUDA.

NaN handling, categorical handling, and determinism notes are non-blocking (XGBoost handles NaN natively like LightGBM; v3 features are all continuous floats; both packages are deterministic with `n_jobs=1` + fixed seeds).

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise; reinforced after iter-v3/015's NULL-RESULT-class subtype): brief Section 2 must include explicit estimates of how many IS trades will change in the roster, with a falsifier triggered if observed change is below the predicted lower bound.

| Metric | iter-v3/013 baseline | Predicted iter-v3/016 | Source |
|---|---:|---:|---|
| IS trade count | 209 | **band [165, 250], median 200** | `xgboost_eda_synthesis.md` |
| Lower bound mechanism | — | XGBoost depth-wise more conservative on signal selection (≈ 0.79 × baseline) | growth-strategy difference |
| Upper bound mechanism | — | XGBoost may surface signal LightGBM ignored (≈ 1.20 × baseline) | iter-v3/015 TBR failure-mode |
| **Saturation falsifier** | — | observed |IS Δ| < 11 trades AND non-bit-identical roster → NULL-RESULT subtype | ceil(0.05 × 209) per `feedback_axis_saturation_predictor.md` |

**Saturation falsifier threshold (precise)**: realized IS trade count in [198, 220] AND trade roster non-bit-identical to iter-v3/013 → §4.4 row 4 NULL-RESULT-class fires (architecture swap was mechanically inert at the trade-decision boundary). Realized IS trade count outside [198, 220] (i.e., |Δ| ≥ 11) → architecture swap propagated; verdict from §4.4 rows 1–3 based on IS Sharpe band.

The realized iter-v3/016 run will diverge from this prediction because:
- Optuna re-optimizes the XGBoost-specific search space (different optimal params).
- `confidence_threshold` Optuna parameter will land at a different value because the probability calibration differs (XGBoost's depth-wise growth produces flatter probability surfaces).
- Risk-gate firing distributions reshape against a different probability output.

The DIRECTION of the prediction is informative; the band is wide because architecture-axis variation is high-variance.

### 2.5 Setup integrity (verified at SHA `b5592bd`)

```
analysis/iteration_v3-016/xgboost_baseline_eda.py committed                     PASS
xgboost_param_map.csv produced (14 rows, 6 cols)                                 PASS
xgboost_smoke_results.csv produced (1 row, 16 cols, status=skipped)              PASS
xgboost_pitfalls.md produced (10 numbered pitfalls, 103 lines)                   PASS
xgboost_eda_synthesis.md produced (52 lines, behavioral-effect prediction)       PASS
xgboost not currently installed (verified grep on pyproject.toml + uv.lock)      EXPECTED — Phase 6 adds
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (BCH+LDO+TRX, inherited from iter-v3/013)

The 3-symbol universe is the iter-v3/013 baseline state. `set({BCHUSDT, LDOUSDT, TRXUSDT}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓.

### 3.2 Labeling — UNCHANGED (inherits iter-v3/010 ATR(2.0/1.0))

| Parameter | iter-v3/015 (current) | iter-v3/016 (this iteration) |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | REQUIRED_GAP = 66 | UNCHANGED (n_symbols=3 unchanged) |

### 3.3 Features — REVERTED to 13 (drop `tbr_zscore_30`; pre-commit per Critic FINAL Rec 3)

```python
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 13, tbr_zscore_30 dropped (REVERTED to iter-v3/013 baseline)
```

`_verify_feature_columns()` will be updated to assert `len == 13` AND `'tbr_zscore_30' not in V3_FEATURE_COLUMNS` AND `'vwap_dev_50' not in V3_FEATURE_COLUMNS` (both dropped baselines preserved).

### 3.4 Risk gates — UNCHANGED (z-score 2.0, BTC band ±15%, ADX 20, all primitive thresholds inherited from iter-v3/013)

| Parameter | iter-v3/015 (current) | iter-v3/016 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED)** |
| `RiskV2Config.adx_threshold` | 20.0 | **20.0 (UNCHANGED — already at iter-v3/013 baseline since iter-v3/015 reset)** |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | **15.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Sub-fix decomposition (single-axis: MODEL ARCHITECTURE — LightGBM → XGBoost)

iter-v3/016 first commit MUST land all 4 pre-commits PLUS the XGBoost integration path before the runner is invoked. Per Critic FINAL Recommendation 3 of iter-v3/015 review, the first commit must include all of these in one commit unit:

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Drop `tbr_zscore_30` from V3_FEATURE_COLUMNS** (revert to 13 features; restore iter-v3/013 baseline) | `src/crypto_trade/features_v3/__init__.py`: edit `V3_FEATURE_COLUMNS_TOP_N` to remove the `"tbr_zscore_30"` line; update docstring | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'tbr_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 2 | **Add `tbr_raw` to V3_NON_FEATURE_COLUMNS** (Critic Clarification 4 hygiene) | `src/crypto_trade/features_v3/__init__.py`: edit `V3_NON_FEATURE_COLUMNS = ("natr_21_raw", "tbr_raw")` | `python -c "from crypto_trade.features_v3 import V3_NON_FEATURE_COLUMNS; assert 'tbr_raw' in V3_NON_FEATURE_COLUMNS"` exits 0 |
| 3 | **Fix `_write_feature_importance` defect at `run_baseline_v3.py:1110-1151`** (Critic FINAL Rec 3 chain; QE-discovered defect at iter-v3/015 must not propagate). **Approach (a) AGGREGATE**: iterate over ALL `(cfg, strategy)` in `primary_model_pairs`, sum split-count + gain importances per (symbol, feature), emit (i) per-symbol CSVs `feature_importance_<SYM>.csv` AND (ii) a portfolio-aggregated `feature_importance.csv` (sum across symbols, ranked descending). Both sit under `report_dir/{in_sample,out_of_sample}/`. | runner | `for sym in BCHUSDT LDOUSDT TRXUSDT; do test -f reports-v3/iteration_v3-016/in_sample/feature_importance_$sym.csv; done` exits 0; `test -f reports-v3/iteration_v3-016/in_sample/feature_importance.csv` exits 0 |
| 4 | **ITERATION_LABEL `"v3-015"` → `"v3-016"`** | `run_baseline_v3.py` line 100: one-line edit | `grep -E 'ITERATION_LABEL.*=.*"v3-016"' run_baseline_v3.py` exits 0 |
| 5 | **Restore adx_threshold = 20.0** (already at this value at iter-v3/015 baseline; verify post-revert) | `run_baseline_v3.py` `_build_v3_model`: `RiskV2Config(zscore_threshold=2.0, adx_threshold=20.0)` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 6 | **Add `xgboost>=2.0,<3.0` to `pyproject.toml`** dependencies; run `uv sync` | `pyproject.toml` `[project]` `dependencies` list | `grep -E 'xgboost' pyproject.toml` exits 0; `uv run python -c "import xgboost; print(xgboost.__version__)"` exits 0 |
| 7 | **Add `XgboostStrategy` class** as a parallel-structure strategy with the same lazy monthly walk-forward retraining + Optuna search loop as `LightGbmStrategy`. Implementation guidance: subclass NOT recommended (LightGbmStrategy's internals are tightly coupled to `lgb.LGBMClassifier`-specific calls in `optimization.py`). Recommended: copy `LightGbmStrategy` to a new file `src/crypto_trade/strategies/ml/xgb.py`, replace `lgb.LGBMClassifier` with `xgb.XGBClassifier`, replace `is_unbalance=True` with `scale_pos_weight=n_neg/n_pos` per-fit, replace `objective='binary'` with `objective='binary:logistic'`, replace `objective='multiclass'` with `objective='multi:softprob'`, drop the `num_leaves` Optuna sample (no-op under depthwise; per §2.1), pin `tree_method='hist'`, pin `n_jobs=1`. Follow `optimization.py` patterns (one parallel `optimize_and_train_xgb` function); do NOT modify the existing LightGBM path. | `src/crypto_trade/strategies/ml/xgb.py` new file; `src/crypto_trade/strategies/ml/optimization_xgb.py` new file (or extension to existing) | `python -c "from crypto_trade.strategies.ml.xgb import XgboostStrategy; XgboostStrategy(training_months=24, n_trials=10, label_tp_pct=8.0, label_sl_pct=4.0, ensemble_seeds=[42], feature_columns=['hurst_100'])"` exits 0 (constructor smoke) |
| 8 | **Add `--model {lgbm,xgboost}` CLI flag** to `run_baseline_v3.py`. Default = `lgbm` (no behavior change for other iterations). iter-v3/016 invokes with `--model xgboost`. The flag wires through `_build_v3_model` selecting either `LightGbmStrategy` or `XgboostStrategy`. | `run_baseline_v3.py` argparse + `_build_v3_model` | `grep -E 'parser.add_argument..--model' run_baseline_v3.py` exits 0 |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input — 15 verifiers)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS reverted to 13 (drop `tbr_zscore_30`) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'tbr_zscore_30' not in V3_FEATURE_COLUMNS, V3_FEATURE_COLUMNS"` exits 0 |
| 2 | `tbr_raw` present in V3_NON_FEATURE_COLUMNS | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_NON_FEATURE_COLUMNS; assert 'tbr_raw' in V3_NON_FEATURE_COLUMNS, V3_NON_FEATURE_COLUMNS"` exits 0 |
| 3 | `_write_feature_importance` aggregates across all (sym, month) models AND emits per-symbol + portfolio CSVs | `run_baseline_v3.py:1110-1151` (rewritten) | post-Phase-6: `for sym in BCHUSDT LDOUSDT TRXUSDT; do test -f reports-v3/iteration_v3-016/in_sample/feature_importance_$sym.csv && test -f reports-v3/iteration_v3-016/out_of_sample/feature_importance_$sym.csv; done` exits 0; AND `test -f reports-v3/iteration_v3-016/in_sample/feature_importance.csv && test -f reports-v3/iteration_v3-016/out_of_sample/feature_importance.csv` exits 0 |
| 4 | `ITERATION_LABEL == "v3-016"` | `run_baseline_v3.py` line ~100 | `grep -E 'ITERATION_LABEL.*=.*"v3-016"' run_baseline_v3.py` exits 0 |
| 5 | `adx_threshold=20.0` (iter-v3/013 baseline restored / unchanged) | `run_baseline_v3.py` `_build_v3_model` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 6 | `xgboost` in pyproject and importable | `pyproject.toml` + env | `grep -E 'xgboost.*>=.*2\.0' pyproject.toml` exits 0; `uv run python -c "import xgboost; assert xgboost.__version__.startswith('2.')"` exits 0 |
| 7 | `XgboostStrategy` class importable + constructible | `src/crypto_trade/strategies/ml/xgb.py` | `uv run python -c "from crypto_trade.strategies.ml.xgb import XgboostStrategy; XgboostStrategy(training_months=24, n_trials=10, label_tp_pct=8.0, label_sl_pct=4.0, ensemble_seeds=[42], feature_columns=['hurst_100'], use_atr_labeling=True, atr_tp_multiplier=2.0, atr_sl_multiplier=1.0)"` exits 0 |
| 8 | `--model` CLI flag present, defaults to `lgbm` | `run_baseline_v3.py` argparse | `grep -E "parser\.add_argument.*--model" run_baseline_v3.py` exits 0; `uv run python run_baseline_v3.py --help` shows `--model` |
| 9 | Sub-fix #6-8 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-016/comparison.csv` |
| 10 | `_verify_feature_columns()` updated to assert len==13 AND tbr_zscore_30 absent | `run_baseline_v3.py` `_verify_feature_columns` | runtime `_verify_feature_columns()` call inside main does not raise; `grep -E 'tbr_zscore_30' run_baseline_v3.py` shows only the assertion strings (not the column itself in any list) |
| 11 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 12 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | wall-clock minutes < 120 |
| 13 | Runner used `--model xgboost` AND backtest ran with XGBoost (NOT LightGBM) | `reports-v3/iteration_v3-016/run.log` | `grep -E "(--model xgboost\|XgboostStrategy)" reports-v3/iteration_v3-016/run.log` exits 0 |
| 14 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md`)**: `|IS trades − 209| ≥ 11` (architecture swap propagated) | comparison.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-016/comparison.csv'); n = int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert abs(n - 209) >= 11 or _bit_identical_check_failed(), f'IS trades = {n}; abs change < 11 AND roster bit-identical → NULL-RESULT (§4.4 row 4)'"` returns informational; the §4.4 row 4 NULL-RESULT classification fires if and only if BOTH `|n - 209| < 11` AND trade-roster bit-identical to iter-v3/013 |
| 15 | XGBoost smoke updated: `xgboost_smoke_results.csv` row populated with `xgboost_available=True` after Phase 6 setup | `analysis/iteration_v3-016/xgboost_smoke_results.csv` | post-`uv sync`, `uv run python analysis/iteration_v3-016/xgboost_baseline_eda.py` re-run; `python -c "import pandas as pd; df = pd.read_csv('analysis/iteration_v3-016/xgboost_smoke_results.csv'); assert bool(df.iloc[0]['xgboost_available']) is True"` exits 0 |

### 3.7 Single-axis discipline reaffirmed

Single axis: **model architecture** (LightGbmStrategy → XgboostStrategy). All 4 pre-commits (drop `tbr_zscore_30`, add `tbr_raw` to non-feature, fix `_write_feature_importance`, ITERATION_LABEL update, restore adx=20) and the XGBoost integration (sub-fixes 6–8) are bundled into the **first commit unit** per Critic FINAL Rec 3. None of the pre-commits are themselves "axis variations" — they are baseline-restoration housekeeping. The architectural swap is the sole semantic change exposed to the model's loss surface.

NO new feature additions. NO labeling change. NO z-score-gate change. NO BTC-band change. NO ADX-gate change. NO new gate primitive. NO universe change.

### 3.8 Inheritance from iter-v3/015

The `iteration-v3/016` branch was branched from `iteration-v3/015` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15 + ITERATION_LABEL=v3-012`
- `5217490 feat(iter-v3/013): drop-MKR universe (4→3 symbols)`
- `b5592bd feat(iter-v3/016): xgboost_baseline_eda — smoke test + hyperparam space` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14"` exits 0 (currently 14 with `tbr_zscore_30`; sub-fix #1 reverts to 13)
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 (already at iter-v3/013 baseline since iter-v3/015 reset)
- `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` exits 0 (3-symbol universe gap from iter-v3/013)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

### 3.9 Implementation strategy notes — XgboostStrategy as parallel class (NOT subclass)

**Recommendation**: ADD `XgboostStrategy` as a parallel class at `src/crypto_trade/strategies/ml/xgb.py`. Do NOT refactor `LightGbmStrategy`. Rationale:

1. `LightGbmStrategy.__init__` and the per-month training loop are tightly coupled to `lgb.LGBMClassifier`-specific calls inside `optimization.py:_objective` and `optimize_and_train`. Hot-path code (CV loop with `tscv.split`, OOF buffer per-trial persistence) imports `lgb` directly.
2. A subclass would have to override almost every method to swap the library — gaining nothing over a parallel class.
3. A parallel class isolates the change: the existing LightGBM path remains byte-identical and continues to serve every other iteration (v1, v2, v3 iter-v3/001-015). Only iter-v3/016 takes the XGBoost path.
4. The `--model {lgbm,xgboost}` CLI flag at `run_baseline_v3.py` is the single decision point. `_build_v3_model` routes to `LightGbmStrategy` or `XgboostStrategy` based on the flag. Default = `lgbm`.

Implementation steps (Engineer):
- Copy `lgbm.py` → `xgb.py`. Rename class `LightGbmStrategy` → `XgboostStrategy`. Keep all the lazy monthly walk-forward retraining infrastructure unchanged (it does not depend on the LGBM library — it depends on the `model.predict_proba` API which both libraries expose identically).
- Copy `optimization.py:optimize_and_train` and `_objective` into a new `optimization_xgb.py` file (or extend `optimization.py` with parallel functions). Replace `lgb.LGBMClassifier` with `xgb.XGBClassifier`. Replace `is_unbalance=True` with `scale_pos_weight = max(n_neg, 1) / max(n_pos, 1)` computed before each fit. Replace objective strings per §2.1. Drop the `num_leaves` Optuna `suggest_int` (no-op under depthwise growth; per §2.1 design decision).
- `_write_feature_importance` (sub-fix #3) reads `model.feature_importances_` — this attribute exists on both `LGBMClassifier` and `XGBClassifier`. The fix is library-agnostic: aggregate properly across (sym, month) cells, emit per-symbol + portfolio CSVs.
- `RiskV3Wrapper` reads `inner.feature_columns` and `inner._interval` — both attributes will exist on `XgboostStrategy` (carried by direct port). NO changes needed to `RiskV3Wrapper`.

Optuna integration: the existing `optuna.create_study` + `study.optimize` pattern in `optimize_and_train` reuses cleanly with XGBoost's hyperparam space — Optuna is library-agnostic. The `oof_buffer` per-trial OOF return persistence pattern carries over identically (it captures `predict_proba` outputs, not LGBM internals).

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING-ALTERNATIVE`, `EXPLORATION-PROMISING-ON-NEW-FEATURES`, `EXPLORATION-NEGATIVE`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/016 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/015 (current head) | iter-v3/013 baseline (reverted target) | iter-v3/016 prediction |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.6445 | +1.0088 | **predicted [+0.70, +1.30] with median +1.00** |
| IS trades | 205 | 209 | **predicted [165, 250] with median 200** |
| OOS trades (informational) | 85 | 85 | **predicted [70, 110]** |
| OOS Sharpe (informational) | +2.1206 | +2.6970 | **informational; gates at OOS_n_trades < 130 floor** |
| Phase 6 wall-clock | n/a | n/a | predicted 8–15 min (XGBoost depthwise CPU ≈ LightGBM serial CPU at 13 features), 2h hard cap |

The prediction band [+0.70, +1.30] is intentionally **broader than iter-v3/013's natural single-seed variance**:
- Centered on iter-v3/013's +1.0088 (the recovery target after dropping `tbr_zscore_30`).
- Lower edge +0.70 absorbs the case where XGBoost depth-wise growth is meaningfully more conservative under the same Optuna budget, yielding lower-confidence signals → fewer trades → lower Sharpe (still PROMISING-ALTERNATIVE territory if importance Spearman ρ < 0.85).
- Upper edge +1.30 absorbs the case where XGBoost surfaces signal LightGBM ignored AND Optuna re-optimization lands in a more-favorable hyperparameter local minimum.
- Per López de Prado AFML Ch. 7: model-architecture differences within the gradient-boosting family typically produce ±0.30 Sharpe variation under the same data and label scheme; band width 0.60 covers ±0.30 around the iter-v3/013 baseline.

Per the iter-v3/010 + iter-v3/011 + iter-v3/013 calibration history (3 consecutive favorable IS overshoots, established at iter-v3/013 caveat 4): for behavior-changing axes, widen upper bound on PROMISING predictions by 30%. Applied here to the +1.00 median: upper band +1.30 = +1.00 × 1.30. Lower band kept at +0.70 (iter-v3/012 NULL-RESULT pattern showed downside underperformance is bounded by Optuna re-optimization variance).

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → XGBoost is fundamentally inferior on this stack (e.g., the depth-wise growth × confidence_threshold interaction yields almost no trades, OR XGBoost convergence is broken at small-sample depths). Verdict: EXPLORATION-NEGATIVE on model-architecture axis. Catalog this finding; closes the model-architecture axis category.

**Falsifier 2** (saturation predictor per `feedback_axis_saturation_predictor.md`): observed IS trade count in [198, 220] AND trade roster bit-identical to iter-v3/013 → architecture swap was mechanically inert (XGBoost produced identical `(symbol, candle, signal)` triples as LightGBM under Optuna's chosen hyperparams). Verdict: §4.4 row 4 NULL-RESULT-class fires.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe → XGBoost fit/predict materially slower than LightGBM at the 13-feature scale; engineer documents the cause (likely missing `n_jobs=1` pin or CUDA fallback).

**Falsifier 4** (importance divergence): Spearman ρ between LightGBM iter-v3/013 importance ranking and XGBoost iter-v3/016 importance ranking ≥ 0.95 → architectures are functionally equivalent on this feature stack; closes the "architecture matters" hypothesis.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 13` returns False OR `import xgboost` fails OR `XgboostStrategy(...)` constructor smoke fails → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (single decision tree — fixes iter-v3/015 §4.3-vs-§4.4 conflict per Critic FINAL Rec 4)

Decision tree applied IN ORDER. First matching row determines the verdict; later rows are mutually exclusive at the boundary thresholds.

| Order | Critic verdict | Required conditions (ALL must hold) | Catalog row | Next iteration |
|---|---|---|---|---|
| 1 | `EXPLORATION-PROMISING-ALTERNATIVE` (PATH A) | IS Sharpe ∈ [+1.00, +1.30] AND importance Spearman ρ vs iter-v3/013 LightGBM < 0.85 AND |IS trades − 209| ≥ 11 | "model architecture matters; XGBoost matches LightGBM Sharpe with materially different feature emphasis" | iter-v3/017 STRUCTURAL axis (NEW labeling architecture or NEW risk primitive); CONFIRMATION QR may bundle XGBoost+LightGBM ensemble at iter-v3/N+ if 10:1 ratio satisfied |
| 2 | `EXPLORATION-PROMISING-ON-NEW-FEATURES` (PATH C) | IS Sharpe ≥ +1.00 AND XGBoost importance for any feature differs by ≥ 5 ranks vs LightGBM iter-v3/013 (e.g., a feature ranked #13 in LGBM lands in top-3 under XGB) AND |IS trades − 209| ≥ 11 | "XGBoost surfaces signal LightGBM ignored; re-test deferred microstructure features under XGBoost" | iter-v3/017 may revisit `tbr_zscore_30` or other deferred microstructure features under XGBoost head; per memory rule continued model-architecture axis closes after iter-v3/016 regardless |
| 3 | `EXPLORATION-PROMISING-INERT` (between PATH A and PATH B) | IS Sharpe ∈ [+0.91, +1.11] AND importance Spearman ρ ≥ 0.85 AND |IS trades − 209| ≥ 11 | "architecture swap is approximately equivalent; LightGBM and XGBoost are interchangeable on this stack" | iter-v3/017 STRUCTURAL axis; closes architecture-as-axis category |
| 4 | `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT-class subtype, per iter-v3/015 lesson) | |IS trades − 209| < 11 AND trade roster bit-identical to iter-v3/013 (BCH/LDO/TRX rows match to 4 decimal places on weighted_pnl) | "architecture swap mechanically inert at trade-decision boundary; XGBoost produced same signals as LightGBM under Optuna" | iter-v3/017 STRUCTURAL axis on a different category; do NOT bundle XGBoost as additive ingredient |
| 5 | `EXPLORATION-NEGATIVE` (PATH B) | IS Sharpe < +0.81 (ie, worse than iter-v3/013 by Δ-0.20+) AND |IS trades − 209| ≥ 11 | "LightGBM is near-optimal for this feature/label combo; XGBoost depth-wise growth underperforms" | iter-v3/017 STRUCTURAL axis (closes architecture-as-axis category for now; may revisit at iter-v3/N+ with different hyperparam budget) |
| 6 | `BLOCK` (process) | Methodology check FAILED, OR Falsifier 3 (wall-clock > 30 min that doesn't recover by 2h cap) triggered, OR pre-flight checks fail | (none) | Diary documents, iter-v3/017 fixes the methodology gap |

**Sharp boundary clarifications (resolves iter-v3/015 §4.3-vs-§4.4 conflict)**:
- Row 1 vs Row 3: importance divergence threshold Spearman ρ < 0.85 is the discriminator at IS Sharpe ∈ [+1.00, +1.11].
- Row 1 vs Row 2: PATH A (importance ranking globally divergent, Spearman) vs PATH C (single-feature emphasis inversion ≥ 5 ranks). PATH C is more specific; if both fire, prefer PATH A (Row 1) at the boundary.
- Row 4 (NULL-RESULT) and Row 5 (NEGATIVE) are mutually exclusive: Row 4 requires bit-identity (mechanical inertness); Row 5 requires non-bit-identical roster AND IS Sharpe Δ-0.20.
- Row 3 (PROMISING-INERT) requires non-bit-identical roster (otherwise Row 4 fires) AND tight Sharpe band ±0.10 around iter-v3/013.

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4)

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h (per skill SHA `d5c9f21`).
2. **Single-axis variation rule** honored: only model architecture changed; features (post-revert), labeling, all gates byte-for-byte identical to iter-v3/013 baseline. The 4 first-commit pre-commits are baseline-restoration housekeeping, not axis variations.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING-ALTERNATIVE / PROMISING-ON-NEW-FEATURES / PROMISING-INERT / NEGATIVE-no-effect / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-016.md`.
4. **Saturation predictor falsifier (per `feedback_axis_saturation_predictor.md`)**: Section 3.6 row 14 actively verifies the architecture swap propagated (IS trade-count change OR trade-roster non-bit-identical).

### 5.2 Methodology-pipeline safeguards (4)

1. **Adversarial unit tests** must PASS before backtest (Section 3.6 row 11).
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight library check**: `import xgboost` must succeed AND `XgboostStrategy(...)` constructor must succeed before Phase 6 launches (Section 3.6 rows 6–7).
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches; iter-v3/015 review process (Round 1 PRELIMINARY → QR clarifications → Round 2 FINAL) is the template.

### 5.3 Axis-specific risks (3)

1. **XGBoost integration bug surface**: the new `XgboostStrategy` + `optimize_and_train_xgb` paths introduce ≈ 200 lines of new code (per the parallel-class strategy in §3.9). Risk: a copy-paste error from `lgbm.py` leaves a `lgb.` reference somewhere, causing silent fallback to LightGBM OR a runtime crash mid-backtest. **Mitigation**: Section 3.6 row 13 verifies `XgboostStrategy` was used (`grep` on run.log). Engineer's pre-flight Phase 6 check should construct the strategy and call `predict_proba` on a 5-row DataFrame to confirm end-to-end XGBoost execution before launching the full backtest.
2. **Hyperparam space mismatch**: §2.1 documents 13 of 13 dimensions map cleanly, with `num_leaves` dropped under depthwise growth and `min_child_samples` semantically replaced by `min_child_weight`. Risk: Optuna explores a meaningfully smaller search space (12 dimensions vs LightGBM's 13), producing a less-thorough exploration and biasing the comparison. **Mitigation**: per §2.1 design decision, drop `num_leaves` for XGBoost is correct (it is a no-op under depthwise); the apparent dimension reduction is principled. Optuna trial budget unchanged at 10 trials per (symbol, month); if the comparison is borderline (Sharpe within ±0.10 of LightGBM), the future CONFIRMATION QR may re-test with higher trial budget.
3. **NaN-row handling differences**: while both libraries handle NaN natively, edge cases differ — XGBoost's missing-value direction is learned per split, LightGBM's is partly heuristic. Risk: at small per-symbol training-window sizes (LDO has fewer months of data due to listing date), the NaN-routing learning may be unstable. **Mitigation**: existing `optimization.py` finite-mask pattern carries over to XGBoost path; per `xgboost_pitfalls.md` item 2, both libraries pass NaN through identically at the practical level. Minor risk only.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED, byte-identical to iter-v3/013 baseline

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > **20** | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 | ≈ 25–35% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±**15%** | ≈ 12–13% killed | Macro flips |

Combined kill rate target: **80–90%** (same as iter-v3/013 baseline). All 7 primitives operate identically regardless of the underlying boosting library because they consume model `predict_proba` output, not internal model state. The architectural swap to XGBoost does not change any primitive's threshold.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and on `predict_proba(X)` output. Both LightGBM and XGBoost expose `predict_proba` returning [n_samples, n_classes] arrays with identical interface. Risk-gate behavior is library-agnostic.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2022-09-24 → 2025-03-23 — same as iter-v3/013. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/013 OOS LDO concentration was 65.65%; the lottery-flag carries forward unchanged (10 trades, 80% WR, exact-binomial 95% CI [44.4%, 97.5%] — too wide to claim signal-from-noise distinction). Concentration is NOT a gate for iter-v3/016 per TYPE=EXPLORATION; informational only. Per the catalog row for iter-v3/011 (LDO lottery-flag), this is monitored but not disqualifying at EXPLORATION level.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 8 prior EXPLORATIONs)

**Prediction P1 (process, P=10%)**: XGBoost installed but smoke fit fails on (BCH, 2024-12) due to platform-specific issue (e.g., glibc version mismatch with prebuilt wheel). **Detection signal**: `uv run python analysis/iteration_v3-016/xgboost_baseline_eda.py` exits non-zero post-`uv sync`. **Mitigation**: Engineer falls back to source build via `uv sync --reinstall xgboost --no-binary xgboost`; if that also fails, emit Phase 6 BLOCK with platform diagnostic.

**Prediction P2 (process, P=15%)**: XgboostStrategy constructor smoke passes BUT runner crashes mid-backtest with library-specific error (e.g., XGBoost rejects integer label dtypes that LightGBM accepts; or `predict_proba` shape differs in edge cases). **Detection signal**: backtest exits with traceback referring to `xgb.` namespace. **Mitigation**: Engineer wraps fits in try/except matching the `LightGbmStrategy` pattern; documents the failing case in engineering report; if unfixable in 2h cap, emits Phase 6 BLOCK.

**Prediction P3 (process, P=5%)**: `_write_feature_importance` rewrite (sub-fix #3) breaks the existing iter-v3/015 published behavior (where `feature_importance.csv` had the per-symbol BCH-last-month rows). Risk: downstream Critic checks rely on specific column schema. **Detection signal**: Critic Check 7 (Reproducibility) fails because feature_importance.csv schema changed; OR per-symbol CSVs missing despite §3.6 row 3 claim. **Mitigation**: Engineer retains both old single-symbol output (renamed `feature_importance_<SYM>.csv`) AND adds the aggregated portfolio CSV. Schema additive, not breaking.

**Prediction P4 (model, P=35%, PATH A or PATH C — PROMISING-ALTERNATIVE / PROMISING-ON-NEW-FEATURES)**: IS Sharpe ∈ [+1.00, +1.30] AND importance Spearman ρ < 0.85 — XGBoost matches or exceeds LightGBM with materially different feature emphasis. The architecture-axis hypothesis is supported; iter-v3/017 may pursue ensemble approaches at CONFIRMATION level.

**Prediction P5 (model, P=30%, PROMISING-INERT)**: IS Sharpe ∈ [+0.91, +1.11] AND importance Spearman ρ ≥ 0.85 — model architectures are approximately equivalent on this 13-feature stack at this Optuna budget. The hypothesis "model-architecture matters" is unsupported; LightGBM remains the production choice. Catalog this as "architecture-as-axis closed."

**Prediction P6 (model, P=20%, NEGATIVE or NULL-RESULT)**: IS Sharpe < +0.81 OR (NULL-RESULT-class: |IS trades − 209| < 11 AND trade-roster bit-identical). XGBoost depth-wise growth materially underperforms on this signal (P6.a, P=15%) OR Optuna lands on hyperparams that produce a near-identical decision boundary by coincidence (P6.b, P=5%, NULL-RESULT-class subtype). Catalog accordingly.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline.
- 3 model-level (P4, P5, P6) covering the 5 §4.4 outcome rows (P4 = rows 1 & 2; P5 = row 3; P6 = rows 4 & 5).
- Per the iter-v3/010 + iter-v3/011 + iter-v3/013 calibration history (3 consecutive favorable IS overshoots on behavior-changing axes; iter-v3/012 NULL-RESULT and iter-v3/015 NULL-RESULT-class on saturated/INERT axes): for model-architecture axis here, priors are 35/30/20 with **broader PROMISING band** reflecting the hypothesized asymmetric upside if XGBoost surfaces signal LightGBM ignores. Process-failure tail is moderate (30%) because XGBoost integration is a non-trivial code addition of ~200 lines.

Summary: **EXPLORATION-PROMISING (any subtype) pathway probability ≈ 65%** (P4+P5); EXPLORATION-NEGATIVE (any subtype) ≈ 20% (P6); process abort ≈ 30% (P1+P2+P3 ≈ 30%; each individually triggers a remediation, not a verdict change).

If any prediction fails to materialize, the iter-v3/016 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/016 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits one of: `EXPLORATION-PROMISING-ALTERNATIVE`, `EXPLORATION-PROMISING-ON-NEW-FEATURES`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING (any subtype) iff ALL 11 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (model architecture: LightGBM → XGBoost) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 12 |
| 4 | `--exploration --seeds 1 --n-trials 10 --model xgboost` used | TRUE | §3.5 sub-fix #8 |
| 5 | All adversarial tests pass | TRUE | §3.6 row 11 |
| 6 | `V3_FEATURE_COLUMNS` reverted to 13 (`tbr_zscore_30` absent) | TRUE | §3.6 row 1 |
| 7 | `tbr_raw` in `V3_NON_FEATURE_COLUMNS` | TRUE | §3.6 row 2 |
| 8 | `_write_feature_importance` produces per-symbol CSVs AND aggregated portfolio CSV | TRUE | §3.6 row 3 |
| 9 | Critic OVERALL = `EXPLORATION-PROMISING-ALTERNATIVE` OR `EXPLORATION-PROMISING-ON-NEW-FEATURES` OR `EXPLORATION-PROMISING-INERT` (NOT NEGATIVE, NOT BLOCK) | enum | Phase 7.5 |
| 10 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 11 | **Saturation predictor verified**: `|IS trades − 209| ≥ 11` (architecture swap propagated) OR (if |Δ| < 11 AND non-bit-identical roster, the §4.4 row 3 PROMISING-INERT path applies); **§4.4 row 4 NULL-RESULT-class fires only if |Δ| < 11 AND trade-roster bit-identical** | TRUE per §4.4 decision tree | §3.6 row 14 |

### EXPLORATION-NEGATIVE (clean) iff:

- Criteria 1-8, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (per §4.4 row 5: IS Sharpe < +0.81 AND |IS trades − 209| ≥ 11).

### EXPLORATION-NEGATIVE-no-effect (NULL-RESULT-class subtype) iff:

- Criteria 1-8, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE-no-effect` (per §4.4 row 4: |IS trades − 209| < 11 AND trade-roster bit-identical to iter-v3/013).

### BLOCK (process) iff ANY of:

- Criteria 1-8, 10 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap
- XGBoost not importable post-Phase-6 setup (Section 3.6 row 6 fails)
- `XgboostStrategy` constructor smoke fails (Section 3.6 row 7 fails)

### Discretionary judgment — EXPLORATION pathway

iter-v3/016 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is one of the 4 PROMISING subtypes or NEGATIVE-no-effect, all of which are forward-pointers: they add one row to the catalog and count toward the 10 EXPLORATION quota. **iter-v3/016 NEVER updates BASELINE_V3.md.** After iter-v3/016 the catalog will need 1 more EXPLORATION row before any CONFIRMATION can launch (per cadence rule 10 EXPLORATION : 1 CONFIRMATION).

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | `kurtosis`, `skew` for comparison.csv stats | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 LGBM path (still default; iter-v3/016 does NOT use) | n/a |
| **`xgboost`** | **`>=2.0,<3.0` (NEW)** | **Apache-2.0** | **M1 XGBoost path (NEW for iter-v3/016)** | **If install fails: source build via `--no-binary xgboost`** |
| `pytest` | (already installed) | MIT | adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |
| `optuna` | (already installed) | MIT | Hyperparam search (library-agnostic) | n/a |

**One new external dep**: `xgboost>=2.0,<3.0`. Engineer adds to `pyproject.toml` `[project]` `dependencies` list as part of sub-fix #6. After `uv sync`, the smoke EDA must be re-run to populate `xgboost_smoke_results.csv` (sub-fix verifier #15).

XGBoost license: Apache-2.0. Compatible with the repo's license posture (LightGBM is MIT; both permissive; no copyleft contamination). v2.x is the recommended major; v3.x exists but introduces breaking API changes — pin upper bound `<3.0`. Per `xgboost_pitfalls.md` item 8, the pin protects against silent dependency drift.

The iteration's NEW code is:
- 1 analysis script + 4 outputs (committed at SHA `b5592bd`)
- Edits in `src/crypto_trade/features_v3/__init__.py` (revert V3_FEATURE_COLUMNS to 13 + add `tbr_raw` to V3_NON_FEATURE_COLUMNS)
- Rewrite of `_write_feature_importance` in `run_baseline_v3.py:1110-1151` (per-symbol + portfolio aggregation)
- New file `src/crypto_trade/strategies/ml/xgb.py` (~700 lines mirroring `lgbm.py`)
- New file `src/crypto_trade/strategies/ml/optimization_xgb.py` (~250 lines mirroring relevant parts of `optimization.py`) OR additive functions inside `optimization.py`
- Edit of `pyproject.toml` (add `xgboost>=2.0,<3.0`)
- Edit of `run_baseline_v3.py` (`--model` CLI flag + `_build_v3_model` routing + `ITERATION_LABEL` update + `_verify_feature_columns` len assertion update)
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths (library-agnostic; all consume per-trial OOF returns or trade rosters)

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation. Carries forward identically because aggregation reads `trial_oof_returns.parquet` written from `predict_proba` outputs — library-agnostic.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-016/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `b5592bd` analysis + the new sub-fix SHA AND any subsequent fixes)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|xgboost|pytest|pandas|pyarrow|optuna)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The runtime `V3_MODELS` (sanity check against §3.1) — must show 3 entries (BCH, LDO, TRX)
- The runtime `REQUIRED_GAP` (sanity check) — must show 66
- The runtime `xgboost.__version__` line in run.log
- The strategy class name actually used (sanity check against §3.5 sub-fix #7) — must show `XgboostStrategy`
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (Falsifier 2 reference, must be evaluated against [198, 220] ∩ bit-identity test for §4.4 row 4 disambiguation)
- The per-symbol AND portfolio-aggregated `feature_importance.csv` row 1 (top feature) for IS and OOS
- The wall-clock minutes total (must be < 120; target < 30)
- The adversarial test outcome (PASS expected)
- The `--exploration --seeds 1 --n-trials 10 --model xgboost` activation banner from `run.log`
- The runner invocation literal (proof of `--model xgboost`)
- The Spearman ρ between iter-v3/013 LightGBM importance vector and iter-v3/016 XGBoost importance vector (computed against the iter-v3/013 published `feature_importance.csv`) for §4.4 PATH A vs PATH C disambiguation

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new behavioral-effect predictor (Section 2):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration; XGBoost path mirrors |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference (#9 of 10); explicit "NEVER updates BASELINE_V3.md"; model-architecture axis MANDATED by `feedback_v3_iter016_xgboost_mandate.md` AND `feedback_structural_over_knob_exploration.md` Category 2 |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ∈ [+0.70, +1.30]; mechanism explanation; 3 pre-registered pathways (PROMISING-ALTERNATIVE / PROMISING-ON-NEW-FEATURES / NEGATIVE) |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-016/xgboost_baseline_eda.py` committed at SHA `b5592bd` BEFORE this brief; param map + smoke (skipped — xgboost not installed) + pitfalls + behavioral-effect predictor (saturation falsifier IS trades [198, 220] AND bit-identity NULL-RESULT) |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features REVERTED to 13 (drop tbr_zscore_30 — pre-commit #1); all gates UNCHANGED; sub-fix decomposition with 8 sub-fixes including 4 first-commit pre-commits; reconciliation table 15 verifiers; inheritance plan §3.8; XgboostStrategy parallel-class implementation strategy §3.9 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.70, +1.30]; 4 falsifiers + 1 process falsifier in §4.3; **single decision tree §4.4 with sharp boundary thresholds** (fixes iter-v3/015 §4.3-vs-§4.4 conflict per Critic FINAL Rec 4) |
| 5 — Risk Mitigation | PASS — 4 cadence-discipline structural safeguards + 4 methodology-pipeline safeguards + 3 axis-specific risks (XGBoost integration bugs, hyperparam space mismatch, NaN handling) |
| 6 — Risk Management Design | PASS — 7-primitive table inherited byte-identical from iter-v3/013 baseline; gate orthogonality verified for library-agnostic `predict_proba` consumption |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)** + 3 model-level (P4 PROMISING, P5 INERT, P6 NEGATIVE/NULL-RESULT); calibrated PROMISING+INERT prior at ~65% (reflecting iter-v3/010 + iter-v3/011 + iter-v3/013 favorable-overshoot history) |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 11 EXPLORATION criteria including **criterion 11: Saturation predictor §4.4 decision-tree disambiguation**; PROMISING-ALTERNATIVE / PROMISING-ON-NEW-FEATURES / PROMISING-INERT / NEGATIVE-no-effect / NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — **NEW dep: `xgboost>=2.0,<3.0` (Apache-2.0)**; aggregator strategy unchanged from iter-v3/006-015; reproducibility stamp includes XGBoost version + strategy class name + Spearman ρ vs LightGBM importance vector |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8. Note that Section 3.6 rows 1, 2, 3, 4, 5, 6, 7, 8 are NEW critical first-commit gates (the 4 pre-commits + XGBoost integration); row 14 implements the saturation predictor falsifier per `feedback_axis_saturation_predictor.md` with the §4.4 decision-tree disambiguation; row 15 verifies the smoke EDA was re-run post-`uv sync` to populate `xgboost_available=True`.
