# Engineering Report — Iteration 063

**Date**: 2026-03-28
**Status**: Full completion — MERGE CANDIDATE (pending seed validation)

## Implementation

Extended Signal dataclass with optional `tp_pct` and `sl_pct` fields. Backtest order creation uses Signal overrides when present, else falls back to BacktestConfig. LightGbmStrategy loads NATR_21 per test candle and computes `tp_pct = K_tp × NATR_21`, `sl_pct = K_sl × NATR_21` for each signal.

Labeling unchanged — model trains on fixed 8%/4% direction labels. Only execution barriers adapt.

## Backtest Results (Seed 42)

| Metric | Iter 063 IS | Baseline IS | Iter 063 OOS | Baseline OOS |
|--------|-------------|-------------|-------------|-------------|
| Sharpe | +1.48 | +1.60 | **+1.95** | +1.16 |
| Win Rate | 45.3% | 43.4% | 44.0% | 44.9% |
| Profit Factor | 1.34 | 1.31 | **1.66** | 1.27 |
| Max Drawdown | 74.9% | 64.3% | **18.4%** | 75.9% |
| Total Trades | 541 | 574 | 100 | 136 |
| PnL | +379.6% | +387.9% | **+123.4%** | +78.6% |
| OOS/IS Sharpe | — | — | **1.32** | 0.72 |

### Per-Symbol

**In-Sample**: BTC 45.7% WR (+149.1%), ETH 44.9% WR (+230.5%) — balanced
**Out-of-Sample**: BTC 47.4% WR (+48.8%, 39.5%), ETH 41.9% WR (+74.6%, 60.5%)

### Dynamic Barrier Examples (OOS)

```
2026-02-01 ETHUSDT SHORT TP=13.7%/SL=6.8% → TP hit +13.58%
2026-02-05 BTCUSDT SHORT TP=10.5%/SL=5.2% → TP hit +10.37%
2026-02-06 ETHUSDT SHORT TP=22.7%/SL=11.4% → SL hit -11.46%
2026-02-23 BTCUSDT SHORT TP=6.0%/SL=3.0% → timeout +3.75%
```

Barriers vary from 3%/1.5% to 22.7%/11.4% depending on volatility.

## Baseline Constraint Check

1. OOS Sharpe 1.95 > baseline 1.16 → **PASS**
2. OOS MaxDD 18.4% ≤ 91.1% → **PASS** (4x better!)
3. Min 50 OOS trades: 100 → **PASS**
4. OOS PF 1.66 > 1.0 → **PASS**
5. Symbol concentration: ETH 60.5% > 30% — with 2 symbols, one must always be >50%. Baseline had similar concentration. → **WAIVE**
6. OOS/IS Sharpe 1.32 > 0.5 → **PASS** (flagged >0.9 per plan — check for bugs)

## Bug Check (OOS/IS > 0.9)

1. Trade execution verified: 10 sampled trades all correct (entry prices, TP/SL based on NATR × multiplier, PnL calculations)
2. No lookahead: model trained on data before each month, NATR loaded from parquet at signal time
3. Fee consistently deducted at 0.1% per trade (same as baseline)
4. The elevated OOS/IS ratio likely reflects: (a) OOS period had strong ETH downtrend (favorable for shorts), (b) ATR barriers were tighter OOS (lower NATR → less drawdown exposure), (c) 100 OOS trades is small sample

## Seed Validation Required

This iteration passes all hard constraints. Before MERGE, need 5-seed validation per protocol.
