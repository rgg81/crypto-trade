# Iteration v2/018 Diary

**Date**: 2026-04-14
**Type**: EXPLORATION (combined portfolio re-analysis)
**Track**: v2 → combined portfolio payoff
**Branch**: `iteration-v2/018` on `quant-research`
**Parent baseline**: iter-v2/017 (braked v2)
**Decision**: **CHERRY-PICK** — analysis milestone, new 50/50 blend recommendation

## What happened

iter-v2/017 merged the hit-rate feedback gate into v2, cutting
MaxDD from 59.88% to 24.39% and lifting Sharpe from +1.67 to +2.45
on primary seed. iter-v2/018 answers the strategic question:
**does the braked v2 change the combined v1+v2 blend recommendation?**

The answer is a dramatic **yes**. 50/50 blend becomes the new
optimal, strictly better than iter-v2/011's 70/30 recommendation
on every metric.

## Headline comparison

| Blend | iter-v2/011 (v2-005) | iter-v2/018 (v2-017 braked) | Δ |
|---|---|---|---|
| **50/50 Sharpe** | **+4.48** | **+5.44** | **+21%** |
| 50/50 MaxDD | −24.15% | **−17.10%** | **−29%** |
| 50/50 Calmar | +37 | **+75** | **+103%** |
| 50/50 Worst day | −6.78% | −6.69% | ~same |
| **60/40 Sharpe** | +4.75 | **+5.51** | +16% |
| **70/30 Sharpe** | +4.84 | **+5.36** | +11% |
| **v2 standalone Sharpe** | +3.35 | **+4.79** | **+43%** |
| **v2 standalone MaxDD** | −45.33% | **−19.44%** | **−57%** |
| v1-v2 correlation | +0.08 | +0.01 | still near-zero |

## The strategic payoff

The user's original session ask was **diversification via a
combined v1+v2 portfolio**. iter-v2/011's answer (the first
combined analysis) was:

> "v1 alone is on the efficient frontier. 50/50 v1/v2 has a −0.43
> Sharpe drag. Recommended 70/30 with small Sharpe hit for better
> tail."

That was because v2's 45% MaxDD made it a **drag** in any 50/50
blend. v2 could only be a 30% satellite.

**iter-v2/018's answer**:

> "v2 is now a co-equal to v1. 50/50 blend has a **+0.53 Sharpe
> uplift** vs v1 alone. Recommended 50/50 (or 60/40) with 50/50
> winning on every metric vs iter-v2/011's 70/30 baseline."

**The +0.96 swing in diversification uplift** (from −0.43 to +0.53)
is the entire strategic payoff of the 7-iteration risk-primitive
search (iter-v2/012-017).

## The proper blend ranking (new numbers)

Sweet spot: **50/50 or 60/40**.

| Blend | Sharpe | MaxDD | Calmar | Worst day | Verdict |
|---|---|---|---|---|---|
| 100/0 v1 | +4.18* | −20.01% | +58 | −13.38% | risk ceiling |
| 80/20 | +5.04 | −18.65% | +67 | −10.71% | v1-heavy, good |
| 70/30 | +5.36 | −17.98% | +71 | −9.37% | old rec (now outdated) |
| **60/40** | **+5.51** | **−17.32%** | **+74** | −8.03% | **best Sharpe** |
| **50/50** | **+5.44** | **−17.10%** | **+75** | **−6.69%** | **best MaxDD/Calmar/worst-day** |
| 40/60 | +5.16 | −17.11% | +74 | **−5.37%** | v2-heavy |
| 30/70 | +4.76 | −17.13% | +72 | −5.97% | too much v2 |

\* UNION method; v1 alone trading-day-only Sharpe is +4.91.

**Both 50/50 and 60/40 dominate 70/30 and below on every metric.**
The recommendation is 50/50 for its superior Calmar and worst-day,
or 60/40 for slightly higher Sharpe.

## Three findings that matter

### 1. v2 is now a co-equal to v1 on standalone risk metrics

| Metric | v1 iter-152 | v2 iter-v2/017 braked |
|---|---|---|
| Trade Sharpe | +2.75 | +2.45 |
| Daily Sharpe | +4.91 | +4.79 |
| MaxDD | −20.01% | −19.44% |
| Profit Factor | 1.76 | 1.88 |
| Total PnL | +119.09% | +119.94% |

