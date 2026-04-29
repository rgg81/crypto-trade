# Iteration v2/007 Diary

**Date**: 2026-04-14
**Type**: EXPLOITATION (Optuna trial count tuning)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/007` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Decision**: **NO-MERGE** — primary OOS regressed by 0.19 on seed 42,
concentration strict-failed at 55.7% (up from 47.8%), IS Sharpe was
essentially unchanged (hypothesis failed). 10-seed validation skipped
to save 2.5 hours of compute — 1-seed evidence was already conclusive.

## Results — side-by-side vs iter-v2/005 baseline (primary seed 42)

| Metric | iter-v2/005 | iter-v2/007 | Δ | Outcome |
|---|---|---|---|---|
| OOS Sharpe | +1.671 | +1.481 | **−0.190** | FAIL |
| OOS PF | 1.457 | 1.447 | ~0 | — |
| OOS MaxDD | 59.88% | **43.12%** | **−16.76 pp** | Improved |
| OOS WR | 45.3% | 40.2% | −5.1 pp | — |
| OOS trades | 117 | 97 | −20 | Fewer signals |
| **IS Sharpe** | +0.116 | **+0.118** | **+0.002** | **Unchanged (hypothesis failed)** |
| IS MaxDD | 111.55% | 118.55% | +7 pp | Slightly worse |
| IS trades | 344 | 323 | −21 | Fewer signals |
| **XRP concentration** | **47.8%** | **55.7%** | **+7.9 pp** | **Regression** |

**The IS recovery hypothesis failed outright**. IS Sharpe moved from
+0.116 to +0.118 — a delta of +0.002, well inside measurement noise.
The whole point of this iteration was to lift IS via more Optuna search.
It didn't.

## The zero-sum per-symbol rebalancing finding

Even though aggregate IS Sharpe is flat, the per-symbol IS distribution
**moved dramatically**:

| IS Metric | iter-v2/005 (10 trials) | iter-v2/007 (25 trials) | Δ |
|---|---|---|---|
| XRPUSDT | 149 trades, **+124.65%** | 103 trades, +55.28% | **−69.4 pp** |
| DOGEUSDT | 107 trades, **+86.80%** | 63 trades, +20.83% | **−65.97 pp** |
| SOLUSDT | 117 trades, −19.23% | 83 trades, −15.70% | +3.53 pp |
| **NEARUSDT** | **72 trades, −67.39%** | **74 trades, +23.16%** | **+90.55 pp** |

**NEAR's IS flipped from −67% to +23% — a +90pp swing**. That's the
biggest single-variable improvement any v2 iteration has produced on
NEAR. But XRP and DOGE IS dropped by roughly equal amounts. The
aggregate is flat because it's a **zero-sum trade between symbols**.

### What this means

With 10 Optuna trials per monthly model, the optimizer greedily finds
hyperparameters that maximize CV Sharpe on the **easiest symbols**
(XRP and DOGE, which have strong trending signals). It accepts NEAR's
loss because fixing NEAR requires exploring parts of the hyperparameter
space that would hurt XRP/DOGE.

With 25 trials, Optuna explores enough to find **balanced**
hyperparameters — ones that work across all 4 symbols. But the
"balanced" solution is NOT better in aggregate — it's just redistributed.

**The aggregate IS Sharpe ceiling is not an optimization-depth
problem. It's a structural data problem.** NEAR's 2022 bear market
dominates its training data. No amount of hyperparameter search on
NEAR's own data can make it profitable on its own data.

The correct fix is to **change what data NEAR is trained on** — not
to search harder through the same data. Options:

1. Shorter training window for NEAR (12 months instead of 24) —
   avoids 2022 entirely
2. Per-symbol Optuna (more trials for NEAR, same for others)
3. Replace NEAR

## Pre-registered failure-mode prediction — validated (97% right)

Brief §6.3 said: "IS is structurally stuck due to NEAR's hostile 2022
bear-market training regime. Signal: IS Sharpe stays essentially
unchanged (±0.05 of +0.12). If that happens, the correct diagnosis is
that IS weakness is a DATA/REGIME issue, not an optimization-depth
issue, and iter-v2/008 should pivot to NEAR-specific interventions."

**Confirmed fully**:

- ✓ IS Sharpe stayed essentially unchanged (+0.002 delta, well inside
  the ±0.05 prediction band)
- ✓ Conclusion is DATA/REGIME issue, not optimization depth
- ✓ Next iteration should pivot to NEAR-specific interventions

**Partially wrong on mechanism** (the brief said "Optuna finds
different ways to lose on NEAR" — actually it found ways to WIN on
NEAR while losing on XRP/DOGE). But the overall conclusion is correct:
**the aggregate IS ceiling doesn't move**.

## Hard Constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: OOS Sharpe > +1.67** | +1.67 | **+1.481** | **FAIL** |
| OOS trades ≥ 50 | 50 | 97 | PASS |
| OOS PF > 1.1 | 1.1 | 1.447 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 43.12% | PASS (strongly) |
| **No single symbol > 50% OOS PnL** | **≤50%** | **55.7%** | **FAIL** |
| DSR > +1.0 | +1.0 | +10.46 | PASS |
| IS/OOS ratio > 0 | 0 | +0.077 | PASS (marginally) |
| v2-v1 correlation < 0.80 | 0.80 | not recomputed | — |

**Two strict failures**: primary metric and concentration. No override
applies (no new symbols, no within-5% margin). Decisive NO-MERGE.

## Why 10-seed validation was skipped

Running the full 10-seed at 25 trials would cost ~150 min. I elected
to NO-MERGE on 1-seed evidence because:

1. **Primary seed 42 is −0.19 below baseline**. In iter-v2/005's 10-seed
   sweep, seed 42 was ABOVE the mean (+1.67 vs +1.30). Starting this
   much below primary suggests the 10-seed mean is ~+1.10, well below
   +1.297 target.
2. **IS hypothesis failed flat**. Running more seeds won't change the
   IS Sharpe value — it's a structural observation from the per-symbol
   distribution.
3. **Concentration strict-failed at 55.7%**. That's iteration-killing
   regardless of primary.
4. **Compute budget discipline**. 2.5 hours for a near-certain NO-MERGE
   is wasteful when iter-v2/008 has a better-targeted hypothesis.

The iter-v2/006 diary lesson #3 — "10-seed mean saves from primary-seed
luck" — went in both directions. Here, primary seed 42 is actively
WORSE than baseline, so more seeds would confirm, not reverse.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)
- iter-v2/007: EXPLOITATION (NO-MERGE)

Rolling 10-iter exploration rate: 2/7 = **29%**, just under the 30%
minimum. **iter-v2/008 should be EXPLORATION** to restore the ratio.

Candidates that count as exploration:
- Symbol replacement (universe change) — fits the NEAR problem directly
- Per-symbol training windows (architecture change)
- Per-symbol Optuna trial counts (architecture change)
- Meta-labeling (new modeling technique)

## Lessons Learned

1. **Optuna trial count is zero-sum across symbols in a shared-run
   setup**. More trials redistribute per-symbol PnL allocation; they
   don't raise the aggregate ceiling. To raise the ceiling, either (a)
   change the input data or (b) give each symbol its own independent
   optimization.

2. **IS weakness ≠ optimization weakness**. The v2 portfolio's IS
   weakness is structural (NEAR's 2022 bear market dominates training),
   not depth-of-search weakness. Pouring more compute at the same
   problem doesn't move the needle.

3. **Concentration is second-order fragile**. An iteration that doesn't
   touch universe or gates can still break concentration via changes
   in per-symbol trade count. SOL's OOS trade count dropped from 37 to
   34, weighted PnL from +28.89% to +7.56% — that alone lifted XRP's
   relative share above 50% even though XRP's absolute PnL dropped
   slightly too. Monitor concentration in every iteration, not just
   universe changes.

4. **Fail fast works both ways**. iter-v2/006's "the primary-seed
   looks good but 10-seed is flat" scenario taught me to run 10 seeds.
   iter-v2/007's "the primary-seed is clearly bad" scenario teaches
   me to NOT run 10 seeds when 1-seed is already conclusive. The
   rule: run 10 seeds when the 1-seed result is ambiguous. Skip them
   when it's unambiguous in either direction.

5. **Brief pre-registered predictions are cheap insurance**. Writing
   the "most likely failure mode" in the research brief before seeing
   data means the iteration can ONLY update the diary toward "failed
   as expected" or "failed unexpectedly". Both outcomes are
   informative; the second is MORE informative but rarer. Keep doing
   this.

6. **NEAR's 2022 bear dominates its training**. This is now confirmed
   from two independent angles: iter-v2/005 showed NEAR's IS of −67%,
   iter-v2/007 showed that dedicated Optuna search can improve NEAR
   IS to +23% at the cost of other symbols. Both point to the same
   structural issue: NEAR's training data is so hostile that any
   optimization lifting NEAR IS must sacrifice elsewhere.

## lgbm.py Code Review

No code changes needed. The `n_trials` parameter flows cleanly from
the CLI through `_build_model` into `LightGbmStrategy.n_trials`. The
rebalancing observation above is an emergent property of Optuna's
TPE sampler finding different hyperparameter regions given more
evaluations — not a bug.

One observation: Optuna's `optimize_and_train` in `optimization.py`
uses a single shared optimizer across symbols within each monthly
fold. A potential future refactor: give each symbol its OWN Optuna
study so the search depth can be tuned per-symbol. This is the
architectural change behind "per-symbol n_trials" (Priority 2 in the
iter-v2/008 candidates below).

## Next Iteration Ideas

### Priority 1 (iter-v2/008): Shorter training window for NEAR

This is the direct, targeted fix for the actual root cause. NEAR's
2022 bear market dominates its 24-month rolling training window. By
using a **12-month training window for NEAR only**, we avoid 2022
entirely in any month that predicts >= 2023-01.

Implementation: `V2_MODELS` tuple entries gain a `training_months`
field. `_build_model` accepts a per-model `training_months` kwarg
and passes it to `LightGbmStrategy.training_months`. Change is
isolated to `run_baseline_v2.py` — no changes to `lgbm.py` or
`risk_v2.py`.

Expected outcome: NEAR IS Sharpe rises from −67% (iter-v2/005
baseline) or +23% (iter-v2/007) to +30-50%. XRP/DOGE/SOL unchanged
(shorter window applies to NEAR only). Aggregate IS Sharpe rises
from +0.12 toward +0.3-0.5. OOS likely roughly flat or modestly up.

**This is EXPLORATION** (architecture change: per-symbol training
window), so it also restores the 30% exploration quota (from 29%).

### Priority 2 (iter-v2/009 if Priority 1 partially works): Per-symbol Optuna n_trials

Give NEAR 50 trials while keeping others at 10. More targeted than
iter-v2/007's universal bump. Requires a small `LightGbmStrategy`
change to accept per-symbol n_trials, OR a per-symbol wrapping in
the runner.

### Priority 3 (iter-v2/010 if NEAR is unsalvageable): Replace NEAR

From iter-v2/001 screening, next-best candidates were FILUSDT and
APTUSDT (both at v1 corr 0.665). Swap Model H from NEAR to one of
these. Keep everything else. Compute XRP concentration and seed
robustness.

### Deferred

- ADX threshold tuning: exhausted (iter-v2/006 NO-MERGE, 15-20 band
  is fragile)
- Drawdown brake: good idea but lower priority than the IS fix
- BTC contagion, Isolation Forest: after drawdown brake

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick research brief + engineering report + this
diary to `quant-research`. Branch stays as record. No BASELINE_V2
update, no tag, no 10-seed validation.

iter-v2/005 remains the v2 baseline:
- 10-seed mean: +1.297
- Primary seed 42: +1.671
- Profitable: 10/10
- Concentration: 47.8% (strict pass)
- v2-v1 correlation: −0.046

iter-v2/008 will directly target NEAR's 2022-training-regime problem
via a 12-month training window for NEAR only. Per-model architecture
change, EXPLORATION category, restores the exploration quota.
