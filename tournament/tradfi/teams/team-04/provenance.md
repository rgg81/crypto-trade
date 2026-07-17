# team-04 provenance — QR phase (registration + design)

## What was read

- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl` (absent at
  registration time), `tournament/tradfi/teams/team-04/BOOTSTRAP.md`.
- Evaluator source (charter-authorized): `analysis/portfolio/tradfi/tournament/engine.py`,
  `constants.py` (full reads); `holdout.py` NOT read.
- Approved substrate module `analysis/portfolio/tradfi/core_tradfi.py`: metric helpers
  only (lines ~95-175: vol_target, msharpe, turnover, maxdd, regime_sharpe) plus a grep
  for constant names — read to understand the scoring convention, not for data.
- Market data: EXCLUSIVELY through `tournament.engine.load_is_panels()` /
  `te.team_view()` / `te.run_is()` inside scratch scripts in this team directory.
  No other data source of any kind.

## What was NOT read (clean-room statement)

None of: `data/` (full store), `data_live_tradfi/`, `data/funding_rates/`,
`diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`, `reports-tradfi/`,
`analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`, `splice_loader.py`,
`reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
`analysis/portfolio/tradfi/tournament/holdout.py`, `tournament/tradfi/MANIFEST.sha256.json`
(path referenced by the engine internally; file contents never opened by me),
`tournament/tradfi/results/`, `tournament/tradfi/critic/`, any other team's directory.
No WebSearch/WebFetch, no network access, no new data ingestion. No holdout probing of
any kind; the IS snapshot ends 2024-06-30 and every load is manifest-verified by the
evaluator.

## Scripts and artifacts produced (all inside teams/team-04/)

- `scratch_inspect.py` — NON-MATERIAL panel-shape inspection (name availability counts,
  VIX presence, sector list). No strategy was run and no PnL/score was read; used only to
  ground the pre-registered grid (e.g. min_side=5 feasibility, ragged-start extent).
- `scratch_explore.py` (batch A), `scratch_explore_bc.py` (B+C), `scratch_explore_d.py`
  (D), `scratch_explore_e.py` (E), `scratch_explore_f.py` / `scratch_explore_f2.py` (F)
  — experiment runners; results dumped verbatim to `out/scratch/batch*_results.json`.
  Moved under `out/scratch/` after the design phase (they import `sys` for the evaluator
  path bootstrap and must stay out of the frozen bundle).
- `family_registration.json` (incl. the vetoed first-round registration, preserved),
  `experiments.jsonl` (append-only; 2 registration lines + 24 material experiment lines,
  each appended BEFORE its result was read), `research_brief.md`, `is_report.md` (draft).

## Ledger accounting

- reg-001 (vetoed residual momentum), reg-002 (approved t04-xs-momentum-12-1-v1).
- exp-001..exp-024 = 24 material experiments (batches A 9, B 2, C 2, D 3, E 5, F 3).
  Budget: 24/40 used; 0 family pivots used. Two pre-registered hypotheses were falsified
  (skip month exp-010, and E-blend robustness exp-017/018 underperforming) and are
  reported as negative results with the same precision as positives.

## Independence statement

All research decisions were made from the charter-authorized materials listed above and
the frozen IS snapshot via the evaluator only. No contact or information flow from any
other team, the Critic, the orchestrator's sealed materials, or the incumbent production
book. The final specification was chosen on IS evidence + a-priori canonical-parameter
grounds, with selection risks flagged in the brief rather than hidden.

## QE implementation phase (Phase 2)

### What was read (QE)

- Boot sequence per CHARTER §7 / task order: `CHARTER.md`, `config.toml`, `BOOTSTRAP.md`,
  `research_brief.md` (binding spec), and the evaluator interfaces implemented against:
  `analysis/portfolio/tradfi/tournament/engine.py`, `harness.py`, `protocol.py`, `cli.py`,
  and `constants.py`. Read `core_tradfi.panels` (lines 81-98) only to confirm the OHLC
  panels share one DatetimeIndex + column set (so the emitted grid aligns with
  `conform_raw`'s `open` grid) and `vol_target` (engine-owned, never pre-applied).
- Design-phase reference `out/scratch/scratch_explore_f.py :: hysteresis_weights(252, 0,
  0.20, 0.35)` — TRANSLATED into `strategy.py`, never imported (it imports `sys` + the
  evaluator path bootstrap and stays under `out/`, excluded from the frozen bundle).

### What was NOT read (QE clean-room, unchanged)

Same prohibited set as the QR phase above: no `data/`, `data_live_tradfi/`,
`data/funding_rates/`, `diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`, `reports-tradfi/`,
`analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`, `splice_loader.py`,
`reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
`analysis/portfolio/tradfi/tournament/holdout.py`, `tournament/tradfi/MANIFEST.sha256.json`,
`tournament/tradfi/results/`, `tournament/tradfi/critic/`, or any other team's directory.
No holdout inspection, no network, no new data ingestion.

### What was implemented

- `strategy.py` — `build_raw_weights(pn, aux)`, a pure/deterministic/past-only function of
  `pn['close']` ONLY (`aux` unused). Imports: `numpy`, `pandas`, `__future__` only. The two
  lookback operators are `close.ffill()` and `.shift(252)` (both causal); the hysteresis
  membership loop's state at row t depends only on rows <= t, so truncated-replay,
  future-corruption, and same-bar equivalence hold by construction. Raw signed weights only —
  gross-normalisation, the 0.10/0.25 caps, the `.shift(1)` lag, costs, and vol-targeting are
  left to the engine. Parameters hard-coded to the brief §2 table: F=252, skip=0, q_in=0.20,
  q_stay=0.35, min-side=5.
- `test_strategy.py` — 10 self-checks, imports restricted to the audit whitelist (`numpy`,
  `pandas`, local `strategy`); no `pytest` import (plain `test_*` discovery). Covers the brief
  §5 mandatory future-corruption and determinism checks plus truncated-replay, same-bar
  causality, aux-independence, warmup-flatness, dollar-balance/breadth invariants, all on a
  self-contained synthetic panel (never touches the snapshot).

### Verification results (QE)

- `uv run pytest test_strategy.py -q` — 10 passed.
- `cli.py team-run --team team-04` — reproduces exp-023 EXACTLY: Sharpe 0.5245496867 @1x /
  0.4712512912 @2x, maxDD -0.23347 (1x) / -0.23938 (2x), total return +174.87% (1x) /
  +144.23% (2x), ann. turnover 8.4779, breadth median 12L/12S, mean gross 1.0, mean net
  ~7e-19, n_months 174, regimes (1x) bull +0.7477 / bear -1.1426 / chop +0.4687. Yearly
  Sharpe from `out/net_is.csv` matches the brief's table (2011 -0.31 … 2024 0.78).
- `cli.py audit --team team-04` — PASS all five: static-scan, determinism, truncated-replay
  (11 cuts), future-corruption, same-bar; zero violations.

### QE independence statement

`strategy.py` and `test_strategy.py` were written solely from the binding `research_brief.md`
spec and the charter-authorized evaluator/substrate source. No research choice was made by the
QE: every parameter, transform order, eligibility rule, state-initialisation, and tie-break is
fixed by the brief. No ambiguity required a bounce to the QR. No cross-team, Critic, or holdout
information was used.
