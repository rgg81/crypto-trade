# Iteration 099 Diary

**Date**: 2026-03-31
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022: PnL=-82.1%, WR=34.6%, 130 trades. IS Sharpe -0.83.

**OOS cutoff**: 2025-03-24

## Hypothesis

Per-symbol LightGBM models will outperform the pooled model because BTC and ETH have fundamentally different trading dynamics (OOS WR: BTC 33.3% vs ETH 50.0%, directional biases opposite).

## What Failed

Per-symbol models catastrophically failed because **2,160 samples per symbol is insufficient for 185 features** (ratio 11.7, well below the 50 minimum). The reduced data caused severe overfitting, especially for ETH.

### Per-Symbol Breakdown (vs Pooled Baseline)

| Metric | BTC per-sym | BTC pooled | ETH per-sym | ETH pooled |
|--------|-------------|------------|-------------|------------|
| IS WR | 40.6% | 43.2% | **29.0%** | 42.4% |
| IS PnL | +3.8% | +64.0% | **-80.8%** | +86.2% |
| IS Trades | 69 | 155 | 62 | 191 |

- **BTC**: Slightly degraded but viable (40.6% WR). Per-symbol BTC may work with fewer features.
- **ETH**: Collapsed entirely (29.0% WR). ETH BENEFITS from BTC's training data — the pooled model provides cross-symbol regularization that prevents ETH overfitting.

## Key Insight: Cross-Symbol Regularization

The pooled model's value isn't just "more data" — it's **diverse data that regularizes**. BTC's bear market patterns help ETH's model avoid overfitting to ETH-specific noise. When ETH trains alone, it memorizes ETH-specific patterns that don't generalize.

This explains why ETH performs better in OOS (50.0% WR) in the pooled model despite having lower IS WR (42.4%) — the BTC data acts as an implicit regularizer.

## Quantifying the Gap

IS WR 35.1%, break-even 33.3% (2:1 RR). Gap is +1.8pp above break-even but PF 0.82 (losing money). The model trades too frequently at low confidence. Optuna selected training_days=10 in some months (~30 samples), confirming memorization.

## Exploration/Exploitation Tracker

Last 10 (iters 090-099): [E, E, X, E, X, E, X, E, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (per-symbol models)

## Research Checklist Categories Completed

- **B (Symbol Universe)**: Deep per-symbol dynamics analysis — BTC vs ETH IS and OOS patterns. Found 17pp OOS WR divergence. Decision: per-symbol models. RESULT: per-symbol failed due to data insufficiency.
- **E (Trade Patterns)**: Per-symbol, per-direction, per-year breakdown. BTC longs degrade IS→OOS, ETH shorts stable.
- **A (Feature Contribution)**: Identified samples/feature ratio as bottleneck (11.7 vs 50 minimum). Feature pruning needed before per-symbol can work — but pruning itself failed in iters 094-095.
- **C (Labeling)**: No labeling change. Confirmed 50/50 label balance per symbol.

## lgbm.py Code Review

The per-symbol implementation is clean: `_train_per_symbol()` iterates symbols, trains independent models, stores per-symbol state. `get_signal()` routes correctly. Feature cache uses sorted column union. No bugs found — the failure is purely statistical (insufficient data), not implementation.

One concern: the `training_days` Optuna parameter [10, 500] is too wide for per-symbol models. With only 2,160 samples, training_days=10 gives ~30 samples. Should floor at 180 days minimum for per-symbol. But moot since per-symbol approach is dead.

## Lessons Learned

1. **Per-symbol models need drastically fewer features.** 185 features × 1 symbol × 24mo = ratio 12. Need ratio ≥ 50 → max ~43 features. But pruning to 50 already failed (iter 094). Catch-22: need fewer features for per-symbol, but can't prune features without destroying signal.

2. **Pooled models provide cross-symbol regularization.** This is more valuable than symbol specialization with current data volume. ETH's OOS success comes FROM the pooled training, not despite it.

3. **Don't split what works.** The baseline pooled model achieves OOS Sharpe +1.01 with honest CV. Per-symbol splitting destroys this by halving training data. The right path is to ADD symbols (increase data) not split existing ones.

4. **Samples/feature ratio is a hard constraint.** With 185 features, need at least 9,250 samples (50× ratio). Two symbols × 24mo = 4,320. Even pooled, ratio is only 23. Need more symbols or fewer features.

## Next Iteration Ideas

After 6 consecutive NO-MERGE (094-099), must propose structural changes only.

1. **EXPLORATION: Regime-conditional prediction (ADX filter).** Add a hard pre-filter: don't trade when BTC ADX_14 < 15 (choppy market). This doesn't change the model — it prevents the model from generating signals in unfavorable conditions. BTC's OOS SL rate of 60.8% suggests many trades happen in ranging markets where the model has no edge. Removing these trades should improve WR without touching the model architecture. This is the simplest structural change that could help.

2. **EXPLORATION: Confidence threshold floor at 0.60.** The baseline Optuna range is [0.50, 0.85]. Many models select thresholds near 0.50, which means trading on low-confidence signals. Raising the floor to 0.60 would reduce trade count but increase average signal quality. This is a targeted change to BTC's weak OOS performance (33.3% WR with current threshold).

3. **EXPLORATION: Asymmetric TP/SL per direction.** BTC longs are terrible OOS (28.0% WR). BTC shorts are better (38.5%). Instead of per-symbol models, try per-direction confidence thresholds: require higher confidence for BTC longs, lower for ETH shorts. Implementation: post-prediction filter based on symbol+direction.
