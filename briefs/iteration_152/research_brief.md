# Iteration 152 Research Brief

**Type**: EXPLOITATION (VT min_scale tuning)
**Model Track**: A+C+D with tuned vol-targeting floor
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

The `min_scale=0.5` floor was a default choice when VT was introduced (iter 145).
It caps deleveraging at 50% of nominal — meaning during the worst vol spikes,
we still carry half a position. Is 0.5 the right floor?

**Hypothesis**: Lowering min_scale allows more aggressive risk-off during crashes
(e.g., July 2025). The scale hits the floor only during extreme vol events, so
lowering it only affects crash periods — not calm trading.

## Research Checklist Categories

### E. Trade Pattern Analysis
During July 2025, all models lost together. With min_scale=0.5, positions were
still 50% sized during that crash. If scaling could drop further (0.33 or 0.25),
exposure during systemic vol spikes would shrink proportionally.

### F. Statistical Rigor
Grid search over min_scale × max_scale combinations. IS-tune, OOS-apply. All
other VT params fixed at iter 151 values (target=0.3, lookback=45).

## Grid Tested

min_scale ∈ {0.25, 0.33, 0.50, 0.67, 0.75} × max_scale ∈ {1.5, 2.0, 3.0}

## Success Criteria

Primary: OOS Sharpe > +2.74 (iter 151 baseline)
All hard constraints must pass
