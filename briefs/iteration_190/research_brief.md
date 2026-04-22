# Iteration 190 — xbtc feature swap (rejected)

**Date**: 2026-04-22
**Type**: EXPLORATION (follow-up to iter 189's augmentation failure)
**Baseline**: v0.186
**Decision**: NO-MERGE

## Motivation

Iter 189 showed augmenting LINK's features with 7 xbtc features (193 → 200)
broke the samples/feature ratio and collapsed IS Sharpe. This iteration
tests whether **replacing** 7 low-MDI features with xbtc features
(keeping feature count at 193) preserves IS performance while adding
cross-asset signal.

## Method

### Feature-importance step

`analysis/iteration_190/feature_importance.py` trains a single LightGBM
on LINK IS data (2022-01 to 2025-03-24) using BASELINE_FEATURE_COLUMNS.
Extracts `feature_importances_`. Identified 7 features with MDI = 0
(never used for a split decision by LightGBM on LINK):

```
cal_hour_norm, mom_rsi_7, mr_rsi_extreme_21, mr_rsi_extreme_14,
mr_dist_sma_10, stat_return_1, stat_log_return_10
```

3 of these 7 (`stat_return_1`, `mr_rsi_extreme_14`, `mr_rsi_extreme_21`)
are also in the R3 OOD feature subset — but they stay in the parquet
and remain available for OOD distance computation. Only the LightGBM
input drops them.

### Swap

`run_iteration_190_link_swap.py` builds a 193-feature list:
`BASELINE_FEATURE_COLUMNS − DROP + XBTC_FEATURE_COLUMNS`. Samples/feature
ratio unchanged at 22.

## Result

| metric | v0.186 LINK | iter 189 (augment 200f) | **iter 190 (swap 193f)** |
|--------|------------:|-------------------------:|-------------------------:|
| IS Sharpe | +1.011 | +0.683 | **+0.423** |
| OOS Sharpe | +1.440 | +1.660 | +0.993 |
| IS trades | 134 | 146 | 150 |
| OOS trades | 40 | 39 | 35 |
| IS MaxDD | — | 30.46% | 53.56% |
| OOS MaxDD | — | 12.68% | 17.00% |
| IS PnL | +128.37% | +86.53% | +48.10% |
| OOS PnL | +49.19% | +54.39% | +33.63% |

**Swap is worse than augmentation.** Both fail the IS > 1.0 floor.
OOS Sharpe also falls below 1.0 for the swap. IS PnL collapsed to
+48% (from baseline's +128%).

## Why swap is worse than augment

Counter-intuitive but explainable: the "lowest MDI" features may still
have **indirect information value** through feature interactions. LightGBM
with only 300 estimators and a modest `colsample_bytree` doesn't always
pick high-IV features directly; it finds them through interactions. MDI=0
means the feature was never chosen AS A SPLIT but doesn't rule out its
*availability* mattering.

Removing these 7 features changed the feature-interaction landscape
during Optuna retuning per month, producing materially different
(and worse) optimized hyperparameters.

## xbtc features do not help LINK

Across three configurations:
1. No xbtc (v0.186 baseline): IS +1.01, OOS +1.44 (good)
2. Add 7 xbtc (iter 189): IS +0.68, OOS +1.66
3. Swap 7 xbtc (iter 190): IS +0.42, OOS +0.99

xbtc features are consistently harmful to LINK's IS Sharpe. Possible causes:

1. **Collinearity**: LINK's daily returns correlate 0.52 with BTC's. The
   existing LINK features (normalized returns, RSI, natr) already encode
   most of the BTC-comovement. Adding explicit BTC features introduces
   redundancy without new signal.
2. **Wrong cross-asset target**: LINK may correlate more with ETH than
   BTC. A future iter could test `xeth_*` features.
3. **Optuna sensitivity**: LINK's existing feature set was iteratively
   tuned; disturbing the feature set forces Optuna to re-optimize in a
   different landscape, often settling on worse local optima.

## Decision

NO-MERGE. xbtc features are parked. The 7 feature columns remain in the
parquet files (future iterations can still access them), but no model
currently uses them.

## Next Iteration Ideas

- **Iter 191**: **New in-house features** (not cross-asset). Review
  iter 089/094/117 notes for failed feature ideas worth revisiting.
  Candidates: rolling skewness of normalized returns, lead-lag volume
  ratios, compressed volatility oscillators (fractional differentiation
  from AFML Ch. 5). Target: propose 3-5 candidates, add ONE at a time,
  displacing a low-MDI baseline feature. Same 193 count.
- **Iter 192**: Explore whether xbtc features might help **DOT** (not
  LINK). DOT had 2022 regime failure that R1+R2 patched; cross-asset
  signal might anticipate the regime shift. Quick standalone test.
- **Iter 193**: xeth cross-asset features. Reimplement `cross_asset.py`
  to accept any anchor symbol. Test LINK with xeth instead of xbtc.
