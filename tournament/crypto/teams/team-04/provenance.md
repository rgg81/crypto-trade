# team-04 provenance — t04-ts-trend-v2

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-04/BOOTSTRAP.md` and files under `teams/team-04/` only

Authorized evaluator source (never `holdout.py`):
- `analysis/portfolio_tournament/constants.py` — splits, caps, cost model, regime tags
- `analysis/portfolio_tournament/engine.py` — order of operations (mask -> normalize_and_cap
  -> shift(1) -> costs -> funding -> vol-target), Metrics fields
- `analysis/portfolio_tournament/teamlib.py` — msharpe/maxdd/turnover helpers
- `analysis/portfolio_tournament/cli.py` — subcommand interface only (grep of argparse lines)

Market data: EXCLUSIVELY via `portfolio_tournament.engine.load_is_panels()` (manifest-verified
frozen IS snapshot), called from scratch scripts inside `teams/team-04/out/scratch/`. No raw
file under `tournament/crypto/data_is/` was opened directly; no other data source of any kind.

## What I did NOT read

No access, direct or indirect, to: `data/`, `pf_data/`, `data/funding_rates/`,
`data/open_interest/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
`analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, `diary-portfolio*`,
`briefs-*`, `reports-*`, `BASELINE_*.md`, `iter_*.py`, `features_*`,
`tournament/crypto/MANIFEST.sha256.json`, `tournament/crypto/results/`,
`tournament/crypto/critic/`, `tournament/crypto/_build/`, any other team's directory, any
URL/network resource. No holdout data, metrics, or hints of any kind were seen or probed.

## What I imported (scratch analysis only)

- `portfolio_tournament.engine`, `portfolio_tournament.constants`,
  `portfolio_tournament.teamlib` — from `out/scratch/` scripts only (out/ is excluded from
  the frozen bundle; team strategy code will import numpy/pandas/teamlib ONLY).
- numpy, pandas (stdlib: sys).

## Experiment ledger

All 12 experiments (e01-e12) were logged via `cli.py log-experiment` BEFORE their results
were computed or read; `experiments.jsonl` is evaluator-stamped. Budget used: 12 of 40.
e12 is the post-team-run anchor-gap adjudication (forensics only, no tuning).

## QE phase (post-research)

The QE implemented `research_brief.md` section 8; `cli.py team-run` produced
`out/is_metrics.json` / `out/net_is.csv` (all official numbers in `is_report.md` come from
there) and `cli.py audit` passed all six harness checks (`out/harness.json`);
`test_strategy.py` 5 passed. During adjudication of a ~1% scratch-vs-official anchor gap,
the QR read the team's own `strategy.py` and `out/is_metrics.json` (team-owned files),
identified a bool-OR dtype subtlety in the step-7 counter (sum-over-available-horizons
implemented vs mean intended), verified it bit-exactly in scratch (ledger e12), and — per
orchestrator ruling — `strategy.py` was NOT modified; the deviation is documented in the
brief's section 8 adjudication note and `is_report.md` section 3. No re-tuning followed
the team-run results; the config was frozen by ledger e10/e11 before team-run.

## Independence statement

All research decisions — family choice, signal construction (vol-normalized multi-horizon
log-price trend, clip, inverse-vol, EMA), parameter ranges, selection rule, and the final
configuration — were made solely by team-04's QR from the authorized documents and the
frozen IS snapshot reached through the evaluator. No communication with any other team; no
production-book code, diaries, briefs, or reports were read; no external data or network
access occurred. The registration collision history (registry.jsonl) exposed only other
teams' family NAMES, which is organizer-published information; no other team content was
seen. One registration redraw occurred (residual momentum -> TS trend) per FCFS rules; the
research pivot budget (1) remains UNUSED.
