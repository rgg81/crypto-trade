# team-11 — walk-forward-learned-model

**Objective.** Learn the cross-sectional combination of causal features, refitting as the market changes.

## Thesis

Every other lane fixes its combination rule in advance. This one asks whether a regularised model, refit on an expanding window of the team's own accumulated observations, adapts across regimes better than a fixed rule. The lane exists because prior investigations in this repository found cross-sectional machine-learned alpha inverting through regime shifts, twice; the interesting question is whether regularisation and honest refitting change that.

## Directions worth testing

- The model may only be fitted from rows the streamed context has already delivered; there is no pre-fitted artifact and no training set outside the replay.
- Rank-transform features cross-sectionally, or the model fits the market's volatility level instead of the cross-section.
- Prefer heavy regularisation and few features; the sample is short and the noise is large.

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
