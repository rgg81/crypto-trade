# team-08 — volume-shock-event-reversal

**Objective.** Fade the overshoot in a single-bar liquidation cascade.

## Thesis

A leveraged market liquidates in cascades: a move large enough to trigger margin calls forces selling that triggers more, and the print overshoots what the news warranted. The overshoot reverts over days. This is an event lane, not a continuous one — most bars are not events, and the book should be flat between them. Its hazard is that a genuine repricing looks identical to a cascade for one bar, and fading it is how a reversal book dies.

## Directions worth testing

- Require both an extreme return and abnormal volume; either alone is a different event.
- A fixed holding period is a legitimate exit and easier to defend than an optimised one.
- Distinguish a shock with the trend from one against it; they are not the same trade.

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
