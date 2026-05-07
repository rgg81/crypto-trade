# Phase 7.5 Critic Review — iter-v3/016 (Round 1 PRELIMINARY)

OVERALL: EXPLORATION-NEGATIVE (clean) — provisional pending one bit-identity boundary clarification

This is the **PRELIMINARY** review. After QR Round 2 disposition of the clarifications below (especially Clarification 1, which controls the §4.4 row 4 vs row 5 boundary), I will issue FINAL.

---

## Per-Check Status (12 checks; EXPLORATION carve-out applied to Check 3-edge)

### Check 1 — Look-Ahead Audit: PASS

Audited the NEW XgboostStrategy implementation at `src/crypto_trade/strategies/ml/xgb.py` and `src/crypto_trade/strategies/ml/optimization_xgb.py` end-to-end. The `_train_for_month` method (`xgb.py:276-565`) constructs train_indices via `(open_time >= train_start_ms) & (open_time < train_end_ms)` — strictly past of the test month boundary. Inside `_objective_xgb` (`optimization_xgb.py:150-226`), `TimeSeriesSplit(n_splits=cv_splits, gap=cv_gap)` produces sequential train/val temporal splits; train fit is on `feat_tr/y_train`, predict on `feat_val`. The `training_days` Optuna parameter trims training data via `cutoff_ms = val_start_time - training_days * 86_400_000` then masks `train_idx`, so cutoff is computed from val_start backward — past-only. NO new feature was introduced this iteration (the single axis is model architecture; V3_FEATURE_COLUMNS reverted to 13 = identical to iter-v3/013); look-ahead audit on features inherited from iter-v3/013 PASS. The XgboostStrategy `get_signal` path (`xgb.py:570-676`) consumes `_month_features` cache populated via `load_features_range(test_start_ms, test_end_ms)` keyed on the test month's start — no future leak across months.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66` candles. Runner's `_verify_label_leakage_gap()` enforced; run.log line 2 records `Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS`. The XGBoost path's `optimize_and_train_xgb` consumes `cv_gap=66` from `xgb.py:430` (`cv_gap = timeout_candles * n_symbols` — NOTE: the XGBoost path drops the `+1` margin compared to the static REQUIRED_GAP; `xgb.py:428-430` computes `timeout_candles = self.label_timeout_minutes // interval_minutes + 1 = 21 + 1 = 22; n_symbols = 3; cv_gap = 22 × 3 = 66`). End math equivalent. Confirmed `gap=66` propagated into TimeSeriesSplit.

### Check 3 — Multiple-Testing Correction (methodology axis): INFORMATIONAL (EXPLORATION carve-out)

`dsr.json` reports DSR=0.0 (single-seed exploration artifact, expected), PBO=0.0889 (slight improvement vs iter-v3/013 0.103), PSR=0.9888, n_trials=30, n_eff=6. Per skill EXPLORATION cadence rule, edge-axis thresholds (DSR > 0.95, PSR > 0.95) are INFORMATIONAL not BLOCK. PBO 0.0889 < 0.4 PASS. Per-cell PBO median structurally similar to iter-v3/013. n_eff dropped 7 → 6 (one Optuna dimension dropped under depthwise growth — `num_leaves` is no-op); this is principled and documented in brief §2.1, not a methodology defect. NOTE: the per_cell_pbo.csv shows several cells with PBO at extreme tails (LDOUSDT/2025-02 PBO=1.0, LDOUSDT/2026-02 PBO=0.9822, BCHUSDT/2023-06 PBO=0.904, LDOUSDT/2025-12 PBO=0.976) — these are pathological cells where Optuna's IS-best is anti-correlated with OOS, but the cross-cell mean correctly dilutes them. Audit-trail-noted; not a verdict driver under EXPLORATION.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` 13×13 lower triangular reads identically to iter-v3/013 baseline (no new features introduced; 13 inherited). Maximum |IC| in the matrix is `range_realized_vol_50 ↔ max_dd_window_50 = -0.685` (below the 0.70 redundancy gate by 0.015 — tight margin but PASS); next-largest is `ema_spread_atr_20 ↔ btc_ret_14d = +0.550`. No NEW feature introduced this iteration so the redundancy-gate frame is vacuous. Audit-trail-note: iter-v3/008 dropped `vwap_dev_50` precisely because `range_realized_vol_50 ↔ max_dd_window_50` was tight even then; the pair remains structurally adjacent and would re-fail at any future feature swap that tightens it further.

### Check 5 — ADF Stationarity: PASS (with EXPLORATION-tolerated early-window concentration)

