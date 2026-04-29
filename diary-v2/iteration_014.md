# Iteration v2/014 Diary

**Date**: 2026-04-14
**Type**: EXPLOITATION (per-symbol drawdown brake feasibility)
**Track**: v2 — risk arm
**Branch**: `iteration-v2/014` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, XRP 47.75%)
**Decision**: **NO-MERGE** (all 4 configs fail concentration; drawdown brake lineage closed)

## What happened

iter-v2/013's portfolio drawdown brake NO-MERGEd on concentration
(XRP 78.55%). The failure mode was cross-symbol contamination: the
portfolio brake flattens ALL trades during portfolio DD, killing
SOL/NEAR winners while saving DOGE losses.

iter-v2/014's hypothesis: a **per-symbol brake** where each model
tracks its own compound equity DD would avoid cross-symbol
contamination. Each symbol's brake fires only on its own DD.

**Result**: all 4 per-symbol brake configurations FAIL the
concentration rule. Best config (D 4/8) achieves Sharpe +1.45,
MaxDD −13.83%, Calmar +4.31 — strong aggregate metrics — but XRP
concentration is 68.76% (strict rule 50%).

More damning: per-symbol brake's **concentration is WORSE than
portfolio brake's** on 2 of 4 configs (113.12% for B, 92.65% for
A) and only slightly better on the others. And its Sharpe is
WORSE than portfolio brake's (+1.35 for C vs +1.60 for
iter-v2/013 C).

## The headline numbers

| Config | Sharpe (trade) | MaxDD | MaxConc | Pass? |
|---|---|---|---|---|
| None (baseline) | +1.66 | −45.33% | 47.75% | — |
| A (5/10) | +1.18 | −19.35% | **92.65%** | FAIL |
| B (6/12) | +0.90 | −28.20% | **113.12%** | FAIL |
| C (8/16) | +1.35 | −27.84% | **71.80%** | FAIL |
| **D (4/8)** | **+1.45** | **−13.83%** | **68.76%** | **FAIL** (closest) |

No config passes. The best is D, still 13.76 percentage points
above the 55% soft limit (and 18.76 pp above the strict 50%).

## Root cause — XRP is structurally dominant

The per-symbol brake decides state from each symbol's OWN
compound equity DD. XRP's per-symbol OOS curve goes nearly
straight up over the OOS period (27 trades, 55.6% WR, +44.89
weighted PnL, no major drawdown). So XRP's per-symbol DD almost
never hits the 4-8% threshold.

Result: XRP's brake rarely fires, XRP keeps nearly all its
contribution. DOGE/SOL/NEAR have more volatile per-symbol curves
and hit their thresholds easily — their brakes fire heavily,
attenuating their contributions by 50-80%.

**Per-symbol brake firing rates (Config D)**:

| Symbol | Normal | Shrink | Flatten | Fire rate |
|---|---|---|---|---|
| DOGE | 7 | 1 | **23** | **77%** |
| SOL | 11 | 7 | 19 | 70% |
| NEAR | 7 | 5 | 10 | 68% |
| **XRP** | **21** | 5 | 1 | **22%** |

Three symbols fire at 68-77% rates. XRP fires at 22%. The
asymmetry is huge.

Ratio shift: XRP keeps 82% of its baseline contribution; DOGE
keeps 98% (brake saved DOGE from losses, DOGE still grows); SOL
keeps 6%; NEAR keeps 43%. XRP's SHARE in the surviving total
becomes 68.76% because SOL and NEAR are heavily depleted.

## The 3-iteration brake lineage — definitively closed

| Iter | Design | Sharpe | MaxDD | XRP Conc | Verdict |
|---|---|---|---|---|---|
| 012 | Feasibility, portfolio brake | +1.60 | −13.35% | not checked | PASS on aggregate |
| 013 | Productionize portfolio brake | +1.60 | −16.41% | **78.55%** | NO-MERGE on concentration |
| 014 | Per-symbol brake feasibility | +1.45 | −13.83% | **68.76%** | NO-MERGE on concentration |

**The drawdown brake primitive is conceptually valid for risk
reduction** (both iterations show 70%+ MaxDD improvement) but
**structurally incompatible with this 4-symbol portfolio**. XRP's
contribution cannot be preserved alongside attenuation of the
other three without blowing out concentration.

This is not a tunable problem. It's a geometry problem: the
brake's per-symbol state is non-uniform, and XRP happens to be
the symbol with the flattest per-symbol curve. No amount of
threshold tuning changes that.

## Lessons Learned

### 1. Concentration constraints can invalidate otherwise-good risk primitives

iter-v2/012 looked great on aggregate. iter-v2/013 looked great
on aggregate. Both failed concentration because the brake's
effect on per-symbol contributions is non-uniform.

**Generalization**: every risk primitive that operates on
trades (rather than on signals) must be tested for per-symbol
impact BEFORE productionization. Decompose the effect by
symbol, check if any symbol goes from positive to negative,
check if the max-concentration ratio stays within the rule.

### 2. "Per-symbol" brakes aren't better than "portfolio" brakes when a dominant symbol exists

Intuitively, per-symbol brakes should avoid cross-symbol
contamination. And they do — no cross-symbol winners are killed
because each symbol is braked on its own DD. BUT the dominant
symbol (XRP here) rarely DDs, so its contribution is preserved
while the minor symbols are attenuated. This amplifies the
dominance ratio.

