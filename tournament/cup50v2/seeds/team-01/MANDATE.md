# team-01 — multi-horizon-trend

**Objective.** Trade the persistence of medium-horizon price trends, in both directions.

## Thesis

Crypto perpetuals are traded around the clock by leveraged retail flow with no closing auction to reset positioning. Trends are extended by margin that follows price and cut by liquidations that follow it down, so directional moves persist over weeks rather than mean-reverting within days. The lane's question is which horizons carry that persistence net of cost, and whether the book should stand down when no horizon agrees.

## Directions worth testing

- Blend several formation horizons rather than betting the lane on one.
- Normalise each horizon by the volatility of its own holding period, or a wild name becomes the whole book.
- Deploy less when horizons disagree; a trend book with nothing to trend on should be smaller, not louder.

## What the organizer owns

- fills at the transaction open, fees, slippage, funding and delisting settlement
- weekly Top-50 membership and eligibility
- the common risk unit that sizes every book to a common volatility target
- gross, net, per-symbol and participation caps

## Forbidden

- reading any earlier tournament's directory, results, parameters or conclusions
- any date literal after the in-sample end
- team-level volatility targeting; the organizer owns book size
- pre-fitted objects, cached data, or any state not reconstructed from the streamed context
- reading another team's workspace, the sealed data, or any organizer-private surface

## Deliverable

one frozen candidate: strategy.py exposing build_strategy(), parameters.json declaring a centre and at most five tunable dimensions, risk-declaration.json, and RESEARCH-CERTIFICATE.md

## Scored on

worst fold, worst regime and the whole path, at 1x/2x/3x cost, across the declared neighbourhood rather than the nominated point alone
