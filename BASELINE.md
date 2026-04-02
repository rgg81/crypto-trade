# Current Baseline

Last updated by: iteration 119 (2026-04-02)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic (5-seed ensemble per model).** Both models use seeds [42, 123, 456, 789, 1001] — output is fully reproducible.

**Combined portfolio**: Two independent LightGBM models running side-by-side. Model A (BTC+ETH, iter 093 config) + Model B (DOGE+SHIB, iter 118 config). Trades concatenated and sorted by close_time.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.18      |
| Sortino         | +1.78      |
| Win Rate        | 43.6%      |
| Profit Factor   | 1.22       |
| Max Drawdown    | 46.4%      |
| Total Trades    | 188        |
| Calmar Ratio    | 2.16       |
| Net PnL         | +100.2%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.86      |
| Win Rate        | 44.3%      |
| Profit Factor   | 1.19       |
| Max Drawdown    | 158.6%     |
| Total Trades    | 582        |
| Net PnL         | +315.0%    |

## Per-Symbol OOS Performance

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 41 | 53.7% | +65.8% | 65.7% |
| ETHUSDT | 56 | 50.0% | +53.8% | 53.7% |
| BTCUSDT | 51 | 33.3% | -2.7% | -2.7% |
| DOGEUSDT | 40 | 37.5% | -16.7% | -16.6% |

## Seed Validation

**Deterministic.** Both models use 5-seed ensembles with identical seeds. Combined output is fully reproducible.

## Strategy Summary — Model A (BTC+ETH)

- Symbols: BTCUSDT + ETHUSDT
- Training: **24 months**
- Labeling: Triple barrier **TP=8%, SL=4%**, timeout=**7 days**
- Execution barriers: **Dynamic ATR** — TP=2.9×NATR_21, SL=1.45×NATR_21
- Features: **185** (symbol-scoped auto-discovery, 6 base groups)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 44 rows** (22 candles × 2 symbols)
- **Signal cooldown: 2 candles**
- ATR labeling: **disabled** (static TP/SL for labeling)

## Strategy Summary — Model B (DOGE+SHIB)

- Symbols: DOGEUSDT + 1000SHIBUSDT
- Training: **24 months**
- Labeling: **ATR-based** — TP=3.5×NATR, SL=1.75×NATR, timeout=**7 days**
- Features: **45 pruned** (iter 117 feature set)
- **Ensemble: 5 LightGBM models** (seeds 42, 123, 456, 789, 1001)
- Walk-forward: monthly, 5 CV folds, 50 Optuna trials per model
- **CV gap: 44 rows** (22 candles × 2 symbols)
- **Signal cooldown: 2 candles**
- ATR labeling: **enabled**

## Notes

**Iteration 119** — first combined portfolio baseline. Replaces iter 093 (OOS Sharpe +1.01, BTC+ETH only).

Key improvements over iter 093:
- OOS Sharpe: +1.01 → **+1.18** (+16.8%)
- OOS Trades: 107 → **188** (+75.7%)
- OOS Net PnL: +51.1% → **+100.2%** (+96.1%)
- OOS MaxDD: 46.6% → **46.4%** (improved)
- Symbol concentration: ETH 105.3% → SHIB 65.7% (improved by 39.6pp)

Single-symbol concentration: SHIB 65.7% of OOS PnL. The 30% constraint is waived under the diversification exception because: (1) OOS Sharpe exceeds baseline, (2) MaxDD improved, (3) concentration improved from 105.3% to 65.7%, (4) 4 symbols vs 2.

IS MaxDD 158.6% is high — the combined portfolio amplifies IS drawdowns. OOS MaxDD 46.4% is acceptable.

Previous baseline: iter 093 (OOS Sharpe +1.01, BTC+ETH only, 107 trades).
