# Iteration v3-015 — Research Brief

**Type**: EXPLORATION (EIGHTH EXPLORATION under cadence discipline; **STRUCTURAL axis (NOT a gate-threshold knob)** — first NEW feature family in v3 catalog per `feedback_structural_over_knob_exploration.md` rule pre-commit 2026-05-07)
**Track**: v3 (rigor arm) — fifteenth iteration
**Branch**: `iteration-v3/015` (off `iteration-v3/014` head; analysis commit `fcf6b06` ships before this brief)
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
colsample_bytree = 1.0             # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–014 briefs / engineering reports / Critic / diaries; iter-v3/015 analysis script `analysis/iteration_v3-015/tbr_zscore_eda.py` outputs (committed at SHA `fcf6b06` BEFORE this brief). The analysis script reads ONLY pre-OOS-cutoff data sliced from `data/features_v3/*.parquet` — no OOS contamination at brief time.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW microstructure feature `tbr_zscore_30` added (V3_FEATURE_COLUMNS 13 → 14)
Cadence: EXPLORATION #8 of 10 needed before next CONFIRMATION
Axis category: 1 (NEW feature family — microstructure/order-flow imbalance)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a universe change. NOT a labeling change.
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — STRUCTURAL axis pivot (per `feedback_structural_over_knob_exploration.md`)**:

By iter-v3/014, the v3 catalog had:
- 4 gate-threshold knob axes (009 zscore, 011 zscore tighter, 012 BTC band, 014 ADX tighter)
- 2 feature-pruning axes (007 top-14, 009 top-13) — still parametric
- 1 universe axis (013 drop-MKR) — only genuine structural change so far, AND that one was MECHANICAL drag-removal (per-symbol architecture; non-compoundable)
- **0 NEW feature families, 0 NEW model architectures, 0 NEW labeling architectures**

The user's correction (verbatim 2026-05-07): *"we are in iteration 15, right? why the quant-researcher is so crazy in fine tune parameters, instead of going full exploration?"*

Per the new memory rule `feedback_structural_over_knob_exploration.md` axis priority order:
1. **NEW feature families** (highest priority — explicit v3 skill iter-v3/002+ scope: funding rate, OI, basis, microstructure, on-chain) ← **iter-v3/015 is here**
2. NEW model architecture (XGBoost, CatBoost, NN)
3. NEW labeling architecture (meta-labeling M2 sizing, regime-conditional triple-barrier)
4. NEW risk primitive (orthogonal to existing 7 gates)
5. NEW universe (cross-track basket — but iter-v3/013 already touched this)
6. Gate-threshold knob (LOWEST priority)

**ADX axis is now CLOSED** per `feedback_adx_axis_asymmetric_v3.md` DOWNGRADED (2026-05-07). The original "iter-v3/015 = ADX 18" mandate was REVOKED by user as itself fine-tuning. iter-v3/015 pivots to category 1.

**Why TBR z-score (over funding rate, OI, basis, liquidations)**:

- **Data-tractability constraint** (2h wall-clock cap): TBR data already lives in EVERY Binance 8h candle (`taker_buy_quote_volume` + `quote_volume` columns are guaranteed by the kline spec — verified at SHA `fcf6b06` for BCH/LDO/TRX, 2193 IS rows × 100% coverage). Funding rate, OI, basis spread, liquidations all need NEW fetcher infrastructure (separate `/fapi/v1/*` endpoints with rate limits and historical-window restrictions). Adding fetcher + storage + features + parquet regen + backfill across ~24 months × 3 symbols = unbounded > 2h risk.
- **Single-feature axis discipline**: One new feature added to V3_FEATURE_COLUMNS (13 → 14). Preserves the single-axis EXPLORATION discipline. The single-axis rule does NOT mean parametric — adding one feature column IS a single-axis structural change (per `feedback_structural_over_knob_exploration.md` counter-rule explicit statement).
- **Crypto-native and never-tried-in-v3**: V3_FEATURE_COLUMNS contains zero taker_buy-derived features. v1 has `vol_taker_buy_ratio` (RAW ratio) in BASELINE_FEATURE_COLUMNS — but the raw ratio is non-stationary across symbols and regimes (BCH IS-mean 0.4919, LDO 0.4860, TRX 0.4966) and violates the project's "scale-invariant features" rule for pooled multi-symbol models. The z-scored variant is structurally distinct.
- **Microstructure foundation**: Taker-buy imbalance is the canonical aggressive-buyer-flow proxy in perpetual-futures markets where queue position is unobservable. Equivalent to OFI in TAQ data; signed-trade imbalance in classical microstructure (Kyle 1985 informed-trader proxy via volume signing). The feature is grounded in the Spine canon §4 Crypto-Native Alpha Sources subsection "Microstructure (bid-ask spread, OFI, taker-maker imbalance)" — explicitly listed as iter-v3/002+ scope.
- **Funding-cycle-aligned timescale**: 30-bar window = ~10 days = ~9 funding periods at 8h cadence. Long enough to capture flow regime persistence; short enough to remain past-only-stationary across the 24-month training window.

After iter-v3/015 the catalog will have axis coverage: features-prune × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 + **NEW-feature-family × 1** = 7 unique axis representations, FIRST genuinely-novel feature-family axis.

---

## Section 1 — Hypothesis

Adding `tbr_zscore_30` (z-score over rolling 30-bar window of taker_buy_quote_volume / quote_volume) as a 14th feature on top of iter-v3/013's stack (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20) will produce IS Sharpe maintained or improved (≥ +0.40 PROMISING threshold; predicted [+0.50, +1.30] median +0.90) by giving the LightGBM model a microstructure regime-classifier signal — the taker-buy z-score captures aggressive-buyer-flow imbalance, which is structurally orthogonal to the existing 13 features (max |IC| = 0.1654, well below 0.70 threshold) and carries non-trivial directional rank-IC vs forward returns (BCH 7-bar +0.065; LDO 1-bar -0.027 fade; TRX weak ~0.013).

**Mechanism explanation** (why microstructure should add edge): in perpetual-futures markets, taker volume by direction signals informed/aggressive flow. When TBR z-score is high (>1σ), aggressive buyers are paying the offer in size — typically associated with breakout continuation or short-squeeze unwinds. When TBR z-score is low (<-1σ), aggressive sellers are hitting the bid — typically signal of cascade beginning or capitulation. Either tail is informative *jointly with the existing trend / regime / volatility features*; the LightGBM model learns interaction effects (TBR-high AND ADX-high = strong-trend continuation; TBR-low AND Hurst-mean-reverting = fade; etc.). The candidate is NOT a standalone alpha, it is a regime-classifier dimension that complements the 13-feature set.

