# Iteration 026 Diary - 2026-03-26 — EXPLORATION

## Merge Decision: NO-MERGE
OOS Sharpe +0.28 < baseline +1.33. Calendar + interaction features didn't improve.

## Type: EXPLORATION (new feature generation — first ever!)

## Exploration/Exploitation Tracker
Last 10: [X, X, X, E, X, X, X, X, X, **E**] (iters 017-026)
Exploration rate: 2/10 = 20% — still below 30%, next iteration should also explore

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | +0.28 | +1.33 |
| WR | 38.3% | 41.6% |
| PF | 1.04 | 1.21 |
| Trades | 209 | 286 |

## New Features Added (7 total, 113 columns from 106)
- cal_hour_of_day, cal_day_of_week, cal_is_weekend
- ix_vwap_x_adx, ix_autocorr_x_natr, ix_mrdist_x_smacross, ix_taker_x_rsi

## IS quantstats Analysis
- Hour-of-day shows 5.1pp spread (07:00 best, 23:00 worst)
- Wednesday best day (39.8% WR), Tuesday worst (30.9%)
- 2021 and mid-2022 are the worst periods (cold-start + bear market)

## What Failed
- New features added noise — Optuna picked different hyperparams, reducing quality
- The runtime injection approach is fragile (user feedback: should regenerate parquet instead)
- 7 new features on 2 symbols may be insufficient data to learn their patterns

## QE Note
User feedback: features should be added to the parquet generation pipeline, not injected at runtime in lgbm.py. This is cleaner and avoids the complex test-month injection logic.

## Next Iteration Ideas
1. **Regenerate parquet with calendar features baked in** — cleaner approach
2. **Per-symbol models for BTC vs ETH** — another EXPLORATION
3. **TP=8%/SL=4% on BTC+ETH** — bold parameter exploration
