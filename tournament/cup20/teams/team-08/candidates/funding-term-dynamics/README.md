# funding-term-dynamics

Team 08's nominee. Reversion in the *dynamics* of funding, gated on the cross-sectional
dispersion of those dynamics.

## Signal

For every eligible coin, from funding settlements strictly before the decision:

    spread = ( mean(last SHORT_WINDOW rates) - mean(last LONG_WINDOW rates) )
             / max( stdev(last LONG_WINDOW rates), 0.00002 )

The numerator is the coin's current funding leg against its own recent regime; the
denominator puts it in that coin's own funding units. A coin whose funding is chronically
high scores near zero — its current leg *is* its regime — which is why this is not a level
book by construction rather than by assertion.

`dispersion` is the cross-sectional standard deviation of that spread over the eligible
names, and the gate is its percentile within its own trailing `DISPERSION_WINDOW = 270`
boundaries. Below `DISPERSION_GATE` the funding move is market-wide rather than
positioning-specific, and the book stands aside.

## Book

Short the highest spread, buy the lowest, `NAMES_PER_SIDE = 1` a side, equal weight, dollar
neutral. Held until the two legs' spread gap closes to zero — the imbalance has cleared — or
`MAX_HOLD_BARS` boundaries, whichever is first; then rolled if the gate is open, closed if
not. `None` is returned in between, so quantities are held and no turnover is paid.

There is no rebalance phase parameter: entries are set by expiries and gate openings, not by
an offset on a clock.

## Parameters

| name | value | role |
|---|---:|---|
| `SHORT_WINDOW` | 3 | current leg of the term structure, in settlements |
| `LONG_WINDOW` | 30 | the coin's own regime window, in settlements |
| `DISPERSION_GATE` | 0.40 | trailing percentile of cross-sectional dispersion to open |
| `MAX_HOLD_BARS` | 18 | hard cap on the holding period, in 8h boundaries |

All four are declared neighbourhood coordinates.

## Risk policy

Nothing declared. `volatility_target.enabled` is `false` (charter §6, amendment A3); the
lower-target turnover exploit was identified and not used.

## Causality

The strategy applies its own `funding_time < decision_time` cut and reads no bar. Verified by
corruption in `research/causality.py`, not asserted.
