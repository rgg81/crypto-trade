# Current Baseline

Last updated by: iteration 138 (2026-04-05)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic (5-seed ensemble per model).** All models use seeds [42, 123, 456, 789, 1001] — output is fully reproducible.

**Combined portfolio**: Three independent LightGBM models running side-by-side. Model A (BTC+ETH) + Model C (LINK) + Model D (BNB). Trades concatenated and sorted by close_time.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +2.32      |
| Sortino         | +3.41      |
| Win Rate        | 50.6%      |
| Profit Factor   | 1.49       |
| Max Drawdown    | 62.8%      |
| Total Trades    | 164        |
| Calmar Ratio    | 2.74       |
| Net PnL         | +172.4%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.15      |
| Win Rate        | 44.5%      |
| Profit Factor   | 1.23       |
| Max Drawdown    | 157.1%     |
| Total Trades    | 652        |
| Net PnL         | +376.5%    |

## Per-Symbol OOS Performance

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| ETHUSDT | A | 34 | 55.9% | +60.2% | 34.9% |
| LINKUSDT | C | 42 | 52.4% | +56.0% | 32.5% |
| BNBUSDT | D | 50 | 52.0% | +37.7% | 21.9% |
| BTCUSDT | A | 38 | 42.1% | +18.5% | 10.7% |

## Seed Validation

**Deterministic.** All models use 5-seed ensembles with identical seeds. Combined output is fully reproducible. Results verified identical across standalone and combined runs.

## Strategy Summary — Model A (BTC+ETH)

- Symbols: BTCUSDT + ETHUSDT
- Training: **24 months**
- Labeling: **ATR-based** — TP=2.9xNATR, SL=1.45xNATR, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9xNATR_21, SL=1.45xNATR_21
- Features: **196** (auto-discovery; includes entropy features from parquet)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 44 rows** (22 candles x 2 symbols)
- **Signal cooldown: 2 candles**
- ATR labeling: **enabled** (labeling and execution barriers aligned)

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

**Iteration 138** — Enables ATR labeling on Model A (BTC+ETH), aligning labeling barriers (2.9x/1.45x NATR) with execution barriers. Single boolean flag change: `use_atr_labeling=True`. Models C and D unchanged.

Key improvements over iter 134:
- OOS Sharpe: +1.94 -> **+2.32** (+20%)
- OOS WR: 46.7% -> **50.6%** (+3.9pp, first time above 50%)
- OOS MaxDD: 79.7% -> **62.8%** (-21%, massive improvement)
- OOS Calmar: 2.04 -> **2.74** (+34%)
- OOS PF: 1.38 -> **1.49** (+8%)
- IS Sharpe: +0.59 -> **+1.15** (+95%)

Tradeoff:
- OOS Trades: 199 -> 164 (-18%, fewer but higher quality)

The mechanism: ETH's static 4% SL was only 1.14× NATR — trivially triggered by noise. ATR labeling gives 1.45× NATR SL, providing adequate breathing room. ETH OOS WR jumped 45.5% → 55.9% (+10.4pp).

All three models now use ATR-based labeling. This is the new standard.

Previous baseline: iter 134 (OOS Sharpe +1.94, A+C+D portfolio, static labeling on Model A).
