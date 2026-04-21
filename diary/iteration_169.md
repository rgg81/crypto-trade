# Iteration 169 Diary

**Date**: 2026-04-21
**Type**: EXPLORATION (per-symbol Model A — BTC alone)
**Decision**: **NO-MERGE (EARLY STOP)** — per-symbol BTC with full feature set is not viable

## Results

| Metric | Pooled Model A (BTC contribution) | BTC stand-alone | Δ |
|---|---:|---:|---|
| IS WR | 46.4% | 36.6% | -9.8 pp |
| IS PnL | +68.98% | -11.38% | -80 pp |
| Year-1 PnL | (positive by construction) | -38.2% | FAIL |

## Root Cause

**Samples-per-feature ratio collapse**:

| Config | Samples | Features | Ratio |
|---|---:|---:|---:|
| Pooled BTC+ETH Model A | ~4,400 | 193 | 22 (dangerous) |
| BTC stand-alone | ~2,200 | 193 | **11 (catastrophic)** |

Iter 078 and iter 094 each observed the same failure mode at ratio ~20. At ratio 11, the model has almost no chance — every feature gets plenty of opportunities to fit noise, and there aren't enough samples to identify which features are stable across regimes.

## Research Checklist

- **B — Architecture**: Option B (per-symbol) tested; fails at the 193-feature level. Option A (pooled) remains the viable architecture for BTC+ETH unless feature count is drastically reduced.
- **A — Feature Contribution**: not executed in this iteration. Would be the next step if pursuing per-symbol seriously.

## Exploration/Exploitation Tracker

Window (160-169): [X, E, E, E, E, E, X, E, E, E] → **8E / 2X**. After 5 straight exploration iterations (164-169), the next iteration should be EXPLOITATION to rebalance — ideally with a high-signal expected outcome.

## Lessons Learned

1. **Feature pruning before per-symbol, not after** — the skill's checklist A1 ("MANDATORY before adding features") is the right place to start if per-symbol is the goal. Trying per-symbol at baseline feature count is a predictable failure.

2. **Fail-fast continues to deliver** — 23 min vs. 90 min. Four consecutive fast rejections (AVAX, ATOM, DOT, BTC-standalone) total ~62 min of compute.

3. **Over-exploration signal** — 5 consecutive EXPLORATION iterations without a win. The 70/30 rule says time to exploit a known winner for a cycle. Options:
   - Revisit the baseline config for tuning (confidence threshold range, Optuna trial count)
   - Extend LTC with the new best practices (the current successful path)

## Next Iteration Ideas

### 1. Iter 170 (EXPLOITATION, highest priority) — Confidence-threshold study for the LTC model

LTC is the success story of the last 5 iterations. Confirm it's being run at its optimal confidence threshold. Optuna picks per-month thresholds from its search space; narrowing or shifting the search range is a cheap exploitation test. Expected cost: single 90-min LTC rerun with a tighter confidence-threshold range.

### 2. Iter 171 — Screen AAVE (different sector)

The three alt-L1 rejections (AVAX/ATOM/DOT) shared a 2022 bear-market failure mode. AAVE is DeFi — different narrative cycle, different beta. Different sector candidate may succeed where alt-L1s failed. Same Gate 3 protocol.

### 3. Iter 172 — If per-symbol is re-attempted, start with FEATURE PRUNING

Skill A1 protocol: train reference Model A, extract feature importances, prune to 30-50 features, then try per-symbol BTC with the pruned set. Not recommended until the exploration ratio is rebalanced.

### 4. Iter 170+ alternative — Rebalance to EXPLOITATION

With exploration rate at 80% over the last 10 iterations, the skill's 70/30 rule indicates the next 2-3 iterations should be EXPLOITATION. Options that qualify:
- Tighten VT parameters (but we're already on iter-152's tuned values)
- Try Model D's ATR multipliers on LTC (LTC currently uses 3.5/1.75 same as old D; could try 2.9/1.45)
- Tune Optuna search space for Model A (smaller trial budget to reduce overfitting)

Any of these is < 2× parameter change, so all are EXPLOITATION-tagged.

## lgbm.py Code Review

No changes this iteration. Prior-iteration findings carry (dead `self.seed` parameter, pending future cleanup).
