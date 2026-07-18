# Top-40 V3 Team Playbook

This is the operational checklist for `team-01` through `team-10`. The charter controls if this
guide is ever ambiguous.

## 1. Build a complete system on training data

Work only with the visible training window and causal warm-up. Develop the signal and the risk
system together. You may add stop losses, time exits, volatility or drawdown brakes, trend/chop
filters, exposure scaling, liquidity filters, sleeve budgets, and deterministic fallback-to-flat
behavior. Test both long and short sleeves and examine bull, bear, chop, and stress performance.
Risk controls are part of the strategy, not an organizer overlay, and must be finished before the
candidate is locked.

The only tradable instruments are the point-in-time members of the A6-certified weekly Top-40.
Do not add a contract because Binance calls it a perpetual. Stablecoins, leveraged tokens,
tokenized or direct metals and commodities, stocks, ETFs, indexes, FX, premarket, and any other
direct TradFi exposure are forbidden. Membership history may be used only at the time at which it
was available.

### Historical incumbent lane for Teams 04, 05, 07, and 09

Each of these teams starts with one provenance-bound V2 port under its `incumbents/` directory.
Treat it as a credible benchmark and an ordinary first V3 material trial—not as a passed model.
Its candidate-local risk policy, seed, entrypoint, and complete source directory must be frozen and
run together. The port receives no inherited train, validation, qualification, rank, probe, or
nomination status.

Incumbents and challengers share the team's ordinary journal and probe budgets. A challenger may
become the preferred lane only after standardized logged V3 evidence shows a meaningful advantage
in qualification gaps, cost/regime robustness, drawdown, concentration, or matching validation.
Until then the team may retain both, but it may probe only within the same three-slot opening
budget and nominate only one exact candidate. Both the incumbent and the final challenger, if
different, must independently be positive on training and validation and pass every ordinary gate.
The full policy and exact ports are in
[`INCUMBENT-CHALLENGER-POLICY.md`](INCUMBENT-CHALLENGER-POLICY.md).

Collision guards remain binding for every new design. They do not retroactively remove the four
listed historical incumbents, and their narrow grandfathering cannot be extended to a new hybrid,
descendant, or copied cross-team mechanism.

## 2. Treat every train run as a real trial

Request train runs through the organizer laboratory. The organizer records the request before
returning results. Give every experiment a purpose and a parent candidate. Code, parameters,
features, seeds, fit windows, sizing, execution assumptions, and risk-rule changes create new
material trials.

For every run, retain:

- candidate and parent IDs plus the hypothesis being tested;
- source, configuration, dependency, seed, risk-policy, data, evaluator, and artifact hashes;
- the complete metric packet, not just Sharpe;
- failures, aborts, gate results, and resource use; and
- the cumulative number of trials examined by the team.

Runs are unlimited, but the history is append-only. Do not delete losing experiments, rename a
candidate to escape its history, split a sweep into supposedly unrelated trials, or present an
identical rerun as new evidence. The active train lab counts every invocation as a material trial;
trial-adjusted confidence uses the complete journal.

A useful train candidate should have positive after-cost return and Sharpe, tolerable drawdown,
positive doubled-cost Sharpe, enough trades, broad quarterly performance, and credible behavior
across the four fixed regimes. A high headline Sharpe with one side, quarter, asset, or parameter
point carrying the result is a warning, even when it is not an automatic veto.

## 3. Spend validation probes deliberately

You receive three probes in the opening round, not three per candidate. Before requesting
one, freeze the exact candidate and verify locally that it is deterministic, causal, solvent,
A6-compliant, and positive on training. A probe request consumes a slot when accepted, including
when your candidate crashes or fails a gate.

The validation service returns only the fixed aggregate packet. It does not reveal raw rows,
returns, trades, positions, regime dates, or interactive slices. Do not infer or request hidden
observations through timing, errors, repeated queries, altered outputs, or side channels.

After a probe:

