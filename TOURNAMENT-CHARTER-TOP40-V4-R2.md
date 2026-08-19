# Top-40 V4-R2 tournament charter

Status: pre-activation authority

Tournament: `quant-portfolio-blind-top40-v4-r2`

## 1. Objective and field

This is a fifteen-team, pure-crypto model-building tournament. Every team begins from the same
strategy-neutral brief and independently chooses its economic mechanism. No team receives a
preferred alpha family, incumbent, historical strategy, prior result, or other team's work.

The tournament has transparent in-sample research, robust IS selection, one sealed historical
championship, and a later live-forward paper observation. At most six eligible nominees advance.
There is no forced finalist, no forced winner, and no lowering of a hard floor to fill a bracket.

## 2. Evidence windows

| Layer | Interval, UTC | Permitted use |
|---|---|---|
| IS research | `[2020-02-03, 2024-07-01)` | complete causal artifacts and standardized feedback |
| Historical holdout | `[2024-07-01, 2026-08-01)` | one atomic cohort release; includes all July 2026 |
| Operational embargo | `[2026-08-01, 2026-09-01)` | no research, scoring, or forward performance |
| Live forward | from `2026-09-01` | paper only, frozen identities, at least 365 days |

The historical holdout is candidate-relative: it is valid only for a candidate and research team
that never accessed it. It is not described as globally pristine. Historical performance alone
cannot authorize capital.

## 3. Clean-room isolation

Team access is deny by default. A short-lived offline process receives only the sanitized edition-2
team kit and its own lane. Repository history, legacy research, other lanes, organizer-private
state, sealed rows, sealed progress, plugins, subagents, browser tools, and the public internet are
outside the OS-enforced surface. The process exits before the organizer evaluates its outbox; a
later fresh process sees only lane-local normalized feedback.

A blocking process-wide broker lease covers both research processes and official evaluation, so
two teams can never be active together. Organizer launch authorities, candidate receipts,
feedback packets, and outbox archives make every phase idempotently restartable; a host restart
cannot restore a trial or strand a completed lane.

The organizer audits all fifteen surfaces at activation and cohort boundaries, and audits only the
named lane before a lane result command so peer progress cannot become an oracle. Candidate trees
must be unlinked regular UTF-8 text, contain no prohibited artifact reference, and carry an exact
candidate-local clean-room attestation. Only Python files from the immutable content-addressed
archive execute in a networkless, process-restricted, repository-masked namespace.
Self-attestation does not cure a demonstrated boundary violation: such a candidate is invalid.
Executable authority is further limited to a compact stateless causal AST subset: one explicit
decision method, no persistent self state or decision-time ordinal, and no packing arithmetic,
literal indexing, character decoding, executable docstrings, or high-capacity literal surface.
The exact archived source must pass this semantic subset and three-scenario future invariance
before nomination.

## 4. Market and execution authority

Only point-in-time members of the frozen, weekly reconstituted Top-40 Binance USD-M native-crypto
universe may be traded. Stablecoins, fiat proxies, leveraged tokens, tokenized or direct TradFi,
equities, funds, metals, commodities, indexes, and FX are ineligible. Unknown classifications fail
closed.

Features use only information available at the decision boundary. Orders execute at the next
executable open. Funding applies to the carried position before rebalance. Base costs are 5 bps
taker fee plus 2.5 bps slippage per side, with independent 2x and 3x evaluations. The organizer
owns gross, net, symbol, participation, membership-exit, and missing-market controls.

## 5. Free research lanes

Teams may choose any causal mechanism compatible with the authorized Binance inputs and execution
contract. Convergent independent ideas are allowed; copying or reading another strategy is not.
A team's first accepted mechanism establishes its lane identity. One documented mechanism pivot is
allowed only after the original thesis is falsified across the required matrix.

Every material trial is accepted into an append-only, hash-chained journal before market data are
opened. Failed, crashed, abandoned, or invalid trials consume their slot. Each team receives at
most twelve trials and must have at least eight accepted trials before nomination or retirement.

## 6. Mandatory research evidence

A nomination certificate must bind journal records covering:

- a transparent baseline and exact sign inversion;
- at least three formation horizons and two rebalance or holding horizons;
- controls-off, individual-control, and combined-control ablations;
- long, short, bull, bear, chop, and stress roles;
- at least five preregistered local-neighborhood points; and
- every success, failure, pivot, crash, and abandonment.

Selection is conjunctive. Required evidence includes full-period base/2x/3x performance, five
chronological folds, positive-quarter breadth, turnover and cost-share limits, gross edge density,
long and short contribution, return-concentration limits, neighborhood stability, and
trial-adjusted block-bootstrap confidence. Exact unrounded values decide every gate.

At IS close, the same bootstrap probability is adjusted again against every accepted trial across
all fifteen lanes. This field-wide confidence must remain at least 0.90. It is computed only after
all lanes are terminal, so teams cannot optimize against a moving field threshold.

## 7. Selection and frozen ensemble

Eligible nominees rank by worst-fold 2x Sharpe, median-fold 2x Sharpe, trial-adjusted confidence,
gross edge per turnover, lower turnover, then team ID. At most six advance. Fewer qualifiers mean
fewer finalists; an empty field is a valid result.

At the same boundary, the organizer freezes a reporting-only inverse-IS-volatility ensemble with a
25% constituent cap. Unallocatable or failed weight remains cash and is never redistributed.
At least two finalists are required; otherwise the ensemble is unavailable and remains 100% cash.
Holdout returns never change weights. The ensemble cannot win the individual tournament.

## 8. One-shot historical holdout

All finalist identities, source archives, risk policies, dependencies, data authority, evaluator,
selection order, and ensemble weights are frozen before any holdout row is opened. Every finalist
acceptance is journaled before the first run begins. A separate start marker consumes the single
observation; interruption after that marker is a DNF with no retry, repair, substitution, or
backfill.

Runs are serial but per-team result, progress, error, timing, and completion order remain sealed.
The organizer builds and verifies all individual packets, the ensemble, and their manifest in a
private staging area. One release authorization binds the complete cohort before one atomic public
rename.

Winner eligibility requires positive base and 2x annualized returns, positive 2x Sharpe, maximum
drawdown no greater than 30%, and at least five positive calendar quarters among the nine touched
by the July-2024 through July-2026 window. Eligible candidates rank by 2x Sharpe, base annualized
return, lower drawdown, gross edge per turnover, lower turnover, then team ID. If none qualifies,
there is no winner.

## 9. Activation and amendments

Activation is single-shot. It must bind this charter, numerical config, all fifteen clean-room
surfaces, implementation, dependency lock, evaluator, July-inclusive snapshot authority,
pure-crypto audit, focused tests, and adversarial-review record. A snapshot ending before
`2026-08-01T00:00:00Z` makes activation impossible.

After activation, changes require a prospective append-only amendment made before affected data
are accessed. No amendment may rewrite evidence, restore a consumed observation, reveal partial
holdout state, lower a qualification floor, or make a changed model inherit earlier evidence.
