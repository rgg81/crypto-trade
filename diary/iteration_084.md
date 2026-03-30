# Iteration 084 Diary — 2026-03-30

## Merge Decision: NO-MERGE

OOS Sharpe -0.03 vs baseline +1.84. Early-stopped on yearly checkpoint (2025: PnL=-21.1%, WR=37.4%).

**OOS cutoff**: 2025-03-24

## Hypothesis

Aggressive feature pruning (198→49 features) would improve model stability and OOS generalization by increasing the samples-per-feature ratio from 57 to 229.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Features: 49** (pruned from 198 via A1 protocol: corr dedup + importance threshold + stability filter)
- Labeling: binary, TP=8% SL=4%, timeout=7d
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 084 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | +1.10 | +1.22 |
| WR | 43.8% | 43.4% |
| PF | 1.33 | 1.35 |
| MaxDD | **42.4%** | 45.9% |
| Trades | 288 | 373 |

Per-symbol IS: BTC 48.0% WR (+109.2%), ETH 40.4% WR (+91.9%).

## Results: Out-of-Sample

| Metric | Iter 084 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.03** | +1.84 |
| WR | 38.8% | 44.8% |
| PF | **0.99** | 1.62 |
| MaxDD | 45.4% | 42.6% |
| Trades | 85 | 87 |
| Net PnL | **-1.15%** | +94.0% |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 36 | 30.6% | -19.7% |
| ETHUSDT | 49 | 44.9% | +18.6% |

## What Happened

**Feature pruning improved IS stability but destroyed OOS performance.** IS MaxDD improved by 3.5pp (42.4% vs 45.9%), confirming that the removed features were noise in-sample. But the model lost its ability to generalize out-of-sample.

**BTC OOS collapsed to 30.6% WR — below break-even.** The baseline's BTC OOS was mediocre but positive; the pruned model's BTC actively loses money. The pruning may have removed features that specifically helped BTC's OOS regime (April-May 2025 sell-off).

**ETH OOS was acceptable: 44.9% WR, +18.6%.** This suggests the pruned features retained enough ETH signal. The problem is BTC-specific.

**The early OOS period (April-May 2025) was devastating: -38.5% in 23 trades.** This 2-month drawdown accounts for most of the OOS loss. The model made too many wrong directional calls during a volatile regime transition.

**IS Sharpe -10% degradation confirms pruning removed some signal.** From +1.22 to +1.10 — the 57 removed features did contribute to IS performance, just not enough to justify keeping 106 features.

## Quantifying the Gap

WR: 38.8% OOS, break-even 33.3%, gap +5.5pp (vs baseline +11.5pp). The gap narrowed by 6pp. PF 0.99 — essentially break-even. Mean PnL per trade: -0.01% (vs baseline +1.08%). The model's directional accuracy degraded substantially in OOS.

BTC specifically: 30.6% WR is 2.7pp below break-even. The model is worse than random for BTC in OOS.

## IS MaxDD Pattern Update

Four data points now:
- IS MaxDD 42.4% → OOS Sharpe -0.03 (iter 084) **BREAKS THE PATTERN**
- IS MaxDD 46% → OOS Sharpe +1.84 (baseline)
- IS MaxDD 72% → OOS Sharpe +0.44 (iter 083)
- IS MaxDD 88% → OOS Sharpe -1.17 (iter 081)

**IS MaxDD is NOT a reliable OOS predictor after all.** Iter 084 has the BEST IS MaxDD (42.4%) but the WORST OOS Sharpe (-0.03). The pattern from iter 083 was an artifact of 3 noisy data points. IS MaxDD reflects in-sample stability, not out-of-sample generalization.

## Exploration/Exploitation Tracker

Last 10 (iters 075-084): [X, E, X, E, E, X, X(abandoned), E, **E**]
Exploration rate: 5/10 = 50%
Type: **EXPLORATION** (structural feature reduction)

## Research Checklist

Completed 4 categories:
- **A1**: Full pruning protocol (correlation dedup, importance threshold, stability check)
- **A3**: Feature importance by category with economic hypotheses
- **E**: Trade pattern analysis (label distributions, flip rates, per-hour/per-month analysis)
- **F**: Statistical rigor (bootstrap WR, binomial tests — WR significantly above break-even in IS)

## lgbm.py Code Review

The new `feature_columns` and `trading_symbols` parameters work correctly. Symbol-scoped discovery with feature filtering is architecturally sound and should be kept. The implementation is clean — features are filtered in `compute_features()` after discovery, preserving schema order.

No bugs found. The backtest ran correctly to completion (early-stopped as expected).

## Lessons Learned

1. **Feature pruning alone doesn't improve OOS.** Removing noise features helps IS stability (IS MaxDD improved) but doesn't guarantee OOS generalization. The model's OOS performance depends on the specific features retained, not just the count.

2. **IS MaxDD is NOT a reliable OOS predictor.** The pattern from iter 083 was premature — iter 084 has the best IS MaxDD but worst OOS. This is a classic case of concluding a pattern from too few data points. IS MaxDD measures in-sample stability, nothing more.

3. **BTC and ETH need different features.** BTC collapsed to 30.6% WR while ETH was fine at 44.9%. The pruned feature set was optimized on the full IS data (which is ETH-biased at 60% short). BTC-specific signal was likely in the removed features.

4. **The baseline's 106 features may be close to optimal for this model.** Pruning to 49 hurt. Adding to 198 hurt (iter 083). The sweet spot for the current architecture is probably 80-120 features.

5. **Feature importance is period-dependent.** The "stable" features (top-20 in all 3 IS sub-periods) didn't guarantee OOS success. Stability within IS doesn't mean stability across the IS/OOS boundary.

6. **The `feature_columns` and `trading_symbols` parameters are useful infrastructure.** They enable controlled experiments and should be kept regardless of this iteration's results.

## Next Iteration Ideas

**After 8 consecutive NO-MERGE iterations (077-084), structural changes are mandatory.**

1. **EXPLORATION: Baseline reproduction with symbol-scoped discovery** — Run the exact baseline config (106 features via global intersection) but using the new `trading_symbols` parameter to confirm it matches the baseline. This establishes whether the infrastructure changes affected results.

2. **EXPLORATION: Regression labeling** — Replace binary classification (long/short) with regression (forward return prediction). This fundamentally changes the learning task. Binary classification with 8%/4% TP/SL creates noisy labels when forward returns are small. Regression lets the model learn magnitude, not just direction.

3. **EXPLORATION: Dynamic barriers per symbol** — Use different TP/SL for BTC vs ETH based on per-symbol NATR. BTC's NATR ~3% makes 8%/4% barriers very wide; ETH's higher volatility makes them more appropriate. Per-symbol barriers could improve BTC's WR.

4. **EXPLOITATION: Restore baseline features** — If idea #1 confirms the baseline is intact, run the exact baseline to re-establish performance. This iteration proved that feature changes (both pruning and expansion) degrade the model. The baseline's feature set may be a local optimum that's hard to beat by feature selection alone.
