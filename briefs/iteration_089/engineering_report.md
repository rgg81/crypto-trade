# Engineering Report: Iteration 089

**Date**: 2026-03-30
**Status**: EARLY STOP — Year 2022 PnL=-81.7%, WR=31.9%, 91 trades

## Implementation

### PurgedKFoldCV (new file)
- Added `src/crypto_trade/strategies/ml/purged_cv.py`
- Class `PurgedKFoldCV(n_splits=5, purge_window=21, embargo_pct=0.02)`
- Drop-in replacement for TimeSeriesSplit in `optimization.py`
- 10 unit tests written and passing (`tests/test_purged_cv.py`)

### optimization.py Change
- Replaced `from sklearn.model_selection import TimeSeriesSplit` with `from crypto_trade.strategies.ml.purged_cv import PurgedKFoldCV`
- Line 178: `tscv = PurgedKFoldCV(n_splits=cv_splits, purge_window=21, embargo_pct=0.02)`
- No other code changes

### Deviations from Research Brief
- None. Single-variable change as specified.
- Note: Feature count is 115 (symbol-scoped discovery on current parquets), not 106 as in baseline iter 068. This is the same confound present since iter 083 — the parquet files have been regenerated since the baseline was established.

## Results

### EARLY STOP Trigger
Year 2022 checkpoint: cumulative PnL=-81.7%, WR=31.9% (threshold: PnL>0, WR>33%)

### In-Sample Metrics (partial — early stopped after 92 trades)

| Metric | Iter 089 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-1.32** | +1.22 |
| WR | **32.6%** | 43.4% |
| PF | **0.72** | 1.35 |
| MaxDD | **116.1%** | 45.9% |
| Trades | 92 (partial) | 373 (full IS) |
| Net PnL | **-81.3** | +264.3 |

### Root Cause Analysis

The PurgedKFoldCV catastrophically degraded performance. Analysis of the Optuna logs reveals:

1. **Many folds produce -10.0 (minimum trades penalty)**: With purging+embargo removing ~109 samples at boundaries, combined with the `training_days` parameter trimming, several CV folds end up with too few validation trades above the confidence threshold. This creates many -10.0 fold scores.

2. **Best CV Sharpe is extremely low**: The best Optuna trial in the last training window had Sharpe=0.24 (fold scores: -0.13, 0.10, 1.14, 0.27, -0.16). Compare with baseline where best trials typically achieve 0.5-1.0. The purged CV correctly removes leakage, revealing that the "true" CV performance is much lower than TimeSeriesSplit suggested.

3. **training_days interaction**: The `training_days` Optuna parameter (10-500) trims the training window before each fold. Combined with purging, this can leave folds with almost no training data — particularly the first 1-2 folds. Trials with training_days < 80 frequently produce empty folds (-10.0 scores).

4. **High confidence thresholds compound the problem**: Optuna selects thresholds 0.80-0.85, which filter out most predictions. On small purged validation folds, this leaves very few trades for Sharpe computation.

### Trade Execution Verification

Sampled 10 trades from trades.csv:
- Entry prices match close prices of signal candles: YES
- SL/TP prices computed correctly: YES (dynamic ATR barriers applied)
- Timeout exits use correct 7-day window: YES
- PnL calculations verified: YES
- SL rate: 52/92 = 56.5% (very high — model's directional accuracy is poor)
- TP rate: 22/92 = 23.9%
- Timeout rate: 18/92 = 19.6%

### Key Observation

The PurgedKFoldCV is working CORRECTLY — it properly purges and embargoes. The problem is that the purged CV reveals the baseline's TimeSeriesSplit was inflating CV scores via leakage, and Optuna was optimizing against these inflated scores. When the leakage is removed, Optuna's best hyperparameters are fundamentally different (and worse for this particular model architecture).

This does NOT mean PurgedKFoldCV is wrong. It means the model's "true" cross-validated performance (without leakage) is much lower than reported. The baseline's OOS Sharpe +1.84 may be a lucky configuration that happened to work despite being selected with leaky CV.