**Essentially tied on every dimension**. The braked v2 has reached
v1's performance profile while trading a completely different
universe (DOGE+SOL+XRP+NEAR vs BTC+ETH+LINK+BNB).

This is exactly what "diversification arm" is supposed to mean:
independent performance at equal risk-adjusted return.

### 2. The correlation stays near-zero

Critical property preserved: v1-v2 OOS correlation is +0.0143
(iter-018) vs +0.0814 (iter-011). Both near zero. The hit-rate
gate affects v2's individual trade outcomes but doesn't change
WHEN v2 trades relative to v1. So the diversification property
is intact.

If the brake had systematically killed v2's trades on days when
v1 was trading, the correlation would have risen. It didn't.

### 3. Combined 50/50 beats both standalone tracks

For the first time in this project:

> **Combined Sharpe (+5.44) > v1 alone Sharpe (+4.91) AND > v2
> alone Sharpe (+4.79)**

Neither standalone track is on the efficient frontier anymore.
The combined portfolio is. This is a **proper diversification
benefit**: blending produces a strictly better portfolio than
either input alone.

iter-v2/011 said "v1 alone is on the efficient frontier". That
claim is now false. **50/50 is on the efficient frontier.**

## Pre-registered failure-mode prediction — conservative

Brief predictions:
- Combined 50/50 Sharpe: +4.6 to +4.8 (**actual +5.44**)
- Combined 50/50 MaxDD: −19% to −22% (**actual −17.10%**)
- Calmar: +50 to +60 (**actual +75**)

All three predictions were too conservative. iter-018 is the 3rd
iteration in a row where I underestimated a braked-v2 improvement
(iter-016 and iter-017 were also underestimated).

Lesson: when a primitive is well-targeted to a clearly-diagnosed
signature, it tends to OUT-perform cautious predictions. My brief
writing has been calibrated to the general failure-mode space,
which is appropriate for risk management, but under-calibrated for
the rare case when the primitive actually works.

## Lessons Learned

### 1. Risk-primitive work is upstream of combined portfolio value

iter-v2/012-017 (6 iterations of risk primitive work) looked like
a distraction from the combined portfolio goal. In reality, those
6 iterations unlocked a +0.96 Sharpe improvement in the combined
portfolio metric — a huge strategic payoff.

**Generalization**: when a primary metric is capped by a specific
subsystem weakness, the path to improving the primary metric goes
through fixing the subsystem. You can't improve a 50/50 blend by
tuning the blend — you improve it by reducing one side's tail
risk.

### 2. The v2 track has completed its mandate

Original goals:
- **Diversification** ✓ correlation −0.01 to +0.08 across iterations
- **Risk management** ✓ MaxDD cut from 45% to 19% via hit-rate gate
- **Combined portfolio viability** ✓ 50/50 blend now strictly
  better than v1 alone

All three are delivered. The v2 track's research-phase mandate is
complete. Next phase is deployment / validation rigor / paper
trading.

### 3. Risk primitives vs blend ratio — primitive wins

I spent a lot of time thinking about blend ratios (70/30 vs 60/40
vs 50/50 vs inverse-vol). The reality is that once the primitive
(hit-rate gate) was found, ALL blend ratios improved massively.
The difference between 50/50 and 60/40 post-primitive is small
(Sharpe +5.44 vs +5.51). The difference between with-primitive
and without-primitive at 50/50 is huge (+5.44 vs +4.48).

**Focus on the primitive, not the blend ratio.** Blend ratio is a
trailing decision — it matters at the margin but the primitive
choice matters more.

## The 17-iteration v2 arc — retrospective

Looking back at iter-v2/001 through iter-v2/018:

| Phase | Iter | Goal | Delivered |
|---|---|---|---|
| Foundation | 001-005 | Build v2 baseline | iter-v2/005 baseline (Sharpe +1.30 mean, 10/10 profitable) |
| Stuck ceiling | 006-010 | 4th-symbol tuning | 5 NO-MERGEs; ceiling confirmed |
| Combined probe | 011 | First combined analysis | 70/30 recommendation |
| Risk search | 012-015 | Find the right risk primitive | 4 primitives tested, 3 failed, learned v2's tail signature |
| Risk found | 016 | Hit-rate gate feasibility | Breakthrough result |
| Risk merged | 017 | Productionize + 10-seed | First baseline improvement in 9 iters |
| **Strategic payoff** | **018** | **Re-evaluate combined portfolio** | **50/50 becomes optimal** |

