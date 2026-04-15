# Iteration v2/032 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (4-symbol, swap SOL→ADA)
**Parent baseline**: iter-v2/029 (forced reset)
**Decision**: **NO-MERGE** — OOS mean regressed despite primary seed improvements

## TL;DR

iter-032 produces the **best primary-seed result** in v2 history and
**first passing concentration audit on primary** — but the 10-seed
mean OOS regressed 11% because 4 seeds (123, 1234, 2345, 3456)
regressed significantly. Symbol swap fixes concentration on primary
seed; does not fix seed variance.

## Results snapshot

| Metric | iter-029 | **iter-032** |
|---|---|---|
| Mean IS monthly | +0.5578 | **+0.7300** (+31%, best IS) |
| Mean OOS monthly | +0.8956 | +0.7992 (−11%) |
| Profitable seeds | 9/10 | 8/10 |
| OOS/IS ratio | 1.61x | **1.09x** (best balance) |
| Primary seed IS/OOS | +0.67/+1.28 | **+0.96**/+1.28 |
| Primary XRP share | 69.47% | **40.37%** (passes 50% rule) |

## The two phases of iter-032

### Phase 1 — 3-symbol DOGE+XRP+ADA (failed smoke test)

First attempt: drop SOL and NEAR, keep only net-positive primary-seed
contributors. Smoke test showed 40% OOS regression vs iter-031 primary.

**Root cause**: hit-rate gate cross-symbol coupling. The "last 20
trades" lookback is shared across symbols; with fewer symbols, the
window spans more calendar time and kills different trades. Same 32
DOGE trades produced +30.12 wpnl in iter-031 (5-sym) vs +9.83 in
iter-032 3-sym purely because gate survivors differed.

**Lesson**: symbol removal is NOT a free lunch. Gates have implicit
cross-symbol dependencies.

### Phase 2 — 4-symbol DOGE+XRP+NEAR+ADA (pivot)

Keep trade density at 4. Swap SOL (worst primary-seed contributor)
for ADA (real signal from iter-031).

Smoke test: **best primary-seed ever**. Full 10-seed confirmed
primary-seed gains but revealed seed variance.

## Per-seed picture (4-symbol)

| Seed | iter-029 OOS | iter-032 OOS | Δ |
|---|---|---|---|
| 42 | +1.28 | +1.28 | 0 (flat) |
| 123 | +1.54 | +1.41 | −0.13 |
| 456 | +0.51 | **+0.90** | +0.39 |
| 789 | +1.18 | +1.21 | +0.03 |
| 1001 | −0.07 | −0.06 | +0.01 (flat) |
| 1234 | +0.99 | +0.62 | **−0.37** |
| 2345 | +1.46 | +0.82 | **−0.64** |
| 3456 | +1.13 | **−0.10** | **−1.23** ← catastrophic |
| 4567 | +0.42 | +0.79 | +0.37 |
| 5678 | +0.52 | +1.12 | +0.60 |

**4 improved, 4 regressed, 2 flat.** Seed 3456 alone drags the mean
by 0.12.

## Seed concentration audit

| Seed | Max Share | Symbol | Pass ≤50% | Distressed? |
|---|---|---|---|---|
| **42** | **40.37%** | XRPUSDT | **PASS** | — |
| 123 | 55.36% | XRPUSDT | FAIL | — |
| 456 | 65.77% | XRPUSDT | FAIL | — |
| 789 | 55.34% | XRPUSDT | FAIL | — |
| 1001 | 95.08% | XRPUSDT | FAIL | DISTRESS |
| 1234 | 65.02% | DOGEUSDT | FAIL | — |
| 2345 | 73.71% | XRPUSDT | FAIL | — |
| 3456 | 100.00% | XRPUSDT | FAIL | DISTRESS |
| 4567 | 55.10% | XRPUSDT | FAIL | — |
| 5678 | 57.78% | NEARUSDT | FAIL | — |

- 1/10 pass per-seed 50% rule (primary seed 42 only)
- Mean 66.35% vs 45% rule → FAIL
- Distressed: **2/10** (meets ≤2 rule for first time!)
- **Overall: FAIL**

## MERGE gating criteria

| Criterion | Target | Result | Pass? |
|---|---|---|---|
| Seed concentration | PASS | FAIL (1/10) | **FAIL** |
| Mean OOS > iter-029 | +0.90 | +0.80 | **FAIL** |
| ≥8/10 profitable | 8/10 | 8/10 | PASS |
| Primary XRP < 50% | 50% | 40.37% | PASS |

**NO-MERGE.** 2 of 4 gates fail, and the primary failure is OOS mean
regression.

## The structural ceiling