- an exact deterministic replay does not consume an additional observation when organizer-owned;
- any code, parameter, seed, dependency, sizing, or risk change creates a new candidate; and
- a changed candidate needs another available probe before it can be nominated.

Budget at least one probe for a genuinely mature full system. If the optional comeback round
triggers, an unqualified team receives exactly two additional logged probes.

## 4. Earn readiness before nomination

A candidate is eligible to be considered for nomination only when both train and validation runs
are complete, every hard gate passes, and each window independently has:

```text
net_sharpe > 0
annualized_return > 0
double_cost_sharpe > 0
```

Zero, missing, nonfinite, incomplete, and `DNF` do not qualify. This is merely the readiness gate;
the train-plus-validation public record must also meet every core floor to advance.

When ordinary labs close, identify your best readiness-eligible, public-core-passing candidate if
you have one. If fewer than three teams have such a candidate, the organizer opens one comeback
lab round for teams without one. Continue from the same trial ledger and use the two additional
probes deliberately. Standards, costs, windows, and floors do not change.

## 5. Lock exactly one formal nominee

After the normal or comeback lab closes, you may nominate at most one candidate. The candidate
must be readiness-eligible, pass every public core floor on its deterministic
train-plus-validation record, and exactly match the hashes of its validation probe. Recheck the
source tree, dependencies, configuration, risk controls, parameters, seed, entrypoint, and
artifact manifest before signing the lock.

The formal lock is terminal. There is no second nominee, tactical withdrawal and replacement,
post-lock repair, parameter tweak, risk-overlay change, or dependency refresh. A below-core or
nonpositive candidate is rejected at lock and remains lab evidence rather than a tournament
submission.

## 6. Know the gates and scores

Hard integrity, data/universe, causality, execution, solvency, and completeness gates run before
performance. One failure ends the run.

Public-core advancement requires all of the following on the concatenated train and validation
record: net Sharpe at least 0.75; annualized return above zero; drawdown at most 0.30; doubled-cost
Sharpe at least 0.35; at least half of quarters positive; at least 1,000 executed fills; at least
two of bull, bear, chop, and stress Sharpe positive; and worst-regime Sharpe at least -0.75.
Core passers are ordered by the charter's fixed robustness formula and the top four advance (all
advance if fewer than four pass).

Role/sign checks, walk-forward folds, IC behavior, multiplicity-adjusted confidence, parameter
neighborhoods, and concentration are scored and published. They can reveal a weak research story,
but cannot secretly disqualify you or alter robustness rank.

## 7. Private and final stages

The private qualifier is one frozen run. To pass, hard gates must hold, net Sharpe, annualized
return, and doubled-cost Sharpe must each be strictly positive, and drawdown must not exceed 0.35.
There is no private per-regime veto. A private failure cannot be repaired or replaced.

Private passers enter final OOS unchanged. Results are withheld until the organizer releases every
finalist's complete packet simultaneously. There is one reveal, no interactive feedback, and no
second attempt. Final ordering uses the same robustness formula on final-OOS metrics; the public
core thresholds appear as descriptive flags rather than retrospective final vetoes.

## Pre-lock audit checklist

Before you nominate, all answers should be yes:

- Is every instrument an exact point-in-time A6-approved native crypto contract?
- Does future-data corruption leave all earlier decisions unchanged?
- Are fits, thresholds, memberships, fills, funding, and controls available at decision time?
- Is the candidate deterministic under an exact replay from the frozen dependency lock and seed?
- Does it finish both windows solvent, finite, fully reconciled, and without hidden exceptions?
- Are train and validation net Sharpe, annualized return, and doubled-cost Sharpe each strictly
  positive?
- Is the full system, including every risk control, identical to the last qualifying probe?
- Are all experiments and failures present in the append-only multiplicity journal?
- For an incumbent team, is any replacement decision supported by logged V3 evidence rather than
  inherited V2 status or novelty alone?
- Are you comfortable spending the team's one formal nomination on these exact bytes?
