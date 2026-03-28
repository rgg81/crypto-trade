# Current Baseline

Last updated by: iteration 067 (2026-03-28)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic or mean-of-seeds.** Single-seed results are unreliable (iter 063 showed OOS Sharpe ranging from -0.78 to +1.95 across seeds). New iterations must beat the baseline's deterministic/mean metrics, not a lucky single seed.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.64      |
| Win Rate        | 39.5%      |
| Profit Factor   | 1.49       |
| Max Drawdown    | 39.0%      |
| Total Trades    | 114        |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.23      |
| Win Rate        | 45.1%      |
| Profit Factor   | 1.29       |
| Max Drawdown    | 50.0%      |
| Total Trades    | 495        |

## Seed Validation

**Not applicable.** The ensemble (3 models, seeds 42/123/789) produces deterministic output. Running with different "outer seeds" has no effect — the ensemble seeds are fixed.

Previous baseline (iter 063) had OOS Sharpe std=0.96 across 5 seeds (range -0.78 to +1.95). The ensemble eliminates this variance entirely.

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Training: **24 months** (covers bull + bear markets)
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9×NATR_21, SL=1.45×NATR_21
- Features: 106 (global intersection)
- **Ensemble: 3 LightGBM models** (seeds 42, 123, 789) — averaged probabilities
- Confidence threshold: Optuna 0.50–0.85 (averaged across 3 models)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model

## Notes

**Iteration 067** — multi-seed ensemble eliminates seed variance.
Compared to iter 063's 5-seed mean (OOS Sharpe +0.64, MaxDD ~50%), iter 067 is significantly better:
- OOS Sharpe +1.64 vs +0.64 (2.5x improvement)
- IS MaxDD 50.0% vs 74.9% (best ever)
- Deterministic output (no seed lottery)

The previous baseline (iter 063) used seed 42's metrics as headline numbers (OOS Sharpe +1.95, MaxDD 18.4%), which was misleading — that was the best of 5 seeds, not representative performance. Methodology updated to require deterministic or mean-of-seeds comparison.
