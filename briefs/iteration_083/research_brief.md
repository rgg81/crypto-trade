# Iteration 083 Research Brief — EXPLORATION

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process
- Reports split at OOS_CUTOFF_DATE into in_sample/ and out_of_sample/ directories

## Hypothesis

**Two simultaneous changes** (both motivated by the same root cause):

1. **Symbol-scoped feature discovery**: The baseline uses global intersection across ~800 symbols, shrinking 198 available BTC+ETH features down to 113. This loses 85 features that BTC+ETH both have but smaller symbols don't (Stochastic, MACD, Aroon, ADX, etc.). Scoping discovery to the 2 trading symbols recovers all 198.

2. **New feature generation**: 6 interaction features (RSI×ADX, Stochastic×ADX, NATR×ADX, RSI×NATR, return×NATR, return×return) and 7 cross-asset BTC features (xbtc_return, xbtc_natr, xbtc_rsi, xbtc_adx). These have never been in the training pipeline despite the code existing since earlier iterations.

Combined: **198 features** (up from 113 baseline). This is 85 additional features (+75%).

## Type: EXPLORATION

New feature generation (interaction + cross-asset) AND architecture change (symbol-scoped discovery). The biggest feature-related change in 83 iterations.

## Configuration

- Symbols: BTCUSDT, ETHUSDT (pooled)
- **Features: 198** (185 base + 6 interaction + 7 xbtc, symbol-scoped discovery)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Labeling: binary (baseline), TP=8% SL=4%, timeout=7d
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45
- Cooldown: 2 candles

## Risk Assessment

**Feature/sample ratio concern**: With 198 features and ~4,400 training samples per month (2 symbols × 2,200), the ratio is 22 (vs 39 with 113 features). This is lower but still within LightGBM's comfort zone — tree ensembles handle high feature counts well, and Optuna's regularization (colsample_bytree, min_child_samples) provides implicit feature selection.

**Comparison to failed attempts**:
- Iter 070 added 13 features to 106 → 119 features, pooled model. Failed because it added cross-asset features to BTC (redundant). We now add xbtc_ to both but LightGBM handles redundancy natively.
- Iter 078 had 185 features with per-symbol models → failed because halved training data (ratio ~21). We're pooled with 4,400 samples (ratio ~22) which is comparable but with pooling's implicit regularization.

**Mitigation**: LightGBM's colsample_bytree (Optuna range: 0.3-1.0) provides automatic feature subsampling. High regularization trials will effectively use ~60-120 features per tree.

## Research Analysis

### Category A: Feature Contribution Analysis

The 85 new features break down as:
- **6 interaction features** (genuinely new): RSI×ADX, Stochastic×ADX, NATR×ADX, RSI×NATR, return×NATR, return×return. These capture nonlinear relationships between indicator categories.
- **7 cross-asset features** (genuinely new): BTC returns (lag 1,3,8), BTC NATR (14,21), BTC RSI(14), BTC ADX(14). BTC leads ETH by ~1 candle historically.
- **72 recovered features** (existed but were excluded by global intersection): Stochastic (8), MACD (9), Aroon (9), ADX/DI (9), BB%B (8), EMA/SMA crosses (6), Supertrend (3), MFI (4), CMF (3), dist_SMA (3), RSI extreme (3), and more.

The recovered 72 features are particularly valuable — they include trend indicators (ADX, Aroon) and mean-reversion signals (BB%B, RSI extreme) that were never available to the model despite being computed for BTC+ETH.

### Category E: Trade Pattern Analysis (referenced from iter 080)

Baseline IS trade patterns: SHORT WR 46.9% > LONG WR 42.9%. The new ADX/DI features should help the model identify trending vs ranging markets, potentially improving LONG trades in trending markets.

### Category F: Statistical Rigor

The 85 additional features increase the risk of overfitting. However:
- LightGBM's built-in regularization (L1/L2, min samples, depth limits) mitigates this
- Optuna optimizes colsample_bytree, effectively performing automatic feature selection
- The walk-forward validation prevents data leakage
- Many of the 72 "recovered" features are well-established technical indicators, not noise

## Expected Outcome

- IS: Sharpe should improve (more information available)
- OOS: Unknown — depends on whether the extra features capture real signal vs noise
- Key metric to watch: IS MaxDD (learned from iter 081: MaxDD > 60% signals overfitting)
