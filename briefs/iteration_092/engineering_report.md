# Engineering Report: Iteration 092

**Date**: 2026-03-31
**Status**: EARLY STOP — Year 2025 PnL=-20.0%, WR=41.0%, 100 trades

## Implementation

Baseline 068 config + TimeSeriesSplit gap=44. Features regenerated with original 6 groups (momentum, volatility, trend, volume, mean_reversion, statistical) → 106 global intersection.

## Results

| Metric | IS | OOS | Baseline OOS |
|--------|-----|-----|-------------|
| Sharpe | +0.47 | **-0.28** | +1.84 |
| WR | 41.9% | 42.1% | 44.8% |
| PF | 1.12 | 0.93 | 1.62 |
| MaxDD | 96.6% | 33.4% | 42.6% |
| Trades | 332 | 76 | 87 |

## Key Finding

106 features + gap=44 → OOS unprofitable (-0.28). Compare iter 091 (115 features + gap=44) → OOS profitable (+0.89). The 9 extra features from expanded trend/volatility modules carry real signal.

## Label Leakage Audit
- TimeSeriesSplit gap = 44 rows: VERIFIED (printed on every training window)
- 106 features (global intersection across 760 symbols): VERIFIED
