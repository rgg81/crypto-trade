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

## Opening-probe coaching record

Trial 1 (`t08-residual-momentum-21-63-126-v1`) is a broad AMBER: train Sharpe 0.674,
annualized return 7.37%, doubled-cost Sharpe 0.387, max drawdown 14.42%, and 60% positive
quarters. All four regimes were positive (bear 0.321, bull 1.261, chop 0.107, stress 0.352).
It missed only the 0.75 train-Sharpe target, by 0.076.

Artifact attribution shows a credible alpha with an execution defect: pre-cost Sharpe was
1.058, while 21,542 trades accumulated 10.67% arithmetic realized costs. Trial 2 is therefore
fixed as a holding-structure revision, not an alpha search. It will retain the exact score,
horizons, ranks, sign, gross, and daily decision schedule, but average three independently dated
daily cohorts using a constant divisor of three. A cohort expires after three calendar days; an
invalid current signal clears every vintage and returns flat, preserving the original fail-flat
data contract. In a stable universe, replacing one cohort bounds one-way signal turnover at
`0.44 / 3 = 0.1467`.

The candidate's redundant 21-bar organizer time stop is disabled because dated cohorts now own
signal expiry; repeated valid forecasts may still maintain a position. The close-confirmed 9%
position stop and its six-bar cooldown remain unchanged; a reopened target must still be backed
by freshly computed daily forecasts. Membership exits are permanently removed from stored
vintages so a re-entry cannot resurrect stale exposure. Survivors are never renormalized; the
candidate returns flat if an exit would breach its net cap.

Trial 2 (`t08-residual-momentum-21-63-126-3d-v2`) improved the intended cost metrics but
remained AMBER. Train Sharpe rose from 0.674 to 0.706, annualized return from 7.37% to 8.26%,
and doubled-cost Sharpe from 0.387 to 0.465. Max drawdown increased from 14.42% to 18.11%,
trade count rose to 31,908 as small cohort changes were executed, and stress Sharpe declined
from +0.352 to -0.243; bear, bull, and chop remained positive. The only public-core miss is
still train Sharpe, now short by 0.044.

Team 08 is stopped after this diagnosis-driven revision. Trying two-day, four-day, or another
nearby vintage solely to cross 0.75 would be IS parameter mining. V1 remains the lower-drawdown,
all-regime-positive reference; V2 is the stronger aggregate and doubled-cost reference. Both are
honest strong-AMBER evidence, but neither is promoted as GREEN or allowed to inherit Team 06's
qualification.

## Collision guard

This team owns cross-sectional residual continuation across multi-week horizons. Do not use
per-coin directional signs and portfolio trend timing from Team 06, liquidity-state reversal from
Team 07, stationary pair spreads from Team 05, funding, calendar cells, or jump-risk features.
