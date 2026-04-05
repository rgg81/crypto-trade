# Iteration 153 Research Brief

**Type**: EXPLOITATION (min_scale lower-bound extension)
**Model Track**: A+C+D VT, test floors below 0.33
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 152 grid found monotonic improvement as min_scale decreased from 0.75 → 0.33.
Is 0.33 the peak or does it continue down? This iteration extends the grid to
{0.10, 0.15, 0.20, 0.25, 0.30}.

## Success Criteria

IS Sharpe must exceed 0.33's 1.3320 to justify a new config.
