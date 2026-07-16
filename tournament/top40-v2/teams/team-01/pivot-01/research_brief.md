# Research brief: regime-conditional trend/carry pivot

Status: specified and implemented locally; not registered, tested, or evaluated  
Family: `t01-regime-conditional-trend-carry-v2`  
Reference: `rctc-pivot-ref-001`  
Parent evidence: stopped family `t01-residual-drift-funding-v1`

## Question

Does unconditional BTC residualization remove common downside information that Team 01's short
sleeve needs in bear markets? The completed H14 parent candidate had strong aggregate, bull, chop,
and doubled-cost results, but only three positive chronological folds and negative bear performance.
The pivot tests one bounded causal answer; it does not reinterpret that parent failure as a pass.

## Frozen hypothesis

A raw, path-efficient 14-day downside trend should identify absolute losers in a lagged BTC bear
state better than the otherwise identical BTC-residual continuation score. Residual continuation
should remain appropriate in bull and chop. The seven-day actual-funding penalty should continue to
reduce crowding in every state.

## Reference design

At each daily `00:00 UTC` boundary, the strategy requires exact BTC closes at `t-1d` and `t-61d`.
It labels bull at a 60-day log return `>=+0.10`, bear at `<=-0.10`, and chop otherwise. The close at
`t` cannot affect either the label or the bounded direction tilt.

For every eligible non-BTC contract, the strategy still requires 30-day paired BTC coverage and a
valid clipped BTC beta. In bull/chop it computes the H14/K3/gamma0.5 transform from BTC-residual 8h
returns. In bear it computes the identical standardized, path-efficient transform from raw asset
8h returns. State-signal sample volatility supplies the sleeve inverse-volatility input. Funding is
the actual seven-day sum with at least 14 events and enters as `-0.35 * robust_z(funding)`.

The current cross-section must contain at least 24 valid contracts. The strategy selects signed
`q=0.25` tails with at least six names per side, uses 20/80 winsorized inverse-volatility weights and
deterministic capped-simplex projection, caps each symbol at `0.09`, and fixes total gross at `0.80`.
The same lagged BTC log return, divided by `0.20` and clipped to `[-1,1]`, tilts the sleeves by
`delta=0.075`. The reference uses runtime seed `20260801` and no risk controls.

## Causal falsifier

The reference fails without rescue if its canonical record is incomplete or insolvent, aggregate
no-control net Sharpe is nonpositive, fewer than four of six chronological folds have positive net
return, any bull/bear/chop net return is nonpositive, any required long-bull/short-bear/chop role is
nonpositive, fewer than three evaluator regimes have positive Sharpe, or worst-regime Sharpe is
below `-0.25`. Bear return and short-bear attribution must be positive against the completed H14
all-residual comparator. Failure authorizes neither neighborhood search nor risk controls.

## Staged work

1. An organizer replaces the pending registration timestamp, records the new family, freezes source
   and policy hashes, runs the local contract suite twice, and records the exact synthetic hash.
2. The organizer registers and evaluates only `rctc-pivot-ref-001` with no controls.
3. A result-blind review applies the falsifier. Failure means DNF or a separately registered second
   and final pivot. Passing permits preregistration of the planned component tests and neighborhood.
4. Risk cells may be registered only after the reference causal and role gates pass.

No result, hash, pass count, performance statistic, or registration timestamp is claimed by this
package.
