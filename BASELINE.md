# Current Baseline

Last updated by: iteration 134 (2026-04-04)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic (5-seed ensemble per model).** All models use seeds [42, 123, 456, 789, 1001] — output is fully reproducible.

**Combined portfolio**: Three independent LightGBM models running side-by-side. Model A (BTC+ETH) + Model C (LINK) + Model D (BNB). Trades concatenated and sorted by close_time.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.94      |
| Sortino         | +3.04      |
| Win Rate        | 46.7%      |
| Profit Factor   | 1.38       |
| Max Drawdown    | 79.7%      |
| Total Trades    | 199        |
| Calmar Ratio    | 2.04       |
| Net PnL         | +162.6%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.59      |
| Win Rate        | 42.5%      |
| Profit Factor   | 1.11       |
| Max Drawdown    | 233.0%     |
| Total Trades    | 666        |
| Net PnL         | +195.0%    |

## Per-Symbol OOS Performance

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| LINKUSDT | C | 42 | 52.4% | +56.0% | 34.4% |
| ETHUSDT | A | 55 | 45.5% | +52.1% | 32.0% |
| BNBUSDT | D | 50 | 52.0% | +37.7% | 23.2% |
| BTCUSDT | A | 52 | 38.5% | +16.8% | 10.3% |

## Seed Validation

**Deterministic.** All models use 5-seed ensembles with identical seeds. Combined output is fully reproducible. Results verified identical across standalone and combined runs.

## Strategy Summary — Model A (BTC+ETH)

- Symbols: BTCUSDT + ETHUSDT
- Training: **24 months**
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9xNATR_21, SL=1.45xNATR_21
- Features: **196** (auto-discovery; includes entropy features from parquet)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 44 rows** (22 candles x 2 symbols)
- **Signal cooldown: 2 candles**
- ATR labeling: **disabled** (static TP/SL for labeling)

## Strategy Summary — Model C (LINK)

- Symbols: LINKUSDT
- Training: **24 months**
- Labeling: **ATR-based** — TP=3.5xNATR, SL=1.75xNATR, timeout=**7 days**
- Features: **185** (symbol-scoped auto-discovery)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 22 rows** (22 candles x 1 symbol)
- **Signal cooldown: 2 candles**
- ATR labeling: **enabled**

## Strategy Summary — Model D (BNB)

- Symbols: BNBUSDT
- Training: **24 months**
- Labeling: **ATR-based** — TP=3.5xNATR, SL=1.75xNATR, timeout=**7 days**
- Features: **185** (symbol-scoped auto-discovery)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 22 rows** (22 candles x 1 symbol)
- **Signal cooldown: 2 candles**
- ATR labeling: **enabled**

## Notes

**Iteration 134** — A+C+D portfolio adds BNB (Model D) to the existing A+C baseline. BNB was screened in iter 132 (IS +0.51, OOS +1.04) and is the second alt to pass all Model D gates after LINK. Symbol screening campaign: ADA (fail), XRP (fail), BNB (pass), DOT (fail).

Key improvements over iter 129 (A+C baseline):
- OOS Sharpe: +1.68 -> **+1.94** (+15%)
- OOS Net PnL: +124.9% -> **+162.6%** (+30%)
- OOS Trades: 149 -> **199** (+34%)
- OOS Win Rate: 45.0% -> **46.7%** (+1.7pp)
- OOS Calmar: 1.85 -> **2.04** (+10%)
- Max concentration: 44.8% -> **34.4%** (-10.4pp, major diversification improvement)

Tradeoffs:
- OOS MaxDD: 67.5% -> 79.7% (+18%, barely passes 1.2x gate at 81.0%)
- IS MaxDD: 233.0% -> 233.0% (unchanged from A+C, structural)

Previous baseline: iter 129 (OOS Sharpe +1.68, A+C portfolio: BTC+ETH+LINK, 149 trades).
