# Iteration 144 Research Brief

**Type**: EXPLORATION (analytical — trade correlation analysis)
**Model Track**: Portfolio composition analysis (no new backtest)
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

After 7 failed iterations since iter 138 MERGE, the portfolio appears at local maximum.
iter 143 added DOGE (Model E) but OOS MaxDD exploded from 62.8% → 92.5% despite DOGE
having strong standalone metrics (OOS Sharpe +1.24). This iteration diagnoses WHY.

## Approach

**No new backtest.** Combine existing trades (iter 138 A+C+D + iter 142 DOGE)
and run analytical tests:

1. Monthly PnL correlation matrix across all 4 models
2. Losing month Jaccard overlap
3. Drawdown attribution by month
4. Portfolio subset comparisons (all combinations of A/C/D/E)

## Expected Outcomes

1. **Quantify temporal correlation** — which models lose in the same months
2. **Identify the drawdown driver** — single bad month vs distributed losses
3. **Evaluate alternative portfolios** — Is there a subset that beats A+C+D?

## Success Criteria

This is diagnostic, not a new strategy. Success = clear explanation of why iter 143
failed + evidence-based recommendation on whether iter 138 is truly optimal or if
an alternative combination beats it on Sharpe.
