# Research Brief: 8H LightGBM Iteration 005

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- IS data only for design decisions; walk-forward on full dataset
- Monthly retraining, 12-month window, reports split at cutoff

## 1. Change from Iteration 004 (current baseline)

**Single variable change: lower TP/SL barriers from 4%/2% to 3%/1.5%.**

### Rationale

- Break-even WR is the same: SL/(TP+SL) = 1.5/4.5 = 33.3% (same 2:1 RR)
- EDA showed 94% resolution at 3%/1.5% vs 87% at 4%/2% — 7pp more trades resolve cleanly via TP/SL
- Fewer timeouts = less ambiguous labels = cleaner training signal
- Shorter average holding period = less exposure to noise and reversals
- Win rate at 32.9% is 1.1pp from break-even — cleaner labels may close the gap

### Parameters

| Parameter | Iter 004 | Iter 005 |
|-----------|---------|---------|
| TP | 4.0% | **3.0%** |
| SL | 2.0% | **1.5%** |
| Timeout | 4320min | 4320min (unchanged) |
| Fee | 0.1% | 0.1% |

### Affects both

- **Labeling**: `label_tp_pct=3.0, label_sl_pct=1.5` — changes how training labels are generated
- **Backtest execution**: `take_profit_pct=3.0, stop_loss_pct=1.5` — changes how trades are executed

## 2. Everything Else Unchanged

Top 50 symbols, all features, confidence threshold 0.50–0.65, monthly walk-forward, 50 Optuna trials, seed 42.
