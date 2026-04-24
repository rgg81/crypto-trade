# Iteration 190 — xbtc feature swap (rejected, worse than augment)

**Date**: 2026-04-22
**Type**: EXPLORATION
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

Swapping 7 lowest-MDI baseline features for 7 xbtc features is WORSE
than iter 189's augmentation. IS Sharpe crashed to +0.42, OOS Sharpe
fell below the 1.0 floor (+0.99). xbtc cross-asset features do not
work for LINK at the 8h timeframe, under either approach.

## Comparison

| config | IS Sharpe | OOS Sharpe | IS PnL |
|--------|----------:|-----------:|-------:|
| v0.186 (no xbtc) | **+1.011** | **+1.440** | +128.37% |
| iter 189 augment (200f) | +0.683 | +1.660 | +86.53% |
| iter 190 swap (193f) | **+0.423** | +0.993 | +48.10% |

Both xbtc variants fail the IS > 1.0 floor. The swap is the worst.

## Why the swap was worse than expected

MDI = 0 does NOT mean the feature is useless. LightGBM with modest
`colsample_bytree` picks features through co-optimization over many
Optuna trials — a feature with MDI=0 in a single fit might still
influence which *other* features get picked.

Removing 7 of these features changed the feature-interaction landscape.
Optuna's monthly re-optimization settled on different hyperparameters,
which on LINK's already-marginal 22 samples/feature ratio, pushed
performance down significantly.

This reinforces the skill's warning: "For mature co-optimized models
(100+ features, Optuna-tuned over many iterations): Explicit pruning
destroys co-optimization."

## Three hypotheses for why xbtc doesn't help LINK

1. **Collinearity**: LINK's own features already encode BTC co-movement
   (daily correlation 0.52). Adding explicit BTC features is redundant.
2. **Wrong anchor**: LINK may correlate more with ETH than BTC. An xeth
   feature set could test this.
3. **Feature dilution**: On a 22-samples/feature ratio model, any
   feature swap disturbs hyperparameters enough to degrade.

## What this exploration DID teach us

1. Cross-asset features from BTC don't work for LINK.
2. `mr_rsi_extreme_14` / `stat_return_1` / `mom_rsi_7` etc. look
   low-importance in isolation but aren't safe to remove.
3. The feature set for LINK is at its effective limit with 193 columns
   on 4400 bars — can't add OR swap without degrading IS Sharpe.

## Exploration/Exploitation Tracker

Window (180-190): [E, X, E, X, X, X, X, X, X, E, **E**] → **4E/7X**.
Two real exploration iters this session (189 xbtc augment + 190 swap).

## Next Iteration Ideas

- **Iter 191**: Pivot to **new in-house features** (not cross-asset).
  Fractional differentiation features per AFML Ch. 5 — find minimum-d
  differentiated price/volume series that are stationary but retain
  memory. Add one at a time via displacement.
- **Iter 192**: Test xbtc on DOT (not LINK). DOT's 2022 regime failure
  might be the regime where cross-asset signal actually matters.
- **Iter 193**: xeth cross-asset features (reimplement cross_asset.py
  to accept any anchor symbol). LINK-ETH correlation was 0.69 in
  iter 183 EDA — potentially a stronger signal than BTC.
