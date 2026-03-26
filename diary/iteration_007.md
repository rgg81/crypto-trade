# Iteration 007 Diary - 2026-03-26

## Merge Decision: NO-MERGE

OOS Sharpe worsened -1.91→-3.21. WR dropped 32.9%→28.0%. Asymmetric barriers hurt — the model is worse at predicting larger moves.

## Hypothesis

Asymmetric barriers TP=5%/SL=2% (break-even 28.6%) would enable profitability since the model's existing 32.9% WR exceeds 28.6%. Based on deep analysis showing TP rate (31.6%) as the real bottleneck, not headline WR.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Change**: TP=5%/SL=2% (from 4%/2%)
- Symbols: Top 50, all 106 features, 50 Optuna trials, seed 42

## Results: Out-of-Sample

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -3.21 | -1.91 |
| Max Drawdown | 1,596% | 997% |
| Win Rate | 28.0% | 32.9% |
| Profit Factor | 0.88 | 0.92 |
| Total Trades | 8,898 | 6,831 |

## Overfitting Diagnostics

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | -3.91 | -3.21 | 0.82 |
| WR | 27.0% | 28.0% | 1.04 |

IS/OOS ratio of 0.82 — best ever. No overfitting, consistently bad.

## Deep Analysis Findings (from Phase 1 of this iteration)

1. **The real TP rate gap is 3.4pp, not 1.1pp**: WR (32.9%) was misleading because it includes tiny timeout wins. Actual TP rate was 31.6% vs 33.3% break-even.
2. **Monthly trade variance is extreme** (99 to 1,766): Trade count correlates -0.85 with monthly PnL.
3. **The model IS profitable on select symbols**: Top 11 symbols have 38.1% WR and +174.1% total PnL in OOS.
4. **BTC is extraordinary**: 50.6% WR (87 trades).
5. **Changing barriers affects WR non-linearly**: 3%/1.5% gave 30.2% WR, 4%/2% gave 32.9%, 5%/2% gave 28.0%. The 4%/2% sweet spot is NOT just about the ratio — the absolute level matters.

## What Failed

- **WR collapsed from 32.9% to 28.0%**: 5% TP moves are fundamentally harder to predict. The model can't distinguish direction at this magnitude.
- **The math was wrong**: I assumed WR would stay ~32.9% with wider TP. It didn't — WR dropped below the new break-even (28.6%).
- **More trades (8,898 vs 6,831)**: With 5% TP, the confidence threshold was lower → more noise trades passed.

## Next Iteration Ideas (from deep analysis)

1. **Train per-symbol models for BTC/ETH**: BTC has 50.6% OOS WR, ETH 39.2%. These two alone could be profitable with dedicated models using all features focused on their specific dynamics. The pooled model dilutes their signal.
2. **Fixed confidence threshold 0.60**: Instead of Optuna optimization, fix at 0.60. The monthly trade variance (99-1766) shows Optuna picks bad thresholds some months. A fixed high threshold forces consistent selectivity.
3. **Add a "don't trade" class**: Instead of binary long/short, add a third label "neutral" for candles where neither TP nor SL is reached or the move is ambiguous. This lets the model learn WHEN to trade, not just which direction.
4. **Ensemble with BTC regime**: Use BTC ADX/NATR to define a regime indicator feature that's fed to the model. The model itself decides when to trade rather than an external filter.

## lgbm.py Code Review

After reviewing the codebase across 7 iterations, the following improvements should be considered:
- The `_discover_feature_columns` intersection across ALL parquet files is too aggressive — some symbols missing features causes good features to be dropped. A union with NaN (handled natively by LightGBM) would be better.
- The `_sync_label_params` in backtest.py still uses hardcoded defaults for detection — fragile if defaults change.
- The monthly walk-forward retrains from scratch every month — adding warm-starting or caching could cut runtime significantly.

## Lessons Learned

- Barrier levels are NOT independent of WR. The model has a SWEET SPOT at 4%/2% for 8h candles. This is a fundamental property of the data, not a hyperparameter to freely tune.
- The barrier sweep results: 3%/1.5% → 30.2% WR, 4%/2% → 32.9% WR, 5%/2% → 28.0% WR. The 4%/2% level captures the right magnitude of momentum moves on 8h crypto candles.
- Deep analysis should come BEFORE iterations, not after 6 failed attempts. The TP rate vs WR distinction would have prevented several wasted iterations.