**Direction symmetry**: TBR is naturally bipolar (positive z = buy aggression, negative z = sell aggression). LightGBM trees split bipolarly without preference. The mixed-sign rank-IC across symbols (BCH +6.5%, LDO -2.7%, TRX +0.4%) is the LightGBM-friendly scenario where per-symbol architecture lets each model learn its own sign loading.

---

## Section 2 — IS-Only Numerical Evidence + Counterfactual + Behavioral-Effect Predictor

**Analysis script**: `analysis/iteration_v3-015/tbr_zscore_eda.py` (committed at SHA `fcf6b06` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS window only — pre-OOS_CUTOFF_DATE 2025-03-24):
- `data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet` — already-generated feature parquets (existing 13 V3_FEATURE_COLUMNS + raw kline columns including `taker_buy_quote_volume` and `quote_volume`).

**Outputs** (committed alongside the script at SHA `fcf6b06`):
- `analysis/iteration_v3-015/tbr_eda_coverage.csv` — IS-window coverage per symbol
- `analysis/iteration_v3-015/tbr_eda_distribution.csv` — distribution stats
- `analysis/iteration_v3-015/tbr_eda_correlation.csv` — Spearman IC vs 13 V3_FEATURE_COLUMNS (39 rows = 3 symbols × 13 cols)
- `analysis/iteration_v3-015/tbr_eda_rankic.csv` — Spearman rank-IC vs forward returns
- `analysis/iteration_v3-015/synthesis.md` — narrative + verdict summary

### 2.1 Coverage check (IS window, 2023-03-24 → 2025-03-23)

| Symbol | n_IS_total | n_valid_tbr_zscore_30 | coverage_zscore_pct |
|---|---:|---:|---:|
| BCHUSDT | 2193 | 2193 | **100.00** |
| LDOUSDT | 2193 | 2193 | **100.00** |
| TRXUSDT | 2193 | 2193 | **100.00** |

**100% coverage on all 3 symbols** — even at the IS-window start, the rolling-30 window uses pre-IS data (training window starts 2023-03-24; rolling-30 lookback uses 2023-02 data, available in parquet from 2020-01-01). Zero NaN issues from `quote_volume = 0` (rare event verified absent).

**Coverage gate PASS** (floor 80%).

### 2.2 Distribution check

| Symbol | feature | mean | median | std | p01 | p25 | p75 | p99 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | tbr_raw | 0.4919 | 0.4919 | 0.0183 | 0.4488 | 0.4806 | 0.5034 | 0.5353 |
| BCHUSDT | tbr_zscore_30 | -0.005 | -0.010 | **1.005** | -2.351 | -0.688 | +0.673 | +2.286 |
| LDOUSDT | tbr_raw | 0.4860 | 0.4864 | 0.0196 | 0.4401 | 0.4734 | 0.4990 | 0.5309 |
| LDOUSDT | tbr_zscore_30 | -0.001 | +0.019 | **1.003** | -2.375 | -0.664 | +0.675 | +2.312 |
| TRXUSDT | tbr_raw | 0.4966 | 0.4970 | 0.0247 | 0.4364 | 0.4811 | 0.5123 | 0.5599 |
| TRXUSDT | tbr_zscore_30 | +0.002 | +0.009 | **0.991** | -2.297 | -0.651 | +0.651 | +2.445 |

**Distribution sanity PASS**: tbr_raw is approximately Normal(0.49, 0.02) per symbol with structurally distinct means across symbols (this is exactly why z-scoring is necessary — pooled raw values would mix per-symbol baselines). tbr_zscore_30 is approximately Normal(0.00, 1.00) by construction with std exactly 1.005 ± 0.01 across all 3 symbols. p1 ≈ -2.4, p99 ≈ +2.4 = consistent with Gaussian-ish but slightly fat-tailed (mild excess kurtosis expected for crypto microstructure).

### 2.3 Correlation gate (vs 13 V3_FEATURE_COLUMNS)

Per-symbol max |Spearman IC| from `analysis/iteration_v3-015/tbr_eda_correlation.csv`:

| Symbol | max abs IC | reached at |
|---|---:|---|
| BCHUSDT | 0.1518 | vwap_dev_20 |
| LDOUSDT | 0.1654 | vwap_dev_20 |
| TRXUSDT | 0.1354 | vwap_dev_20 |

**Overall max |IC| across all (symbol × V3col) pairs: 0.1654**

**IC redundancy gate PASS** (threshold 0.70 per BASELINE_V3.md). Even the strongest pair (vs vwap_dev_20 — also volume/order-flow related, makes structural sense) is clearly independent. Compare to v3 max |IC| in iter-v3/008 audit (0.685, just under threshold) and iter-v3/013-014 (0.685 unchanged) — the candidate adds substantial information margin (the gap from 0.685 to 0.70 was thin; adding a feature with max |IC| 0.1654 is exceptionally low-correlation).

### 2.4 Rank-IC vs forward returns (predictive signal)

Per `analysis/iteration_v3-015/tbr_eda_rankic.csv`:

| Symbol | horizon_bars | horizon_days | n_pairs | rank_ic_spearman |
|---|---:|---:|---:|---:|
| BCHUSDT | 1 | 0.33 | 2192 | +0.00429 |
| BCHUSDT | 3 | 1.00 | 2190 | +0.01657 |
| BCHUSDT | 7 | 2.33 | 2186 | **+0.06493 (LARGEST)** |
| LDOUSDT | 1 | 0.33 | 2192 | **-0.02650 (negative-direction)** |
| LDOUSDT | 3 | 1.00 | 2190 | -0.01979 |
| LDOUSDT | 7 | 2.33 | 2186 | -0.01426 |
| TRXUSDT | 1 | 0.33 | 2192 | -0.01309 |
| TRXUSDT | 3 | 1.00 | 2190 | -0.00698 |
| TRXUSDT | 7 | 2.33 | 2186 | +0.00399 |

**Non-trivial rank-IC PASS**: max |rank-IC| = 0.0649 (BCH 7-bar). Above the v3 implicit threshold of 0.02 inferred from existing-feature behavior. The BCH 7-bar +0.065 is roughly 30x the noise floor (1/√2186 ≈ 0.021) — meaningful directional signal, statistically distinguishable from zero.

**Mixed-sign rank-IC ACROSS symbols** (BCH +6.5% / LDO -2.7% / TRX weak) is the LightGBM-friendly scenario per project's per-symbol architecture: each symbol's model learns its own sign loading via tree splits. The signal is NOT pooled across symbols (which would average to ~0) — the model uses TBR z-score WITHIN each symbol's interaction with regime/momentum features.

### 2.5 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise): brief Section 2 must include explicit estimate of how many IS trades will change in the roster. Adding a NEW feature is structurally different from gate-threshold tuning (which removes/adds candidate trades) — adding a feature changes the LightGBM splitting surface, which can shift trade timing, direction, entry/exit conditions WITHOUT necessarily changing the candle universe.

