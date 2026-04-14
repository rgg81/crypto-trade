# Iteration v2/006 Diary

**Date**: 2026-04-14
**Type**: EXPLOITATION (ADX threshold tuning)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/006` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Decision**: **NO-MERGE** — primary 10-seed mean flat (−0.003), IS Sharpe
flipped negative, IS/OOS ratio −6.39 strict-fails the researcher-
overfitting gate. Pre-registered failure mode materialized in full.

## Results — side-by-side vs iter-v2/005

### Primary metric (10-seed mean)

| Statistic | iter-v2/005 | iter-v2/006 | Δ | Outcome |
|---|---|---|---|---|
| **Mean OOS Sharpe** | **+1.297** | **+1.294** | **−0.003** | **FAIL (flat)** |
| Std | 0.552 | 0.641 | +0.09 | wider (less stable) |
| Min | +0.319 | +0.107 | −0.21 | worst seed dropped |
| Max | +1.964 | +1.866 | −0.10 | — |
| Profitable | 10/10 | 10/10 | — | — |
| > +0.5 | 9/10 | 8/10 | −1 | — |

**10-seed mean is within ±0.003 of baseline** — pure noise. Primary
strictly fails (+1.294 < +1.297). Distribution widened by 0.09 Sharpe
on std, worst-case seed dropped by 0.21.

### Primary seed 42 (the misleading signal)

| Metric | iter-v2/005 | iter-v2/006 | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | +1.782 | +0.11 |
| OOS trades | 117 | 137 | +20 |
| OOS WR | 45.3% | 46.0% | +0.7 pp |

Primary seed 42 looked attractive — up 0.11 Sharpe with 20 more trades.
**Running only 1 seed would have led to a bad MERGE.** The 10-seed
validation caught the truth: 4 seeds up, 6 seeds down, mean flat.

### IS catastrophe — the critical failure

| IS Metric | iter-v2/004 | iter-v2/005 | iter-v2/006 |
|---|---|---|---|
| Sharpe | +0.465 | +0.116 | **−0.278** |
| PF | 1.135 | 1.029 | **0.938** |
| MaxDD | 77.02% | 111.55% | **177.98%** |
| WR | 41.2% | 40.1% | 38.7% |
| Trades | 272 | 344 | 398 |

**IS Sharpe has decayed monotonically over three iterations** and now
is NEGATIVE. IS PF is below 1.0 — the model is losing money on its own
training data. IS MaxDD ballooned to 178%.

### IS/OOS Sharpe ratio

| Iteration | IS Sharpe | OOS Sharpe | Ratio |
|---|---|---|---|
| iter-v2/004 | +0.465 | +1.745 | +0.267 |
| iter-v2/005 | +0.116 | +1.671 | +0.069 |
| **iter-v2/006** | **−0.278** | **+1.782** | **−0.156** |

The ratio has been decaying iteration-over-iteration and is now
**negative**, strict-failing the v2 skill's `IS/OOS Sharpe ratio > 0.5`
hard constraint.

## The pre-registered failure prediction was exactly right

Brief §6.3 said:

> "The most likely way iter-v2/006 fails is that the ADX 15-20 band
> contains trades that are IS-negative but OOS-positive — a regime-
> specific pattern that looks good on 2025 OOS but would reverse in
> other regimes. Signal: IS Sharpe drops meaningfully while OOS
> Sharpe rises. If IS Sharpe falls below zero while OOS is positive,
> that's a **strong** flag that the strategy is working by accident,
> not by design. The IS/OOS Sharpe ratio should stay above 0.5
> (strictly) for MERGE."

**Every bullet materialized**:

1. ✓ "IS Sharpe drops meaningfully while OOS Sharpe rises" — IS fell
   by 0.39, OOS rose by 0.11 on primary
2. ✓ "IS Sharpe falls below zero while OOS is positive" — IS −0.28, OOS +1.78
3. ✓ "Strong flag that the strategy is working by accident" — 10-seed
   mean is flat; the primary-seed gain is seed-42 luck
4. ✓ "IS/OOS Sharpe ratio should stay above 0.5" — ratio is −0.156

**The brief correctly anticipated the exact failure mode.** Writing
the failure mode prediction at the research stage — before seeing the
data — is the discipline that protected iter-v2/006 from being merged
on a tempting-but-fragile OOS improvement.

## Mechanism — why the ADX change backfired

The change lowered `adx_threshold` from 20 to 15, letting through
trades in the ADX 15-20 band (mildly trending markets).

**What I expected**: combined kill rate drops ~15pp (to ~55%), trades
rise to ~150, model captures more signal.

**What happened**: combined kill rate dropped only 7-8pp. Most of the
trades that ADX would have killed at threshold 20 now get killed by
the **low-vol filter** (which fires at `atr_pct_rank_200 < 0.33`).
Low-vol filter fire rate rose from 19-29% to 26-39% — it absorbed
most of the slack. Only a handful of ADX-band trades are new net-new
trades, and those net-new trades are **IS-negative**.

**Why ADX-band trades are IS-negative**: trades with ADX 15-20 are
mildly trending — the weakest part of the "trending regime" the
strategy relies on. In the IS window, these are borderline signals
that don't clearly resolve to TP. In the OOS window, by coincidence
of the 2025 alt-season regime, they tend to resolve positively.

**This is regime luck, not structural signal.** The trades are
IS-losers by construction — weakest signals in the trending bucket —
and their OOS gain is dependent on the specific 2025 regime persisting.

## Hard Constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary 10-seed mean > +1.297** | +1.297 | **+1.294** | **FAIL** (−0.003) |
| ≥7/10 seeds profitable | 7/10 | 10/10 | PASS |
| OOS trades ≥ 50 | 50 | 137 | PASS |
| OOS PF > 1.1 | 1.1 | 1.443 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 59.88% | PASS |
| No single symbol > 50% OOS PnL | 50% | ≤ 50% (likely) | likely PASS |
| DSR > +1.0 | 1.0 | +12.10 | PASS |
| v2-v1 correlation < 0.80 | 0.80 | ~−0.04 | PASS |
| **IS/OOS Sharpe ratio > 0.5** | 0.5 | **−0.156** | **FAIL** |

**Two strict failures**. No override available — the pre-registered
failure mode applies.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)

Rolling 10-iter exploration rate: 2/6 = **33%**, still above the 30%
minimum. iter-v2/007 can be either but there are no pending
must-explore ideas.

## Lessons Learned

1. **Pre-registered failure predictions work at a professional level**.
   The brief §6.3 didn't just hedge ("might fail in these ways"); it
   specifically said "IS Sharpe falls below zero, ratio below 0.5,
   this is a strong flag". The failure matched every specific. This
   is the Popperian discipline at its best — the iteration told me
   in advance what evidence would convict it, and then that evidence
   arrived exactly.

2. **Gate loosening hits diminishing returns**. The combined kill
   rate was at 66-76% after iter-v2/005, not because gates are
   individually miscalibrated but because the gates cover
   **overlapping regions** of the signal space. Loosening one gate
   mostly just passes the trades to another gate. The "combined kill
   rate > 30% target" is a misleading metric in cascaded gates — the
   overlap is the real issue.

3. **10-seed mean saved a bad MERGE**. Primary seed 42 suggested
   +0.11 Sharpe improvement; 10-seed mean revealed the truth of
   ±0.003 (flat). Without the 10-seed validation I would have
   merged a fragile iteration. **The methodology clarification in
   iter-v2/005 (primary = 10-seed mean) is proving its worth.**

4. **IS degradation is a warning even when OOS improves**. The typical
   researcher-overfitting pattern is IS >> OOS. This is the opposite:
   OOS >> IS, with IS going negative. Both are signs of fragility.
   The v2 skill's `IS/OOS ratio > 0.5` constraint catches both
   directions because a negative IS makes the ratio negative
   regardless of OOS strength. This is a good rule.

5. **Don't confuse seed variance with signal**. iter-v2/006's primary
   seed happened to land at +0.11 over baseline. That's ~0.2σ of the
   std 0.55 distribution — totally ordinary luck. Running 10 seeds
   made the noise visible.

6. **Shift to non-gate variables going forward**. Gate tuning is
   exhausted at the current calibration. Next iterations should
   explore: Optuna trial count, drawdown brake, NEAR-specific
   hyperparameters, per-symbol low-vol thresholds, or labeling
   experiments. Not more gate threshold changes.

## lgbm.py Code Review

No code changes needed. The runner correctly applies the new threshold
to all 4 models. Gate statistics are consistent with the threshold
change (ADX kill rate fell by ~2/3 as expected). No bugs.

## Next Iteration Ideas

### Priority 1 (iter-v2/007): Bump Optuna trials 10 → 25

The current IS Sharpe decay suggests the models are under-optimized —
10 Optuna trials per monthly model is 5× less than v1's 50. Especially
NEAR (which has a hostile IS regime) would benefit from more trials
finding hyperparameters that handle the 2022 bear market gracefully.

Expected outcome: IS Sharpe rises materially (from −0.28 back toward
+0.5 or higher), OOS stays flat or modestly rises. The key test: does
bumping trials restore IS/OOS ratio above 0.5?

**This is the cleanest EXPLOITATION candidate** — adds compute (roughly
2.5× wall-clock, so a 10-seed validation becomes ~120 min instead of
~50) but doesn't change the feature set, gates, or architecture.

### Priority 2 (iter-v2/008 if needed): Per-symbol NEAR settings

NEAR's IS/OOS inversion is the biggest contributor to the aggregate IS
weakness. NEAR IS is −67% vs OOS +3.5% per iter-v2/005 per-symbol
breakdown. Options:

- Shorter training window for NEAR (12 months instead of 24)
- NEAR-specific ATR multipliers (wider barriers?)
- Higher NEAR low-vol threshold (already hinted at by iter-v2/005's
  regime-stratified result showing NEAR dragging the mid-vol bucket)

Requires per-symbol `RiskV2Config` and `LightGbmStrategy` kwargs — small
refactor, maybe a dataclass `V2ModelSpec` that carries all
per-model knobs.

### Priority 3 (iter-v2/009): Enable drawdown brake

The iter-v2/002+ deferred risk primitive. Catches slow monotone
drawdowns that no existing gate detects. Adds capital preservation
for the "fragile OOS regime" scenarios this iteration highlighted.

### Deferred

- ADX gate tuning is DONE. Do not revisit below threshold 18 or above
  threshold 22 — the 15-20 band is fragile.
- BTC contagion circuit breaker, Isolation Forest — lower priority
  than the above.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick the research brief, engineering report, and
this diary to `quant-research`. iter-v2/006 branch stays as a record
and as the proof that the pre-registered failure mode discipline caught
a bad-looking improvement.

iter-v2/005 remains the v2 baseline:
- 10-seed mean: +1.297
- Primary seed 42: +1.671
- Profitable: 10/10
- Concentration: 47.8% (strict pass)
- v2-v1 correlation: −0.046

iter-v2/007 targets IS recovery via Optuna trial bump — the first
v2 iteration aimed at IS rather than OOS.
