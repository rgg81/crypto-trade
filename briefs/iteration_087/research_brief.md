# Iteration 087 Research Brief — Ternary Classification with Relaxed Threshold

**Type**: EXPLORATION (labeling paradigm change + signal selection change)
**Date**: 2026-03-30

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Section 1: Research Analysis

References iter 086's 4-category analysis (Categories A, D, E, F) — still valid.

### New Analysis: Prediction Smoothing DISPROVED

Analysis of baseline IS trades (373 trades) showed:
- Only 19% of consecutive trades flip direction (81% same direction)
- **Flipped trades are MORE profitable**: ETH flips WR=59%, mean PnL=+3.46% vs same-direction WR=42%, mean PnL=+0.54%
- Prediction smoothing (requiring consecutive same-direction signals) would REMOVE profitable reversal trades

**Conclusion**: Direction flips are a feature, not a bug. The model correctly identifies regime changes.

### Category C: Labeling Analysis (addendum)

Iter 080 (ternary classification) was the best exploration since baseline:
- OOS MaxDD 33.4% (22% improvement over baseline's 42.6%)
- OOS WR 45.2% (+0.4pp above baseline)
- BTC OOS WR 51.4% (best ever for BTC)
- OOS Sharpe 1.00 (below baseline's 1.84)

The Sharpe gap was driven by fewer trades: 73 vs 87 (16% fewer). Ternary with neutral_threshold=2.0% removed ~11% of training labels as neutral, making the model more selective. The higher selectivity improved per-trade quality (WR +0.4pp, MaxDD -22%) but reduced trade count enough to lower Sharpe.

**Hypothesis**: By relaxing the confidence threshold range for ternary (from [0.50, 0.85] to [0.34, 0.60]), we let the ternary model's neutral class do more of the filtering while reducing the confidence threshold's secondary filtering. This should recover trade count while maintaining ternary's noise reduction.

## Section 2: Proposed Change

### Ternary Classification with Relaxed Confidence Threshold

1. **Ternary labeling**: neutral_threshold_pct=2.0% (same as iter 080). Timeout candles with |forward_return| < 2% are labeled neutral (class 0). Binary: long (class 2), short (class 0). Neutral is the "I don't know" class.

2. **Relaxed confidence threshold**: Optuna range [0.34, 0.60] instead of [0.50, 0.85]. For 3-class classification, P(class) ≥ 0.34 is effectively "any class above uniform probability." This lets the ternary model's neutral class handle the filtering.

3. **Everything else unchanged**: Same 113 features (global intersection), ensemble (seeds 42, 123, 789), cooldown=2, ATR barriers.

### Expected Effect

- **More trades** than iter 080 (which used [0.50, 0.85] threshold)
- **Better per-trade quality** than baseline (ternary removes noisy timeout labels)
- **Net**: Higher Sharpe than iter 080 (more trades) with similar or better MaxDD

### Risk

- If the relaxed threshold lets through too many low-quality trades, WR could drop below break-even
- The neutral class might be too small (only ~11% of labels) to meaningfully improve predictions

### What stays the same

- Model: LGBMClassifier ensemble (seeds 42, 123, 789) with multiclass objective
- Features: 113 (global intersection — baseline default)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers (TP=2.9×NATR, SL=1.45×NATR), cooldown=2
- Symbols: BTCUSDT + ETHUSDT (pooled)