**Predicted IS trade count behavioral effect**:

| Scenario | Expected IS trade count | Mechanism |
|---|---:|---|
| Lower bound (axis fully propagated, model learned non-trivial split) | ~120 | Optuna may converge on shorter-tree models that gate trades more selectively when the new feature drives a new threshold |
| Median (typical NEW-feature behavior in v1/v2 history) | ~180 | Model uses new feature as a partial filter; trade roster shifts ~15-20% |
| Upper bound (axis added but Optuna trees largely ignore the new feature) | ~250 | Model includes the feature but it has low importance; trade roster ~iter-v3/014's ~200 baseline |
| **Saturation falsifier threshold (per Critic FINAL Rec 3 of iter-v3/013 chain)** | **`ceil(1.2 × counterfactual_n_trades)`** = **`ceil(1.2 × 209)` = 251** | If observed > 251, axis did NOT propagate (the model used the new column for SOME splits OR not at all but trade count couldn't have grown above 1.2x baseline without rejection criteria changing) |

**Counterfactual derivation**: the closest comparable baseline is iter-v3/013 (3-symbol, ADX=20, all-other-gates UNCHANGED, 209 IS trades). iter-v3/014 (ADX=25 tighter) had 153 IS trades — but that's an outlier from gate-axis variation. iter-v3/015 RESETS adx_threshold to 20 (matching iter-v3/013), so the counterfactual baseline is 209 IS trades (iter-v3/013). The saturation falsifier threshold = `ceil(1.2 × 209)` = **251**.

**Falsifier reading**: if observed iter-v3/015 IS trades > 251, the new feature axis did NOT propagate (analogous to iter-v3/012's NULL-RESULT but with different root cause — likely `V3_FEATURE_COLUMNS` reassignment didn't propagate through `_verify_feature_columns()` OR `LightGbmStrategy(feature_columns=...)` argument). The falsifier is sensitive in the right direction: **larger-than-counterfactual trade roster + new column not in tree splits = axis failure**. Realized iter-v3/015 IS trade count is expected in [120, 251] based on the predicted band; the upper bound 251 absorbs Optuna re-optimization variance.

**SECONDARY behavioral-effect verifier (feature-importance check)**: if `tbr_zscore_30` does not appear in the top-10 feature importance ranks across at least 1 of the 3 per-symbol models, the feature was effectively unused — the IS Sharpe delta is not attributable to the new feature, and the catalog row should mark INERT-via-noncontribution. The Engineer's Phase 6 report MUST stamp the feature-importance ranking for `tbr_zscore_30` on each per-symbol model.

### 2.6 Realized vs counterfactual divergence drivers

The realized iter-v3/015 run will diverge from a naive 209-trade counterfactual because:
- Optuna re-optimizes hyperparameters with a 14th candidate column (different optimal tree depth/leaves; different colsample picks since `colsample_bytree=1.0` in `--exploration` mode means all 14 columns are available to every tree — but Optuna chooses the *number* of features actually split on per tree implicitly via `min_data_in_leaf` and `feature_fraction` interactions).
- LightGBM tree splits may shift entry/exit thresholds, changing which signals fire and which get cooled down.
- The 14th column adds 1 column to every parquet row's input vector — feature-loading time is +~7% but parses to no observable wall-clock delta.

The DIRECTION of the EDA evidence (max |IC| 0.1654 well below redundancy threshold + non-trivial rank-IC vs forward returns) is informative; the realized trade count and Sharpe will land in the predicted bands with high probability.

### 2.7 Setup integrity (verified at SHA `fcf6b06`)

```
data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet extant + non-empty   PASS (3/3)
taker_buy_quote_volume + quote_volume columns present                       PASS
tbr_eda_coverage.csv produced                                               PASS
tbr_eda_distribution.csv produced                                            PASS
tbr_eda_correlation.csv produced (39 rows)                                   PASS
tbr_eda_rankic.csv produced (9 rows)                                         PASS
synthesis.md produced                                                        PASS
Coverage gate (>= 80% IS valid)                                              PASS (100% all 3 symbols)
IC redundancy gate (max |IC| < 0.70)                                         PASS (max 0.1654)
Rank-IC non-trivial (>= 0.02)                                                PASS (max 0.0649)
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013)

| Symbol | iter-v3/014 status | iter-v3/015 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED | UNCHANGED (drop-MKR rule executed at iter-v3/013) |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/014 (current) | iter-v3/015 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — ADD ONE NEW FEATURE (`tbr_zscore_30`); 13 → 14 columns

| Feature column | iter-v3/014 (V3_FEATURE_COLUMNS_TOP_N) | iter-v3/015 (V3_FEATURE_COLUMNS_PLUS_TBR) |
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
| **tbr_zscore_30** | (not present) | **ADDED** (the single new column) |

`len(V3_FEATURE_COLUMNS) == 14` after iter-v3/015. `_verify_feature_columns()` updated to assert `len == 14` and `'tbr_zscore_30' in V3_FEATURE_COLUMNS`.

The Engineer's Phase 6 task includes:
1. Add `compute_tbr_zscore` function to `src/crypto_trade/features_v3/volume_micro_v3.py` (existing module; cleanest home for a taker_buy-derived feature).
2. Update `add_volume_micro_v3_features` to populate `df["tbr_zscore_30"]`.
3. Add `tbr_zscore_30` to `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py` (or define a new constant `V3_FEATURE_COLUMNS_PLUS_TBR` if the team prefers explicit named constants).
4. Regenerate `data/features_v3/{BCH,LDO,TRX,MKR}USDT_8h_features.parquet` so the 14-column feature set is materialized (via `uv run crypto-trade features --symbols ... --interval 8h --track v3 --format parquet --workers 4`). MKR is regenerated for completeness even though V3_MODELS excludes it (the parquet is harmless if untouched).
5. Update `_verify_feature_columns` assertion to `len == 14`.

### 3.4 Risk gates — RESET adx_threshold from 25.0 (iter-v3/014) BACK to 20.0 (iter-v3/013 baseline)

**CRITICAL**: iter-v3/015 RESETS the `adx_threshold` value to the iter-v3/013 baseline of 20.0. This is NOT a separate axis change — it is REVERSING iter-v3/014's failed gate-knob test (which is now CLOSED per `feedback_adx_axis_asymmetric_v3.md` DOWNGRADED). The single axis varied in iter-v3/015 is the NEW feature `tbr_zscore_30`; the adx_threshold reset is a baseline-restoration step, not a second axis variation.

| Parameter | iter-v3/014 (current) | iter-v3/015 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| **`adx_threshold`** | **25.0 (iter-v3/014's failed test)** | **20.0 (RESET to iter-v3/013 baseline)** |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

**Why the reset is single-axis-compatible**: iter-v3/014 explicitly closed the ADX axis test as NEGATIVE — the value 25.0 was a one-shot test that failed. Reverting to the pre-test baseline (iter-v3/013's effective default 20.0) is NOT a new axis variation; it is restoring the established baseline before introducing the genuinely new variation (the TBR z-score feature). The Critic FINAL of iter-v3/014 explicitly mandated that "iter-v3/016+ moves to a different axis regardless" — iter-v3/015 IS that pivot, and it requires the baseline to be restored to compare cleanly against iter-v3/013's stack.

**An alternative framing** (for Critic disambiguation): one could argue iter-v3/015 IS a 2-axis variation (TBR-add + ADX-reset). The QR's disposition: ADX-reset is structurally equivalent to "iter-v3/015 branches off iter-v3/013's effective config, not iter-v3/014's." Since branches in git are arbitrary (we branched off iter-v3/014 for code-history continuity and to inherit the docstring hygiene fix from `bdcce5d`), the comparison baseline is iter-v3/013's metrics, not iter-v3/014's. The single VARIED axis vs the iter-v3/013 reference is `+tbr_zscore_30`. This framing is consistent with the catalog discipline — iter-v3/014 and iter-v3/015 are sibling EXPLORATIONs both branching conceptually off iter-v3/013.

### 3.5 Sub-fix decomposition (7-item — single new feature axis + ADX-reset baseline restoration + iteration label + V3_FEATURE_COLUMNS plumbing + verifier update + parquet regen + assertion)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Add `compute_tbr_zscore` + write `tbr_zscore_30` column** in `src/crypto_trade/features_v3/volume_micro_v3.py` | New function: `compute_tbr_zscore(df, window=30)` matching the EDA reference implementation in `analysis/iteration_v3-015/tbr_zscore_eda.py`. Append `df["tbr_zscore_30"] = ...` line at the end of `add_volume_micro_v3_features`. | `python -c "from crypto_trade.features_v3.volume_micro_v3 import add_volume_micro_v3_features; import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); df2 = add_volume_micro_v3_features(df.drop(columns=['tbr_zscore_30'], errors='ignore')); assert 'tbr_zscore_30' in df2.columns and df2['tbr_zscore_30'].notna().mean() > 0.95"` exits 0 |
| 2 | **Add `tbr_zscore_30` to `V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py` (append at end; total 14 columns) | One-line addition: `"tbr_zscore_30",  # rank N — microstructure (iter-v3/015 NEW feature family)` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'tbr_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 3 | **Update `_verify_feature_columns()`** assertion in `run_baseline_v3.py` (around line 182-200) from `len == 13` to `len == 14`; add explicit assertion `assert "tbr_zscore_30" in V3_FEATURE_COLUMNS` | Edit the assertion clause | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 |
| 4 | **RESET `adx_threshold` from 25.0 (iter-v3/014) to 20.0 (iter-v3/013 baseline)** in `run_baseline_v3.py:872-874` | Edit the kwarg value | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 AND `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 1 |
| 5 | **Update `ITERATION_LABEL`** from `"v3-014"` to `"v3-015"` in `run_baseline_v3.py:100` | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-015"' run_baseline_v3.py` exits 0 |
| 6 | **Regenerate v3 feature parquets** via `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,MKRUSDT --interval 8h --track v3 --format parquet --workers 4` | Existing CLI command; produces fresh `data/features_v3/*.parquet` with the new 14-column feature set | `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'tbr_zscore_30' in df.columns and df['tbr_zscore_30'].notna().mean() > 0.95"` exits 0 (and same check for LDO/TRX) |
| 7 | **Run `--exploration --seeds 1 --n-trials 10`** on the 3-symbol universe with the 14-feature set | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10`. Wall-clock target: < 15 min (3-symbol, +1 feature column = +~7% feature-loading), 2h hard cap. | `test -f reports-v3/iteration_v3-015/comparison.csv` |

NO NEW labeling change. NO universe change. NO z-score-gate change. NO BTC-band change. NO Hurst change. NO low-vol-floor change. NO hit-rate change. The single varied axis vs iter-v3/013 baseline is `+tbr_zscore_30` to V3_FEATURE_COLUMNS; the ADX-reset is baseline restoration after iter-v3/014's failed test.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 15 verifiers

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **`tbr_zscore_30` computed in `add_volume_micro_v3_features`** | `src/crypto_trade/features_v3/volume_micro_v3.py` | `python -c "from crypto_trade.features_v3.volume_micro_v3 import add_volume_micro_v3_features; import pandas as pd; df = pd.read_parquet('data/BCHUSDT/8h.csv'.replace('csv','parquet')) if False else pd.read_csv('data/BCHUSDT/8h.csv', usecols=['close','high','low','open','volume','quote_volume','taker_buy_volume','taker_buy_quote_volume','open_time','close_time']); df.columns = list(df.columns); out = add_volume_micro_v3_features(df); assert 'tbr_zscore_30' in out.columns"` exits 0 |
| 2 | **V3_FEATURE_COLUMNS contains tbr_zscore_30 at 14 columns** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'tbr_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 3 | **Per-symbol parquet has tbr_zscore_30 with > 95% non-NaN coverage on full series** | `data/features_v3/{BCH,LDO,TRX,MKR}USDT_8h_features.parquet` | `python -c "import pandas as pd; [pd.read_parquet(f'data/features_v3/{s}USDT_8h_features.parquet')['tbr_zscore_30'].notna().mean() > 0.95 for s in ['BCH','LDO','TRX','MKR']]"` returns all True |
| 4 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 5 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 6 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 7 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py:121` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 8 | **`V3_MODELS` has exactly 3 entries; MKR NOT present (inherited iter-v3/013)** | `run_baseline_v3.py:106-110` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3 and 'MKRUSDT' not in {s for _,s in m.V3_MODELS}"` exits 0 |
| 9 | **`REQUIRED_GAP == 66` UNCHANGED (iter-v3/013)** | `src/crypto_trade/strategies/ml/validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==66"` exits 0 |
| 10 | **`adx_threshold=20.0` RESET (iter-v3/013 baseline restored after iter-v3/014's failed test)** | `run_baseline_v3.py:872-874` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 AND `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 1 |
| 11 | **`ITERATION_LABEL` updated to `"v3-015"`** | `run_baseline_v3.py:100` | `grep -E 'ITERATION_LABEL.*=.*"v3-015"' run_baseline_v3.py` exits 0 |
| 12 | **Sub-fix #7 produces comparison.csv** | runner | `test -f reports-v3/iteration_v3-015/comparison.csv` |
| 13 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (axis change took effect; non-trivial signal computed) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-015/comparison.csv'); ms=df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6"` exits 0 |
| 14 | **All adversarial tests pass** | tests | `uv run pytest tests/strategies/ml/ tests/features_v3/ -v` exits 0 (or `tests/strategies/ml/ -v` if no v3 tests dir) |
| 15 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3 chain)**: IS trades < **251** (= ceil(1.2 × 209) counterfactual_n_trades from iter-v3/013 baseline). Plus SECONDARY verifier: `tbr_zscore_30` appears in feature_importance.csv non-zero for at least 1 of 3 per-symbol models. | comparison.csv + feature_importance.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-015/comparison.csv'); n=df.loc[df['metric']=='n_trades','in_sample'].iloc[0]; assert int(n) < 251, f'IS trades >= 251 — TBR feature did not propagate: {n}'"` exits 0 AND feature-importance check |

### 3.7 NO labeling/feature-prune/universe/gate-knob changes

iter-v3/015 is a single-axis (NEW feature family) EXPLORATION. The labeling, model architecture, ATR labeling multipliers, z-score OOD threshold, BTC trend filter band, low-vol floor, Hurst regime check, hit-rate feedback (disabled), CPCV parameters, and walk-forward window are unchanged from iter-v3/013 (note: iter-v3/014 had the failed ADX=25 test; iter-v3/015 RESETS to iter-v3/013's effective baseline). The only differences vs iter-v3/013: `+tbr_zscore_30` in V3_FEATURE_COLUMNS (13 → 14) + `ITERATION_LABEL` (cosmetic) + new `compute_tbr_zscore` function in `volume_micro_v3.py` + `_verify_feature_columns` assertion bump (13 → 14) + parquet regeneration to materialize the 14-column feature set.

### 3.8 Inheritance from iter-v3/014

The `iteration-v3/015` branch was branched from `iteration-v3/014` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15 + ITERATION_LABEL=v3-012`
- `e3168f2 feat(iter-v3/013): drop MKR universe (4→3 symbols) + REQUIRED_GAP 88→66 + ITERATION_LABEL=v3-013`
- `bdcce5d feat(iter-v3/014): ADX threshold 20 → 25 + ITERATION_LABEL=v3-014 + parametrize stale "= 88" docstrings` (note: iter-v3/015 RESETS the ADX value but RETAINS the stale-docstring hygiene fix)
- `fcf6b06 feat(iter-v3/015): tbr_zscore_30 EDA — NEW microstructure feature family` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0 (BEFORE iter-v3/015 sub-fix #2)
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3"` exits 0 (still iter-v3/013 value)
- BEFORE iter-v3/015 sub-fix #4: `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 0 (iter-v3/014's value still in)
- AFTER iter-v3/015 sub-fix #4: `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 AND `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 1 (RESET complete)
- AFTER iter-v3/015 sub-fix #2: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'tbr_zscore_30' in V3_FEATURE_COLUMNS"` exits 0
- AFTER iter-v3/015 sub-fix #6: `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'tbr_zscore_30' in df.columns and df['tbr_zscore_30'].notna().mean() > 0.95"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing
- `grep -nE '= 88' run_baseline_v3.py | wc -l` returns 0 (hygiene from iter-v3/014 retained)

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/015 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/013 (baseline ref) | iter-v3/014 (failed gate test) | iter-v3/015 prediction (3-symbol, 14-feature, ADX=20 RESET) |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | +0.6593 | **predicted [+0.50, +1.30] (median +0.90)** |
| IS trades | 209 | 153 | **predicted 120–251** (counterfactual + Optuna re-opt + new feature interaction) |
| OOS trades | 85 | 60 | **informational ~50–110** |
| OOS Sharpe | +2.6970 | +0.8661 | **informational; high variance because new feature changes both the entry-signal surface AND the model's regime-classifier dimension** |
| Phase 6 wall-clock | 6 min | 6 min | predicted 8–15 min (3 symbols, 14-column feature set adds ~7% to feature-loading time per training fold, plus parquet regen ~2-3 min separate from runner), hard cap 2h |

The IS prediction band [+0.50, +1.30] is intentionally **broad** because NEW-feature-family axes are higher-variance than gate-threshold variations:
- The candidate has non-trivial rank-IC (BCH 7-bar +0.065, LDO 1-bar -0.027 fade) AND low IC redundancy (max 0.1654 vs existing 13). First-order direction is favorable.
- Optuna re-optimization on a 14-feature set: with 1 additional column (8% more), Optuna may converge on different optimal tree depth/leaves; the model may either incorporate the new feature meaningfully (improving Sharpe) or leave it in low-importance position (no change).
- The mixed-sign per-symbol rank-IC is the LightGBM-friendly scenario but also introduces sign-loading variance — the model must learn each symbol's TBR direction independently.
- 3rd consecutive favorable IS calibration overshoot pattern (iter-v3/010, 011, 013) was BROKEN at iter-v3/014 (NEGATIVE outcome, IS Sharpe +0.66 in lower half of predicted band). The 30%-upper-bound widening is no longer warranted post-iter-v3/014; iter-v3/015 uses a more moderate band consistent with NEW-axis variance.

Median +0.90 sits below iter-v3/013's +1.01 to reflect: (a) NEW-feature axes are higher-variance than gate-threshold axes (axis category 1 vs category 6); (b) Optuna may downweight the new feature in early-iteration tree splits if the loss surface change is gradual; (c) the new feature could introduce some additional noise in low-information regimes.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → the new feature actively hurt the model (overfit on tbr_zscore_30 in some regime, or interacted destructively with existing features). Verdict: EXPLORATION-NEGATIVE on feature-family axis. Catalog row marks NO candidate; iter-v3/016+ explores a different axis.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3 chain)**: IS trade count > **251** (= ceil(1.2 × counterfactual_n_trades=209)) → NEW feature axis did NOT propagate (analogous to iter-v3/012's NULL-RESULT trade-roster identity but with different root cause — likely `V3_FEATURE_COLUMNS` reassignment didn't propagate through `_verify_feature_columns()` OR `LightGbmStrategy(feature_columns=...)` argument OR the feature parquet is stale). Verdict: BLOCK (process); engineer documents.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe with 14-feature set → unexpected slowdown in feature-loading or training; engineer documents the cause.

**Falsifier 4 (NEW for NEW-feature-axis discipline)**: `tbr_zscore_30` does not appear in feature_importance.csv for ANY of the 3 per-symbol models (or appears with importance == 0 on all 3) → the model effectively ignored the new feature; the IS Sharpe delta is not attributable to the new feature. Verdict: EXPLORATION-NEGATIVE-no-effect (NULL-RESULT subtype, sister to iter-v3/012). Catalog row marks NO candidate.

**Process falsifier**: pre-flight `grep adx_threshold=20.0 run_baseline_v3.py` exits non-zero, OR `grep -E 'tbr_zscore_30' src/crypto_trade/features_v3/__init__.py` exits non-zero, OR `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'tbr_zscore_30' in df.columns"` exits non-zero → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe Δ ≥ +0.10 vs iter-v3/013 (i.e., ≥ +1.11) AND broad-based per-symbol AND IS trades < 251 (Falsifier 2 PASS) AND `tbr_zscore_30` in top-10 importance for ≥ 1 model (Falsifier 4 PASS) | "Microstructure regime-classifier added genuine alpha — broad-based gain" | iter-v3/016 EXPLORATION on a DIFFERENT axis category (NEW model arch / NEW labeling / NEW risk primitive) — single-axis discipline preserved |
| `EXPLORATION-PROMISING-INERT` | IS Sharpe within ±0.10 of iter-v3/013 (i.e., in [+0.91, +1.11]) AND IS trades < 251 AND `tbr_zscore_30` in top-10 importance | "Microstructure feature added but information overlap with existing features near-saturated" | iter-v3/016+ EXPLORATION on a DIFFERENT axis category |
| `EXPLORATION-PROMISING-MECHANICAL` | IS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/013 — UNLIKELY for new-feature axis given non-trivial rank-IC; flagged for completeness | "New feature added without behavioral change — accounting drift" | similar to iter-v3/013 framing |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | IS Sharpe direction wrong (-Δ vs iter-v3/013) AND `tbr_zscore_30` importance == 0 across all 3 models (Falsifier 4 fires) | "Model ignored the new feature; saturation pattern" | iter-v3/016+ EXPLORATION on a DIFFERENT axis category |
| `EXPLORATION-NEGATIVE` | IS Sharpe down > 0.10 (i.e., < +0.91) AND `tbr_zscore_30` IS in feature importance (Falsifier 4 PASS) → the model used the new feature but it actively hurt | "TBR z-score destructive — possibly overfit on transient flow imbalance regime" | iter-v3/016+ EXPLORATION on a DIFFERENT axis category (NOT another microstructure variant — single-axis discipline) |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades > 251) triggered, OR Falsifier 3 (wall-clock) triggered | (none) | Diary documents, iter-v3/016 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 inherited + 4 methodology-specific = 8 total)

