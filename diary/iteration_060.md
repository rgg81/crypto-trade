# Iteration 060 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2023 PnL = -28.3% (WR 35.7%). IS Sharpe +0.34 vs baseline +1.60. Regression model generated too few trades and couldn't sustain profitability.

**OOS cutoff**: 2025-03-24

## Hypothesis

Replace binary classification with regression. Target: `long_pnl - short_pnl` (continuous PnL advantage). Use LGBMRegressor with Huber loss. Trade when |prediction| exceeds a return threshold optimized by Optuna.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT (pooled)
- Features: **106** (same global intersection as baseline)
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42
- **regression=True**: LGBMRegressor, Huber loss, return_threshold optimized

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | +0.34 | +1.60 |
| Win Rate | 39.0% | 43.4% |
| Profit Factor | 1.075 | 1.31 |
| Max Drawdown | 59.9% | 64.3% |
| Total Trades | 213 | 574 |
| PnL | +35.6% | +387.9% |

## Results: Out-of-Sample

No OOS data — early stopped in Year 2 (2023).

## What Happened

### 1. Regression generates too few trades

Optuna selected return_threshold ≈ 6.3, meaning only candles where the predicted PnL advantage exceeds 6.3% are traded. This is an extreme filter — only 213 trades over 2+ years (vs 574 for classification). The model is correct that high-conviction predictions exist, but there aren't enough of them to sustain portfolio growth.

### 2. Symbol dynamics reversed

| Symbol | Classification WR | Regression WR | Classification PnL | Regression PnL |
|--------|-------------------|---------------|--------------------|--------------  |
| BTC | 40.5% | 41.4% | +81.8% | +44.8% |
| ETH | 45.7% | 36.8% | +306.1% | -9.1% |

ETH collapsed from 45.7% to 36.8% WR. The regression model learned to be more selective on ETH (114 trades vs 317) but selected WORSE trades. BTC slightly improved (41.4% vs 40.5%) but generated far fewer trades (99 vs 257).

### 3. The optimization surface is very noisy

Many Optuna trials produced -10.0 penalties (< 20 trades in CV folds). The regression target `long_pnl - short_pnl` has a bimodal distribution centered at ±12 with a peak at 0. The model's continuous predictions don't map cleanly to this distribution — most predictions are near zero, making threshold selection brittle.

### 4. What regression got right

- MaxDD 59.9% < baseline 64.3% — the high threshold filters out some bad trades
- Year 2022 was profitable (+7.4%) — the model initially finds signal
- BTC WR improved slightly (41.4% vs 40.5%)

### 5. What regression got wrong

- Year 2023 collapsed (-28.3%) — the model doesn't generalize well
- ETH degraded dramatically — regression captures different patterns than classification
- Trade count too low — Sharpe penalized by sparse trading

## Quantifying the Gap

- IS Sharpe: +0.34 vs baseline +1.60 — 79% degradation
- IS WR: 39.0%, break-even ~34.2%, gap = +4.8pp. Baseline gap = +9.2pp. Lost 4.4pp.
- IS PF: 1.075 — barely above break-even. Baseline PF 1.31.
- Trade count: 213 vs 574 — 63% fewer trades
- ETH WR: 36.8%, barely above break-even, while baseline ETH was 45.7%

## Decision: NO-MERGE (EARLY STOP)

IS Sharpe 0.34 far below baseline 1.60. Year 2023 fail-fast triggered.

## lgbm.py Code Review

The regression implementation is clean. `_signal_regression()` correctly compares prediction magnitude against threshold. `optimize_and_train_regression()` uses Huber loss and return_threshold search.

One issue: the return_threshold search range [0.5, 8.0] is too wide for the target distribution. The target `long_pnl - short_pnl` ranges from -12 to +12, with most values at the extremes (when one direction hits TP and the other SL). A threshold of 6+ means only extreme predictions are traded. A narrower range like [1.0, 5.0] might generate more trades while still being selective. However, this is unlikely to close the 79% Sharpe gap.

