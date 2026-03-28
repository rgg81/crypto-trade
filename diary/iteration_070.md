# Iteration 070 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2025 PnL -1.4% (WR 36.8%, 95 trades). OOS Sharpe +0.54 vs baseline +1.84.

**OOS cutoff**: 2025-03-24

## Hypothesis

Add 13 new features (6 interaction + 7 BTC cross-asset) to the existing 106. First feature engineering in 70 iterations.

## Results

| Metric | Iter 070 | Baseline (068) | Change |
|--------|----------|----------------|--------|
| IS Sharpe | +1.09 | +1.22 | -10.7% |
| IS MaxDD | 70.6% | 45.9% | +24.7pp |
| OOS Sharpe | +0.54 | +1.84 | -70.7% |
| OOS MaxDD | 30.4% | 42.6% | -12.2pp |
| OOS Trades | 75 | 87 | -13.8% |
| OOS PF | 1.14 | 1.62 | -29.6% |
| OOS/IS | 0.49 | 1.50 | - |

## What Happened

### The new features made things worse

Adding 13 features (106→113) degraded performance across almost every metric. IS MaxDD went from 45.9% to 70.6%, IS Sharpe dropped 11%, OOS Sharpe collapsed by 71%.

### Likely causes

1. **Curse of dimensionality**: 113 features with ~4400 training samples = high feature/sample ratio. LightGBM overfits to noise in the extra dimensions.
2. **Cross-asset features are redundant for BTC**: For BTC, the xbtc_ features are identical to existing features (just different column names). This doubles feature importance for BTC-specific indicators.
3. **Interaction features may not add information**: Products of indicators are monotonic transforms — LightGBM can already capture these relationships through tree splits.

## Exploration/Exploitation Tracker

Last 10 (iters 061-070): [X, X, E, X, E, X, E, E, X, E]
Exploration rate: 5/10 = 50%
Type: EXPLORATION (feature engineering)

## Lessons Learned

1. **More features != better with small sample sizes.** 4400 samples / 113 features ≈ 39 samples per feature — too low. LightGBM's regularization can't fully compensate.
2. **Feature selection before feature addition.** Should have pruned low-importance existing features first (permutation importance), then added new ones to keep total count similar.
3. **Cross-asset features need careful implementation.** Duplicating BTC features for BTC itself adds noise. Should only add xbtc_ features to non-BTC symbols.

## Next Iteration Ideas

1. **EXPLOITATION: Revert to 106 features** — The baseline feature set is proven. Don't change what works.
2. **EXPLORATION: Feature pruning** — Use permutation importance to remove the ~30 least important features, then add interaction/cross-asset features to maintain ~106 total.
3. **EXPLORATION: Add more symbols (SOL, DOGE)** — Would increase training data per month, making additional features more viable.
4. **EXPLORATION: Calendar features** — Day of week, hour of day (0/8/16 UTC). Only 2-3 features, minimal dimensionality increase.
