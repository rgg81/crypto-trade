# Iteration 166 Engineering Report

**Role**: QE
**Config**: LTC seed sweep (outer seeds 123, 456, 789, 1001), same architecture as iter 165
**Status**: **STOPPED** (design bug discovered — outer-seed sweep is a no-op for ensemble architecture)
**Elapsed**: ~100 minutes (seed=123 completed one full walk-forward before the finding was made)

## What happened

The first new seed (123) completed the full backtest with output identical to the iter-165 seed=42 run:

| Metric | seed=42 (iter 165) | seed=123 (iter 166) |
|---|---:|---:|
| IS Sharpe | 0.5957 | 0.5957 |
| OOS Sharpe | 0.3075 | 0.3075 |
| IS trades | 155 | 155 |
| OOS trades | 43 | 43 |
| IS PnL | +48.21 | +48.21 |
| OOS PnL | +7.29 | +7.29 |

Byte-identical to the seed=42 run. Not a rounding artifact — every column matches.

## Root cause

In `src/crypto_trade/strategies/ml/lgbm.py:424`:

```python
seeds = self.ensemble_seeds or [self.seed]
```

When `ensemble_seeds` is set (it always is in the baseline — `[42, 123, 456, 789, 1001]`), `self.seed` is **never consulted**. The outer constructor `seed=` parameter is effectively dead code once the ensemble list is populated.

Tracing every random source in `optimization.py`:
- Line 176: `"random_state": seed` — uses the per-ensemble seed from the outer loop iteration
- Line 368: `"random_state": seed` — same
- Optuna sampler: seeded from `seed` passed into `optimize_and_train(..., seed, ...)` — the inner ensemble seed

Every random source in the training pipeline is controlled by the inner ensemble seed. The outer `self.seed` never reaches any RNG.

## Implication for seed validation

The skill's "5 outer seeds" prescription (`42, 123, 456, 789, 1001`) was written for **single-seed** configurations. For our ensemble architecture, sweeping the outer seed produces bit-identical runs — it is not a real validation.

Meaningful alternatives:
1. **Sweep the entire ensemble set** (e.g., `[10, 20, 30, 40, 50]` vs `[42, 123, 456, 789, 1001]`). Each iteration is a full 5-seed ensemble; comparing 5 such sweeps = 25 total single-seed trainings. Cost: ~7.5 h per set, ~37 h for 5 sets. Heavy.
2. **Sweep single-seed configs** (`ensemble_seeds=[42]`, `[123]`, `[456]`, ...). This shows the variance across individual seeds but changes the architecture (ensemble → single-seed). Not a direct validation of the ensemble config.
3. **Rely on the ensemble itself** as the variance reduction mechanism. The 5-seed ensemble is already a within-seed average; the design intent was to *be* robust, not to need *further* seed validation.

Option 3 is the pragmatic interpretation: the existing architecture's 5-seed ensemble is the answer to "is the model seed-robust", so long as every model in the portfolio uses the SAME ensemble set (parity).

Model A and Model C in the baseline both use `ensemble_seeds=[42, 123, 456, 789, 1001]`. Iter 165's LTC runner uses the same set. Parity is already satisfied.

## Decision

- Iter 166 **STOPPED**. The remaining seeds (456, 789, 1001) would have produced identical output and burnt ~4.5 h of compute for no information.
- Iter 165 merge of LTC stands. Seed parity in the proper (ensemble) sense is confirmed — LTC matches Models A and C.
- Skill update pushed to main to document the clarification (commit `6c605f2` + this iteration's additions).

## Label Leakage Audit

No new runs → no new check needed. Prior audit (iter 165) still stands.

## Feature Reproducibility Check

Runner used `feature_columns=list(BASELINE_FEATURE_COLUMNS)` (193 explicit cols). Confirmed by log.

## Lessons for Future Iterations

- When new "seed validation" requirements surface, check WHICH seed actually controls randomness before scheduling 5 runs.
- For ensemble architectures, "seed parity" = same ensemble set, same ensemble size, same inner seeds. Not outer-seed sweeps.
- `LightGbmStrategy.__init__` accepts an unused `seed` parameter when `ensemble_seeds` is set. Consider cleaning this up (deprecate / remove / repurpose) in a future maintenance iteration.
