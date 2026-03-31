# Iteration 096 Diary — 2026-03-31

## Merge Decision: NO-MERGE

Not worse, but not better. Identical to baseline — no reason to merge.

**OOS cutoff**: 2025-03-24

## Hypothesis

Test the Sharpe overflow fix in isolation (no feature changes) to quantify its effect.

## Results

All metrics identical to baseline (iter 093):
- IS: Sharpe +0.73, WR 42.8%, PF 1.19, 346 trades
- OOS: Sharpe +1.01, WR 42.1%, PF 1.25, 107 trades

The Sharpe overflow fix changed nothing. The bug was a rare edge case (1 month × 1 seed) that the 5-seed ensemble already diluted.

## Key Insight: Feature Pruning Was the Problem, Not the Bug

Iterations 094-095 failed catastrophically, but the cause was entirely the feature pruning — not the Sharpe overflow bug or any other change. Iter 096 confirms the baseline is reproducible with the bug fix. This means:

1. **185 features are essential** — the walk-forward pipeline is tightly coupled to this feature set
2. **Future improvements must change training/labeling/architecture, not features**
3. **The Sharpe overflow fix is benign** — keep it for correctness but don't expect impact

## Exploration/Exploitation Tracker

Last 10 (iters 087-096): [E, X, E, E, E, X, E, X, E, **X**]
Exploration rate: 6/10 = 60%
Type: **EXPLOITATION** (bug fix isolation test)

## Next Iteration Ideas

The feature pruning avenue is definitively closed (4 failed attempts: 061, 073, 094, 095). The bug fix had zero impact. What's left:

1. **EXPLORATION: Sample uniqueness weighting (AFML Ch. 4)** — Next MLP technique. Overlapping triple-barrier labels create non-independent observations. Uniqueness weights down-weight crowded label periods. Changes training signal, not features.

2. **EXPLORATION: Per-symbol models** — BTC 33.3% WR vs ETH 50.0% WR in OOS. Separate LightGBM per symbol with own Optuna optimization. Has been tried (iters 059, 078, 079) but never with the honest CV baseline (gap=44). Worth re-testing.

3. **EXPLORATION: Dynamic confidence threshold** — Instead of Optuna-fixed threshold, make it a function of market regime (NATR quartile, ADX level). High-confidence predictions in trending markets, lower threshold in choppy markets.

## Lessons Learned

1. **Baseline is deterministic and reproducible.** Same config + same seeds = same results. The Sharpe overflow fix is the only code change between iter 093 and 096, and it had zero effect.

2. **Feature pruning is dead (confirmed 4x).** Don't attempt it again. The model architecture (LightGBM + Optuna + walk-forward) depends on the full 185-feature set.

3. **Bug fixes should be isolated.** Running the bug fix alone (iter 096) was necessary to prove that iters 094-095 failed due to pruning, not the fix.
