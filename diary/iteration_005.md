# Iteration 005 Diary - 2026-03-25

## Merge Decision: NO-MERGE

OOS Sharpe collapsed from -1.91 to -5.96. Win rate dropped 32.9%→30.2%. Lower TP/SL barriers made everything worse.

## Hypothesis

Lowering TP/SL from 4%/2% to 3%/1.5% (same 2:1 RR) would produce cleaner labels with higher resolution (94% vs 87%), improving win rate past break-even.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Change**: TP=3%, SL=1.5% (from TP=4%, SL=2%)
- Symbols: Top 50 (unchanged)
- Features: 106 (unchanged)
- Walk-forward: monthly, 12-month, 5 CV, 50 trials, seed 42

## Results: Out-of-Sample

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -5.96 | -1.91 |
| Sortino | -7.27 | -2.80 |
| Max Drawdown | 2,828% | 997% |
| Win Rate | 30.2% | 32.9% |
| Profit Factor | 0.79 | 0.92 |
| Total Trades | 11,955 | 6,831 |
| Calmar Ratio | 0.97 | 0.77 |

## Overfitting Diagnostics

| Metric   | IS     | OOS    | Ratio (OOS/IS) |
|----------|--------|--------|----------------|
| Sharpe   | -5.95  | -5.96  | 1.00           |
| Win Rate | 28.6%  | 30.2%  | 1.06           |

IS/OOS ratio of 1.00 — no overfitting, consistently bad.

## What Failed

- **Win rate DROPPED 2.7pp**: 32.9% → 30.2%. Lower barriers did NOT produce better labels — they produced more trades on smaller, noisier price moves.
- **More trades, worse quality**: 11,955 OOS trades vs 6,831. The model traded more (lower barriers = more TP hits for the confidence threshold to pass through) but each trade was worse.
- **Sharpe 3x worse**: -5.96 vs -1.91. The combination of lower per-trade PnL (3% TP vs 4%) and lower WR (30.2% vs 32.9%) compounded the damage.

## Key Insight

The 4%/2% barriers are BETTER than 3%/1.5% for this model. Counter to intuition, the higher barriers produce a more predictable signal. The model can distinguish "will this move 4% in one direction before 2% against?" better than "will this move 3% vs 1.5%?". This likely because:
- 4% moves are associated with stronger, more identifiable market conditions (momentum, breakouts)
- 3% moves are too common and too noise-driven for the features to distinguish direction

## Next Iteration Ideas

1. **Add BTC regime filter**: Only trade in trending regimes. This was idea #2 from iter 004 diary. Still the most promising untried approach.
2. **Increase Optuna trials to 100**: With 50 trials, the search space may be underexplored.
3. **Try asymmetric barriers**: TP=5%/SL=2% (2.5:1 RR). Bigger moves may be even MORE predictable, requiring lower WR for break-even (~29%).

## Lessons Learned

- Lower TP/SL barriers do NOT automatically produce better labels. The higher barriers (4%/2%) capture more structured, momentum-driven moves that LightGBM can predict.
- Break-even WR depends on the ratio, but actual WR depends on barrier levels. At 3%/1.5% the model's WR dropped, even though break-even was the same.
- The 4%/2% barrier choice from the Phase 2 EDA was well-calibrated.
