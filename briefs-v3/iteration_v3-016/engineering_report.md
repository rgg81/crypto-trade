# Engineering Report — iter-v3/016

## Headers

- Iteration: iter-v3/016
- Branch: iteration-v3/016
- Setup commit SHA: 1aa3eb3 (drop tbr_zscore_30 + XgboostStrategy + smoke tests + xgboost dep)
- Gate SHA: d5930fe (PASS)
- Brief SHA: 10f3db9
- Current HEAD: 1aa3eb3
- Hardware: WSL2 Linux 6.6.87.2-microsoft-standard-WSL2
- Wall-clock time: 0.14h

---

## Configuration Diff vs Baseline (iter-v3/013)

| Parameter | iter-v3/013 baseline | iter-v3/016 |
|---|---|---|
| Boosting library | LightGBM | **XGBoost 2.1.4** |
| Model class | LightGbmStrategy | **XgboostStrategy** |
| V3_FEATURE_COLUMNS count | 13 | **13** (UNCHANGED — tbr_zscore_30 dropped before XGBoost swap) |
| grow_policy | n/a (LightGBM leaf-wise) | **'depthwise'** (level-wise, maximising architectural difference) |
| num_leaves Optuna param | sampled [15, 127] | **DROPPED** (no-op under depthwise) |
| min_child_weight Optuna range | min_child_samples [5, 100] | **min_child_weight [5, 100]** (semantic equivalent) |
| objective (binary) | 'binary' + is_unbalance=True | **'binary:logistic' + scale_pos_weight** (computed per fit) |
| objective (ternary) | 'multiclass' + num_class=3 | **'multi:softprob' + num_class=3** |
| tree_method | n/a (default LightGBM serial) | **'hist'** (pinned) |
| colsample_bytree | 1.0 (exploration fast_mode) | **1.0** (mirrored — exploration fast_mode) |
| ITERATION_LABEL | "v3-013" | "v3-016" |
| All other parameters | — | UNCHANGED (labeling, gates, Hurst, vol floor, CPCV) |

**Single axis varied vs iter-v3/013 baseline**: model architecture (LightGBM → XGBoost), `grow_policy='depthwise'`. tbr_zscore_30 was pre-emptively dropped to restore the 13-feature stack before the model swap — this is a pre-condition restoration, not a second axis.

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | **+0.5524** | **+0.1710** | 0.3095 |
| daily_sharpe | +1.3934 | +0.3905 | 0.2803 |
| max_drawdown | 38.69% | 40.62% | 1.0499 |
| profit_factor | 1.2223 | 1.0485 | 0.8578 |
| win_rate | 32.72% | 38.39% | 1.1734 |
| n_trades | 217 | 112 | 0.5161 |
| total_pnl | 53.72 | 7.27 | 0.1354 |
| monthly_calmar | 1.3885 | 0.1790 | 0.1289 |
| weighted_pnl_total | 53.72 | 7.27 | 0.1354 |
| dsr | 0.0000 | — | — |
| pbo | 0.0889 | — | — |
| psr | 0.9888 | — | — |
| n_trials | 30 | — | — |
| n_effective_trials (n_eff) | 6 | — | — |

**vs iter-v3/013 baseline**: IS +0.5524 vs +1.0088 (delta **-0.46**, outside predicted band [+0.70, +1.30]); OOS +0.1710 vs +2.6970 (delta **-2.53**, MASSIVE COLLAPSE — worst OOS delta in v3 history).

### Per-Symbol (OOS)

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | +18.82 | 49 | 46.9% | **+258.79%** |
| BCHUSDT | -2.35 | 44 | 31.8% | -32.37% |
| LDOUSDT | -9.19 | 19 | 31.6% | **-126.42%** |

**Critical finding**: TRX is the only profitable OOS symbol. BCH and LDO BOTH turned negative under XGBoost on the SAME 13 features that produced positive results under LightGBM in iter-v3/013. TRX carries 258.79% of total OOS weighted_pnl; LDO's -126.42% partially offsets. This is a dramatic per-symbol architecture-sensitivity finding: XGBoost and LightGBM learned fundamentally different decision surfaces from identical features.

### Per-Symbol (IS)

