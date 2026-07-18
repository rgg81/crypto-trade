# team-06 provenance — t06-ls-ratio-contrarian-v1

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`,
  `tournament/crypto/teams/team-06/BOOTSTRAP.md`.
- Evaluator source (authorized, holdout.py EXCLUDED — never opened):
  `analysis/portfolio_tournament/engine.py`, `analysis/portfolio_tournament/constants.py`.
  A directory listing of `analysis/portfolio_tournament/` (filenames only) was taken to
  locate these two files; no other evaluator file was opened.

Data: reached EXCLUSIVELY through `portfolio_tournament.engine.load_is_panels()` from
scratch scripts inside `tournament/crypto/teams/team-06/out/scratch/` (manifest-verified
frozen IS snapshot). No file in `tournament/crypto/data_is/` was opened directly. No other
team directory, no `data/`, `pf_data/`, production analysis trees, `src/crypto_trade/`,
reports, diaries, baselines, or `MANIFEST.sha256.json` were read. No network access of any
kind (toolset has none; none attempted).

Orchestrator-shared substrate facts used: registry.jsonl approval lines (incl. team-02's
journaled OI-breadth amendment, cited as motivation to run my own coverage check first).

## What I imported

Scratch analysis only (`out/scratch/*.py`, excluded from the frozen bundle): numpy, pandas,
stdlib (sys, json), and `portfolio_tournament.engine` / `portfolio_tournament.constants`
(authorized for scratch). The future strategy.py will import numpy/pandas only, per charter.

## Experiments

`experiments.jsonl`: e01–e10, all logged via `cli.py log-experiment` BEFORE reading each
result (evaluator-stamped). 10 of 40 budget used. No hand-written timestamps.

## QE phase (finalization)

The QE implemented `strategy.py` + `test_strategy.py` from research_brief.md §10 verbatim;
team-run reproduced the frozen §10.3 expectations to float precision (harness PASS ×6,
5 team tests passed). For is_report.md the QR read, from the team's own `out/` directory
ONLY: `out/is_metrics.json` and `out/net_is.csv` (team-run artifacts). Every official
number in is_report.md comes from those artifacts; honest-window quantities are labeled
*[scratch, ledger eNN]* and trace to `experiments.jsonl`. The QR did not modify
`strategy.py` or `test_strategy.py` at any point.

## Independence statement

All research decisions (family choice, signal construction, parameter grids, selection
rule, falsifier) are my own, derived from the charter-authorized documents and the frozen
IS snapshot via the evaluator. I had no communication with any other team, read no other
team's directory, and received no holdout information. The pre-registered brief (§1–§9 of
research_brief.md) was written before any experiment ran; post-experiment edits are
confined to §10 (QE SPEC) and §11 (results addendum), as declared in the brief.
