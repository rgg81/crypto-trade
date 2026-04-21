# Iteration 164 Engineering Report

**Role**: QE
**Config**: AVAX stand-alone Gate 3 screen (ATR 3.5 TP / 1.75 SL, 24mo, 193 features, VT on)
**Status**: **EARLY STOP (year-1 checkpoint)**
**Elapsed**: ~9 minutes (538 s)

## Trigger

`yearly_pnl_check=True` aborted the backtest at the end of calendar year 2022 (first full year of walk-forward predictions, since 24-month training starts predicting mid-2022):

```
Year 2022: PnL=-34.6% (WR=36.4%, 22 trades)
```

This violates both year-1 thresholds (cumulative PnL < 0, WR below ~33% break-even). AVAX is not a viable Gate 3 candidate under baseline config.

## Partial results (IS only; no OOS reached)

| Metric | Value |
|---|---:|
| Total trades | 23 |
| IS Sharpe | -1.84 |
| IS Sortino | -1.34 |
| IS WR | 39.1% |
| IS Profit Factor | 0.59 |
| IS MaxDD | 24.96% |
| IS Net PnL | -14.87% |
| IS DSR | -18.88 |

All Gate 3 criteria fail:
- IS Sharpe > 0? **FAIL** (-1.84)
- IS WR > 33.3%? borderline pass (39.1%) but with PF < 1.0 irrelevant
- ≥ 100 IS trades? **FAIL** (23)
- Year-1 PnL ≥ 0? **FAIL** (-34.6%)

## Trade Execution Verification

Skipped — partial run, low sample count (23 trades), no practical need to re-verify execution mechanics already validated in baseline v152.

## Label Leakage Audit

CV gap: `(10080 / 480 + 1) * 1 symbol = 22`. Confirmed in `lgbm.py._train_for_month()`. No change from baseline.

## Feature Reproducibility Check

Runner passes `feature_columns=list(BASELINE_FEATURE_COLUMNS)` — 193 explicit columns. Confirmed by `[lgbm] 193 feature columns, 51 walk-forward splits` in the log. No auto-discovery.

## Elapsed Time vs Expected

Expected: up to 90 min, early-abort possible.
Actual: 9 min — fail-fast did its job efficiently.
