# Team-08 QE report

## Outcome and scope

Persistent Carry Dispersion Harvest is implemented as a fresh `build_strategy()` factory and a
stateful target-only adapter. The ambiguity gate was closed by the QR before implementation. QE
did not read another team, Git history, historical portfolio code/artifacts, reports, or public
OOS data. No snapshot, OOS, canonical performance, source-manifest, submission, or Git operation
was run. The QR-owned brief, provenance, feature lineage, and ablations were not edited.

The adapter derives every actual funding interval from adjacent strictly past events, uses the
frozen 7d/28d persistence rule, applies the closed-price quarantines, emits only on the 72h anchor,
keeps buffered sleeve state across `None` holds, and clears state on every explicit `{}`. Its
float64 SLSQP projection uses the frozen analytic constraints and symmetric paired-tail fallback.

## Frozen bindings and hashes

- Phase-0 record: `012727865acecad6ea0c3327745359820b8e45c6`
- Common freeze commit: `48df09341f02eba7a3469abd1ccda6649a4ef0ba`
- Strategy seed: `20260713`
- Data manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Common config SHA-256: `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`
- Phase-0 evaluator SHA-256: `508f56af0b4fe2636933909977cdbcfbb38e4ff821072dbf12b35bfb04d3af66`
- Strategy SHA-256: `0e6cf2ffff246c18e3e1055d2e6882248958fd30f956a01b0ed53e8457132dbe`
- Frozen config SHA-256: `dbceee82553c5e5ee68fbf98be9e8b7fda2a882bce8247235c96e21870343b98`
- QE test SHA-256: `ffd17178a1f4997eabd1b2be65caf8841988bc58fae6c63c26eda4f0904aec29`
- Team/root dependency-lock SHA-256: `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`
- Compliance SHA-256: `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`

The team `uv.lock` is byte-identical to the root lock (`cmp` exit status 0).

## Environment and commands

QE environment: Linux 6.18.33.2 WSL2 x86-64, CPython 3.13.12, NumPy 2.2.6, pandas
3.0.0, SciPy 1.17.0, pytest 9.0.2. Bytecode generation was disabled for every test command.

Test command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tournament/top40/teams/team-08/test_team_08_strategy.py
```

Static command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check tournament/top40/teams/team-08/strategy.py tournament/top40/teams/team-08/test_team_08_strategy.py
```

Observed focused-suite result: 18 passed in 5.91 seconds (6.58 seconds command wall, 16.10 user
CPU seconds, 0.77 system CPU seconds, 169740 KiB maximum RSS). Numeric discrepancy tolerance is
zero for truncation/corrupt-future/append frames and clean-process artifact hashes; the frozen
optimizer acceptance checks are bounds `1e-10` and equalities `1e-9` exactly as the QR specified.

Stable post-freeze reproduce command (not run during QE):

```bash
uv run python scripts/top40_tournament.py validate tournament/top40/teams/team-08/submission.json
```

## Test-backed compliance evidence

- `public_binance_only`: `test_source_scanner_runtime_bundle_and_neutral_imports`
- `point_in_time_top40`: `test_point_in_time_membership_uses_completed_prior_dates_only` and the
  ineligible-target assertion in
  `test_fail_closed_nonfinite_caps_duplicates_missing_prices_and_empty_outputs`
- `closed_data_only`, `corrupt_future_test`, `append_invariance_test`:
  `test_truncation_corrupt_future_and_append_invariance`
- `next_bar_execution`, `fees_and_slippage_charged`, `funding_cashflows_charged`, and
  `long_and_short_enabled`:
  `test_next_open_actual_funding_signs_costs_and_long_short_reconciliation`
- `double_cost_rerun`: `test_fresh_double_cost_run_doubles_execution_cost_rates`
- `deterministic_rerun`: `test_clean_process_target_position_return_and_manifest_hashes`

Additional tests cover exact irregular funding intervals and the strict boundary; sample-ddof
price windows; both quarantines; bounded dollar/beta-neutral weights; state buffer and clear/hold
semantics; symmetric fallback; local non-BTC versus global BTC faults; NaN/Inf, gaps, duplicates,
gross/net/symbol caps, missing marks, empty output, participation-limited fills, fees/slippage on
ordinary and forced turnover, adverse delist residual settlement, and the fixed realized sleeve
and buy/sell floors in each of two synthetic evaluation windows. Source scanning and staged
runtime import are exercised without launching an official sandbox or canonical run.

## Canonical artifact locations and limitations

The independent base and 2x-cost canonical report locations are respectively
`reports-top40/team-08/bar_returns.csv` and
`reports-top40/team-08/double_cost_bar_returns.csv`; neither was created or read by QE. The
orchestrator must produce them later from two clean official runs, along with positions, events,
targets, daily returns, manifest, and metrics. There are therefore no QE performance claims,
base/2x figures, exposure claims about the real windows, or public-OOS observations in this
report.

Known limitations: SciPy SLSQP may legitimately fail a numerically degenerate feasible set, in
which case the frozen paired-tail expansion is attempted and persistent failure explicitly
flattens. A non-BTC contract is locally quarantined until its complete required lookback is clean;
a malformed BTC benchmark flattens the scheduled book. Participation can leave target gaps,
membership exits, risk reductions, or forced delist exits unfilled; central execution records
those gaps and applies the common adverse residual settlement. The strategy deliberately makes no
funding-schedule forecast and cannot repair missing source events.
