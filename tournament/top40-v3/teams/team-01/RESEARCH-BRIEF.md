# Team 01 research brief: weekday residual seasonality

## Mandate

Build a broad, market-neutral portfolio from recurring weekday-specific relative returns. This
is a calendar-flow hypothesis, not generic momentum and not an invitation to mine arbitrary
dates.

Primary evidence: [Seasonality in the Cross-Section of Cryptocurrency Returns](https://www.sciencedirect.com/science/article/pii/S154461232030235X)
reports that a coin's prior same-weekday returns predict its future cross-sectional return and
that the effect is not subsumed by standard size, momentum, beta, idiosyncratic-volatility, or
liquidity controls.

## Causal feature

At each 00:00 UTC daily decision:

1. Aggregate completed 8-hour bars into UTC daily close-to-close returns.
2. For every past day, subtract the eligible pure-crypto cross-sectional median return.
3. For each coin, estimate the robust mean of its residual return on the same weekday as the
   target day, using only earlier occurrences.
4. Shrink toward zero for short histories and studentize by the dispersion of same-weekday
   observations. Rank the final expected residual once across eligible coins.

The reference portfolio is equal-dollar long the top quantile and short the bottom quantile,
exactly net neutral, entered at the next available open. Require a predeclared minimum number of
same-weekday observations. Do not use the target day's partial bars.

## Required research

- Baselines: zero forecast; unconditional cross-sectional mean; ordinary trailing-return
  momentum with the same turnover; raw weekday mean without market residualization.
- Lookbacks: 8, 13, and 26 prior same weekdays. Test expanding and rolling estimates without
  selecting a different window per coin.
- Holding periods: one, two, and three days. Overlapping holdings must be represented as
  independent causal sleeves, not treated as independent observations.
- Sign tests: same-weekday continuation, its exact inversion, and a weekday-label permutation
  placebo fixed before evaluation.
- Neutralization: raw return, cross-sectional-median residual, and causal rolling-beta residual.
- Attribution: every weekday, both sleeves, every chronological fold, bull/bear/chop, costs, and
  membership-entry cohorts.

## Risk controls

Use broad sleeves, a small symbol cap, a minimum-history gate, volatility scaling capped at one,
and a turnover limit matched to the chosen holding period. Test a close-confirmed stop and
cooldown only for isolated coin gaps. Do not suppress an inconvenient weekday after seeing its
return. The final portfolio must retain active long and short sleeves in all regimes.

## Falsifiers

Pivot if the residualized factor is nonpositive after base and doubled costs or a fixed weekday
permutation performs similarly. Concentration in one weekday, coin, or listing cohort and sign
changes across nearby lookbacks are repair signals that lower robustness, not standalone vetoes.
Weak fold or role evidence is treated the same way. Risk controls cannot rescue a negative
calendar core.

## Collision guard

Do not model within-day UTC slots, previous-bar continuation/reversal, funding, taker flow,
liquidity routing, or multi-horizon trend. Those belong to Teams 10, 09, 07, and 08. Team 01's
alpha must be the identity of the UTC weekday and the coin's strictly lagged history on that
weekday.
