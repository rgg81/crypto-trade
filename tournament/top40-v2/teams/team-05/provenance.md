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

A local `sha256sum` read of Team-05-authored bytes bound the current `strategy.py`,
`frozen_config.json`, combined/ablation risk policies, and eight neighbor parameter artifacts into
the fold, ablation, neighborhood, and source-binding drafts. It did not read or hash data, results,
journals, or external artifacts. The organizer must recompute these hashes after any review edit
and before registration.

## Runtime provenance contract

- Runtime dependencies: Python standard library and organizer-provided pandas; the neutral
  `DecisionContext`/`TargetStrategy` interface is the only tournament import in strategy code.
- Strategy entrypoint: `strategy.build_strategy()`.
- Frozen seed: `20260801`; randomness is absent and all valid seeds produce the same signal.
- No filesystem, network, environment, credentials, reports, staged models, or subprocess access
  exists in the strategy.
- All algorithm constants are compiled into `StrategyParameters`; `frozen_config.json` is the
  human/machine audit mirror and must be drift-checked before registration.
- Risk execution is exclusively organizer-owned under `risk_policy.json`.

## Freeze obligations

Before the first material run, the organizer must verify strategy/config parity, execute the
synthetic and central integration tests, replace placeholders with exact hashes/paths/timestamps,
register the family and trial, and bind dependency/source/config/risk bytes in its authoritative
journal. Later fold, neighbor, private, and final artifacts must be derived only through the
authorized lifecycle. A mismatch or reproducibility failure falsifies eligibility.
