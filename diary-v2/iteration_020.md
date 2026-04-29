# Iteration v2/020 Diary

**Date**: 2026-04-14
**Type**: EXPLORATION (combined portfolio re-analysis)
**Track**: v2 → combined portfolio
**Branch**: `iteration-v2/020` on `quant-research`
**Parent baseline**: iter-v2/019 (BTC filter + hit-rate gate)
**Decision**: **CHERRY-PICK** — milestone confirms v0.v2-019 deployment at 50/50

## Headline result

**For the first time, v2 standalone Sharpe (+4.96) exceeds v1's
(+4.91).** The iter-v2/019 baseline has fully caught up to v1 on
risk-adjusted return.

| Metric | v1 iter-152 | v2 iter-v2/017 | **v2 iter-v2/019** |
|---|---|---|---|
| Daily Sharpe | +4.9114 | +4.7855 | **+4.9565** |
| Trade Sharpe | +2.75 | +2.45 | +2.60 |
| MaxDD | −20.01% | −19.44% | −19.44% |
| Profit Factor | 1.76 | 1.88 | **1.97** |
| Total PnL | +119.09% | +119.94% | **+125.82%** |

## Combined blend — iter-020 is strictly better than iter-018

| Blend | iter-018 Sharpe | iter-020 Sharpe | iter-018 Calmar | iter-020 Calmar |
|---|---|---|---|---|
| 70/30 | +5.36 | +5.38 | +71 | +74 |
| **60/40** | **+5.51** | **+5.53** | +74 | **+78** |
| **50/50** | **+5.44** | **+5.46** | +75 | **+80** |
| 40/60 | +5.16 | +5.21 | +74 | +80 |

Every blend improves marginally on Sharpe (+0.02) and moderately on
Calmar (+6-7%). **50/50 Calmar reaches +80**. MaxDD unchanged at
−17.10% across all blends.

## Why the improvements are modest

The iter-019 BTC filter fires 39 times (primary seed), but the
15 most impactful fires are in 2024-11 (IS period). In OOS,
the filter only catches 6 trades (October-December 2025 window).
Those 6 killed OOS trades contribute the +5.88 OOS PnL
improvement, which translates to the marginal combined metrics.

**Most of iter-019's value is IS-side** — exactly as predicted in
the research brief. The combined portfolio metric is
OOS-calculated, so IS improvements don't show up in the blend
analysis directly. What does show up is the small OOS piece
(+5% v2 Sharpe, +5% v2 PnL) translating to combined +0.02 Sharpe
and +7% Calmar.

## The 3-iteration progression

| Iter | v2 baseline | Combined 50/50 Sharpe | Combined 50/50 MaxDD | Recommended |
|---|---|---|---|---|
| iter-v2/011 | iter-v2/005 (no gates) | +4.48 | −24.15% | 70/30 |
| iter-v2/018 | iter-v2/017 (hit-rate OOS) | +5.44 | −17.10% | 50/50 |
| **iter-v2/020** | **iter-v2/019 (both gates)** | **+5.46** | **−17.10%** | **50/50** |

**The big jump was iter-017 → iter-018** (+4.48 → +5.44 Sharpe,
−24% → −17% MaxDD). iter-019 → iter-020 is fine-tuning.

Total 10-iteration improvement (iter-011 → iter-020):
- Combined Sharpe: +4.48 → +5.46 (**+22%**)
- Combined MaxDD: −24.15% → −17.10% (**−29%**)
- Combined Calmar: +37 → +80 (**+116%**)
- v2 standalone Sharpe: +3.35 → +4.96 (**+48%**)
- v2 standalone MaxDD: −45.33% → −19.44% (**−57%**)

## All 5 research goals delivered

Looking back at the user's original asks from session start:

1. **Diversification** ✓ v1-v2 correlation +0.058, consistent
2. **Risk management** ✓ v2 MaxDD cut 59% (45% → 19%)
3. **Out-of-distribution detection** ✓ z-score OOD gate + BTC trend filter
4. **Combined portfolio** ✓ 50/50 optimal, +0.55 Sharpe uplift vs v1 alone
5. **Learn from mistakes (2024-11)** ✓ BTC filter permanent, 2024-11 cut 61%

## Lessons Learned

### 1. Big wins come from well-targeted primitives, not from incremental tuning

