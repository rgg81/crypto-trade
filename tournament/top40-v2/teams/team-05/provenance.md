# Provenance and clean-room declaration

Prepared 2026-07-16 in the designated Team-05 V2 worktree.

## Shared inputs read

Only these public shared files were read:

- `tournament/top40-v2/PHASE0-POLICY.md`
- `tournament/top40-v2/TEAM-PLAYBOOK.md`
- `tournament/top40-v2/METHODOLOGY-DISTILLATION.md`
- `tournament/top40-v2/config.toml`
- `tournament/top40-v2/README.md` (exact additional path authorized by the organizer/root)
- relevant schemas and the sample risk policy under `tournament/top40-v2/templates/`
- `src/crypto_trade/tournament/protocol.py`
- `src/crypto_trade/tournament/risk_policy.py`
- pre-existing files inside `tournament/top40-v2/teams/team-05/`

The charter path named by the task,
`tournament/top40-v2/TOURNAMENT-CHARTER-TOP40-V2.md`, was absent. The organizer/root confirmed the
absence, authorized the exact V2 README as a lifecycle summary, and instructed Team 05 not to
search for a substitute or broaden scope.

## Inputs explicitly not read

No V1 team/result, other V2 team namespace, report, journal contents, run state, evaluator output,
private/final artifact, leaderboard, ballot, snapshot, market history, or performance data was
listed, searched, opened, hashed, serialized, or inferred. No repository-wide search was run.

## Authoring actions

All writes are confined to the Team-05 namespace. Files were created through patch-based edits.
No Python, test runner, lifecycle command, evaluator, network request, subprocess from strategy
code, or Git command was run. Consequently, all synthetic tests and JSON/schema checks are
**authored but unexecuted**, and every result-dependent SHA-256 field is an explicit invalid
`REPLACE_WITH...` placeholder.

Earlier local draft hashes were invalidated and removed or marked `RECOMPUTE_AFTER_REMEDIATION`.
No replacement evidence hashes were fabricated. The organizer must recompute all source, config,
risk, neighbor, fold, score-contract, and manifest hashes after Amendment 0005 is frozen and before
registration.

## Runtime provenance contract

- Runtime dependencies: Python standard library, organizer-provided pandas, the neutral
  `DecisionContext`/`TargetStrategy` interface, and the prospective organizer-owned
  `score_adapter_protocol_v5.score_boundary` identity hook.
- Strategy entrypoint: `strategy.build_strategy()`.
- Frozen seed: `20260801`; every other runtime seed is rejected.
- No filesystem, network, environment, credentials, reports, staged models, or subprocess access
  exists in the strategy.
- All algorithm constants are compiled into `StrategyParameters`; `frozen_config.json` is the
  human/machine audit mirror and must be drift-checked before registration.
- Risk execution is exclusively organizer-owned. `risk_policy.json` is initially no-control;
  `risk_ablations/combined.json` may activate only after the core-alpha gate.

## Freeze obligations

Before registration or a material run, the organizer must freeze Amendment 0005 and its v5 module,
verify strategy/config parity, execute the synthetic and central integration tests, replace
placeholders with exact hashes/paths/timestamps, and bind dependency/source/config/risk/score bytes
in its authoritative journal. Exact equal chronological fold boundaries must be evaluator-derived
before fold evidence is recorded. Later fold, neighbor, private, and final artifacts must be
derived only through the authorized lifecycle. A mismatch or reproducibility failure falsifies
eligibility.
