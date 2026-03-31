# Iteration 095 — Research Brief

**Type**: EXPLORATION (conservative pruning methodology + bug fix)
**Date**: 2026-03-31
**Previous**: Iteration 094 (NO-MERGE, EARLY STOP — aggressive MDA pruning 185→50 destroyed signal)

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Hypothesis

Iter 094's aggressive pruning (185→50) killed the model because tree models need correlated features for different split points. This iteration takes a conservative approach:

1. **Remove only near-perfect duplicates** (|Spearman r| ≥ 0.99): features that are mathematically identical (e.g., ROC ≡ return ≡ log_return, EMA_5 ≡ EMA_9 ≡ SMA_10). These provide no additional split information.
2. **Remove 3 harmful features** (MDA < -0.01 from iter 094 analysis): `trend_aroon_osc_50`, `trend_sma_cross_20_100`, `vol_bb_bandwidth_30`.
3. **Fix Optuna Sharpe overflow bug**: Add sanity cap to prevent degenerate trial selection.

**TWO variables changed**: feature count (185 → 145) and Sharpe overflow fix. The bug fix is a correctness issue, not a strategy change — it prevents Optuna from selecting degenerate trials with training_days=30.

## Research Checklist Categories

### Category A: Conservative Pruning Analysis

37 features dropped as near-perfect duplicates (|r| ≥ 0.99):
- 7 return/ROC duplicates (stat_return_* ≡ stat_log_return_* ≡ mom_roc_*)
- 4 Bollinger %B/z-score duplicates (vol_bb_pctb ≡ mr_bb_pctb ≡ mr_zscore)
- 10 EMA/SMA duplicates (all EMA/SMA with different periods are r>0.99 in pooled data)
- 5 ATR/NATR duplicates (ATR_5/7/10/14 all r>0.99 with ATR_21)
- 4 volatility estimator duplicates (Garman-Klass ≡ Parkinson at same period)
- 1 RSI duplicate (RSI_7 ≡ RSI_9, r=0.99)
- 6 other near-perfect duplicates

3 harmful features dropped (MDA < -0.01 from iter 094 MDA analysis):
- `vol_bb_bandwidth_30`: MDA=-0.053 (actively degrades predictions)
- `trend_sma_cross_20_100`: MDA=-0.014
- `trend_aroon_osc_50`: MDA=-0.012

### Category E: Bug Analysis

**Optuna Sharpe overflow (found in iter 094)**: When a CV fold has exactly 1 trade with std=0, `compute_sharpe_with_threshold` returns `mean/0 = inf`. Optuna then selects this degenerate trial. In iter 094 month 2023-01 seed 1001, this produced Sharpe=8.9e14 and selected training_days=30 (180 samples).

**Fix**: Return -10.0 if `|sharpe| > 100`. No real trading strategy achieves Sharpe > 100.

## Proposed Configuration (iter 095)

**UNCHANGED from iter 093**:
- Symbols: BTCUSDT + ETHUSDT
- Training: 24 months, walk-forward monthly
- Labeling: TP=8%, SL=4%, timeout=7 days, dynamic ATR barriers
- CV: 5 folds, gap=44, 50 Optuna trials
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

**CHANGED**:
- Features: 185 → 145 (conservative dedup + harmful removal)
- Bug fix: Sharpe overflow guard in `compute_sharpe_with_threshold()`

## Expected Outcome

- IS Sharpe ≥ +0.62 (within 15% of baseline +0.73)
- OOS Sharpe ≥ baseline +1.01 (fewer noisy features = better generalization)
- Samples/feature ratio: ~4,400/145 = 30 (improved from 24)