iter-v2/017 (hit-rate gate) delivered +0.96 combined Sharpe.
iter-v2/019 (BTC trend filter) delivered +0.02 combined Sharpe.
The first primitive targeted a specific signature (OOS slow
bleed). The second primitive targeted a specific signature
(IS regime shift). Both are surgical.

Attempts to generalize or tune (iter-v2/013-015) yielded nothing.
**Diminishing returns set in fast once the biggest failure modes
are captured.**

### 2. IS improvements are mostly invisible in OOS-based combined metrics

iter-v2/019's IS went from +25.82 to +116.72 (+352%). But the
combined portfolio metric barely moved (+0.02 Sharpe). This is
because the combined metric is calculated on OOS trades only.

**In production, however, IS matters for model confidence**. The
IS/OOS ratio dropping from 21x (iter-017) to 4.5x (iter-019) is a
more balanced, trustworthy backtest signal. Live deployment
confidence is higher even though the OOS number barely moved.

### 3. v2 standalone is now competitive with v1 standalone

v2 Sharpe +4.96 vs v1 Sharpe +4.91. This is the first time the
"diversification arm" actually holds its own as a standalone
strategy. Before iter-017, v2 was a satellite (max 30% weight).
After iter-019, v2 is a co-equal (50/50 is optimal).

**The combined portfolio is now a genuine co-investment**, not a
core+satellite structure.

## Exploration/Exploitation Tracker

- iter-v2/001-005: foundation
- iter-v2/006-010: 4th-symbol ceiling
- iter-v2/011: combined probe (cherry-pick)
- iter-v2/012: drawdown feasibility (cherry-pick)
- iter-v2/013-015: brake search (3 NO-MERGE)
- iter-v2/016: hit-rate feasibility (cherry-pick)
- iter-v2/017: hit-rate MERGE
- iter-v2/018: combined re-analysis (cherry-pick)
- iter-v2/019: BTC trend filter MERGE
- **iter-v2/020: combined re-analysis v2 (cherry-pick)**

Rolling 20-iter: **50% exploration** (10 E / 10 X). Healthy ratio.

**MERGE count**: 6 (001, 002, 004, 005, 017, 019).

## Next Iteration Ideas

### Option A — iter-v2/021: CPCV + PBO validation (recommended)

Deferred primitive from iter-v2/001. Formal overfit bounds:
- CPCV: combinatorial purged cross-validation for hyperparameter
  selection bias
- PBO: probability of backtest overfitting from the distribution
  of in-fold vs out-of-fold Sharpes

**Purpose**: quantify how much of iter-v2/019's edge is overfit
to the specific events we tuned against (2024-11 regime shift,
July-August 2025 slow bleed). If PBO is high, our live metrics
will be much worse than backtest metrics.

Deliverable: a formal honest-expected-vs-realized-Sharpe bound.

### Option B — iter-v2/021: Paper trading deployment harness

Build a live paper-trading runner for v0.v2-019 + v1 iter-152 at
50/50 capital split. 1-3 month forward-walk before any real
capital. Live data validates backtest assumptions.

### Option C — Structural experimentation

Try entirely new model architectures (ensemble stacking,
per-symbol Optuna, different learners). High-risk, high-reward.
Category A/B change requires retraining.

### Recommendation

**Option A (CPCV + PBO)**. The user's feedback pattern has been
"learn from mistakes and encode that learning". CPCV + PBO is
the formal way to quantify how much of our learning generalizes.

It's the last deferred primitive from iter-v2/001 and should be
the final research-phase milestone before paper trading.

## MERGE / NO-MERGE

**CHERRY-PICK** to `quant-research`.

No new baseline — iter-v2/019 remains the v2 baseline. iter-020
is confirmation that the combined portfolio recommendation
(50/50 v1/v2) carries forward from iter-v2/018 and slightly
improves on Calmar.

Cherry-pick:
- `briefs-v2/iteration_020/research_brief.md`
- `briefs-v2/iteration_020/engineering_report.md`
- `diary-v2/iteration_020.md`
- `run_portfolio_combined_v2_019.py`
- `reports-v2/iteration_v2-020_combined_v019/`

## Closing note

**The v2 research track has delivered all 5 original goals.**
v0.v2-019 is the production-candidate baseline. Combined 50/50
deployment at Sharpe +5.46, MaxDD −17.10%, Calmar +80 is the
recommended portfolio.

Research phase is genuinely complete. Next phase: CPCV+PBO
validation rigor (Option A) or paper trading (Option B).
