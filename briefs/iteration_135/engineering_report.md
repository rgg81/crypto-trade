# Iteration 135 — Engineering Report

**Date**: 2026-04-04
**Type**: EXPLORATION (Model E screening: SOL standalone)
**Runner**: `run_iteration_135.py`
**Runtime**: 4246s (~1.2h)

## Implementation

Single model, iter 126 config template:
- Symbol: SOLUSDT
- Labeling: ATR-based TP=3.5x, SL=1.75x, timeout=7d
- Features: 185 auto-discovered
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- CV gap: 22 rows (22 × 1 symbol)

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +0.16 | +0.47 | 2.92 |
| Max Drawdown | 124.1% | 31.4% | 0.25 |
| Win Rate | 42.6% | 46.9% | 1.10 |
| Profit Factor | 1.05 | 1.19 | 1.13 |
| Total Trades | 141 | **32** | 0.23 |
| Net PnL | +20.1% | +15.1% | 0.75 |

## Model E Screening — MARGINAL PASS

| Gate | Threshold | SOL | Pass? |
|------|-----------|-----|-------|
| IS Sharpe > 0 | > 0 | +0.16 | PASS (weak) |
| OOS Sharpe > 0 | > 0 | +0.47 | PASS |
| OOS WR > 33% | > 33% | 46.9% | PASS |
| OOS Trades ≥ 20 | ≥ 20 | 32 | PASS |
| IS/OOS ratio > 0.3 | > 0.3 | 0.34 | PASS (barely) |

SOL passes all gates but with much weaker signal than LINK or BNB. Only 32 OOS trades (below 50 hard constraint for portfolio merge). IS PF 1.05 is essentially break-even.
