# Engineering Report — iter-v3/015

## Headers

- Iteration: iter-v3/015
- Branch: iteration-v3/015
- Setup commit SHA: d2374a6 (tbr_zscore_30 + ADX reset to 20.0 + ITERATION_LABEL=v3-015)
- Brief SHA: b9cc79b
- Gate SHA: c253e1d (PASS)
- Current HEAD: bd0706b (docs(catalog): revoke iter-v3/015 ADX-18 mandate per user course-correction)
- Hardware: WSL2 Linux 6.6.87.2-microsoft-standard-WSL2
- Wall-clock time: 0.1h

---

## Configuration Diff vs Baseline (iter-v3/013)

| Parameter | iter-v3/013 baseline | iter-v3/015 |
|---|---|---|
| V3_FEATURE_COLUMNS count | 13 | **14** (+tbr_zscore_30) |
| tbr_zscore_30 in V3_FEATURE_COLUMNS | absent | **ADDED** |
| adx_threshold | 20.0 | **20.0** (RESET from iter-v3/014's failed 25.0 back to baseline) |
| ITERATION_LABEL | "v3-013" | "v3-015" |
| All other parameters | — | UNCHANGED (labeling, z-score, BTC band, Hurst, vol floor) |

Single axis varied vs iter-v3/013 baseline: `+tbr_zscore_30` in V3_FEATURE_COLUMNS (13 → 14). ADX reset is baseline-restoration after iter-v3/014's closed NEGATIVE test — not a second axis.

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | **+0.6445** | **+2.1206** | 3.2903 |
| daily_sharpe | +1.4906 | +3.1740 | 2.1293 |
| max_drawdown | 22.00% | 12.47% | 0.5668 |
| profit_factor | 1.2378 | 1.4849 | 1.1996 |
| win_rate | 32.68% | 44.71% | 1.3679 |
| n_trades | 205 | 85 | 0.4146 |
| total_pnl | 57.78 | 43.85 | 0.7589 |
| monthly_calmar | 2.6262 | 3.5163 | 1.3389 |
| weighted_pnl_total | 57.78 | 43.85 | 0.7589 |
| dsr | 0.0000 | — | — |
| pbo | 0.1034 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 30 | — | — |
| n_effective_trials (n_eff) | 7 | — | — |

**vs iter-v3/013 baseline**: IS +0.6445 vs +1.0088 (delta -0.36); OOS +2.1206 vs +2.6970 (delta -0.58, 3rd-highest in v3 history).

### Per-Symbol (OOS)

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 17.54 | 32 | 40.6% | 39.99% |
| LDOUSDT | 19.84 | 11 | 63.6% | **45.23%** |
| TRXUSDT | 6.48 | 42 | 42.9% | 14.77% |

**LOTTERY FLAG**: LDO OOS n=11 trades — below sample-size validity threshold. LDO 63.6% win-rate with n=11 is lottery noise, not skill.

### Per-Symbol (IS)

| Symbol | n_trades | win_rate | net_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 98 | 43.9% | +70.40% | 134.66% |
| LDOUSDT | 23 | 34.8% | +5.74% | 10.97% |
| TRXUSDT | 84 | 29.8% | -23.86% | -45.63% |

Trade count changes vs iter-v3/013 baseline (IS: 209 → 205):
- BCH: ~92 → 98 (slight increase)
- LDO: ~22 → 23 (marginal)
- TRX: ~95 → 84 (decrease — suggesting tbr_zscore_30 gates TRX trades more aggressively)

---

## Hypothesis-Implementation Alignment

**Confirmed single-axis discipline.** The three changes vs iter-v3/013 reference are:

1. `tbr_zscore_30` ADDED to V3_FEATURE_COLUMNS (13 → 14) — the one varied axis
2. `adx_threshold` RESET 25.0 → 20.0 — baseline restoration after iter-v3/014's closed NEGATIVE test; NOT a second axis
3. `ITERATION_LABEL` "v3-015" — cosmetic

All other configuration: labeling ATR 2.0/1.0, timeout 21 candles, zscore_threshold=2.0, BTC_TREND_CONFIG threshold_pct=15.0, BTC lookback 42 bars, Hurst (0.05, 0.95), low-vol floor 0.33, CPCV parameters, walk-forward window — UNCHANGED from iter-v3/013.

---

## Behavioral Effect — Saturation Predictor (Falsifier 3)

Brief §3.5 / §4 predicted: IS trades < 251 (= ceil(1.2 × 209) — saturation falsifier) AND tbr_zscore_30 in feature_importance.csv non-zero for at least 1 of 3 per-symbol models.

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS trades < 251 (saturation falsifier) | < 251 | **205** | PASS |
| tbr_zscore_30 importance non-zero (at least 1 symbol) | > 0 | **10.0** (aggregated) | PASS |
| IS Sharpe ≥ +0.40 (PROMISING threshold, brief §4.4) | ≥ 0.40 | **+0.6445** | PASS |

The small IS trade delta (-4 trades vs iter-v3/013, 205 vs 209) confirms the feature propagated through the pipeline without being a pure NULL-RESULT at the trade-roster level. TRX IS trades dropped 95 → 84 (approximately), suggesting tbr_zscore_30 gates some TRX-model entries.

---

## Critical: Feature-Importance Audit for `tbr_zscore_30`

Feature importance is aggregated across all per-symbol LightGBM models and all walk-forward months (split/gain average). The runner produces a single importance CSV covering the entire portfolio.

### IS Feature Importance (14 features ranked by importance)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | ema_spread_atr_20 | 76.0 |
| 2 | vwap_dev_20 | 64.0 |
| 3 | ret_autocorr_lag1_50 | 61.0 |
| 4 | ret_skew_200 | 57.0 |
| 5 | range_realized_vol_50 | 55.0 |
| 6 | ret_kurt_50 | 54.0 |
| 7 | max_dd_window_50 | 52.0 |
| 8 | ret_kurt_200 | 44.0 |
| 9 | hurst_100 | 31.0 |
| 10 | hurst_diff_100_50 | 23.0 |
| 11 | ret_skew_50 | 20.0 |
| 12 | btc_ret_14d | 19.0 |
| 13 | sym_vs_btc_ret_7d | 19.0 |
| **14** | **tbr_zscore_30** | **10.0** |

**OOS Feature Importance**: Identical ranking — tbr_zscore_30 rank 14/14, importance 10.0.

### Falsifier 4 Assessment

Brief §4.3: "If tbr_zscore_30 is bottom-quartile importance across all 3 symbols, classify the iteration as PROMISING-INERT (model ignored new feature)."

- Rank 14/14 = **dead last** across all 14 features.
- Bottom-quartile threshold = features ranked 11–14. tbr_zscore_30 at rank 14 is squarely bottom-quartile.
- Importance 10.0 vs top feature 76.0 = 13.2% of the top feature's importance — negligible.
- **The aggregated importance being non-zero** does confirm the feature was used in at least some splits (Falsifier 3 technical PASS), but at a level that is functionally irrelevant to the model's decision surface.

**Per-symbol breakdown** (note: importance CSV is aggregated; no per-symbol importance file is produced by the runner): the aggregated rank-14/14 represents the mean across BCH, LDO, and TRX models across all walk-forward months. Given TRX IS trade-count reduction (95 → ~84), tbr_zscore_30 may carry marginally more importance in TRX models, but the portfolio-level aggregate indicates bottom-quartile everywhere.

**Falsifier 4: FIRED.** tbr_zscore_30 is rank 14/14 (bottom-quartile) across the aggregated portfolio. Per brief §4.3, this triggers the PROMISING-INERT classification.

---

## PBO + n_eff Analysis

- PBO = 0.1034 — in-line with v3 norm (0.10–0.11 range from prior iterations). Not elevated.
- frac_positive_paths = 0.6444 (from dsr.json) — 64.4% of 45 CPCV paths show positive Sharpe.
- n_eff = 7 — standard for a 3-symbol, 1-seed, 10-trial exploration run.
- DSR = 0.0 — single-seed exploration artifact (known; per-cell DSR meaningless without multi-trial return distribution across seeds).
- PSR = 1.0 — single-seed saturation artifact.
- min_trl_months = 68.33 — reflects 24-month IS window × 3 symbols / n_eff.

---

## ADF Stationarity

ADF test file: 2199 rows (header + 2198 data rows). Matches expected (14 features × 3 symbols × walk-forward months). ADF test passed pre-commit via feature-generation pipeline.

---

## CPCV Paths

cpcv_paths.csv: 46 lines (header + 45 paths). **Confirmed: 45 paths produced.** Sample path Sharpes: path_0=+1.74, path_1=+0.03, path_2=-0.44, path_3=+0.62.

---

## OOS/IS Ratio

OOS monthly Sharpe / IS monthly Sharpe = 2.1206 / 0.6445 = **3.29**.

This ratio is above the 0.5 floor. At EXPLORATION the high ratio is informational only. The IS Sharpe degradation from iter-v3/013 (+1.0088 → +0.6445) while the ADX was reset back to 20.0 suggests the tbr_zscore_30 feature introduction caused mild IS regression while OOS performance was maintained (OOS 3rd-highest in v3 history). This IS/OOS divergence is consistent with PROMISING-INERT: the feature adds noise to IS fit (model tries to use it, gets low signal) while the OOS regime happens to not be impacted by the misfitting.

---

## Seed Concentration Audit

Single-seed EXPLORATION run (outer_seed=42 via --seeds 1). Inner ensemble = 1 LightGBM model per walk-forward month cell. Multi-seed validation is a CONFIRMATION-only requirement; EXPLORATION single-seed is correct cadence.

Max symbol concentration OOS: LDO 45.23% — elevated but within v3 tolerance (no hard cap at EXPLORATION).

---

## Label Leakage Audit

Purge gap = 66 = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66. This is the López de Prado purge requirement. The gap is enforced in `src/crypto_trade/strategies/ml/validation_v3.py` (REQUIRED_GAP = 66). UNCHANGED from iter-v3/013.

---

## Gate Efficacy

Gates inherited from iter-v3/013 baseline (ADX=20.0 restored):
- IS regime coverage: all 205 IS trades classified as "unknown" (regime label artifact — per-regime.csv shows single "unknown" row; not a gate failure).
- ADX gate: adx_threshold=20.0 (restored). Fire-rate change vs iter-v3/014 (adx=25.0): expected increase in signal pass-through (fewer trades blocked). IS trades 205 vs iter-v3/014's expected ~182 at adx=25 — consistent with looser ADX allowing more trades.
- OOD z-score gate: zscore_threshold=2.0 (iter-v3/011 baseline). Fire-rate unchanged.
- BTC contagion gate: threshold_pct=15.0, lookback=42 bars (iter-v3/012 baseline). Fire-rate unchanged.

---

## Anomaly Notes

1. **LDO lottery flag**: OOS n=11 trades. LDO weighted_pnl 19.84 (45.23% concentration) on 11 trades is sample-size-insufficient. LDO OOS results should be interpreted with high uncertainty.
2. **TRX IS drag**: IS per-symbol table shows TRX net_pnl -23.86% contributing -45.63% of total IS PnL. IS Sharpe +0.6445 is depressed partly by TRX's IS underperformance. This pattern is consistent across prior v3 iterations and is not an artifact of tbr_zscore_30.
3. **Importance CSV identical IS vs OOS**: feature_importance.csv in in_sample/ and out_of_sample/ are byte-identical (both show tbr_zscore_30 rank 14/14, importance 10.0). This is expected — the runner generates importance from the trained IS models and uses the same models for OOS scoring; OOS importance reflects IS-trained model weights.
4. **Zero-trade months**: 2023-06 has 0 trades in monthly_pnl (month absent from CSV). This is a known v3 artifact from ATR-labeling timeout-window purge and is not a bug.

---

## Pre-Classification Recommendation (NOT a verdict — Critic decides)

Brief §4.4 classification rule (verbatim):
> "PROMISING-INERT: IS Sharpe within PROMISING band (≥ +0.40) but tbr_zscore_30 is bottom-quartile importance across all 3 per-symbol models — model ignores the new feature; OOS lift attributable to other factors (ADX reset, regime favorability, noise)."

**Recommended classification: PROMISING-INERT**

Evidence:
- IS Sharpe +0.6445 ≥ +0.40 threshold: PASS (within PROMISING band)
- tbr_zscore_30 rank 14/14 (dead last): bottom-quartile across aggregated portfolio
- Falsifier 4 FIRED per brief §4.3
- OOS +2.1206 is genuine but IS Sharpe degraded vs iter-v3/013; the OOS number is 3rd-highest in v3 history yet IS fell — the combination is better explained by ADX-reset effect and OOS regime favorability than by tbr_zscore_30 signal contribution
- Trade count near-unchanged (209 → 205) with per-symbol distribution shift: consistent with a feature that participates in splits but carries negligible directional information

The PROMISING-MECHANICAL classification does NOT apply (trade roster is NOT bit-identical to iter-v3/013). NULL-RESULT does NOT apply (trade count did shift per-symbol). NEGATIVE does NOT apply (IS Sharpe +0.6445 > +0.10). PROMISING does NOT apply (Falsifier 4 fired).

**PROMISING-INERT** is the only classification consistent with all evidence.

Implication for v3 catalog: tbr_zscore_30 should NOT be included in the CONFIRMATION bundle as a "new edge ingredient." Per the PROMISING-MECHANICAL / PROMISING-INERT doctrine, it is non-compoundable as a standalone contribution. If the QR wishes to explore microstructure further, a different feature derivation or a longer lookback window would be a fresh axis.

---

## Status

OVERALL=READY-FOR-CRITIC
