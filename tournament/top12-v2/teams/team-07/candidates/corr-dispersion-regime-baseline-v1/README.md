# Correlation-dispersion regime baseline v1

This baseline implements Team 07's assigned `correlation-dispersion-regime-allocation`
mechanism. It asks whether a common crypto market mode changes how cross-sectional dislocations
should be traded.

At each Monday 00:00 UTC decision, the strategy retains only bars that completed before the
boundary and forms a common-time return panel. Median pairwise correlation over 42 days measures
the strength of the market mode. Cross-sectional median absolute return dispersion over the last
7 days is compared with the preceding 42-day baseline. Both regime inputs exclude the newest
completed return.

High correlation and elevated dispersion smoothly activate a dollar-neutral reversal of 14-day
beta-residual moves, skipping the newest two bars. High correlation with compressed dispersion
turns off that relative-value budget and permits a smaller equal-weight directional tilt from the
lagged 21-day median-market trend. Weak-correlation regimes naturally hold mostly or entirely
cash. Cross-sectional percentile scores, a 0.16 symbol cap, weekly decisions, and the organizer's
0.20 one-way turnover limit are intended to resist concentration and trading costs.

The implementation is deterministic and state-free. It does not use funding, future opens,
calendar anchors, files, network access, or generated fills. Outside the weekly boundary it
returns `None`; insufficient data at a rebalance requests a flat book.

## Falsifier

Reject the thesis if the residual-reversal sleeve fails specifically when both lagged correlation
and relative dispersion are high, if the regime gates add no stability over an ungated control,
or if apparent edge disappears at doubled costs or is confined to a minority of development
folds. The directional tilt is secondary and should also be removed if its compressed-dispersion
conditional contribution is not independently positive.
