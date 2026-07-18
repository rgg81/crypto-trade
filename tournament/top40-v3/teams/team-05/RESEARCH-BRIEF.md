# Team 05 research brief: dynamic cointegration spread convergence

## Mandate

Construct causal relative-value trades from stable pairwise log-price relationships. This is a
spread-stationarity hypothesis, not own-price mean reversion and not a loose correlation trade.

Primary evidence: [Evaluation of dynamic cointegration-based pairs trading strategy in cryptocurrency market](https://arxiv.org/abs/2109.10662)
tests Engle-Granger, Johansen, and nonlinear specifications with rolling half-life and realistic
market implementation.

## Causal feature

At a fixed weekly formation boundary:

1. Use only completed closes for currently eligible pure-crypto coins with adequate exact-grid
   common history; request no additional bar fields or external classifications.
2. Reduce multiplicity with a predeclared causal candidate graph, such as each coin's few
   highest past correlations; do not use external sector labels.
3. On the trailing formation window, fit log price A minus intercept minus hedge-ratio times log
   price B. Retain only pairs passing a preregistered residual-stationarity and half-life rule.
4. Standardize the current spread with a trailing, past-only mean and scale. Enter convergence
   at the next open: a rich A spread is short A and long beta-weighted B, while a cheap A spread
   is long A and short beta-weighted B. Normalize each pair to unit gross before aggregation so
   beta controls the hedge rather than manufacturing exposure. Close at convergence, timeout,
   or a causal break.

Aggregate the clipped dislocation conviction of overlapping pairs into symbol targets. The
predeclared maximum absolute z-score is a winsorization cap for sizing, not a rule that rejects a
stronger dislocation after the spread has passed the causal stability gates. Apply
only a common portfolio downscale for symbol, gross, and net limits; do not flatten the resulting
scores into equal-weight sides or erase their relative conviction. Both legs must be eligible and
executable.

## Required research

- Baselines: normalized-price distance pairs, correlation-only pairs, fixed unit hedge ratio,
  and an equal-turnover random pair graph.
- Formation horizons: 126, 252, and 378 bars. Spread-scale horizons: 42, 63, and 126 bars.
  Holding timeouts: 7, 14, and 28 days.
- Sign tests: convergence and exact divergence.
- Model tests: frozen versus rolling hedge ratio; strict versus relaxed stationarity; half-life
  gate ablation; pair graph ablation.
- Report pair-level PnL, funding on each leg, turnover, rejected-pair counts, break losses,
  symbol/pair concentration, membership exits, folds, and regimes.

## Risk controls

Use conservative gross, pair and symbol caps, the frozen common-history gate, spread entry and
exit hysteresis, a close-confirmed spread-loss stop, a half-life-based time stop,
cooldown after structural breaks, and a portfolio drawdown brake. Do not average down without a
predeclared maximum. A pair disappears immediately from new-entry consideration when either leg
leaves eligibility.

## Falsifiers

Pivot if convergence is nonpositive after base and doubled costs, divergence performs as well,
stationarity and half-life gates add no value, or funding makes the expected trade uneconomic.
Pair or episode concentration, break losses, hedge-ratio instability, and regime weakness trigger
targeted repair and lower robustness rather than automatically rejecting a strong system.
Extensive pair search with no multiplicity discipline is itself a falsifier.

## Collision guard

The alpha must be a fitted two-coin stationary spread. Do not replace it with a coin's distance
from its own VWAP, cross-sectional residual momentum, leader/follower diffusion, funding spread,
or generic short-horizon reversal. The submitted implementation must retain the fitted causal
beta in executable leg dollars and the pair-level convergence magnitude through overlap
aggregation; a correlation graph feeding equal-dollar or equal-score baskets is not this mandate.
