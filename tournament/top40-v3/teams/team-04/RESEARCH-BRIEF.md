# Team 04 research brief: downside-risk premium net of lottery risk

## Mandate

Test a deliberately decomposed idiosyncratic-risk hypothesis: persistent residual downside risk
may earn compensation, while positive-jump lottery variance may be overpriced. The model must
show that both signs contribute; a generic low-volatility anomaly is not acceptable.

Primary evidence: [Is idiosyncratic volatility priced in cryptocurrency markets?](https://www.sciencedirect.com/science/article/pii/S0275531920301926)
reports positive cross-sectional pricing of idiosyncratic volatility, while
[Downside risk and the cross-section of cryptocurrency returns](https://www.sciencedirect.com/science/article/pii/S0378426621002053)
finds higher idiosyncratic downside risk predicts higher subsequent returns. Team 03's
[variance-decomposition source](https://www.scheller.gatech.edu/directory/research/finance/lee/pdf/crypto_variance_leewang_5feb2024.pdf)
motivates separating positive-jump lottery risk.

## Causal feature

Estimate each coin's residual return from a past-only rolling beta to the eligible-crypto median
return; compare with simple median subtraction as a required robustness case. Over 63, 126, or
252 completed 8-hour bars calculate:

- downside residual semivariance or lower partial moment;
- positive residual semivariance and positive-tail share;
- total residual variance as a control.

The reference composite is rank(downside risk) minus a fixed-weight rank(positive-tail risk).
Long coins with compensated downside exposure but limited lottery tails; short coins with weak
downside compensation and excessive positive-tail risk. Use one cross-sectional rank only after
the components are computed.

## Required research

- Baselines: total idiosyncratic variance, downside risk alone, positive-tail risk alone, and a
  conventional low-volatility portfolio.
- Formation horizons: 63, 126, and 252 bars. Rebalance horizons: 7, 14, and 28 days.
- Sign tests: invert each component separately and invert the whole composite.
- Neutralization: median residual and rolling-beta residual, with beta fitted strictly before
  the scoring boundary.
- Composite weights: a small preregistered set including equal weight and component-only
  endpoints; no continuous optimizer.
- Report component IC, component sleeve PnL, liquidity/listing-age controls, fold stability, and
  bull/bear/chop plus long/short roles.

## Risk controls

Compensated downside exposure can become realized crash loss. Require broad sleeves, low gross,
small coin caps, minimum quote-volume/history, downward-only volatility scaling, a portfolio
drawdown brake, and close-confirmed symbol stops with cooldown. Evaluate a recent-gap quarantine
as an explicit risk ablation, not as a hidden alpha rewrite.

## Falsifiers

Pivot if either component has the wrong preregistered sign, the composite does not improve on
both component baselines, or aggregate train, stitched validation, or doubled-cost performance
is nonpositive. Liquid-cohort weakness, delisting or crash concentration, unstable beta
residualization, and regime or sleeve weakness lower robustness and demand repair but are not
standalone vetoes. A successful low-positive-jump factor with no compensated downside
contribution belongs to Team 03, not this mandate.

## Collision guard

Team 04 uniquely owns the two-sided risk decomposition and must demonstrate a positive downside
risk premium net of a negative lottery premium. Do not use single-event MAX, clock conditioning,
funding, generic multi-horizon momentum, or price-spread convergence.
