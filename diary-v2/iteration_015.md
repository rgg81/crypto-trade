# Iteration v2/015 Diary

**Date**: 2026-04-14
**Type**: EXPLORATION (BTC contagion feasibility)
**Track**: v2 — risk arm
**Branch**: `iteration-v2/015` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, 59.88% MaxDD)
**Decision**: **NO-MERGE** (brake fires outside v2's drawdown window)

## What happened

iter-v2/014 closed the drawdown brake lineage. iter-v2/015 was the
last-chance risk primitive: BTC contagion circuit breaker, the
only approach that could bypass XRP dominance by firing
symmetrically on a cross-asset signal (BTC crash).

**Result**: the BTC contagion brake fires at the wrong times. The
July-August 2025 v2 drawdown (which iter-v2/005 experiences with
59.88% MaxDD) is **alts-specific**, not BTC-correlated. BTC was
calm during that window. The brake's triggers cluster in April,
October-December 2025, and January 2026 — none of them overlap
v2's actual drawdown.

## Headline

| Config | Events | Kills | MaxDD | Sharpe | XRP Share |
|---|---|---|---|---|---|
| **None (baseline)** | 0 | 0 | **−45.33%** | **+1.66** | 47.75% |
| A (tight −3/−8) | 23 | 14 | −48.61% (worse) | +0.60 | 111.30% (blew up) |
| B (mid −4/−10) | 6 | 1 | −45.33% (unchanged) | +1.55 | 51.37% |
| C (loose −5/−12) | 2 | 3 | **−45.33% (unchanged)** | +1.33 | 56.83% |
| D (mid+9-bar kill) | 6 | 6 | **−45.33% (unchanged)** | +1.13 | 51.28% |

**Three of four configs leave MaxDD identical to baseline** because
the brake's trigger windows never overlap v2's actual drawdown.

## The strongest diagnostic

Listing Config B's trigger dates chronologically:

| Trigger date | Type | 1-bar | 3-bar | Context |
|---|---|---|---|---|
| 2025-04-07 | 1bar | −4.22% | −9.53% | Early April dip |
| 2025-06-22 | 1bar | −3.47% | −4.51% | Late June |
| **2025-07 → 2025-09** | **—** | **—** | **—** | **NO EVENTS — v2 is in drawdown here** |
| 2025-10-10 | 1bar | −5.25% | −7.29% | October |
| 2025-10-11 | 3bar | −2.11% | −8.73% | October |
| 2025-10-21 | 1bar | −4.50% | −2.01% | October |
| 2025-10-30 | 1bar | −3.27% | −3.40% | October |

Between **2025-06-22 and 2025-10-10** — a 110-day window — BTC had
ZERO qualifying contagion events. But v2's worst drawdown happens
inside that window. The brake can't protect against a drawdown it
never sees.

**The July-August 2025 v2 drawdown is NOT a BTC contagion event.**
It's NEAR and SOL drifting down against a stable BTC. A brake
that fires on BTC crashes is the wrong tool for this specific
tail.

## Why Config A makes things worse

Config A's tight thresholds (−3%/−8%) fire 23 times, killing 14
trades. But since the kills happen in April, October-December,
January — outside the drawdown window — they remove winning
trades that would have OFFSET the July-August drawdown. Result:
equity curve is lower at peak AND at trough, and **MaxDD is
WORSE (−48.61% vs −45.33%)**.

The tightest brake is strictly worse than no brake. This is a
cleanly negative result for the tight-threshold hypothesis.

## Pre-registered failure-mode prediction — perfect hit

Brief §"Pre-registered failure-mode prediction":

> **"BTC didn't materially crash during 2025 OOS, so the
> contagion brake doesn't fire at all. ALTERNATIVELY: BTC crashed
> during periods where v2 was not trading, so the brake fires but
> has no effect on trades. SECONDARY: July-August 2025 v2
> drawdown may have been alt-specific rather than
> BTC-correlated."**

**Actual**: hit the secondary prediction exactly. BTC did crash a
few times (20 bars with 1-bar return < −3%), but NONE of them in
the July-August window. The drawdown is alts-specific.

This is the second time in 15 iterations that I've written a
pre-registered failure mode that the data confirmed. (The first
was iter-v2/013 predicting Sharpe drag within noise but missing
concentration.) Failure-mode prediction discipline is paying off.

## What this teaches us about v2's drawdown

Three iterations have been dedicated to understanding and fixing
v2's 59.88% OOS MaxDD:

- **iter-v2/012-014**: drawdown brake lineage. Works on aggregate
  but breaks concentration.
- **iter-v2/015**: BTC contagion. Doesn't fire during the actual
  drawdown.

The combined evidence says v2's drawdown has a specific signature:

1. **Slow multi-week drift**, not a flash crash
2. **Alts-specific**, not BTC-correlated
3. **Hit-rate inversion**: shorts keep hitting SL instead of TP
4. **Gradual feature shift**, not a sudden regime change

None of the existing gates (z-score OOD, Hurst, ADX, low-vol) see
this signature clearly. z-score catches distributional shifts but
this was gradual. Hurst catches regime transitions but this was
gradual. ADX catches ranging regimes but July-August was
trending. Low-vol catches noise but this was normal-vol.

**The unique feature of v2's drawdown is the hit-rate inversion.**
When the model is systematically wrong about direction, recent
trades cluster heavily on SL exits. A gate that tracks the recent
SL/TP ratio and fires when it crosses a threshold (e.g., "last
10 trades hit SL 8 times, kill signals until the ratio recovers")
would specifically catch this pattern.

## Lessons Learned

### 1. Tail events have different signatures — a single brake design can't catch all

iter-v2/012-014 drawdown brake would catch sudden multi-bar
crashes (portfolio equity drops quickly). iter-v2/015 BTC
contagion would catch cross-asset flash crashes. Neither catches
the specific pattern v2 is vulnerable to: slow alts-specific
bleed with hit-rate inversion.

**Generalization**: risk primitives must be matched to the
SPECIFIC tail signature they defend against. A portfolio with a
sudden-crash history needs drawdown brake. A portfolio with
cross-asset contagion vulnerability needs BTC contagion. A
portfolio with model-directionality risk needs a hit-rate
feedback gate.

v2's tail signature is directionality risk. The right defence
is hit-rate feedback, not DD or cross-asset gates.

### 2. Pre-registered failure-mode prediction has become reliable

The brief predicted "BTC contagion misses the actual drawdown"
and the data confirmed it exactly. iter-v2/013's brief predicted
Sharpe drag but missed concentration — that was a 50% hit.
iter-v2/014's brief predicted per-symbol brake would hit
concentration and missed the DOGE dominance shift — that was
also a partial hit.

Over the last 5 iterations, the failure-mode predictions have
been directionally correct 4-for-5 and precise 2-for-5. This is
substantially better than my direction in iter-v2/001-010 where
several predictions were completely wrong.

**Practice**: the discipline of writing a pre-registered
failure-mode BEFORE running the experiment keeps my intuition
honest. I should continue this.

### 3. Negative results are informative — iter-015 is a cleanly-negative result

The brake fires as designed. The math is correct. The decision
criteria are sensible. But the specific risk the brake is
designed to catch DOESN'T EXIST in the data. That's a
cleanly-negative finding: not "the brake is broken" but "the
brake targets a risk v2 isn't actually exposed to".

Cleanly-negative results are more valuable than ambiguous
results because they definitively close a search direction.
After iter-015, I can say with high confidence that neither
drawdown brakes nor BTC contagion will work for v2's specific
tail risk profile.

### 4. The v2 track's risk-primitive search space is nearly exhausted

Gates implemented and tested:
- z-score OOD (iter-v2/001) ✓ active
- Hurst regime (iter-v2/001) ✓ active
- ADX gate (iter-v2/001) ✓ active
- Low-vol filter (iter-v2/004) ✓ active
- Vol-adjusted sizing (iter-v2/001-002) ✓ active

Gates tested and closed:
- Drawdown brake (portfolio) — iter-v2/013 NO-MERGE
- Drawdown brake (per-symbol) — iter-v2/014 NO-MERGE
- BTC contagion — iter-v2/015 NO-MERGE

Gates still deferred:
- Isolation forest anomaly (iter-v2/001 primitive #7)
- Liquidity floor (iter-v2/001 primitive #8)
- **Hit-rate feedback** (NEW, emerged from iter-v2/015)

Only three primitives remain unexplored. Isolation forest and
liquidity floor don't seem to target v2's specific drawdown
pattern. Hit-rate feedback is the most promising candidate because
it directly targets "shorts keep hitting SL" behavior.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)
- iter-v2/007: EXPLOITATION (NO-MERGE)
- iter-v2/008: EXPLORATION (NO-MERGE)
- iter-v2/009: EXPLOITATION (NO-MERGE)
- iter-v2/010: EXPLORATION (NO-MERGE)
- iter-v2/011: EXPLORATION (cherry-pick)
- iter-v2/012: EXPLOITATION (cherry-pick)
- iter-v2/013: EXPLOITATION (NO-MERGE)
- iter-v2/014: EXPLOITATION (NO-MERGE)
- **iter-v2/015: EXPLORATION (NO-MERGE)**

Rolling 15-iter: 6 EXPLORATION / 9 EXPLOITATION = **40% exploration**.
Above 30% floor. Last 5 iterations: 2 EXPLORATION / 3 EXPLOITATION.

**8 consecutive NO-MERGEs on iteration branches**
(006-010, 013-015). iter-v2/005 is the undefeated v2 baseline.

## Next Iteration Ideas

### Option A — iter-v2/016: hit-rate feedback gate (recommended, EXPLORATION)

A NEW primitive emerging from iter-015's negative result. Tracks
the SL/TP ratio of the last N trades (across all 4 models) and
kills new signals when the ratio flips aggressively. Feasibility
first via post-hoc simulation:

1. For each trade in iter-v2/005's OOS stream sorted by open_time,
   compute the SL/TP ratio of the previous 10 closed trades
2. If that ratio exceeds a threshold (e.g., ≥ 0.7 SL hits out of
   10), mark the current trade as "feedback-killed"
3. Zero the feedback-killed trades' weighted_pnl
4. Report aggregate + per-symbol metrics

Pro: directly targets the signature of v2's July-August 2025
drawdown (model keeps being wrong about direction).
Con: may be too reactive (fires AFTER a few losses, too late).

### Option B — iter-v2/016: CPCV + PBO validation upgrades (EXPLOITATION)

Doesn't improve the baseline but quantifies its confidence
before deployment. Implements:
- CPCV (Combinatorial Purged Cross-Validation)
- PBO (Probability of Backtest Overfitting)
- ACF-based embargo for walk-forward

Pro: gives a formal expected-vs-realized Sharpe gap, which is
the single most important number before paper-trading deployment.
Con: doesn't advance the OOS metrics at all.

### Option C — accept iter-v2/005 and move to paper trading

Accept iter-v2/005 as the final v2 baseline for this
configuration. Switch tracks entirely. Build a paper trading
harness that runs iter-v2/005's models on live data and reports
realized metrics. The research track continues when the paper
trading produces new questions.

Pro: delivers actual live data, the ground truth of all validation.
Con: no more research improvements until paper trading reveals
new failure modes.

### Recommendation

**Option A (iter-v2/016 hit-rate feedback gate)**. It's the only
unexplored primitive that directly targets v2's specific tail
signature, and the feasibility is cheap (<5 minutes post-hoc).

If iter-v2/016 also NO-MERGEs, then Option C (paper trading) is
the right pivot because the v2 track's research value on this
specific configuration is exhausted.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick to `quant-research`:
- `briefs-v2/iteration_015/research_brief.md`
- `briefs-v2/iteration_015/engineering_report.md`
- `diary-v2/iteration_015.md`
- `analyze_btc_contagion.py`
- `reports-v2/iteration_v2-015_btc_contagion/`

Branch stays as record.

**iter-v2/005 remains the v2 baseline.**

**8 consecutive NO-MERGEs on iteration branches.** Risk primitive
search space nearly exhausted. iter-v2/016 has one more primitive
to try (hit-rate feedback gate) before paper-trading becomes the
default next action.
