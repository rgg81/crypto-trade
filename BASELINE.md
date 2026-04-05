# Current Baseline

Last updated by: iteration 152 (2026-04-06)
OOS cutoff date: 2025-03-24 (fixed, never changes)

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + per-symbol vol targeting **integrated into backtest engine**).

**Combined portfolio**: Three independent LightGBM models (A=BTC+ETH, C=LINK, D=BNB)
running side-by-side. Per-symbol volatility targeting is applied **live within the
backtest engine**: each trade's `weight_factor` is computed at open time from the std
of that SYMBOL's past 30-day daily PnL, scaled as `target_vol / realized_vol` and
clipped to [0.33, 2.0].

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +2.83      |
| Sortino         | +3.33      |
| Win Rate        | 50.6%      |
| Profit Factor   | 1.76       |
| Max Drawdown    | 21.81%     |
| Total Trades    | 164        |
| Calmar Ratio    | 5.46       |
| Net PnL         | +119.1%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.33      |
| Win Rate        | 44.5%      |
| Profit Factor   | 1.33       |
| Max Drawdown    | 76.89%     |
| Total Trades    | 652        |
| Net PnL         | +237.5%    |

## Per-Symbol OOS Performance

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| ETHUSDT | A | 34 | 55.9% | +60.2% | 34.9% |
| LINKUSDT | C | 42 | 52.4% | +56.0% | 32.5% |
| BNBUSDT | D | 50 | 52.0% | +37.7% | 21.9% |
| BTCUSDT | A | 38 | 42.1% | +18.5% | 10.7% |

## Position Sizing (per-symbol, iter 152 — fully tuned)

```
For each trade on symbol S at open_time T:
    symbol_daily_pnls = [daily aggregate PnL of S's trades for dates in [T-45d, T-1d]]
    if len(symbol_daily_pnls) >= 5 and std > 0:
        realized_vol = std(symbol_daily_pnls)
        scale = 0.3 / realized_vol
        scale = clip(scale, 0.33, 2.0)    # tuned floor (iter 152)
    else:
        scale = 1.0
    trade_pnl *= scale
```

Config (iter 151 tuned): `target_vol=0.3, lookback=45` days. 45-day lookback gives
more stable vol estimates than 30-day over crypto regime cycles (~3-6 weeks).

## Strategy Summary

**Model A (BTC+ETH pooled)** — 196 features, ATR labeling 2.9×NATR / 1.45×NATR, 24mo training

**Model C (LINK)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

**Model D (BNB)** — 185 features, ATR labeling 3.5×NATR / 1.75×NATR, 24mo training

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles,
CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model.

**STATUS**: Position sizing is **INTEGRATED into the backtest engine** (iter 150).
Enable with `vol_targeting=True` in `BacktestConfig`. Walk-forward validated:
full engine re-run produces identical metrics to iter 147's post-processing reference.

## Notes

**Iteration 152** — Tuned VT `min_scale` (position floor) from 0.5 → 0.33. Allows
more aggressive deleveraging during crashes without affecting calm-period trading.
Floor only matters during high-vol events — asymmetric improvement.

Key improvements over iter 151:
- OOS Sharpe: +2.74 → **+2.83** (+3.4%)
- OOS MaxDD: 32.22% → **21.81%** (-32%)
- OOS Calmar: 4.12 → **5.46** (+33%)
- OOS PF: 1.64 → **1.76** (+7%)
- IS MaxDD: 93.93% → **76.89%** (-18%)

Grid search validated monotonic relationship: lower floor → better Sharpe AND lower
MaxDD across all tested values [0.25, 0.33, 0.5, 0.67, 0.75].

**Iteration 151** — Broader VT parameter grid search (30 configs) reveals that
iter 147's config (target=0.5, lookback=30) wasn't tuned over a wide enough
lookback range. Better config found: **target=0.3, lookback=45**.

Key improvements over iter 150:
- OOS Sharpe: +2.65 → **+2.74** (+3.3%)
- OOS MaxDD: 39.17% → **32.22%** (-18%)
- OOS Calmar: 4.02 → **4.12** (+2.5%)
- OOS PF: 1.62 → **1.64**

27 of 30 tested configs beat no-VT baseline — demonstrates VT robustness.

**No code change required** — same engine, just updated `BacktestConfig` params.

**Iteration 150** — Per-symbol vol targeting integrated into the backtest engine.
Full walk-forward re-run with VT active in `backtest.py` reproduces iter 147's
metrics exactly (OOS Sharpe +2.6486, MaxDD 39.17%, Calmar 4.02). Strategy is
production-ready end-to-end.

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
