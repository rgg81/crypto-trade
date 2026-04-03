# Iteration 134 — Engineering Report

**Date**: 2026-04-04
**Type**: EXPLOITATION (MILESTONE: A+C+D portfolio — BTC/ETH + LINK + BNB)
**Runner**: `run_iteration_134.py`
**Runtime**: ~5.7h (Model A: 9377s, Model C: 5623s, Model D: 5724s)

## Implementation

Three independent models, trades concatenated and sorted by close_time:

### Model A (BTC/ETH)
- Symbols: BTCUSDT, ETHUSDT | Features: 196 | CV gap: 44 | Static 8%/4%, ATR exec 2.9x/1.45x

### Model C (LINK)
- Symbols: LINKUSDT | Features: 185 | CV gap: 22 | ATR labeling 3.5x/1.75x

### Model D (BNB)
- Symbols: BNBUSDT | Features: 185 | CV gap: 22 | ATR labeling 3.5x/1.75x

All models: 5-seed ensemble [42, 123, 456, 789, 1001], 50 Optuna trials, 5 CV folds.

## Label Leakage Audit

- Model A: CV gap = 44 (22 × 2 symbols). Verified.
- Model C: CV gap = 22 (22 × 1 symbol). Verified.
- Model D: CV gap = 22 (22 × 1 symbol). Verified.

## Determinism Verification

Per-symbol OOS results match standalone runs:
- BTC: 52 trades, 38.5% WR, +16.8% ✓ (iter 129)
- ETH: 55 trades, 45.5% WR, +52.1% ✓ (iter 129)
- LINK: 42 trades, 52.4% WR, +56.0% ✓ (iter 129)
- BNB: 50 trades, 52.0% WR, +37.7% ✓ (iter 132)

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | 0.59 | **1.94** | 3.27 |
| Sortino | 0.71 | 3.04 | 4.31 |
| Max Drawdown | 233.0% | 79.7% | 0.34 |
| Win Rate | 42.5% | **46.7%** | 1.10 |
| Profit Factor | 1.11 | 1.38 | 1.24 |
| Total Trades | 666 | **199** | 0.30 |
| Calmar | 0.84 | 2.04 | 2.44 |
| Net PnL | +195.0% | **+162.6%** | 0.83 |

### OOS Per-Symbol

| Symbol | Model | Trades | WR | Net PnL | % of Total |
|--------|-------|--------|----|---------|------------|
| LINKUSDT | C | 42 | 52.4% | +56.0% | 34.4% |
| ETHUSDT | A | 55 | 45.5% | +52.1% | 32.0% |
| BNBUSDT | D | 50 | 52.0% | +37.7% | 23.2% |
| BTCUSDT | A | 52 | 38.5% | +16.8% | 10.3% |

## Seed Validation

All three models use 5-seed ensembles internally. Combined results are deterministic (verified via standalone comparison). No additional seed sweep required.
