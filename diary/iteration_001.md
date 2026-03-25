# Iteration 001 Diary - 2026-03-25

## Merge Decision: MERGE (first iteration — becomes initial baseline)

This is iteration 001. Per the plan, the first iteration always merges to main to establish the initial baseline, regardless of absolute performance. The results are clearly unprofitable, which is expected — this iteration establishes the measurement framework and identifies the primary issues to address.

## Hypothesis

A LightGBM binary classifier trained on 185 technical features via monthly walk-forward can predict 8h candle direction (long vs short) profitably across 201 crypto symbols, using TP=4%/SL=2% barriers with 3-day timeout.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier TP=4%, SL=2%, timeout=4320min (3 days), fee-aware returns
- Symbols: 201 active USDT symbols (pooled model)
- Features: 185 (all groups, no selection by Optuna)
- Walk-forward: monthly retraining, 5 CV folds, 12-month minimum training window
- Optuna: 50 trials/month, optimizes training_days + LightGBM hyperparams only
- Random seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value |
|--------|-------|
| Sharpe | -8.55 |
| Sortino | -11.94 |
| Max Drawdown | 117,381% |
| Win Rate | 30.2% |
| Profit Factor | 0.80 |
| Total Trades | 415,268 |
| Calmar Ratio | 1.00 |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -4.89 | (first baseline) |
| Sortino | -8.01 | (first baseline) |
| Max Drawdown | 16,387% | (first baseline) |
| Win Rate | 30.9% | (first baseline) |
| Profit Factor | 0.87 | (first baseline) |
| Total Trades | 83,408 | (first baseline) |
| Calmar Ratio | 0.93 | (first baseline) |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS     | OOS    | Ratio (OOS/IS) | Assessment |
|----------|--------|--------|----------------|------------|
| Sharpe   | -8.55  | -4.89  | 0.57           | OOS degrades less — both terrible |
| Sortino  | -11.94 | -8.01  | 0.67           | Same pattern |
| Win Rate | 30.2%  | 30.9%  | 1.02           | Stable (consistently bad) |

The OOS/IS Sharpe ratio of 0.57 technically passes the >0.5 gate, but this is meaningless when both values are deeply negative. There is no researcher overfitting — the strategy is uniformly bad across all periods.

## Hard Constraints Check (all evaluated on OOS)

| Constraint                        | Value   | Threshold | Pass |
|-----------------------------------|---------|-----------|------|
| Max Drawdown (OOS)                | 16,387% | ≤ TBD     | (first baseline) |
| Min OOS Trades                    | 83,408  | ≥ 50      | PASS |
| Profit Factor (OOS)               | 0.87    | > 1.0     | FAIL |
| Max Single-Symbol PnL Contribution| <1%     | ≤ 30%     | PASS |
| IS/OOS Sharpe Ratio               | 0.57    | > 0.5     | PASS |

## Per-Regime Performance (OOS)

All trades tagged as "unknown" due to a bug in the regime lookup (trade open_time doesn't align with candle open_time for BTC regime mapping). To fix in iteration 002.

## What Worked

- **Infrastructure is functional**: Walk-forward, labeling, Optuna, report splitting all work end-to-end
- **Fee-aware labeling**: Returns and weights now properly account for trading costs
- **Simplified optimization**: Removing feature/threshold selection reduced Optuna search space, each trial runs faster
- **OOS/IS stability**: Win rate is remarkably stable between IS (30.2%) and OOS (30.9%), showing no researcher overfitting

## What Failed

- **Trading every candle**: Without any confidence filter, the model places 498K trades — one per symbol per candle. Most are noise. This is the #1 problem.
- **30% win rate**: With 2:1 RR, need ~34% WR to break even. The model barely beats random (which would be ~33% given the label distribution of ~32% long TP, ~34% short TP).
- **185 features on all symbols**: The feature space is too large relative to signal strength. Many features are noise for a pooled cross-asset model.
- **Negative Sharpe in CV**: The Optuna best Sharpe values during training were already slightly negative (-0.03 to -0.13), indicating the model couldn't find profitable patterns even in-sample.

## Overfitting Assessment

There is no overfitting — the strategy is unprofitable in both IS and OOS periods with nearly identical win rates. The problem is not that the researcher's choices don't generalize; the problem is that a pooled LightGBM on 185 features with no trade filtering cannot predict 8h candle direction better than chance.

## Next Iteration Ideas

1. **Re-introduce a confidence threshold or trade filter**: The model should NOT trade when it has no edge. Either re-add a confidence threshold (e.g., skip when max(P) < 0.55) or add a volatility/regime filter so the model only trades in conditions where signals are clearer.
2. **Reduce feature set**: Run feature importance analysis on this iteration's models. Drop features that contribute nothing. Fewer, more predictive features should improve generalization.
3. **Try regression instead of classification**: Instead of predicting direction, predict the actual forward return. Use the predicted magnitude as a confidence proxy — only trade when |predicted_return| > threshold.
4. **Fix regime tagging**: The per-regime report shows "unknown" for all trades. The regime lookup needs to match trade open_time to BTC candle open_time properly.
5. **Consider symbol-tier models**: Top 30 by volume vs rest may have different dynamics. A model trained only on liquid symbols might perform better.

## Lessons Learned

- A model that trades every candle with no selectivity will be killed by fees. Even at 0.1% per trade, 498K trades × 0.1% = 498% in fees alone.
- Win rate is the bottleneck. With fixed TP/SL, the model needs to be right at least 1/3 of the time. At 30%, it's losing the fee drag.
- The simplified Optuna (no feature selection, no threshold) is faster but produced worse results than needed. Some form of feature importance or trade filtering is necessary.
- The walk-forward infrastructure works correctly at scale (201 symbols, 62 months, 15K model fits). This is a solid foundation.
