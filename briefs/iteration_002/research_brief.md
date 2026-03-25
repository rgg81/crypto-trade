# Research Brief: 8H LightGBM Iteration 002

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 12-month minimum training window (unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Change from Iteration 001

**Single variable change: re-introduce confidence threshold at prediction time.**

### Problem Identified in Iteration 001

The model traded every candle for every symbol (498K total trades, ~50 per symbol per month) with 30% win rate. With TP=4%/SL=2%, break-even requires ~34%. The model had no selectivity — 69% of trades hit SL.

### Solution

Add a confidence threshold to `get_signal()`: only trade when `max(P(long), P(short)) >= confidence_threshold`. When the model's probabilities are near 0.50, it has no conviction — these are noise trades.

### Key Design Decision

The **optimization objective is unchanged** — it evaluates ALL predictions using actual returns (no threshold in Sharpe calculation). The threshold is applied ONLY at inference time in the backtest. This keeps the Optuna search realistic (the model is scored on its full predictive ability) while filtering out low-conviction trades at execution time.

### Threshold Value

**Add `confidence_threshold` back to Optuna** with range **0.50–0.65** (wider than iter 001's 0.50–0.55).

Rationale: at 0.50, no filtering occurs (same as iter 001). At 0.65, only ~20-30% of trades survive. Optuna will find the sweet spot where the remaining trades have sufficient win rate to be profitable.

The threshold is optimized per walk-forward month alongside LightGBM hyperparams and training_days.

## 2. Everything Else Unchanged

| Component | Value | Change from iter 001? |
|-----------|-------|-----------------------|
| Labeling | Triple barrier TP=4%, SL=2%, timeout=4320min | No |
| Fee handling | Fee-aware returns in labeling and weights | No |
| Symbol universe | 201 active USDT symbols | No |
| Features | All 185, no Optuna selection | No |
| Walk-forward | Monthly, 12-month window, 5 CV folds | No |
| Optuna trials | 50 per month | No |
| LightGBM | Binary classifier, is_unbalance=True | No |
| Sharpe metric | Actual returns (long_pnls/short_pnls) | No |
| Seed | 42 | No |

## 3. Implementation Spec

### Changes to `optimization.py`

Add `confidence_threshold` as an Optuna parameter:
```python
confidence_threshold = trial.suggest_float("confidence_threshold", 0.50, 0.65)
```

In the CV evaluation loop, after getting predictions, apply the threshold before computing Sharpe:
```python
confidence = y_proba.max(axis=1)
mask = confidence >= confidence_threshold
# Only compute Sharpe on trades that pass the threshold
# If fewer than min_trades survive → penalty
```

The `compute_sharpe` function needs a threshold-aware variant that takes probabilities + threshold.

### Changes to `lgbm.py`

Store the optimized `confidence_threshold` from Optuna. In `get_signal()`:
```python
if confidence < self._confidence_threshold:
    return NO_SIGNAL
```

The `optimize_and_train` return signature changes back to:
```python
(model, columns, confidence_threshold)
```

### Changes to `labeling.py`

None.

## 4. Expected Impact

- **Trade count**: Should decrease dramatically (from ~500K to ~50K-200K depending on threshold)
- **Win rate**: Should increase (removing noise trades concentrates on higher-conviction predictions)
- **Net PnL**: May still be negative but should improve significantly
- **Sharpe**: Target: better than -4.89 (OOS baseline)

## 5. Risks

- If the model has no real signal, thresholding will just reduce trade count without improving win rate — Sharpe may improve purely from fewer trades
- Higher threshold = fewer trades = higher variance in results = less statistical significance
- Threshold could be overfit per walk-forward month (but this is managed by Optuna's regularization and the IS/OOS split)
