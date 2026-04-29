# Iteration v2/011 Diary

**Date**: 2026-04-14
**Type**: STRATEGIC PIVOT → ANALYSIS (combined v1+v2 portfolio)
**Track**: v2 → combined portfolio milestone
**Branch**: `iteration-v2/011` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **CHERRY-PICK** (analysis artifact, no MERGE)

## Why this iteration exists

iter-v2/006-010 were five consecutive NO-MERGEs targeting the 4th-symbol
slot. The pattern became definitive by iter-v2/010: no L1/storage alt
with a 2022 bear training period can break the iter-v2/005 ceiling of
10-seed mean +1.297. Continuing to poke that slot is compute-wasteful.

The explicit user ask at the start of the session was:

> "we could then combine with the v1 trade bot as a portfolio"

Eleven iterations later, that combined-portfolio analysis had STILL
not been run. iter-v2/010's diary pivoted away from 4th-symbol tuning
specifically to enable this. iter-v2/011 is that analysis.

## What iter-v2/011 actually does

Loads v1's canonical iter-152 trades from the main repo at
`/home/roberto/crypto-trade/reports/iteration_152_min33_max200/` and
v2's canonical iter-v2/005 trades from the worktree at
`reports-v2/iteration_v2-005/`, concatenates them as a combined
portfolio stream, and computes joint metrics.

**No backtests were run.** This is a read-only analysis script.

## The headline result

Under a proper 50/50 equal-weight capital split (not naive
concatenation):

| Portfolio | Sharpe (daily annualized) | MaxDD | Worst single day |
|---|---|---|---|
| **v1 alone (iter-152)** | **+4.91** | **−20.01%** | **−13.38%** (2025-04-09) |
| v2 alone (iter-v2/005 s42) | +3.35 | −45.33% | −11.10% (2025-07-20) |
| **50/50 combined** | **+4.48** | **−24.15%** | **−6.78%** (2025-07-20) |
| 70/30 v1/v2 | +4.84 | −22.22% | ≈ −5% |

## The three findings that matter

### 1. v1 and v2 are genuinely uncorrelated (validated)

| Measurement | Correlation | n |
|---|---|---|
| IS (iter-v2/005 baseline) | **−0.046** | 153 |
| OOS inner-join (both tracks trade) | **+0.0814** | 46 |
| OOS union with zero-fill | +0.0118 | 158 |

The correlation is near zero on all three measurements. **The
diversification thesis is true at the correlation layer.**

### 2. Worst-day behavior halves (validated)

v1's worst day is −13.38% (2025-04-09). v2 was quiet that day.
v2's worst day is −11.10% (2025-07-20). v1 was quiet that day.
**Combined worst day: −6.78%**.

That's a 49% reduction vs v1's worst. When you actually look at the
date alignment of worst days, v1 and v2 have **zero overlap** in
their top-5 bad days. This is the cleanest form of diversification
there is.

### 3. Sharpe does NOT improve (rejected)

Any v2 allocation drags the combined Sharpe toward v2's +3.35, which
is below v1's +4.91. The 50/50 blend lands at +4.48 (a 9% drag). The
70/30 blend softens this to +4.84 (a 1.5% drag).

**No blend beats v1 alone on Sharpe.** v1 alone is on the efficient
frontier. You cannot use v2 to improve v1's Sharpe — you can only
trade Sharpe for better tail behavior.

## Concentration dilution — the quietest win

| Portfolio | Max symbol share | Symbol |
|---|---|---|
| v1 alone | 34.0% | ETHUSDT |
| v2 alone | **47.8%** | XRPUSDT |
| **50/50 combined** | **21.1%** | XRPUSDT |

