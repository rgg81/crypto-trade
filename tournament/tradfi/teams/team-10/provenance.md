# team-10 provenance — t10-ts-trend-v1

## What was read (complete list)

Tournament governance (authorized):
- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl` (empty at
  registration time), `tournament/tradfi/teams/team-10/BOOTSTRAP.md`.

Evaluator source (authorized: "the evaluator source in analysis/portfolio/tradfi/tournament/"):
- `analysis/portfolio/tradfi/tournament/engine.py` (interface, Metrics fields, cap order)
- `analysis/portfolio/tradfi/tournament/constants.py` (splits, caps, cost, seed)
- `holdout.py` was NOT read, NOT imported, NOT referenced.

Team-owned files: everything under `tournament/tradfi/teams/team-10/` only.

## Data access

Market data reached this team EXCLUSIVELY through
`tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot, boundary-
enforced at 2024-06-30) inside `out/scratch/scratch_ts_trend.py`, run from the worktree
root. Signals were built from `te.team_view(pn)` (OHLCV only — in fact only `close` is
used); the full `pn` dict was passed solely to `te.run_is` for scoring. `pn['ret_fwd']`
was never read, indexed, or used in signal construction. No other data source of any kind
was touched: no `data/`, no `data_live_tradfi/`, no funding files, no network access, no
new data ingestion.

## What was imported

Scratch analysis: `numpy`, `json`, `sys`, `pathlib` + `tournament.engine` (authorized
evaluator). The frozen spec (research_brief.md Section 9) requires only `numpy`/`pandas`
operations on the `pn` panels — no substrate modules, no file I/O, no subprocesses, no
randomness (`aux['seed']` unused).

## Prohibited-path statement

None of the following were read, grepped, imported, or referenced at any point: `data/`,
`data_live_tradfi/`, `data/funding_rates/`, `diary-portfolio-tradfi/`,
`BASELINE_TRADFI.md`, `reports-tradfi/`, `analysis/portfolio/tradfi/iter_*.py`,
`oos_forensic.py`, `splice_loader.py`, `reconcile_basis_tradfi.py`, `live_tradfi.py`,
`live_weights_tradfi.py`, `analysis/portfolio/tradfi/tournament/holdout.py`,
`tournament/tradfi/MANIFEST.sha256.json` (path referenced only implicitly by the evaluator
loader itself), `tournament/tradfi/results/`, `tournament/tradfi/critic/`, any other
team's directory.

## QE implementation notes (2026-07-17)

The QE implemented `strategy.py` verbatim from the FROZEN SPEC (research_brief.md Section
9.1) — no hidden research choices. Every constant is the QR's: K=252, skip=5, sqrt(247)
normalizer, sigma = EWM std(span=63, min_periods=42) of `close.pct_change(fill_method=None)`
floored at 0.004/day, sign transform, 1/sigma sizing, EMA span 21 (min_periods=1) after
`fillna(0.0)`. The function reads `pn['close']` only; `aux` (vix, sector_map, seed) is
imported into the signature but unused. Tickers are the panel columns at runtime (never
hard-coded). The engine owns caps / shift(1) / cost / vol-target — none is pre-applied here.

Evaluator interfaces read (authorized, `analysis/portfolio/tradfi/tournament/`): `engine.py`,
`protocol.py`, `harness.py`, `cli.py`, `leaderboard.py`. `holdout.py` was NOT read/imported.

`test_strategy.py` imports numpy/pandas + the local `strategy` module ONLY (no pytest, no
evaluator, no data path) so it passes the static-scan whitelist. Six tests: determinism,
interface shape/finiteness, aux-unused, future-bar corruption self-check (mangle every bar
strictly after each cut with the harness `*7+5` transform; weights at/before the cut
unchanged), truncated replay, and same-bar perturbation. All green.

Verification (all on the frozen IS snapshot via the evaluator):
- `pytest test_strategy.py -q` -> 6 passed.
- `cli.py team-run --team team-10` -> net IS Sharpe +0.8201 @1x / +0.7653 @2x, maxDD -23.15%,
  ann. turnover 6.40x, breadth L/S 37/11 — bit-identical to exp-016 in `out/exp_results.json`.
- `cli.py audit --team team-10` -> PASS all five checks (static-scan, determinism,
  truncated-replay, future-corruption, same-bar; 11 truncation cuts).

## Independence statement

All research decisions (family choice, parameter grids, selection rule, final spec) were
made inside this team from the authorized inputs above. No cross-team communication
occurred. No holdout information of any kind was received, inferred, or probed; the
holdout window (2024-07-01..2026-06-30) was never scored or inspected. The experiment
ledger (`experiments.jsonl`) is append-only; every material experiment line was written
BEFORE its result was read; the two vetoed-family registration lines (reg-001, reg-002)
and one selection-decision line (dec-024) are the only non-experiment lines. 21 material
experiments were used of the 40 budget.
