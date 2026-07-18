# team-01 provenance — t01-funding-carry-xs-v1

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`
- `tournament/crypto/config.toml`
- `tournament/crypto/FAMILY-MENU.md`
- `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-01/BOOTSTRAP.md`
- My own team tree (`tournament/crypto/teams/team-01/`), which I authored.

Evaluator source (authorized, EXCLUDING `holdout.py`, which I did not open):
- `analysis/portfolio_tournament/engine.py`
- `analysis/portfolio_tournament/constants.py`
- Directory listing of `analysis/portfolio_tournament/` (file names only).

I did NOT read: `data/`, `pf_data/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
`analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, any `diary-*`/`briefs-*`/
`reports-*`/`BASELINE_*`/`iter_*`/`features_*` path, `tournament/crypto/MANIFEST.sha256.json`,
`tournament/crypto/results/`, `tournament/crypto/critic/`, `tournament/crypto/_build/`, or any
other team's directory. No network access of any kind was attempted (no such tools exist in
my toolset).

## How market data was accessed

Exclusively through the evaluator inside my team scratch dir:
`portfolio_tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot), and
scoring exclusively through `engine.conform_raw` / `engine.net_series` / `engine.evaluate`,
called from `tournament/crypto/teams/team-01/out/scratch/carrylib.py` and inline scratch
scripts. No direct file reads of `tournament/crypto/data_is/`. The sealed holdout was never
probed, and no data past 2024-06-30 was requested (the loader's boundary check also enforces
this mechanically).

## What I imported in scratch code

`portfolio_tournament.engine`, `portfolio_tournament.constants` (scratch-only, permitted in
`out/scratch/`), numpy, pandas, stdlib (sys, json, warnings). The strategy specification
handed to the QE imports ONLY numpy + pandas and does not import the evaluator, read files,
or use the network.

## Experiment ledger

All 12 material experiments (e01–e12) were logged via
`cli.py log-experiment --team team-01` BEFORE reading their results; the evaluator-stamped
ledger is `tournament/crypto/teams/team-01/experiments.jsonl`. Budget used: 12/40. No
experiments were run un-ledgered; the only un-ledgered computations were re-prints of
already-ledgered configurations for tabulation.

## QE phase & finalization (added at freeze time)

- The QE implemented the QE SPEC from `research_brief.md` verbatim in `strategy.py` +
  `test_strategy.py` (8 team tests passing). I (QR) did not modify either file at any point.
- During harness bring-up the QE's BLOCK report surfaced a harness/engine inconsistency in
  funding-jitter variant construction; the orchestrator resolved it as **journaled evaluator
  amendment #1** (variant construction only — no scoring change; applied uniformly to all
  teams). Our team-run cross-check targets reproduced to float precision before and this is
  reflected in the final artifacts.
- Final harness state: all six checks pass (`out/harness.json`, zero violations).
- For `is_report.md` I read exactly two additional files, both team-owned team-run/audit
  artifacts: `tournament/crypto/teams/team-01/out/is_metrics.json` (sole source of every
  team-run metric quoted) and `tournament/crypto/teams/team-01/out/harness.json`. Scratch-
  provenance numbers in the report are labeled as such and cite their ledgered experiment
  ids (e02, e03, e06, e10, e11).
- No additional data access, no new experiments (ledger closed at 12/40), no network, no
  prohibited paths, holdout never probed.

## Independence statement

The mechanism (cross-sectional funding carry) was chosen from the public FAMILY-MENU on
economic reasoning stated in `family_registration.json` BEFORE any data access. I have not
read the production book's code, any other team's work, or any prohibited path. All design
decisions (smoothing halflife, rank transform, inverse-vol sizing, weight EWM, masks) were
derived solely from the pre-registered parameter plan in `research_brief.md` plus the
ledgered IS experiments above. Numbers quoted in the brief come from the evaluator's own
scoring functions; canonical `is_report.md` numbers will come only from `team-run` output.
