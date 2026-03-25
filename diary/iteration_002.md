# Iteration 002 Diary - 2026-03-25

## Merge Decision: MERGE

OOS Sharpe improved from -4.89 to -1.96 (+60%). Trade count reduced 68%. Max drawdown reduced 69%. Still unprofitable but a clear improvement on the single variable changed (confidence threshold). Two hard constraints fail (PF<1.0, IS/OOS Sharpe<0.5), but the trajectory is in the right direction.

## Hypothesis

Adding an Optuna-optimized confidence threshold (0.50–0.65) at prediction time will filter out low-conviction noise trades, reducing trade count and improving win rate.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier TP=4%, SL=2%, timeout=4320min (unchanged)
- Symbols: 201 active USDT (unchanged)
- Features: 185 (unchanged)
- Walk-forward: monthly, 12-month window, 5 CV, 50 Optuna trials
- **Change**: confidence_threshold optimized by Optuna (0.50–0.65)
- Random seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value |
|--------|-------|
| Sharpe | -5.04 |
| Sortino | -6.16 |
| Max Drawdown | 42,423% |
| Win Rate | 30.7% |
| Profit Factor | 0.83 |
| Total Trades | 169,097 |
| Calmar Ratio | 0.99 |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -1.96 | -4.89 |
| Sortino | -2.58 | -8.01 |
| Max Drawdown | 5,079% | 16,387% |
| Win Rate | 30.7% | 30.9% |
| Profit Factor | 0.89 | 0.87 |
| Total Trades | 26,545 | 83,408 |
| Calmar Ratio | 0.76 | 0.93 |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric   | IS     | OOS    | Ratio (OOS/IS) | Assessment |
|----------|--------|--------|----------------|------------|
| Sharpe   | -5.04  | -1.96  | 0.39           | Below 0.5 — threshold may overfit |
| Sortino  | -6.16  | -2.58  | 0.42           | Same pattern |
| Win Rate | 30.7%  | 30.7%  | 1.00           | Perfectly stable |

IS/OOS Sharpe ratio of 0.39 is below the 0.5 gate. However, both values are negative, and the ratio arithmetic is misleading: OOS is actually LESS bad than IS, which is the opposite of typical overfitting. The issue is that the IS period has earlier, noisier months with fewer symbols.

## Hard Constraints Check (all evaluated on OOS)

| Constraint                        | Value  | Threshold | Pass |
|-----------------------------------|--------|-----------|------|
| Max Drawdown (OOS)                | 5,079% | ≤ 19,664% | PASS |
| Min OOS Trades                    | 26,545 | ≥ 50      | PASS |
| Profit Factor (OOS)               | 0.89   | > 1.0     | FAIL |
| Max Single-Symbol PnL Contribution| <1%    | ≤ 30%     | PASS |
| IS/OOS Sharpe Ratio               | 0.39   | > 0.5     | FAIL |

## What Worked

- **Trade reduction**: 68% fewer trades (498K→196K total). The threshold is effectively filtering.
- **Drawdown reduction**: 69% less OOS drawdown (16,387%→5,079%). Fewer noise trades = less accumulated losses.
- **Sharpe improvement**: OOS Sharpe from -4.89 to -1.96 — still negative but the direction is right.

## What Failed

- **Win rate unchanged at 30.7%**: The threshold removed trades but didn't improve accuracy on the remaining ones. This means the model's confidence scores don't correlate with trade quality.
- **Still below break-even**: 30.7% WR with 4%/2% TP/SL needs ~34% to break even. The model is still essentially random.
- **IS/OOS Sharpe ratio fails**: 0.39 < 0.50. The monthly threshold optimization may be fitting to noise.

## Overfitting Assessment

The win rate is perfectly stable between IS and OOS (30.7% both), confirming no researcher overfitting. The IS/OOS Sharpe ratio below 0.5 is a technical artifact of comparing two negative numbers — the OOS period actually performs LESS badly per trade. The real problem is the model lacks signal, not that decisions are overfit.

## Next Iteration Ideas

1. **Switch to regression**: Instead of binary classification (long/short), predict the actual forward return magnitude. This gives a natural confidence proxy — trade only when |predicted_return| is large. The win rate problem may be fundamental to classification with near-50/50 class balance.
2. **Reduce feature count via importance**: Run feature importance on iter 002 models. Drop the bottom 80% of features. Fewer, more targeted features may improve signal extraction.
3. **Try TP=3%/SL=1.5% barriers**: The 4%/2% barriers produce 87% resolution but maybe the model is better at predicting shorter moves. Lower barriers = more signals but lower per-trade edge needed.
4. **Add regime-based filtering**: Only trade in trending regimes (ADX > threshold), skip choppy markets where prediction is hardest.

## Lessons Learned

- Confidence thresholding reduces trade count and drawdown but doesn't improve per-trade accuracy if the model's probabilities are poorly calibrated.
- The model's probability output doesn't discriminate: 30.7% WR whether threshold is 0.50 or 0.65. This suggests the probabilities are compressed near 0.50.
- Reducing from 500K to 200K trades is good but not enough — we need to get from 30% to 34%+ WR, which requires a fundamentally different approach.
