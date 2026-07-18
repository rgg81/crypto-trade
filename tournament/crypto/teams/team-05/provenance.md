# team-05 provenance — t05-taker-flow-imbalance-v2

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-05/BOOTSTRAP.md` (own team dir only)

Authorized evaluator source (CHARTER §5; `holdout.py` NEVER opened):
- `analysis/portfolio_tournament/constants.py`
- `analysis/portfolio_tournament/engine.py`
- (directory listing of `analysis/portfolio_tournament/` — file names only)

Own team artifacts as written by me: `family_registration.json`, `research_brief.md`,
`out/scratch/flow_lab.py`, `out/scratch/results_e0*.csv`, `experiments.jsonl` entries via
`cli.py log-experiment`.

NOT read/accessed: `data/` (full store), `pf_data/`, `analysis/portfolio/`,
`analysis/portfolio_v2/`, `analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`,
any other team's directory, `tournament/crypto/critic/`, `tournament/crypto/results/`,
`tournament/crypto/_build/`, `MANIFEST.sha256.json` (verified only implicitly by the
evaluator loader), any diary/briefs/reports/baseline/iter/features paths, any URL. No
network access of any kind. Holdout never probed; no data past 2024-06-30 ever loaded
(evaluator boundary check active on every `load_is_panels()`).

## What I imported

Scratch analysis only (`out/scratch/flow_lab.py` — outside the harness scan, authorized for
scratch): `portfolio_tournament.engine`, `portfolio_tournament.constants` via
`sys.path.insert` of `analysis/`; plus `numpy`, `pandas`, `math`, `sys`.
Market data reached exclusively through `engine.load_is_panels()` (manifest-verified frozen
IS snapshot).

Team strategy code (to be written by the QE) will import NOTHING beyond
numpy/pandas/stdlib-math (+ `teamlib` if needed) per CHARTER §5 — it must NOT import the
evaluator.

## Independence statement

All mechanism reasoning, the hypothesis map (continuation vs exhaustion bands), parameter
grids, selection rule, and falsifier are my own work, derived from the FAMILY-MENU seed
(family #3), the charter's data menu, and general crypto-market knowledge. I had no sight of
any other team's code, briefs, registrations beyond the shared `registry.jsonl` outcome
lines, or results. No production-book code (`analysis/portfolio*`, `src/crypto_trade/`) was
read before or during this work. The signal uses only `taker_buy_quote_volume`,
`quote_volume` (klines) and `aux["eligibility"]` — consistent with the registered
taker-flow-imbalance family; no funding-, OI-, or ratio-panel inputs feed the signal.

## QE phase & finalization (added at finalization)

The QE implemented `strategy.py` and `test_strategy.py` from `research_brief.md` §9 alone;
the QR did not write, edit, or read either file at any point (division of labor preserved:
spec-only handoff). Team-run reproduced the QR's scratch anchors to float precision
(orchestrator-confirmed); harness 6/6 PASS. For `is_report.md` the QR additionally read,
within the own-team tree only: `out/is_metrics.json` (sole source of performance numbers
in that report, per charter §8) and `out/harness.json` (harness verdict citation).
Scratch diagnostics quoted in `is_report.md` §5–§6 are explicitly labelled with their
`experiments.jsonl` ids and `out/scratch/results_e0*.csv` provenance. No new data access,
imports, or experiments occurred during finalization; ledger unchanged at 6 entries.

## Experiment ledger integrity

Six material experiments (e01–e06), every one logged via
`uv run python analysis/portfolio_tournament/cli.py log-experiment --team team-05 --json ...`
BEFORE its result was computed/read (evaluator-stamped 2026-07-18). Budget used: 6 of 40.
No unlogged material experiments were run; e02/e05 were pre-declared diagnostics with no
selection feedback, and no rejected variant (e03 sharpening, e04 smoothing) was adopted.
