# Engineering Report: Iteration 047

## Config
24mo training, TP=8%/SL=4%, timeout=7days (10080min), BTC+ETH, 0.50-0.85 threshold.

## Results
IS Sharpe +1.60, OOS +1.16. 710 trades (574 IS, 136 OOS).
IS/OOS ratio 0.72. Passed year-1 fail-fast.

## Seed Sweep (5 seeds)
IS: 5/5 positive (mean +1.38). OOS: 3/5 positive (mean +0.41).

## Code on This Branch
- EarlyStopError + yearly_pnl_check in backtest.py
- ATR support in labeling.py (atr_values param)
- feature_columns param in lgbm.py
