# Team 03 auction-shape baseline v1

## Thesis

A completed 8h bar records an auction path, not merely a return. Directional body displacement
that finishes near the same-side extreme is treated as **acceptance** of the new price area. A
dominant lower (upper) wick followed by a close above (below) the midpoint is treated as bullish
(bearish) **rejection** of the excursion. Repeated states in the same direction over twelve
completed bars should persist into the next daily holding interval.

The two states are measured separately. Acceptance receives 60% of the composite and rejection
40%. Each component is its signed mean active-state strength multiplied by its directional
consistency. Thus alternating auction shapes cancel even when their individual bars are large.
The signal does not use a previous close or any close-to-close return.

Before ranking, the cross-sectional linear exposure of the composite signal to mean absolute
open-to-close return is removed. This leaves the shape hypothesis to stand on normalized
wick/body/close-location geometry rather than raw move magnitude.

## Causality and portfolio construction

- Every row must satisfy `open_time + 8h <= decision_time`.
- Only the most recent twelve valid completed 8h bars are used.
- The strategy requests targets only at 00:00 UTC, so it rebalances no more than once per day.
- Up to three highest residual scores receive `+0.08` each and the same number of lowest scores
  receive `-0.08` each.
- The requested book is exactly dollar neutral, has gross exposure at most `0.48`, and has
  individual absolute exposure at most `0.08`.
- With fewer than four valid symbols or no cross-sectional dispersion, the request is flat.

## Baseline state definitions

All geometry is divided by the same bar's high-low range.

- Acceptance: body and close location have the same sign, absolute body is at least `0.18`, and
  absolute close location is at least `0.30`.
- Rejection: absolute lower-minus-upper wick asymmetry is at least `0.18`, the close location
  confirms the direction away from the rejected wick, and absolute body is at most `0.45`.
- A state family contributes only after at least three active observations in the twelve-bar
  formation window.

Adjacent formation states for later preregistered trials are body thresholds `0.12` and `0.24`
for acceptance, and wick-asymmetry thresholds `0.12` and `0.24` for rejection. Formation-grid
neighbors are 6 and 24 completed bars around the 12-bar baseline. The rebalance-grid neighbor is
six 8h bars (48h) around the three-bar (24h) baseline.

## Falsifier

Falsify the mechanism if signed performance is not present on both long and short roles across
the mandatory chronological and regime checks, if sign inversion is not directionally worse, or
if the effect disappears after neutralizing raw open-to-close return magnitude. Also reject it if
the adjacent formation/rebalance coordinates or adjacent auction-state thresholds show an
isolated optimum rather than a stable neighborhood.
