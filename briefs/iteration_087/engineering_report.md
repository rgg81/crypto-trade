# Iteration 087 Engineering Report — Ternary + Relaxed Threshold

**Date**: 2026-03-30
**Runtime**: 10,314s (~172 min)

## Configuration

- **Ternary labeling**: neutral_threshold_pct=2.0% (timeout candles with |return| < 2% → neutral)
- **Relaxed threshold**: Optuna range [0.34, 0.60] (was [0.50, 0.85])
- **Features**: 115 (global intersection)
- **Model**: LGBMClassifier multiclass (3-class: short/neutral/long), ensemble seeds [42, 123, 789]
- **Everything else**: Same as baseline (24mo window, 5 CV, 50 trials, ATR barriers, cooldown=2)

## Results

| Metric | IS (087) | IS (baseline) | OOS (087) | OOS (baseline) |
|--------|----------|---------------|-----------|----------------|
| Sharpe | +0.83 | +1.22 | +0.57 | +1.84 |
| WR | 42.4% | 43.4% | 40.0% | 44.8% |
| PF | 1.19 | 1.35 | 1.13 | 1.62 |
| MaxDD | **98.7%** | 45.9% | **79.6%** | 42.6% |
| Trades | 469 | 373 | 130 | 87 |

### OOS/IS Sharpe ratio: 0.69 (healthy generalization)

## Analysis

The relaxed threshold succeeded in increasing trades (469 IS / 130 OOS vs 373 / 87 baseline, ~26% and ~49% more respectively). But the extra trades were low-quality — MaxDD exploded to 98.7% IS and 79.6% OOS. The model generated signals on candles where it shouldn't have, because the confidence threshold was too low.

The ternary neutral class (11.1% of labels) was insufficient to filter these bad trades. When confidence threshold is low (~0.34-0.50), the model predicts "long" or "short" for nearly every candle, defeating the purpose of ternary's selective filtering.

## Trade Execution

Verified via output: PnL calculations correct, ATR barriers applied correctly. Feb 2026 OOS showed profitable short trades (ETH TP at 1815, 1834) interspersed with SL hits — consistent with the model working directionally but with poor selectivity.
