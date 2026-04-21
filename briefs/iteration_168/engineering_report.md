# Iteration 168 Engineering Report

**Role**: QE
**Config**: DOT stand-alone Gate 3 (ATR 3.5/1.75, 24mo, 193 features, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: 11 min (675 s)

## Trigger

```
Year 2022: PnL=-14.0% (WR=37.5%, 16 trades)
```

## Partial results (IS only; no OOS reached)

| Metric | Value |
|---|---:|
| Total trades | 17 |
| IS Sharpe | +0.54 |
| IS WR | 41.2% |
| IS Profit Factor | 1.21 |
| IS MaxDD | 18.00% |
| IS Net PnL | +6.31% |

IS metrics are actually positive on the 17 trades observed, but year-1 PnL was negative enough (-14%) to trip fail-fast. The checkpoint doesn't distinguish "marginal but positive over time" from "flat-out broken" — it just enforces year-1 discipline.

Gate 3 scorecard:
- IS Sharpe > 0? ✓ (+0.54)
- IS WR > 33.3%? ✓ (41.2%)
- ≥ 100 IS trades? ✗ (17)
- Year-1 PnL ≥ 0? ✗ (-14%)

Half-pass but the trade-count and year-1 failures dominate.

## Label Leakage Audit

CV gap `22` rows/fold. Unchanged from baseline.

## Feature Reproducibility Check

193 explicit columns from `BASELINE_FEATURE_COLUMNS`. Log confirms.

## Summary

DOT's signal is not dead, but the config doesn't carry it through year-1. Three consecutive Gate 3 candidates (AVAX, ATOM, DOT) have failed at this ATR multiplier set. Time to pivot — see diary "Next Iteration Ideas".
