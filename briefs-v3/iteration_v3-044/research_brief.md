# Iteration v3-044 — Research Brief

**Type**: EXPLORATION (Cycle 3 #5 of 10)
**Track**: v3 (rigor arm) — forty-fourth iteration
**Branch**: `iteration-v3/044` (off iter-v3/043 head)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #5 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --exploration --seeds 1 --model xgboost
  - ENSEMBLE_SIZE=5 (auto; non-exploration inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Two-part axis (atomic revert + model swap):
  PART A (revert): REVERT efficiency_ratio_50 (V3_FEATURE_COLUMNS_TOP_N 15 → 14).
    iter-v3/043 DISASTROUS NEGATIVE (IS -0.8445 / OOS -0.8990; all 4 symbols broken).
    Kaufman ER REMOVED from V3_FEATURE_COLUMNS_TOP_N — no Path B/C sub-criterion needed
    because the EXPLORATION mandate fires on DISASTROUS result (worst-ever in cycle 3).
    RETURNS to iter-v3/042/040 14-feature anchor (the cycle 3 baseline restored at 040).
  PART B (model swap): SWITCH from LightGBM to XGBoost (--model xgboost CLI flag).
    iter-v3/016 NEGATIVE was at 3-sym/13-feature baseline with n_trials=10.
    Current baseline: 4-sym/14-feature stack with regime_momentum_signed_5d; n_trials=35.
    New conditions may produce different XGBoost decision surface.
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED from iter-v3/040-043.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  V3_FEATURES_PER_SYMBOL = {} (empty — UNCHANGED).
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — UNCHANGED).
  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED from iter-v3/043 (already reverted).
Predicted classification: NEGATIVE (prior art = iter-v3/016 NEGATIVE at -2.53 OOS delta;
  changed conditions are marginal — 4th symbol ALGO + regime_momentum_signed_5d + n_trials=35.
  Unlikely to flip NEGATIVE → POSITIVE but worth one test at current configuration.
  First XGBoost retest since iter-v3/016; 4-sym/14-feature stack is materially different.)
```

---

## Section 1 — Hypothesis

XGBoost with depth-wise tree growth on the 14-feature 4-symbol stack (including `regime_momentum_signed_5d`) may learn a meaningfully different decision surface than the iter-v3/016 3-symbol/13-feature configuration, because the addition of ALGOUSDT and `regime_momentum_signed_5d` changes the optimization landscape and XGBoost's depth-wise splits may interact differently with the composed feature's signed-regime signal.

Falsifier: if IS Sharpe < +0.40 (below iter-v3/016's +0.55 XGBoost IS), the hypothesis is rejected and model-architecture axis remains CLOSED for Cycle 3.

---

## Section 2 — IS-Only Numerical Evidence

No new analysis script is required for this iteration. The evidence base is prior-iteration results from committed engineering reports, which are IS-only (training fold data from the walk-forward cells):

**iter-v3/016 XGBoost results (3-sym/13-feature, n_trials=10):**

| Metric | iter-v3/016 XGBoost | iter-v3/013 LightGBM (baseline for that test) |
|--------|--------------------:|-----------------------------------------------:|
| IS monthly Sharpe | +0.5524 | +1.0088 |
| IS MaxDD | 38.69% | ~22.00% |
| IS n_trades | 217 | 209 |
| Spearman ρ (importance rank) | 0.56 (vs LGBM) | — |

**iter-v3/040 anchor (4-sym/14-feature, LightGBM, current cycle 3 baseline):**

| Metric | iter-v3/040 anchor |
|--------|--------------------|
| IS monthly Sharpe | +0.7926 |
| OOS monthly Sharpe | +1.7653 |
| IS n_trades | ~189 (cycle 3 baseline) |

**Conditions changed vs iter-v3/016:**
- 4th symbol ALGOUSDT added (REQUIRED_GAP 66 → 88)
- `regime_momentum_signed_5d` added (14th feature, composed; Category 2)
- n_trials = 35 (was 10 in iter-v3/016)
- Outer seeds = 1 (same EXPLORATION spec)

Source: `briefs-v3/iteration_v3-016/engineering_report.md` (SHA `1aa3eb3`), `briefs-v3/iteration_v3-040/engineering_report.md`.

---

## Section 3 — Proposed Changes

Three sub-changes (atomic; all required to set up the XGBoost retest on the clean 14-feature anchor):

**Sub-fix 1 — REVERT efficiency_ratio_50 (V3_FEATURE_COLUMNS_TOP_N 15 → 14):**
- Remove `"efficiency_ratio_50"` from `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py`.
- The `compute_efficiency_ratio_50` function in `engineered_v3.py` is RETAINED as dead code (zero revert cost; same pattern as vol_adj_autocorr/cross_asset_divergence_norm).
- `add_engineered_v3_features` dispatch of `efficiency_ratio_50` is REMOVED (parquet generation no longer computes it).
- Warmup period reverts: 51 bars → 50 bars (efficiency_ratio_50 warmup no longer needed for top-N).

**Sub-fix 2 — ITERATION_LABEL update:**
- `ITERATION_LABEL = "v3-043"` → `ITERATION_LABEL = "v3-044"` in `run_baseline_v3.py`.

**Sub-fix 3 — Update `_verify_feature_columns`:**
- Change length assertion from `n != 15` → `n != 14`.
- Remove `efficiency_ratio_50 MUST be present` check block.
- Add `efficiency_ratio_50 MUST be ABSENT` check.
- Update docstring to reflect iter-v3/044 state.
- Update all `print()` messages from "15-feature" / "iter-v3/043" references to "14-feature" / "iter-v3/044".
- Update per-symbol loop assertion from `len(sym_feats) != 15` → `len(sym_feats) != 14`.

**Unchanged (no sub-fix required):**
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` — already correct (reverted at iter-v3/043).
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` — already empty.
- `V3_FEATURES_PER_SYMBOL = {}` — already empty.
- `V3_MODELS = (BCH, LDO, TRX, ALGO)` — unchanged.
- `REQUIRED_GAP = 88` — unchanged.

**Run command change (no code change — CLI flag):**
- `uv run python run_baseline_v3.py --exploration --seeds 1 --model xgboost`
- The `--model xgboost` flag routes to `XgboostStrategy` (already implemented; `src/crypto_trade/strategies/ml/xgb.py` from iter-v3/016).

---

## Section 4 — Expected OOS Impact

**Predicted bands (IS / OOS monthly Sharpe):**

| Scenario | IS | OOS |
|----------|----|-----|
| Optimistic | +0.90 | +1.80 |
| Median | +0.60 | +1.15 |
| Pessimistic | +0.30 | +0.50 |

**Basis:**
- iter-v3/016 XGBoost IS was +0.55 on 3-sym/13-feature at n_trials=10. The 4th symbol and 14th feature add training signal; n_trials=35 adds Optuna budget. Plausible IS range: [+0.30, +0.90].
- OOS range reflects the wide uncertainty: iter-v3/016 OOS was +0.17 (catastrophic), but the conditions are materially different. If XGBoost latches onto regime_momentum_signed_5d more strongly than depth-wise LightGBM, OOS might improve toward [+0.50, +1.80].
- Anchor (LightGBM) at iter-v3/040: IS +0.79 / OOS +1.77. XGBoost rarely matches or beats LightGBM at equal Optuna budget on tabular data per prior v3 evidence.

**Falsifier:** if OOS Sharpe < +0.50, model-architecture axis is CLOSED for remainder of Cycle 3 (no further XGBoost tests). Classified NEGATIVE.

---

## Section 5 — Risk Mitigation

**R1 (consecutive-SL streak / cooldown):** Unchanged from baseline. Risk gate stack identical to iter-v3/040-043.

**R2 (cumulative drawdown brake):** Unchanged. RiskV3Wrapper applied identically to all 4 symbols.

**R3 (OOD z-score gate):** `zscore_threshold=2.0` unchanged (iter-v3/011 calibrated).

**Architecture risk:** XgboostStrategy is already implemented and tested (iter-v3/016 SHA `1aa3eb3`). No new risk from model-class swap — `--model xgboost` CLI flag routes to the same CPCV/walk-forward pipeline.

**IS-calibrated thresholds:** All gate thresholds (ADX 20.0, BTC trend 15.0, z-score 2.0, Hurst [0.05, 0.95], vol floor 0.33) unchanged from iter-v3/040 baseline.

**Simulated effect on prior iterations:** No code change to gate parameters; gate fire rates will differ only due to XGBoost producing different confidence score distributions (binary:logistic vs LightGBM binary calibration). Per iter-v3/016: BTC-killed trades ~34 — similar expected range.

---

## Section 6 — Risk Management Design

8-primitive gate stack (unchanged from iter-v3/040 anchor):

| Primitive | Config | IS Fire Rate (est.) | Notes |
|-----------|--------|---------------------|-------|
| BTC contagion kill | threshold_pct=15.0, lookback=42 bars | ~15% of signals killed | Enabled |
| Vol-adjusted sizing | ATR-based via natr_21_raw | Always active | Baseline (2.0, 1.0) |
| ADX gate | adx_threshold=20.0 | ~20-25% filtered | Enabled |
| Hurst regime gate | [0.05, 0.95] passband | ~5% filtered | Enabled |
| Feature z-score OOD | zscore_threshold=2.0 | ~10% filtered | Enabled |
| Low-vol floor | 0.33 threshold | ~5% filtered | Enabled |
| Hit-rate gate | enabled=False | DISABLED | Per iter-v2/045 lesson |
| Regime-conditional kill | disabled | DISABLED | Iter-v3/022 PARTIALLY-EFFECTIVE; deferred |

**Regime coverage:** 4 symbols (BCH/LDO/TRX/ALGO) across 24-month IS window covers 2023-2024 bull+bear regimes. XGBoost's depth-wise splits may handle the 2024 bull regime differently from LightGBM's leaf-wise GOSS approach.

**Fire-rate predictions:** Gate fire rates expected comparable to iter-v3/043 (same underlying data; XGBoost confidence scores differ from LightGBM but pass through same threshold checks).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Primary failure mode:** XGBoost repeats the iter-v3/016 pattern — IS Sharpe degrades vs LightGBM anchor (+0.79) by ≥0.30, landing below +0.50. The mechanism: depth-wise tree growth at max_depth=3-5 with n_trials=35 Optuna budget overfits the IS period for 2-3 of the 4 symbols, producing IS PnL that doesn't transfer OOS. Per iter-v3/016, BCH and LDO were the "victims" (IS profitable, OOS negative); TRX was the inverse. ALGO's behavior is unknown — if ALGO also inverts polarity OOS, all 4 symbols may show the IS/OOS polarity inversion pattern.

**What the gates should catch:** The BTC contagion kill and z-score OOD gate should fire at similar rates regardless of model architecture (the features feeding them are identical). If XGBoost produces higher-confidence false positives that pass all gates, the IS MaxDD will be elevated (iter-v3/016: IS MaxDD 38.69% vs LGBM 22.00%). A MaxDD IS >35% is a strong indicator of the failure mode.

**What failure looks like in metrics:** IS monthly Sharpe < +0.50, IS MaxDD > 35%, per-symbol IS/OOS polarity inversion for 2+ symbols, OOS Sharpe < +0.50. The PBO may improve (iter-v3/016: PBO 0.0889 vs LGBM 0.1034) even as Sharpe collapses — PBO is not a substitute for Sharpe in this failure mode.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria

**This is an EXPLORATION. MERGE criteria are not applicable. Outcome classification:**

```
PROMISING: IS Sharpe >= +0.60 AND OOS Sharpe >= +1.55 (≥ iter-v3/040 anchor OOS)
PROMISING-MARGINAL: IS Sharpe >= +0.40 AND OOS Sharpe >= +0.90
NEGATIVE: IS Sharpe < +0.40 OR OOS Sharpe < +0.50
DISASTROUS: IS Sharpe < 0.0 OR OOS Sharpe < 0.0 (same as iter-v3/043)
```

**Model-architecture axis closure rule:** If classified NEGATIVE or DISASTROUS, XGBoost model-architecture axis is CLOSED for remainder of Cycle 3 (iterations 044-049). Cannot be renegotiated post-hoc.

**If PROMISING:** XGBoost becomes a candidate for a Cycle 3 CONFIRMATION bundle — but only in combination with other PROMISING ingredients, not as a standalone CONFIRMATION (single-axis CONFIRMATION with known NEGATIVE prior art at iter-v3/016 does not meet the evidence bar).

---

## Section 9 — Library Stack Declaration

```
lightgbm == 4.6.0        # baseline model (NOT used for this iter's primary run)
xgboost == 2.1.4         # primary model — installed since iter-v3/016; pinned in pyproject.toml
optuna == 4.8.0          # hyperparameter tuning
numpy == 2.2.6
pandas == 3.0.0
scikit-learn == 1.8.0
scipy == 1.17.0
statsmodels == 0.14.6    # adfuller for ADF stationarity testing
pyarrow == 23.0.1
```

**mlfinlab / mlfinpy:** Not used in this iteration. CPCV implemented natively in `validation_v3.py` (established iter-v3/001). No mlfinlab license risk.

**pypbo:** Used for PBO computation in `pbo_from_cpcv`. Version pinned in pyproject.toml.

**fracdiff:** Used for `fracdiff_logclose_dstat` and `fracdiff_logvolume_dstat` feature generation. Version >= 0.10 pinned.

**XgboostStrategy fallback:** No fallback needed. `xgboost 2.1.4` is installed and tested since iter-v3/016 (SHA `1aa3eb3`). `--model xgboost` CLI flag routes to `XgboostStrategy` in `src/crypto_trade/strategies/ml/xgb.py`.
