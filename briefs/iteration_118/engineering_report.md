# Iteration 118 — Engineering Report

**Date**: 2026-04-02
**QE Role**: Backtest execution, trade verification, report generation

## Configuration

| Parameter | Value |
|-----------|-------|
| Symbols | DOGEUSDT, 1000SHIBUSDT |
| Interval | 8h |
| Features | 45 (pruned, same as iter 117) |
| Training window | 24 months |
| CV | 5 folds, 50 Optuna trials |
| Ensemble | 5 seeds [42, 123, 456, 789, 1001] |
| Labeling | ATR: **TP=3.5×NATR, SL=1.75×NATR** (was 2.9x/1.45x) |
| Timeout | 7 days (10080 min) |
| Cooldown | 2 candles |
| Fee | 0.1% per trade |
| Position size | $1000 USD |

**Single variable changed**: `atr_tp_multiplier` 2.9→3.5, `atr_sl_multiplier` 1.45→1.75.

## Backtest Execution

- **Runtime**: 3507 seconds (~58 minutes)
- **Total trades**: 317 (236 IS + 81 OOS)
- **Walk-forward months processed**: 44
- **CV gap**: 44 rows (verified in all monthly logs)
- **No errors, no early stops**

## Results

### Comparison CSV

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|--------|-----------|---------------|--------------|
| Sharpe | +0.63 | **+0.73** | 1.17 |
| Sortino | +0.63 | +1.16 | 1.85 |
| Max Drawdown | 170.7% | 53.2% | 0.31 |
| Win Rate | 46.6% | 45.7% | 0.98 |
| Profit Factor | 1.19 | 1.20 | 1.00 |
| Total Trades | 236 | 81 | — |
| Calmar Ratio | 0.97 | 0.92 | 0.96 |
| Net PnL | +164.8% | +49.1% | — |

### Per-Symbol Performance

**In-Sample:**

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 115 | 51.3% | +125.9% | 76.4% |
| DOGEUSDT | 121 | 42.1% | +38.9% | 23.6% |

**Out-of-Sample:**

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 41 | 53.7% | +65.8% | 134.0% |
| DOGEUSDT | 40 | 37.5% | -16.7% | -34.0% |

### Exit Reason Analysis

**IS:**
| Exit | Count | % | Avg PnL |
|------|-------|---|---------|
| stop_loss | 107 | 45.3% | -7.60% |
| take_profit | 49 | 20.8% | +14.50% |
| timeout | 80 | 33.9% | +3.34% |

**OOS:**
| Exit | Count | % | Avg PnL |
|------|-------|---|---------|
| stop_loss | 39 | 48.1% | -6.04% |
| take_profit | 19 | 23.5% | +11.01% |
| timeout | 23 | 28.4% | +3.27% |

TP avg PnL increased from ~10% (iter 117 with 2.9x barriers) to +14.5% IS / +11.0% OOS with 3.5x barriers. SL avg PnL also increased in magnitude: -7.6% IS / -6.0% OOS (was ~-5% with narrower barriers). The trade-off is working as expected.

### Direction Split

**IS:** LONG 135 trades (43.7% WR, +97.8%), SHORT 101 trades (50.5% WR, +66.9%)
**OOS:** LONG 29 trades (31.0% WR, -19.2%), SHORT 52 trades (53.8% WR, +68.3%)

OOS shows strong SHORT directional bias. Longs are unprofitable (31% WR). This is consistent with the bearish meme market in 2025 post-ATH.

### IS Monthly PnL Summary

| Period | Months | Profitable | Net PnL |
|--------|--------|------------|---------|
| 2022 H2 | 6 | 4 | +107.0% |
| 2023 H1 | 6 | 3 | +32.3% |
| 2023 H2 | 6 | 0 | -45.9% |
| 2024 H1 | 6 | 5 | +83.4% |
| 2024 H2 | 6 | 3 | -12.4% |
| 2025 Q1 (IS) | 3 | 0 | -56.6% |

Best IS month: March 2024 (+79.2%). Worst IS month: June 2024 (-48.2%).

## Trade Execution Verification

10 OOS trades randomly sampled (seed=42). PnL calculation verified against entry/exit prices:

| Symbol | Dir | Entry | Exit | Reason | PnL | Calc PnL | Diff |
|--------|-----|-------|------|--------|-----|----------|------|
| DOGEUSDT | SHORT | 0.193020 | 0.168733 | take_profit | +12.58% | +12.58% | 0.0002% |
| 1000SHIBUSDT | LONG | 0.012516 | 0.011947 | timeout | -4.55% | -4.55% | 0.0000% |
| 1000SHIBUSDT | SHORT | 0.012544 | 0.012935 | stop_loss | -3.12% | -3.12% | 0.0017% |
| DOGEUSDT | SHORT | 0.230080 | 0.213160 | timeout | +7.35% | +7.35% | 0.0000% |
| 1000SHIBUSDT | SHORT | 0.013435 | 0.014135 | stop_loss | -5.21% | -5.21% | 0.0019% |
| 1000SHIBUSDT | SHORT | 0.012522 | 0.011488 | timeout | +8.26% | +8.26% | 0.0000% |
| DOGEUSDT | SHORT | 0.204190 | 0.217530 | stop_loss | -6.53% | -6.53% | 0.0001% |
| 1000SHIBUSDT | LONG | 0.007510 | 0.007056 | stop_loss | -6.04% | -6.05% | 0.0048% |
| DOGEUSDT | LONG | 0.179240 | 0.168232 | stop_loss | -6.14% | -6.14% | 0.0001% |
| DOGEUSDT | SHORT | 0.195430 | 0.209425 | stop_loss | -7.16% | -7.16% | 0.0000% |

**All trades verified** — max diff 0.005%, consistent with floating-point precision.

## Label Leakage Audit

- **CV gap**: 44 rows = (10080/480 + 1) × 2 = 22 × 2. Verified in all 44 monthly training logs ("CV gap: 44 rows").
- **TimeSeriesSplit**: `n_splits=5, gap=44` correctly applied.
- **Walk-forward**: Each month's model trains only on past klines. Training window is 24 months rolling. No future data leakage.
- **Label scanning**: ATR-based labels scan forward up to timeout (21 candles). Gap of 44 rows (22 per symbol) prevents any training label from seeing into validation folds.

## Code Changes

None. This iteration only changed configuration parameters (`atr_tp_multiplier`, `atr_sl_multiplier`) in `run_iteration_118.py`. No modifications to `src/` code.

## Anomalies

1. **IS MaxDD 170.7%** — significantly higher than iter 117 (90.5%). The wider barriers create larger per-trade losses during drawdown periods. The June 2024 IS drawdown (-48.2% in one month) is the primary driver.

2. **DOGE OOS WR 37.5%** — below the 2:1 break-even of 33.3% but barely profitable. With wider barriers, DOGE's marginal trades (that would have been small SL exits) become large SL exits.

3. **OOS LONG WR 31.0%** — the model's long predictions are consistently wrong in OOS. This is a regime issue: the OOS period (Mar 2025 → Feb 2026) is predominantly bearish for meme coins after the Nov 2024 ATH.