`adf_test.csv` reports 1657/2041 cells stationary (81.2%). 384 non-stationary cells — concentrated in early IS months (2020-01, 2020-02, 2020-03 etc. show empty ADF values because `len < min_window`) and at LDO listing-edge months (LDO doesn't begin until 2024-09). This pattern is bit-identical to iter-v3/013/015 — same features, same windows, same NaN-emit behavior. No NEW feature introduced; the audit chain is inherited. PASS, same posture as iter-v3/015.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed EXPLORATION)

`pareto_front.csv` contains the single seed=42 row: OOS Sharpe +0.171 / OOS MaxDD 40.62% / Calmar 0.179 / PBO 0.0889 / 112 trades / 100% concentration (NB: the 100.00 concentration value is a single-seed-degenerate artifact when one symbol carries the entire portfolio's PnL after the other two go negative — TRX +18.82, BCH -2.35, LDO -9.19). EXPLORATION single-seed Pareto check is vacuous; per skill carve-out, PASS. The 40.62% OOS MaxDD and 4.26× MaxDD inflation vs iter-v3/013 are catalogued in the "What Was Measured" diary (per QE recommendation), but this is a NEGATIVE-iteration informational catalog entry, not a Pareto-check failure.

### Check 7 — Reproducibility: PASS

Engineering report stamps SHA `1aa3eb3` (setup commit), gate SHA `d5930fe` (PASS), brief SHA `10f3db9`. Runner uses explicit `feature_columns=V3_FEATURE_COLUMNS` (13 columns), confirmed at `run_baseline_v3.py` (`xgb.py:138-143` raises if None). Inner ensemble seed list literal: per `_derive_ensemble_seeds(seed=42, size=1) = [42]` for `--exploration` mode. CLI flag `--model xgboost` forwarded through `_build_v3_model` at runtime, confirmed in run.log via repeated "XGBoost model trained for YYYY-MM" lines. Strategy class actually used = `XgboostStrategy` per code path. xgboost 2.1.4 in pyproject (`xgboost>=2.0,<3.0`); semver pin valid. All 4 first-commit pre-commits verified PASS by gate `d5930fe` (drop tbr_zscore_30, add tbr_raw to V3_NON_FEATURE_COLUMNS, fix _write_feature_importance, ITERATION_LABEL "v3-016").

### Check 8 — Hypothesis-Implementation Alignment: PASS (with one classification-boundary clarification — see Clarification 1)

Single-axis discipline honored. Diff vs iter-v3/013:
- `LightGbmStrategy` → `XgboostStrategy` (the one varied axis: model architecture)
- `tbr_zscore_30` DROPPED (revert from iter-v3/015's V3_FEATURE_COLUMNS=14 to iter-v3/013's =13) — pre-condition restoration per brief §3.7
- `grow_policy='depthwise'`, `tree_method='hist'`, `n_jobs=1` PINNED (load-bearing axis-definition)
- `objective` swap for binary/ternary; `min_child_samples → min_child_weight`; `num_leaves` Optuna param dropped (no-op under depthwise); `scale_pos_weight = n_neg/n_pos` per-fit (substituting for LightGBM's `is_unbalance=True`)

Brief §1 hypothesis: "IS Sharpe within ±0.30 of iter-v3/013's +1.0088 (calibrated band [+0.70, +1.30] median +1.00) AND importance Spearman ρ < 0.85". REALIZED: IS Sharpe +0.5524 (OUTSIDE band by 0.15 below lower bound — Falsifier 1 NOT triggered since +0.10 lower threshold cleared; PATH B (NEGATIVE) §4.4 row 5 fires per IS Sharpe < +0.81 threshold) AND Spearman ρ ≈ 0.56 (importance-divergence prediction CONFIRMED, well below 0.85). Importance-divergence sub-hypothesis CONFIRMED; performance sub-hypothesis FALSIFIED. Joint outcome maps unambiguously to PATH B (§4.4 row 5).

### Check 9 — Symbol Exclusion Enforcement: PASS

Runner `run_baseline_v3.py:154-158` enforces `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` overlap check, raises if violated. Active universe BCH+LDO+TRX disjoint from V3_EXCLUDED_SYMBOLS = {BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, NEAR, DOGE, MKR}. PASS.

### Check 10 — Feature Isolation Enforcement: PASS

`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns 2 files but BOTH matches are inside DOCSTRINGS (the `__init__.py` cross-reference comment and `fracdiff_v3.py:23` "MUST NOT import from..." track-isolation comment). No actual cross-track import. PASS.

### Check 11 — Forming-Candle: PASS (inherited from staleness guard)

Pre-flight staleness guard fired clean per run.log: "Pre-flight: branch OK, symbols OK, data fresh (<16h), feature-cols=13 PASS". Per skill convention, forming-candle audit cleared at staleness gate. PASS.

### Check 12 — Library Version Pinning: PASS

`pyproject.toml`:
- `xgboost>=2.0,<3.0` NEW dep (Apache-2.0); brief §9 declared exactly this pin
- `lightgbm>=4.0` retained (default --model lgbm path unchanged)
- `optuna>=3.0` retained
- All other deps inherited from iter-v3/015

xgboost 2.1.4 actually loaded (per the absence of any version mismatch warnings in run.log). PASS.

---

## Clarifications to QR (5)

### Clarification 1 (LOAD-BEARING for §4.4 boundary call) — bit-identity test against iter-v3/013

Brief §4.4 row 4 (NULL-RESULT-class subtype) fires iff `|IS trades − 209| < 11 AND trade-roster bit-identical to iter-v3/013`. Observed |217 − 209| = **8 < 11** — this triggers the bit-identity test. Per-symbol IS distribution shifts (BCH 92→87 = −5; LDO 22→24 = +2; TRX 95→106 = +11) make bit-identity overwhelmingly unlikely, but the §4.4 row-4-vs-row-5 disambiguation requires explicit per-trade verification (4-decimal weighted_pnl match against iter-v3/013 per-symbol roster).

The QR's classification of **NEGATIVE (clean) per §4.4 row 5** is the structurally correct verdict given the dramatic per-symbol redistribution and Sharpe collapse, but row 5 strictly requires `|IS trades − 209| ≥ 11` per the brief's own decision-tree text. Two resolution paths:
- **(a)** QR explicitly verifies trade-roster non-bit-identity (which it almost certainly is, given +11 TRX trade shift) and documents this in the diary as a Critic-disposed boundary call.
- **(b)** QR demonstrates the brief's `|Δ| ≥ 11` row-5 condition is itself defective (the brief's threshold is a too-tight artifact of the saturation-falsifier `ceil(0.05 × 209) = 11`) and proposes a brief-template fix for iter-v3/017+ where row 5's condition is "either |Δ| ≥ 11 OR per-symbol shift > 5 trades on any symbol".

My read: NEGATIVE (clean) is the correct verdict regardless because the per-symbol roster IS demonstrably non-identical (+11 TRX, +2 LDO, −5 BCH); IS Sharpe +0.55 < +0.81 is the dominant signal. But the brief's literal text needs the verification or a documented exception.

### Clarification 2 — XGBoost importance-divergence: genuine architecture finding or hyperparam search artifact?

Spearman ρ ≈ 0.56 is well below the 0.85 falsifier threshold (Falsifier 4 of brief §4.3 confirmed). However, the brief's mechanism narrative ("XGBoost depth-wise growth surfaces signal across a broader feature set; LightGBM leaf-wise + GOSS may ignore consistent-but-small contributions") is a *structural* claim. The observed importance shuffle includes:
- `sym_vs_btc_ret_7d` (LightGBM rank **13/13** = dead last) → XGBoost rank **4/13** (jump of +9)
- `ema_spread_atr_20` (LightGBM rank **1/13** = top) → XGBoost rank **6/13** (drop of -5)
- `max_dd_window_50` (LightGBM rank 5) → XGBoost rank **1/13**

The QR's framing is that this confirms the structural mechanism. But an alternative interpretation — and one the Critic must surface — is that **at n_trials=10 single-seed Optuna budget, the importance ranking is dominated by hyperparam-search noise, not by a structural architecture difference**. Evidence pointing to the noise hypothesis:
- The IS Sharpe collapsed (-0.46) which suggests Optuna landed on a poor-fit configuration; importance distributions from poor-fit models are not reliable
- `max_dd_window_50` is depth-0 split for 2 of 3 per-symbol models (BCH rank 3, TRX rank 1, LDO rank 2) under XGBoost — this is consistent with depth-wise growth's tendency to lock onto a single globally-discriminative feature, but it could also be Optuna's narrow trial budget settling there by chance
- Single-seed n_trials=10 is exactly the regime where importance rankings have highest cross-seed variance (the `n_eff=6` from the trial-PCA confirms the search space is sparsely explored)

QR Clarification: please document in the diary whether the architecture-divergence finding is robust to seed/trial-budget perturbation, OR caveat the §4.4-row-5 catalog row to flag that the importance-divergence finding is not yet structurally validated.

### Clarification 3 — `_write_feature_importance` defect fix correctness

Verified: per-symbol CSVs (`feature_importance_BCHUSDT.csv`, `_LDOUSDT.csv`, `_TRXUSDT.csv`) AND portfolio CSV (`feature_importance.csv`) emitted in BOTH `in_sample/` and `out_of_sample/` per brief §3.5 sub-fix #3. Schema correct (feature, importance with rounded 4-decimal). Aggregation logic at `run_baseline_v3.py:1144-1196` iterates over ALL primary_model_pairs (3 = one per symbol), aggregates `_models` ensemble (size=1 in --exploration), accumulates `feature_importances_` per (sym, feature), then sorts and writes. The fix is correct and propagates correctly to BOTH split labels.

**Two outstanding caveats:**
**(a)** The aggregation reads `inner._models` which holds only the FINAL month's lazily-trained ensemble. So per-symbol importance CSVs are LAST MONTH'S models per symbol, NOT walk-forward-aggregated across all months. This is a strictly less misleading version of the iter-v3/015 defect, but the brief's intent was full month-aggregation.
**(b)** OOS feature_importance CSVs are byte-identical to IS CSVs (the loop emits the same dict to both subdirectories). Recommend: either drop the OOS CSV OR rename the output to clarify "model_importance.csv" with no split-directory duplication.

### Clarification 4 — Saturation falsifier predicted lower bound 165 vs realized 217

Brief §2.4 predicted IS trade count band [165, 250] median 200. Observed = 217 (above median by +17, well within band). The behavioral-effect prediction was explicitly bracketed *wider* than v3 has historically allowed for axis variations. Future EXPLORATION briefs should tighten the saturation falsifier predictor: a wide band [165, 250] effectively makes the falsifier non-falsifying for any non-NULL-result outcome.

QR Clarification: should the iter-v3/017 brief template tighten the saturation-predictor band to [iter_NNN_baseline ± 25%]?

### Clarification 5 — XGBoost depth-wise-growth maximum drawdown analysis

OOS MaxDD = 40.62% is nearly 4× iter-v3/013's 12.47%. The structural mechanism: "XGBoost depth-wise growth at depth 3-5 with 10 Optuna trials found higher-IS-PnL solutions at the cost of elevated drawdown that was not penalized in the optimization objective (binary cross-entropy, not Sharpe-ratio or Calmar-ratio objective)". This is a load-bearing finding for the iter-v3/017 axis decision: the failure mode is NOT "XGBoost is broken" but rather "depth-wise growth at this Optuna budget without a Sharpe/Calmar-based objective is risk-unaware".

QR Clarification: should the iter-v3/016 catalog row note that XGBoost is NOT closed for all hyperparam configurations, OR should the row note "model-architecture axis closed at the n_trials=10 + cross-entropy + depth-wise default"? This affects iter-v3/017 brief authoring.

---

## Pre-Commitment for iter-v3/017 Axis (Critic Prior, NOT Mandatory)

The model-architecture axis is closed by §4.4 row 5 (subject to Clarification 5 disposition). Per `feedback_structural_over_knob_exploration.md` priority order and the v3 catalog axis coverage (now 8 unique representations: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 + NEW feature family × 1 + NEW model architecture × 1), the unexplored axes for iter-v3/017 are, in priority order:

1. **NEW labeling architecture (Category 3)** — strongest prior. The triple-barrier label (ATR 2.0/1.0, 21-candle timeout) has been fixed since iter-v3/001; only ATR multipliers were tuned in iter-v3/010. Two sub-axes:
   - **Fixed-horizon return labels** (e.g., sign of 5-bar forward log-return): eliminates triple-barrier path-dependency, drastically simplifies the label noise structure.
   - **Meta-labeling** (binary classifier on top of an existing momentum/mean-reversion signal): per López de Prado AFML Ch. 3; orthogonal compounding component to all prior axes.

   Either is acceptable. Meta-labeling has slightly higher prior on PROMISING because it is structurally compoundable (the labeling change does not invalidate the existing 13-feature stack — it changes how the model uses them).

2. **NEW risk primitive (Category 4)** — weaker prior.

3. **NEW universe (Category 5)** — weakest prior on remaining axes.

**Critic STRONG prior**: iter-v3/017 axis = **NEW labeling architecture** (meta-labeling preferred; fixed-horizon as fallback). This aligns with QE's recommendation, and is the unique untested category. CONFIRMATION cadence is now 9 of 10 EXPLORATIONs since last CONFIRMATION; iter-v3/017 will be the 10th, after which CONFIRMATION can launch.

---

## Strong Prior on Classification

**EXPLORATION-NEGATIVE (clean) per §4.4 row 5** — concur with QE recommendation, conditional on Clarification 1 disposition (bit-identity verification or documented exception). All 12 methodology checks pass (or are appropriately INFORMATIONAL under EXPLORATION carve-out). The iteration tested its registered hypothesis cleanly (importance Spearman ρ < 0.85 confirmed), the model-architecture axis is now CLOSED at n_trials=10/cross-entropy/depth-wise default, and the catalog row will record the worst OOS delta in v3 history (Δ -2.53). The 4 first-commit pre-commits all verified PASS at QE setup.

iter-v3/017 axis prior = **NEW labeling architecture (Category 3)**; meta-labeling preferred for structural compoundability. After QR Round 2, FINAL Critic review issues with full per-check status.
