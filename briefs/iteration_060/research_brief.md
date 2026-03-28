# Research Brief — Iteration 060

**Type**: EXPLORATION (model type change: classification → regression)
**Date**: 2026-03-28

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

All analysis below uses IS data only (before 2025-03-24).

## Hypothesis

Replace binary classification (predict direction: long vs short) with regression (predict continuous PnL advantage). The regression target `long_pnl - short_pnl` captures both direction AND magnitude. Instead of a confidence threshold on class probabilities, a return threshold on predicted PnL advantage filters trades.

The classification approach forces the model into a binary decision. With 34.2% break-even WR, the model must correctly predict direction at least 1/3 of the time. Regression can learn that some candles have large directional advantage (trade these) while others are ambiguous (skip these), providing a more nuanced signal.

## Research Analysis (4 Categories: A, C, E, F)

### A. Feature Contribution Analysis

Same 106 global intersection features as baseline. No feature changes — isolating the model type variable.

Key insight from iter 059: the pooled BTC+ETH model is essential (per-symbol models failed). Regression uses the same pooled architecture.

### C. Labeling Analysis

**Current classification labels**: Direction (-1 or 1) determined by which TP hits first, or forward return sign.
- Label distribution: 57% long / 43% short (class imbalance handled by is_unbalance=True)
- Label flips: high on adjacent candles — the market often hits both TP and SL within 7 days

**Regression target**: `long_pnl - short_pnl`
- Positive = long is more profitable → LONG
- Negative = short is more profitable → SHORT
- Near zero = both directions similar → NO TRADE
- Continuous target eliminates the hard boundary between "long" and "short" labels

**Advantages of regression**:
1. No class imbalance — continuous target has no classes
2. Huber loss is robust to outliers (extreme PnL events)
3. The model learns PnL magnitude, not just direction
4. The return threshold directly filters by predicted profitability

### E. Trade Pattern Analysis

From baseline IS trades:
- TP rate: 32.2%, SL rate: 51.7%, Timeout rate: 16.0%
- Timeout avg PnL: +1.6% (range: [-3.4%, +6.6%])
- Timeout trades are ambiguous — classification labels them based on forward return sign, but they're often near-zero signal
- Regression treats timeouts proportionally (small PnL → small target → less likely to trade)

### F. Statistical Rigor

Forward return predictability (IS, BTC+ETH):
- 1-candle (8h): SNR = 0.03 — too noisy for raw prediction
- 3-candle (24h): SNR = 0.06
- 21-candle (168h/7d): SNR = 0.14 — best match for 7-day timeout

However, we're NOT predicting raw forward returns. The target `long_pnl - short_pnl` has higher SNR because it captures the TP/SL structure. The triple barrier labeling amplifies directional moves (+7.9% for TP, -4.1% for SL) relative to raw returns.

Expected target distribution: bimodal around ±12 (when one direction hits TP while the other hits SL) with a peak near 0 (when both resolve similarly).

## Design Specification

### Model Change

**Before** (baseline): LGBMClassifier, objective='binary', is_unbalance=True
**After**: LGBMRegressor, objective='huber' (robust to outliers)

### Target Construction

```python
target = long_pnls - short_pnls  # from existing label_trades()
```

### Signal Generation

```python
prediction = model.predict(features)
if prediction > +return_threshold: → LONG
if prediction < -return_threshold: → SHORT
else: → NO TRADE
```

### Optuna Search Space

- `return_threshold`: [0.5, 8.0] — minimum |prediction| to trade
- `training_days`: [10, 500]
- Same tree hyperparameters as baseline
- **Removed**: confidence_threshold, is_unbalance (not applicable to regression)

### What Stays the Same
- 106 global intersection features
- TP=8%, SL=4%, timeout=7 days
- 24-month training window
- 50 Optuna trials, 5 CV folds
- Seed=42, BTC+ETH pooled
- Walk-forward monthly, yearly fail-fast

### Risk Assessment
- **Huber loss sensitivity**: May need tuning of delta parameter. Default should work.
- **Return threshold range**: [0.5, 8.0] covers small to large predicted advantages. Optuna will find the sweet spot.
- **Sample weight**: Using same PnL-magnitude weights. No is_unbalance since no classes.
