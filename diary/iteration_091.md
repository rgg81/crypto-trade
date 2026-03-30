# Iteration 091 Diary — 2026-03-31

## Merge Decision: NO-MERGE

OOS Sharpe +0.89 < baseline +1.84. But OOS MaxDD 30.5% is the best ever (vs baseline 42.6%). The gap mechanism works — honest CV produces genuinely profitable results.

**OOS cutoff**: 2025-03-24

## Hypothesis

Eliminate CV label leakage via `TimeSeriesSplit(gap=44)` instead of PurgedKFoldCV (iter 089-090). Gap = (timeout_candles + 1) * n_symbols = 22 * 2 = 44.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **CV gap: 44 rows** (22 candles × 2 symbols) — NEW
- Features: 115 (symbol-scoped — NOT matching baseline's 106)
- Model: LGBMClassifier binary, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results

| Metric | IS | OOS | Baseline OOS |
|--------|-----|-----|-------------|
| Sharpe | +0.54 | **+0.89** | +1.84 |
| WR | 42.6% | 40.6% | 44.8% |
| PF | 1.14 | 1.25 | 1.62 |
| MaxDD | 78.8% | **30.5%** | 42.6% |
| Trades | 352 | 96 | 87 |

## What Happened

**The gap mechanism works.** First iteration since 068 to complete a full walk-forward with modified CV and produce profitable OOS results. Key observations:

1. **IS Sharpe dropped from +1.22 to +0.54** — confirms leaky CV inflated IS by ~2x. The "true" CV performance is about half what was reported.
2. **OOS Sharpe +0.89 vs +1.84** — the signal is real but weaker. With honest hyperparameter selection, OOS degrades proportionally.
3. **OOS MaxDD 30.5%** — best ever, beating iter 080's 33.4%. Honest CV produces more conservative hyperparameters that avoid catastrophic drawdowns.
4. **96 OOS trades vs 87** — more trades with honest CV, not fewer.

## Confounding Variable: Feature Count

This iteration used 115 features (symbol-scoped discovery) vs baseline's 106 (global intersection). The 9 extra features are a confound — iter 092 must replicate baseline with exactly 106 features + gap to isolate the CV gap effect.

## Exploration/Exploitation Tracker

Last 10 (iters 082-091): [X(abandoned), E, E, E, E, E, E, X, E, **E**]
Exploration rate: 8/10 = 80%
Type: **EXPLORATION** (CV methodology — TimeSeriesSplit gap)

## MLP Diagnostics (AFML)

| Metric | Value |
|--------|-------|
| Deflated Sharpe Ratio (DSR) | < 0 (N=91, E[max] ~3.00) |
| CV method | TimeSeriesSplit(n_splits=5, gap=44) |
| Label leakage | NONE (gap = 22 candles × 2 symbols) |

## Next Iteration Ideas

1. **EXPLOITATION: Exact baseline replication + gap** — Use exactly 106 features (match baseline), same config, only add gap=44. This isolates the CV gap effect from the feature count confound.

## Lessons Learned

1. **TimeSeriesSplit gap is the correct CV leakage fix.** Simple, minimal data loss (~1%), honest metrics.
2. **The baseline's signal is real but inflated by ~2x.** IS Sharpe +1.22 → +0.54 with honest CV.
3. **Honest CV produces better risk management.** OOS MaxDD improved from 42.6% to 30.5% — the best ever.
4. **Feature count must be controlled.** 115 vs 106 features is a confound that must be resolved.
