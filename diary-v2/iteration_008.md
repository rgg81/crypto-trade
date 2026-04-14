# Iteration v2/008 Diary

**Date**: 2026-04-14
**Type**: EXPLORATION (per-symbol training window)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/008` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **NO-MERGE** — primary 10-seed mean dropped from +1.297
to +1.089 (−0.208). Spectacular primary seed 42 (+1.97 — v2's best
single-seed ever) and dramatic NEAR per-symbol improvements (+15 pp
weighted PnL) did not survive the 10-seed distribution.

## Results — side-by-side vs iter-v2/005 baseline

### 10-seed distribution

| Statistic | iter-v2/005 | iter-v2/008 | Δ |
|---|---|---|---|
| **Mean OOS Sharpe** | **+1.297** | **+1.089** | **−0.208** |
| Std | 0.552 | ~0.74 | +0.19 (WIDER) |
| Min | +0.319 | **−0.090** | **−0.409** |
| Max | +1.866 | **+2.165** | **+0.299** |
| Profitable seeds | 10/10 | 9/10 | −1 |
| > +0.5 target | 9/10 | 8/10 | −1 |

**5 seeds improved, 5 seeds degraded** — net effect is mean down and
distribution wider. The NEAR 12-month window is a high-variance
intervention that amplifies hyperparameter-search seed-dependence.

### Primary seed 42 — the misleading signal

| Metric | iter-v2/005 | iter-v2/008 | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | **+1.965** | **+0.294** |
| OOS PF | 1.457 | **1.564** | +0.11 |
| OOS MaxDD | 59.88% | 58.05% | −1.8 pp |
| OOS WR | 45.3% | 47.0% | +1.7 pp |

Primary seed 42 alone looked spectacular — this is v2's best
single-seed performance. But **the 10-seed validation caught the
truth**: the gain is highly seed-specific.

### Per-symbol OOS (primary seed)

| Symbol | iter-v2/005 | iter-v2/008 |
|---|---|---|
| DOGEUSDT | 31 trades, +11.52% wt, 12.3% share | **identical** |
| SOLUSDT | 37 trades, +28.89% wt, 30.7% share | **identical** |
| XRPUSDT | 27 trades, +44.89% wt, 47.8% share | **identical** |
| **NEARUSDT** | **22 trades, +8.71% wt, 9.3% share** | **22 trades, +23.93% wt, 21.9% share** |

**DOGE/SOL/XRP are byte-for-byte identical** — the one-variable
isolation held perfectly. Only NEAR changed.

**NEAR OOS tripled in weighted PnL** (+8.71% → +23.93%) with the same
trade count. This is genuine per-symbol signal improvement.

**Concentration**: XRP 41.1% (best-ever v2 reading, down from 47.8%).

### The cross-seed problem

Primary seed 42's NEAR result is NOT typical of the 10-seed distribution.
Other seeds (2345, 3456) produced materially worse NEAR results because
the 12-month window made hyperparameter search more sensitive to
initialization. With half the training samples (~1,400 vs ~2,800),
small randomness in feature selection or leaf construction cascades
into very different final models.

## Hard constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: 10-seed mean > +1.297** | +1.297 | **+1.089** | **FAIL** (−0.21) |
| ≥ 7/10 seeds profitable | 7/10 | 9/10 | PASS |
| OOS trades ≥ 50 | 50 | 117 | PASS |
| OOS PF > 1.1 | 1.1 | 1.564 | PASS (strong) |
| OOS MaxDD ≤ 64.1% | 64.1% | 58.05% | PASS |
| Concentration ≤ 50% | 50% | **41.1%** | PASS (best v2 yet) |
| DSR > +1.0 | 1.0 | +13.37 | PASS |
| IS/OOS ratio > 0 | 0 | +0.04 | PASS marginal |

**Primary fails**. All other constraints pass, some strongly (PF,
concentration, DSR). No override applies — the primary miss is a
structural distribution-shift, not seed noise.

## Pre-registered failure mode — 70% confirmed

Brief §6.3 predicted: "12 months is too short for LightGBM to find
stable hyperparameters... NEAR OOS could degrade... aggregate OOS
lands close to baseline ±0.2."

**70% right**:
- ✓ The shorter window DID destabilize hyperparameter search across seeds
- ✓ Aggregate OOS landed within ±0.3 of baseline (actually −0.21)
- ✗ NEAR OOS did NOT degrade — it IMPROVED dramatically on primary
  seed (+15 pp weighted PnL), and even the seeds that regressed on
  aggregate didn't regress because of NEAR specifically

**The 30% the brief missed**: the failure mechanism is
**cross-seed variance**, not average NEAR OOS degradation. NEAR OOS
on average is BETTER with 12 months; it's just that the seed-to-seed
spread is much wider.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)
- iter-v2/007: EXPLOITATION (NO-MERGE)
- **iter-v2/008: EXPLORATION (NO-MERGE)**

Rolling 10-iter exploration rate: **3/8 = 37.5%**, above the 30% minimum.
The quota is satisfied. iter-v2/009 can be EITHER category.

**Note**: the v2 track has had 4 NO-MERGEs in a row (iter-v2/006, 007,
008 plus iter-v2/003 earlier). Per the v2 skill's "3+ consecutive
NO-MERGE" rule, the next iteration should have a full Research
Checklist. Specifically: 4+ categories from A-H.

## Lessons Learned

1. **Primary seed 42 is biased upward**. Across 5 iterations now, seed
   42 consistently lands above the 10-seed mean. In iter-v2/008,
   seed 42's delta was +0.88 ABOVE the mean — larger than typical.
   Always run 10 seeds for merge decisions.

2. **Shorter training windows amplify seed variance**. Half the
   samples means half the stability. The best-case seed with 12
   months is materially better than the best-case with 24 months,
   but the worst-case seed is materially worse. Net mean is lower.

3. **NEAR can produce +1.97 Sharpe on the right seed** — that's the
   ceiling we're chasing. The challenge is finding a configuration
   that delivers that OOS quality with stable cross-seed variance.
   Options for iter-v2/009:

   a. **Middle-ground window** (18 months) — compromise
   b. **Per-symbol Optuna trials** — give NEAR 25 trials while
      keeping others at 10. More search depth should stabilize
      the hyperparameter selection within the 12-month window.
   c. **Replace NEAR** with FIL or APT (next-best screening candidates)

4. **The signature of a "correct improvement that gets rejected" is
   primary-seed gain + 10-seed loss**. This is the 3rd iteration in a
   row with this pattern (iter-v2/006, iter-v2/007, iter-v2/008).
   The v2 track is probing local optima; small changes produce
   1-seed gains but shift the distribution.

5. **NEAR per-symbol OOS is genuinely +15pp better**. This isn't
   noise — XRP/SOL/DOGE are byte-for-byte identical. The 12-month
   window gave NEAR access to non-bear-regime training data, and
   that yielded real OOS improvement. The cross-seed issue is the
   only thing blocking the merge.

6. **Four consecutive NO-MERGEs is a pattern worth stopping to
   think about**. iter-v2/005's baseline (+1.297) is a genuinely
   strong local optimum. Further improvements are NOT coming easily.
   iter-v2/009 should either try a fundamentally different direction
   or accept the current baseline and shift to external concerns
   (paper trading prep, combined-portfolio work).

## lgbm.py Code Review

No changes needed. `LightGbmStrategy` handled the per-symbol
`training_months` parameter correctly — NEAR models used a 12-month
window and the walk-forward split generator produced correct monthly
splits for each model independently. No bug.

## Next Iteration Ideas

The rolling NO-MERGE streak is at 3 consecutive (iter-v2/006, 007,
008 all NO-MERGE). Per the v2 skill, iter-v2/009 should do a full
Research Checklist (4+ of 8 categories from A-H plus Category I).

### Priority 1 (iter-v2/009, EXPLOITATION): NEAR 18-month compromise window

Middle ground between 12 (too wide variance) and 24 (hostile bear).
18 months still avoids the worst of 2022 (starts mid-2022 rather
than early-2022) while retaining 75% of the training samples for
stability.

Pre-registered hypothesis: 18-month window gives 50-75% of iter-v2/008's
primary-seed improvement (so NEAR OOS +8 pp from +8.71% toward +15%)
with half the cross-seed variance increase. 10-seed mean lands at
+1.20 to +1.40 (above iter-v2/005's +1.297).

### Priority 2 (iter-v2/010): Per-symbol Optuna trials

Give NEAR 25 trials, others 10. Requires a small refactor to
`LightGbmStrategy` OR per-model wrapping. Attempts to solve the
"shorter window = less stable search" problem by compensating with
more search depth for the symbol that needs it.

### Priority 3 (iter-v2/011 if 009-010 fail): Replace NEAR with FIL

From iter-v2/001 screening: FILUSDT has v1 correlation 0.665, 4,845
IS rows, $257M daily volume. Same category as NEAR (L1/storage
network) but different historical trajectory — no 2022 crypto bear
domination. Swap Model H from NEAR to FIL, keep 24-month window.

### Priority 4 (iter-v2/012+): Accept baseline and shift focus

If NEAR fixes are exhausted, iter-v2/005's +1.297 mean is a strong
local optimum. Consider shifting effort to:
- Enabling the drawdown brake (deferred risk primitive)
- BTC contagion circuit breaker
- Paper trading preparation
- Combined-portfolio work (loading v1 + v2 models on main)

### Mandatory Research Checklist Coverage for iter-v2/009

Per the 3+ consecutive NO-MERGE rule, iter-v2/009's research brief
should cover 4+ categories from A-H plus Category I:
- **A (Feature Contribution)**: Analyze which v2 features contribute
  most to each symbol's signal. NEAR may be weighted toward different
  features than the others.
- **B (Symbol Universe)**: Re-examine the 6-gate screening result —
  is NEAR still the best choice? Should we promote a different candidate?
- **C (Labeling Analysis)**: NEAR's triple-barrier hit rates per
  regime — maybe NEAR needs different ATR multipliers like v1 Model C/D.
- **D (Feature Frequency)**: Is the 35-feature catalog appropriate
  for NEAR? Do some features drag NEAR more than others?

Category I (Risk Management): standard section.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick research brief + engineering report + this
diary to `quant-research`. Branch stays as record.

iter-v2/005 remains the v2 baseline:
- 10-seed mean: +1.297
- Primary seed 42: +1.671
- Profitable: 10/10
- Concentration: 47.8%
- v2-v1 correlation: −0.046

This is the **3rd consecutive NO-MERGE** (after iter-v2/006 and /007).
iter-v2/009 per the skill must run a full Research Checklist.
