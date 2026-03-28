# Iteration 066 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS Sharpe worse than baseline for both seeds tested. More Optuna trials causes IS overfitting.

**OOS cutoff**: 2025-03-24

## Hypothesis

Double Optuna trials (50 → 100) to reduce seed variance through more thorough optimization.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- All params identical to baseline (iter 063) EXCEPT n_trials=100 (was 50)
- Seeds tested: 42, 123

## Results

| Seed | IS Sharpe (066) | IS Sharpe (063) | OOS Sharpe (066) | OOS Sharpe (063) |
|------|----------------|----------------|-----------------|-----------------|
| 42   | **+1.55** | +1.48 | +1.72 | **+1.95** |
| 123  | **+1.23** | +1.00 | -0.22 | **+0.70** |

IS improved for both seeds. OOS degraded for both seeds. Classic optimization overfitting.

## What Happened

### 1. More trials = better IS fit = worse OOS generalization

With 100 trials, TPE finds parameters that score higher on the time-series CV. But these parameters are more tuned to the specific training data distribution, so they generalize less well. The 50-trial level was apparently the right balance.

### 2. IS MaxDD improved dramatically

Both seeds showed IS MaxDD ~51% (vs baseline 74.9%). This is because 100 trials found better regularization parameters. But the tighter IS fit came at the cost of OOS.

### 3. Seed variance was NOT reduced

| Metric | 066 (2 seeds) | 063 (5 seeds) |
|--------|--------------|--------------|
| Mean OOS Sharpe | +0.75 | +0.64 |
| OOS std | ~1.37 | 0.96 |

Variance actually INCREASED with more trials. Each seed now finds a more "locally optimal" but less generalizable solution.

## Baseline Constraint Check

Seed 42:
1. OOS Sharpe 1.72 < 1.95 → FAIL
2. OOS MaxDD 30.6% > 22.1% → HARD FAIL
3. 114 OOS trades → PASS
4. OOS PF 1.50 > 1.0 → PASS
5. OOS/IS 1.11 > 0.5 → PASS (but >0.9 flagged)

Seed 123: OOS Sharpe negative → FAIL

## lgbm.py Code Review

No code changes for this iteration. The optimization pipeline works correctly — more trials genuinely improve in-sample performance. The issue is fundamental: more hyperparameter search in a fixed data regime leads to overfitting.

## Exploration/Exploitation Tracker

Last 10 (iters 057-066): [E, E, E, E, X, X, E, X, E, X]
Exploration rate: 5/10 = 50%
Type: EXPLOITATION (n_trials change)

## Lessons Learned

1. **50 Optuna trials is near-optimal for this problem.** More trials → IS overfitting. Fewer trials → underfitting. 50 is the sweet spot.
2. **Seed variance comes from the PROBLEM, not the optimization.** Different seeds lead to different TPE search paths, which find different local optima. More trials just finds BETTER local optima, not the SAME optimum.
3. **To reduce seed variance, you need to change the architecture, not the search depth.** This confirms the user's ensemble idea.

## Next Iteration Ideas

After 3 consecutive NO-MERGE (064, 065, 066), full research is mandatory and parameter-only changes are banned.

**Top priority — per user suggestion:**

1. **EXPLORATION: Multi-seed ensemble** — Train 3 models with different seeds (42, 123, 789) per walk-forward month. Average predicted probabilities before applying confidence threshold. Ensemble prediction is mathematically guaranteed to reduce variance (law of large numbers). This addresses the root cause: seed variance comes from the optimization path, not the model.

   Implementation: In `_train_for_month`, run `optimize_and_train` 3 times with different seeds, store 3 models. In `get_signal`, predict with all 3 and average probabilities.

2. **EXPLORATION: Signal cooldown** — After opening a trade, don't predict opposite direction for N candles. Reduces prediction flip noise.

**Recommended**: Option 1 (ensemble). It's theoretically sound, directly addresses the identified weakness, and was suggested by the user.
