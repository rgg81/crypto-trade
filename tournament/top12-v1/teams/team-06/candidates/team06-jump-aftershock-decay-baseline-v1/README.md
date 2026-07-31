# Team 06 jump-aftershock decay baseline

## Thesis

A discontinuous repricing can leave a short-lived sequence of smaller, same-direction
aftershocks as slower participants and forced flows finish adjusting. The baseline treats an
outsized completed 8-hour close-to-close return as a jump proxy, but does not trade the jump or a
one-bar reversal. It waits for the first completed post-event bar to confirm a smaller
same-direction move, then holds a directionally aligned signal whose strength decays with explicit
event age.

Each symbol is processed by a deterministic event-time state machine:

1. A jump starts or replaces the state when its absolute log return exceeds both 3% and five
   robust trailing-volatility units, using up to 90 earlier completed bars.
2. The next completed bar must continue in the jump direction, while measuring between 3% and 65%
   of the jump magnitude. Otherwise the event is invalidated without a position.
3. A confirmed event ages once per completed 8-hour bar. It is invalidated by a large opposing
   aftershock, loss of cumulative directional follow-through, a renewed impulse, or post-event
   growth inconsistent with decay.
4. A surviving signal decays with a two-bar half-life and expires after six post-event bars.

Positive and negative events produce long and short signals respectively. When both sides are
present they receive equal side budgets; a one-sided book is limited to 20% gross. Targets are
finite, capped at 8% per symbol, 80% gross, and 20% absolute net. Rebalancing is no more frequent
than once per 24 hours.

## Falsifier

The hypothesis is falsified if the conditional post-jump hazard profile is not directionally
consistent and economically positive across jump-size buckets, positive and negative jump signs,
and chronological eras after costs. It is also falsified if apparent edge is concentrated in the
jump bar itself, disappears when the first post-event decay confirmation is required, or depends
on events that violate the declared age and invalidation rules.

## Causality

Only rows whose `open_time + 8h` is at or before the UTC decision boundary are used. Rolling jump
thresholds exclude the candidate event return. Orders are expressed only as target weights for
execution by the organizer at the next executable open.
