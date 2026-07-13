# Team-04 QE report

## Outcome and scope

`t04-fps-001` implements the frozen Funding Receiver Aftershock handoff as a fresh
`build_strategy()` adapter. It recomputes all learned transforms from the supplied past context,
returns an explicit finite target mapping on every decision, and never computes execution, costs,
funding cashflows, PnL, or scores.

This QE pass used synthetic and infrastructure-unit data only. It did not read or evaluate public
OOS rows and did not create an experiment event, official target artifact, base result, 2x-cost
result, submission, source manifest, or report outside the team-04 namespace.

## Freeze bindings

- Phase-0 record commit: `012727865acecad6ea0c3327745359820b8e45c6`.
- Common freeze commit: `48df09341f02eba7a3469abd1ccda6649a4ef0ba`.
- Data manifest SHA-256:
  `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
- Strategy SHA-256:
  `97f89203a116cfe674a34ed1d26d43d62909e34999e199332195d1e3e26cead8`.
- Frozen-config SHA-256: `ecb6fdcd3932224b89fdd339319359dde77f5815358a95fe9608f61988dc4472`.
- Test-source SHA-256:
  `56517ab7a204763cecf6400effaaf92d77d80568d6cc44f30da9f98e4cdaa418`.
- Team lock and root lock SHA-256:
  `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`;
  `cmp -s` confirms byte identity.
- Compliance SHA-256:
  `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`.

## Environment

- Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64, glibc 2.35.
- Python `3.13.12`, uv `0.11.1`.
- NumPy `2.2.6`, pandas `3.0.0`, pytest `9.0.2`.
- Strategy seed `20260713`; trial seed namespace `2026071304`.
- No strategy filesystem, subprocess, credential, network, or evaluator imports.

## Implementation checks

The implementation independently reapplies the information boundary even when a broader direct
context is supplied. Funding is filtered to `funding_time < t`; transaction observations are
filtered to bars closed by `t`. The latest funding event alone is considered, subsecond settlement
jitter uses the evaluator's floor-hour convention, UTC 8h ceiling equality is allowed, and a newer
unfinished event suppresses an older match.

Funding surprise uses the exact 180-day, 20/60, median/MAD, floor, clip, and cross-sectional rules.
Price confirmation uses the exact 180-day UTC-slot transform, 30/90 minimums, BTC-first then
10-name fallback market, 270/120 beta, variance floor and clip, 90/60 residual scale, and
cross-sectional response score. Activation, receiver direction, strength, beta-gap pairing,
greedy disjoint ordering, two-pair minimum, five-pair maximum, and weights are literal translations
of the QR handoff. No stale signal or fitted artifact is retained.

A 40-symbol synthetic multi-year decision benchmark took approximately 0.074 seconds after the
past-window fast path was enabled. This is a diagnostic, not an official whole-run timing claim.

## Test evidence

Primary command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q \
  tournament/top40/teams/team-04/test_team_04_strategy.py
```

Result: `32 passed in 2.10s` (focused pytest wall time; surrounding process startup was under three
seconds). The suite covers:

- exact funding sign, score, response alignment, subsecond jitter, off-grid waiting, same-hour and
  all-hour funding minima, newer-event supersession, and strict exclusion at `funding_time == t`;
- exact BTC and 10-name fallback paths, beta/residual math, activation direction, deterministic
  pairing/ties, pair count, gross/net/symbol caps, missing response closure, and explicit flat maps;
- master-data truncation invariance, future corruption invariance, future append invariance, and a
  deliberately broader direct context whose future numeric rows are NaN/Inf;
- point-in-time membership from prior completed dates and rejection of ineligible targets;
- next-open fills, actual-timestamp funding with positive-rate long debit/short credit, independent
  long/short PnL reconciliation, entry/rebalance/exit fee and slippage, fresh 2x-cost execution,
  participation-limited fills, forced-delist capacity sharing/costs/residual haircut, missing marks,
  duplicate bars/targets, empty decisions, and gross/net/symbol-cap rejection;
- fail-closed NaN and Inf rejection both at strategy-mapping ingestion and in raw target frames;
- clean-process equality of target, position, return, and composite manifest SHA-256 values.

Additional checks:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  tournament/top40/teams/team-04/strategy.py \
  tournament/top40/teams/team-04/test_team_04_strategy.py

PYTHONDONTWRITEBYTECODE=1 uv run python -c \
  "from pathlib import Path; paths=[Path('tournament/top40/teams/team-04/strategy.py'),Path('tournament/top40/teams/team-04/test_team_04_strategy.py')]; [compile(p.read_text(encoding='utf-8'),str(p),'exec') for p in paths]"

cmp -s uv.lock tournament/top40/teams/team-04/uv.lock
```

Ruff and in-memory compilation pass; the dependency locks compare byte-identical. All test and
scanner commands set `PYTHONDONTWRITEBYTECODE=1`; the team tree contains no `__pycache__` directory.

## Compliance evidence

Every key in `compliance.json` is a JSON Boolean and is true only with direct evidence:

- `public_binance_only`: source-surface test rejects network/evaluator/filesystem access; strategy
  consumes only the canonical context fields documented in `feature_lineage.json`.
- `point_in_time_top40`: prior-completed-date rank test plus explicit ineligible-target rejection.
- `closed_data_only`, `corrupt_future_test`, `append_invariance_test`: the three exact invariance
  families above, including hidden-open and strict-funding-boundary cases.
- `next_bar_execution`: producing-bar versus hidden-next-open trade-event test.
- `fees_and_slippage_charged`: entry, rebalance, exit, participation, and forced-delist tests.
- `funding_cashflows_charged`: actual timestamp and independent long/short sign reconciliation.
- `long_and_short_enabled`: exact two-long/two-short mechanism output and realized synthetic sleeve
  attribution.
- `double_cost_rerun`: two independent evaluator results with doubled fee/slippage rates and
  unchanged funding-event cashflow.
- `deterministic_rerun`: fresh factory tests and clean-process target/position/return/manifest hashes.

Discrepancy tolerance is zero bytes for canonical artifacts and hashes. Numeric unit assertions use
exact equality where algebra permits and explicit floating tolerances only for evaluator arithmetic.

## Reproduction and organizer-owned outputs

The stable official command, after the organizer creates and freezes `submission.json`, is:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-04/submission.json
```

Base result location: `NOT_GENERATED_QE_TARGETED_TESTS_ONLY`.

2x-cost result location: `NOT_GENERATED_QE_TARGETED_TESTS_ONLY`.

Those outputs must come from fresh central evaluator runs; this report does not invent paths or
metrics for artifacts that do not yet exist.

## Known limitations and remaining gates

- No public OOS view or official canonical run was authorized. IS/OOS Sharpe, drawdown, regimes,
  quarterly consistency, falsifier thresholds, and paper eligibility are therefore unmeasured.
- The realized two-sleeve exposure and 1,000-USDT execution floors are verified only on synthetic
  evaluator cases here; both official evaluation windows still require central-run confirmation.
- The QR's IS-only coverage audit and nested outer/inner selection results were not rerun by QE.
- The official fail-closed sandbox and 900-second whole-run cap were not invoked. Only a bounded
  synthetic per-decision performance diagnostic was run.
- Continuous historical quantities and current-filter metadata remain the charter's disclosed
  Binance point-in-time filter limitation; the strategy does not add a workaround.
- Phase-0 bindings were reconciled before candidate registration and source-manifest construction.
