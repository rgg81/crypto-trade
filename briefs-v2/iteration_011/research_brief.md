# Iteration v2/011 Research Brief

**Type**: STRATEGIC PIVOT (combined v1+v2 portfolio analysis)
**Track**: v2 — diversification arm → combined portfolio milestone
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/011` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — why the pivot

iter-v2/006-010 produced **5 consecutive NO-MERGEs** targeting the
4th-symbol slot (ADX, Optuna, NEAR 12mo, NEAR 18mo, FIL). None
improved the iter-v2/005 ceiling of 10-seed mean +1.297. The pattern
is now definitive: **the 4th-symbol slot is structurally bounded** —
any L1/storage alt with a 2022 bear training period produces a
hostile, marginally-profitable tail contributor.

Continuing 4th-symbol tuning has diminishing returns. The strategic
pivot recommended by iter-v2/010's diary (§"Strategic Pivot
Recommendation", Option B) is **combined portfolio analysis** — the
actual end-goal of the entire v2 track, which has not been started
despite being the explicit user ask from the start of the session.

> "we could then combine with the v1 trade bot as a portfolio"
> — user, session start

iter-v2/011 is that first combined-portfolio analysis.

## Hypothesis

A naive equal-weight blend of v1's iter-152 portfolio (BTC+ETH+LINK+BNB)
and v2's iter-v2/005 portfolio (DOGE+SOL+XRP+NEAR) should, under the
near-zero v1-v2 correlation already measured in iter-v2/005 (-0.046
on the in-sample period), deliver:

1. **Similar Sharpe** — combined Sharpe in the range of v1's +2.83 to
   v1+v2 ≈ +3.5 depending on how much the uncorrelated v2 track
   contributes.
2. **Better tail behavior** — worst single-day loss strictly below
   v1's worst single day, because v1 and v2 don't crash on the same
   days.
3. **Lower single-symbol concentration** — 47.8% XRP → ~21%, with
   the largest contributor around 20-25%.
4. **More active days** — combined union of v1's 116 OOS trading
   days and v2's 88 days = 150-160 unique trading days.

## Pre-registered failure-mode prediction

The most likely way iter-v2/011's combined analysis disappoints:

> **v1 alone already dominates v2 on risk-adjusted metrics.** v1's
> iter-152 OOS Sharpe is +2.83 with MaxDD 21.81%. v2's iter-v2/005
> OOS Sharpe is +1.67 (seed 42) / +1.297 (10-seed mean) with MaxDD
> 59.88%. Any equal-weight blend of a high-Sharpe low-DD strategy
> with a lower-Sharpe higher-DD strategy will produce a combined
> Sharpe between the two — closer to the average than to the
> maximum.
>
> **Likely outcome**: combined 50/50 Sharpe lands at +2.2 to +2.6,
> below v1 alone but with reduced per-track MaxDD and better
> worst-day behavior. The diversification benefit manifests in
> **tail risk** (worst single day) and **concentration**, NOT in
> average Sharpe.
>
> **Key decision**: if the combined Sharpe is below v1 alone, the
> user must weigh diversification vs. pure risk-adjusted return. If
> the worst combined day is materially better than the worst v1 day,
> diversification wins. If not, v2 is a profitable satellite that
> should run at a small weight (10-30%), not a co-equal.

## Methodology — what `run_portfolio_combined.py` does

This iteration does NOT run any backtests. It loads existing trades
from disk and computes joint metrics:

### Inputs

- **v1 OOS trades**: `/home/roberto/crypto-trade/reports/iteration_152_min33_max200/out_of_sample/trades.csv`
  (164 trades, 4 symbols, canonical iter-152 baseline with min_scale=0.33)
- **v2 OOS trades**: `reports-v2/iteration_v2-005/out_of_sample/trades.csv`
  (117 trades, 4 symbols, canonical iter-v2/005 baseline seed 42)

### Metrics computed

1. Per-track OOS Sharpe, PF, MaxDD, active days (v1, v2, naive-concat,
   proper 50/50 equal-weight)
2. Per-symbol concentration table across all 8 symbols
3. v1-v2 daily return correlation (both union-with-zero-fill and
   both-trading inner join)
4. Diversification benefit: equal-weight combined Sharpe vs each alone
   and vs a theoretical independent-portfolio Sharpe
5. Worst-5-days analysis per track and per combined portfolio

### Why this is single-run (no seeds)

Both inputs are fixed trade streams. v1's iter-152 was 5-seed ensemble;
v2's iter-v2/005 seed 42 is the primary seed (the 10-seed mean +1.297
is already known from iter-v2/005's MERGE validation). The combined
analysis adds no model training, so no seed robustness is relevant
at this layer.

## Success criteria

This is EXPLORATION — an analysis milestone, not a competitive
iteration against a baseline. The goal is **measurement, not
improvement**. Definitions:

- **Success**: combined-portfolio metrics are produced, documented,
  and either validate the diversification thesis OR expose a
  specific failure mode that informs v2 going forward.
- **No MERGE decision** in the usual sense — this is an analysis
  artifact. Research brief + engineering report + diary get
  cherry-picked to `quant-research`.

### Specific questions to answer in Phase 7

1. What is the combined 50/50 OOS Sharpe? Is it above or below v1
   alone?
2. What is the combined MaxDD under proper equal-weight capital
   split (not naive concat)?
3. What is the combined worst single day? Strictly better than v1's
   worst day?
4. What is the v1-v2 daily return correlation computed on both-
   trading days (inner join, not NaN-fill)?
5. What is the optimal blend ratio (inverse-vol, equal-weight,
   Sharpe-weighted) that maximizes combined Calmar?
6. Does adding v2 as a 10-30% satellite to v1 improve tail behavior
   without meaningfully degrading Sharpe?

## Configuration

No backtest. Read-only. Code is `run_portfolio_combined.py`
(already committed at 45f23e2).

## Deferred to iter-v2/012+

- **Combined 10-seed validation**: run v2 10-seed AND v1 5-seed,
  combine each pair of trade streams, report distribution of
  combined Sharpes. Expensive (50 min v1 × 5 seeds + 50 min v2 × 10
  seeds, maybe 200+ min total).
- **Dynamic blend ratio**: compute a time-varying weight based on
  rolling inverse-vol. Adds complexity but improves Calmar under
  regime transitions.
- **Cross-track correlation features**: feed v1 portfolio returns
  into v2 as a cross-asset feature (the reverse direction of v2's
  diversification logic). iter-v2/001's "T1.5 cross-v1 portfolio
  correlation feature" in the skill's idea bank.
- **Live-trade readiness checklist**: paper trading both tracks
  simultaneously, monitoring the realized v1-v2 correlation against
  the OOS baseline of +0.08.

## Section 6: Risk Management Design

Unchanged from iter-v2/005 (v2 side) and iter-152 (v1 side). No new
gates. This iteration is analysis only.

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary: combined
Sharpe lands below v1 alone because v1 has higher standalone Sharpe.
Diversification benefit manifests in tail risk and concentration, not
in average Sharpe. Decision hinges on whether worst-day behavior
justifies the Sharpe drag.