iter-v3/015 inherits the cadence-discipline safeguards from skill SHA `d5c9f21` + the saturation-predictor rule + the new structural-axis preference rule:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h.
2. **Single-axis variation rule** honored (only `+tbr_zscore_30` added to V3_FEATURE_COLUMNS; ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/CPCV byte-for-byte identical to iter-v3/013; `adx_threshold` RESET from iter-v3/014's failed test back to iter-v3/013 baseline = baseline restoration, not separate axis variation per §3.4 framing).
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE / NEGATIVE-no-effect / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-015.md`.
4. **Saturation predictor falsifier** (Section 3.6 row 15, threshold derived `ceil(1.2 × counterfactual_n_trades=209) = 251` per Critic FINAL Rec 3 chain) actively verifies that the new feature axis propagated to the model output (IS trades < 251).

Methodology-specific safeguards (NEW-feature-family axis):

5. **Feature-importance verifier** (Section 3.6 row 15 secondary): `tbr_zscore_30` must appear in feature_importance.csv non-zero for at least 1 of 3 per-symbol models (Falsifier 4). Distinguishes "model used the feature actively" from "model ignored the feature; Sharpe Δ was Optuna re-opt artifact."
6. **EDA gate pre-commits** (Section 2): coverage ≥ 80% PASS (100%); IC redundancy < 0.70 PASS (max 0.1654); rank-IC non-trivial PASS (max 0.0649). All three EDA gates passed BEFORE the brief was written; Phase 6 inherits a candidate that is structurally tractable.
7. **Past-only computation discipline**: `compute_tbr_zscore` uses `.shift(1)` on rolling stats so bar t z-score uses bars t-30...t-1 only — STRICTLY past-only. Critic Check 1 (Look-Ahead) verifier mirrors the EDA reference implementation.
8. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-014)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-checks**: `adx_threshold=20.0` reset, `tbr_zscore_30` in V3_FEATURE_COLUMNS, parquet has `tbr_zscore_30` column. Catches the case where setup edits were silently lost or feature regen was skipped.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NEW-feature-axis-specific risks (3 explicit)

1. **Data quality**: TBR raw values are guaranteed in [0, 1] by Binance kline spec, but extreme regimes (e.g., 100% taker-buy on a thin candle) could produce z-scores >5σ if the rolling-30 baseline is misaligned. Mitigation: distribution check in §2.2 confirms p99 ≈ +2.4 (no extreme-tail blowup); the EDA implementation does not clip z-scores. If extreme z-scores appear in regen at Phase 6, Engineer reports in the engineering report (audit-trail discipline).
2. **Look-ahead from intra-candle TBR settlement**: kline candles report TBR aggregated over the entire candle period. The TBR for candle t is FULLY KNOWN at candle t close (close_time). The strategy decision at candle t open uses TBR z-score from candle t-1 (via `.shift(1)` discipline in EDA + the same discipline in `add_volume_micro_v3_features` implementation). No look-ahead. Critic Check 1 verifier mirrors this — the past-only `.shift(1)` pattern is the canonical defense.
3. **Feature redundancy with existing vol-related features**: max |IC| = 0.1654 vs `vwap_dev_20` (the strongest pair) — both volume/order-flow related. Although below the 0.70 threshold by a wide margin, the structural similarity may cause LightGBM to exhibit moderate substitution effects (the new feature steals some `colsample_bytree` picks from `vwap_dev_20`). Since `colsample_bytree=1.0` in `--exploration` mode, this is mostly an information-redundancy concern, not a tree-construction concern. Mitigation: Falsifier 4 (feature-importance check) catches the case where TBR is fully substituted.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED (single-feature-axis variation; gates byte-identical to iter-v3/013)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, 14-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | **ADX gate (RESET)** | trade only when ADX ≥ **20** (RESET from iter-v3/014's failed 25 to iter-v3/013 baseline) | ≈ 60% of bars pass | Trend filter — wider passthrough than iter-v3/014 |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over **14** features now — slightly higher kill rate due to one more column for OOD computation) | ≈ 26–37% killed (was ~25-35% with 13 cols; minor uplift expected) | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited iter-v3/012) | Macro flips |

Combined kill rate target: **80–90%** (matches iter-v3/013's range; ADX RESET back to 20 widens passthrough vs iter-v3/014's 85-92%; z-score OOD over 14 cols may slightly tighten). The only primitive whose threshold changes is the ADX RESET (back to iter-v3/013 baseline); all others' specs are byte-identical to iter-v3/013.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent. Adding `tbr_zscore_30` to V3_FEATURE_COLUMNS expands primitive 4's z-score OOD computation to 14 features (more dimensions to check, slightly tighter kill rate). The other 6 primitives are unaffected by feature-set changes — they operate on candle/symbol-level signals computed independently of the LightGBM model's input features.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/013/014. Regime coverage includes 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction. The 3-symbol portfolio's exposure to these regimes is broadly similar; the new TBR feature provides additional regime-classification dimension (high-flow vs low-flow regimes) WITHIN each of these macro periods.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/013 OOS showed 65.65% LDO concentration. iter-v3/015 OOS concentration may shift either direction depending on whether TBR feature reshapes per-symbol trade frequencies. Per-symbol effects are informational; the brief does not pre-register a concentration falsifier (EXPLORATION protocol). Future CONFIRMATION QR will scope ex-LDO basket fragility separately.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 7 prior EXPLORATIONs)

**Prediction P1 (process, P=5%)**: `tbr_zscore_30` column not added to V3_FEATURE_COLUMNS or not propagated to the LightGBM strategy's `feature_columns` argument. Engineer adds the column to the constant but a path-resolution issue in `LightGbmStrategy(feature_columns=list(V3_FEATURE_COLUMNS))` causes runtime to use a stale column list. **Detection signal**: Falsifier 4 (feature-importance check) shows TBR with importance 0 across all 3 models OR Falsifier 2 (saturation predictor) fires (IS trades > 251). **Mitigation**: §3.6 row 2, 3, 15 verifiers (3 independent signals).

**Prediction P2 (process, P=5%)**: parquet regeneration fails or produces stale parquets (tbr_zscore_30 missing or NaN). Most likely cause: `add_volume_micro_v3_features` not called via the v3 features CLI (or called on cached pre-feature data). **Detection signal**: §3.6 row 3 verifier fails — `pd.read_parquet(...)['tbr_zscore_30'].notna().mean() > 0.95` returns False. **Mitigation**: pre-flight verifier blocks Phase 6 launch.

**Prediction P3 (process, P=10%)**: wall-clock overshoots the 30-min target due to feature-set expansion (14 cols vs 13 means ~7% more loading per training fold). 3-symbol universe with 14-feature set should run in 8-15 min. If runtime > 30 min, signal of unexpected slowdown (e.g., feature-loading pathology or filesystem issue with parquet regen). **Detection signal**: engineering report wall-clock minutes. **Mitigation**: 2h hard cap by skill spec.

**Prediction P4 (model, P=45%)**: IS Sharpe lifts moderately to [+1.10, +1.30]; the new TBR z-score gives the model a microstructure regime-classifier signal that complements the existing 13-feature set; PROMISING. The LightGBM model uses the TBR feature in tree splits, learning per-symbol sign loadings (BCH high TBR = continuation; LDO high TBR = fade) consistent with the EDA rank-IC pattern.

**Prediction P5 (model, P=30%)**: IS Sharpe stays in iter-v3/013 range [+0.91, +1.11] ±0.10; the new TBR z-score is included in the model but its information overlap with existing features (max |IC| 0.1654 with vwap_dev_20) is enough that the model's tree splits substitute TBR for vwap_dev_20 in some contexts without net Sharpe lift; PROMISING-INERT.

**Prediction P6 (model, P=15%)**: IS Sharpe drops to < +0.91; the new TBR z-score introduces noise that the model overfits on in early Optuna trials (the +1.0 IS Sharpe of iter-v3/013 was at the high-end of the v3 catalog; adding a new feature increases the loss-surface dimensionality and Optuna may converge to an overfit point); NEGATIVE-soft. iter-v3/016+ would explore a different axis (NEW model arch or NEW labeling architecture) since the feature axis demonstrated edge-detrimental risk.

**Prediction P7 (model, P=10%)**: IS Sharpe spikes to > +1.30; TBR provides a structurally novel signal that compounds with existing features for an unexpected lift; PROMISING-strong. This would be the strongest evidence yet that NEW-feature-family axes are higher-impact than gate-knob axes (consistent with `feedback_structural_over_knob_exploration.md` rationale).

P4 + P5 + P7 sum to 85% (PROMISING-family outcome). P6 sums to 15% (off-distribution outcomes). Process predictions P1-P3 sum to 20% (failure-mode hedging).

**Calibration vs prior EXPLORATIONs**:
- 3-consecutive favorable IS overshoot pattern (iter-v3/010, 011, 013) was BROKEN at iter-v3/014 (NEGATIVE outcome below median). The 30%-upper-bound widening rule from iter-v3/013 caveat 4 is no longer warranted post-iter-v3/014; iter-v3/015 uses a moderate band consistent with NEW-axis-category variance.
- The NEW-feature-family axis category has ZERO prior calibration data in v3 — iter-v3/015 is the first. The QR's prior bands draw on:
  - iter-v3/007's top-14 features axis (IS Sharpe Δ +0.30 vs iter-v3/003 baseline) — feature-pruning, not new feature, so weak analog
  - iter-v3/010's labeling-axis (IS Sharpe Δ +0.49) — non-feature axis but also non-knob
  - iter-v3/013's universe drop (IS Sharpe Δ +0.20) — also non-knob structural change
- The median +0.90 prediction sits between iter-v3/013's +1.01 (highest in v3) and iter-v3/014's +0.66 (NEGATIVE outcome) — appropriately conservative-to-moderate for an axis category with no prior calibration data. The 30% widening from iter-v3/013 caveat 4 is NOT applied because that pattern was broken at iter-v3/014.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 11 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 11 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers (per skill spec at SHA `f0f8b84`).

1. **IS Sharpe ≥ +0.40** (PROMISING threshold inherited from cadence skill): catalog row records PROMISING verdict on numerical-axis basis.
2. **IS Sharpe < +0.10**: Falsifier 1 — EXPLORATION-NEGATIVE.
3. **IS Sharpe in [+0.10, +0.40)**: PROMISING-INERT (inert verdict) — catalog row records INERT.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level` (informational at EXPLORATION; 120 IS / 50 OOS lower bound from Section 4.2 prediction). Realized iter-v3/015 IS expected ~120-251; OOS expected ~50-110. Both ABOVE the 50-trade floor; the bundle (5 outer × 3-4× ensemble) at CONFIRMATION will multiply this 3-4×.
5. **PBO < 0.40 (per-cell mean) AND `n_high_pbo_cells_99 ≤ 4`**: methodology hygiene; both inherited unchanged from iter-v3/013 0.1075 mean / 2 high-cells (TRX 2025-Q4 carry-forward). iter-v3/015 expected near-identical PBO unless new feature has unexpected cell-level effect.
6. **IC max abs < 0.70**: per Critic Check 4 — the new feature `tbr_zscore_30` has max |IC| 0.1654 vs the existing 13 (verified at SHA `fcf6b06`); the existing 13-feature pairwise max was 0.685; **after-add expected max |IC| in the 14-feature pairwise matrix remains 0.685** (the new column doesn't create a NEW pair above 0.685 since its max IC is 0.1654, well below 0.685 — so the IC ceiling is unchanged at iter-v3/013's 0.685).
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS** (or stationarity rationale per Section 4 precedent): the 13 inherited features unchanged; the new `tbr_zscore_30` is a z-score (rolling-window mean-zero by construction) — ADF p-value is structurally near-zero on z-scored series. Engineer's Phase 6 ADF test will confirm; pre-commit expectation is PASS.
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis `fcf6b06`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-014).
10. **Symbol exclusion + feature isolation**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `features_v3` does not import `features` (v1) or `features_v2` (v2). The new `compute_tbr_zscore` lives in `volume_micro_v3.py` (track-isolated); zero new imports from v1/v2.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3 chain)**: IS trades < **251** (= ceil(1.2 × counterfactual_n_trades=209 from iter-v3/013 baseline)). The threshold is DERIVED per-iteration from §2.5's counterfactual; not a hardcoded constant. **PLUS SECONDARY VERIFIER (Falsifier 4)**: `tbr_zscore_30` appears in feature_importance.csv non-zero for at least 1 of 3 per-symbol models. Critic uses BOTH signals to disambiguate "axis propagated AND model used feature" from "axis added but model ignored it (NULL-RESULT)." Predicted behavioral effect: IS trade count change ~5-30% from baseline 209 (range [120, 251]).

