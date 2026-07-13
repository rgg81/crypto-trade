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
6 passed in 0.63s

cmp -s uv.lock tournament/top40/teams/team-03/uv.lock
exit 0
```

The synthetic causal tests cover exact 8h adjacency and gap rejection, exact 84-return momentum
completeness, closed/future truncation, corrupt-future and append invariance, deterministic fresh
instances, average-tie ranks, capped water-filling, Monday mapping versus non-Monday hold, both
factor paths, fallback-hedge sleeve exclusion, finite eligible-only signed targets, gross/net/name
caps, and algebraic factor-beta neutrality. The canonical source-bundle validator also accepted
the complete team tree after generated Python caches were removed.

`compliance.json` marks only closed-data, append-invariance, and corrupt-future checks true. All
evaluator-owned or realized-result checks remain false pending an organizer run.

## Reproduction and result locations

The preregistered organizer-gated command is:

```bash
uv run python scripts/top40_tournament.py run-team team-03 --candidate-id t03-idtail-v1
```

The organizer has not run it yet. Consequently no base or 2x-cost files exist under
`reports-top40/team-03/`, and this QE did not inspect public OOS. The organizer must append the
canonical result event to `experiments.jsonl`; the team ledger intentionally contains only its one
registered event.

Local deterministic target comparisons require exact equality. No tolerance is claimed yet for
canonical positions, returns, or manifests because the two independent clean evaluator reruns have
not occurred.

## Known limitations

- Synthetic contexts do not establish realized long/short exposure or execution-notional floors.
- Fees, slippage, actual funding, delisting, participation, base/2x reconciliation, and next-open
  fills are evaluator-owned and were not re-evaluated locally.
- Full-history runtime under the official 900-second sandbox remains to be measured by the
  organizer. The focused synthetic suite completed well inside that limit.
- The local WSL environment is not the official fail-closed worker sandbox.
