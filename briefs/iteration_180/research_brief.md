# Iteration 180 — APT screen with R1+R2

**Date**: 2026-04-22
**Type**: EXPLORATION (different-sector candidate)
**Baseline**: v0.176 — unchanged
**Decision**: NO-MERGE

## Candidate

APT (Aptos Labs) — Oct 2022 launch. Newer L1 outside the AVAX/ATOM/DOT cluster that consistently failed. R1+R2 active from the start.

## Result

| Metric       | IS      | OOS     |
|--------------|--------:|--------:|
| Trades       | 12      | 41      |
| Sharpe       | −1.29   | −0.07   |
| WR           | 41.7%   | 46.3%   |
| PF           | 0.54    | 0.97    |
| MaxDD        | 25.93%  | 8.86%   |
| PnL          | −13.7%  | −1.15%  |

## Reason APT is not viable

**Insufficient IS history.** APT data starts 2022-10. With a 24-month training window, the first valid training-month is Jan 2025 (training data 2023-01 to 2024-12). IS predictions therefore only exist for Jan-Mar 2025 (12 trades) before the OOS cutoff. That's far below the Gate 3 threshold of 100 IS trades.

OOS PnL is nearly break-even (−1.15% over 41 trades, Sharpe −0.07). R1+R2 effectively bound MaxDD at 8.86% OOS, but the signal isn't there.

## Lesson

New candidates from the 2022-2023 launch window don't have enough IS data for our standard Gate 3. Either:

- Reduce `training_months` (not allowed per skill — 24 is fixed)
- Lower Gate 3's IS trade threshold for recently-launched symbols
- Skip these candidates until they accumulate more history

The 100-IS-trade threshold exists to prevent statistical fluke merges. For post-2022 symbols, this probably means waiting until 2026 for enough IS data. Not actionable in 2026-Q2.

## Next Iteration Ideas

- **Iter 181**: R5 concentration soft-cap. Structural intervention on LINK's 78% share. Expected tradeoff: lower PnL, better diversification.
- **Iter 182**: R3 OOD feature detector (Mahalanobis z-score) — harder to implement but addresses the root cause of ATOM-style 2022 failures.
- **Iter 183+**: Wait for APT/SUI/TIA to accumulate more IS data; revisit in future sessions.

## Exploration/Exploitation Tracker

Window (170-180): [E, E, X, E, E, X, E, E, E, X, E] → 7E/4X.