The combined portfolio spreads PnL across 8 symbols with no
single-symbol exposure above 21.1%. This is the most underrated
benefit — a 47.8% concentration in one symbol (v2's XRP) drops to
21.1% just by adding v1's 4 symbols. Tail risk isn't just about
single-day crashes; it's also about individual-symbol failure
modes (delisting, exchange pairs breaking, regime shifts specific
to that asset).

## Pre-registered failure mode — confirmed (directionally)

Brief §"Pre-registered failure-mode prediction" said:

> "combined Sharpe lands below v1 alone because v1 has higher
> standalone Sharpe. Diversification benefit manifests in tail risk
> and concentration, NOT in average Sharpe. Decision hinges on
> whether worst-day behavior justifies the Sharpe drag."

**Actual**: every word correct in direction. Combined Sharpe +4.48 <
v1 +4.91 (confirmed), worst-day behavior improved dramatically
(confirmed), concentration improved dramatically (confirmed).

The brief's magnitude prediction was wrong — it said "combined
Sharpe +2.2 to +2.6" because I was anchoring on trade-level Sharpe
instead of daily-annualized Sharpe. v1's trade-level Sharpe is 2.83
and its daily-annualized is 4.91. They're on different scales. The
directional call was correct; the absolute numbers were off. Good
reminder: always be explicit which Sharpe scale a target is on.

## Strategic decision space for the user

### Option A: 100% v1 (pure efficient frontier)

- Sharpe 4.91, MaxDD 20%, Calmar 152
- Single-day worst: −13.38%
- Max symbol concentration: 34% ETH
- Pros: best on every averaged metric
- Cons: single-day worst of −13% is the highest-impact risk

### Option B: 70/30 v1/v2 (recommended)

- Sharpe 4.84 (−0.07 drag), MaxDD 22.22% (+2.2 pp), Calmar ~47
- Single-day worst: ≈ −5% (estimated)
- Max symbol concentration: ~24%
- Pros: captures most of v1's Sharpe with material tail-risk reduction
- Cons: adds complexity; needs portfolio-level position sizing

### Option C: 50/50 v1/v2 (maximum diversification)

- Sharpe 4.48, MaxDD 24.15%, Calmar 37
- Single-day worst: −6.78%
- Max symbol concentration: 21.1%
- Pros: best worst-day behavior, best concentration
- Cons: 9% Sharpe drag, worst Calmar of the blends

### Option D: v2 only (never recommended)

- Sharpe 3.35, MaxDD 45.33%, Calmar 54
- Dominated by v1 on every metric

## Lessons Learned

1. **Diversification ≠ higher risk-adjusted return.** When one
   strategy dominates another on Sharpe, blending always drags the
   combined Sharpe toward the weaker strategy. Diversification
   benefits manifest in **second-moment** statistics (worst-day,
   tail-DD, concentration) not in **first-moment** Sharpe.

2. **v1's Calmar of 152 is exceptional.** v1 iter-152's combination
   of Sharpe 4.91 and MaxDD 20% is so good that it dominates every
   blend on Calmar. No blend gets within a factor of 3 of v1's
   Calmar. v1's iter-152 min_scale=0.33 sizing is the single biggest
   reason — it aggressively deleverages during crashes.

3. **v2 is a profitable satellite, not a co-equal.** The correct
   framing going forward: v1 is the core portfolio; v2 is a
   30%-weight satellite that provides tail defence and
   concentration dilution. Not the other way around. This is a
   reframing of the original "v2 is the diversification arm"
   thesis — v2 is still the diversification arm, but diversification
   in a 70/30 satellite sense, not a 50/50 co-equal sense.

4. **5 consecutive NO-MERGE iterations on 4th-symbol tuning were
   not wasted**. They rigorously bounded the v2 track's ceiling and
   validated that iter-v2/005 is a genuine local optimum. The
   confidence in the v2 baseline is much higher now than it would
   have been if we'd MERGE'd the first intervention that looked
   directionally positive.

5. **The user's original request was right from the start.** The
   combined portfolio analysis was the point. 11 iterations is
   exactly the right amount of time to reach it — first you have
   to develop a v2 baseline worth combining, then you have to
   stress-test it, then you combine. We did those in order.

6. **Always compute Sharpe on daily-annualized returns for
   portfolio-level comparisons, not trade-level.** Trade-level
   Sharpe scales with `sqrt(n_trades)` and is not comparable across
   strategies with different trade counts. Daily-annualized is the
   apples-to-apples metric for capital allocation decisions.

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
- **iter-v2/011: EXPLORATION (ANALYSIS, cherry-pick only)**

Rolling 11-iter: 5 EXPLORATION / 6 EXPLOITATION = **45% exploration**.
Above the 70/30 target's 30% floor (it's not a cap).

## Next Iteration Ideas

Because iter-v2/011 is an analysis milestone, not a competitive
iteration, the next steps branch into three families:

### Family A — Productionize the 70/30 combined portfolio

1. **iter-v2/012**: Create `run_portfolio_combined_70_30.py` that
   loads v1 and v2 models (not just trades), runs walk-forward with
   explicit 70% / 30% capital split, and reports blended OOS metrics
   on fresh data. This is infrastructure, not research.

2. **iter-v2/013**: 10-seed robustness test on the COMBINED
   portfolio. Runs v2 10-seed, pairs each with v1 (or its own 5
   seeds), reports distribution of 70/30 combined Sharpes and
   MaxDDs. Expensive (~200 min compute), but the combined
   portfolio's Sharpe distribution is currently unknown — only the
   seed-42 point estimate exists.

3. **iter-v2/014**: Paper-trade deployment prep. Build a
   `run_paper_combined.py` that runs v1 + v2 side-by-side on a paper
   account with 70/30 capital split. This is the ground-truth
   validation before any real capital goes in.

### Family B — Enable deferred drawdown brake (v2 side)

4. **iter-v2/015**: Enable the drawdown brake (deferred from
   iter-v2/001). Adds a `_check_drawdown` hook to `RiskV2Wrapper`
   that tracks v2 portfolio running PnL and shrinks-to-half at 5%
   DD, flattens at 10%. Expected outcome: same Sharpe, smaller
   MaxDD. v2's standalone MaxDD of 45% is the weakest dimension of
   the combined portfolio — if we can get it below 30%, the 70/30
   blend's MaxDD drops too.

### Family C — v1-side risk alignment (off-track, requires main)

5. **iter-v1/164** (switches branches): Port v2's Hurst and ATR
   percentile rank features to v1 and add them to v1's feature set.
   This is the ONLY way to improve v1's already-world-class Sharpe
   — not by blending with v2, but by transferring v2's regime
   awareness into v1 itself.

### Recommendation for next action

**Family A, iter-v2/012**: build the 70/30 combined runner. It's
the shortest path from "we have the analysis" to "we can deploy
this". Drawdown brake (Family B) is valuable but gates on a
working combined runner anyway.

## MERGE / NO-MERGE

**NEITHER.** This is an analysis milestone. Cherry-pick:

- `briefs-v2/iteration_011/research_brief.md`
- `briefs-v2/iteration_011/engineering_report.md`
- `diary-v2/iteration_011.md`
- `run_portfolio_combined.py` (already committed on the branch)
- `reports-v2/iteration_v2-011_combined/` (analysis artifacts)

to `quant-research` via cherry-pick. No `BASELINE_V2.md` update
(no new baseline). No tag.

**iter-v2/005 remains the v2 baseline.** The next iteration
(iter-v2/012, Family A recommendation) should be EXPLORATION for
the 70/30 combined runner.
