# Team 06 research brief: per-coin time-series momentum with volatility management

## Mandate

Build the tournament's pure directional trend system. Each coin's forecast must come from its
own past return signs, while inverse-volatility sizing and portfolio-level downward scaling
manage exposure when risk rises. Do not turn this into a cross-sectional winner-minus-loser
factor.

Primary evidence: [Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877)
documents strong crypto time-series momentum. [Volatility Managed Portfolios](https://www.nber.org/papers/w22208)
provides the general lagged-variance scaling rationale. As a related crypto comparator,
[Cryptocurrency market risk-managed momentum strategies](https://www.sciencedirect.com/science/article/abs/pii/S1544612325011377)
studies risk-managed cross-sectional crypto momentum; it does not directly establish this
team's time-series or downside-scaling specification.

## Causal feature

For every eligible coin at a fixed decision boundary:

1. Compute own-coin cumulative log returns over fixed fast, medium, and slow windows.
2. Convert each to a bounded sign or volatility-standardized trend; combine them by a
   preregistered equal or consensus rule.
3. Size active coin directions inversely to their trailing realized volatility, subject to a
   floor and coin cap.
4. Scale total requested gross downward when lagged strategy or forecast-portfolio variance
   exceeds target. Maximum volatility scale is one: low estimated volatility never creates
   leverage.
5. Enforce the tournament's directional-net cap by proportional sleeve scaling, not by
   cross-sectional return ranks.

All volatility and trend estimates end before the decision. Targets execute next open.

## Required research

- Baselines: single-horizon sign trend with equal weights; buy-and-hold equal weight; inverse
  volatility with no direction; and the same trend without portfolio volatility management.
- Formation horizons: 21, 42, and 84 bars, plus a fixed consensus. Rebalance horizons: 1, 3, and
  7 days.
- Sign tests: trend and exact contrarian inversion for every horizon.
- Scaling tests: equal weight, inverse own volatility, portfolio downward-only scale, and both
  together. Report whether the benefit comes from alpha or exposure timing.
- Direction tests: long-only signals, short-only signals, and both; market net and beta must be
  reported explicitly.
- Report whipsaw turnover, trend-crash days, funding PnL, fold/quarter breadth, and bull, bear,
  chop, long, and short attribution.

## Risk controls

The full system should examine downward-only volatility targeting, a portfolio drawdown brake,
close-confirmed symbol stops, time stops for stale trends, cooldown after whipsaw exits, and a
turnover cap. Gross and symbol weights must be conservative enough for short-side gaps. Controls
must be evaluated separately and together; they cannot make a negative unscaled trend thesis
look positive by simply remaining flat.

## Falsifiers

Pivot if no trend horizon is positive before risk overlays, the exact inversion wins, volatility
management merely removes almost all exposure, or aggregate after-cost train, stitched
validation, or doubled-cost performance is nonpositive. BTC or episode concentration, nearby
horizon fragility, and persistent short-bear or chop weakness demand repair and reduce
robustness, but none is an independent veto.

## Opening-probe coaching record

Trial 1 (`t06-own-coin-momentum-consensus-v1`) is GREEN with no open core gap: train Sharpe
1.671, annualized return 35.50%, doubled-cost Sharpe 1.448, max drawdown 10.64%, and 90%
positive quarters. All four frozen regimes were positive: bear 1.566, bull 2.250, chop 0.479,
and stress 1.894. Its 95% train-Sharpe interval was `[0.555, 2.726]`, and even the doubled-cost
interval had a positive lower endpoint of 0.311.

The candidate passes every public-core IS target with robustness score 98.62. No IS revision is
authorized: changing a strong, broad result after inspection would add selection risk without a
diagnosed failure. This exact source, risk policy, and parameter set is the Team 06 leader for
subsequent sealed validation.

## Collision guard

Use own-coin history only for direction. Do not rank residual winners and losers as Team 08 does,
flip between momentum and reversal by liquidity as Team 07 does, condition on UTC cells as Team
10 does, or add funding carry. Cross-sectional operations are allowed only for risk caps and
book-level exposure normalization.
