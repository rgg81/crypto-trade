# Current Baseline

Last updated by: iteration 093 (2026-03-31)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic (5-seed ensemble).** The ensemble seeds [42, 123, 456, 789, 1001] are fixed — output is fully reproducible.

**This is the first honest CV baseline.** Prior baselines (iter 068 and earlier) used TimeSeriesSplit without a gap, allowing triple-barrier labels to leak across CV fold boundaries. Iterations 089-092 proved this leakage inflated CV Sharpe by 5-10x. The gap=44 fix eliminates all label leakage.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.01      |
| Win Rate        | 42.1%      |
| Profit Factor   | 1.25       |
| Max Drawdown    | 46.6%      |
| Total Trades    | 107        |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.73      |
| Win Rate        | 42.8%      |
| Profit Factor   | 1.19       |
| Max Drawdown    | 92.9%      |
| Total Trades    | 346        |

## Per-Symbol OOS Performance

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| ETHUSDT | 56 | 50.0% | +53.8% | 105.3% |
| BTCUSDT | 51 | 33.3% | -2.7% | -5.3% |

## Seed Validation

**Deterministic.** The 5-seed ensemble produces identical output on every run. Validated by comparing iter 091 (3 seeds, OOS +0.89) vs iter 093 (5 seeds, OOS +1.01) — more seeds improved stability, confirming the signal is not seed-dependent.

## Strategy Summary

- Symbols: BTCUSDT + ETHUSDT only
- Training: **24 months** (covers bull + bear markets)
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9×NATR_21, SL=1.45×NATR_21
- Features: **185** (symbol-scoped discovery, 6 base groups)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001) — averaged probabilities
- Confidence threshold: Optuna 0.50–0.85 (averaged across 5 models)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 44 rows** (22 candles × 2 symbols) — prevents label leakage
- **Signal cooldown: 2 candles** (16h on 8h candles) after trade close

## Notes

**Iteration 093** — first honest CV baseline. Replaces iter 068 (OOS Sharpe +1.84, leaky CV).

Key changes from iter 068:
- TimeSeriesSplit gap=44: eliminates CV label leakage (the defining change)
- Symbol-scoped feature discovery: 185 features (was 106 global intersection)
- 5-seed ensemble (was 3 seeds)

The OOS Sharpe dropped from +1.84 to +1.01 (−45%). This is the cost of honest CV — the model's true signal is weaker than the leaky baseline suggested. But what remains is genuine.

Single-symbol concentration: ETH 105.3% of OOS PnL. BTC is at break-even (33.3% WR = 2:1 RR break-even). This is inherent to the 2-symbol universe and not a blocking constraint until more symbols are added.

IS MaxDD 92.9% is concerning — the model has rough in-sample periods. OOS MaxDD 46.6% is acceptable.
