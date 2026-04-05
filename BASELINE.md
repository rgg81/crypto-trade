# Current Baseline

Last updated by: iteration 145 (2026-04-05)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + vol-targeting post-processing).

**Combined portfolio**: Three independent LightGBM models (A=BTC+ETH, C=LINK, D=BNB)
running side-by-side, with **volatility-targeted position sizing** applied as a
post-processing rule. Each trade's size is scaled by `target_vol / realized_14d_vol`,
clipped to [0.5, 2.0].

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +2.33      |
| Sortino         | +3.01      |
| Win Rate        | 50.6%      |
| Profit Factor   | 1.53       |
| Max Drawdown    | 38.09%     |
| Total Trades    | 164        |
| Calmar Ratio    | 3.40       |
| Net PnL         | +129.5%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.36      |
| Win Rate        | 44.5%      |
| Profit Factor   | 1.30       |
| Max Drawdown    | 100.43%    |
| Total Trades    | 652        |
| Net PnL         | +308.7%    |

## Per-Symbol OOS Performance

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| BNBUSDT | D | 50 | 52.0% | +47.5% | 36.6% |
| ETHUSDT | A | 34 | 55.9% | +37.4% | 28.9% |
| LINKUSDT | C | 42 | 52.4% | +36.3% | 28.0% |
| BTCUSDT | A | 38 | 42.1% | +8.3% | 6.4% |

## Strategy Summary

**Model A (BTC+ETH pooled)** — 196 features, ATR labeling 2.9×NATR / 1.45×NATR, 24mo training

**Model C (LINK)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

**Model D (BNB)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles,
CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model.

## Position Sizing (NEW in iter 145)

Applied as post-processing to trade outputs:

```
For each trade at open_time T:
    realized_vol = std(daily portfolio PnLs from [T - 14 days, T - 1 day])
    scale = 1.5 / realized_vol       (if realized_vol > 0 and ≥ 5 past days)
    scale = clip(scale, 0.5, 2.0)
    trade_pnl *= scale
```

Average OOS scale: 0.65 (portfolio ~35% deleveraged on average during OOS).

**IMPORTANT**: This rule is not yet in the backtest engine. For deployment, it must be
implemented in `src/crypto_trade/backtest.py` (set weight_factor at trade open time).

## Notes

**Iteration 145** — Vol-targeted position sizing applied to iter 138's A+C+D trades.

Walk-forward validation:
- Config tuned on IS trades only (24 configs tested)
- Best IS config: target_vol=1.5, lookback=14 days
- Applied to OOS without further tuning

Key improvements over iter 138:
- OOS Sharpe: +2.32 → **+2.33** (+0.4%, marginal)
- OOS MaxDD: 62.8% → **38.1%** (-39%, major)
- OOS Calmar: 2.74 → **3.40** (+24%)
- OOS PF: 1.49 → 1.53 (+3%)
- IS Sharpe: +1.15 → **+1.36** (+18%)

Tradeoffs:
- OOS Net PnL: +172.4% → +129.5% (smaller average position)
- OOS Sortino: +3.41 → +3.01 (-12%)
- Concentration shifted from LINK (34.4%) to BNB (36.6%) — still passes ≤50%

Previous baseline: iter 138 (OOS Sharpe +2.32, MaxDD 62.83%, A+C+D without sizing).