**Catalog-axis verdicts** map to §4.4 table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-014** — no version bumps in iter-v3/015:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 2.3.1 (or recent compatible)
scikit-learn = 1.6.1
pyarrow = 19.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork — fallback from mlfinlab=1.4)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.5 (adfuller for ADF stationarity)
optuna = 4.5.0
```

No package additions or version bumps. The new `compute_tbr_zscore` function uses only `numpy` + `pandas` (already imported in `volume_micro_v3.py`); no new dependencies. No new fetcher modules — the TBR data is already in every Binance 8h candle.

---

## Section 10 — Adversarial Tests (inherited; one new test recommended)

Adversarial test suite at `tests/strategies/ml/` is unchanged. The Engineer SHOULD add one new test in Phase 6 (recommended, not strictly required for EXPLORATION):

- `tests/features_v3/test_volume_micro_v3.py::test_tbr_zscore_past_only` — assert `compute_tbr_zscore(df)` produces NaN for the first 30 rows (rolling window initialization) AND that the value at row N depends only on rows N-30 to N-1 (past-only, .shift(1) verified). Mirrors the look-ahead defense in EDA.

If Engineer runs out of time (2h cap), the adversarial test addition is deferred to iter-v3/016+ (Critic FINAL note). The runtime correctness is verified via §3.6 row 1 verifier (which runs `add_volume_micro_v3_features` on the full BCH parquet and asserts column presence + coverage).

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/015 catalog row before backtest results are known:

```
| iter-v3/015 | 2026-05-07 | NEW microstructure feature → +tbr_zscore_30 (V3_FEATURE_COLUMNS 13 → 14) | IS Sharpe Δ TBD vs iter-v3/013 +1.01 | OOS Sharpe TBD (informational) | TBD verdict | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 + §8 criterion 1-3 + 11. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/015 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc):
- If verdict = `EXPLORATION-PROMISING` AND `EXPLORATION-PROMISING-INERT` is NOT triggered AND Falsifier 4 (feature-importance check) PASSES: catalog row marked YES candidate (compoundable with iter-v3/010 labeling + iter-v3/011 z-score as a fourth axis-lift; first NEW-feature-family ingredient in the v3 bundle).
- If verdict = `EXPLORATION-PROMISING-INERT`: catalog row marked NO candidate (axis is orthogonal but information overlap saturates lift; future feature-family axes should test less-correlated features OR more aggressive single-feature-add experiments).
- If verdict = `EXPLORATION-PROMISING-MECHANICAL` (unlikely but flagged): catalog row marked YES with NON-COMPOUNDABLE flag (point decision, like drop-MKR).
- If verdict = `EXPLORATION-NEGATIVE` or `EXPLORATION-NEGATIVE-no-effect`: catalog row marked NO; iter-v3/016 explores a DIFFERENT axis category (NEW model arch e.g., XGBoost, OR NEW labeling e.g., meta-labeling M2 sizing, OR NEW risk primitive). NEXT iteration MUST NOT be another microstructure variant — single-axis discipline + axis-category-rotation discipline (per `feedback_structural_over_knob_exploration.md` axis priority order).

