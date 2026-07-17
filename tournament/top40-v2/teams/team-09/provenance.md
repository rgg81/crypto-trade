# Team09 provenance and clean-room declaration

Status: **pivot-01 prospective and unregistered; parent evidence preserved**

## Permitted sources inspected

This draft was produced from the public Top-40 V2 charter, `config.toml`, methodology, Phase-0
policy, team playbook, public JSON schemas, neutral strategy protocol/runner interfaces, the
organizer-supplied A7/A5 identity contract, active Amendment 0006, and Team09's own bootstrap,
parent ledgers, parent score artifacts, and parent terminal result. No other V2 team, V1
strategy/result, private record, final-OOS data,
ballot, leaderboard, report, or evaluator output was inspected.

The eventual market authority is the shared immutable Binance USD-M snapshot bound by
`tournament/top40/data_manifest.json` with SHA-256
`077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
The strategy uses only the neutral worker's past-closed `bars`, strictly past `funding`, and
point-in-time `eligible_symbols` views. It does not read snapshot files directly.

The parent family ran only top-level no-control `risk_policy.json` and failed its activation rule;
all parent controls are permanently forbidden. Pivot-01 again begins with top-level no-control
bytes, byte-identical to `risk_policies/00-none.json`. Optional pivot policies are dormant unless
the new core passes every activation gate and cannot rescue failure.

## A7 execution, delegated A5 score, and pure-crypto authority

All future lifecycle and result-bearing commands must use
`scripts/top40_v2_tournament_runtime_preload_v7.py`, SHA-256
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`. A7 integration freeze
commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, SHA-256
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`, preloads and delegates
the exact A5 score surface pinned in `a5_score_lineage.json`. The historical A5 script is not
invoked directly. The authority chain preserves Amendment 0006, whose canonical report SHA-256 is
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b` and policy SHA-256
`2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`.
Only native-crypto assets certified by that authority are in scope. A Binance perpetual listing
alone is not sufficient; stablecoins, tokenized/direct metals or commodities, equities, ETFs,
indexes, FX, premarket/TradFi contracts, and leveraged tokens are forbidden.

## Pivot origin

The parent result showed that confirmed funding-crowd unwind was profitable overall but structurally
failed in bear conditions. Pivot-01 replaces the parent selection mechanism only during a causal
broad decline: it longs relative resilience and shorts downside fragility using relative trend,
downside beta, and drawdown depth. It does not consume organizer regime labels or portfolio risk
state and is not a sign flip or optional risk overlay. The design is self-contained in
`strategy.py` and was not copied from another team.

## Dependency and execution declaration

Executable strategy dependencies are Python standard library modules `dataclasses`, `math`,
`numbers`, and `collections.abc`, organizer-provided `numpy` and `pandas`, and the exact A5
`score_adapter_protocol_v5.score_boundary` hook preloaded by A7. `build_strategy()`
performs no I/O. Strategy execution uses no network, subprocess, filesystem, credentials,
environment data, repository discovery, opaque fitted state, or unseeded randomness. The strategy returns target
weights only. The central evaluator exclusively owns fills, fees, slippage, funding cashflows,
participation, positions, equity, entry basis, delistings, and risk actions.

Before any registration, an organizer/static review must enumerate and hash every executable file
in the Team09 source tree and prove the manifest is complete and acyclic. Placeholder zero hashes
in template files are not source bindings and must be replaced only by the organizer's exact
first-added freeze process.

## Current evidence state

The ledgers preserve one registered parent family and one completed parent no-control trial. Its
exact result and score artifacts remain history. Pivot-01 itself has no family registration, trial
registration, evaluator result, private run, or OOS run. Its walk-forward, neighborhood, A5, and
risk files remain prospective templates until organizer/reviewer hashes exist.
