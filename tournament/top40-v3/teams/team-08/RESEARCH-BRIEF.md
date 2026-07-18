# Team 08 research brief: market-neutral multi-horizon residual momentum

## Mandate

Build the canonical cross-sectional crypto momentum factor: own persistent relative leaders and
short persistent relative laggards across several economically distinct horizons, while removing
the common crypto market direction.

Primary evidence: [Common Risk Factors in Cryptocurrency](https://www.nber.org/papers/w25882)
finds market, size, and momentum factors capture much of the cryptocurrency cross-section, while
[Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877) provides broader
crypto-momentum evidence. Treat survivorship seriously:
[On survivor cryptocurrency momentum](https://www.sciencedirect.com/science/article/pii/S1544612326001339)
shows that results can change in fixed survivor cohorts.

## Causal feature

For each completed 8-hour bar, remove either the eligible-crypto median return or a causal rolling
beta times that median. For each eligible coin:

- sum residual returns over fast, medium, and slow formation windows;
- scale each horizon by past residual volatility;
- combine horizon ranks only when a preregistered consensus or weighted-average rule is met;
- rank the final score once into broad, equal-gross long and short sleeves.

The reference book is exactly dollar neutral and tightly beta controlled. It rebalances at a
fixed schedule and never uses current membership to rewrite pre-admission histories.

## Required research

- Baselines: raw cross-sectional momentum; median-residual momentum; beta-residual momentum;
  single-horizon momentum; and equal-turnover residual reversal.
- Formation horizons: 21, 63, and 126 bars, with a 252-bar slow robustness case. Holding periods:
  3, 9, and 21 bars.
- Sign tests: continuation and exact inversion at every horizon and for the combination.
- Combination tests: equal average, sign consensus, fast/slow agreement, and each component
  alone. Keep the grid small and preregistered.
- Neutralization tests: dollar neutral only, median residual, rolling-beta residual, and a
  post-score beta cap. Report residual beta rather than assuming neutrality worked.
- Cohort tests: contemporaneous membership, minimum-history cohorts, a cohort frozen using only
  information available at its predeclared formation date and held for a fixed diagnostic
  horizon, and point-in-time listing-age buckets. Eventual survival is never a cohort criterion.

## Risk controls

Use broad sleeves, low symbol caps, deterministic ties, minimum history/liquidity, rebalance
hysteresis, downward-only volatility scaling, a turnover limit, a portfolio drawdown brake, and
close-confirmed stops with cooldown. Risk controls must preserve both sleeves; going flat during
every adverse period is not an all-regime model.

## Falsifiers

Pivot if residual momentum is nonpositive after base and doubled costs, raw common-market
exposure explains the return, or the inversion wins. Horizon, coin, or point-in-time-cohort
concentration, weak fast/slow consensus, imperfect beta neutrality, and fold, quarter, regime, or
role weakness reduce robustness and trigger repair but are not individual vetoes.

## Collision guard

This team owns cross-sectional residual continuation across multi-week horizons. Do not use
per-coin directional signs and portfolio trend timing from Team 06, liquidity-state reversal from
Team 07, stationary pair spreads from Team 05, funding, calendar cells, or jump-risk features.
