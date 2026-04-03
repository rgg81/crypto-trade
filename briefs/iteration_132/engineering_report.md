# Iteration 132 — Engineering Report

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D screening: BNB standalone)
**Runner**: `run_iteration_132.py`
**Runtime**: 5724s (~1.6h)

## Implementation

Single model, iter 126 config template:
- Symbol: BNBUSDT
- Labeling: ATR-based TP=3.5x, SL=1.75x, timeout=7d
- Features: 185 auto-discovered
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV gap: 22 rows (22 × 1 symbol)

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified from logs.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | **+0.51** | **+1.04** | 2.03 |
| Sortino | +0.49 | +1.29 | 2.63 |
| Max Drawdown | 62.7% | 37.8% | 0.60 |
| Win Rate | 44.8% | **52.0%** | 1.16 |
| Profit Factor | 1.20 | 1.38 | 1.16 |
| Total Trades | 143 | **50** | 0.35 |
| Calmar | 0.99 | 1.00 | 1.01 |
| Net PnL | +62.1% | +37.7% | 0.61 |

## Model D Screening — PASS

| Gate | Threshold | BNB | Pass? |
|------|-----------|-----|-------|
| IS Sharpe > 0 | > 0 | +0.51 | **PASS** |
| OOS Sharpe > 0 | > 0 | +1.04 | **PASS** |
| OOS WR > 33% | > 33% | 52.0% | **PASS** |
| OOS Trades ≥ 20 | ≥ 20 | 50 | **PASS** |
| IS/OOS ratio > 0.3 | > 0.3 | 0.49 | **PASS** |

BNB is the second symbol (after LINK) to pass all 5 Model D qualification gates. Qualifies for portfolio combination testing.
