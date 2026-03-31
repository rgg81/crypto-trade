# Engineering Report — Iteration 101

## Change Summary

Baseline reproduction with regenerated 185-feature parquets. Zero code changes.

## Parquet Restoration

During iter 100, BTC/ETH parquets were regenerated with ALL 8 feature groups (193 features). This broke the baseline because 8 extra features (calendar: 2, interaction: 6) acted as distractors.

**Fix**: Regenerated with only 6 groups (momentum, volatility, trend, volume, mean_reversion, statistical) — the same groups that produced the original baseline parquets. Result: 185 features, identical to baseline.

**First attempt (193 features)**: EARLY STOP, Year 2022: PnL=-26.5%, IS Sharpe -0.31.
**Second attempt (185 features)**: Full completion, IS Sharpe +0.73, OOS Sharpe +1.01.

## Results — EXACT BASELINE REPRODUCTION

| Metric | Iter 101 | Baseline (093) |
|--------|----------|----------------|
| IS Sharpe | +0.7339 | +0.7339 |
| OOS Sharpe | +1.0129 | +1.0129 |
| IS WR | 42.8% | 42.8% |
| OOS WR | 42.1% | 42.1% |
| IS MaxDD | 92.94% | 92.94% |
| OOS MaxDD | 46.57% | 46.57% |
| IS Trades | 346 | 346 |
| OOS Trades | 107 | 107 |
| IS PF | 1.1941 | 1.1941 |
| OOS PF | 1.2477 | 1.2477 |

All metrics match exactly. The 5-seed ensemble is fully deterministic — regenerated parquets with the same features produce identical models and identical trade sequences.

## Key Finding: Calendar and Interaction Features Are Harmful

The 8 features (2 calendar + 6 interaction) that were added in iters 070/072 and included in 193-feature parquets caused EARLY STOP in first attempt. These features were already tested and found harmful in their original iterations. Including them in parquets is dangerous.

**Rule for future parquet regeneration**: Use ONLY the 6 base groups: momentum, volatility, trend, volume, mean_reversion, statistical. Do NOT include calendar or interaction groups.

## Label Leakage Audit

Identical to baseline — CV gap=44, TimeSeriesSplit, walk-forward with monthly retraining. No changes.
