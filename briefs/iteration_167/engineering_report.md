# Iteration 167 Engineering Report

**Role**: QE
**Config**: ATOM stand-alone Gate 3 screen (ATR 3.5/1.75, 24mo, 193 features, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: 19 min (1,159 s)

## Trigger

```
Year 2022: PnL=-7.1% (WR=38.2%, 55 trades)
```

Year-1 cumulative PnL is negative — trips `yearly_pnl_check`.

## Partial results (IS only; no OOS reached)

| Metric | Value |
|---|---:|
| Total trades | 56 |
| IS Sharpe | -0.89 |
| IS Sortino | -0.54 |
| IS WR | 39.3% |
| IS Profit Factor | 0.75 |
| IS MaxDD | 43.95% |
| IS Net PnL | -29.46% |

All Gate 3 criteria fail:
- IS Sharpe > 0? **FAIL** (-0.89)
- IS WR > 33.3%? pass (39.3%) but PF < 1.0 makes it moot
- ≥ 100 IS trades? **FAIL** (56)
- Year-1 PnL ≥ 0? **FAIL** (-7.1%)

## Trade Execution Verification

Skipped — 56 trades is a small sample and no anomalies surfaced in partial log.

## Label Leakage Audit

CV gap: `(10080/480 + 1) × 1 = 22`. Confirmed in lgbm.py (unchanged from baseline).

## Feature Reproducibility Check

Runner passes `feature_columns=list(BASELINE_FEATURE_COLUMNS)` (193 explicit columns). Confirmed by `[lgbm] 193 feature columns, 51 walk-forward splits` in log.

## Elapsed Time

Expected: ≤ 90 min or fast early stop. Actual: 19 min — fail-fast worked as intended.
