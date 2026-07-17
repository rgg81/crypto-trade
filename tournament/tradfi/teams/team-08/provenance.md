# team-08 — Provenance

## What was read (complete list)

Tournament governance (authorized):
- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl`
- `tournament/tradfi/teams/team-08/BOOTSTRAP.md`
- `.claude/agents/tradfi-tournament-qr.md` (role definition)

Evaluator source (authorized by charter §5; `holdout.py` NEVER opened):
- `analysis/portfolio/tradfi/tournament/engine.py`
- `analysis/portfolio/tradfi/tournament/constants.py`
- `analysis/portfolio/tradfi/tournament/protocol.py`
- `analysis/portfolio/tradfi/core_tradfi.py` (approved substrate; metric/panel helper
  sections: `panels`/`ret_fwd`, `msharpe`, `vol_target`, `turnover`, `maxdd`,
  `regime_sharpe`, cost/vol constants)

Market data: reached EXCLUSIVELY through `tournament.engine.load_is_panels()` /
`team_view()` inside `out/scratch/scratch_reversal.py`, run from the worktree root. No other
data source of any kind was touched.

## What was NOT read (prohibited, confirmed untouched)

`data/` (full store), `data_live_tradfi/`, `data/funding_rates/`,
`diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`, `reports-tradfi/`,
`analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`, `splice_loader.py`,
`reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
`analysis/portfolio/tradfi/tournament/holdout.py`,
`tournament/tradfi/MANIFEST.sha256.json` (hashed only internally by the evaluator),
`tournament/tradfi/results/`, `tournament/tradfi/critic/`, every other team's directory.
No WebSearch/WebFetch, no network access, no subprocesses in analysis code.

## Imports used in scratch analysis

`tournament.engine`, `tournament.constants` (evaluator), `numpy`, `pandas`, `json`, `sys`,
`pathlib` (stdlib). `aux['sector_map']`, `aux['vix']`, `aux['seed']` were NEVER used in any
signal (family fidelity: own-name reversal only; deterministic, no randomness).
`pn['ret_fwd']` was never accessed by signal code — signals are built from
`te.team_view(pn)` (open/high/low/close/volume) only; `pn` is passed only to the evaluator's
own `run_is`/`evaluate`.

## Artifacts produced

- `research_brief.md` — pre-registration (frozen before exp-003) + falsification verdict
- `experiments.jsonl` — append-only: 2 registration lines, 8 material experiments
  (exp-003..exp-010), 1 verdict line; every experiment line written BEFORE its result was read
- `out/exp003..exp010*.json` — verbatim evaluator (`run_is`/`evaluate`) metric dumps
- `out/base_cfg.json` — frozen base-config handoffs between pre-registered experiments
- `out/scratch/scratch_reversal.py` — the only analysis script (moved out of the bundle root)
- `is_report.md` — negative-result report; no submission, hence no `out/is_metrics.json`

## Independence statement

All research decisions, code, and conclusions in this directory are the work of the team-08
QR alone, based solely on the authorized reads listed above and the frozen IS snapshot via
the evaluator. No communication with any other team occurred; no other team's directory,
the critic tree, results, or any holdout-bearing path was read; no external/network data
entered the analysis. The registry was read only for family-approval status. The family was
researched to its pre-registered falsifier and reported honestly as a negative result.
