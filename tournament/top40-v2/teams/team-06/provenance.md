# Team 06 provenance

## Design boundary

This package was authored on 2026-07-16 in the Team 06 V2 namespace. The original design review used only
the permitted Top-40 V2 public README, Phase-0 policy, team playbook, methodology distillation,
frozen `config.toml`, relevant public templates, the neutral strategy protocol and declarative
risk-policy contract, and pre-existing Team 06 bootstrap files. It did not inspect performance
data, snapshot observations, evaluator outputs, reports, journals, run state, amendments, private
or final artifacts, ballots, leaderboards, another team, or any V1 team/result.

No Python, test, tournament lifecycle, evaluator, or Git command was run. No network source,
external research, historical coefficient, performance estimate, or opaque fitted state informed
the mechanism or parameters. Accordingly, every expected behavior in `research_brief.md` is a
preregistered hypothesis rather than evidence.

## Active-authority rebind

On 2026-07-16 the prospective package metadata was rebound, without evaluation, to the public A5
active entrypoint SHA-256
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4` and integration-freeze
commit/SHA-256 `d2b95f610722aab65b4e67466b34efeaa3554101` /
`b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`. The A5 dispatcher
delegates unchanged to the A6 integration-freeze commit/SHA-256
`ed3af1398543dfee4a50150915dc2e37b3631fc9` /
`3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34` and its zero-violation
pure-crypto audit. This rebind inspected only public A5/A6 authority/code/schemas and Team06.

No scripts, tests, evaluators, lifecycle operations, or Git commands were run during the rebind.
No candidate hash, independent-review approval, registration, result, or performance evidence was
created. Public authority hashes above are bindings, not Team06 result evidence.

## Executable provenance

- Runtime dependency: Python standard library plus pandas already named by the neutral protocol.
- Canonical entrypoint: `strategy.py:build_strategy` with seed `20260801`.
- Candidate selection: the zero-argument root factory validates and consumes the exact candidate
  ID/override dictionary committed in root `candidate_variant.py`. Unknown IDs and mismatched
  overrides are hard errors; there is no nested entrypoint selection.
- Runtime reads/writes: none. The strategy has no filesystem, network, subprocess, environment,
  credential, report, snapshot, or evaluator access.
- State: immutable source constants, the hash-bound root candidate variant, and a new strategy
  instance; no learned or persisted state.
- Randomness: none. The seed is nevertheless checked exactly to prevent accidental drift.
- Input fields used: decision time, A6-certified pure-crypto eligible-symbol identity, and canonical
  RangeIndex bar `open_time` / `close`.
  Funding, auxiliary fields, prices other than close, positions, fills, costs, and risk state are
  ignored. Team06 performs no symbol-text asset classification; the active organizer authority must
  exclude stablecoins, TradFi/equities, commodities/metals, and indexes before context creation.
- Timestamp rule: admit a close only when `open_time + 8h <= decision_time`, sort stably by
  `open_time`, resolve duplicates deterministically, and reject noncanonical/stale/invalid data.
- Construction rule: every valid finite built-in score crosses the directly imported public
  `score_boundary` exactly once after transforms and before selection/weight caps/risk. Its
  returned values drive construction.
- Risk: the evaluator reads only top-level `risk_policy.json`. Files under `risk_policies/` are
  inert templates until the organizer copies the selected bytes to that root path before the
  candidate commit, registration, and run. Only the evaluator may act on state.

Every `.py` file in the registered Team06 tree—including `candidate_variant.py`—plus
`frozen_config.json` and top-level `risk_policy.json` must appear in the complete A5
executable-source manifest. The obsolete nested neighbor wrappers were removed;
neighbor JSON files now prescribe exact root materialization. Controls and neighbors remain
dormant until their noncompensatory activation conditions pass.

## Hash and registration status

No hash in a `*.template.json` file is evidence. Angle-bracket values are deliberate invalid
sentinels so an unproduced artifact cannot masquerade as a valid SHA-256 or timestamp. The
organizer must first commit the exact root `candidate_variant.py` and byte-materialized root
`risk_policy.json`, then finalize executable bytes; materialize the complete acyclic
executable-source manifest; obtain the independent semantic-coupling review; and materialize the
score manifest and exact nested registration opt-in. Only after replacing sentinels from
authoritative bytes may the organizer validate and register through the active lifecycle. Do not
edit templates to simulate a journal record or review approval.

`families.jsonl` and `experiments.jsonl` were left untouched because they are derived organizer
projections. Resource usage remains zero only as an unevaluated design statement; the organizer
journal becomes authoritative as soon as registration/execution begins.

## Reproduction contract

Two clean official workers must instantiate the exact frozen bundle and seed and emit identical
targets and artifact hashes. Synthetic tests are authored in `test_strategy.py` but not executed.
Evaluator-owned integration checks are listed separately in `synthetic_test_plan.md`. A replay
mismatch, source/config mismatch, or hidden runtime dependency is a provenance failure.
