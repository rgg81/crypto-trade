# Engineering Report: Iteration 005

## Implementation

No code changes. Runner script uses TP=3.0%, SL=1.5% in both BacktestConfig and LightGbmStrategy params.

## Results

- 53,240 total trades (vs 54,100 in iter 004) — similar count
- 11,955 OOS trades (vs 6,831) — 75% more
- Win rate dropped: 30.2% vs 32.9% (-2.7pp)
- OOS Sharpe collapsed: -5.96 vs -1.91
- Runtime: ~7,000s (similar to iter 004)
