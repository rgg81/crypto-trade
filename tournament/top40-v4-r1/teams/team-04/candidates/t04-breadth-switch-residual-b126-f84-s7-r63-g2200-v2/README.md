# Team 04 breadth-switched residual momentum: neighborhood center

This candidate preserves the baseline's causal market-residual ranking. It estimates each coin's
beta to the median native-crypto return over 126 days and scores 84 days of residual momentum after
a seven-day skip. A separate completed 63-day native-crypto breadth reading selects one side: at
50% or greater positive breadth, only the highest residual-momentum cohort is held long; below 50%,
only the lowest cohort is held short.

The active side targets 0.22 gross and refreshes weekly on Monday. The original full organizer
controls remain enabled because the controls-off ablation worsened drawdown, edge, folds, and bull
performance. The breadth state uses only eligible pure-crypto bars, with no stablecoin, TradFi,
metal, index, calendar hindsight, or OOS observation.

This is the preregistered center of `t04-breadth-switch-formation-neighborhood`, whose only declared
coordinate is residual `formation_days`. It is falsified if both sleeves and at least four folds do
not become positive, or if Sharpe, drawdown, turnover, costs, or regime breadth remain ineligible.
It makes no performance claim.
