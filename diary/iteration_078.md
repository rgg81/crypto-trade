# Iteration 078 Diary — 2026-03-29

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2022 PnL -54.2% (WR 38.2%, 131 trades). Per-symbol models with 185 features overfit badly due to halved training data.

**OOS cutoff**: 2025-03-24

## Hypothesis

Per-symbol LightGBM models will outperform the pooled baseline by allowing BTC and ETH to specialize in their different dynamics (ETH SHORT 51.1% WR vs BTC LONG 43.6% in baseline).

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Architecture: per-symbol models** (separate LightGBM per symbol) — NEW
- Labeling: Triple barrier fixed TP=8%, SL=4%, timeout=7d
- Symbols: BTCUSDT, ETHUSDT
- **Features: 185 per symbol** (no cross-symbol intersection)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789] per symbol
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample (EARLY STOP — Year 1 only)

| Metric | Iter 078 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.61** | +1.22 |
| WR | **38.6%** | 43.4% |
| PF | **0.88** | 1.35 |
| MaxDD | **90.4%** | 45.9% |
| Trades | 132 | 373 |

### Per-Symbol Split

| Symbol | Trades | WR | vs Baseline |
|--------|--------|-----|-------------|
| BTCUSDT | 74 | **32.4%** | -10pp (catastrophic) |
| ETHUSDT | 58 | **46.6%** | +2.3pp (improved!) |

## What Happened

The per-symbol architecture **changed two variables simultaneously** instead of one:
1. Training architecture: pooled → per-symbol (intended)
2. Feature count: 106 → 185 (unintended side effect)

When `_discover_feature_columns()` runs per-symbol, it no longer intersects across symbols. Each symbol gets all 185 of its own features instead of the 106 that exist in both. This **nearly doubled the feature count while halving the training samples**.

Feature/sample ratio degradation:
- Baseline: 106 features / 4,400 samples = 41.5 (healthy)
- Per-symbol: 185 features / 2,200 samples = 11.9 (3.4x worse, overfit territory)

**ETH improved to 46.6% WR** — the per-symbol hypothesis has merit. ETH specialization works. But **BTC collapsed to 32.4% WR** (below break-even). BTC likely has fewer clean patterns, and the 185-feature model learned noise.

## Research Checklist Categories Completed

- **B**: Symbol Universe & Diversification (correlation, lead-lag, architecture decision)
- **C**: Labeling Analysis (per-symbol label distributions)
- **E**: Trade Pattern Analysis (per-symbol WR, direction split, exit reasons)
- **F**: Statistical Rigor (bootstrap CI, binomial test, PnL distribution)

## Key Findings from Research

1. BTC-ETH correlation = 0.83 (high, strengthens in high-vol). No lead-lag relationship.
2. ETH SHORT 51.1% WR vs ETH LONG 38.5% — major directional asymmetry supports per-symbol.
3. Baseline signal is statistically real (p=0.000031 vs break-even).
4. Per-symbol feature discovery gives 185 features (not 106) — this was the root cause of failure.

## Exploration/Exploitation Tracker

Last 10 (iters 069-078): [X, E, E, E, E, X, X, E, X, **E**]
Exploration rate: 6/10 = 60%
Type: **EXPLORATION** (architecture change: pooled → per-symbol)

## Lessons Learned

1. **Per-symbol models must use the same feature set as pooled.** The 106-feature global intersection should be enforced regardless of architecture. Per-symbol discovery giving 185 features was the fatal flaw — it changed two variables at once.

2. **ETH per-symbol specialization works.** 46.6% WR (+2.3pp over baseline) with a dedicated model. The hypothesis is validated for ETH.

3. **BTC needs more signal, not more features.** BTC collapsed to 32.4% WR with 185 features. BTC may simply be harder to predict, or the 185-feature model overfits on BTC's smaller signal.

4. **Feature/sample ratio matters.** Dropping from 41.5 to 11.9 was catastrophic. Any per-symbol approach must maintain a healthy ratio.

## lgbm.py Code Review

The per-symbol code (`_train_per_symbol`, `_predict_per_symbol`) works correctly. No bugs found. The issue was research design, not engineering. The code should be reused in the next iteration with a fix: pass the global feature intersection to per-symbol training.

Specific improvement needed: Add a `feature_columns` parameter to `LightGbmStrategy` that overrides per-symbol discovery. When per_symbol=True and feature_columns is provided, use those columns for all symbols.

## Next Iteration Ideas

1. **EXPLORATION: Per-symbol models with 106-feature intersection** — Exact same architecture as iter 078 but force all symbol models to use the global 106-feature intersection. This isolates the per-symbol training variable from the feature count variable. One change at a time.

2. **EXPLORATION: Per-symbol models with feature selection** — Add permutation importance pruning within per-symbol Optuna: train on 185 features, prune bottom 50% by importance, retrain. This could work if symbol-specific features add genuine signal.

3. **EXPLOITATION: Hybrid — ETH per-symbol, BTC pooled** — Since ETH improved with per-symbol (46.6% WR) but BTC collapsed, try training ETH separately and keeping BTC in the pooled model. This is a cautious exploitation of the ETH finding.
