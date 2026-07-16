# Team 06 provenance

## Design boundary

This package was authored on 2026-07-16 in the Team 06 V2 namespace. The design review used only
the permitted Top-40 V2 public README, Phase-0 policy, team playbook, methodology distillation,
frozen `config.toml`, relevant public templates, the neutral strategy protocol and declarative
risk-policy contract, and pre-existing Team 06 bootstrap files. It did not inspect performance
data, snapshot observations, evaluator outputs, reports, journals, run state, amendments, private
or final artifacts, ballots, leaderboards, another team, or any V1 team/result.

No Python, test, tournament lifecycle, evaluator, or Git command was run. No network source,
external research, historical coefficient, performance estimate, or opaque fitted state informed
the mechanism or parameters. Accordingly, every expected behavior in `research_brief.md` is a
preregistered hypothesis rather than evidence.

## Executable provenance

- Runtime dependency: Python standard library plus pandas already named by the neutral protocol.
- Canonical entrypoint: `strategy.py:build_strategy` with seed `20260801`.
- Runtime reads/writes: none. The strategy has no filesystem, network, subprocess, environment,
  credential, report, snapshot, or evaluator access.
- State: only immutable constants and a new strategy instance; no learned or persisted state.
- Randomness: none. The seed is nevertheless checked exactly to prevent accidental drift.
- Input fields used: decision time, eligible-symbol identity, and past-closed bar time/close.
  Funding, auxiliary fields, prices other than close, positions, fills, costs, and risk state are
  ignored.
- Timestamp rule: explicitly truncate to close timestamp <= decision time, sort stably, resolve
  duplicate timestamps deterministically, and reject stale/invalid histories.
- Construction rule: all valid members cross the public preconstruction score boundary before
  selection or sizing. The optional local identity hook must echo keys and values exactly and is
  absent from the canonical build. No nonexistent shared hook is imported.
- Risk: `risk_policy.json` is declarative; only the central evaluator may act on authoritative
  state, at the next open, with ordinary costs and shared participation capacity.

`frozen_config.json`, `feature_lineage.json`, `risk_policy.json`, `strategy.py`, and the six fold
declarations form the intended base source/config bundle. The four neighbor parameter artifacts
and wrappers are dormant and byte-distinct; they must not enter a trial bundle until base-core
pass. Risk-only policy files are likewise dormant attribution artifacts.

## Hash and registration status

No hash in a `*.template.json` file is evidence. Angle-bracket values are deliberate invalid
sentinels so an unproduced artifact cannot masquerade as a valid SHA-256 or timestamp. The
organizer must compute hashes from final bytes, replace sentinels in a copy, validate it against
the public schema, and register it through the authoritative lifecycle. Do not edit the templates
after registration to simulate a journal record.

`families.jsonl` and `experiments.jsonl` were left untouched because they are derived organizer
projections. Resource usage remains zero only as an unevaluated design statement; the organizer
journal becomes authoritative as soon as registration/execution begins.

## Reproduction contract

Two clean official workers must instantiate the exact frozen bundle and seed and emit identical
targets and artifact hashes. Synthetic tests are authored in `test_strategy.py` but not executed.
Evaluator-owned integration checks are listed separately in `synthetic_test_plan.md`. A replay
mismatch, source/config mismatch, or hidden runtime dependency is a provenance failure.
