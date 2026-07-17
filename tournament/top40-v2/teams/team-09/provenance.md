# Team09 provenance and clean-room declaration

Status: **pivot-02 prospective and unregistered; both prior trial histories preserved**

## Permitted sources inspected

This draft was produced from the public Top-40 V2 charter, `config.toml`, methodology, Phase-0
policy, team playbook, public JSON schemas, neutral strategy/runner interfaces, organizer-supplied
A7/A5 identity contract, active Amendment 0006, and Team09's own ledgers, registrations, score
artifacts, and terminal results. No other V2 team, V1 strategy/result, private record, final-OOS
data, ballot, leaderboard, or unrelated evaluator output was inspected.

The shared immutable market authority is bound by `tournament/top40/data_manifest.json`, SHA-256
`077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`. Pivot-02 consumes only
the neutral worker's past-completed `bars` and point-in-time `eligible_symbols`; it does not use
funding and does not read snapshot files directly.

Both prior families ran only top-level no-control `risk_policy.json` and failed before control
activation. Their controls are permanently forbidden. Pivot-02 also begins with root no-control
bytes, byte-identical to `risk_policies/00-none.json`. A pivot-02 control remains dormant unless
the center, full preregistered neighborhood, all development gates, and all A5 gates pass; it
cannot rescue final-pivot failure.

## A7 execution, delegated A5 score, and pure-crypto authority

All future lifecycle and result-bearing commands must use
`scripts/top40_v2_tournament_runtime_preload_v7.py`, SHA-256
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`. A7 integration freeze
commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, SHA-256
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`, preloads and delegates
the exact A5 score surface pinned in `a5_score_lineage.json`; the historical A5 script is never
invoked directly.

The chain preserves Amendment 0006, canonical report SHA-256
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, policy SHA-256
`2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`, and zero violations.
Only authority-certified native crypto is in scope. A Binance perpetual listing alone is not
sufficient; stablecoins, direct/tokenized metals or commodities, equities, ETFs, indexes, FX,
premarket/TradFi contracts, and leveraged tokens are forbidden. Team code adds no ticker heuristic.

## Pivot origin and independence

The initial funding-crowd mechanism failed the bear/drawdown gates. Pivot-01 introduced a causal
broad-decline route but retained `0.90` requested gross and became insolvent on `2022-05-13`.
Pivot-02 is not a router refinement: it removes funding and regime routing and applies one slow
residual-persistence rule at every scheduled boundary. Crash-fragility exclusion, score shrink,
broad sleeves, `0.20` gross ceiling, and `0.015` cap are internal signal/portfolio construction,
not portfolio-state controls. The design is self-contained in `strategy.py` and was not copied
from another team.

## Dependency and execution declaration

Executable dependencies are Python standard library modules `dataclasses`, `math`, `numbers`, and
`collections.abc`, organizer-provided `numpy` and `pandas`, and the exact A5
`score_adapter_protocol_v5.score_boundary` hook preloaded by A7. `build_strategy()` performs no
I/O. Execution uses no network, subprocess, filesystem, credentials, environment data, repository
discovery, opaque fitted state, or unseeded randomness. The strategy returns target weights only;
the central evaluator exclusively owns fills, fees, slippage, funding cashflows, participation,
positions, equity, entry basis, delistings, and risk actions.

Before registration, organizer/static review must enumerate and hash every executable Team09 file
and prove the source manifest complete and acyclic. Template placeholders are not source bindings
and may be replaced only by the organizer's exact first-added freeze process.

## Current evidence state

The ledgers preserve two registered families and two terminal no-control trials. All corresponding
score artifacts remain immutable history. Pivot-02 has no family registration, trial registration,
evaluator result, private run, or OOS run. Its walk-forward, neighborhood, A5, and risk files are
prospective until exact organizer/reviewer bindings exist.
