# Iteration 095 Diary — 2026-03-31

## Merge Decision: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022 PnL=-57.6%, WR=34.9%, 106 trades.

**OOS cutoff**: 2025-03-24

## Hypothesis

Conservative pruning (remove only |r|≥0.99 duplicates + 3 harmful features) would preserve signal while reducing feature count from 185 to 145.

## Results: In-Sample (EARLY STOP — partial)

| Metric | Iter 095 | Iter 094 | Baseline (093) |
|--------|----------|----------|----------------|
| Sharpe | **-0.83** | -1.46 | +0.73 |
| WR | 34.6% | 31.3% | 42.8% |
| PF | 0.82 | 0.71 | 1.19 |
| Trades | 107 | 115 | 346 |

## Gap Quantification

WR is 34.6%, break-even is 33.3%, gap is **+1.3 pp** (barely above break-even). But PF 0.82 means the model loses money despite positive WR — SL exits dominate. Baseline WR was 42.8%. To close the 8.2 pp gap, pruning must not be done.

## What Failed

1. **Even conservative pruning destroys signal.** Removing 40 features (37 near-perfect duplicates + 3 harmful) changed the optimization landscape enough to produce worse monthly models. The 185-feature baseline was co-optimized with Optuna — the features and hyperparameters are interdependent.

2. **Feature pruning is the wrong approach for this model.** Two consecutive failures (iter 094: 50 features → IS -1.46, iter 095: 145 features → IS -0.83) prove that explicit feature selection degrades LightGBM's performance in this pipeline. The model's `colsample_bytree` parameter (0.3-1.0) already does implicit feature selection per tree.

3. **The Sharpe overflow fix worked correctly** but was not enough to save the iteration.

## Exploration/Exploitation Tracker

Last 10 (iters 086-095): [E, E, X, E, E, E, X, E, X, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (pruning methodology + bug fix)

## What We Learned

1. **Feature pruning is definitively dead for this model.** Four pruning attempts across iterations (061: 50 features, 073: 60, 094: 50, 095: 145) all failed. The model architecture (LightGBM + Optuna + walk-forward) depends on having the full 185-feature set available. Feature count is not a knob to turn.

2. **The Sharpe overflow fix should be kept.** It prevents degenerate trial selection and costs nothing.

3. **Don't change the feature set.** Future iterations should change everything EXCEPT features: labeling, model architecture, symbols, execution logic, sample weighting.

## Next Iteration Ideas

After 2 consecutive EARLY STOPs (iters 094-095), must propose structural changes only.

1. **EXPLORATION: Keep 185 features + Sharpe overflow fix only.** Run the baseline with just the bug fix to quantify its isolated effect. This is the minimum viable change.

2. **EXPLORATION: Sample uniqueness weighting (AFML Ch. 4).** The next MLP technique in the queue. Overlapping triple-barrier labels create non-independent observations. Uniqueness weights down-weight crowded label periods. This changes the training signal, not the features.

3. **EXPLORATION: Per-symbol models.** BTC 33.3% WR vs ETH 50.0% WR in OOS. Fundamentally different dynamics that a pooled model cannot serve. This has been tried (iters 059, 078, 079) but always with other changes confounding the result. Try it with the honest CV baseline config.

## lgbm.py Code Review

The `feature_columns` parameter added in this iteration works correctly. It should be kept for future use (e.g., if walk-forward MDA is implemented). The Sharpe overflow fix in `optimization.py` is clean and correct.
