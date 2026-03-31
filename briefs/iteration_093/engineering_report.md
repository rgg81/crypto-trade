# Engineering Report: Iteration 093

**Date**: 2026-03-31
**Status**: Full walk-forward completed — 453 trades in 8815s

## Implementation

1. Symbol-scoped feature discovery: `_discover_feature_columns(..., symbols=trading_symbols)` → 185 features
2. TimeSeriesSplit gap=44: label leakage prevention
3. 5-seed ensemble: [42, 123, 456, 789, 1001]

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +0.73 | **+1.01** |
| WR | 42.8% | 42.1% |
| PF | 1.19 | 1.25 |
| MaxDD | 92.9% | 46.6% |
| Trades | 346 | 107 |
| Net PnL | +150.2 | +51.1 |

## Per-Symbol OOS

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| ETHUSDT | 56 | 50.0% | +53.8 | 105.3% |
| BTCUSDT | 51 | 33.3% | -2.7 | -5.3% |

ETH carries the strategy. BTC is slightly negative in OOS (WR at break-even for 2:1 RR).

## Label Leakage Audit

- TimeSeriesSplit gap = 44 rows: VERIFIED
- CV fold gaps: 176-184h (all exceed 168h timeout): VERIFIED
- No training label can scan into validation period: CONFIRMED
- Walk-forward trains only on past klines: VERIFIED
