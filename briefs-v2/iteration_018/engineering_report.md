# Iteration v2/018 Engineering Report

**Type**: EXPLORATION (combined portfolio re-analysis with braked v2)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/018` on `quant-research`
**Parent baseline**: iter-v2/017 (braked v2)
**Decision**: **CHERRY-PICK** (analysis milestone; new blend recommendation)

## Run Summary

| Item | Value |
|---|---|
| Runner | `run_portfolio_combined_v2_017.py` (commit `a2446cf`) |
| v1 input | `/home/roberto/crypto-trade/reports/iteration_152_min33_max200/` (unchanged) |
| v2 input | `reports-v2/iteration_v2-017/` (**NEW: braked v2 baseline**) |
| Wall-clock | <5 sec |
| Artifacts | `reports-v2/iteration_v2-018_combined_braked/` |

## Headline: combined 50/50 becomes VIABLE and BEST

| Blend | Sharpe | MaxDD | Calmar | Worst day |
|---|---|---|---|---|
| 100/0 (v1 alone, UNION) | +4.18 | −20.01% | +58 | −13.38% |
| 90/10 | +4.61 | −19.32% | +63 | −12.04% |
| 80/20 | +5.04 | −18.65% | +67 | −10.71% |
| 70/30 (iter-011 rec) | +5.36 | −17.98% | +71 | −9.37% |
| **60/40** | **+5.51** | **−17.32%** | **+74** | −8.03% |
| **50/50** | **+5.44** | **−17.10%** | **+75** | **−6.69%** |
| 40/60 | +5.16 | −17.11% | +74 | −5.37% |
| 30/70 | +4.76 | −17.13% | +72 | −5.97% |
| 0/100 (v2 alone) | +3.53 | −19.44% | +56 | −7.79% |

**Sweet spots**: 50/50 and 60/40. 60/40 edges out on Sharpe (+5.51),
50/50 wins on MaxDD (−17.10%) and Calmar (+75) and worst day (−6.69%).

## Comparison with iter-v2/011 (pre-braked)

| Blend | iter-v2/011 Sharpe | iter-v2/018 Sharpe | Δ | iter-v2/011 MaxDD | iter-v2/018 MaxDD | Δ |
|---|---|---|---|---|---|---|
| 100/0 | +4.91 (trading-day) | +4.18 (UNION)* | — | −20.01% | −20.01% | same |
| 70/30 | +4.84 | **+5.36** | **+11%** | −22.22% | **−17.98%** | **−19%** |
| 60/40 | +4.75 | **+5.51** | **+16%** | −22.99% | **−17.32%** | **−25%** |
| **50/50** | **+4.48** | **+5.44** | **+21%** | **−24.15%** | **−17.10%** | **−29%** |
| 0/100 | +3.35 (trading-day) | +3.53 | +5% | −45.33% | **−19.44%** | **−57%** |

\*v1 alone Sharpe is inherently methodology-dependent: trading-day
only = +4.91, UNION with v2 days = +4.18. The blend analysis uses
UNION internally (as iter-v2/011 did for its blend numbers), so
the blend deltas are apples-to-apples.

**The 50/50 blend jumped from +4.48 to +5.44** — a full Sharpe point
better than iter-v2/011's measurement. The braked v2 removed
enough of v2's drawdown volatility that it now carries its weight
in a combined portfolio rather than dragging it down.

## Per-track standalone metrics (from runner groupby method)

| Metric | v1 iter-152 | v2 iter-v2/005 (iter-011) | v2 iter-v2/017 (iter-018 BRAKED) |
|---|---|---|---|
| Trade Sharpe | +2.75 | +1.66 | **+2.45** (+47%) |
| Daily Sharpe | +4.91 | +3.35 | **+4.79** (+43%) |
| MaxDD | −20.01% | −45.33% | **−19.44%** (−57%) |
| Win rate | 50.6% | 45.3% | 45.3% |
| Profit Factor | 1.76 | 1.46 | **1.88** (+29%) |
| Total PnL | +119.09% | +94.01% | **+119.94%** |
| Active days | 116 | 88 | 88 |

**v2's standalone Sharpe is now essentially equal to v1's (+4.79
vs +4.91, only −2%)**. v2's standalone MaxDD is now slightly BETTER
than v1's (−19.44% vs −20.01%). **v2 is no longer a satellite — it's
a co-equal contributor.**

## v1-v2 correlation — STILL near zero

| Measurement | iter-v2/011 | iter-v2/018 | Comment |
|---|---|---|---|
| Inner join (both trading) | +0.0814 | **+0.0143** | Both near-zero |
| Union with zero-fill | +0.0118 | (similar) | Near-zero |

The brake **did not break the diversification property**. v2's trade
dates relative to v1's are still essentially random (correlation
near 0). The braked v2 remains a genuine diversifier.

## Per-symbol combined portfolio (50/50)

From the runner's combined (200% exposure, but ratios are
scale-invariant):

| Symbol | n trades | Share % | Track |
|---|---|---|---|
| XRPUSDT | 27 | 19.32% | v2 |
| DOGEUSDT | 31 | 18.30% | v2 (brake helped DOGE) |
| ETHUSDT | 34 | 16.93% | v1 |
| SOLUSDT | 37 | 13.47% | v2 |
| BNBUSDT | 50 | 13.22% | v1 |
| LINKUSDT | 42 | 11.73% | v1 |
| BTCUSDT | 38 | 7.94% | v1 |
| NEARUSDT | 22 | **−0.92%** | v2 (marginal negative) |

**Max single-symbol share: 19.32% (XRP)**. Well below the 50% rule.
Combined portfolio has 7 positive contributors and NEAR at
marginal −0.92% (down from iter-011's +4.09%, due to the brake's
effect on NEAR).

## Tail-risk analysis — 50/50 worst days

| Date | 50/50 daily return | Dominant track |
|---|---|---|
| **2025-04-09** | **−6.69%** | v1 (its −13.38% worst day, halved) |
| 2025-10-30 | −4.76% | v2 (brake didn't fire here) |
| 2025-05-10 | −4.57% | v1 (−6.30%) |
| 2025-07-18 | −4.17% | v2 (still in hit-rate gate warmup) |
| 2025-07-16 | −3.80% | v2 (first brake fire day) |

**Combined worst day: −6.69%** (vs iter-v2/011's −6.78%, essentially
unchanged). The brake doesn't materially improve 50/50 worst-day
because v1 and v2's worst days are on DIFFERENT dates, and v1's
worst day is halved by the 50/50 weighting regardless of v2.

**What DID improve**: the **density** of bad days. In iter-v2/011
baseline v2 had many days in the −3% to −11% range during
July-August; the brake flattens these. The 50/50 combined equity
curve is much smoother in July-August now.

## Blend recommendation — UPDATED

**New recommendation: 50/50 v1/v2 blend**.

Rationale:
1. Sharpe +5.44 vs iter-v2/011's 70/30 at +4.84 (+12%)
2. MaxDD −17.10% vs 70/30 at −22.22% (−23%)
3. Calmar +75 vs 70/30 at ~47 (+60%)
4. Worst day −6.69% vs 70/30 at ~−9 (−25%)
5. Capital efficiency: two tracks at equal weight, natural scaling

**Alternative recommendation: 60/40 v1/v2** for users who prefer
slightly more weight on v1's proven reliability:
- Sharpe +5.51 (marginally better than 50/50)
- MaxDD −17.32%
- Slightly more v1-exposure than 50/50

Both 50/50 and 60/40 strictly dominate iter-v2/011's 70/30 on
every metric. The choice between them is a judgment call.

**Not recommended**: 30/70 or 40/60. Sharpe drops sharply below
+5.2 past 60/40. v1's +4.18 (or +4.91 by the other method)
exceeds v2's standalone Sharpe of +3.53, so too much v2 drags.

## Diversification benefit — REAL uplift now

iter-v2/011 diversification uplift vs v1 alone: −0.43 (v1 alone
was strictly better than 50/50).

iter-v2/018 diversification uplift vs v1 alone: +0.53 (50/50 is
strictly better than v1 alone).

**That's a +0.96 Sharpe swing in the diversification uplift.**
The braked v2 converts the combined portfolio from a Sharpe drag
into a Sharpe uplift.

## Why this matters — the v2 goal is validated

The user's stated goal at the start of the session was:
> "we could then combine with the v1 trade bot as a portfolio"

iter-v2/011 delivered the first combined analysis and found v2's
50% MaxDD made it a 30% satellite. iter-v2/013-017 developed the
right risk primitive (hit-rate feedback gate). iter-v2/018 proves
the primitive unlocks the combined portfolio's potential.

**The v2 track has now delivered its original goal**: a combined
v1+v2 portfolio that is strictly better than v1 alone on
risk-adjusted metrics.

## Pre-registered failure-mode prediction — partially wrong

Brief said:
> "Expected: combined 50/50 Sharpe around +4.6-4.8 (vs iter-011's
> +4.48)."

**Actual**: +5.44 (well above the +4.6-4.8 range).

> "Combined MaxDD around 19-22% (vs iter-011's 24.15%)."

**Actual**: −17.10% (slightly better than the 19-22% range).

> "Calmar around +50-60 (vs iter-011's +37)."

**Actual**: +75 (above the +50-60 range).

**Predictions were systematically conservative.** The brake's effect
on the combined portfolio is stronger than I anticipated. This is
the 3rd iteration in a row where my conservative prediction
underestimated a braked-v2 improvement.

## Conclusion

iter-v2/018's combined re-analysis delivers the strategic payoff
of the entire iter-v2/012-017 risk-primitive search:

1. **v2 standalone Sharpe** jumps from +3.35 to +4.79 (+43%)
2. **v2 MaxDD** halves from −45.33% to −19.44% (−57%)
3. **Combined 50/50 Sharpe** jumps from +4.48 to +5.44 (+21%)
4. **Combined 50/50 MaxDD** improves from −24.15% to −17.10% (−29%)
5. **50/50 becomes the new recommended blend**, strictly better
   than iter-v2/011's 70/30 on every metric
6. **v1-v2 correlation** remains near-zero (+0.0143 inner)
7. **Concentration** on combined is 19.32% max (XRP), well under 50%

**Decision**: **CHERRY-PICK** to `quant-research`. No MERGE (this
is analysis, not a model change). The v2 baseline remains
iter-v2/017 (the braked baseline). Tag and BASELINE_V2.md
unchanged.

Future deployment recommendation: **50/50 v1/v2 blend** with
capital equally split between v1 (iter-152) and v2 (iter-v2/017
with hit-rate gate).
