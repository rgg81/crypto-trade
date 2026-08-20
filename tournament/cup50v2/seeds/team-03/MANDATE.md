# team-03 — residual-cross-sectional-momentum

**Objective.** Trade the cross-section of relative strength after removing the market factor.

## Thesis

Almost all of an altcoin's variance is BTC beta, so raw cross-sectional momentum is largely a leveraged market bet that works until the market turns. The residual — how a name performed relative to what its beta implied — is the part that could be about the name. The lane's known hazard is the momentum crash: after a deep drawdown the shorts rebound hardest, and an unguarded book takes its worst loss precisely when the market recovers.

## Directions worth testing

- Skip the most recent days of the formation window; the last week is reversal, not momentum.
- Hysteresis between entry and exit ranks cuts turnover without changing the view.
- A guard against the rebound after a market drawdown is expected, and its trigger must be causal.

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
