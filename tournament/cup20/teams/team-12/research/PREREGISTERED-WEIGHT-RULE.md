# Preregistered sleeve-combination rule — team-12

Written **before** any combined book of any kind had been computed, offline or otherwise, and
before the sleeve set was frozen. It is journaled verbatim in the organiser's hash-chained
research journal at the first accepted trial; the journal record, not this file, is the evidence.

## The rule, verbatim

> **Inverse-volatility (naive risk-parity) sleeve weighting.** At every decision boundary `t`,
> each sleeve `k` emits a weight vector over the eligible symbols that is normalised to unit
> gross (`Σ_i |w_k,i(t)| = 1`). Sleeve `k`'s contribution to the combined book is that unit-gross
> vector multiplied by `1 / σ_k(t)`, where `σ_k(t)` is the sample standard deviation (ddof = 1)
> of sleeve `k`'s own past-only proxy return series over the most recent `RISK_PARITY_BARS`
> observations available strictly before `t`. The proxy return attributed to boundary `g` is
> `x_k(g) = Σ_i w_k,i(g-1) · (close_i[g-1] / close_i[g-2] − 1)` — the sleeve's own unit-gross
> weight vector formed at the previous boundary, applied to the close-to-close simple return of
> the bar that closed at `g`; no costs, no funding, no leverage. Until `RISK_PARITY_BARS` such
> observations exist, or if `σ_k(t)` is not finite and strictly positive, sleeve `k` receives the
> multiplier `1`. The combined book is the plain sum of the scaled sleeve vectors and is returned
> unnormalised; the evaluator's own unit-gross normalisation then applies. **No other sleeve-level
> multiplier, tilt, cap, floor, sign flip, correlation adjustment or performance-conditioned term
> of any kind is applied, at any boundary, ever.**

`RISK_PARITY_BARS = 270` (90 days on the 8h grid), chosen a priori to match the organiser's own
common-risk-unit lookback of 90 days (charter §6) rather than being selected from any result.

## What this rule deliberately does not do

- It does **not** use the cross-sleeve correlation matrix. A full equal-risk-contribution
  solution would, and it would then adapt the combination toward whatever happened to diversify
  in sample — which is precisely the tuning this lane forbids. Naive risk parity is the version
  of "equal risk" that cannot learn from the answer.
- It does **not** condition on any sleeve's realised Sharpe, drawdown, hit rate or sign. A sleeve
  that is losing money receives exactly the same risk budget as one that is not.
- It does **not** allow a zero weight. Dropping a sleeve after seeing a combined result is
  re-weighting under another name.

## Falsifiable consequence, stated before the fact

If independent mechanisms diversify each other's drawdowns here, the equal-risk combination will
show a **lower maximum drawdown and a higher worst-fold Sharpe than its own best single sleeve**,
not merely a return that is the average of the sleeves'. If instead the combination's drawdown
sits between the sleeves' — an average rather than a cancellation — then the sleeves shared a
common factor and diversification did nothing, and that is the result to report.

## Sleeve set

Four sleeves on four distinct causal bases, fixed before the first combined evaluation:

| Sleeve | Causal base | Construction |
|---|---|---|
| CARRY | the perpetual funding mechanism transfers cash from the crowded side to the uncrowded side | cross-sectional rank of trailing mean funding rate, sign flipped |
| TREND | slow diffusion of information across a fragmented 24/7 retail base, plus reflexive leverage | per-coin time-series momentum, volatility-scaled, multi-horizon; net exposure is free |
| LOWRISK | leverage-constrained and lottery-seeking participants overpay for high-volatility names | cross-sectional rank of trailing drawdown depth, sign flipped |
| FLOW | aggressive, price-insensitive taker demand leaves a persistent footprint in the buy/sell split of traded volume | cross-sectional rank of trailing taker-buy share |

Two of these four (CARRY, TREND) have a **negative** standalone ranking score on the offline
replica. They are in the book anyway. Dropping a sleeve because its standalone number is poor is
selecting the combination on performance, which is the same disease as selecting the weights on
performance; the point of a preregistered ensemble is that the weakest member still gets its
risk budget.
