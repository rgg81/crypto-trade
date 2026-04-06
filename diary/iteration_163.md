# Iteration 163 Diary

**Date**: 2026-04-06
**Type**: EXPLORATION (retrain with entropy/CUSUM features)
**Decision**: **NO-MERGE** — entropy/CUSUM features catastrophically degrade OOS

## Results

| Metric | Baseline v0.152 | Iter 163 | Δ |
|--------|-----------------|----------|---|
| OOS Sharpe | **+2.83** | **+1.22** | **-57%** |
| OOS MaxDD | 21.81% | 37.15% | +70% |
| OOS WR | 50.6% | 45.1% | -5.5pp |
| OOS PF | 1.76 | 1.27 | -28% |
| IS Sharpe | +1.33 | +1.10 | -18% |

**Every metric degraded.** The 11 entropy/CUSUM features harmed the model.

## Root Cause

1. **Samples-per-feature ratio collapsed**: 204 features with ~4400
   samples → ratio 22. This is the iter 078 pathology (ratio 21 →
   catastrophic overfitting). The model can't learn 204 feature
   interactions reliably with 4400 samples.

2. **Entropy noise at small windows**: Shannon entropy from 10-candle
   bins has high variance — noisy feature creates noisy splits.

3. **CUSUM threshold not adaptive per-window**: Single global threshold
   (`median(rolling_std_50)`) doesn't adapt to walk-forward training
   windows. Creates regime-dependent artifacts.

## Hard Constraints

| Check | Threshold | Actual | Pass |
|-------|-----------|--------|------|
| OOS Sharpe > baseline | > +2.83 | +1.22 | **FAIL (-57%)** |
| OOS MaxDD ≤ 26.2% | ≤ 26.2% | 37.15% | **FAIL** |

## Research Checklist

- **A (Feature Contribution)**: A4 — 11 new features tested. All harmful.
  Feature count discipline violated (204 > 200 soft ceiling, ratio 22 <
  50 threshold). The skill explicitly warned about this:
  "iter 078: 185 features → ratio 21, catastrophic overfitting."

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, X, X, X, X, **E**, E, E] (iters 154-163)
Exploration rate: 5/10 = 50% ✓

## Lessons Learned

1. **Adding features without pruning is ALWAYS wrong.** This is the 4th
   time this lesson was reinforced (iter 078, 083, 094, now 163). The
   skill warns explicitly but the temptation to "just add novel features"
   persists.

2. **Entropy/CUSUM features need REPLACEMENT, not addition.** The right
   approach: add 11 ent_/cusum_ features AND prune 11+ existing features
   to keep total ≤ 193. Use importance ranking to identify displacement
   candidates.

3. **204 features is above the hard ceiling (200).** Should have been
   caught in the research brief review.

## Next Iteration Ideas

### 1. Retrain with entropy/CUSUM REPLACING bottom-11 features

Run feature importance on IS, identify the 11 least important features,
drop them, and replace with the 11 entropy/CUSUM features. Net count
stays at 193. This tests whether the NEW features carry signal while
maintaining the critical samples-per-feature ratio.

### 2. Retrain with ONLY entropy/CUSUM (11 features) for Model A

Extreme test: train a minimal LightGBM with ONLY the 11 entropy/CUSUM
features. If IS Sharpe > 0, there's signal. If IS Sharpe ≤ 0, the
features carry no predictive value and should be abandoned entirely.

### 3. Accept v0.152 as final, deploy to paper trading

After 163 iterations, the strategy is mature. Further feature
engineering without pruning will continue to fail. Paper trading
validates the strategy on truly live data — more valuable than more
backtesting.
