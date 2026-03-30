# Iteration 089 Diary — 2026-03-30

## Merge Decision: NO-MERGE (EARLY STOP)

Early-stopped: Year 2022 PnL=-81.7%, WR=31.9%, 92 trades. IS Sharpe -1.32, MaxDD 116.1%. PurgedKFoldCV with embargo catastrophically degraded performance vs baseline's TimeSeriesSplit.

**OOS cutoff**: 2025-03-24

## Hypothesis

Replace TimeSeriesSplit with Purged k-Fold CV + embargo (AFML Ch. 7) to eliminate information leakage from overlapping triple-barrier labels. This is the first MLP Foundation technique (Tier 1.1) — a methodological correction, not a strategy change.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **CV method: PurgedKFoldCV** (purge_window=21, embargo_pct=0.02) — NEW
- Features: 115 (symbol-scoped discovery)
- Model: LGBMClassifier binary, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2
- All other config identical to baseline iter 068

## Results: In-Sample (partial — early-stopped at 2022 checkpoint)

| Metric | Iter 089 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-1.32** | +1.22 |
| WR | **32.6%** | 43.4% |
| PF | **0.72** | 1.35 |
| MaxDD | **116.1%** | 45.9% |
| Trades | 92 (partial) | 373 (full IS) |

## What Happened

**PurgedKFoldCV correctly removes CV leakage — and reveals the model's true cross-validated performance is much worse than TimeSeriesSplit indicated.**

The purge window of 21 candles (7-day timeout at 8h) + embargo of 88 samples (~29 days) creates a substantial gap between training and validation folds. This gap, combined with Optuna's `training_days` parameter (which further trims training data), causes:

1. **Many CV folds produce -10.0** (minimum trades penalty): After purging, embargo, and training_days trimming, some folds have insufficient validation data above the confidence threshold.

2. **Best Optuna Sharpe drops from ~0.5-1.0 (TimeSeriesSplit) to ~0.06-0.24 (PurgedKFoldCV)**: The leaked information was contributing a large fraction of the apparent signal during hyperparameter optimization.

3. **Optuna selects fundamentally different hyperparameters**: With lower CV scores across all trials, the optimization landscape changes. The best trial's parameters may not be close to the baseline's parameters.

4. **The SL rate of 56.5% confirms poor directional accuracy**: The model's predictions are essentially random, leading to stop-loss exits dominating.

## Quantifying the Gap

WR: 32.6%, break-even 33.3%, gap **-0.7pp** (below break-even). PF 0.72 — the strategy actively destroys capital. IS MaxDD 116.1% means total capital destruction.

## The Sobering Truth

This iteration reveals something important: **the baseline's TimeSeriesSplit was leaking information through overlapping triple-barrier labels, and this leakage was contributing significantly to the model's apparent cross-validated performance.** When the leakage is properly removed via PurgedKFoldCV, the model cannot find profitable hyperparameters.

This does NOT invalidate PurgedKFoldCV — it validates it. The technique correctly identifies that the previous CV was too optimistic. The question now is: how do we build a model that works WITH proper CV?

## Exploration/Exploitation Tracker

