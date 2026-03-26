# Iteration 036 Diary - 2026-03-26 — EXPLOITATION
## Merge Decision: NO-MERGE
OOS +0.11 < baseline +1.33. More features (185 vs 106) made things WORSE.

## CRITICAL FINDING
The feature intersection across ALL 760 parquets was acting as NATURAL FEATURE SELECTION. Features that survive across all symbols are the most universal and robust. The 106 features from the global intersection are BETTER than the 185 from BTC+ETH only.

DO NOT merge the symbol-scoped discovery fix. The "bug" is a feature.

## Exploration/Exploitation Tracker
Last 10: [E, X, E, E, E, X, X, E, E, **X**] → 6/10 = 60%

## Next Ideas
1. Revert to 106 features (main branch behavior) for ALL future iterations
2. Try feature SELECTION from the 106: use top 50-60 by importance
3. Generate SLOW features (3x lookback) via parquet regeneration for ALL symbols
