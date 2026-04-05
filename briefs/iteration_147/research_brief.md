# Iteration 147 Research Brief

**Type**: EXPLORATION (Per-symbol volatility targeting)
**Model Track**: A+C+D with per-symbol (not portfolio-wide) vol targeting
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 145 introduced portfolio-wide vol targeting (scale by std of aggregate daily PnL).
This dampens ALL trades equally when the portfolio is volatile — including good
trades from low-vol symbols that happen during high-vol events on other symbols.

**Hypothesis**: Per-symbol vol targeting (scale each trade by ITS symbol's vol) preserves
more signal. BTC trades scale by BTC's recent daily PnL vol; LINK by LINK's; etc.

**Mechanism**: When one symbol is calm and another chaotic, iter 145 scales both down.
Iter 147 scales only the chaotic one, preserving the calm symbol's edge.

## Configuration

| Parameter | Value |
|-----------|-------|
| Scaling rule | `scale = target_vol / symbol_realized_vol` |
| Per-symbol aggregation | Daily PnL per symbol, std over lookback days |
| Target vol | 0.5 (IS-tuned) |
| Lookback days | 30 (IS-tuned) |
| Min scale | 0.5 |
| Max scale | 2.0 |

**Note**: Lower target_vol (0.5 vs iter 145's 1.5) reflects lower per-symbol vol
than portfolio-aggregate vol.

## Walk-Forward Methodology

20 configs tested (target × lookback grid) on IS trades only. Best by IS Sharpe
applied to OOS without further tuning. Daily aggregation and rolling vol use only
PAST data (days_before ≥ 1).

## Success Criteria

Primary: OOS Sharpe > baseline +2.33
Constraints: MaxDD ≤ 45.7%, PF > 1.0, trades ≥ 50, concentration ≤ 50%
