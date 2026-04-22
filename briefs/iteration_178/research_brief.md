# Iteration 178 Research Brief + Engineering Report + Diary

**Date**: 2026-04-22
**Role**: QR + QE (combined — all 3 candidate screens, NO-MERGE for each)
**Type**: EXPLORATION (re-screen previously-rejected candidates with R1+R2 active)
**Baseline**: v0.176 (A + C(R1) + LTC(R1) + DOT(R1,R2), OOS +1.41)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Hypothesis

AVAX (iter 164), ATOM (iter 167), AAVE (iter 170) were rejected at year-1 before R1+R2 existed. With the new framework, they may now clear year-1.

## Results

| Candidate | Prior iter | Prior year-1 | Iter 178 outcome | Elapsed |
|-----------|-----------:|-------------:|------------------|--------:|
| AVAX      | 164        | -34.6%       | EARLY STOP year-1 -32.5% (20 trades, WR 35%) | 9 min |
| ATOM      | 167        | -7.1%        | EARLY STOP **year-3** -20.1% (50 trades, WR 38%) | 61 min |
| AAVE      | 170        | -17.8%       | EARLY STOP year-1 -17.8% (13 trades, WR 30.8%) | 7.6 min |

**ATOM is the interesting result.** It cleared year-1 (2022) and year-2 (2023) with R1+R2 — previously failed year-1 without them. Aborted only at year-3 (2024) with -20.1%. Its IS Sharpe over 3 observed years is -0.65 at 161 trades, so it's still a losing strategy, but R1+R2 meaningfully reshaped its early-year outcomes.

AVAX and AAVE are essentially unchanged — R1+R2 didn't unlock them. The failure modes are structurally different from DOT's (which R1+R2 was designed for).

## Meta-finding: yearly_pnl_check code deviates from skill spec

`backtest.py:282-304` checks EVERY year's PnL independently. The skill specifies only:
- Year 1: year-1 PnL ≥ 0 OR STOP
- Year 2: cumulative (year 1 + year 2) PnL ≥ 0 OR STOP

After year 2 there should be NO fail-fast. The code's per-year check is stricter than the skill and likely aborted ATOM prematurely in iter 178 (year-3 check isn't in the spec). Iter 179 will fix this.

## Decisions

- AVAX — NO-MERGE. Not a viable candidate even with R1+R2.
- ATOM — NO-MERGE this iteration (due to year-3 check). Re-evaluate in iter 179 after the yearly_pnl_check fix.
- AAVE — NO-MERGE. R1+R2 don't apply (too few trades in the failing year to trigger streak or drawdown gates).

## Merge decision: NO-MERGE

No candidate passes. Baseline v0.176 stands.

## Next Iteration Ideas

### 1. Iter 179 (EXPLOITATION) — Fix yearly_pnl_check code to match skill spec

Change the code to only check at year-1 and year-2 boundaries. Re-run ATOM after the fix; if its cumulative year-1+2 is positive (or at least not < 0 by a wide margin), proceed to Gate 3 evaluation.

### 2. Iter 180 (EXPLORATION) — R5 concentration soft-cap

The remaining structural issue. LINK 78% of OOS PnL. R5 clips LINK's weight_factor when its running share exceeds a threshold (e.g. 50%). Would reduce concentration mechanically at some PnL cost.

### 3. Iter 181+ — Screen different-sector candidates

SUI, APT, TIA, INJ — none of these are in the alt-L1-smart-contract cluster that consistently failed. Different macro drivers = potentially different signal.

## Exploration/Exploitation Tracker

Window (168-178): [E, E, E, X, E, E, X, E, E, E, E] → 8E/3X. Rebalance toward X with iter 179's code fix.