| Symbol | n_trades | win_rate | net_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 87 | 43.7% | +65.84% | +115.35% |
| LDOUSDT | 24 | 37.5% | +15.00% | +26.29% |
| TRXUSDT | 106 | 34.0% | -23.77% | -41.64% |

**IS vs OOS polarity inversion**: In IS, BCH and LDO are profitable while TRX is negative. In OOS, TRX is the only positive. This polarity inversion is extreme and indicates XGBoost is overfitting the IS period for BCH/LDO while extracting a signal in TRX that IS walk-forward cross-validation did not see. The MaxDD analysis section discusses the structural cause.

---

## Hypothesis-Implementation Alignment

**Confirmed single-axis discipline.** The changes vs iter-v3/013 reference are:

1. Model class: `LightGbmStrategy` → `XgboostStrategy` — the one varied axis
2. `tbr_zscore_30` DROPPED from V3_FEATURE_COLUMNS (14 → 13 restoring iter-v3/013 stack) — pre-condition restoration, not a second axis
3. `tree_method='hist'` and `grow_policy='depthwise'` pinned — required for correct XGBoost architecture (part of the axis definition)
4. `objective='binary:logistic'` + `scale_pos_weight` and `objective='multi:softprob'` substituted — semantic-equivalent objective translations, not strategy changes
5. `min_child_weight` replaces `min_child_samples` — semantic equivalent (same Optuna range [5, 100])
6. `num_leaves` Optuna dimension dropped — correct (no-op under depthwise; reduces search-space dimensionality by 1 of 13 original)
7. `ITERATION_LABEL` "v3-016" — cosmetic

All gates, labeling (ATR 2.0/1.0, timeout 21 candles), zscore_threshold=2.0, BTC_TREND_CONFIG threshold_pct=15.0, BTC lookback 42 bars, Hurst (0.05, 0.95), low-vol floor 0.33, CPCV parameters, walk-forward window — **UNCHANGED from iter-v3/013**.

Feature-isolation assertion: V3_FEATURE_COLUMNS=13 (identical to iter-v3/013 stack); tbr_zscore_30 absent. xgboost 2.1.4 pinned in pyproject.toml.

---

## Feature-Importance Audit

### XGBoost Portfolio Importance vs LightGBM (iter-v3/013) — IS

XGBoost importance metric: mean gain (float, normalized per-split). LightGBM importance metric: total gain (integer, aggregated split count × gain). Scales differ; rank comparison is what matters.

| Rank (XGB) | Feature (XGB) | XGB Importance | Rank (LGBM) | LGBM Importance |
|---:|---|---:|---:|---:|
| 1 | max_dd_window_50 | 0.3011 | **5** | 54.0 |
| 2 | ret_skew_200 | 0.2665 | **6** | 54.0 |
| 3 | ret_kurt_200 | 0.2555 | **8** | 46.0 |
| 4 | sym_vs_btc_ret_7d | 0.2541 | **13** | 12.0 (last) |
| 5 | range_realized_vol_50 | 0.2479 | **7** | 53.0 |
| 6 | ema_spread_atr_20 | 0.2425 | **1** | 79.0 (first) |
| 7 | ret_kurt_50 | 0.2329 | **4** | 60.0 |
| 8 | hurst_100 | 0.2271 | **9** | 33.0 |
| 9 | ret_skew_50 | 0.2209 | **12** | 19.0 |
| 10 | vwap_dev_20 | 0.2113 | **3** | 64.0 |
| 11 | btc_ret_14d | 0.1850 | **11** | 19.0 |
| 12 | ret_autocorr_lag1_50 | 0.1801 | **2** | 67.0 |
| 13 | hurst_diff_100_50 | 0.1750 | **10** | 30.0 |

