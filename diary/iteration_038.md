# Iteration 038 Diary - 2026-03-26 — EXPLOITATION (ROBUSTNESS TEST)

## Merge Decision: NO-MERGE
OOS Sharpe -1.15 with seed=123 (baseline +1.33 with seed=42).

## CRITICAL FINDING: STRATEGY IS SEED-DEPENDENT
The +1.33 OOS Sharpe at seed=42 does NOT hold with seed=123 (-1.15). This means:
1. The Optuna optimization is finding seed-specific hyperparameters that overfit to CV
2. The OOS result is partially luck, not pure signal
3. Any "improvement" we measure may just be seed noise

## Impact
- The last 21 iterations of NO-MERGE may have been measuring seed-specific noise, not real improvements
- The 106-feature, 0.85-threshold config may not be truly optimal — it's optimal FOR SEED 42
- To get robust results, we need to either:
  a) Average across multiple seeds (ensemble of Optuna runs)
  b) Use a fixed hyperparameter set (no Optuna per month)
  c) Reduce the Optuna search space to reduce seed sensitivity

## Next Iteration Ideas
1. **Multi-seed ensemble**: Run seed=42, 123, 456 and average predictions. If the signal is real, the ensemble should still be profitable.
2. **Fixed hyperparameters**: Find a good param set once, use it for all months. No monthly Optuna.
3. **Reduce Optuna search space**: Fix confidence threshold at 0.75, only optimize LightGBM params + training_days.

## Exploration/Exploitation Tracker
Last 10: [X, E, E, E, X, X, E, E, E, **X**] → 6/10 = 60%
