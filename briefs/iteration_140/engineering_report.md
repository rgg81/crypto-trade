# Iteration 140 Engineering Report

**Role**: QE
**Config**: Model A with colsample_bytree_max=0.5

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +0.74 | **-0.35** |
| WR | 41.9% | 37.1% |
| PF | 1.20 | 0.91 |
| MaxDD | 76.8% | 67.6% |
| Trades | 322 | 89 |
| Net PnL | +142.9% | -18.9% |

## Comparison with Iter 138 Baseline

| Metric | Baseline (iter 138) | Iter 140 | Change |
|--------|---------------------|----------|--------|
| IS Sharpe | +1.14 | +0.74 | **-35%** |
| OOS Sharpe | +1.67 | **-0.35** | **complete collapse** |
| IS WR | 45.1% | 41.9% | -3.2pp |
| OOS WR | 48.6% | 37.1% | **-11.5pp** |
| OOS PF | 1.60 | 0.91 | **below 1.0** |

## Per-Symbol OOS

| Symbol | Trades | WR | Net PnL |
|--------|--------|-----|---------|
| BTCUSDT | 45 | 42.2% | +11.9% |
| ETHUSDT | 44 | **31.8%** | -30.8% |

ETH's OOS WR dropped from 55.9% to 31.8% — a 24.1pp collapse. BTC held steady (42.1% → 42.2%).

## Label Leakage Audit

- CV gap = 44 (22 × 2 symbols). Verified unchanged.

## Runtime: 7,918s (~132 min)