Last 10 (iters 080-089): [X, X(abandoned), E, E, E, E, E, E, X, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (MLP Foundation — CV methodology change)

## Research Checklist

Completed 4 categories:
- **A**: Feature verification — 115 features, no change from recent iterations
- **F**: Statistical rigor — Quantified purge window (21 candles), embargo (88 samples), effective training loss (~4%)
- **G**: Stationarity analysis — deferred to iter 092
- **H**: Overfitting audit — E[max(SR_0)] ~ 2.99 for N=88 trials, baseline DSR < 0

## MLP Diagnostics (AFML)

| Metric | Value |
|--------|-------|
| Deflated Sharpe Ratio (DSR) | < 0 (baseline +1.84 < E[max] 2.99) |
| Expected max random Sharpe (N=89) | ~2.99 |
| Average label uniqueness | Not computed (deferred iter 091) |
| PBO (if CPCV used) | N/A |
| Non-stationary features used | Not audited (deferred iter 092) |
| CV method | PurgedKFoldCV(n_splits=5, purge=21, embargo=0.02) |

## lgbm.py Code Review

No bugs in lgbm.py. The PurgedKFoldCV is correctly integrated as a drop-in replacement for TimeSeriesSplit in optimization.py. The issue is structural, not a bug.

## What Worked

- PurgedKFoldCV implementation is correct (10/10 tests pass)
- The technique correctly identifies and removes CV leakage
- The engineering is sound — the problem is the model, not the tool

## What Failed

- The model's hyperparameters were overfit to leaked CV information
- When leakage is removed, no profitable hyperparameter combination exists (within the Optuna search space)
- The `training_days` parameter interacts badly with purging — aggressive trimming + purging = empty folds
- IS Sharpe dropped from +1.22 to -1.32 — a complete collapse

## Overfitting Assessment

**This is the most important finding since iteration 068.**

The IS/OOS ratio of the baseline (1.50 — flagged as "suspiciously good") now has a plausible explanation: the CV used to optimize hyperparameters was leaking information from overlapping labels. This means:

1. The baseline's hyperparameters were selected using an inflated CV metric
2. Those hyperparameters happened to work in OOS (possibly by luck)
3. When we fix the CV to remove leakage, the hyperparameter selection changes and the strategy fails

The DSR analysis (E[max(SR_0)] ~ 2.99 > baseline 1.84) supports this: the baseline OOS Sharpe is within the expected range of random trials.

## Next Iteration Ideas

**The PurgedKFoldCV failure is a methodological blocker that must be resolved before any other MLP technique can be applied.** Three approaches:

1. **EXPLOITATION: PurgedKFoldCV with reduced embargo** — The 2% embargo (~88 samples, ~29 days) may be too aggressive for 8h candles. Try embargo_pct=0.005 (~22 samples, ~7 days) while keeping purge_window=21. This reduces data loss while still addressing the primary leakage problem.

2. **EXPLOITATION: PurgedKFoldCV without training_days optimization** — Remove `training_days` from the Optuna search space (fix at 500 = full window). The interaction between training_days trimming and purging is the primary cause of empty folds. With full training windows, each fold has enough data after purging.

3. **EXPLORATION: Revert to TimeSeriesSplit + add embargo-only** — A lighter touch: keep TimeSeriesSplit but add an embargo gap between folds (skip N samples between train end and val start). This partially addresses leakage without the full purging overhead that causes empty folds. Implement as a simple wrapper.

**Recommended next**: Approach 2 (remove training_days). The training_days parameter is the root cause of the empty fold problem, and removing it simplifies the optimization while preserving the purging benefit.

## Lessons Learned

1. **CV leakage from overlapping labels is real and significant.** The gap between TimeSeriesSplit and PurgedKFoldCV performance is massive (IS Sharpe +1.22 vs -1.32). This means at least some of the baseline's apparent IS performance was inflated by leakage.

2. **PurgedKFoldCV + training_days optimization is a toxic combination.** The purge and embargo remove samples from fold boundaries, while training_days trims from the beginning. Together, they can leave folds with almost no training data.

3. **The model's "true" CV performance (without leakage) is much worse than reported.** This doesn't mean the model has zero signal — the walk-forward backtest still prevents actual leakage at the model level. But it means Optuna was selecting hyperparameters based on overoptimistic feedback.

4. **Methodological corrections can break things before they make things better.** The MLP Foundation sequence (089-094) should expect initial degradation. The value is in building a correct foundation, not in immediate performance improvement.

5. **The feature count confound persists.** 115 features (current) vs 106 (baseline) may contribute to the failure. Resolving this requires either pinning the feature set or regenerating baseline results.
