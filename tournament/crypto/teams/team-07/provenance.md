# team-07 — provenance

## What was read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/teams/team-07/BOOTSTRAP.md`.
- `tournament/crypto/registry.jsonl` — attempted at registration time (did not exist yet);
  approval of `t07-vol-structure-v1` was communicated by the orchestrator dispatch.
- Evaluator source (charter §5 allows all of `analysis/portfolio_tournament/` EXCEPT
  `holdout.py`): `constants.py`, `engine.py` — read in full. `holdout.py` was NOT read,
  opened, grepped, or referenced. No other evaluator file was read.
- Orchestrator dispatch messages (registration verdict + research-phase instructions).

Market data: reached EXCLUSIVELY through
`portfolio_tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot),
called only from scratch scripts inside `tournament/crypto/teams/team-07/out/scratch/`.
No direct reads of `tournament/crypto/data_is/` files, ever.

## What was NOT touched (clean-room statement)

No reads/greps/imports of: `data/`, `pf_data/`, `data/funding_rates/`,
`data/open_interest/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
`analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, `diary-portfolio*`,
`briefs-*`, `reports-*`, `BASELINE_*.md`, any `iter_*.py`, `features_*`,
`tournament/crypto/MANIFEST.sha256.json`, `tournament/crypto/results/`,
`tournament/crypto/critic/`, `tournament/crypto/_build/`, any other team's directory.
No network access of any kind. No holdout inference, probing, or requests — the only
holdout-related fact used is its existence and date range as stated in the charter.

## Imports used in scratch code (out/scratch/ only — excluded from the frozen bundle)

`sys`, `pathlib`, `numpy`, `pandas`, `portfolio_tournament.engine`,
`portfolio_tournament.constants`. Scratch may import the evaluator per the orchestrator's
process note; the deliverable `strategy.py` (QE-owned) will import ONLY numpy/pandas (+
stdlib math if needed) and use no evaluator, no file I/O, no subprocess, no randomness.

## Research trail

- Family registered and approved: `t07-vol-structure-v1` (primary and backup-2 collided,
  FCFS; NO pivot used — all work stayed within the vol-structure family: vol level, vol
  dynamics/compression-expansion, estimator and smoothing variants).
- 12 material experiments (e01–e12), every one logged via `cli.py log-experiment`
  (evaluator-stamped) BEFORE its result was read; ledger: `experiments.jsonl`. Budget
  40, used 12.
- Pre-registration honesty: the original low-vol lottery-premium falsifier FIRED at
  e01/e02 and is documented in `research_brief.md` §A1; the reversed/dynamics branches
  were pre-registered with a STRICTER bar before being run (A1, e06 ledger entry) per the
  orchestrator's sign-flexibility mandate; the final spec cleared that bar (A2).
- Selection used pre-registered plateau rules (neighborhood means, pre-committed grid
  extensions); the final config is an interior optimum on a broad 2D plateau, not a peak.

## QE phase (finalization note)

The QE implemented `strategy.py` exactly from the frozen `research_brief.md` §7 spec and
wrote `test_strategy.py` (8 tests, all passing); `cli.py team-run` reproduced the QR's
scratch reference numbers at float precision (IS Sharpe +1.0247 @1× / +0.8260 @2×-stress)
and `cli.py audit` passed all six harness checks (`out/harness.json`). The QR did not edit
`strategy.py` or `test_strategy.py` at any point. `is_report.md` headline numbers (§1–§2)
come exclusively from `out/is_metrics.json`; auxiliary robustness numbers therein are
explicitly labeled *[scratch]* with their ledger ids. Final deliverable set at freeze:
`research_brief.md`, `strategy.py`, `test_strategy.py`, `experiments.jsonl`, `is_report.md`,
`provenance.md`, `out/` artifacts.

## Independence statement

All hypotheses, code, and decisions in this directory are the independent work of the
team-07 QR within the clean-room rules above. No cross-team communication occurred. No
production-book code, baselines, diaries, briefs, or reports of this repository were read
or referenced. Numbers quoted in `research_brief.md` amendments come from evaluator
computations (`engine.net_series`/`evaluate`) invoked by the scratch scripts listed in
`out/scratch/`; the authoritative `is_report.md` numbers will come only from
`cli.py team-run` output after the QE builds `strategy.py`.
