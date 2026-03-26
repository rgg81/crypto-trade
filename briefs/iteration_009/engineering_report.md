# Engineering Report: Iteration 009

## Changes

1. Added `mode` param to LightGbmStrategy ("classification" or "regression")
2. Added `regression_horizon` param (default 3 candles = 24h)
3. Added regression target computation in _train_for_month()
4. Updated optimization.py: new _objective_regression, compute_sharpe_regression
5. Updated get_signal(): model.predict() for regression, weight ∝ |predicted|

## Trade Execution Verification

Sampled trades: entry/exit correct. Regression mode correctly filters by |prediction| > min_return_threshold. Trades that pass are executed with standard TP/SL barriers.

## Results

- 39,214 trades (34,576 IS + 4,638 OOS)
- OOS Sharpe: -3.73, WR: 31.6%, PF: 0.86
- Runtime: ~7,000s
