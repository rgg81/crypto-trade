# Team09 provenance and clean-room declaration

Status: **prospective, unregistered, no evidence generated**

## Permitted sources inspected

This draft was produced from the public Top-40 V2 charter, `config.toml`, methodology, Phase-0
policy, team playbook, public JSON schemas, neutral strategy protocol/runner interfaces, active
Amendment 0006, and Team09's own bootstrap/empty ledgers. No other V2 team, V1 strategy/result,
private record, final-OOS data, ballot, leaderboard, report, or evaluator output was inspected.

The eventual market authority is the shared immutable Binance USD-M snapshot bound by
`tournament/top40/data_manifest.json` with SHA-256
`077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
The strategy uses only the neutral worker's past-closed `bars`, strictly past `funding`, and
point-in-time `eligible_symbols` views. It does not read snapshot files directly.

## Pure-crypto authority

All future lifecycle and result-bearing commands must use
`scripts/top40_v2_tournament_pure_crypto_v6.py`, SHA-256
`a9197dc2f83d4415f1aa4c098546e21e010cb99e754580de96c3e339cc927641`.
Amendment 0006's active integration freeze records canonical pure-crypto report SHA-256
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b` and policy SHA-256
`2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`.
Only native-crypto assets certified by that authority are in scope. A Binance perpetual listing
alone is not sufficient; stablecoins, tokenized/direct metals or commodities, equities, ETFs,
indexes, FX, premarket/TradFi contracts, and leveraged tokens are forbidden.

## Independent origin

Team09's hypothesis is a funding-crowding dislocation with relative-price confirmation and
balanced sleeves. Funding pressure is treated as a transfer-price/crowding measure, not a future
return label. The price leg waits for evidence that the crowded side is unwinding. The design is
self-contained in `strategy.py`; it was not copied from a historical or competing strategy.

## Dependency and execution declaration

Executable strategy dependencies are Python standard library modules `dataclasses`, `math`,
`numbers`, and `collections.abc`, plus organizer-provided `numpy` and `pandas`. `build_strategy()`
performs no I/O. Strategy execution uses no network, subprocess, filesystem, credentials,
environment data,
repository discovery, opaque fitted state, or unseeded randomness. The strategy returns target
weights only. The central evaluator exclusively owns fills, fees, slippage, funding cashflows,
participation, positions, equity, entry basis, delistings, and risk actions.

Before any registration, an organizer/static review must enumerate and hash every executable file
in the Team09 source tree and prove the manifest is complete and acyclic. Placeholder zero hashes
in template files are not source bindings and must be replaced only by the organizer's exact
first-added freeze process.

## Current evidence state

`families.jsonl` and `experiments.jsonl` are empty. No script, test, evaluator, lifecycle command,
registration, development run, private run, or OOS run has been executed for this draft. The
package makes no IS or OOS performance claim. The walk-forward, neighborhood, and risk artifacts
are prospective plans whose eventual hashes and central return artifacts do not yet exist.
