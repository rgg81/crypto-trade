# Team 09 VCIT baseline v1

## Thesis

Trading activity defines a causal business-time clock. When that clock accelerates relative to
wall-clock time, recent directional returns should be followed; when it decelerates, the same
returns should be faded. The effect should survive after every activity input is normalized
against that coin's own history.

For each symbol, the strategy:

1. keeps only 8-hour rows completed by the UTC decision boundary;
2. log-transforms quote volume and trade count, then subtracts their own lagged rolling medians;
3. averages those two relative-activity series and scales the result by its own lagged rolling
   dispersion;
4. measures the transition in the fast-minus-slow intensity state;
5. multiplies that per-coin transition score by a per-coin volatility-normalized recent return;
   and
6. ranks the composite score across the currently eligible symbols.

The lower half is short and the upper half is long with equal long and short gross exposure.
Rebalancing is attempted only at 00:00 UTC, so it occurs at most once per day. The strategy caps
gross exposure at 0.80, absolute net exposure at 0.20, and each symbol at 0.08.

This is not a raw volume or liquidity-size rank. Absolute quote volume and trade count enter only
after lagged, within-symbol normalization.

## Falsifier

Reject the thesis if the mandatory research matrix shows that the signal is materially explained
by static raw-volume rank, disappears after within-coin activity normalization, lacks positive
long and short gross contribution, or is not stable across the preregistered formation and
rebalance grids.

## Baseline controls

Volatility targeting, drawdown brakes, position stops, time stops, and turnover limiting are
disabled in this transparent baseline. Organizer-owned execution and exposure controls still
apply.
