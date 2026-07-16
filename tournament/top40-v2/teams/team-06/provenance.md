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
- Input fields used: decision time, eligible-symbol identity, and canonical RangeIndex bar
  `open_time` / `close`.
  Funding, auxiliary fields, prices other than close, positions, fills, costs, and risk state are
  ignored.
- Timestamp rule: admit a close only when `open_time + 8h <= decision_time`, sort stably by
  `open_time`, resolve duplicates deterministically, and reject noncanonical/stale/invalid data.
- Construction rule: every valid finite built-in score crosses the directly imported public
  `score_boundary` exactly once after transforms and before selection/weight caps/risk. Its
  returned values drive construction.
- Risk: top-level `risk_policy.json` is the initial no-control policy; combined controls are
  separate in `risk_policies/combined.json`. Only the evaluator may act on state.

`frozen_config.json`, `feature_lineage.json`, `risk_policy.json`, `strategy.py`, and the organizer-
derived fold declaration form the initial bundle. Controls and neighbors remain dormant until
their noncompensatory activation conditions pass.

## Hash and registration status

No hash in a `*.template.json` file is evidence. Angle-bracket values are deliberate invalid
sentinels so an unproduced artifact cannot masquerade as a valid SHA-256 or timestamp. The
organizer must first complete the A5 candidate-manifest/contract freeze and byte-invariance replay,
then compute hashes from final bytes, replace sentinels in a copy, validate it, and register it
through the authoritative lifecycle. Do not edit templates to simulate a journal record.

`families.jsonl` and `experiments.jsonl` were left untouched because they are derived organizer
projections. Resource usage remains zero only as an unevaluated design statement; the organizer
journal becomes authoritative as soon as registration/execution begins.

## Reproduction contract

Two clean official workers must instantiate the exact frozen bundle and seed and emit identical
targets and artifact hashes. Synthetic tests are authored in `test_strategy.py` but not executed.
Evaluator-owned integration checks are listed separately in `synthetic_test_plan.md`. A replay
mismatch, source/config mismatch, or hidden runtime dependency is a provenance failure.
