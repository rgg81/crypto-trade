# team-05 provenance — QR phase

## What I read (complete list)

- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl` (absent/empty at
  registration time), `tournament/tradfi/teams/team-05/BOOTSTRAP.md`.
- Evaluator source (authorized): `analysis/portfolio/tradfi/tournament/engine.py`,
  `analysis/portfolio/tradfi/tournament/constants.py`. NOT read: `holdout.py`.
- Approved substrate module source (metric/loader semantics only):
  `analysis/portfolio/tradfi/core_tradfi.py` (constants, `msharpe`, `turnover`, `maxdd`,
  `regime_sharpe`, `vol_target`, `panels`, `load_tradfi`).
- Directory LISTING only (no file contents): `tournament/tradfi/data_is/` symbol names,
  `analysis/portfolio/tradfi/tournament/` file names.
- My own team directory files.

## What I imported in scratch code

- `tournament.engine` (via `sys.path.insert(0, "analysis/portfolio/tradfi")`) — data access
  exclusively through `te.load_is_panels()` / `te.team_view()` / `te.run_is()`.
- `core_tradfi as ct` — approved; used for `ct.msharpe` subperiod diagnostics on evaluator
  net series only.
- `numpy`, `pandas`, stdlib `json`/`sys`/`pathlib`.

## Independence statement

- No other team's directory was read, listed, or referenced.
- No prohibited path was read: no `data/` store, no `data_live_tradfi/`, no funding data, no
  `diary-portfolio-tradfi/`, no `BASELINE_TRADFI.md`, no `reports-tradfi/`, no `iter_*.py`,
  no `oos_forensic.py` / `splice_loader.py` / `reconcile_basis_tradfi.py` / `live_tradfi.py`
  / `live_weights_tradfi.py`, no `holdout.py`, no `MANIFEST.sha256.json` contents, no
  `tournament/tradfi/results/` or `critic/`.
- No network access of any kind; no WebSearch/WebFetch; no new data ingestion.
- `ret_fwd` was never used in signal construction — signals are built from
  `team_view` panels + `aux` only; `ret_fwd` reaches only the evaluator internals.
- All reported metrics originate from `tournament.engine.run_is` output (archived JSON in
  `out/scratch/`); subperiod/beta diagnostics are computed FROM the evaluator's net series
  with the approved `ct.msharpe`/pandas and are labeled as diagnostics wherever cited.
- Experiment ledger `experiments.jsonl` is append-only; every experiment line was written
  before its result was read. 10 material experiments used at falsification of
  t05-lowvol-bab-v1; pivot requested via reg-003 (STR target vetoed by orchestrator —
  registry was not re-checked before requesting; noted as process lesson), redirected to
  the pre-approved t05-volume-liquidity-anomalies-v1 via reg-004; 11 further material
  experiments (exp-011…exp-021) to the FINAL SPEC. Total 21/40 material + 4
  registration/pivot lines.

## Pivot chain (family discipline record)

1. t05-residual-momentum-v1 — round-1 registration, vetoed on FCFS collision (no pivot spent).
2. t05-lowvol-bab-v1 — approved primary; FALSIFIED on IS per pre-registered kill (a);
   documented in research_brief.md + is_report.md Appendix A.
3. t05-shorthorizon-reversal-v1 — pivot request vetoed (another team's approved family);
   pivot not spent per orchestrator ruling.
4. t05-volume-liquidity-anomalies-v1 — ACTIVE (the one documented pivot), chosen from the
   orchestrator's pre-approved list; reg-004.

## Scratch code

- `out/scratch/scratch_explore.py` (lowvol family), `out/scratch/scratch_volume.py`
  (volume family) — both access data exclusively via `te.load_is_panels()` /
  `te.team_view()` and score exclusively via `te.run_is()`. Batch configs + full result
  JSONs archived alongside in `out/scratch/`.

---

## QE implementation phase (2026-07-17)

### What I read (QE, complete)

- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`, this team's
  `BOOTSTRAP.md`, `research_brief.md` (the FINAL SPEC is the binding normative source),
  `is_report.md`, `provenance.md`, `experiments.jsonl`, `family_registration.json`.
- Evaluator package I implement against: `analysis/portfolio/tradfi/tournament/engine.py`,
  `harness.py`, `protocol.py`, `cli.py`, `leaderboard.py`. Approved substrate: grepped signatures
  in `analysis/portfolio/tradfi/core_tradfi.py` (`CANDLES_PER_YEAR`, `vol_target`, `msharpe`,
  `panels` — semantics only, no data).
- QR reference material under `out/scratch/`: `scratch_volume.py`,
  `results_b5_amihud_divergence.json` (the exp-016 artifact I must reproduce).
- `tournament/tradfi/registry.jsonl` (confirmed the pivot approval line for
  `t05-volume-liquidity-anomalies-v1`). Directory listings only elsewhere.

### What I built / imported

- `strategy.py` — `build_raw_weights(pn, aux)`, pure/deterministic/past-only. Reads ONLY
  `pn['close']` and `pn['volume']`. Amihud ILLIQ = `(|ret| / dollar).rolling(252,
  min_periods=126).mean()`, `dollar = (close*volume)` masked `<=0`, `ret =
  close.pct_change(fill_method=None)`; long-illiquid/short-liquid centered rank weights
  `raw = rank - (N+1)/2`. No imports beyond `from __future__ import annotations` (all-pandas
  method calls). Every parameter is fixed by the FINAL SPEC — zero QE discretion; no research
  choice was made or left open (nothing bounced to the QR).
- `test_strategy.py` — imports numpy + pandas + local `strategy` only (no `pytest`, no
  evaluator, no data). Six tests: determinism, seed-invariance, future-corruption (mangle
  bars strictly after a cut → weights at/before unchanged), truncation-equivalence,
  dollar-neutral/breadth, long-illiquid direction. All self-contained on synthetic panels.

### Verification (all green)

- `pytest test_strategy.py` — 6 passed.
- `cli.py team-run --team team-05` — reproduced the exp-016 artifact bit-identically
  (@1× 0.3500406620057439, @2× 0.3423412001392022, maxDD −0.4286333053055349, turnover
  0.9151988641888337, breadth 24/24). Wrote `out/is_metrics.json` + `out/net_is.csv`.
- `cli.py audit --team team-05` — PASS all five (scan, determinism, truncated-replay,
  future-corruption, same-bar; 11 truncation cuts).

### QE independence statement

- Worked ONLY under `tournament/tradfi/teams/team-05/`. Read no prohibited path (no `data/`,
  no `data_live_tradfi/`, no funding data, no `diary-portfolio-tradfi/`, no `BASELINE_TRADFI.md`,
  no `reports-tradfi/`, no `iter_*.py`, no `oos_forensic.py`/`splice_loader.py`/
  `reconcile_basis_tradfi.py`/`live_tradfi.py`/`live_weights_tradfi.py`, no `holdout.py`, no
  `MANIFEST.sha256.json` contents, no `results/`, no `critic/`, no other team's directory).
  No holdout inspection. No network, no subprocess in team code, no wall-clock, no unseeded
  randomness. `aux['seed']` is accepted but unused. The evaluator package was read, never
  modified. Data reached the strategy only as `build_raw_weights` arguments.
