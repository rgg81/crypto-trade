# team-09 provenance

## What was read (complete list)
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-09/BOOTSTRAP.md` and team-09's own files only
- Evaluator source (authorized, holdout.py EXCLUDED):
  `analysis/portfolio_tournament/constants.py`, `analysis/portfolio_tournament/engine.py`,
  `analysis/portfolio_tournament/cli.py` (log-experiment handler + usage header only)
- Orchestrator messages (registration approval, redraw notice, research-phase brief with
  the two journaled data amendments: OI usable breadth ~Dec-2021+, L/S ratios ~Dec-2022+)

## What was NOT read (clean-room statement)
- NO access to `data/`, `pf_data/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
  `analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, any `diary-*`/`briefs-*`/
  `reports-*`/`BASELINE_*`/`iter_*`/`features_*`, `tournament/crypto/MANIFEST.sha256.json`,
  `tournament/crypto/results/`, `tournament/crypto/critic/`, `tournament/crypto/_build/`,
  or ANY other team's directory. No network access of any kind.

## Data access
- Market data reached EXCLUSIVELY through `portfolio_tournament.engine.load_is_panels()`
  (manifest-verified frozen IS snapshot) inside scratch scripts under
  `tournament/crypto/teams/team-09/out/scratch/` (sig.py, e01_coverage.py, e02_grid.py,
  e03_eventstudy.py, e04_oi_eventstudy.py for the falsified v2 family; sig2.py,
  e05_diag.py and inline runners for the v3 family — all evaluator-scored via
  te.net_series/te.evaluate).
- `pn['ret_fwd']` was used ONLY in scratch analysis (scoring panel, permitted in scratch);
  the v3 QE SPEC signal uses ONLY quote_volume, trades, eligibility.
- The sealed holdout was never accessed, probed, or inferred.

## Imports in scratch code
- numpy, pandas, sys/stdlib; `portfolio_tournament.engine` / `.constants` (scratch-only,
  as authorized by the orchestrator's research-phase process note).

## Experiment ledger integrity
- 10 material experiments (e01-e04 for t09-liq-squeeze-reversal-v2, falsified; e05-e10
  for t09-trade-size-composition-v3), each logged via `cli.py log-experiment` BEFORE its
  result was computed or read (evaluator-stamped). Budget used: 10/40. The e09 entry
  pre-registered its own decision bars and the (42,1) selection amendment before the run.

## QE phase note
- `strategy.py` and `test_strategy.py` were written by the team-09 QE from research_brief.md
  Section 9 (QE SPEC) exclusively; the QR did not modify them. team-run reproduced the QR's
  scratch reference to float precision; `out/is_metrics.json` is the sole source of
  is_report.md Section-1 numbers. Harness: all six checks PASS; team tests: 7 passed.
- The orchestrator's escalation ruling on the e09 momentum-overlap finding (SHIP with full
  disclosure) is implemented in is_report.md Section 3.

## Independence statement
All analysis, signal design, and conclusions are team-09's own work from the authorized
inputs above. No cross-team communication occurred. The family falsification (research
brief Section 8) is reported with the same precision as a positive result would have been.
