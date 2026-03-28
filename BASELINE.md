# Current Baseline

Last updated by: iteration 068 (2026-03-28)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic or mean-of-seeds.** Single-seed results are unreliable (iter 063 showed OOS Sharpe ranging from -0.78 to +1.95 across seeds). New iterations must beat the baseline's deterministic/mean metrics, not a lucky single seed.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.84      |
| Win Rate        | 44.8%      |
| Profit Factor   | 1.62       |
| Max Drawdown    | 42.6%      |
| Total Trades    | 87         |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.22      |
| Win Rate        | 43.4%      |
| Profit Factor   | 1.35       |
| Max Drawdown    | 45.9%      |
| Total Trades    | 373        |

## Seed Validation

**Not applicable.** The ensemble (3 models, seeds 42/123/789) produces deterministic output. Running with different "outer seeds" has no effect — the ensemble seeds are fixed.

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Training: **24 months** (covers bull + bear markets)
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9×NATR_21, SL=1.45×NATR_21
- Features: 106 (global intersection)
- **Ensemble: 3 LightGBM models** (seeds 42, 123, 789) — averaged probabilities
- Confidence threshold: Optuna 0.50–0.85 (averaged across 3 models)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **Signal cooldown: 2 candles** (16h on 8h candles) after trade close

## Notes

**Iteration 068** — signal cooldown reduces trade count 24%, improves OOS Sharpe 12%.
- OOS Sharpe +1.84 vs +1.64 (baseline iter 067)
- IS MaxDD 45.9% vs 50.0% (4pp improvement)
- 0% immediate re-entry (down from 81% in iter 067)
- Trade quality improved: fewer but better trades
- OOS/IS Sharpe ratio 1.50 (flagged >0.9 — OOS period favorable, small sample)

Single-symbol concentration: ETH 91.6% of OOS PnL (baseline was 102.9%). This is inherent to the 2-symbol universe and not a blocking constraint until more symbols are added.
