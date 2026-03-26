# Research Brief: 8H LightGBM Iteration 009

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- IS data only for design decisions; walk-forward on full dataset
- Monthly retraining, 12-month window, reports split at cutoff

## 1. Research Analysis Summary

From iteration 008's mandatory checklist (A, C, E, F):

**F. Statistical Rigor proves the classification approach is fundamentally limited**: Bootstrap CI on IS WR is [30.18%, 30.98%]. Break-even (33.3%) is NOT in the CI. p=4.8e-37. No amount of tuning can close this gap within the current binary classification paradigm.

**C. Labeling**: Forward 1-candle returns have high information content. Labels are stable (flip rate 16-25%). The 4%/2% triple barrier captures meaningful moves.

**A. Features**: Volume and trend features dominate. The model has signal (better than random) but the classification boundary is poorly positioned.

## 2. Gap Quantification

WR is 30.6% (IS), break-even is 33.3%, gap is 2.7pp. TP rate is 29.5%, SL rate is 68.9%. Bootstrap CI EXCLUDES break-even (p < 1e-36). Classification cannot reach profitability.

## 3. Structural Change: Switch to LGBMRegressor

### What Changes

| Component | Classification (current) | Regression (proposed) |
|-----------|------------------------|----------------------|
| Model | `LGBMClassifier` | `LGBMRegressor` |
| Target | Binary label (1=long, -1=short) | Forward 3-candle return (%) |
| Objective | binary cross-entropy | MSE (regression) |
| Output | P(long), P(short) | Predicted return value |
| Trade filter | max(P) > threshold | \|predicted\| > threshold |
| Direction | argmax of probabilities | sign(predicted return) |
| Trade weight | Fixed 100 | Proportional to \|predicted\| |

### Why 3-Candle (24h) Forward Return

From EDA (Phase 1, iter 001): 3-candle horizon has 21.8% of returns within ±0.5% (vs 37.7% for 1-candle). Longer horizon = more signal, less noise. 3 candles = 24h, which aligns with the 3-day timeout.

### Why This Will Help

1. **Regression learns magnitude, not just direction**: The model can express "I expect a +5% move" vs "I expect a +0.1% move" — the first is worth trading, the second isn't
2. **Natural trade selectivity**: Only trade when |predicted| > min_return_threshold. No need for the poorly-calibrated probability confidence threshold
3. **Better use of features**: Volume features (top contributors) correlate with move MAGNITUDE, not just direction. Regression captures this directly
4. **Sharpe alignment**: The optimization objective (minimize prediction MSE) naturally selects for magnitude accuracy, which directly impacts PnL

### Implementation Spec

#### New target computation (in labeling or runner)
For each candle i: `target[i] = (close[i+3] - close[i]) / close[i] * 100` (3-candle forward return in %)

#### Changes to optimization.py
- Use `lgb.LGBMRegressor` instead of `LGBMClassifier`
- Remove `labels_to_classes` / `classes_to_labels` usage
- Optuna optimizes: `min_return_threshold` (0.5–3.0%), `training_days`, LightGBM regressor params
- Sharpe: predict return → if |pred| > threshold, trade in sign(pred) direction → compute PnL from long_pnls/short_pnls

#### Changes to lgbm.py
- `get_signal()`: model.predict() returns float, not probabilities
- If |prediction| < threshold → NO_SIGNAL
- Direction = 1 if prediction > 0 else -1
- Weight proportional to |prediction| (capped at 100)

#### Feature intersection (revert iter 008)
Use intersection (106 features), NOT union (189). Iter 008 proved intersection is better.

### Everything Else Unchanged
Top 50 symbols, TP=4%/SL=2%, 50 Optuna trials, seed 42.
