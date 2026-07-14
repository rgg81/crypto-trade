# Team-03 quantitative engineering report

Candidate: `t03-idtail-v1`
Entrypoint: `tournament/top40/teams/team-03/strategy.py:build_strategy`
Seed: `20260713`
Registration time: `2026-07-13T16:27:11Z`

## Implementation

The entrypoint returns a fresh `ResidualTailAsymmetryStrategy`. It implements the QR-bound tuple
`a=2`, blend `0.75`, windows `84/168/336`, `K=6`, and annualized volatility target `0.30`.
It reads only closed `close` prices and their `open_time` timestamps, the supplied executable PIT
membership, and the UTC calendar. Non-Monday decisions return `None`; a failed Monday calculation
returns `{}`. The fallback hedge remains in the factor/nuisance fit and is excluded from both alpha
sleeves. No filesystem, environment, network, subprocess, random, funding, volume, open-price, or
prefitted-state dependency exists in runtime code.

## Environment and frozen hashes

- Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64
- Python `3.13.12`
- uv `0.11.1`
- Frozen data manifest SHA-256:
  `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Common config SHA-256:
  `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`
- Strategy SHA-256:
  `3b6816adf956c7911d09918a02cc65ac5260d39e36433ced75665a16d1dd4309`
- Frozen config SHA-256:
  `26ab6e4c7624dcabacab0a347037680b13b9a3099708866cd8c3ce75a95fd980`
- Root and team lock SHA-256 (byte-identical):
  `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`

## Validation performed

```text
uv run ruff check tournament/top40/teams/team-03/strategy.py tournament/top40/teams/team-03/test_team_03_strategy.py
All checks passed!

uv run ruff format --check tournament/top40/teams/team-03/strategy.py tournament/top40/teams/team-03/test_team_03_strategy.py
2 files already formatted

uv run pytest -q tournament/top40/teams/team-03/test_team_03_strategy.py
...... [100%]
6 passed in 0.62s

uv run pytest -q tests/tournament/test_engine.py
......................... [100%]
25 passed in 1.60s

uv run pytest -q tests/tournament/test_runner.py
....................................... [100%]
39 passed in 8.83s

uv run pytest -q tests/tournament/test_data.py
... [100%]
3 passed in 0.35s

cmp -s uv.lock tournament/top40/teams/team-03/uv.lock
exit 0
```

The team causal tests cover exact 8h adjacency and gap rejection, exact 84-return momentum
completeness, closed/future truncation, corrupt-future and append invariance, deterministic fresh
instances, average-tie ranks, capped water-filling, Monday mapping versus non-Monday hold, both
factor paths, fallback-hedge sleeve exclusion, finite eligible-only signed targets, gross/net/name
caps, and algebraic factor-beta neutrality. The common engine, runner, and data suites cover
closed-context construction, point-in-time membership, next-open execution, fees and slippage,
actual-timestamp funding, two-sided accounting, independent 2x-cost evaluation, and exact fresh-run
artifact determinism. The canonical source-bundle validator also accepted the complete team tree
after generated Python caches were removed.

`compliance.json` now records all hard checks as true against that direct test evidence, the frozen
public-Binance snapshot/manifest, the restricted strategy source surface, and the completed official
research attempt described below. The official returns contain nonzero exposure in both sleeves
(maximum long exposure `0.541966585`, maximum short exposure `0.565320848`) and the trade ledger
contains both positive- and negative-quantity executions.

## Reproduction and result locations

The first organizer process was interrupted by the host restart and was closed as a counted failed
attempt. The unchanged retry `t03-idtail-v1-r1` completed at
`2026-07-13T19:20:13.738586+00:00`; its registration, reservation, result, resource use, metrics,
artifact hashes, and source-bundle hash are append-only in `experiments.jsonl` and the organizer
research journal. The successful attempt used `0.4164631597` CPU hours and `0.4164260791` wall-clock
hours. No strategy or parameter changed after the public-OOS observation.

The produced base artifacts are `reports-top40/team-03/bar_returns.csv` and
`reports-top40/team-03/daily_returns.csv`; the independent cost-stress artifacts are
`reports-top40/team-03/double_cost_bar_returns.csv` and
`reports-top40/team-03/double_cost_daily_returns.csv`. The remaining target, position, event, and
trade locations and their SHA-256 hashes are recorded in the successful result event and
`reports-top40/team-03/research-attempt-2.json`.

Target and common-runner deterministic comparisons require exact byte equality. The later cohort
finalization still must perform its charter-required two independent clean evaluator reruns; this
QE repair does not claim that finalization has already occurred.

## Known limitations

- Realized exposure and execution floors can vary by period even though the completed research
  attempt exercised both sleeves.
- Fees, slippage, actual funding, delisting, participation, base/2x reconciliation, and next-open
  fills remain evaluator-owned; the strategy does not reproduce accounting logic.
- The completed research run establishes full-history feasibility under the current official
  worker limits, but it does not guarantee identical timing on a more heavily loaded host.
- The local WSL environment is not the official fail-closed worker sandbox.