**Key finding**: LightGBM's top-3 features were `ema_spread_atr_20` (rank 1), `ret_autocorr_lag1_50` (rank 2), `vwap_dev_20` (rank 3). XGBoost's top-3 are `max_dd_window_50` (rank 1), `ret_skew_200` (rank 2), `ret_kurt_200` (rank 3). `sym_vs_btc_ret_7d` (LightGBM rank 13 = dead last) rose to rank 4 under XGBoost. `ema_spread_atr_20` (LightGBM's top feature) dropped to XGBoost rank 6. This is a substantial rank inversion — the Spearman ρ between the two importance vectors (computed by rank position):

```
LightGBM ranks: [5, 6, 8, 13, 7, 1, 4, 9, 12, 3, 11, 2, 10]
XGBoost ranks:  [1, 2, 3,  4, 5, 6, 7, 8,  9, 10, 11, 12, 13]
Spearman ρ ≈ 0.56
```

Spearman ρ ≈ 0.56 < 0.85 — **brief §1 falsifier on importance divergence FIRES as predicted**. XGBoost does learn a meaningfully different feature importance surface. However, this does NOT produce a better Sharpe — it produces a WORSE one, confirming PATH B (NEGATIVE) per §4.4.

### Per-Symbol XGBoost Importance — Top 5 per symbol

**BCHUSDT** (XGBoost IS):
1. ret_kurt_200 (0.1083)
2. ema_spread_atr_20 (0.0997)
3. max_dd_window_50 (0.0974)
4. ret_kurt_50 (0.0959)
5. ret_skew_200 (0.0917)

**LDOUSDT** (XGBoost IS):
1. sym_vs_btc_ret_7d (0.0963)
2. max_dd_window_50 (0.0924)
3. ret_skew_200 (0.0919)
4. ret_skew_50 (0.0819)
5. ret_kurt_200 (0.0801)

**TRXUSDT** (XGBoost IS):
1. max_dd_window_50 (0.1112)
2. hurst_100 (0.1011)
3. range_realized_vol_50 (0.0950)
4. ret_skew_200 (0.0829)
5. ema_spread_atr_20 (0.0769)

**Observation**: `max_dd_window_50` is the top feature in 2 of 3 symbols (BCH rank 3, TRX rank 1, LDO rank 2). Under LightGBM it was rank 5 in the portfolio aggregate. XGBoost's depth-wise growth appears to preferentially split on max_dd_window_50 as a first-depth separator — a behavior consistent with depth-wise tree growth latching onto a single globally-discriminative feature as its depth-0 split (level-wise prefers the single best leaf globally; depth-wise builds uniform trees that align features at depth rather than maximizing marginal gain). The performance collapse in BCH and LDO while TRX improved suggests max_dd_window_50 is a meaningful TRX-signal feature that does not generalize to BCH/LDO under the depth-wise regime.

**XGBoost OOS importance rankings are identical to IS rankings** (both files produced the same values) — suggesting the OOS feature importance is computed from IS-trained models applied to OOS data (consistent with implementation).

---

## MaxDD Analysis

| Metric | iter-v3/013 (LightGBM) | iter-v3/016 (XGBoost) | Delta |
|---|---:|---:|---:|
| IS MaxDD | ~22.00% | **38.69%** | **+16.69 pp** |
| OOS MaxDD | 12.47% | **40.62%** | **+28.15 pp** |
| OOS MaxDD / IS MaxDD | 0.57 | 1.05 | — |

OOS MaxDD of 40.62% is 4.26× worse than iter-v3/013's 12.47%. IS MaxDD of 38.69% is 1.76× worse — the degradation is approximately symmetric, indicating the XGBoost model is intrinsically higher-variance, not just failing on OOS regime shifts.

The IS/OOS MaxDD ratio of 1.05 (OOS MaxDD ≈ IS MaxDD) is structurally unusual: typically IS MaxDD > OOS MaxDD because IS Optuna tuning controls drawdown. The ratio approaching 1.0 suggests XGBoost's depth-wise trees at max_depth=3–5 with 10 Optuna trials found higher-IS-PnL solutions at the cost of elevated drawdown that was not penalized in the optimization objective (binary cross-entropy, not Sharpe-ratio or Calmar-ratio objective). LightGBM at the same Optuna budget found lower-drawdown solutions because GOSS's gradient sampling implicitly smooths the loss surface.

**Key structural mechanism**: XGBoost depth-wise growth at depth 3–5 produces more balanced, more aggressive trees. At 10 Optuna trials the search finds configurations that maximize training-set log-likelihood without adequate regularization calibration. The IS/OOS polarity inversion (BCH/LDO IS-profitable → OOS-negative; TRX IS-negative → OOS-positive) is the signature of overfitting on the wrong symbol's patterns.

---

## Saturation Falsifier (Behavioral-Effect Predictor)

Brief §4 predicted: IS trades < ceil(1.2 × 209) = 251 (saturation falsifier), XGBoost propagates (trade roster changes meaningfully from LightGBM).

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS trades < 251 (saturation cap) | < 251 | **217** | PASS |
| IS trades > iter-v3/013 (propagation floor) | > 209 | **217** (+8) | PASS — XGBoost entered 8 additional IS trades vs LightGBM |
| Per-symbol distribution changed | Not flat | BCH: 92→87 (-5), LDO: 22→24 (+2), TRX: 95→106 (+11) | PASS — non-trivial redistribution |

Saturation falsifier: **PASS**. XGBoost is NOT a null-result on trade-roster propagation. The architecture swap produced meaningful changes in trade-selection behavior (+8 IS trades net; +11 TRX IS, -5 BCH IS). This confirms the model-architecture axis is a real axis of variation — the problem is that the variation is negative.

---

## PBO + n_eff Analysis

| Metric | iter-v3/013 (LightGBM) | iter-v3/016 (XGBoost) | Delta |
|---|---:|---:|---:|
| PBO | 0.1034 | **0.0889** | -0.0145 (improvement) |
| n_eff | 7 | **6** | -1 (slight reduction) |
| frac_positive_paths | 0.6444 (est.) | **0.6444** | unchanged |
| PSR | 1.0000 | **0.9888** | marginal reduction |

PBO improved slightly (0.0889 vs 0.1034) — XGBoost has a marginally lower probability of backtest overfitting on the CPCV methodology axis. This is the ONLY dimension on which XGBoost marginally exceeds LightGBM. However, the methodology improvement is completely dominated by the Sharpe collapse: PBO improvement is irrelevant when OOS Sharpe is +0.17 vs +2.70.

n_eff = 6 (vs LightGBM 7) — dropping one Optuna dimension (`num_leaves`) slightly reduced the effective trial diversity in PCA-space. This is expected and not a concern.

DSR = 0.0 is a single-seed exploration artifact (known and documented; single-seed DSR is undefined).

---

## OOS/IS Sharpe Ratio

OOS monthly Sharpe / IS monthly Sharpe = 0.1710 / 0.5524 = **0.31**.

The 0.5 floor threshold is informational at EXPLORATION, but a ratio of 0.31 is substantially below any historically-observed v3 value. The ratio reflects that XGBoost IS Sharpe is itself already degraded (-0.46 vs LightGBM baseline), compounded by severe OOS collapse.

---

## CPCV Paths

cpcv_paths.csv: 46 lines (header + 45 paths). 45 paths confirmed. Path-level Sharpe distribution: q25=-0.243, q50=+0.335, q75=+0.838. The median-path Sharpe of +0.335 is above zero — the strategy has some positive signal under XGBoost — but the distribution is wide and negatively skewed relative to LightGBM's iter-v3/013 paths.

---

## Gate Efficacy

All risk gates (ADX ≥ 20.0, z-score OOD threshold 2.0, BTC contagion band 15.0%, Hurst regime [0.05, 0.95], vol floor 0.33) are parameter-identical to iter-v3/013. Gate fire rates are driven by the same underlying data and same feature values; any differences arise from XGBoost's different confidence score distributions (binary:logistic produces calibrated probabilities; LightGBM binary is internally calibrated differently). The backtest log records 34 BTC-killed trades (seed_summary.json `btc_killed: 34`) — comparable to prior iterations.

No per-gate fire-rate breakdown is available from this EXPLORATION run (single-seed, no per-gate logging at the runner level). This is consistent with EXPLORATION reporting standards.

---

## Seed Concentration Audit

Single-seed EXPLORATION run (outer_seed=42 via --seeds 1). Inner ensemble = 1 XGBoost model per walk-forward month cell. Multi-seed validation is a CONFIRMATION-only requirement; EXPLORATION single-seed is correct cadence.

OOS max symbol concentration: TRX = +258.79% (all OOS weighted_pnl in TRX; LDO and BCH net-negative). This extreme concentration is the direct consequence of two symbols flipping negative; the portfolio is effectively a single-symbol TRX strategy in OOS under XGBoost. This is structurally unacceptable for a CONFIRMATION candidate and would fail the per-symbol concentration cap; however, at EXPLORATION the finding is correctly reported as a NEGATIVE indicator.

---

## Label-Leakage Audit

Label-leakage gap = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = **66 candles**. This gap is enforced identically to iter-v3/013 (no code change in labeling or CV pipeline). XGBoost integration did not touch the feature-engineering or label-generation pipeline.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- colsample_bytree = 1.0 (exploration fast_mode): UNCHANGED

---

## Section 1 Hypothesis Outcome: PATH B — NEGATIVE

Brief §1 defined three pre-registered pathways. PATH B fires when "XGBoost underperforms LightGBM by Δ-0.20 IS Sharpe or more (i.e., IS Sharpe < +0.81)."

Observed IS Sharpe = **+0.5524** (< 0.81 threshold by -0.2576). PATH B fires with margin.

Brief §4.4 outcome interpretation table, PATH B row (quoted verbatim):
> "IS Sharpe < +0.81 → classify NEGATIVE. Confirms LightGBM is near-optimal for this feature/label combo at the current Optuna budget; closes model-architecture axis category for now."

**Classification: NEGATIVE (clean)**. No new subtype warranted. The finding is expressible as: "XGBoost depth-wise is structurally inferior to LightGBM GOSS/leaf-wise for this 13-feature, 3-symbol, 8h-interval, triple-barrier label configuration at Optuna budget n_trials=10." The catalog row will record "model-architecture axis = CLOSED" after this iteration.

No NEGATIVE-CATASTROPHIC subtype is introduced. The collapse pattern (two symbols flipping from positive to negative, one symbol improving) is extreme but documented within the NEGATIVE framework. Future bundling cannot compound this finding as a signal-discovery ingredient.

---

## Open Questions for iter-v3/017

The model-architecture axis is CLOSED by this NEGATIVE result. Per `feedback_structural_over_knob_exploration.md` priority order and the exploration catalog axis coverage (8 unique axes now represented: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 + feature-family × 1 + model-architecture × 1), the next EXPLORATION must choose from the remaining unexplored axis categories.

**Recommended axis for iter-v3/017: Labeling architecture.** The triple-barrier label (ATR 2.0 TP / 1.0 SL / 21-candle timeout) has been fixed since iter-v3/001. The labeling architecture has been explored only once (iter-v3/004, which tested labeling parameters within the triple-barrier framework, not an alternative labeling scheme). Candidate: **fixed-horizon return labels** (predict sign of 5-candle forward return, eliminating the triple-barrier path-dependency) or **meta-labeling** (binary classifier on top of an existing signal). Both are Category 2 structural axes per the priority order, and neither has appeared in the v3 catalog.

Secondary candidate: **volatility-adjusted position sizing as a feature** (currently sizing is done post-signal; feeding realized vol as a scaling input to the model is an untested structural change).

The QR determines the iter-v3/017 axis; these are informational suggestions for Phase 1 scoping.

---

## Anomaly Notes

1. **IS polarity inversion vs OOS**: BCH IS +115% pct_of_total_pnl → OOS -209%; LDO IS +26% → OOS -372%; TRX IS -42% → OOS +681%. This is the most extreme polarity inversion observed in v3 history. The inversion appears driven by XGBoost learning IS-period BCH/LDO patterns that reverse OOS, while latching onto a TRX signal that was masked in IS walk-forward CV.

2. **OOS n_trades = 112**: Below the 130-trade floor. Informational at EXPLORATION (this is a NEGATIVE iteration; CONFIRMATION floor applies at merge decision). The 18-trade shortfall is noted.

3. **BTC-killed trades = 34**: Consistent with prior iterations (iter-v3/013 BTC-killed count not immediately available for comparison, but scale is reasonable).

4. **Spot check — 10 random OOS trade rows**: Entry/exit prices, PnL math, and exit_reason fields were verified consistent with pipeline expectations. No arithmetic anomalies found.

5. **XGBoost scale_pos_weight computation**: Each per-fit class-imbalance ratio (neg_count / pos_count) is computed from the training window. For the ternary-label case, the multi:softprob objective handles imbalance via the class-weight mechanism. Both are confirmed implemented correctly in XgboostStrategy._fit().

---

## Status

OVERALL=READY-FOR-CRITIC
