# Current Baseline

Last updated by: iteration 147 (2026-04-05)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + per-symbol vol-targeting post-processing).

**Combined portfolio**: Three independent LightGBM models (A=BTC+ETH, C=LINK, D=BNB)
running side-by-side, with **per-symbol volatility-targeted position sizing** applied
as a post-processing rule. Each trade's size is scaled by `target_vol / symbol_realized_30d_vol`,
clipped to [0.5, 2.0], where `symbol_realized_vol` is the std of that SYMBOL's daily PnL
over the past 30 days.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +2.65      |
| Sortino         | +3.81      |
| Win Rate        | 50.6%      |
| Profit Factor   | 1.62       |
| Max Drawdown    | 39.17%     |
| Total Trades    | 164        |
| Calmar Ratio    | 4.02       |
| Net PnL         | +157.5%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.26      |
| Win Rate        | 44.5%      |
| Profit Factor   | 1.27       |
| Max Drawdown    | 118.12%    |
| Total Trades    | 652        |
| Net PnL         | +303.4%    |

## Per-Symbol OOS Performance

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| LINKUSDT | C | 42 | 52.4% | +61.1% | 38.8% |
| ETHUSDT | A | 34 | 55.9% | +37.9% | 24.1% |
| BNBUSDT | D | 50 | 52.0% | +36.6% | 23.2% |
| BTCUSDT | A | 38 | 42.1% | +21.9% | 13.9% |

## Position Sizing (per-symbol, iter 147)

```
For each trade on symbol S at open_time T:
    symbol_daily_pnls = [daily aggregate PnL of S's trades for dates in [T-30d, T-1d]]
    if len(symbol_daily_pnls) >= 5 and std > 0:
        realized_vol = std(symbol_daily_pnls)
        scale = 0.5 / realized_vol
        scale = clip(scale, 0.5, 2.0)
    else:
        scale = 1.0
    trade_pnl *= scale
```

Average OOS scales per symbol:
- BTC: 0.82 (calmest asset)
- ETH: 0.76
- LINK: 0.75
- BNB: 0.73 (most volatile)

## Strategy Summary

**Model A (BTC+ETH pooled)** — 196 features, ATR labeling 2.9×NATR / 1.45×NATR, 24mo training

**Model C (LINK)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

**Model D (BNB)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles,
CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model.

**IMPORTANT**: Position sizing is not yet in backtest engine. For deployment, implement
per-symbol rolling vol at trade-open time in `src/crypto_trade/backtest.py`.

## Notes

**Iteration 147** — Upgraded from portfolio-wide (iter 145) to per-symbol vol targeting.
Each trade scales by ITS symbol's recent vol, not aggregate portfolio vol. This preserves
signal from calm symbols when other symbols are volatile.

Walk-forward validation:
- 20 configs tested on IS trades only
- Best IS config: target_vol=0.5, lookback=30 days
- Applied to OOS without further tuning

Key improvements over iter 145:
- OOS Sharpe: +2.33 → **+2.65** (+14%)
- OOS Sortino: +3.01 → **+3.81** (+27%)
- OOS Calmar: 3.40 → **4.02** (+18%)
- OOS PF: 1.53 → **1.62** (+6%)
- OOS PnL: +129.5% → **+157.5%** (+22%)

Tradeoffs:
- IS Sharpe: +1.36 → +1.26 (-7%, less IS scaling triggered)
- OOS MaxDD: 38.1% → 39.2% (+3%, marginal)

Previous baseline: iter 145 (OOS Sharpe +2.33, portfolio-wide vol targeting).
