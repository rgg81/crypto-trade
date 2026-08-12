# carry-crowd-guard — team-07 nominee

A dollar-neutral cross-sectional funding-carry book on the point-in-time top-20 perpetual
universe, sized by carry-to-risk, with a crowding guard that sizes down — but never removes —
the shorts the crowd has occupied longest.

## What it trades

At every second 8h boundary (`REBALANCE_CADENCE = 2`, `REBALANCE_PHASE = 0`; `None` is returned
in between, so positions are held rather than re-targeted):

1. For every eligible symbol, `carry_i` is the mean funding rate over the last
   `CARRY_LOOKBACK = 63` settlements (≈ 21 days) and `sigma_i` is the standard deviation of the
   last `RISK_LOOKBACK = 63` bar close-to-close returns.
2. Names are ranked by carry-to-risk, `(carry_i − median carry) / sigma_i`. The
   `SLEEVE_NAMES = 7` richest are shorted, the 7 cheapest are bought.
3. Every position is sized `1/sigma_i`, so each name contributes comparable risk rather than
   comparable dollars.
4. **The crowding guard.** Each *short* weight is multiplied by
   `1 − CROWDING_PENALTY × premium_duration_i`, where `premium_duration_i` is the fraction of the
   last `CROWDING_LOOKBACK = 63` settlements whose funding rate exceeded
   `PREMIUM_BASELINE = 0.0001`. That baseline is Binance's interest component, so exceeding it
   means the perpetual genuinely traded at a premium to its index rather than merely paying the
   resting rate. `CROWDING_PENALTY = 0.60`.
5. Each sleeve is normalised to equal gross, so the book is dollar-neutral by construction. The
   evaluator then normalises to unit gross, applies its caps and its common risk unit.

## Why the guard is a multiplier and not a filter

The single most crowded names are also the largest carry in the book, and their funding leg is the
part of the return that does not vary across folds. Removing them — the obvious reading of "stand
aside" — throws that cashflow away and made the book strictly worse at every strength tested.
Sizing them down keeps the cashflow while moving risk toward the less entrenched shorts beside
them. `CROWDING_PENALTY = 1.00`, at which a permanently-premium name reaches exactly zero weight,
is the filter version, and it is the point at which the guard stops helping. See
`RESEARCH-CERTIFICATE.md`.

## The ablation

`CROWDING_PENALTY = 0.00` disables the guard exactly and changes nothing else. That candidate is
frozen alongside this one as `carry-guard-off`; `RISK_SIZING = 0` turns off the other control
(carry-to-risk ranking and inverse-volatility sizing) in the same way.

## Declared roles

`long,short`. Both sleeves are traded at every rebalance and carry equal gross.

## Causality

`DecisionContext` supplies funding strictly before the decision instant and bars closing at or
before it. The strategy reads nothing else — no execution price, no fill, no cost, no equity. The
funding event that settles *at* the decision boundary is never visible: in this snapshot every
`funding_time` lands in `[boundary, boundary + 1s)`, so the harness's strictly-before filter
excludes it, and the freshest rate the book can see is one full 8h interval old — two boundaries
before the one whose funding its new position will actually pay.
