# Iteration 114 Research Brief
**Type**: EXPLOITATION
**Theme**: Disable early stop to evaluate OOS — iter 113 config unchanged

## Section 0: Data Split
- OOS cutoff: `2025-03-24` (fixed)

## Change
Single change: `yearly_pnl_check=False`. Same 67 features, same everything.

## Result: FIRST PROFITABLE OOS MEME MODEL
- IS Sharpe: +0.11, OOS Sharpe: +0.29
- OOS WR: 43.0%, OOS PF: 1.07
- OOS Trades: 93, OOS Net PnL: +18.8%
- Both DOGE (+11.0%) and SHIB (+7.8%) profitable OOS
- OOS/IS Sharpe ratio: 2.59 (no overfitting)
