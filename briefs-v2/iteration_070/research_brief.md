# iter-v2/070 Research Brief — BOLD feature addition

**Type**: EXPLORATION (new feature families, bold-idea quota)
**Parent baseline**: iter-v2/069 (MERGEd, OOS monthly +2.108, combined +2.982)
**Bold-idea quota**: satisfies the 1-per-3-iteration rule (iter-v2/067 brake
was bold but failed; iter-v2/068 z-score and iter-v2/069 prune were EXPLOITATION).

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable. New features built from
OHLCV data only, no OOS leakage.

## Category A — Feature Contribution Analysis (drives this iteration)

From QR Phase 1 EDA in iter-v2/068, the current 34-feature set has several
BOTTOM-rho features (near-zero predictive power on univariate
3-bar-forward Spearman):
- `parkinson_gk_ratio_20`: rho −0.0002
- `ret_skew_200`: rho −0.0004
- `sym_vs_btc_ret_7d`: rho −0.0005
- `hurst_200`: rho +0.0025

These are candidates for future removal. **iter-v2/070 ADDS instead of
removes** — keep pruning controlled, separate from feature addition, so
we can attribute effect.

**New features proposed**:

### 1. `liquidity_impact_20` (in `volume_micro.py`)

Formula: `rolling_mean_20(|close - open| × volume / (high - low + eps))
÷ rolling_mean_20(volume)`

Intuition: measures how much body-size (directional trade pressure)
weighted by volume exists relative to the bar range. High when trades
DRIVE directional moves; low when volume churns through indecision
(large wicks, small body). Scale-invariant via range-normalization and
volume denominator.

Category A validation (IS-only, pooled 4 symbols):
- Correlation with existing features: max 0.79 with `parkinson_gk_ratio_20`
  (below 0.85 duplicate threshold)
- Univariate fwd-ret rho: +0.019 (mid-pack)
- Stationary by construction (ratio of same-units quantities)

### 2. `return_zscore_20` (in `tail_risk.py`)

Formula: `(log_return_t − rolling_mean_20(log_return)) ÷ rolling_std_20(log_return)`

Intuition: z-score of most recent 1-bar log return against its own
20-bar distribution. Captures "how unusual is right now vs recent".
Different family from `atr_pct_rank_*` (those are volatility ranks, this
is return ranks with sign).

Category A validation:
- Correlation with existing features: max 0.27 with `vwap_dev_20`
- **Univariate fwd-ret rho: −0.027** (2nd strongest after
  `fracdiff_logclose_d04` at −0.073)
- Stationary by construction (z-score)

## Category G — Stationarity Analysis

Both new features stationary by construction:
- `liquidity_impact_20` is a volume-normalized ratio
- `return_zscore_20` is a rolling z-score (zero mean, unit std)

No drift concerns.

## Category I — Risk Management Design

Gates unchanged from iter-v2/069. The new features are ADDITIONAL
model inputs; the risk layer operates downstream of the model's signal
and doesn't need retuning for new features (z-score OOD gate will
automatically include the 2 new features in its OOD check).

### 6.3 Pre-registered failure-mode prediction

**Most likely failure**: adding 2 features dilutes `colsample_bytree`
(each tree picks same % of columns, now from a larger pool). If the new
features are NOT useful, the model sees more noise per tree → OOS
regression.

**Failure signature**: if OOS monthly Sharpe < +1.79 (0.85 × 2.108),
NO-MERGE. The model found no edge in the new features.

**Success signature**: OOS monthly ≥ +2.108 (baseline), ideally
improved. At least one of the new features appears in top-15 feature
importance.

## 3. Config

Single change to `V2_FEATURE_COLUMNS`: append 2 new strings
(`liquidity_impact_20`, `return_zscore_20`). Total 34 → 36.

New code in:
- `src/crypto_trade/features_v2/volume_micro.py` (liquidity_impact_20)
- `src/crypto_trade/features_v2/tail_risk.py` (return_zscore_20)

All other config identical to iter-v2/069 baseline.

## 4. MERGE criteria

| # | Criterion | Target |
|---|---|---|
| 1 | Combined monthly | ≥ 2.98 (iter-v2/069 baseline) |
| 2 | OOS monthly | ≥ 0.85 × 2.108 = 1.79 |
| 3 | IS monthly | ≥ 0.85 × 0.874 = 0.74 |
| 4 | OOS MaxDD | ≤ 1.2 × 18.80% = 22.6% |
| 5 | PF>1, trades≥50, SR>0 | — |
| 6 | Concentration ≤ 50% (outer) | — |
| 7 | Concentration ≤ 40% inner (n=4) | — |

## 5. Expected runtime

~2.5h single seed. Same 4 baseline symbols + BTC. Pre-flight mandatory
(runner now hard-fails on stale data per iter-v2/069 infrastructure).
