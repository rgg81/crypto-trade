# Iteration 057 Diary — 2026-03-27

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2024 PnL = -23.5% (WR 37.2%). IS Sharpe +0.35 vs baseline +1.60. Adding 56 slow features + exposing 80 previously-hidden features degraded the model severely. The feature-to-sample ratio became too high (242 features / 4400 samples).

**OOS cutoff**: 2025-03-24

## Hypothesis

Adding daily-equivalent slow features (3x lookback multiplier) to all 6 feature groups would give the model access to stable, trend-level signals. Iter 056's research found 15/25 feature types lack lookbacks > 10 days on 8h candles.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT
- Features: **242** (vs baseline 106) — 56 new slow + 80 previously-excluded
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | +0.35 | +1.60 |
| Win Rate | 41.8% | 43.4% |
| Profit Factor | 1.07 | 1.31 |
| Max Drawdown | 79.3% | 64.3% |
| Total Trades | 479 | 574 |

## Results: Out-of-Sample

No OOS data — early stopped before OOS period.

## What Happened

### 1. TWO problems, not one

The feature discovery change exposed a critical issue. By scoping to BTC+ETH only, we picked up **80 features that were previously excluded** by the all-symbol intersection. These include:
- Raw price-level features (EMA values, SMA values, OBV, A/D, VWAP)
- Additional BB/volatility variants
- Volume features not present in all ~800 symbols

The baseline's 106 features were the **global intersection** across all symbols. Many features existed in BTC/ETH parquets but were excluded because some obscure altcoins didn't have them. The symbol-scoped discovery inadvertently "unlocked" these extra features.

So this iteration changed TWO things simultaneously:
1. Added 56 new slow features (the intended change)
2. Exposed 80 previously-hidden features (unintended side effect)

This violates the "one variable at a time" principle.

### 2. Feature overload (242 features / 4400 samples)

The combined 242 features overwhelmed the model. Evidence:
- Optuna consistently found near-zero Sharpe across most months
- Later months (2024-2025) had ALL negative best-trial Sharpe
- Year 2024 triggered fail-fast with -23.5% PnL

### 3. Per-symbol divergence

BTC remained modestly profitable (47.4% WR, +118%) but ETH collapsed (37.3% WR, -44%). The extra price-level features likely confused the model when pooling BTC and ETH data at very different price scales.

## Quantifying the Gap

- IS Sharpe: +0.35 vs baseline +1.60 — 78% degradation
- IS WR: 41.8%, break-even ~34.2%, gap = +7.6pp. Baseline gap = +9.2pp. Lost 1.6pp.
- IS PF: 1.07 — barely profitable. Baseline PF 1.31.
- The degradation is IS, not just OOS — this isn't overfitting. The model genuinely performs worse with 242 features.

## lgbm.py Code Review

Found the root cause: `_discover_feature_columns()` previously intersected ALL parquet files in the directory. With the symbol-scoped fix, it exposes features that only high-volume symbols have but that rarer symbols lack. This is correct behavior for symbol-specific backtests but changes the effective feature set. **The baseline was trained on 106 globally-intersected features, not BTC+ETH-specific features.**

To test slow features in isolation, the next iteration must restore the exact baseline feature set and add ONLY the new slow features.

## Research Checklist

Research was completed in iter 056 (4 categories: A, D, E, F). This iteration acted on finding D (feature frequency gap). The findings were correct — slow features ARE missing — but the implementation introduced confounders.

## Exploration/Exploitation Tracker

Last 10 (iters 048-057): [E, E, X, E, E, E, X, X, X, E]
Exploration rate: 6/10 = 60% — still above target. Exploitation needed.
Type: EXPLORATION (new feature generation)

## What Worked

- Nothing. IS Sharpe dropped 78%.

## What Failed

- Feature count more than doubled (106 → 242), overwhelming the model
- Two changes conflated: slow features + previously-hidden features
- The symbol-scoped discovery fix was logically correct but experimentally confounding

## Overfitting Assessment

Not applicable — degradation is in IS, not OOS. The model is worse in-sample. This is a dimensionality problem, not an overfitting problem.

## Next Iteration Ideas

The slow feature hypothesis hasn't been properly tested yet. The confounding variable (80 extra features from symbol-scoped discovery) must be isolated.

1. **Revert symbol-scoped discovery, add only slow features** (EXPLOITATION, HIGHEST PRIORITY): Use the original `_discover_feature_columns()` behavior (all-symbol intersection) so the base feature set stays at ~106. Then generate slow features for ALL symbols so they appear in the global intersection. This isolates the slow feature effect.

2. **Selective slow features only** (EXPLOITATION): Instead of adding ALL slow periods, add only the top-3 feature types that iter 056 found most important at longer periods: RSI_42, ADX_42, NATR_42. Start small — 6-10 new features instead of 56.

3. **Feature selection before training** (EXPLOITATION): With 242 features, add a pre-training step: compute correlation matrix, drop features with |corr| > 0.95, then run permutation importance on a single IS fold to prune to top-K features.

4. **Per-symbol models** (EXPLORATION): BTC and ETH diverged significantly (47.4% vs 37.3% WR). Separate models would avoid price-scale confusion from raw features. This was already in iter 056's ideas.

## Lessons Learned

- **Symbol-scoped feature discovery changes the effective feature set.** The baseline's 106 features were a specific global intersection. Changing the intersection scope is a variable change, even if unintended.
- **Feature count matters.** Going from 106 to 242 features on ~4400 training samples is too aggressive. The features-to-samples ratio of ~18:1 is poor for tree models.
- **Always check what features the model actually sees.** The 80 "bonus" features from symbol-scoped discovery were invisible in the code change but dominated the model's behavior.
- **One variable at a time is sacred.** Even "infrastructure" changes (like fixing feature discovery) can have experimental consequences.
