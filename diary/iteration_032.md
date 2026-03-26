# Iteration 032 Diary - 2026-03-26 — EXPLOITATION
## Merge Decision: NO-MERGE
OOS Sharpe +0.29 < baseline +1.33. Higher threshold floor too restrictive.

## IS Deep Analysis (QR reading quantstats)
The IS loss (-246% total) comes from 3 specific quarters:
- 2021 Q1: -83% (cold start, only 12mo training)
- 2022 Q3: -80% (bear market bottom, model has never seen sustained bear)
- 2022 Q4: -56% (continued bear)

In 2022: LONGS had 27.6% WR — model went long 156 times in a -65% year.
The model doesn't know it's in a bear market. NO feature captures macro regime.

## Next: EXPLORATION — add macro regime features:
1. BTC drawdown from ATH (tells model if we're in a bear market)
2. Rolling 90-day return (trend direction at macro level)  
3. Volatility regime (current ATR vs 90-day median ATR)
These should be added to the feature pipeline and regenerated in parquet.
