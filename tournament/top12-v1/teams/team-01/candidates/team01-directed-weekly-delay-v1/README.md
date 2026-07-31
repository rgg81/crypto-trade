# Team 01 directed weekly response-delay baseline

## Thesis

A large completed weekly information shock in one eligible coin can be incorporated into another
eligible coin with a delay. The candidate estimates every ordered leader-to-follower relationship
using only earlier completed weekly returns. It favors edges whose forward lag correlation is
positive and stronger than the reverse direction, then resolves equal scores by lexicographic
leader and follower symbols.

At a weekly decision:

- **continue:** follow the leader's sign when the follower has incorporated less than half of the
  standardized leader shock;
- **reverse:** take a half-strength counter-position when the follower has moved in the same
  direction by more than 1.25 times the leader's standardized shock, treating that as overshoot;
- **absent:** request no alpha exposure for a pair when the leader shock is smaller than 0.75
  standard deviations, the lag correlation is below 0.15, the lead-over-reverse advantage is
  below 0.05, or the response lies between under-response and overshoot.

The raw follower signals are cross-sectionally centered across the current eligible universe.
This is an exposure constraint, not the selection signal: pair discovery is directed and based on
lagged cross-coin returns rather than same-coin momentum or contemporaneous beta ranks. The final
book has gross exposure no greater than 0.48, zero target net exposure up to floating-point
roundoff, and no symbol above 0.08 absolute weight.

## Causality and trading cadence

For every row, the usable timestamp is `open_time + 8 hours`; rows with a later completion time
than `context.decision_time` are discarded explicitly. Weekly close snapshots are taken as of the
decision and its preceding seven-day cutoffs. The relationship fit excludes the most recent
weekly return, which is reserved as the new shock. Pair scoring, tie-breaking, and allocation are
deterministic. The strategy requests a new target no more often than once every seven days and
otherwise returns `None`.

## Falsifier

Reject the mechanism if its directed leader-to-follower advantage is unstable across chronological
eras, if sign inversion is not materially worse, if long and short shock roles do not both
contribute, if chop filtering does not reduce unproductive turnover, or if the edge fails at the
mandatory 2x and 3x trading costs. A result driven by contemporaneous common beta, one isolated
coin, or one era also falsifies the causal response-delay interpretation.
