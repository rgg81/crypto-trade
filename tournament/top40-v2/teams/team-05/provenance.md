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

For the later authority rebind, inspection was additionally limited to Team05 and the public A5/A6
implementation, contract schemas, and authority JSON under `src/crypto_trade/tournament/` and
`tournament/top40-v2/amendments/0005/`/`0006/`. No team namespace, report, evaluator artifact, or
performance source was added to scope.

For the still later A8 administrative replacement rebind, inspection added only the public A7/A8
authority files and the exact Team05 v2 registration/reservation/empty terminal incident bindings
named by the A8 freeze. No model metric or market-data artifact existed in that failed result, and
no other team or performance source entered scope.

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
code, or Git command was run during construction or this authority rebind. This declaration does
not override any separately recorded organizer validation; it makes no claim about such evidence.
All organizer-dependent artifacts remain prospective, and every result-dependent SHA-256 field is
an explicit invalid `REPLACE_WITH...`/`RECOMPUTE...` placeholder.

Earlier local draft hashes were invalidated and removed or marked `RECOMPUTE_AFTER_REMEDIATION`.
No replacement evidence hashes were fabricated. Exact public authority hashes were added because
they are already frozen and explicitly supplied for this rebind; they are not Team05 material
evidence. The organizer must recompute all source, config, risk, neighbor, fold, score-contract, and
manifest hashes from the final Team05 bytes before registration.

## Runtime provenance contract

- Runtime dependencies: Python standard library, organizer-provided pandas, the neutral
  `DecisionContext`/`TargetStrategy` interface, and the active organizer-owned
  `score_adapter_protocol_v5.score_boundary` identity hook.
- Strategy entrypoint: `strategy.build_strategy()`.
- Material candidate selector: hash-bound root `candidate_variant.py`; its ID, overrides, and
  risk-template declaration must exactly match one preregistered cell before the canonical
  zero-argument builder will run.
- Frozen seed: `20260801`; every other runtime seed is rejected.
- No filesystem, network, environment, credentials, reports, staged models, or subprocess access
  exists in the strategy.
- All algorithm constants are compiled into `StrategyParameters`; `frozen_config.json` is the
  human/machine audit mirror and must be drift-checked before registration.
- Risk execution is exclusively organizer-owned. `risk_policy.json` is initially no-control.
  `risk_ablations/*.json` are immutable declarations; after the core-alpha gate, the selected
  declaration must be copied byte-for-byte to root `risk_policy.json` before candidate commit,
  registration, and canonical execution.
- Universe eligibility is exclusively organizer-owned. Team05 consumes the exact point-in-time
  `DecisionContext.eligible_symbols` supplied through active A7 and unchanged delegated A5/A6
  pure-crypto enforcement. It has no symbol allowlist, fallback universe, or eligibility expansion.

## Bound public authorities

- Active A7 runtime entrypoint: `scripts/top40_v2_tournament_runtime_preload_v7.py`, SHA-256
  `8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`.
- Active A7 integration freeze: commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, SHA-256
  `6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`.
- Frozen A8 Team05 one-shot authority: commit `f6003ae687d5a6bf665abb001715b01ea8b10abb`,
  SHA-256 `08bf194c9ade1f66bf38012210ad8604df61ca467cdad00bd3957aa679ea9bdd`.

- Active A5 entrypoint: `scripts/top40_v2_tournament_score_diagnostics_v5.py`, SHA-256
  `0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`.
- Active A5 integration freeze: commit `d2b95f610722aab65b4e67466b34efeaa3554101`, SHA-256
  `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.
- Active A5 score-adapter protocol module: SHA-256
  `8f8f5db3be3069cce7c7c0605fb15b31c4f28af7c2e0f2e24d79d861a65ae4ff`.
- Delegated A6 integration freeze: commit `ed3af1398543dfee4a50150915dc2e37b3631fc9`, SHA-256
  `3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34`.
- A6 canonical report: 73,777 bytes, SHA-256
  `b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, policy SHA-256
  `2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`, zero
violations.

The A6 classification is non-negotiable: stablecoins, equities/TradFi, indexes, metals,
commodities, and any other non-crypto contracts are ineligible even if Binance exposes them as
perpetual contracts. Native crypto coins/tokens certified by A6 are the only universe.

## Freeze obligations

Before registration or a material run, the organizer must verify the active A5/A6 authorities,
strategy/config parity, synthetic and central integration tests, and the complete executable
dependency set. It must then first-add the core executable-source manifest, independently approved
semantic review, score manifest, and registration in that strict order; replace every material
placeholder with exact hashes/paths/timestamps; and bind dependency/source/config/risk/score bytes
in its authoritative journal. Exact equal chronological fold boundaries must be evaluator-derived
before fold evidence is recorded. Later fold, neighbor, private, and final artifacts must be
derived only through the active entrypoint and authorized lifecycle. A mismatch, non-crypto
universe leak, or reproducibility failure falsifies eligibility.
