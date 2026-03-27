# Research Brief: 8H LightGBM Iteration 058

**Type**: EXPLORATION (new feature generation — daily-equivalent slow features, isolation fix)

## 0. Data Split & Backtest Approach
- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 24-month training window
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Hypothesis

Same as iter 057: daily-equivalent slow features (3x lookback multiplier on 8h candles) give the model access to stable, trend-level signals. The research from iter 056 found 15/25 feature types lack lookbacks > 10 days.

**What's different from iter 057**: Iter 057 changed TWO variables simultaneously — (a) added slow features, (b) changed feature discovery to symbol-scoped, exposing 80 extra features. This confounded the experiment (242 features instead of expected ~160). This iteration fixes that by:
1. Keeping the ORIGINAL global-intersection feature discovery (unchanged from baseline)
2. Generating slow features for ALL ~800 symbols
3. The global intersection will naturally include the new slow features since all symbols have them

Expected feature count: ~106 (baseline) + ~56 new slow = ~162 (NOT 242).

## 2. What Changes

Identical slow feature additions as iter 057 (all 6 feature groups), but regenerated for ALL symbols so they pass global intersection. Feature discovery code is NOT modified.

See iter 057 brief Section 2 for the complete feature list.

## 3. What Does NOT Change

- Feature discovery: global intersection across ALL symbols (baseline behavior)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT only
- Training window: 24 months
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials
- Confidence threshold: Optuna 0.50-0.85
- is_unbalance=True + PnL sample weights
- Seed: 42

## 4. Model Spec
- Model: LightGBM classification
- is_unbalance: True
- Hyperparameters: Optuna-optimized
- Random seed: 42

## 5. Expected Outcome

With ~162 features (controlled increase from 106), the model should handle the dimensionality better than iter 057's 242. If slow features have real signal, IS Sharpe should improve or maintain. If they're just noise, IS should be similar to baseline (not worse like iter 057).

## 6. Risk

Some slow features may not exist for symbols with short history (< 150 candles). These will become NaN and may be dropped from the global intersection. The actual feature count could be lower than 162 if some slow features don't survive the intersection filter.