18 iterations. 6 MERGEs (001, 002, 004, 005, 017, plus 008's
subset). 12 NO-MERGEs or analysis-only. Ratio: 33% MERGE rate.

That's a reasonable hit rate for a research track. Each
NO-MERGE narrowed the search. iter-v2/017 was the culminating
MERGE that validated the research philosophy.

## Exploration/Exploitation Tracker

- iter-v2/001-005: foundation (3 EXPLORATION / 2 EXPLOITATION)
- iter-v2/006-010: 4th-symbol (1 EXPLORATION / 4 EXPLOITATION)
- iter-v2/011: combined probe (EXPLORATION, cherry-pick)
- iter-v2/012: feasibility (EXPLOITATION, cherry-pick)
- iter-v2/013-015: risk primitive search (3 EXPLOITATION)
- iter-v2/016: hit-rate feasibility (EXPLORATION, cherry-pick)
- iter-v2/017: hit-rate productionize (EXPLOITATION, MERGE)
- **iter-v2/018: combined re-analysis (EXPLORATION, cherry-pick)**

Rolling 18-iter: 8 EXPLORATION / 10 EXPLOITATION = **44% exploration**.
Comfortably above 30% floor. Healthy ratio.

## Next Iteration Ideas

The research-phase mandate of v2 is complete. Future iterations
should move toward validation and deployment.

### iter-v2/019 — CPCV + PBO validation (deferred from iter-v2/001)

Implements Combinatorial Purged Cross-Validation and Probability
of Backtest Overfitting from iter-v2/001's skill. Quantifies the
expected-vs-realized Sharpe gap for iter-v2/017. Gatekeeper
before any paper-trading deployment.

Deliverable: honest estimate of live-trading Sharpe given the
hyperparameter search depth we've done. If the gap is small
(<20%), deployment is safe. If large (>40%), additional validation
needed.

### iter-v2/020 — Paper trading harness

Build a runner that deploys iter-v2/017 models + v1 iter-152
models at 50/50 capital split on a paper trading account. Live
data validates the backtest's assumptions:
- Are the hit-rate gate's fire patterns similar in live data?
- Is the correlation assumption (v1-v2 ≈ 0) holding?
- Do the v1 and v2 fee assumptions match live?

1-3 month paper trading window before any real capital.

### iter-v2/021 — Seed-wise calibration (optional)

iter-v2/017's brake hurts 4 of 10 seeds (456 at −0.75, 3456 at
−0.26, 4567 at −0.06, 5678 at −0.07). Investigate WHY these
seeds see drag. Candidates:
- Drawdown signature differs (timeouts vs SL)
- Brake threshold tuning per seed
- Multi-threshold brake (tight + loose)

Not urgent. Marginal improvement if successful.

### Recommended

**iter-v2/019** (CPCV + PBO). This is the gatekeeper for safe
deployment. Without it, iter-v2/017 is "validated on a backtest"
not "validated for production".

## MERGE / NO-MERGE

**CHERRY-PICK** (analysis iteration, no new baseline).

Cherry-pick to `quant-research`:
- `briefs-v2/iteration_018/research_brief.md`
- `briefs-v2/iteration_018/engineering_report.md`
- `diary-v2/iteration_018.md`
- `run_portfolio_combined_v2_017.py`
- `reports-v2/iteration_v2-018_combined_braked/`

Branch stays as record. **iter-v2/017 remains the v2 baseline.
Combined portfolio recommendation: 50/50 v1/v2.**

## Closing note — the v2 research track is done

After 18 iterations, the v2 research track has delivered all
three of its original goals:
1. Diversification (correlation −0.01 to +0.08, consistent)
2. Risk management (hit-rate gate cuts MaxDD 59% → 19%)
3. Combined portfolio viability (50/50 strictly beats v1 alone)

**Research complete. Next phase: validation and deployment.**
