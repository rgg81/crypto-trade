# Iteration v3-024 — Research Brief

**Type**: EXPLORATION (cadence #6 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 1 — NEW external-data-source feature family — cross-asset variant)** — `btc_funding_rate_zscore_30` cross-asset funding stress signal per Critic FINAL `c4574af` of iter-v3/023 Recommendation #3)
**Track**: v3 (rigor arm) — twenty-fourth iteration
**Branch**: `iteration-v3/024` (off `iteration-v3/023` head; brief authored after EDA committed at SHA `afdb8bc`)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (PRELIMINARY-VALIDATED through iter-v3/020/021/022/023)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–023 briefs / engineering reports / Critic FINALs / diaries; the new iter-v3/024 EDA at SHA `afdb8bc` (`analysis/iteration_v3-024/btc_funding_eda.py` + outputs).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #6 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW external-data-source feature family —
                       cross-asset variant. DROP per-symbol
                       funding_rate_zscore_30 from V3_FEATURE_COLUMNS
                       (revert 14 → 13). ADD btc_funding_rate_zscore_30
                       to V3_FEATURE_COLUMNS (13 → 14). Cross-asset
                       feature: BTC's funding rate broadcast to all 3
                       per-symbol models.
                       Per Critic FINAL Rec #3 of iter-v3/023 (SHA `c4574af`).
Cadence: EXPLORATION #6 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 1 (NEW external-data-source feature family — cross-asset variant)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob.
NOT a feature-pruning variation. NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — cross-asset funding axis (per Critic FINAL `c4574af` of iter-v3/023 Recommendation #3 + new memory rule `feedback_v3_inert_features_at_higher_budget.md`)**:

After iter-v3/023 EXPLORATION-NEGATIVE clean (per-symbol `funding_rate_zscore_30` retest at n_trials=35 confirmed INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET; OOS Sharpe -1.07 — WORST single-seed OOS in v3; Critic FINAL SHA `c4574af`, diary commit `b97b2a1`):

- The PER-SYMBOL funding feature is **PERMANENTLY-CLOSED for v3** at the catalog level: 2 EXPLORATION data points (iter-v3/019 + iter-v3/023) both produce rank 14/14 across LDO+TRX+Portfolio at BOTH n_trials=10 AND n_trials=35. The feature is genuinely structurally INERT in v3's per-symbol-LightGBM-on-13-features architecture.
- iter-v3/023 closeout established new memory rule `feedback_v3_inert_features_at_higher_budget.md`: drop INERT features after 1 EXPLORATION verdict; do not retest at higher budget.
- Per Critic FINAL Rec #3 of iter-v3/023: **iter-v3/024 axis = `btc_funding_rate_zscore_30` cross-asset variant**. STRUCTURALLY DISTINCT mechanism vs iter-v3/019/023:
  - iter-v3/019/023: each per-symbol model received its OWN funding z-score (BCH model saw BCH funding; LDO model saw LDO funding; TRX model saw TRX funding). The model couldn't surface a cross-asset stress signal because the feature was TOO local.
  - iter-v3/024: ALL 3 models receive BTC's funding z-score (broadcast — identical column values across BCH/LDO/TRX training datasets at any given timestamp). The feature carries MARKET-WIDE leveraged-positioning information.
- Forward priority order from `feedback_v3_iter019_axis_priorities.md` post iter-v3/023:
  1. ~~HIGH — NEW feature families (iter-v3/019/023)~~ — PERMANENTLY-CLOSED for per-symbol variant; iter-v3/024 = cross-asset variant (STRUCTURALLY DISTINCT mechanism)
  2. ~~HIGH — Concentration architecture sub-axis A (per-symbol cap, iter-v3/020)~~ — CLOSED-mechanism
  3. ~~HIGH — Concentration architecture sub-axis B (universe expansion, iter-v3/021)~~ — CLOSED-symbols-cycle
  4. ~~MEDIUM (ELEVATED) — TRX/2022-Q4 regime gate (iter-v3/022)~~ — PARTIALLY-EFFECTIVE-CLOSED at single-seed
  5. MEDIUM — DSR gate reformulation
  6. **HIGH — NEW external-data-source feature family CROSS-ASSET variant (iter-v3/024 mandate, this iteration)**
  7. LOW — Knob axes (saturated)

**iter-v3/024 first EXPLORATION axis = HIGH-priority — `btc_funding_rate_zscore_30` cross-asset funding stress signal.** Cannot be renegotiated post-hoc per Critic FINAL `c4574af` of iter-v3/023.

**Why cross-asset funding now (post iter-v3/023 INERT-CONFIRMED)**:

- The structural-INERT classification of per-symbol funding at 2 trial budgets has a precise scope: it applies to the per-symbol-LightGBM-on-13-features architecture where each model's loss surface is separately optimized on its own per-symbol funding signal. Cross-asset funding is a DIFFERENT mechanism: ALL 3 models share the SAME column values; the feature is a system-stress indicator, not a per-symbol micro-signal.
- BTC funding rate captures market-wide leveraged-position crowding. Per BIS WP 1087 (2025), 10% carry shock predicts 22% liquidation jump — the systemic signal. The same paper notes that altcoin liquidation cascades are highly coupled to BTC funding-stress regimes.
- The 13-feature stack already contains `btc_ret_14d` (BTC 14-day return, cross-asset macro feature). EDA confirms `btc_funding_rate_zscore_30` has 0.18 IC with `btc_ret_14d` (well below 0.50 brief target) — it carries signal not present in `btc_ret_14d` (positioning-stress vs return-momentum).
- Single-axis discipline preserved: ONE feature swap (drop per-symbol funding; add BTC cross-asset funding); regime gate stays disabled (was iter-v3/022 axis, kept at iter-v3/023 spec); ITERATION_LABEL=v3-024.

**Why this experiment is inexpensive at iter-v3/024**:

- BTC funding rate cache fetched at iter-v3/024 setup (verified at brief authoring: `data/funding_rates/BTCUSDT.csv` extant with 7295 rows from 2020-08 onward; 7144 z-scored non-NaN values).
- The funding_v3.py module (preserved from iter-v3/019 zero revert cost) provides the rolling-z-score computation primitive. Implementation: extend the module with `compute_btc_funding_rate_zscore` (or new file `cross_funding_v3.py`) that loads BTC funding cache and broadcasts to per-symbol kline frames.
- Wall-clock impact: +1 cross-asset feature column at 3-symbol universe × n_trials=35 expected to add ~7% to feature-loading time (similar to iter-v3/019's overhead profile). Total wall-clock predicted 8-15 min (well within 2h cap).

After iter-v3/024 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PERMANENTLY-CLOSED per-symbol variant) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + NEW external-data-source feature RETEST at higher Optuna budget × 1 (CLOSED-PERMANENTLY) + **NEW external-data-source feature CROSS-ASSET variant × 1** = 16 unique axis representations after iter-v3/024.

---

## Section 1 — Hypothesis

Replacing per-symbol `funding_rate_zscore_30` (PERMANENTLY-CLOSED INERT) with cross-asset `btc_funding_rate_zscore_30` (BTC's funding rate z-score broadcast to all 3 per-symbol models) on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS) — at the EXPLORATION default n_trials=35 — will produce **importance rank improvement** (predicted ≤7 for ≥ 1 symbol) AND **IS Sharpe Δ ≥ +0.10** if the cross-asset funding stress signal carries information distinct from `btc_ret_14d` (the existing macro feature). Predicted IS Sharpe band [+0.30, +0.55] median +0.40 (anchor +0.38; modest single-axis lift); predicted OOS Sharpe band [+0.40, +0.65] median +0.50 (anchor +0.39).

**Mechanism explanation** (why a cross-asset BTC funding signal should surface where per-symbol funding didn't): in iter-v3/019/023's INERT-CONFIRMED diagnosis, the per-symbol funding feature was REDUNDANT with each per-symbol's existing 13-feature stack — the per-symbol model had already calibrated its trade selection through volume/return/regime features that encode the same per-symbol leverage information. The CROSS-ASSET BTC funding signal is fundamentally different: it's a SYSTEM-STRESS indicator (market-wide liquidation pressure proxy) that:
- Is identical across all 3 per-symbol training datasets (broadcast feature)
- Captures BTC's funding regime, which empirically drives altcoin liquidation cascades (per BIS WP 1087, 2025)
- Has 0.18 IC with `btc_ret_14d` — partial overlap with macro return, but carries POSITIONING information not present in the return signal
- Has rank-IC magnitude 0.0474 (LDO 3-bar, NEGATIVE-direction) — comparable to per-symbol funding's 0.0485 max in iter-v3/019, but in a DIFFERENT mechanism (cross-asset stress vs per-symbol micro)

**Why iter-v3/019/023's INERT pattern doesn't directly predict iter-v3/024's outcome**:

The structural-INERT classification at iter-v3/019/023 has a SCOPE clause: it applies to per-symbol-LightGBM-on-13-features architecture where each model's loss surface is separately optimized on its own per-symbol funding signal. Cross-asset funding violates the SCOPE: the feature is a SYSTEM-LEVEL signal (BTC funding rate z-score) broadcast to all 3 per-symbol models, fundamentally different from a per-symbol micro-feature. The hypothesis is that the model's tree splits will learn to use BTC funding stress as a regime classifier (gate trades during high funding-stress periods) rather than as a per-symbol return predictor.

**Direction symmetry**: BTC funding stress is naturally bipolar (positive z = market-wide leveraged-long crowding, negative z = market-wide leveraged-short crowding). EDA shows 8 of 9 NEGATIVE-direction rank-IC cells (high BTC funding → low forward return; mean-reversion direction across BCH/LDO/TRX horizons) — CONSISTENT with the per-symbol funding pattern but at a DIFFERENT mechanism.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**EDA reference**: `analysis/iteration_v3-024/btc_funding_eda.py` + outputs at SHA `afdb8bc`. Brief committed AFTER EDA outputs (Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only window 2023-03-24 → 2025-03-24):
- `data/funding_rates/BTCUSDT.csv` — 7295 BTC funding rate rows; 7144 z-scored non-NaN values
- `data/{BCH,LDO,TRX}USDT/8h.csv` — 8h kline data
- `data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet` — 13 V3_FEATURE_COLUMNS

### 2.1 EDA evidence (5 of 5 IS-only gates PASS)

| Gate | Threshold | Observed | PASS? |
|---|---|---|---|
| Coverage IS window per symbol | ≥ 80% | **100%** all 3 (2193/2193 each) | ✓ |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (HARD) | < 0.70 | **0.1921** | ✓ |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (BRIEF target) | < 0.50 | **0.1921** | ✓ |
| ADF p-value per symbol | < 0.05 | **0.0** all 3 (structural stationarity) | ✓ |
| Max \|rank-IC\| vs forward returns | ≥ 0.02 | **0.0474** (LDO 3-bar) | ✓ |

### 2.2 Top correlations vs 13 V3_FEATURE_COLUMNS (per symbol)

| Symbol | Top feature | IC | Interpretation |
|---|---|---:|---|
| LDO | ema_spread_atr_20 | **0.1921** | EMA-spread vs ATR captures momentum-vs-volatility regime; weakly aligned with BTC funding stress |
| BCH | btc_ret_14d | 0.1779 | BTC 14d return shares macro signal with BTC funding rate (positional pressure) |
| LDO | btc_ret_14d | 0.1779 | (broadcast) |
| TRX | btc_ret_14d | 0.1779 | (broadcast) |
| BCH | ema_spread_atr_20 | 0.1765 | Same regime signal as LDO |
| BCH | max_dd_window_50 | 0.1653 | Drawdown regime correlates with leveraged-stress periods |
| LDO | range_realized_vol_50 | -0.1519 | Inverted: volatility-spike periods often have negative funding |

**No single feature exceeds 0.20 IC**. The maximum 0.1921 is well below the 0.50 brief target and 0.70 hard gate. The cross-asset BTC funding signal carries genuinely new information vs the existing 13-feature stack.

### 2.3 Rank-IC vs forward returns (per symbol, 1/3/7-bar horizons)

| Symbol | Horizon (bars) | Rank-IC | \|Rank-IC\| | Direction |
|---|---:|---:|---:|---|
| LDO | 3 | **-0.0474** | **0.0474** | NEGATIVE (mean-reversion: high BTC funding stress → low LDO 3-bar return) |
| LDO | 7 | -0.0441 | 0.0441 | NEGATIVE (consistent with 3-bar) |
| TRX | 3 | -0.0303 | 0.0303 | NEGATIVE |
| BCH | 7 | -0.0210 | 0.0210 | NEGATIVE (above 0.02 floor) |
| LDO | 1 | -0.0128 | 0.0128 | weakly NEGATIVE |
| TRX | 1 | -0.0108 | 0.0108 | weakly NEGATIVE |
| BCH | 3 | -0.0121 | 0.0121 | weakly NEGATIVE |
| TRX | 7 | -0.0053 | 0.0053 | near-zero |
| BCH | 1 | -0.0026 | 0.0026 | near-zero |

**8 of 9 cells NEGATIVE-direction** (high BTC funding → low forward return; mean-reversion / liquidation-cascade pressure direction). Strongest signal: LDO at 3-bar (0.0474) and 7-bar (0.0441) horizons. **Comparable in magnitude** to per-symbol funding's max 0.0485 in iter-v3/019, but the SCOPE is different (cross-asset stress vs per-symbol micro).

### 2.4 Distribution (broadcast feature; identical across 3 symbols)

| Statistic | Value |
|---|---:|
| n (IS bars per symbol) | 2193 |
| mean | -0.001 |
| std | 1.435 |
| min | -10.0 (clipped) |
| p01 | -3.98 |
| p05 | -1.80 |
| p25 | -0.62 |
| p50 | 0.00 |
| p75 | 0.67 |
| p95 | 1.69 |
| p99 | 3.50 |
| max | 10.0 (clipped) |
| skew | -0.79 |
| kurtosis | 15.94 (heavy-tailed; clipped to ±10) |

**Heavy-tailed distribution clipped to ±10**: like per-symbol funding, BTC funding has funding-floor-clamp regimes producing extreme z-scores that are clipped for LightGBM training stability.

### 2.5 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Predicting the IS trade-count change for iter-v3/024 vs iter-v3/018 anchor (3-symbol BCH+LDO+TRX universe; iter-v3/018 anchor IS = 172 multi-seed mean trade count):

| Scenario | Expected IS trade count | Mechanism |
|---|---:|---|
| Lower bound | ~145 | At higher budget, Optuna may converge on shorter-tree models that gate trades selectively when BTC funding stress drives a new threshold |
| Median (typical NEW-feature behavior at higher budget) | ~175 | Model uses cross-asset feature as a partial regime filter; trade roster shifts ~5-10% from anchor 172 |
| Upper bound | ~205 | Model includes the feature but it has moderate importance; trade roster ~iter-v3/019/023's 195-209 baseline |
| **Saturation falsifier band (per `feedback_axis_saturation_predictor.md` ±25% rule)** | **[129, 215]** | Anchor: iter-v3/018 IS trades 172; band low = 0.75 × 172 = 129; band high = 1.25 × 172 = 215 |

**Counterfactual reference**: iter-v3/019 single-seed=42 n_trials=10 with PER-SYMBOL funding (14 cols): IS = 209. iter-v3/020/021/022 single-seed=42 n_trials=35 without funding (13 cols): IS = 200. iter-v3/023 single-seed=42 n_trials=35 with PER-SYMBOL funding (14 cols): IS = 195. iter-v3/024 single-seed=42 n_trials=35 with CROSS-ASSET BTC funding (14 cols): predicted band [145, 205] median 175.

**Falsifier reading**: if observed iter-v3/024 IS trades < 129 OR > 215 (saturation band), the new-feature-axis behavioral effect deviated from prediction.

### 2.6 PATH-A vs PATH-B vs PATH-C predictor calibration (load-bearing)

**Pre-committed PATH classification table** (load-bearing for Critic FINAL):

| Critic verdict path | Observed IS Sharpe Δ vs iter-v3/018 multi-seed | Observed importance rank for btc_funding_rate_zscore_30 | Catalog row | Next iteration |
|---|---|---|---|---|
| **PATH A (PROMISING)** | Δ ≥ +0.10 (i.e., observed ≥ +0.4788) | rank ≤7 for ≥ 1 symbol | "Cross-asset BTC funding surfaces — genuine system-stress signal at higher budget" | Keep btc_funding for CONFIRMATION (iter-v3/029+) bundling consideration |
| **PATH B (PROMISING-INERT)** | Δ in [-0.10, +0.10] (i.e., observed in [+0.28, +0.48]) | rank still 14/14 across all 3 OR rank ≤7 fails for ≥ 1 symbol | "Cross-asset BTC funding INERT — ALL funding-derived axes closed (funding family permanently dead in v3)" | iter-v3/025 = different axis category (DSR gate reformulation OR a structurally-different feature family — Open Interest delta, basis spread, on-chain proxies) |
| **PATH C (NEGATIVE)** | Δ < -0.10 (i.e., observed < +0.2788) | importance non-zero but feature actively hurts the model | "Cross-asset BTC funding actively hurts — funding family confirmed structurally orthogonal to v3 architecture" | iter-v3/025 = different axis category — NOT another funding variant |

The PATH classification IS the Critic FINAL outcome; cannot be renegotiated post-hoc per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_inert_features_at_higher_budget.md` LOCKED.

### 2.7 Setup integrity (verified at brief authoring)

- iter-v3/024 EDA outputs at SHA `afdb8bc` exist in repo and reference 5 IS-only gates pass
- BTC funding rate cache extant at `data/funding_rates/BTCUSDT.csv` (7295 rows; verified at iter-v3/024 EDA run)
- iter-v3/023 head HEAD at brief authoring is `b97b2a1` (diary commit); iter-v3/024 brief lands AFTER (Phase 5.5 sequencing)
- Past-only discipline: `compute_btc_funding_rate_zscore` uses `.shift(1)` on rolling stats so bar t z-score uses bars t-30...t-1 only — STRICTLY past-only (mirrors `compute_funding_rate_zscore` from `funding_v3.py`)
- funding_v3 module + fetch-funding CLI infrastructure preserved at iter-v3/019 zero revert cost (extends naturally for cross-asset variant)

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013, baselined at iter-v3/018)

| Symbol | iter-v3/023 status | iter-v3/024 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED | UNCHANGED |
| HBARUSDT | DROPPED at iter-v3/022 | UNCHANGED |
| AVAXUSDT | DROPPED at iter-v3/022 | UNCHANGED |

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/023 (current) | iter-v3/024 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — DROP per-symbol funding; ADD cross-asset BTC funding (V3_FEATURE_COLUMNS = 14)

| Feature column | iter-v3/023 (V3_FEATURE_COLUMNS_TOP_N) | iter-v3/024 (V3_FEATURE_COLUMNS_TOP_N) |
|---|---|---|
| max_dd_window_50 | KEEP | UNCHANGED |
| ema_spread_atr_20 | KEEP | UNCHANGED |
| ret_kurt_50 | KEEP | UNCHANGED |
| ret_skew_200 | KEEP | UNCHANGED |
| range_realized_vol_50 | KEEP | UNCHANGED |
| hurst_diff_100_50 | KEEP | UNCHANGED |
| ret_kurt_200 | KEEP | UNCHANGED |
| hurst_100 | KEEP | UNCHANGED |
| btc_ret_14d | KEEP | UNCHANGED |
| ret_skew_50 | KEEP | UNCHANGED |
| vwap_dev_20 | KEEP | UNCHANGED |
| ret_autocorr_lag1_50 | KEEP | UNCHANGED |
| sym_vs_btc_ret_7d | KEEP | UNCHANGED |
| **funding_rate_zscore_30** | **PRESENT** (per-symbol; iter-v3/023 RETEST INERT-CONFIRMED) | **DROPPED** (per Critic FINAL Rec #1 of iter-v3/023; per-symbol funding family PERMANENTLY-CLOSED) |
| **btc_funding_rate_zscore_30** | (not present) | **NEW** (cross-asset; BTC funding broadcast to all 3 per-symbol models) |

`len(V3_FEATURE_COLUMNS) == 14` after iter-v3/024 (DROP per-symbol funding 14 → 13; ADD cross-asset BTC funding 13 → 14). `_verify_feature_columns()` updated to assert `len == 14` and `'btc_funding_rate_zscore_30' in V3_FEATURE_COLUMNS` and `'funding_rate_zscore_30' NOT in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — UNCHANGED (single-axis: feature swap only)

| Parameter | iter-v3/023 (current) | iter-v3/024 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| `adx_threshold` | 20.0 | UNCHANGED |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| `enable_per_symbol_cap` | False | UNCHANGED |
| `enable_regime_gate` | False | UNCHANGED (kept disabled per iter-v3/023) |

### 3.5 Sub-fix decomposition (5-item)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **DROP `funding_rate_zscore_30` from `V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py` (revert iter-v3/023 re-add); **ADD `btc_funding_rate_zscore_30`** at the end. Total 14 columns. Update docstring with iter-v3/024 history line. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'btc_funding_rate_zscore_30' in V3_FEATURE_COLUMNS and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 2 | **Implement `compute_btc_funding_rate_zscore`** in `src/crypto_trade/features_v3/funding_v3.py` (extend the existing module rather than create a new file — the per-symbol primitive `compute_funding_rate_zscore` lives there, and the cross-asset variant is a natural extension). The function: loads BTC funding cache (`data/funding_rates/BTCUSDT.csv`); computes past-only z-score on the BTC stream; broadcasts the z-score to per-symbol kline frames via timestamp left-join. Add `add_btc_funding_v3_features` as the GROUP_REGISTRY entry point (callable on per-symbol kline frames). | `python -c "from crypto_trade.features_v3.funding_v3 import compute_btc_funding_rate_zscore, add_btc_funding_v3_features"` exits 0 |
| 3 | **Register `btc_funding_v3` in GROUP_REGISTRY** in `src/crypto_trade/features_v3/__init__.py` (separate from `funding_v3` because the loaders differ: per-symbol funding reads <SYM> file; cross-asset reads BTCUSDT file regardless of which symbol is being processed) | `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'btc_funding_v3' in GROUP_REGISTRY"` exits 0 |
| 4 | **Update `_verify_feature_columns()` assertion** in `run_baseline_v3.py`: assert `'btc_funding_rate_zscore_30' in V3_FEATURE_COLUMNS` and `'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS`. Total still 14. **Update `ITERATION_LABEL`** from `"v3-023"` to `"v3-024"`. | `grep -E 'ITERATION_LABEL.*=.*"v3-024"' run_baseline_v3.py` exits 0 |
| 5 | **Regenerate v3 feature parquets** via `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,MKRUSDT --interval 8h --track v3 --format parquet --workers 4`. Existing CLI command. `add_btc_funding_v3_features` registered in GROUP_REGISTRY runs as part of GROUP_REGISTRY iteration, producing fresh `data/features_v3/*.parquet` with the new 14-column feature set (per-symbol funding column REMOVED; cross-asset BTC funding column ADDED). **Pre-flight check**: verify `data/funding_rates/BTCUSDT.csv` extant + non-empty. | `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'btc_funding_rate_zscore_30' in df.columns and 'funding_rate_zscore_30' not in df.columns and df['btc_funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0 (and same check for LDO/TRX) |
| 6 | **Run `--exploration --seeds 1`** on the 3-symbol universe with the 14-feature set (n_trials=35 default) | `test -f reports-v3/iteration_v3-024/comparison.csv` |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 13 verifiers

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **`V3_FEATURE_COLUMNS` has `btc_funding_rate_zscore_30` and NOT `funding_rate_zscore_30` at 14 columns** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'btc_funding_rate_zscore_30' in V3_FEATURE_COLUMNS and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 2 | **`btc_funding_v3` registered in GROUP_REGISTRY (NEW at iter-v3/024)** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'btc_funding_v3' in GROUP_REGISTRY"` exits 0 |
| 3 | **`fetch-funding` CLI subcommand operative (preserved from iter-v3/019)** | `src/crypto_trade/main.py` | `uv run crypto-trade fetch-funding --help` exits 0 |
| 4 | **BTC funding rate cached** | `data/funding_rates/BTCUSDT.csv` | `python -c "from pathlib import Path; assert Path('data/funding_rates/BTCUSDT.csv').exists()"` exits 0 AND row-count > 5000 |
| 5 | **Per-symbol parquet has `btc_funding_rate_zscore_30` (broadcast) and NO `funding_rate_zscore_30`** | `data/features_v3/{BCH,LDO,TRX,MKR}USDT_8h_features.parquet` | `python -c "import pandas as pd; r=[(pd.read_parquet(f'data/features_v3/{s}USDT_8h_features.parquet')) for s in ['BCH','LDO','TRX','MKR']]; assert all('btc_funding_rate_zscore_30' in df.columns and 'funding_rate_zscore_30' not in df.columns for df in r); assert all(df['btc_funding_rate_zscore_30'].notna().mean() > 0.95 for df in r)"` exits 0 |
| 6 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 7 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 8 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 9 | **`adx_threshold=20.0` UNCHANGED (iter-v3/013 baseline)** | `run_baseline_v3.py` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 10 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 11 | **`enable_regime_gate=False` UNCHANGED (kept disabled per iter-v3/023)** | `run_baseline_v3.py` | `grep -E 'enable_regime_gate=False' run_baseline_v3.py` exits 0 |
| 12 | **`enable_per_symbol_cap=False` UNCHANGED (kept disabled per iter-v3/020 closeout)** | `run_baseline_v3.py` | `grep -E 'enable_per_symbol_cap=False' run_baseline_v3.py` exits 0 |
| 13 | **V3_MODELS has exactly 3 entries; MKR/HBAR/AVAX NOT present** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3 and 'MKRUSDT' not in {s for _,s in m.V3_MODELS} and 'HBARUSDT' not in {s for _,s in m.V3_MODELS} and 'AVAXUSDT' not in {s for _,s in m.V3_MODELS}"` exits 0 |
| — | **`ITERATION_LABEL` updated to `"v3-024"`** | `run_baseline_v3.py:102` | `grep -E 'ITERATION_LABEL.*=.*"v3-024"' run_baseline_v3.py` exits 0 |
| — | **Sub-fix #6 produces comparison.csv** | runner | `test -f reports-v3/iteration_v3-024/comparison.csv` |
| — | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in band [129, 215] (anchor iter-v3/018 IS trades 172). PLUS SECONDARY VERIFIER: `btc_funding_rate_zscore_30` appears in feature_importance.csv non-zero for ≥ 1 of 3 per-symbol models. PRIMARY DISAMBIGUATION: rank ≤7 for ≥ 1 symbol. | comparison.csv + feature_importance.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-024/comparison.csv'); n=int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert 129 <= n <= 215, f'IS trades {n} OUTSIDE saturation band [129, 215]'"` exits 0 AND feature-importance non-zero for cross-asset BTC funding feature on ≥ 1 of 3 models AND PATH-A/B/C classified per §2.6 |

### 3.7 Inheritance from iter-v3/023

The `iteration-v3/024` branch was branched from `iteration-v3/023` head (HEAD `b97b2a1` = iter-v3/023 diary commit). Critical inheritance verifiers (run before any code edits in Phase 6):

- BEFORE iter-v3/024 sub-fix #1: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0
- BEFORE iter-v3/024 sub-fix #4: `grep -E 'ITERATION_LABEL.*=.*"v3-023"' run_baseline_v3.py` exits 0
- AFTER iter-v3/024 sub-fix #1: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'btc_funding_rate_zscore_30' in V3_FEATURE_COLUMNS and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0
- AFTER iter-v3/024 sub-fix #5: `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'btc_funding_rate_zscore_30' in df.columns and df['btc_funding_rate_zscore_30'].notna().mean() > 0.95 and 'funding_rate_zscore_30' not in df.columns"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/024 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

Anchor: iter-v3/018 BOOTSTRAP baseline IS Sharpe **+0.3788 (multi-seed mean)** / **+0.4563 (seed 42 single)**.

| Metric | iter-v3/018 (anchor multi-seed) | iter-v3/018 (anchor seed-42 single) | iter-v3/024 prediction (3-symbol, 14-feature, +btc_funding @ n_trials=35) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.4563 | **predicted [+0.30, +0.55] (median +0.40)** = Δ vs multi-seed anchor [-0.08, +0.17] (median +0.02) |
| IS trades | 172 (multi-seed mean cumul) | 172 (seed 42) | **predicted [129, 215]** (saturation band ±25%); inner band [145, 205] median 175 |
| OOS trades | 90.5 (mean) / 102 (seed 42) | 102 (seed 42) | **informational ~75-130** |
| OOS Sharpe | +0.3869 (mean) / +0.2343 (seed 42) | +0.2343 | **informational; predicted [+0.40, +0.65] median +0.50** if PATH A; predicted [+0.20, +0.50] if PATH B; predicted [-0.50, +0.10] if PATH C |
| Phase 6 wall-clock | 4.54h | (CONFIRMATION mode) | predicted 8-15 min (3 symbols, 14-column feature set; n_trials=35 default), hard cap 2h |

The IS prediction band [+0.30, +0.55] (Δ over multi-seed anchor +0.02 median) is calibrated against:
- iter-v3/018 anchor +0.3788 multi-seed mean
- The single-axis-swap nature of the iteration (1 column swapped: per-symbol funding → cross-asset BTC funding)
- The empirical NEW-feature-family axis-category history at n_trials=35 (iter-v3/023 INERT-CONFIRMED for per-symbol variant) — iter-v3/024 is the first CROSS-ASSET variant data point in v3
- Median +0.40 sits modestly above iter-v3/018 anchor +0.38 by +0.02 — consistent with the Bayesian prior that funding-derived features have shown INERT pattern at the per-symbol level; the cross-asset variant is testing whether the SCOPE matters

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < iter-v3/018 multi-seed anchor +0.3788 - 0.10 = +0.2788 → the new feature actively hurt the model OR the axis didn't propagate. Verdict: **PATH C (NEGATIVE)** on cross-asset feature axis (clean). Catalog row marks NO candidate; iter-v3/025 explores a different axis.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count outside [129, 215]. If trades < 129 (>-25% reduction): the new feature is heavily restricting trade entries. If trades > 215 (>+25% expansion): the new feature is loosening trade entries OR the axis didn't propagate. Verdict path: BLOCK if axis didn't propagate (verified via Falsifier 4); otherwise PATH-classification per §2.6.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe with 14-feature set → unexpected slowdown in feature-loading or parquet regen pipeline. Engineer documents the cause.

**Falsifier 4 (PRIMARY for INERT discrimination)**: `btc_funding_rate_zscore_30` rank 14/14 across all 3 per-symbol models (or rank ≤7 fails for ≥ 1 symbol) → the cross-asset signal does NOT surface in the model; the iteration confirms PATH B (PROMISING-INERT). Per `feedback_v3_inert_features_at_higher_budget.md`, this triggers permanent close of the funding-derived feature family in v3. Verdict: **PATH B (PROMISING-INERT)** — ALL funding-derived axes closed.

**Falsifier 5 (PATH A indicator)**: rank ≤7 for ≥ 1 symbol AND IS Sharpe Δ ≥ +0.10 → genuine cross-asset signal at higher budget; **PATH A (PROMISING)**. Catalog row marks YES candidate (compoundable as a feature ingredient at iter-v3/029+ CONFIRMATION bundling).

**Process falsifier**: pre-flight `grep btc_funding_rate_zscore_30 src/crypto_trade/features_v3/__init__.py` exits non-zero (after sub-fix #1), OR `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'btc_funding_rate_zscore_30' in df.columns"` exits non-zero (after sub-fix #5), OR `data/funding_rates/BTCUSDT.csv` not present → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| **PATH A (`EXPLORATION-PROMISING`)** | IS Sharpe Δ ≥ +0.10 vs iter-v3/018 multi-seed anchor (i.e., ≥ +0.4788) AND broad-based per-symbol AND IS trades in [129, 215] (Falsifier 2 PASS) AND `btc_funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol (Falsifier 5 PASS) | "Cross-asset BTC funding stress signal surfaces at higher budget — first NEW external-data-source feature ingredient validated at higher budget" | iter-v3/025 EXPLORATION on a DIFFERENT axis category (DSR gate reformulation, Open Interest delta, basis spread, on-chain proxies) |
| **PATH B (`EXPLORATION-PROMISING-INERT`)** | IS Sharpe within ±0.10 of iter-v3/018 multi-seed anchor (i.e., in [+0.28, +0.48]) AND IS trades in [129, 215] AND rank still 14/14 across all 3 OR rank ≤7 fails for ≥ 1 symbol | "Cross-asset BTC funding INERT — ALL funding-derived axes closed (funding family permanently dead in v3)" | iter-v3/025 EXPLORATION on a DIFFERENT NEW feature family (NOT funding) — Open Interest delta, basis spread, on-chain proxies |
| **PATH C (`EXPLORATION-NEGATIVE`)** | IS Sharpe Δ < -0.10 vs iter-v3/018 multi-seed anchor i.e. < +0.2788 AND non-bit-identical roster AND `btc_funding_rate_zscore_30` IS in feature importance (Falsifier 5 partial PASS) → the model used the new feature but it actively hurt | "Cross-asset BTC funding actively hurts at n_trials=35 — funding family confirmed structurally orthogonal to v3 architecture" | iter-v3/025 EXPLORATION on a DIFFERENT axis category — NOT another funding variant |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | IS Sharpe direction wrong AND `btc_funding_rate_zscore_30` importance == 0 across all 3 models (Falsifier 4 fires) AND trade roster bit-identical to iter-v3/023 (UNLIKELY for cross-asset feature given non-trivial rank-IC) | "Model ignored the new feature; trade roster unchanged" | iter-v3/025 EXPLORATION on a DIFFERENT axis category |
| `EXPLORATION-PROMISING-MECHANICAL` (UNLIKELY for new-feature axis given non-trivial rank-IC; flagged for completeness) | IS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/023 — UNLIKELY | "New feature added without behavioral change — accounting drift" | similar to iter-v3/013 framing |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades outside [129, 215]) AND axis didn't propagate (Falsifier 4 fires), OR Falsifier 3 (wall-clock) triggered | (none) | Diary documents, iter-v3/025 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 inherited + 4 methodology-specific = 8 total)

iter-v3/024 inherits the cadence-discipline safeguards from skill SHA + the saturation-predictor rule + the structural-axis preference rule + `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_inert_features_at_higher_budget.md` LOCKED:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. Wall-clock target < 30 min.
2. **Single-axis variation rule** honored: 1 column swapped (per-symbol funding → cross-asset BTC funding); regime gate stays disabled; per-symbol cap stays disabled. ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/ADX/CPCV byte-for-byte identical to iter-v3/018.
3. **EXPLORATION never updates BASELINE_V3.md**.
4. **Saturation predictor falsifier** (Section 3.6 + Section 4.3 Falsifier 2, threshold derived from anchor `iter-v3/018 IS trades = 172` ±25% = [129, 215]).

Methodology-specific safeguards (NEW-feature-family CROSS-ASSET variant axis):

5. **Feature-importance verifier** (Section 3.6 + Section 4.3 Falsifier 4 + Falsifier 5; PRIMARY disambiguation metric): `btc_funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol distinguishes "model surfaces the cross-asset signal at higher budget (PATH A)" from "model ignores the cross-asset signal at higher budget (PATH B INERT — funding family permanently dead in v3)".
6. **EDA gate from iter-v3/024 SHA `afdb8bc`** (Section 2.1): coverage 100%; IC redundancy 0.1921 < 0.50 brief target; ADF p≈0; rank-IC max 0.0474. All 5 IS-only EDA gates pass.
7. **Past-only computation discipline**: `compute_btc_funding_rate_zscore` uses `.shift(1)` on rolling stats (mirrors `compute_funding_rate_zscore` from iter-v3/019). BTC funding rate AT bar t is the rate that just SETTLED at the candle open, knowable from the previous 8h period close.
8. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-023)

1. **Adversarial unit tests** must PASS before backtest: `tests/strategies/ml/` 26 tests (regime gate tests at iter-v3/022 must STILL pass even though gate disabled).
2. **File-artifact reconciliation table** (§3.6). 13 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-checks**: `btc_funding_rate_zscore_30` in V3_FEATURE_COLUMNS, parquet has `btc_funding_rate_zscore_30` column, BTC funding rate cache present at `data/funding_rates/BTCUSDT.csv`, `funding_rate_zscore_30` REMOVED from V3_FEATURE_COLUMNS.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 CROSS-ASSET-axis-specific risks (3 explicit)

1. **Cross-asset BTC funding STILL INERT at n_trials=35 (PATH B)**: rank 14/14 across all 3 symbols would close the funding-derived feature family permanently for v3 (3 EXPLORATION data points: iter-v3/019 + iter-v3/023 + iter-v3/024). **Mitigation**: PATH-A vs PATH-B vs PATH-C is THE point of the iteration — all three outcomes are pre-committed in §2.6 + §4.4.
2. **Cross-asset BTC funding ACTIVELY HURTS (PATH C)**: the cross-asset broadcast feature introduces noise that the model overfits on at higher budget. Per `feedback_v3_inert_features_at_higher_budget.md`, this confirms the funding-family scope is structurally orthogonal to v3 architecture. **Mitigation**: PATH C captured in §2.6 + §4.4; clean classification + permanent close of funding-derived family.
3. **Cross-asset BTC funding has 0.18 IC with `btc_ret_14d`**: partial overlap with the existing macro feature. The cross-asset variant may not carry sufficient INDEPENDENT signal beyond what `btc_ret_14d` already provides. **Mitigation**: rank-IC magnitude 0.0474 (LDO 3-bar) is comparable to per-symbol funding's 0.0485 — the cross-asset variant has comparable predictive content; the question is whether it surfaces at higher budget.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED (single-feature-axis swap)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, 14-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX ≥ 20 | ≈ 60% of bars pass | Trend filter |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over **14** features now — cross-asset BTC funding column added; per-symbol funding removed; net: 14 columns) | ≈ 26–37% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited iter-v3/012) | Macro flips |

Combined kill rate target: **80–90%**. The only primitive whose computation changes is primitive 4 (z-score OOD computed over the swapped 14-column feature set); all others' specs are byte-identical to iter-v3/018.

**Important sub-point**: the new `btc_funding_rate_zscore_30` becomes one of the 14 columns the z-score OOD primitive computes the per-bar kill on. In stress regimes where BTC funding rate spikes (|z| > 2.0), the OOD gate will kill the bar's signal across all 3 per-symbol models simultaneously — this is intentional defensive behavior consistent with cross-asset stress filtering. The cross-asset feature's heavy-tailed distribution (clipped to [-10, 10]) means OOD kills will fire more aggressively in BTC funding-stress regimes (e.g., BTC liquidation cascades). This is RISK-AWARE behavior, not an over-restriction.

**Regime gate (primitive 9)**: DISABLED at iter-v3/024 (`enable_regime_gate=False`). Code stays in repo. Not in active gate stack.

**Per-symbol cap (primitive 8)**: DISABLED. Code stays in repo.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent. The cross-asset BTC funding feature provides MARKET-WIDE stress information; the 7 primitives operate on per-symbol context. No cross-primitive contamination.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/018. Regime coverage includes 2023 banking crisis, 2024 halving + Trump rally, 2024-08 yen-carry crash, 2025 January correction. The cross-asset BTC funding feature provides additional regime-classification dimension (high-system-stress vs low-system-stress vs negative-system-stress regimes) WITHIN each of these macro periods.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/018 multi-seed showed TRX 66.08% / 55.83% concentration. iter-v3/024 OOS concentration may shift either direction depending on whether cross-asset BTC funding reshapes per-symbol trade frequencies. Per `feedback_v3_iter019_axis_priorities.md` + `feedback_v3_concentration_is_signal.md`, concentration architecture is a separate axis category; this iteration does NOT pre-register a concentration falsifier.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 13 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/019 + iter-v3/023 INERT precedents)

**Prediction P1 (process, P=10%)**: `btc_funding_rate_zscore_30` column not added to V3_FEATURE_COLUMNS or not propagated to the LightGBM strategy's `feature_columns` argument. **Detection signal**: Falsifier 4 (feature-importance check) shows feature with importance 0 across all 3 models OR Falsifier 2 (saturation predictor) fires (IS trades outside [129, 215]). **Mitigation**: §3.6 rows 1, 5, 14 verifiers (3 independent signals).

**Prediction P2 (process, P=10%)**: parquet regeneration fails or produces stale parquets (btc_funding_rate_zscore_30 missing or NaN OR funding_rate_zscore_30 still present). **Detection signal**: §3.6 row 5 verifier fails. **Mitigation**: pre-flight verifier blocks Phase 6 launch.

**Prediction P3 (process, P=5%)**: wall-clock overshoots the 30-min target. 3-symbol universe with 14-feature set should run in 8-15 min. **Detection signal**: engineering report wall-clock minutes. **Mitigation**: 2h hard cap by skill spec.

**Prediction P4 (model, P=30%)** = **PATH A (PROMISING)**: rank ≤7 for ≥ 1 symbol AND IS Sharpe Δ ≥ +0.10. The cross-asset BTC funding signal gives the model a market-wide leveraged-positioning regime-classifier signal that complements the existing 13-feature set; at n_trials=35 budget, Optuna explores enough of the 14-column loss surface to surface the feature via tree splits. The 8-of-9 NEGATIVE-direction rank-IC cells signal a coherent mean-reversion edge across the 3 symbols at the cross-asset SCOPE level.

**Prediction P5 (model, P=45%)** = **PATH B (PROMISING-INERT)**: IS Sharpe stays in iter-v3/018 multi-seed anchor range [+0.28, +0.48]; the cross-asset BTC funding signal is included in the model but its information overlap with `btc_ret_14d` (0.18 IC) is enough that the model's tree splits substitute btc_funding for btc_ret_14d in some contexts without net Sharpe lift. Even at higher budget, the feature does not surface to top-7 importance because the 13-feature stack has been calibrated through iter-v3/007-018 evolution and exploits the same macro-stress information channel via `btc_ret_14d`.

**Prediction P6 (model, P=20%)** = **PATH C (NEGATIVE)**: IS Sharpe drops below iter-v3/018 multi-seed anchor (-0.10 → < +0.28); the cross-asset BTC funding feature introduces noise that the model overfits on at higher budget. Mechanism: `feedback_v3_inert_features_at_higher_budget.md` predicts that adding INERT features at higher budgets actively harms OOS — if cross-asset BTC funding is INERT in the per-symbol-LightGBM-on-13-features architecture (similar to per-symbol funding), n_trials=35 will produce overfit-negative.

P4 + P5 + P6 sum to 95%. Process predictions P1-P3 sum to 25%.

**Calibration vs prior EXPLORATIONs**:
- 4 NEW-feature-family axis-category data points exist in v3 (post iter-v3/024): iter-v3/015 (microstructure tbr_zscore_30 INERT @ n_trials=10), iter-v3/019 (per-symbol funding INERT @ n_trials=10), iter-v3/023 (per-symbol funding INERT @ n_trials=35), iter-v3/024 (cross-asset BTC funding @ n_trials=35).
- The PATH-B prediction (P=45%) reflects a Bayesian update against the prior INERT pattern: 3-of-3 prior NEW-feature-family axes were INERT, suggesting a strong structural-INERT prior for funding-derived features in the per-symbol-LightGBM-on-13-features architecture. The cross-asset variant is the disambiguation experiment on SCOPE.
- The PATH-A prediction (P=30%) reflects the structural distinctness of cross-asset vs per-symbol mechanism — the broadcast nature of the feature could surface a system-stress signal that per-symbol couldn't.
- The PATH-C prediction (P=20%) reflects the iter-v3/023 INERT-OVERFIT precedent: if cross-asset BTC funding is INERT at the architecture level, n_trials=35's larger search may overfit on the noise dimension.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 12 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md. The 12 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers.

1. **IS Sharpe ≥ iter-v3/018 multi-seed anchor + 0.10 (i.e., ≥ +0.4788)**: catalog row records PATH A verdict on numerical-axis basis.
2. **IS Sharpe < iter-v3/018 multi-seed anchor - 0.10 (i.e., < +0.2788)**: PATH C verdict (active drag).
3. **IS Sharpe in [+0.2788, +0.4788]**: PATH B (INERT) verdict — neither active drag nor active surfacing.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level.md` (informational at EXPLORATION; predicted IS in [129, 215]; OOS predicted ~75-130 — ≥50).
5. **PBO < 0.40 (per-cell mean) AND `n_high_pbo_cells_99 ≤ 4`**: methodology hygiene; both inherited unchanged from iter-v3/018 multi-seed.
6. **IC max abs < 0.70**: per Critic Check 4 — the new feature `btc_funding_rate_zscore_30` has max |IC| 0.1921 vs the existing 13 (verified at iter-v3/024 EDA SHA `afdb8bc`); after-add expected max |IC| in the 14-feature pairwise matrix remains 0.685 (existing 13-feature pairwise max).
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS**: the 13 inherited features unchanged; the new `btc_funding_rate_zscore_30` is a z-score (rolling-window mean-zero by construction) — ADF p-value structurally near-zero (verified 0.0 in EDA).
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis SHA `afdb8bc`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION.
10. **Symbol exclusion + feature isolation**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `features_v3` does not import `features` (v1) or `features_v2` (v2). The cross-asset BTC funding feature lives in `features_v3/funding_v3.py` (track-isolated).
11. **Behavioral-effect verifier (saturation falsifier)**: IS trades in **[129, 215]** (= anchor iter-v3/018 IS trades 172 ± 25%).
12. **PRIMARY DISAMBIGUATION VERIFIER (Falsifier 5 / PATH-A predictor)**: `btc_funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol AND non-zero importance for ≥ 1 of 3 models. Critic uses BOTH signals to disambiguate PATH A from PATH B from PATH C: PATH A = rank ≤7 ≥ 1 sym AND IS Δ ≥ +0.10; PATH B = rank still 14/14 OR rank ≤7 fails for ≥ 1 sym; PATH C = IS Δ < -0.10. Predicted disambiguation: PATH A 30%, PATH B 45%, PATH C 20% per §7.

**Catalog-axis verdicts** map to §4.4 PATH-classification table.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-023** — no version bumps in iter-v3/024:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0
scikit-learn = 1.8.0 (pinned >=1.8,<1.9 per iter-v3/020 sklearn pin)
pyarrow = 23.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.6 (adfuller for ADF stationarity)
optuna = 4.8.0
scipy = 1.17.0
httpx = (already used for kline fetcher; reused for funding-rate fetcher)
```

**No package additions or version bumps.** The cross-asset BTC funding implementation extends the existing `funding_v3.py` module preserved from iter-v3/019 zero-revert-cost decision.

---

## Section 10 — Adversarial Tests

Adversarial test suite at `tests/strategies/ml/` is unchanged. The Engineer should:
- Verify `tests/features_v3/test_funding_v3.py::test_funding_rate_zscore_past_only` passes
- Add a new adversarial test for `compute_btc_funding_rate_zscore` (or extend existing) verifying:
  - Past-only invariant (bar t z-score uses ONLY rates t-30...t-1)
  - Broadcast invariant (BTC z-score column values identical across BCH/LDO/TRX kline frames at the same open_time)
  - NaN handling at series start (rolling-window initialization)

Total expected test count: 26 + however many funding tests.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

```
| iter-v3/024 | 2026-05-08 | NEW external-data-source feature CROSS-ASSET variant: btc_funding_rate_zscore_30 (replaces per-symbol funding_rate_zscore_30; broadcast to all 3 models) | IS Sharpe Δ TBD vs iter-v3/018 multi-seed +0.3788 | OOS Sharpe TBD (informational) | TBD verdict (PATH A / PATH B / PATH C) | TBD candidate? |
```

**Pre-committed disposition** (cannot be renegotiated post-hoc per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_inert_features_at_higher_budget.md` LOCKED):
- If verdict = **PATH A (`EXPLORATION-PROMISING`)**: catalog row marked YES candidate (compoundable as a feature ingredient at iter-v3/029+ CONFIRMATION bundling consideration; first NEW-external-data-source ingredient validated).
- If verdict = **PATH B (`EXPLORATION-PROMISING-INERT`)**: catalog row marked NO candidate (funding family permanently dead in v3 — 3 EXPLORATION data points all INERT).
- If verdict = **PATH C (`EXPLORATION-NEGATIVE`)**: catalog row marked NO; iter-v3/025 explores a DIFFERENT axis category. NEXT iteration MUST NOT be another funding variant.
- If verdict = `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT; UNLIKELY): catalog row marked NO; iter-v3/025 explores a DIFFERENT axis category.

**Catalog count after iter-v3/024**: 6 of 10 EXPLORATIONs in the post-bootstrap cycle; **4 more required** before any CONFIRMATION can launch (earliest = iter-v3/029).

**Forward axis pipeline** (iter-v3/025-028 candidates pre-pre-committed for QR continuity, NOT mandates):
- iter-v3/025 candidates: depend on iter-v3/024 PATH-A/B/C outcome:
  - PATH A: iter-v3/025 = different axis category (DSR gate reformulation OR a new structural axis)
  - PATH B/C: iter-v3/025 = NEW feature family NOT funding (Open Interest delta, basis spread, on-chain proxies — each requires its own external data source)
- iter-v3/026-028 candidates: depend on accumulated evidence

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (6 of 10 in post-bootstrap cycle); STRUCTURAL axis declared (NEW external-data-source feature family CROSS-ASSET variant); references Critic FINAL `c4574af` of iter-v3/023 + `feedback_v3_inert_features_at_higher_budget.md`.
- [x] §1 Hypothesis with locked numerical bands + mechanism + INERT-precedent caveat.
- [x] §2 IS-only numerical evidence at SHA `afdb8bc`; 5 of 5 EDA gates PASS; behavioral-effect predictor with saturation falsifier band [129, 215]; PATH-A/B/C pre-classification table.
- [x] §3 6-sub-fix decomposition + 13-row Brief-vs-Code reconciliation table + iter-v3/023 inheritance verifiers.
- [x] §4 EXPLORATION outcome interpretation table mapped to PATH-A/B/C; falsifiers locked before backtest.
- [x] §5 Risk Mitigation: 4 cadence-discipline + 4 methodology-specific = 8 total safeguards; 3 cross-asset-axis-specific risks.
- [x] §6 Risk Management Design: 7-primitive table UNCHANGED; regime gate disabled; per-symbol cap kept disabled.
- [x] §7 Pre-Registered Failure-Mode Prediction: 6 predictions calibrated against iter-v3/015 + iter-v3/019 + iter-v3/023 INERT precedents.
- [x] §8 12 EXPLORATION criteria with PATH-classification + PRIMARY DISAMBIGUATION VERIFIER.
- [x] §9 Library Stack Declaration UNCHANGED.
- [x] §10 Adversarial Tests preserved + new BTC funding broadcast test specified.
- [x] §11 Catalog Row Pre-Commit + Forward axis pipeline.
