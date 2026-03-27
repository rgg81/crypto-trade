# Iteration 058 Diary — 2026-03-27

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2024 PnL = -13.8% (WR 38.2%). IS Sharpe +0.38 vs baseline +1.60. Slow features confirmed harmful even with proper isolation (137 features via global intersection, not 242).

**OOS cutoff**: 2025-03-24

## Hypothesis

Same as iter 057: daily-equivalent slow features (3x lookback multiplier on 8h candles) would give the model access to stable, trend-level signals. This iteration fixed iter 057's confound by regenerating ALL ~760 symbols and using the original global intersection.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT
- Features: **137** (106 baseline + 31 slow via global intersection)
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | +0.38 | +1.60 |
| Win Rate | 40.6% | 43.4% |
| Profit Factor | 1.07 | 1.31 |
| Max Drawdown | 110.0% | 64.3% |
| Total Trades | 480 | 574 |

## Results: Out-of-Sample

No OOS data — early stopped before OOS period.

## What Happened

### 1. Slow features are definitively harmful

Iter 057 (242 features) and iter 058 (137 features) produced nearly identical results:

| Metric | Iter 057 (242) | Iter 058 (137) | Baseline (106) |
|--------|---------------|---------------|----------------|
| IS Sharpe | +0.35 | +0.38 | +1.60 |
| IS WR | 41.8% | 40.6% | 43.4% |
| IS PF | 1.07 | 1.07 | 1.31 |
| IS MaxDD | 79.3% | 110.0% | 64.3% |

The confounding variable (80 extra features from symbol-scoped discovery) accounts for < 0.03 Sharpe difference. The slow features are the primary cause of degradation.

### 2. Why slow features hurt

The 31 new slow features (RSI_42/63, NATR_42/63, vol_hist_63/90, etc.) are **highly correlated** with existing features at shorter periods. For LightGBM with ~4400 training samples:
- Adding correlated features splits the importance budget without adding information
- Optuna must search a larger effective hyperparameter space (more features to weight)
- Cross-validation Sharpe consistently near zero even for the best trials

The hypothesis that "the model needs daily-equivalent indicators" was wrong. The model's existing short-period features already capture the relevant patterns at 8h resolution. Slower lookback periods add only lagged, smoothed versions of the same information.

### 3. MaxDD 110% is alarming

The worst MaxDD across all iterations. The model makes worse directional calls with slow features, leading to longer losing streaks and deeper drawdowns.

## Quantifying the Gap

- IS Sharpe: +0.38 vs baseline +1.60 — 76% degradation
- IS WR: 40.6%, break-even ~34.2%, gap = +6.4pp. Baseline gap = +9.2pp. Lost 2.8pp.
- The model went from solidly profitable (PF 1.31) to barely profitable (PF 1.07) with just 31 additional features.

## Decision: NO-MERGE (EARLY STOP)

IS Sharpe 0.38 far below baseline 1.60. MaxDD 110% far exceeds any acceptable threshold.

## lgbm.py Code Review

No changes to lgbm.py in this iteration. Discovery code unchanged from baseline. The code is correct — the problem is the features, not the implementation.

## Research Checklist

Research was completed in iter 056 (4 categories: A, D, E, F). Iters 057-058 acted on finding D (feature frequency gap). The finding that "15/25 feature types lack lookbacks > 10 days" was accurate, but the conclusion that adding them would help was wrong.

## Exploration/Exploitation Tracker

Last 10 (iters 049-058): [E, X, E, E, E, X, X, X, E, E]
Exploration rate: 6/10 = 60% — still above target.
Type: EXPLORATION (new feature generation)

## What We've Eliminated (iters 047-058)

| Iter | Change | Result | Learning |
|------|--------|--------|----------|
| 048 | Add _balance_weights() | NO-MERGE | More class balancing hurts |
| 049 | Parallel BTC+ETH + SOL+DOGE | NO-MERGE | Symbol pairs don't combine |
| 050 | Balanced weights (no code change) | NO-MERGE | Baseline re-run fluke |
| 051 | 14-day timeout | EARLY STOP | Longer timeout hurts |
| 052 | Add XRP to pool | EARLY STOP | More symbols hurt |
| 053 | BNB+LINK independent pair | EARLY STOP | BTC+ETH best pair |
| 054 | AVAX+DOT independent pair | EARLY STOP | BTC+ETH best pair |
| 055 | Balanced weights (real code) | NO-MERGE | Over-correction |
| 056 | Remove is_unbalance | NO-MERGE | is_unbalance is load-bearing |
| 057 | Slow features + scoped discovery | EARLY STOP | 242 features overwhelm model |
| **058** | **Slow features (global intersection)** | **EARLY STOP** | **Slow features are noise, not signal** |

**Dead ends confirmed**: symbol expansion, class weights, timeout changes, and now **feature expansion with slow lookback periods**. The baseline 047's 106 features are sufficient.

## What Worked

- Nothing. But the two-iteration bracket (057 + 058) cleanly isolated and disproved the slow feature hypothesis.

## What Failed

- Adding 31 daily-equivalent slow features degraded IS Sharpe from 1.60 to 0.38
- The hypothesis that "the model needs longer lookback periods" is definitively wrong for this configuration
- Highly correlated features dilute signal without adding information

## Next Iteration Ideas

The feature expansion approach (adding more indicators) is a dead end. The baseline's 106 features are the right feature set. Future improvements should focus on **model behavior**, not data expansion.

1. **Per-symbol models** (EXPLORATION): BTC and ETH have different dynamics. Separate models avoid scale confusion and can learn symbol-specific patterns. The pooled model uses ~50% of its feature importance budget distinguishing BTC from ETH (iter 056 found VWAP, A/D, OBV as top features — all price-level).

2. **Prediction smoothing / signal cooldown** (EXPLOITATION): Majority vote of last 3 predictions or N-candle cooldown after a trade. Reduces flip-flopping and may improve trade quality.

3. **Feature SELECTION (pruning)** (EXPLOITATION): Instead of adding features, remove the 55 near-zero importance ones. Go from 106 → ~50 features. Less noise, faster training, potentially better signal.

4. **Dynamic TP/SL via ATR** (EXPLORATION): Scale barriers by recent volatility. Fixed 8%/4% works well in volatile 2022 but poorly in calm 2024 (year-over-year decay seen in baseline).

5. **Regression target** (EXPLORATION): Instead of classification (long/short), predict forward return magnitude. Could capture more nuanced signal.

## Lessons Learned

- **More features ≠ better model.** Adding 31 correlated features to a working 106-feature model degraded it by 76%. LightGBM doesn't automatically ignore useless features — they dilute the split budget.
- **Test hypotheses with minimal changes.** Iter 058 proved the slow feature hypothesis was wrong using only 31 extra features (vs 057's 136 extra). The controlled experiment was worth the effort.
- **The feature set is locally optimal.** The baseline's 106 features are the right balance of information and parsimony. Future iterations should change the model, not the features.
- **Two consecutive early stops on the same hypothesis = definitive rejection.** Don't revisit slow features.
