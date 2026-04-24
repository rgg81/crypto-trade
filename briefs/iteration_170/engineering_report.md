# Iteration 170 Engineering Report

**Role**: QE
**Config**: AAVE stand-alone Gate 3 (ATR 3.5/1.75, 24mo, 193 features, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: 7 min (434 s)

## Trigger

```
Year 2022: PnL=-17.8% (WR=30.8%, 13 trades)
```

## Partial results (IS only; no OOS reached)

| Metric | Value |
|---|---:|
| Total trades | 14 |
| IS Sharpe | +0.06 |
| IS WR | 35.7% |
| IS Profit Factor | 1.02 |
| IS MaxDD | 9.11% |
| IS Net PnL | +0.45% |

Gate 3 scorecard:
- IS Sharpe > 0? ✓ (+0.06, barely)
- IS WR > 33.3%? ✓ (35.7%)
- ≥ 100 IS trades? ✗ (14)
- Year-1 PnL ≥ 0? ✗ (-17.8%)

All four candidates in the recent sequence (AVAX, ATOM, DOT, AAVE) fail the year-1 checkpoint. The shared issue is bear-market 2022 performance, not sector-specific.

## Feature Reproducibility Check

193 explicit columns from `BASELINE_FEATURE_COLUMNS`. Confirmed by log.

## Summary

Four consecutive Gate 3 failures at the same config. LTC now stands as a clear outlier. Time to stop screening and pivot.
