# Iteration 003 Diary - 2026-03-25

## Merge Decision: NO-MERGE

OOS Sharpe worsened from -1.96 (baseline) to -2.17. Feature reduction did not improve the strategy. Marginal WR improvement (30.7→31.2%) insufficient to compensate.

## Hypothesis

Reducing features from 185 to top 40 by importance (~80% cumulative importance) will reduce noise and improve the model's discriminative ability, increasing win rate.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier TP=4%, SL=2%, timeout=4320min (unchanged)
- Symbols: 201 active USDT (unchanged)
- **Change**: Features reduced from 185 to top 40 (25 survived parquet intersection)
- Walk-forward: monthly, 12-month window, 5 CV, 50 Optuna trials
- Confidence threshold: Optuna 0.50–0.65 (unchanged)
- Seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value |
|--------|-------|
| Sharpe | -6.68 |
| Sortino | -8.12 |
| Max Drawdown | 51,035% |
| Win Rate | 30.0% |
| Profit Factor | 0.80 |
| Total Trades | 174,450 |
| Calmar Ratio | 1.00 |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -2.17 | -1.96 |
| Sortino | -2.99 | -2.58 |
| Max Drawdown | 6,415% | 5,079% |
| Win Rate | 31.2% | 30.7% |
| Profit Factor | 0.90 | 0.89 |
| Total Trades | 36,606 | 26,545 |
| Calmar Ratio | 0.78 | 0.76 |

## Overfitting Diagnostics

| Metric   | IS     | OOS    | Ratio (OOS/IS) | Assessment |
|----------|--------|--------|----------------|------------|
| Sharpe   | -6.68  | -2.17  | 0.32           | Below 0.5 |
| Sortino  | -8.12  | -2.99  | 0.37           | Below 0.5 |
| Win Rate | 30.0%  | 31.2%  | 1.04           | Stable |

## What Worked

- **Faster execution**: 25 features vs 185 → 2x faster training (~7000s vs ~17000s)
- **Marginal WR improvement**: 31.2% vs 30.7% — the top features may carry slightly more signal

## What Failed

- **OOS Sharpe worsened**: -2.17 vs -1.96. More trades at slightly better WR still produces a worse Sharpe.
- **Feature reduction was too aggressive**: Only 25 of 40 selected features survived the parquet intersection (15 features like vol_ad, vol_vwap, vol_obv were not in all parquet files). The top 3 most important features (vol_ad, vol_vwap, vol_obv) were lost.
- **Still below break-even**: 31.2% WR vs 34% needed. 2.8pp gap persists.

## Next Iteration Ideas

1. **Fix parquet intersection**: The top features (vol_ad, vol_vwap, vol_obv) were absent from some parquet files, removing the most important features. Regenerate parquet files to ensure all features are present, or use a union+NaN approach.
2. **Try regression**: The classification win rate is stuck at ~31%. Regression might provide better signal by predicting return magnitude.
3. **Lower TP/SL barriers**: Try TP=3%/SL=1.5% — more trades resolve via TP, potentially cleaner labels.
4. **Reduce symbol count**: Instead of 201 symbols, try top 50 by volume only. Liquid symbols may have cleaner dynamics.

## Lessons Learned

- Feature importance analysis must account for the parquet intersection — importance was measured on 185 features but the intersection reduced the available set to 106 (iter 002) or 25 (iter 003).
- Removing features doesn't help when the removed features were actually the most important ones (due to the intersection mismatch).
- The classification approach with 4%/2% barriers and 8h candles appears to have a fundamental signal ceiling around 30-31% WR. Incremental feature changes can't bridge the 3pp gap to break-even.
