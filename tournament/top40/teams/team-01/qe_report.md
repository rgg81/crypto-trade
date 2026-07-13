# QE report — t01-alr-002

Status: implementation-complete, preregistered, official evaluation pending.

## Frozen implementation

- Team: `team-01`
- Strategy: `asymmetric-liquidity-replenishment`
- Candidate: `t01-alr-002` (predecessor `t01-alr-001` IS-falsified flat)
- Phase-0 commit: `012727865acecad6ea0c3327745359820b8e45c6`
- Seed: `20260713`
- Parameters: `H=6`, `W=189`, `theta=1.0`, `lambda_f=0.25`
- Entrypoint: `tournament/top40/teams/team-01/strategy.py`
- Data manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Strategy SHA-256: `2325e379b732c85a4518305986b4016f4ac37d0f9f9bc1b177c33925a982876d`
- Frozen-config SHA-256: `cf2380fb498a53c8c6ce7bebf9bb1b3e65a1de806368a662d6001c749b3889d5`
- Dependency-lock SHA-256: `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`
- Trial-ledger SHA-256: `21af46822772fee868ffd1fb7eab9e32315f03f24a6ff50173fe070223233937`

`build_strategy()` returns a fresh stateless strategy. Non-Monday decisions return `None` and
therefore hold quantities; a Monday that cannot form the complete eligible book returns `{}` and
therefore requests flat. The weekly computation uses a bounded 317-bar grid, historical rolling
betas, exact 8h gap checks, strict funding endpoints, ordinal symbol-tiebroken ranks, and no
prefitted state or timestamp-to-target table. C002 removes the former imbalance-magnitude cutoff.
After splitting nonzero flow events by sign, it divides each side by its own past weighted RMS
before applying the unchanged ridge slope and normalized denominator gate.

## Environment and verification

- Platform: Linux 6.18.33.2 WSL2, x86-64, glibc 2.35
- Python: CPython 3.13.12
- NumPy: 2.2.6
- pandas: 3.0.0
- Focused verification wall time: approximately 13 seconds total across the commands below.
- Official whole-run wall/CPU time: pending the organizer-gated evaluation; no value is
  fabricated before that run.

Commands run successfully:

```text
uv run ruff check tournament/top40/teams/team-01/strategy.py tournament/top40/teams/team-01/test_team_01_strategy.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tournament/top40/teams/team-01/test_team_01_strategy.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/tournament/test_engine.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/tournament/test_runner.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/tournament/test_data.py
```

Observed results: team strategy `8 passed`; common engine `24 passed`; common runner `39 passed`;
common data `3 passed`; Ruff passed. The team tests cover fresh-factory determinism,
`None`-versus-`{}`, finite eligible-only two-sided weights, 0.80 gross/zero net/0.075 cap,
append/corrupt-future identity, exact-gap failure, duplicate-funding failure, historical-beta
endpoints, deterministic rank ties, and retention/RMS normalization of nonzero flow below the
retired 0.05 cutoff. The frozen common suites evidence next-open execution,
funding/cost accounting, the independent double-cost path, worker isolation/reproducibility, and
point-in-time membership mechanics.

Target discrepancy tolerance is zero bytes for repeated canonical artifacts. Numerical portfolio
constraints are guarded internally at `1e-12`; the central evaluator retains its own stricter
contract validation. A clean canonical rerun must reproduce target, position, return, and manifest
hashes exactly.

## Reproduction and output locations

Stable reproduce command:

```text
uv run python scripts/top40_tournament.py validate tournament/top40/teams/team-01/submission.json
```

Expected evaluator-owned output locations after the organizer run:

- Base bar returns: `reports-top40/team-01/bar_returns.csv`
- Base daily returns: `reports-top40/team-01/daily_returns.csv`
- 2x-cost bar returns: `reports-top40/team-01/double_cost_bar_returns.csv`
- 2x-cost daily returns: `reports-top40/team-01/double_cost_daily_returns.csv`

No base or 2x performance result is claimed in this report. The ledger preserves the c001
registration, records its IS-only flat-feasibility result with no public-OOS access, and then
registers c002 for the authorized public-OOS view. It contains three newline-terminated events in
that order. The QR's separate IS-only feasibility sample reported 18 nonflat targets on 23 sampled
Mondays; the QE did not repeat a market-data smoke or inspect returns/PnL during this patch.

## Known limitations

- The organizer corrected the common source-bundle validator before the replacement Phase-0
  freeze: target concepts now require field-name tokens, and a regression test proves that the
  schema-required `timestamp_utc` plus `disposition` pair is accepted. The ledger itself was not
  rewritten to work around the defect.
- The complete snapshot run has not yet established that the strategy finishes inside the
  900-second worker wall/CPU limits. Computation is bounded to the required recent history and is
  performed only at Monday 00:00 UTC decisions, but the official measurement remains pending.
- Early, gapped, illiquid, duplicate-funding, or otherwise incomplete Mondays fail flat by design;
  this can reduce realized side-exposure floors and must be checked in both evaluation windows.
- BTC must be present in the current eligible context to construct matched residuals; BTC is never
  emitted as an alpha target.
- Historical Binance quantity steps and minimum notionals are unavailable point in time, as
  disclosed by the common manifest; the evaluator consequently uses continuous quantities.
- Official REST gap responses have no upstream checksum sidecar and may be revised by Binance;
  the common snapshot freezes canonical responses and local hashes but cannot remove that source
  limitation.
