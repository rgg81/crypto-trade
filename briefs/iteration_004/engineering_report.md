# Engineering Report: Iteration 004

## Implementation Summary

No code changes to `src/`. Only the runner script uses a hardcoded top-50 symbol list instead of `select_symbols()`.

## Changes

### `run_iteration_004.py` (new)
- Hardcoded `TOP_50_SYMBOLS` tuple ranked by IS quote volume
- Everything else identical to iter 002 runner

## Results

- 54,100 total trades (vs 195,642 in iter 002) — 72% fewer
- 6,831 OOS trades (vs 26,545) — 74% fewer
- Win rate improved: 32.9% vs 30.7% (+2.2pp)
- OOS Sharpe: -1.91 vs -1.96 (slightly better)
- OOS MaxDD: 997% vs 5,079% (5x better)
- Runtime: ~6,000s (vs ~17,000s) — 2.8x faster