Three consecutive iters have hit similar OOS mean ceilings:

| Iter | Config | Mean OOS | Profitable | Concentration |
|---|---|---|---|---|
| 029 | 4-sym DOGE+SOL+XRP+NEAR | +0.90 | 9/10 | Fail (~71%) |
| 030 | Same (audit only) | +0.90 | 9/10 | Same |
| 031 | 5-sym +ADA | +0.66 | 7/10 | Fail (66%, 3 distressed) |
| 032 | 4-sym swap SOL→ADA | +0.80 | 8/10 | Fail (66%, 2 distressed) |

**None break above +0.90 on mean OOS monthly.** Each iter is better
on primary seed but worse on 10-seed mean, or same. The variance
across seeds is the binding constraint.

## Key insight — symbol choice has a local ceiling around +0.90 OOS mean

I've tried:
- Different 4-symbol compositions (iter-023, iter-024, iter-029, iter-032)
- Different Optuna trial counts (iter-019 10-trial, iter-028 25-trial,
  iter-029 15-trial)
- Different feature additions (iter-026 BTC cross, iter-028 entropy+CUSUM
  from the v1-track)
- Adding a 5th symbol (iter-031)
- Swapping symbols (iter-022 LTC, iter-023 TRX, iter-032 ADA)

**None broke through +1.00 on mean OOS monthly**. The primary seed often
reaches +1.3-1.6 OOS monthly, but the 10-seed mean hovers at +0.70-0.90.

**This strongly suggests the binding constraint is Optuna seed variance,
not symbol/feature choice.** Moving the symbol lever has diminishing
returns.

## iter-033 recommendation — attack seed variance directly

### Option A — Ensemble internal seeds per model (recommended)

Currently each model uses one seed at a time. Change to
`ensemble_seeds=[seed, seed+1, seed+2]` so each model averages
predictions across 3 internal seeds. This smooths Optuna hyperparameter
noise directly.

**Pros**:
- Directly targets the identified root cause
- `ensemble_seeds` parameter already exists in `LightGbmStrategy`
- Well-understood technique

**Cons**:
- 3x runtime per model → ~4-5 hours for iter-033 validation
- If ensemble averaging fails, we're out another 5 hours

### Option B — Ensemble-average 10 seeds outside the model

Average OOS predictions across the 10 external seeds after each runs
separately. Doesn't require code changes to lgbm.py.

**Pros**: Cleaner, no model-level change
**Cons**: 10x runtime even for validation

### Option C — Reduce hit-rate gate over-firing

iter-019 added the hit-rate gate. On some seeds it over-fires and kills
legitimate trades. iter-033 could tune the hit-rate threshold higher
(kill fewer trades) on a per-seed basis.

**Pros**: Targets observed gate-level seed variance
**Cons**: Fewer kills could worsen the protection against real bad streaks

### Option D — Optuna warm-start from seed 42's hyperparameters

Seed 42 is the "best" seed consistently. Warm-start the Optuna search
on other seeds with seed 42's final hyperparameter values. Should
produce tighter distributions around seed 42's result.

**Pros**: Simple to implement, targets Optuna variance directly
**Cons**: Could over-anchor to seed 42 and reduce diversity

**Recommendation: Option A (ensemble internal seeds).** Despite the
runtime cost, it's the most direct attack on the identified problem.
If it works, subsequent iters can run faster with smaller ensembles.
If it doesn't, we have definitive evidence that seed variance is not
just Optuna-driven and need to look elsewhere.

## Lessons learned (iter-030 through iter-032)

1. **Cross-symbol gate coupling is real and non-obvious**. Can't just
   "drop losing symbols" — changes the gate behavior.
2. **ADA is a real signal**, not a filler (unlike DOGE/SOL historically).
3. **Symbol-choice has a local ceiling** at mean OOS +0.90. The primary
   seed can go higher but the 10-seed mean doesn't break through.
4. **IS improvements are available** — iter-032 has the best IS mean yet
   (+0.73). But IS is cheap to overfit; OOS is the real test.
5. **Balance ratio is fixable** via symbol choice. iter-032 achieved 1.09x,
   best in v2 history. Not enough alone to beat baseline.
6. **Distressed seeds are symptomatic** of Optuna hyperparameter variance,
   not concentration per se. Fixing seed variance should fix distressed
   count.

## MERGE / NO-MERGE

**NO-MERGE.** iter-029 stays as baseline.

Ship infrastructure regardless: the iter-032 commits (V2_MODELS,
cross-symbol coupling finding, best primary-seed result, best balance
ratio) should merge to `quant-research` as record.

**Next iteration**: iter-v2/033 = **ensemble 3 internal seeds per
model** (Option A). Directly attack seed variance.
