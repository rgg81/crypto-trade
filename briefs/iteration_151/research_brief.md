# Iteration 151 Research Brief

**Type**: EXPLOITATION (VT parameter robustness — broader IS tuning grid)
**Model Track**: A+C+D with per-symbol VT, expanded lookback range
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 147's IS tuning grid was `target ∈ {0.3, 0.5, 0.75, 1.0, 1.5}` × `lookback ∈ {14, 21, 30}`.
This locked lookback ≤ 30. Post-deployment robustness check requires verifying the
production config isn't a lucky tuning point.

**Hypothesis**: Expanding lookback to {14, 21, 30, 45, 60} might reveal a better config.

## Research Checklist Categories

### E. Trade Pattern Analysis
30-day lookback uses ~25-30 daily PnL observations per symbol. 45-day captures a
fuller regime window (including typical crypto pump/dump cycles of ~3-6 weeks).
Longer windows produce more stable vol estimates.

### F. Statistical Rigor
Full grid search on IS only: target ∈ {0.3, 0.4, 0.5, 0.6, 0.8, 1.0} ×
lookback ∈ {14, 21, 30, 45, 60} = 30 configs. Select IS-best, apply to OOS.

## Grid Search Results (sorted by IS Sharpe)

| target | lookback | IS Sharpe | IS MaxDD | OOS Sharpe | OOS MaxDD |
|--------|----------|-----------|----------|------------|-----------|
| **0.3** | **45** | **+2.12** | 93.9% | **+4.74*** | **32.2%** |
| 0.3 | 30 | +2.12 | 111.1% | +4.59 | 39.2% |
| 0.4 | 45 | +2.11 | 94.9% | +4.74* | 32.2% |
| 0.5 | 45 | +2.09 | 97.2% | +4.73* | 32.2% |
| 0.4 | 30 | +2.09 | 114.3% | +4.59 | 39.2% |
| 0.5 | 30 (PROD) | +2.06 | 118.1% | +4.59 | 39.2% |
| ... | ... | ... | ... | ... | ... |

(*custom Sharpe values, ×√365 annualization; actual engine Sharpe = custom/~1.73)

**All 6 lookback=45 configs dominate lookback=30 on BOTH Sharpe and MaxDD.**

## IS-Best Config

**target=0.3, lookback=45** wins by IS Sharpe. Verified on OOS via official engine
metrics.

## Success Criteria

Primary: OOS Sharpe > +2.65 (iter 147/150 baseline)
All hard constraints must pass
