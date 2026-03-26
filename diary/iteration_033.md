# Iteration 033 Diary - 2026-03-26 — EXPLORATION

## Merge Decision: NO-MERGE
OOS Sharpe +0.62 < baseline +1.33. IS worsened -0.96 → -1.77. Macro features hurt.

## Type: EXPLORATION (new feature generation — macro regime)

## Results
| Metric | Value | Baseline |
|--------|-------|----------|
| OOS Sharpe | +0.62 | +1.33 |
| OOS WR | 38.7% | 41.6% |
| IS Sharpe | -1.77 | -0.96 |

## What Worked
- Feature pipeline regeneration works correctly (198 features from 185+13)
- Fixed _discover_feature_columns to scan only backtest symbols (critical fix!)
- Macro features are well-computed and capture genuine market context

## What Failed
- 13 new features at once = too many. Curse of dimensionality — more features with same training data → overfitting.
- IS got WORSE (-1.77 vs -0.96) despite macro features designed to help 2021-2022.
- The model may be using macro features to overfit to specific periods rather than learning generalizable patterns.

## IS Quantstats Analysis
2021 Q1: -83% (unchanged — macro features don't help cold-start, model lacks training data)
2022 Q3: -80% (macro features may have actually HURT here by adding noise)

## Next Iteration Ideas
1. **Add ONLY 2-3 key macro features**: macro_dd_from_ath_all + macro_return_90d only. Simpler.
2. **Regenerate features with 3x lookback multiplier**: Instead of adding NEW features, make EXISTING features operate at daily timescale (e.g., SMA_300 instead of SMA_100).
3. **Feature selection**: Use permutation importance to select top 50 features from the 198. Remove noise.

## Exploration/Exploitation Tracker
Last 10: [E, E, E, X, E, E, E, X, X, **E**] → 7/10 = 70% exploration
