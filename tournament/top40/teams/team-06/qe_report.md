# Team-06 QE report — T06-HWDS-001

## Outcome and scope

The frozen strategy adapter implements the QR specification as a daily UTC-midnight hierarchical
weekday differential-seasonality target generator. It returns `None` at intraday 8-hour decisions,
fits only from completed past transaction candles, partially pools weekday residual means,
neutralizes beta/momentum/volatility/liquidity by ridge regression, and maps the residuals into a
deterministic market-neutral, capped inverse-volatility portfolio.

Independent synthetic QE is complete: 33 tests pass, Ruff passes, AST compilation passes, the
canonical team-tree scanner passes, and two independent child processes produce identical target,
position, return, and synthetic-manifest hashes. No public-OOS row or official OOS evaluator run
was accessed. No report outside the team-06 namespace was created.

## Freeze bindings and hashes

- Phase-0 record commit: `012727865acecad6ea0c3327745359820b8e45c6`.
- Common freeze commit: `48df09341f02eba7a3469abd1ccda6649a4ef0ba`.
- Common data manifest: `tournament/top40/data_manifest.json`.
- Data-manifest SHA-256: `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
- Strategy SHA-256: `971a7e841c3fb07f1b1fc712068fced78352a4373c82907b4e4c4968cbeaf3ec`.
- Frozen-config SHA-256: `57c074f309cc6441da5630f3e15827afc53d2c6ef15b0b7b2938bbbdb1015472`.
- Test-source SHA-256: `cf1d42a5c3ed432fcf7822b7cbcc85aef5cb4ab94ae6e35d8974192fbaff3eff`.
- Compliance SHA-256: `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`.
- Team/root `uv.lock` SHA-256: `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`;
  `cmp` confirms byte identity.
- The replacement Phase-0 record includes the shared fail-closed NaN-target correction.

## Environment

- Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64, glibc 2.35
- CPython 3.13.12
- uv 0.11.1
- NumPy 2.2.6
- pandas 3.0.0
- pytest 9.0.2
- Ruff 0.15.1
- Frozen dependency source: repository-root `uv.lock`, copied byte-for-byte
- Strategy seed: `20260713`; trial seed: `2026071306`

## Test evidence

Run from `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40`:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q \
  tournament/top40/teams/team-06/test_team_06_strategy.py
```

Result: `33 passed in 6.67s` on the final logic. The suite covers:

- truncation, corrupt-future, append, direct future-row, and chronological-cache invariance;
- exact daily rebalance versus `None` holds, fresh factory instances, and seed pinning;
- beta/weekday weighting, partial-pooling inputs, robust cross-sectional transforms, ridge-driven
  two-sided output, deterministic ranking, inverse-volatility redistribution, gross/net/name caps,
  finite outputs, empty mappings, and ineligible-name rejection;
- prior-completed-date Top-40 membership and immediately-prior-date eligibility;
- close-to-next-unseen-open execution, positive-funding long debit/short credit, long/short price
  PnL reconciliation, entry/rebalance/exit/forced-delist costs, participation limits, adverse
  disappearing-residual settlement, missing-price and duplicate-timestamp failures;
- a fresh central 2x fee/slippage evaluation, synthetic realized two-sleeve floors in two disjoint
  windows, and two clean-process target/position/return/manifest hash comparisons;
- explicit NaN, positive-Inf, and negative-Inf target rejection after the shared evaluator fix;
- strategy source/import/I/O scanning, public-Binance lineage, lock identity, and config binding.

Formatting and static checks:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  tournament/top40/teams/team-06/strategy.py \
  tournament/top40/teams/team-06/test_team_06_strategy.py
PYTHONDONTWRITEBYTECODE=1 uv run python -c \
  "import ast,pathlib; [ast.parse(pathlib.Path(p).read_text()) for p in ('tournament/top40/teams/team-06/strategy.py','tournament/top40/teams/team-06/test_team_06_strategy.py')]"
```

Results: `All checks passed!`; both files compile through `ast.parse` without bytecode output.

Canonical text-tree scanner:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python - <<'PY'
from pathlib import Path
from crypto_trade.tournament.runner import _team_tree_files
files = _team_tree_files(Path("tournament/top40/teams/team-06"))
print(len(files), sum(item.size for item in files))
PY
```

Result including this report: `11` accepted files and `451903` bytes. Rerun after replacement of
the pending Phase-0 field; the report is itself part of the scanned text tree.

## Reproduction commands and canonical locations

The exact current non-OOS QE reproduction command is the pytest command above. After the organizer
binds the replacement Phase-0 record, builds the source manifest, records the champion, freezes all
ten teams, and finalizes this team, the stable official command is:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-06/submission.json
```

Canonical evaluator report paths are reserved but intentionally not generated by this QE task:

- base bar returns: `reports-top40/team-06/bar_returns.csv`;
- 2x-cost bar returns: `reports-top40/team-06/double_cost_bar_returns.csv`;
- base daily returns: `reports-top40/team-06/daily_returns.csv`;
- 2x-cost daily returns: `reports-top40/team-06/double_cost_daily_returns.csv`.

The organizer-owned finalizer must create those artifacts in two independent official clean runs.

## Discrepancy tolerance

- Target, position, return, and manifest rerun hashes: exact byte identity; tolerance zero.
- Canonical scalar reruns: exact identity as required by the charter.
- Funding and fee/slippage formula reconciliation in focused tests: absolute tolerance `1e-12`.
- Floating portfolio cap/net checks in focused tests: absolute tolerance no larger than `1e-14`.

## Known limitations and required organizer follow-up

- Phase-0 bindings were reconciled before candidate registration and source-manifest construction.
- No real-data IS fold, public-OOS, base-cost, or 2x-cost performance evaluation was run. Therefore
  the QR falsifier (positive pooled fold Sharpes, three positive folds, positive long and short
  price-plus-funding PnL) and actual realized-sleeve floors remain unverified. Compliance booleans
  attest tested mechanics and lineage, not performance.
- No canonical report, submission, experiment ledger, source manifest, or Git state was created or
  modified. Those remain organizer-owned lifecycle steps.
- The chronological cache stores only already-exposed derived daily history. It is bit-identical to
  fresh daily refits in the tests and rebuilds on a discontinuity or re-entry; it relies on the
  evaluator contract that per-symbol bar frames are sorted and append-only.
- Binance does not provide point-in-time historical quantity/minimum-notional filters; this remains
  the common charter limitation and is not addressed in strategy code.
