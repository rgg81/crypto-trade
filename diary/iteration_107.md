# Iteration 107 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (Kelly sizing changes PnL magnitudes but not trade quality — same WR/PF)

**OOS cutoff**: 2025-03-24

## Results

| Metric | Iter 107 (Kelly) | Baseline (093) |
|--------|-----------------|----------------|
| IS Sharpe | +0.70 | +0.73 |
| OOS Sharpe | +1.18 | +1.01 |
| IS/OOS WR | 42.8%/42.1% | 42.8%/42.1% |
| IS/OOS PF | 1.19/1.25 | 1.19/1.25 |
| Trades | 346/107 | 346/107 |

Kelly sizing doesn't change which trades execute or their direction — only position sizes. WR, PF, and trade count are identical. The Sharpe difference comes from weighted PnL magnitudes.

## Key Insight
Half-Kelly reduces average position size from 100 to ~25-35. This reduces both gains and losses proportionally. Since the same trades occur, this is just capital efficiency scaling — not a strategy improvement. NO-MERGE because it doesn't improve the actual trading signal.

## Exploration/Exploitation Tracker
Last 10 (iters 098-107): [E, E, E, X, E, E, E, E, E, **E**]
Exploration rate: 9/10 = 90%. Type: EXPLORATION.

## Next: Meme coin research track (DOGE + 1000SHIB) per user request.
