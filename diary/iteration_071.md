# Iteration 071 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL -51.2% (WR 39.8%, 166 trades). IS Sharpe -0.50. Model is catastrophically worse with 4 symbols.

**OOS cutoff**: 2025-03-24

## Hypothesis

Expand from 2 to 4 symbols (BTC+ETH+SOL+DOGE) to increase training data and diversify.

## Results

| Metric | Iter 071 (4 sym) | Baseline (068, 2 sym) |
|--------|-----------------|----------------------|
| IS Sharpe | **-0.50** | +1.22 |
| IS MaxDD | **101.0%** | 45.9% |
| IS Trades | 167 | 373 |
| IS WR | 39.5% | 43.4% |
| OOS | not reached | +1.84 |

**Runtime**: 1570s (26 min) — early stop cut it short.

## What Happened

The pooled model with 4 symbols is catastrophically worse. The model learned an incoherent signal by mixing BTC/ETH patterns with SOL/DOGE patterns.

### Root cause: price scale and dynamics differences

- **BTC/ETH**: Lower volatility (NATR ~2-4%), correlated, more predictable momentum
- **SOL/DOGE**: Higher volatility (NATR ~5-15%), more meme-driven, less predictable
- Pooling these into one model forces the model to find a single decision function that works for both groups — which works for neither

### Optuna found terrible hyperparameters

Best training_days=10 for the last month (essentially random) — the optimizer couldn't find any profitable configuration across all 4 symbols.

## Exploration/Exploitation Tracker

Last 10 (iters 062-071): [X, E, X, E, X, E, E, X, E, E]
Exploration rate: 5/10 = 50%
Type: EXPLORATION (symbol universe expansion)

## Lessons Learned

1. **Pooled models don't work across fundamentally different assets.** BTC/ETH and SOL/DOGE have different dynamics. A single LightGBM can't learn both.
2. **More data is not always better.** Doubling training data with dissimilar data is worse than having less but coherent data.
3. **Per-symbol or per-cluster models are needed for multi-symbol.** If we want to trade SOL/DOGE, they need separate models or a hierarchical approach.

## Next Iteration Ideas

1. **EXPLOITATION: Stay with BTC+ETH** — The baseline 2-symbol configuration is proven. Don't dilute the model.
2. **EXPLORATION: Per-symbol models** — Train separate LightGBM per symbol, each with its own Optuna optimization. Allows different hyperparameters for BTC vs ETH.
3. **EXPLORATION: Calendar features (hour/day)** — Minimal dimensionality increase (2-3 features), could capture time-of-day patterns.
4. **EXPLORATION: Prediction smoothing** — Majority vote of last 3 predictions to reduce flip-flopping.
