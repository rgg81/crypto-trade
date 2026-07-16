# Team07 research brief: liquid-leader shock diffusion

Status: prospective clean-room family; no trial registered and no performance measured.

## Mechanism and thesis

Information reaches the most liquid crypto perpetuals first, then diffuses unevenly through the
rest of the point-in-time Top-40. At each daily rebalance, the strategy forms a trailing-liquidity
leader basket, estimates each coin's delayed response after removing its contemporaneous market
beta, and forecasts the next interval from the last closed leader shock. A small idiosyncratic
reversal term handles overshoot, and past funding is a secondary crowding/carry conditioner.

The portfolio is cross-sectional and two-sided. It buys the strongest under-reactions and sells
the weakest or over-reacting names. A slow leader-basket trend changes long versus short gross
within a 16% net cap; it never disables either sleeve.

## Expected regime roles

- Bull: positive slow trend gives the long sleeve more gross; positive leader shocks favor
  under-reacting followers. Long-bull attribution should be positive.
- Bear: negative trend gives the short sleeve more gross; negative shocks favor shorting delayed
  followers. Short-bear attribution should be positive.
- Chop: side gross is nearly balanced; residual reversal and funding crowding are expected to
  monetize dispersion after two-way shocks.
- Stress: shocks are winsorized, the organizer volatility target scales gross down, drawdown
  brakes de-risk, and per-position stops impose cooldowns. Flat or modest stress return is
  acceptable only if drawdown and tail gates pass.

## Causal construction

Only candles with open_time plus eight hours no later than the decision boundary are accepted.
Funding timestamps must be strictly before the boundary. The liquid-leader set, regression
moments, scaling, ranks, and trend are recomputed from that past-only view. No future row,
evaluator state, fill, PnL, private window, or external file is consumed.

Amendment 0006 is the sole universe authority. Team code trusts `eligible_symbols` and does not
create a competing symbol classifier. Every result-bearing command must use the active Amendment
0005 superset entrypoint, which preserves the exact frozen A6 pure-crypto preflight.

## Center candidate

The declared center uses 189 bars of history, 126 minimum observations, a 20% liquid leader set
with at least four leaders, one daily rebalance, 80% target gross, 16% maximum directional net,
9% per-name cap, 12% idiosyncratic reversal, 6x funding carry, and six or more names per sleeve.
The exact declaration is in frozen_config.json.

## Falsifiers and decision rule

Reject or pivot before private qualification if any of these holds on stitched six-fold OOF
development evidence:

1. net Sharpe is below 0.75, annualized return is nonpositive, or doubled-cost Sharpe is below
   0.35;
2. fewer than four folds or 55% of quarters are positive;
3. bull, bear, or chop net return is nonpositive, fewer than three regime Sharpes are positive,
   or worst-regime Sharpe is below -0.25;
4. long-bull, short-bear, or combined-chop attribution is nonpositive;
5. propagation ablation is no worse than the complete signal, meaning the lead-lag thesis is not
   doing useful work;
6. fewer than 70% of declared neighbors are profitable, neighbor median Sharpe is below 0.50, or
   positive PnL concentration exceeds 40%; or
7. controls improve headline Sharpe only through unacceptable turnover, inactive sleeves, or a
   single fold/regime.

No least-bad negative candidate is a submission. A failure triggers a documented simplification,
one of at most two pivots, or DNF within the shared 80-trial budget.

## Planned trial allocation

Reserve 1 center trial, 6 mechanism/feature ablations, 10 parameter-neighborhood trials, 5
additional risk-policy trials (the combined policy is the center, and each policy automatically
produces base- and doubled-cost outputs), and up to 8 confirmatory/fold-diagnostic trials: 30
planned material configurations. The remaining 50 are contingency capacity and are not
authorization to search
until something looks good. Every material run is preregistered first.
