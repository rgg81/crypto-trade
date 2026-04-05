# Iteration 149 Research Brief

**Type**: EXPLORATION (Hybrid VT: per-symbol × portfolio)
**Model Track**: A+C+D with hybrid vol targeting
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Per-symbol VT (iter 147) catches symbol-specific risk. Portfolio VT (iter 145)
catches cross-asset co-movement. Hybrid might combine both.

**Formula**: `scale = sqrt(per_symbol_scale × portfolio_scale)` — geometric mean.

## Configuration

IS-tuned target=0.3, lookback=14 (best of 15 configs on IS trades).

## Success Criteria

Primary: OOS Sharpe > baseline iter 147 (+2.65)
