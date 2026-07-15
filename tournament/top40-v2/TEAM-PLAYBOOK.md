# Top-40 V2 team playbook

This playbook applies to every `team-01` through `team-10` pair. The charter, Phase-0 policy, and
frozen config are authoritative.

## The tournament mindset

A team is not required to defend its first idea or submit a model merely because time was spent
on it. Negative development evidence means continue, simplify, change the risk policy, make a
documented mechanism pivot, or finish DNF. It is not a submission.

The target is a causal, reproducible portfolio that clears every non-compensatory development
gate and then survives the one-shot private qualifier. Relative rank, Critic points, and user
points can never rescue a failed gate.

## Clean-room boundary

Read only the V2 charter, V2 methodology/config/templates, neutral V2 evaluator interfaces,
approved public references, and your own namespace. Do not inspect V1 teams or results, another
V2 team, private qualifier artifacts, final-OOS data, ballots, or leaderboards. Never call the
snapshot or evaluator outside an organizer command.

The worker receives only past-closed data through the authorized stage cutoff. A strategy must
not contain timestamp-to-target tables, prefitted opaque state, or historical coefficients learned
from the complete evaluation period.

## QR responsibilities

Before measuring a family, preregister its mechanism, economic thesis, data availability rules,
expected bull/bear/chop/stress behavior, long/short sleeve roles, parameter ranges, selection
metric, falsifier, and planned risk-control ablations. Every material feature, model, parameter,
ensemble, portfolio rule, and risk overlay counts toward the same cumulative trial budget.

Use genuinely chronological walk-forward construction. Learned preprocessing, feature selection,
model fitting, and ensemble weights belong inside training folds. Predictions used for the
qualification series must be out of fold, with purging and embargo where labels overlap.

At each review point, prefer evidence over attachment to a thesis. If no candidate is profitable
across most folds, pivot. If a result is an isolated parameter spike, reject it even if its point
estimate passes.

## QE responsibilities

Implement only the QR's explicit specification behind `build_strategy()` and
`target_weights(context, seed=...)`. Return finite signed weights for eligible symbols, `{}` to
request flat, or `None` to hold. The central evaluator exclusively owns fills, membership exits,
funding, fees, slippage, participation, positions, equity, risk-policy actions, and scores.

Keep all executable helpers and fixed configuration inside the team namespace. Official workers
have no network, subprocess, writable filesystem, credential, repository, report, or private-data
access. All randomness, feature order, refits, and dependencies must be deterministic.

Required tests cover future truncation/corruption/append invariance, next-open execution,
point-in-time membership, funding signs and timestamps, base versus doubled costs, long/short
attribution, risk-policy action ordering, same-boundary reentry prevention, and clean-process
reproducibility.

## Qualification sequence

1. Register the initial mechanism family before its first material trial.
2. Register every material candidate with `register-trial` before reading its result; never edit
   `experiments.jsonl`, which is an exact projection of the organizer hash-chain journal.
3. Use `run-window development` for the cutoff-safe evaluator and inspect the complete gate report.
4. Continue, ablate, or use at most two documented pivots until one candidate passes every gate.
5. Provide six hash-bound fold/model declarations and at least three byte-distinct neighboring
   parameter definitions/return series. Fixed slices of one fitted backtest are not proof of OOF.
6. Freeze the executable source bundle, parameters, seeds, risk policy, journal head,
   neighborhood, runner artifacts, provenance, and centrally derived development evidence.
7. Consume the one private ticket through `run-window private`. Before cohort lock, the team
   receives pass/fail and failed gate names only, never numerical private observations.
8. A private failure is terminal DNF. A pass creates a finalist.
9. Final OOS becomes available only after all ten teams are qualified or DNF and the cohort lock
   is committed. It is evaluated once and is never a tuning round.

## Risk controls

Risk controls are declarative and centrally executed from authoritative state. Available controls
are volatility targeting, drawdown brakes, close-confirmed position stops, time stops, cooldowns,
side scaling, and turnover limits. No control receives an intrabar fill. A confirmed action uses
the next transaction open, pays normal costs, and shares participation capacity. Unless the
frozen policy explicitly allows it, a stopped symbol cannot reopen at the same boundary.

Evaluate the signal without controls, each control alone, the combined policy, and all of those at
doubled costs. A risk policy should improve a stated failure mode rather than cosmetically lower
volatility after seeing the answer.

## Required team artifacts

Maintain the team-authored inputs around organizer-owned `families.jsonl` and `experiments.jsonl`:
`research_brief.md`, `feature_lineage.json`,
`ablations.json`, `parameter_neighborhood.json`, `provenance.md`, `strategy.py`,
`frozen_config.json`, and `risk_policy.json`. Record negative and abandoned results as carefully as
positive ones. A DNF with honest evidence is a valid scientific outcome; fabricated or omitted
research accounting is not.