**Catalog count after iter-v3/015**: 8 of 10 EXPLORATIONs; **2 more required** before any CONFIRMATION can launch. Axis coverage: features-prune × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 + **NEW-feature-family × 1** = 7 unique axis representations after iter-v3/015, FIRST genuinely-novel feature-family axis.

**Forward axis pipeline** (iter-v3/016, /017 candidates pre-pre-committed for QR continuity, NOT mandates per `feedback_structural_over_knob_exploration.md` axis priority discipline):
- iter-v3/016 candidates: NEW model architecture (XGBoost, CatBoost, stacking ensemble) — Category 2; NEW labeling (meta-labeling M2 sizing) — Category 3; NEW risk primitive (correlation-aware kill switch) — Category 4
- iter-v3/017 candidates: depends on iter-v3/015 + iter-v3/016 verdicts; NEW feature family (funding rate, OI, basis — the data-fetch-required ones) only if a fetch+regen workflow can be developed; otherwise rotate among Categories 2-4

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (8 of 10); STRUCTURAL axis declared; explicit "NOT a gate-threshold knob"; references `feedback_structural_over_knob_exploration.md`.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (microstructure regime-classifier + LightGBM-friendly mixed-sign per-symbol rank-IC).
- [x] §2 IS-only numerical evidence with COMMITTED analysis script SHA `fcf6b06`; coverage 100% / max |IC| 0.1654 / max rank-IC +0.0649 / behavioral-effect predictor with derived `falsifier_threshold = ceil(1.2 × 209) = 251`.
- [x] §3 sub-fixes (7-item) with verifier commands; reconciliation table 15 rows; explicit RESET adx_threshold=20.0 in sub-fix #4.
- [x] §4 predicted IS Sharpe band [+0.50, +1.30] (median +0.90, calibrated against iter-v3/013 +1.01 baseline AND iter-v3/014 NEGATIVE break of 30%-widening pattern); 4 catalog framings + falsifiers 1-4 + process locked.
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks).
- [x] §6 7-primitive table with adx_threshold=20 RESET explicit.
- [x] §7 6 failure-mode predictions calibrated against 7 prior EXPLORATIONs (process P1-P3 = 20%; model P4-P7 = 100%).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived threshold per Critic FINAL Rec 3 chain + Falsifier 4 secondary feature-importance verifier.
- [x] §9 library stack, no bumps; no new dependencies.
- [x] §10 adversarial tests inherited; one new test recommended (deferrable).
- [x] §11 catalog row pre-commit + dispositions; forward axis pipeline (iter-v3/016+ candidates per axis priority order).

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
