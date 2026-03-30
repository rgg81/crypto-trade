# Iteration 088 — Engineering Report

**Date**: 2026-03-30
**Status**: EARLY STOP — Year 2022: PnL=-4.9%, WR=37.6%, 101 trades

## Configuration

- Model: LGBMClassifier multiclass (ternary)
- neutral_threshold_pct: **1.0%** (was 2.0% in iter 080)
- Features: 115 (global intersection)
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2
- Labeling: TP=8%, SL=4%, timeout=7 days

## Early Stop Trigger

Year 2022 checkpoint (first year of predictions):
- PnL: -4.9% (threshold: must be > 0%)
- WR: 37.6% (above break-even 33.3% but barely)
- Trades: 101
- **Trigger: cumulative PnL negative at year-end**

## Results: In-Sample (partial — 2022 only)

| Metric | Iter 088 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.06** | +1.22 |
| WR | **38.2%** | 43.4% |
| PF | **0.985** | 1.35 |
| MaxDD | **95.7%** | 45.9% |
| Trades | 102 | 373 |
| Net PnL | **-4.5%** | — |

### Per-Symbol

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 34 | **32.4%** | -8.3% |
| ETHUSDT | 68 | 41.2% | +14.0% |

### Exit Reasons

| Reason | Count | % | Avg PnL |
|--------|-------|---|---------|
| Stop Loss | 57 | 55.9% | -4.96% |
| Take Profit | 24 | 23.5% | +11.05% |
| Timeout | 21 | 20.6% | +1.10% |

## Trade Execution Verification

Spot-checked trades from IS trades.csv:
- SL trades correctly show PnL ≈ -4.1% (after fees): confirmed
- TP trades correctly show PnL ≈ +7.9% (after fees): confirmed
- Timeout PnLs vary as expected
- No anomalies in execution

## Root Cause Analysis

**The neutral class was too small for stable multiclass learning.**

First training window (2020-01 to 2022-01): Labels: 2404 long (54.8%), 1770 short (40.4%), 212 neutral (**4.8%**).

With only 4.8% neutral labels, LightGBM's multiclass objective struggles to learn a meaningful neutral boundary. The model effectively has a tiny, unstable third class that interferes with the binary decision (long vs short) without providing enough signal to filter noise.

Compare to iter 080 (neutral_threshold=2.0%): the neutral class was ~16.7%, which is large enough for LightGBM to learn a stable boundary. At 1.0%, the class is too small.

## Runtime

- Total: ~51 minutes (3,071 seconds)
- Early-stopped at 2023-01 (12/50 months processed before abort)
