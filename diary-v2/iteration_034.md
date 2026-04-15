# Iteration v2/034 Diary — Seed Diagnostic

**Date**: 2026-04-16
**Type**: DIAGNOSTIC (isolate seed variance issue)
**Parent baseline**: iter-v2/029
**Decision**: **NO-MERGE** (diagnostic run, not a baseline candidate)

## What we tested

Per critical user directive:
> "Try the baseline using same setup but using different seeds. We
>  need to isolate this seed issue. Critical."

**Same** as iter-029: 4 symbols DOGE+SOL+XRP+NEAR, 15 Optuna trials,
single-seed ensemble, same features, same risk gates.

**Different**: FULL_SEEDS changed from (42, 123, 456, 789, 1001, 1234,
2345, 3456, 4567, 5678) to (11, 37, 131, 257, 541, 1093, 2287, 4657,
7621, 9941) — 10 distinct primes spanning a similar range.

## Headline finding — partially structural, partially seed-dependent

| Metric | iter-029 (old) | **iter-034 (new)** | Reading |
|---|---|---|---|
| Mean IS monthly | +0.56 | **+0.82 (+46%)** | **seed-dependent** |
| Mean OOS monthly | +0.90 | +0.86 (−4%) | **bounded** |
| Profitable | 9/10 | 9/10 | same |
| Balance | 1.61x | **1.06x** (best) | seed-dependent |
| Concentration pass-50% | ~1/10 | **5/10** | seed-dependent |
| Distressed | 2/10 | 2/10 | **structural (~20%)** |

**Primary seed 11**:
- OOS trade Sharpe **+1.9586** (best in v2 history)
- OOS MaxDD **27.56%** (best in v2 history)
- XRP concentration **44.97%** PASSES (primary passes rule for second
  iter in a row: iter-032 primary was 40.37%, iter-034 primary is 44.97%)

## Three distinct conclusions

### 1. IS mean is strongly seed-dependent

iter-029's mean IS was +0.56; iter-034's is +0.82 (+46%). Same config,
same features, same trials — different seeds find different-quality
hyperparameters.

This explains why iter-029 showed "IS is weak" — seed 1001 was weakly
optimized on IS (−0.43) and dragged the mean.

### 2. OOS mean is bounded around +0.85-0.90

Regardless of seed choice, the 10-seed OOS mean hovers at +0.85-0.90.
Neither iter-029 nor iter-034 breaks +0.90 on the 10-seed mean despite
very different seed distributions.

**This is a real ceiling for the iter-029 config.** To break through
+1.0, we need something other than seed rotation.

### 3. Distressed-seed failure rate is structural (~20%)

Every 10-seed run has ~2 seeds where Optuna finds strong IS
hyperparameters that don't generalize to OOS:

- iter-029: seed 1001 (IS −0.43, OOS −0.07)
- iter-034: seed 131 (IS +1.08, OOS +0.05) and seed 1093 (IS +0.37,
  OOS −0.42)
- iter-031/032 data showed similar pattern

This isn't the specific seed IDs — it's a property of how Optuna
searches the hyperparameter space. Some initial-value trajectories
always find local minima that overfit IS.

## Hypothetical: 8-seed mean excluding distressed

If we drop the 2 distressed seeds (131, 1093) from iter-034:
- **IS mean: +0.84**
- **OOS mean: +1.124** ← **first time above 1.0 in v2 history!**
- **Profitable: 8/8**
- Concentration: 5/8 pass 50% rule

Of course, we can't cherry-pick seeds for the baseline. But this
strongly suggests: **if we can eliminate the distressed-seed failure
mode, the baseline breaks above +1.0.**

## Why iter-033 ensemble failed (retrospective)

iter-033 tried `ensemble_seeds=[seed, seed+1, seed+2]` with 15 Optuna
trials each. Result: primary seed OOS monthly collapsed from +1.28 to
+0.02 (99% regression).

Root cause analysis:
1. **15 trials per inner seed is too few** for Optuna to converge on
   stable hyperparameters
2. **3 seeds produced very different hyperparameter sets** because
   each seed's shallow search found a different local optimum
3. **Averaging 3 divergent models' probabilities** produces lower
   average confidence
4. **The averaged confidence fell below the confidence threshold** on
   most trades, so the strategy skipped them
5. **The ensemble effectively became "trade only when all 3 models
   strongly agree"** which filtered out most profitable trades

The user pointed out:
> "It's weird because it worked for v1. We run 5 seeds for each model
>  and average the probability, why don't follow the same approach?"

**The averaging mechanism is identical to v1's.** The difference is
that v1 uses `n_trials=50` per inner seed (vs iter-033's 15). With 50
trials, each inner seed's Optuna search finds a mature hyperparameter
set, and averaging 5 mature models produces a stable, confident
ensemble. With 15 trials, each inner seed's search is immature and
averaging yields noise.

## iter-035 plan — match v1's architecture exactly

```python
ensemble_seeds=[42, 123, 456, 789, 1001]  # 5 fixed seeds, same as v1
n_trials=50                                # match v1 budget
# Single run, no outer 10-seed loop
```

Total Optuna budget: **50 × 5 = 250 trials per model per month**
(vs iter-029's 15 trials single-seed = 15 per month).

**Runtime**: very roughly 250/15 ≈ 17x per model = ~6 min per model
(vs iter-029's ~2min). 4 models × 6 min = ~24 min total for iter-035
(vs iter-029's ~95 min for the full 10-seed sweep).

**Architectural change**: no outer 10-seed loop. The 5-seed internal
ensemble IS the robustness validation. This matches v1's approach
exactly.

This is also consistent with user memory:
- "10 seeds, mean Sharpe > 0, ≥7/10 profitable" — this rule will
  need updating if v2 switches to v1-style single-run ensembles
- Or: we keep the 10-seed outer validation BUT inside each outer
  seed, use a 5-internal-ensemble (heavy runtime ~10x)

iter-035 will try the v1-style single-run approach first (faster,
matches v1's proven pattern). If it works, we can revisit the
methodology rule.

## MERGE / NO-MERGE

**NO-MERGE** — this was a diagnostic. No new baseline.

The iter-034 report and diary are the deliverable. iter-035 will be
the next baseline candidate with v1-style 5-seed ensemble.

## Next iteration

**iter-v2/035** = v1-style 5-seed ensemble, 50 Optuna trials per seed,
single run (no outer loop). iter-029 config (4 symbols DOGE+SOL+XRP+NEAR).

Also consider: running iter-035 with iter-032's symbol mix
(DOGE+XRP+NEAR+ADA) once the v1-style ensemble approach is validated.
