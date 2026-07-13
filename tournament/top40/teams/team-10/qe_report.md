# Team-10 QE report — T10-PLMP-270-540-C14

## Disposition

Implemented the QR's unchanged fixed primary, **Perpetual Listing-Maturation Premium**, as
candidate `T10-PLMP-270-540-C14`. The QR did not accept the candidate's validation evidence:
`qr_accepted=false`. The organizer advanced it under the tournament's anti-performance-veto rule
after the fixed-primary nested gate failed. This is an honest tournament submission, not a claim
that the strategy is ready for capital.

The fixed mapping is long the five oldest mature contracts and short the five youngest contracts,
at `+0.08/-0.08` each, on a 14-day schedule anchored at the common IS start. Young means a
non-left-censored age from 30 through 270 days inclusive. Mature means at least 540 days old or
left-censored by an exact first transaction-bar open at the snapshot start. A scheduled call with
fewer than five names in either disjoint pool returns `{}`; every off-schedule call returns `None`.

The implementation reads only past transaction-bar `open_time` and the organizer-supplied
`eligible_symbols`. It recomputes the first observable open from the streamed past context on every
scheduled call and stores no timestamp lookup. Price, return, volume, funding, marks, membership
rank, fills, positions, PnL, and scores are not alpha inputs. Current point-in-time membership and
decision-open fillability are supplied centrally; the current open price is hidden.

## Fixed evidence and hashes

- Frozen data-manifest SHA-256:
  `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`
- Strategy SHA-256:
  `212c1bda50ac7a3884792554da1bba8b85c51bc7f9535c5950466a1c007ae837`
- Frozen-config SHA-256:
  `4ca63591a82740e7df660eae8f0529bb256357b1c224723241206cc5b1a67829`
- Test-source SHA-256:
  `6c66a99112e27b51bae7b3cf9ab041a165f5050474b8701af39fc9a6b6a96f64`
- Dependency-lock SHA-256:
  `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`
- Compliance-evidence SHA-256:
  `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`
- Strategy seed: `20260713`; no stochastic operation is used.
- Dependency lock: byte-identical to the root `uv.lock` (`cmp` verified).

The organizer bound final Phase-0 record `012727865acecad6ea0c3327745359820b8e45c6`, common
freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`, data manifest, and evaluator hash before
registration or public-OOS access. The source-manifest hash, team freeze commit, and canonical
output manifest are added only after the result ledger closes; no team file embeds its own future
commit SHA.

## Environment and commands

- Platform: Linux 6.18.33.2 WSL2 x86-64, glibc 2.35
- Python: 3.13.12
- NumPy: 2.2.6
- pandas: 3.0.0
- pytest: 9.0.2
- ruff: 0.15.1

Executed from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check \
  tournament/top40/teams/team-10/strategy.py \
  tournament/top40/teams/team-10/test_team_10_strategy.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/pytest -q \
  tournament/top40/teams/team-10/test_team_10_strategy.py
```

Result: `41 passed` in 1.90 seconds; ruff reported no errors. The test suite itself runs two fresh
Python processes and requires identical SHA-256 values for target bytes, positions, base returns,
2x-cost returns, and the complete source-bundle fingerprint. Exact discrepancy tolerance is zero.

After the organizer finalizes the frozen cohort, the stable full reproduction command is:

```bash
uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-10/submission.json
```

## Test coverage

The suite verifies all nine preregistered `{180,270,360}` young-cap by `{7,14,28}` cadence cells
remain representable while the factory binds only the preselected `270/14` primary. It covers the
exact anchor, off-schedule hold, scheduled insufficient-pool flat, inclusive 30/270/540-day
boundaries, exact snapshot-start left censoring, mature-descending and young-ascending age order,
lexicographic ties, five-by-five signs, gross/net/symbol caps, deterministic row-order behavior,
and rejection of a different runtime seed.

Leakage tests compare truncated, future-appended, and future-corrupted contexts. An unclosed
decision-time bar cannot create a launch observation. A separate test corrupts every historical
price/volume field and the funding table while preserving open times, proving those fields do not
affect targets. Missing, naive, or future-only lifecycle histories are unavailable rather than
imputed. Extra noneligible histories cannot enter a target.

Synthetic common-evaluator tests—not team accounting—verify next-open execution, actual positive
funding charging longs and crediting shorts, independent 2x fee/slippage replay, long/short price
signs, participation-limited fills and carried gaps, entry/rebalance/exit costs, participation
sharing on a disappearing contract, the adverse residual settlement, risk-cap rejection,
non-finite and ineligible-target rejection, duplicate-bar rejection, and empty-grid behavior. The
canonical text-tree scanner also accepts the full Team-10 source tree.

## QR diagnostic handoff (not canonical tournament output)

The QR reports full-IS net Sharpe `0.3670250557` and 2x-cost Sharpe `0.3262076300` for the fixed
primary. The preregistered nine-cell basin had six positive cells at each cost stress, but this was
diagnostic only and no neighbor replaced the primary. Reverse and all-age controls were negative
(`-0.579752` and `-0.047061` base Sharpe). The fixed primary failed its six-fold nested stability
gate: three of six base folds were positive, median base Sharpe was `-0.0643973865`, and median
2x-cost Sharpe was `-0.1254654572`. Public OOS accesses remain zero.

These values are preserved because the failed gate materially weakens generalization confidence.
They are not populated into `submission.json`; only the organizer's later canonical evaluator may
write tournament metrics.

## Canonical report locations

The organizer-owned clean run will publish the base outputs under `reports-top40/team-10/`,
including `bar_returns.csv`, `daily_returns.csv`, `positions.parquet`, `events.parquet`, and
`trades.csv`. The independent stress run will publish `double_cost_bar_returns.csv` and
`double_cost_daily_returns.csv`. Those outputs do not exist yet and were not fabricated by QE.

## Known limitations

- The first archived valid transaction-bar open is a deterministic proxy for lifecycle origin,
  not guaranteed proof of the venue's true listing instant. An archive gap can make a launch look
  later and younger. No repair or external listing source is allowed.
- Contracts already visible at the snapshot boundary have unknown earlier age. The explicit rule
  treats them as mature; that structural assumption can dominate the mature tail early in IS.
- The fixed primary failed its nested stability gate and its aggregate IS Sharpe is modest. The
  anti-veto advancement preserves a valid competitor but does not erase that evidence.
- Fourteen-day targets reduce routine turnover, but central membership exits, delist handling,
  fill limits, and exposure reductions can trade between scheduled calls. Realized holdings can
  therefore differ from requested weights.
- Funding is fully charged by the common evaluator but is not forecast or optimized. A lifecycle
  sleeve can inherit adverse funding regimes.
- The historical evaluator uses continuous quantities because Binance lacks complete
  point-in-time filter history. Forward paper must apply then-current step, tick, quantity, and
  minimum-notional rules.
- Public OOS is visible by tournament design but remains untouched for this candidate at handoff.
  It is not sealed evidence; prospective forward paper is the first genuinely untouched period.
