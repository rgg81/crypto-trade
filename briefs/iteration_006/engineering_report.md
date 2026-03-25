# Engineering Report: Iteration 006

## Implementation

No code changes. Runner script sets `n_trials=100` (from 50).

## Results

- 50,168 total trades (vs 54,100 in iter 004)
- 6,638 OOS trades (vs 6,831)
- Win rate: 32.6% vs 32.9% (-0.3pp)
- OOS Sharpe: -2.34 vs -1.91 (worse)
- Runtime: ~12,000s (2x iter 004)
