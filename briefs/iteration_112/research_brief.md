# Iteration 112 Research Brief

**Type**: EXPLORATION  
**Theme**: Trend features + training window variants for 2024 bull fix

## Section 0: Data Split
- OOS cutoff: `2025-03-24` (fixed)

## Changes
- 8 new trend-following features (cumulative returns, breakouts, HH/LL, RSI slope, volume trend)
- Tested 12-month (112a) and 24-month (112b) training windows
- 62 total features (42 base + 12 microstructure + 8 trend)

## Result: 112b (24mo, 62 features) is the best meme configuration
- IS Sharpe +0.21, PF 1.056, MaxDD 60.6%, 112 trades
- 2023 PnL: -2.7% (nearly break-even, vs -69.7% in iter 108)
- SHIB: +23.5% PnL (44.6% WR), DOGE: -4.7% (35.7% WR)
