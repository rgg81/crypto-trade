# Iteration 179

**Date**: 2026-04-22
**Role**: QR + QE combined
**Type**: EXPLOITATION (code fix) + validation
**Baseline**: v0.176 — unchanged

## Summary

Fix `yearly_pnl_check` in `run_backtest` to match the skill spec (year-1 and year-1+2 cumulative boundary checks only; silent after year 2). Previously the code checked EACH year independently, which was stricter than the skill and aborted candidates that would have been allowed to run under the correct rule.

Re-tested ATOM with the fixed code: ran to completion. Confirmed ATOM is NOT viable (IS Sharpe −0.60, OOS Sharpe −0.97, both halves of the data show negative PnL). Rejection in iter 178 was correct in outcome but reached via a buggy check.

## Code change

`src/crypto_trade/backtest.py:282-325` (yearly_pnl_check block):

- **Old**: fires at every year boundary, checks that year's PnL alone.
- **New**: fires at year-1 boundary (checking year-1 alone) and year-2 boundary (checking year-1+2 cumulative). Silent thereafter.

## ATOM with corrected check

| Metric  | IS      | OOS     |
|---------|--------:|--------:|
| Sharpe  | −0.596  | −0.967  |
| WR      | 42.4%   | 36.8%   |
| PF      | 0.78    | 0.73    |
| MaxDD   | 27.09%  | 11.14%  |
| PnL     | −21.46% | −6.69%  |
| Trades  | 172     | 57      |

R1+R2 successfully limited MaxDD (notably low in OOS at 11.14%), but the underlying model produces negative expected value on ATOM. Not a merge candidate.

## Decision: NO-MERGE for ATOM. Baseline unchanged.

The code fix itself is a silent improvement — it doesn't change any currently-merged iteration's outcome because v0.176's baseline runner uses `yearly_pnl_check=False`. Fail-fast only runs during candidate screens, and none of those were previously unfairly aborted (AVAX failed year-1 legitimately; AAVE failed year-1 legitimately; ATOM's rejection is re-confirmed here).

## Test status

366 tests pass after the fix.

## Next Iteration Ideas

- **Iter 180**: R5 concentration soft-cap. LINK at 78% is the structural issue. R5 would scale down LINK's weight when its running share exceeds a threshold (e.g. 50%).
- **Iter 181**: screen SUI/APT/TIA/INJ — different sector than alt-L1s, may carry different signal.
- **Iter 182**: R3 OOD detector (Mahalanobis z-score on feature vectors vs. IS distribution).

## Exploration/Exploitation Tracker

Window (169-179): [E, E, E, X, E, E, X, E, E, E, X] → 7E/4X. Balanced.
