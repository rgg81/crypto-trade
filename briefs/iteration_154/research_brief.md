# Iteration 154 Research Brief

**Type**: EXPLOITATION (analytical — temporal stability check)
**Model Track**: v0.152 baseline validation
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

v0.152's OOS Sharpe +2.83 is an aggregate metric over 12 months. Deployment confidence
requires verifying the strategy is stable THROUGHOUT the OOS period — not concentrated
in a few lucky months.

## Analysis

Compute per-quarter and per-month OOS PnL using iter 152's config. Count profitable
months. Check if any single month dominates the total PnL.

## Success Criteria

- At least 60% of months profitable (conservative threshold)
- No single month contributes > 40% of total OOS PnL
- Each quarter's Sharpe positive