## Research Checklist

Completed 4 categories (A, C, E, F) in the research brief:
- **A (Feature Contribution)**: Same 106 features, isolated model type variable
- **C (Labeling)**: Regression target design analyzed (long_pnl - short_pnl distribution, timeout treatment)
- **E (Trade Patterns)**: Baseline trade statistics used to motivate regression approach
- **F (Statistical Rigor)**: Forward return SNR analysis showed low predictability for raw returns; triple-barrier target expected to amplify signal

Finding: The triple-barrier PnL target is more informative than raw returns, but the regression model can't predict it well enough. The bimodal distribution (±12 at extremes, 0 in middle) may be inherently harder to predict than binary direction.

## Exploration/Exploitation Tracker

Last 10 (iters 051-060): [E, E, E, X, X, X, E, E, E, E]
Exploration rate: 7/10 = 70% — very high. Next must be EXPLOITATION.
Type: EXPLORATION (model type change)

## What We've Eliminated (iters 047-060)

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
| 058 | Slow features (global intersection) | EARLY STOP | Slow features are noise |
| 059 | Per-symbol models | EARLY STOP | Pooling is essential |
| **060** | **Regression target** | **EARLY STOP** | **Classification > regression for this task** |

**Dead ends confirmed**: symbol expansion, class weights, timeout changes, feature expansion, per-symbol models, AND now regression. The baseline 047's CLASSIFICATION approach is locally optimal.

## What Worked

- MaxDD slightly better (59.9% vs 64.3%)
- BTC WR slightly improved (41.4% vs 40.5%)
- The return_threshold concept is sound — filtering by predicted magnitude is useful

## What Failed

- LGBMRegressor on triple-barrier PnL target: too few trades, noisy optimization
- ETH collapsed from 45.7% to 36.8% WR
- Bimodal target distribution makes prediction harder than binary classification

## Next Iteration Ideas

Exploration rate is 70% — next MUST be exploitation. The classification baseline is the right model type, architecture, and feature set. The only levers left are:

1. **Feature pruning** (EXPLOITATION): Drop the ~55 lowest-importance features. Go from 106 → ~50. Less noise, faster training, potentially better Optuna convergence. Use permutation importance from a single IS LightGBM to identify which features to keep.

2. **Prediction smoothing / signal cooldown** (EXPLOITATION): Majority vote of last 3 predictions, or N-candle cooldown after a trade. The baseline may flip direction too often.

3. **Tighter confidence threshold range** (EXPLOITATION): Current range [0.50, 0.85]. Iter 047's best thresholds are typically 0.75-0.82. Narrow to [0.70, 0.85] to give Optuna a smaller search space.

4. **Dynamic TP/SL via ATR** (EXPLORATION): This remains the most promising unexplored structural change. Fixed 8%/4% works in volatile periods but is too wide in calm markets. ATR-based barriers adapt automatically.

5. **Ternary classification** (EXPLORATION): Add neutral class for ambiguous candles. But this is another model type change — may face similar issues as regression.

## Lessons Learned

- **Classification outperforms regression for this task.** Binary direction prediction with confidence gating is a better inductive bias than continuous PnL prediction with magnitude gating. The model's strength is in directional calls, not magnitude estimation.
- **Bimodal targets are hard to predict.** The `long_pnl - short_pnl` distribution has three modes (≈-12, 0, +12). Regression models prefer smooth, unimodal targets. Classification naturally handles the bimodal structure (long/short = the two modes at ±12).
- **Trade count matters.** Fewer trades ≠ better trades. The regression model's high threshold (6.32) was too selective — it missed profitable opportunities that the classification model captured with its probability-based filter.
- **Symbol dynamics can reverse with model changes.** BTC became the stronger symbol under regression, while ETH collapsed. This suggests the model type interacts with symbol-specific signal structure.
