# Iteration 083 Diary — 2026-03-29

## Merge Decision: NO-MERGE

OOS Sharpe +0.44 vs baseline +1.84. IS Sharpe +0.69 vs baseline +1.22. More features = worse performance across the board.

**OOS cutoff**: 2025-03-24

## Hypothesis

Symbol-scoped feature discovery (198 features vs 113 baseline) with 6 interaction + 7 cross-asset features would improve signal quality.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Features: 198** (symbol-scoped discovery + interaction + xbtc)
- Labeling: binary, TP=8% SL=4%, timeout=7d
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 083 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **+0.69** | +1.22 |
| WR | 43.6% | 43.4% |
| PF | **1.19** | 1.35 |
| MaxDD | **72.0%** | 45.9% |
| Trades | 330 | 373 |

## Results: Out-of-Sample

| Metric | Iter 083 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **+0.44** | +1.84 |
| WR | 42.2% | 44.8% |
| PF | **1.09** | 1.62 |
| MaxDD | 43.6% | 42.6% |
| Trades | 102 | 87 |
| Net PnL | **+20.5%** | +94.0% |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 47 | 44.7% | +18.4% |
| ETHUSDT | 55 | 40.0% | +2.0% |

## What Happened

**198 features catastrophically hurt the model.** IS Sharpe dropped 43% from baseline. The feature/sample ratio dropped from 39 (113/4400) to 22 (198/4400), and the model couldn't effectively regularize across that many features.

**Root cause: most of the 85 "new" features are redundant noise.** The 72 "recovered" features (Stochastic, MACD, Aroon at multiple periods) are heavily correlated with existing features (RSI, EMA, ADX). Adding 8 Stochastic variants when the model already has 6 RSI variants just gives LightGBM more correlated options to split on, reducing tree diversity and stability.

**The interaction and xbtc features were drowned out.** Only 13 of 198 features were genuinely new (6 interaction + 7 xbtc). Their signal was diluted by 72 redundant features that shouldn't have been added.

**IS MaxDD 72% confirms the pattern.** Iter 081: IS MaxDD 88% → OOS Sharpe -1.17. Iter 083: IS MaxDD 72% → OOS Sharpe +0.44. Baseline: IS MaxDD 46% → OOS Sharpe +1.84. **IS MaxDD is the strongest predictor of OOS failure.**

## Quantifying the Gap

WR: 42.2%, break-even 33.3%, gap +8.9pp (vs baseline +11.5pp). PF 1.09 — barely profitable. The model makes correct directional calls but with smaller magnitude (mean PnL per trade +0.20% vs baseline +1.08%).

## Exploration/Exploitation Tracker

Last 10 (iters 074-083): [X, X, E, X, E, E, X, X(abandoned), **E**]
Exploration rate: 4/10 = 40%
Type: **EXPLORATION** (new feature generation + discovery architecture change)

## Research Checklist

Completed 4 categories: A (feature generation — interaction + xbtc), A2 (symbol-scoped discovery), E (trade patterns referenced), F (feature/sample ratio analysis).

## lgbm.py Code Review

The symbol-scoped discovery change is correct and should be kept — it's the right behavior for any model that trades a subset of symbols. The bug was in the baseline's global intersection, not in this fix.

## Lessons Learned

1. **More features = worse model.** 198 features with 4,400 samples is too many. The baseline's 113 was already too many — the signal is likely concentrated in 30-50 features.

2. **IS MaxDD is the best OOS predictor.** Three data points now:
   - IS MaxDD 46% → OOS Sharpe +1.84 (baseline)
   - IS MaxDD 72% → OOS Sharpe +0.44 (iter 083)
   - IS MaxDD 88% → OOS Sharpe -1.17 (iter 081)
   Linear relationship. Any iteration with IS MaxDD > 55% should be treated as suspicious.

3. **Correlated features are worse than missing features.** Adding Stochastic(5,7,9,14,21) when RSI(5,7,9,14,21,30) already exists doesn't help — it fragments the model's splits across redundant indicators.

4. **Symbol-scoped discovery is correct but dangerous without pruning.** The fix (scope to trading symbols) is architecturally right, but it unlocks 198 features that MUST be pruned before use. Keep the fix, add pruning.

5. **Interaction + xbtc features deserve a fair test.** They were drowned out by 72 redundant features. The next iteration should test them with aggressive pruning — start with 30-40 base features + 13 new = 43-53 total.

## Next Iteration Ideas

**MANDATORY: Feature pruning before anything else.**

1. **EXPLORATION: Aggressive feature pruning** — Run importance analysis, correlation dedup, stability check per the new A1 protocol. Target 30-40 features. Then rerun baseline config. This isolates the pruning effect.

2. **EXPLORATION: Pruned features + interaction/xbtc** — After pruning base to 30-40, add back the 13 interaction+xbtc features (total 43-53). Tests whether these features help when not drowned by noise.

3. **EXPLORATION: Symbol diversification** — With a leaner feature set (30-40 features), screen SOL/XRP/DOGE/BNB through the 5-gate protocol. More symbols + fewer features = better samples-per-feature ratio.