**Generalization**: if a portfolio has a dominant contributor,
per-symbol attenuation primitives will make it MORE dominant,
not less. The correct fix for dominance is a **rebalancing
primitive** (constrain the top symbol's share), not an
attenuation primitive (attenuate everyone else's losses).

### 3. The iter-v2/005 baseline is the v2 local optimum

Five consecutive NO-MERGEs on 4th-symbol tuning (iter-v2/006-010)
established that iter-v2/005 is the ceiling for 4-symbol v2.
Three consecutive NO-MERGEs on drawdown brake (iter-v2/012-014,
with 012 as cherry-pick) now establish that the same baseline
is the ceiling for this risk-primitive family.

**iter-v2/005 with its +1.297 10-seed mean, 59.88% MaxDD,
47.75% concentration is the final v2 baseline for this
configuration.** Further improvements require either:
- A fundamentally different symbol basket (add/remove symbols)
- A fundamentally different risk primitive (BTC contagion,
  isolation forest, liquidity floor)
- A fundamentally different validation approach (CPCV + PBO)
- A different model architecture (ensemble stacking, etc.)

### 4. XRP's dominance is a feature, not a bug

XRP had 55.6% win rate and +44.89 weighted PnL in iter-v2/005
OOS. That's the best per-symbol profile in the portfolio. It's
the REASON iter-v2/005 is +1.297 instead of much lower.

Attenuating XRP to improve concentration would DEGRADE the
baseline metric. Preserving XRP while attenuating others blows
out concentration. This is a zero-sum trade-off.

The only way out is to dilute XRP's denominator — add a 5th
symbol or scale up other symbols' gross exposure. Neither is a
brake-architecture change.

## Six-plus consecutive NO-MERGE tracker

iter-v2/006-010 (5 consecutive) + iter-v2/013 + iter-v2/014 = **7
consecutive NO-MERGEs** on iteration branches (not counting
011 and 012 which were cherry-pick analyses). The "3+ consecutive
NO-MERGE" rule mandates a full research checklist on the next
iteration — which iter-v2/014's brief already covered.

The next iteration (015+) also needs the full research checklist
given the persistent NO-MERGE streak.

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
- **iter-v2/014: EXPLOITATION (NO-MERGE)**

Rolling 14-iter: 5 EXPLORATION / 9 EXPLOITATION = **36% exploration**.
Still above 30% floor.

Too many exploitations. Next iteration should be EXPLORATION to
rebalance the ratio.

## Next Iteration Ideas

### iter-v2/015 — BTC contagion circuit breaker (RECOMMENDED, EXPLORATION)

Primitive #6 from iter-v2/001. Unconditionally kills ALL v2
positions when BTC's 1h or 24h return drops below a threshold
(typically −5% for a single bar).

**Why it could work where drawdown brake failed**:
- BTC signal is SYMMETRIC across all 4 v2 symbols: the same
  "BTC fell 5%" event fires the same kill for DOGE, SOL, XRP,
  NEAR simultaneously.
- Attenuation is uniform across symbols, so concentration stays
  roughly unchanged.
- Complementary to feature z-score OOD: catches fast cross-asset
  crashes that the z-score gate (which is per-symbol feature
  distribution) doesn't see.
- Doesn't suffer the XRP dominance problem because it doesn't
  use per-symbol DD at all.

**Implementation**: read BTCUSDT's kline data, compute 1h and
24h return for each bar, flag cross-asset crash windows. Apply
as a pre-filter to all v2 signals (kill signal if any active
crash flag is set for this bar's open_time).

Feasibility first via post-hoc simulation on iter-v2/005 trades.

### iter-v2/016 — CPCV + PBO validation upgrades (EXPLOITATION)

Deferred from iter-v2/001's skill. Adds:
- **CPCV** (Combinatorial Purged Cross-Validation) for more
  robust hyperparameter selection
- **PBO** (Probability of Backtest Overfitting) for honest
  expected-vs-realized Sharpe gap estimation

Not a baseline improvement but a **confidence booster** for
deploying iter-v2/005 to paper trading.

### iter-v2/017 — add 5th symbol (Model I) to dilute XRP

Use the 6-gate screening from iter-v2/001 to pick AVAX or UNI
as Model I. Add it to the 4-model runner, re-train, measure.

Expected outcome: XRP's share drops from 47.75% to ~38%,
concentration headroom opens up, and future risk primitives
(including drawdown brake) can fire on XRP without blowing
out concentration.

**Risk**: a 5th symbol might not pass stand-alone profitability.
The iter-v2/005 4-symbol choice was already optimized; adding a
5th symbol may add variance without adding edge.

### Recommendation

**iter-v2/015: BTC contagion circuit breaker**. It's the only
risk primitive that bypasses the XRP dominance problem and it's
been deferred since iter-v2/001. EXPLORATION category, which
helps rebalance the exploration ratio.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick to `quant-research`:
- `briefs-v2/iteration_014/research_brief.md`
- `briefs-v2/iteration_014/engineering_report.md`
- `diary-v2/iteration_014.md`
- `analyze_per_symbol_brake.py`
- `reports-v2/iteration_v2-014_per_symbol_brake/`

Branch stays as record.

**iter-v2/005 is the final v2 baseline.** The drawdown brake
lineage is closed. iter-v2/015 pivots to BTC contagion.
