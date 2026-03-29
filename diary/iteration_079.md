# Iteration 079 Diary — 2026-03-29

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL -46.0% (WR 35.7%, 154 trades). Per-symbol models with 106-feature global intersection still fail. Third consecutive per-symbol failure (059, 078, 079).

**OOS cutoff**: 2025-03-24

## Hypothesis

Per-symbol models with the same 106-feature global intersection (fixing iter 078's 185-feature bloat) would allow specialization without overfitting.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Architecture: per-symbol models with **global 106-feature intersection** — FIX from iter 078
- Labeling: Triple barrier fixed TP=8%, SL=4%, timeout=7d
- Symbols: BTCUSDT, ETHUSDT
- Features: **106** (global intersection, same as baseline)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789] per symbol
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample (EARLY STOP — Year 1 only)

| Metric | Iter 079 | Iter 078 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | **-0.49** | -0.61 | +1.22 |
| WR | **36.1%** | 38.6% | 43.4% |
| PF | **0.91** | 0.88 | 1.35 |
| MaxDD | **112.9%** | 90.4% | 45.9% |
| Trades | 155 | 132 | 373 |

### Per-Symbol

| Symbol | Iter 079 | Iter 078 | Baseline |
|--------|----------|----------|----------|
| BTCUSDT | 37.7% | 32.4% | 42.4% |
| ETHUSDT | 35.9% | 46.6% | 44.3% |

## What Happened

The fix improved BTC (+5.3pp vs iter 078) but destroyed ETH (-10.7pp). With the same 106 features, ETH lost the specialization advantage that 185 features provided. This creates an impossible dilemma:
- 185 features: ETH works but BTC overfits (iter 078)
- 106 features: BTC improves but ETH loses specialization (iter 079)
- Either way: per-symbol is worse than pooled

**Root cause confirmed**: The fundamental issue is not features — it's **sample size**. Each symbol has ~2,200 training samples (halved from ~4,400 pooled). With only ~2,200 samples and 106 features (ratio ~21), Optuna cannot find robust hyperparameters. The pooled model's regularization from mixing both symbols' patterns is genuinely beneficial.

## Exploration/Exploitation Tracker

Last 10 (iters 070-079): [E, E, E, E, X, X, E, X, **E**, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (architecture change)

## Lessons Learned

1. **Per-symbol models are definitively dead for BTC+ETH.** Three failures (059, 078, 079) with different feature strategies all fail. Halved training data is the root cause. DO NOT attempt per-symbol models until the universe has 5+ symbols with 3+ years of data each.

2. **Pooling provides beneficial regularization.** The baseline's pooled model benefits from 2x training data. Mixed BTC+ETH patterns act as implicit regularization.

3. **Feature count is secondary.** Iter 078 (185 features) vs 079 (106 features) showed different trade-offs but both failed. The problem is architecture, not features.

4. **ETH-specific features exist but aren't enough.** The 79 features unique to ETH (in iter 078) helped ETH specifically but couldn't compensate for BTC's failure. This is useful knowledge for future feature engineering — but not for per-symbol models.

## lgbm.py Code Review

The per_symbol code works correctly in both configurations (185 and 106 features). No bugs. The code can be kept in the codebase for future use when more symbols are available, but should not be used for the 2-symbol universe.

## Next Iteration Ideas

Per-symbol models and ATR-aligned labeling are both exhausted. Shift to fundamentally different approaches:

1. **EXPLORATION: Regression target** — Predict forward 8h/24h return magnitude (not binary). Uses `objective="regression"` in LightGBM. This is the most fundamental unexplored change. The model learns magnitude, not just direction. No discretization of labels.

2. **EXPLORATION: Ternary classification** — Add "neutral" class for timeout candles with |return| < 1%. Reduces noise by giving the model a way to say "no trade." Current binary model forces a direction even when the signal is weak.

3. **EXPLOITATION: Confidence threshold tuning** — The baseline uses Optuna range 0.50-0.85. Try narrowing to 0.65-0.85 (higher minimum) to force fewer, higher-quality trades.
