# Iteration 125 Diary

**Date**: 2026-04-03
**Type**: EXPLORATION (Model C: SOL+AVAX pooled L1 alt model)
**Model Track**: SOL+AVAX pooled (single-model)
**Decision**: **NO-MERGE** — catastrophic IS/OOS divergence. IS Sharpe +1.24, OOS Sharpe -1.57.

## Hypothesis

Pooling SOL+AVAX doubles training data vs SOL-only (iter 124), improving the samples/feature ratio from 12 to 24 with auto-discovered 185 features and ATR labeling 3.5x/1.75x.

## Results

| Metric | Iter 124 (SOL only) | Iter 125 (SOL+AVAX) | Change |
|--------|---------------------|----------------------|--------|
| IS Sharpe | +0.162 | **+1.244** | +668% |
| IS WR | 42.6% | **48.7%** | +6.1pp |
| IS PF | 1.051 | **1.346** | +28% |
| IS Trades | 141 | **234** | +66% |
| IS Net PnL | +31.2% | **+274.5%** | +781% |
| OOS Sharpe | +0.47 | **-1.57** | catastrophic |
| OOS WR | 46.9% | **33.0%** | -13.9pp |
| OOS Trades | 32 | **94** | +194% |
| OOS Net PnL | +19.0% | **-128.0%** | catastrophic |

### OOS Per-Symbol

| Symbol | Trades | WR | Net PnL |
|--------|--------|----|---------|
| SOLUSDT | 53 | 34.0% | -66.5% |
| AVAXUSDT | 41 | 31.7% | -61.5% |

Both symbols lose money OOS. AVAX is slightly worse (31.7% WR below break-even).

## Root Cause: Textbook Overfitting

**IS Sharpe +1.24 is the strongest IS we've ever seen for a new model.** But OOS Sharpe -1.57 is also the worst OOS collapse. IS/OOS ratio of -1.26 means the model learned patterns that are SPECIFIC to the IS period and reverse in OOS.

**Why this happened:**
1. **185 features with ~4,400 pooled training samples = ratio 24.** This is well below the 50 minimum. The model has far too many features for the available data.
2. **Optuna overfits to IS noise.** With 50 trials and high feature dimensionality, Optuna finds hyperparameters that exploit IS-specific artifacts. These artifacts don't persist OOS.
3. **SOL+AVAX are highly correlated.** Pooling two L1 alts that move together doesn't add genuine new information — it just doubles the correlated data. Unlike BTC+ETH (which have different dynamics), SOL+AVAX are essentially the same signal.
4. **colsample_bytree doesn't compensate enough.** Even with LightGBM's implicit feature selection, 185 features with ratio 24 is too extreme.

## Key Insight: Pooling Correlated Symbols Causes Overfitting

Iter 124 (SOL-only) had weak IS Sharpe (+0.16) but positive OOS (+0.47). Pooling with AVAX dramatically improved IS (+1.24) but destroyed OOS (-1.57). This means AVAX added noise, not signal. The model exploited AVAX's IS patterns that don't generalize.

**Lesson**: Pooling only helps if the symbols bring DIFFERENT information. SOL and AVAX move together — pooling them is like training on the same data twice with slightly different noise. The model overfits to the noise.

## Label Leakage Audit

CV gap = 44 (22 candles × 2 symbols). Correct. The OOS collapse is NOT from leakage — it's from overfitting.

## lgbm.py Code Review

No code changes. The overfitting is architectural (too many features, correlated symbols), not a bug.

## Gap Quantification

OOS WR 33.0% is AT break-even for ATR-scaled barriers. OOS PF 0.69 confirms the model has negative edge OOS. IS WR 48.7% was illusory.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, E, X, X, E, E, E, **E**] (iters 116-125)
Exploration rate: 8/10 = 80%

## Research Checklist

- **B** (symbols): SOL+AVAX pooling tested — AVAX adds noise, not signal
- **A** (features): 185 auto-discovered features with ratio 24 → catastrophic overfitting

## Next Iteration Ideas

**The SOL/AVAX L1 alt model track has been thoroughly explored (iters 123-125). SOL has marginal standalone signal; pooling with AVAX destroys it. Time to change direction.**

1. **LINK standalone with ATR labeling** (EXPLORATION, single-model) — LINK has different dynamics than L1 alts (oracle infrastructure, DeFi dependency). 5678 IS candles, $26M daily volume. Passes gates 1-2. If LINK's standalone IS Sharpe is stronger than SOL's +0.16, it's a better Model C candidate.

2. **XRP standalone with ATR labeling** (EXPLORATION, single-model) — XRP has 5696 IS candles, $1.26B daily volume. Different market structure (regulatory-driven, cross-border payments). Gate 1 borderline on gaps but passable.

3. **Regression model for BTC/ETH** (EXPLORATION, single-model) — Fundamentally different approach. Instead of classification, predict forward return magnitude. Could capture signal the classifier misses.

4. **Feature pruning for SOL** (EXPLOITATION, single-model) — SOL standalone (iter 124) showed IS +0.16 with 185 features. If pruned to ~45 features like the meme model, samples/feature ratio goes from 12 to 49. Could significantly strengthen the signal.
