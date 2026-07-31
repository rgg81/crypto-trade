# Team 05 dispersion-breadth-recoupling baseline

This candidate tests whether a cross-section whose return dispersion becomes unusually large
without matching directional breadth subsequently recouples. It waits for the standardized
dispersion-minus-absolute-breadth gap to be elevated and then contract. At that point it takes the
opposite side of each coin's cross-sectional deviation: below-center contributors are long and
above-center contributors are short. Allocation is proportional to squared relative deviation,
so the portfolio expresses coins' contributions to the dislocation rather than a generic
winner-minus-loser rank.

All inputs are completed 8-hour bars. The formation return is 21 days, the market-state reference
window is 42 days, and decisions are permitted only on a fixed 48-hour UTC grid. The alpha target
is balanced between long and short sides, with 0.32 maximum gross per side and 0.08 maximum
absolute symbol weight.

The hypothesis is falsified if performance is explained by common-beta exposure, lacks positive
gross contribution from either side, fails across directional regimes, or disappears under the
preregistered formation and rebalance grids.
