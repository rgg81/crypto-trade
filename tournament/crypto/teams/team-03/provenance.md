# team-03 — Provenance

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/teams/team-03/BOOTSTRAP.md`
- `tournament/crypto/registry.jsonl` (attempted pre-registration read: file did not exist yet;
  family approval was communicated by the orchestrator)

Evaluator source (authorized, EXCLUDING holdout.py — never opened):
- `analysis/portfolio_tournament/constants.py`
- `analysis/portfolio_tournament/engine.py`

Nothing else. In particular, NOT read/imported/grepped: `data/`, `pf_data/`,
`analysis/portfolio/`, `analysis/portfolio_v2/`, `analysis/portfolio_tournament/holdout.py`,
`src/crypto_trade/`, any `diary-*`/`briefs-*`/`reports-*`/`BASELINE_*`/`iter_*`/`features_*`,
`tournament/crypto/MANIFEST.sha256.json`, `tournament/crypto/results/`,
`tournament/crypto/critic/`, `tournament/crypto/_build/`, any other team's directory.
No network access of any kind.

## Data access

Market data reached exclusively through the evaluator:
`portfolio_tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot), called
from scratch scripts inside `tournament/crypto/teams/team-03/out/scratch/` only
(`rmlib.py` — orchestrator-authorized location for evaluator imports). Scoring used the
evaluator's own `conform_raw` / `net_series` / `evaluate` — no bespoke metric code.

## What I imported

Scratch analysis (`out/scratch/rmlib.py`): numpy, pandas, `portfolio_tournament.engine`,
`portfolio_tournament.constants`. The QE SPEC for `strategy.py` (research_brief.md §10)
requires numpy + pandas only and does NOT import the evaluator.

## Experiments

10 material experiments (e01–e10), each logged via
`cli.py log-experiment --team team-03` BEFORE its result was computed/read; ledger:
`tournament/crypto/teams/team-03/experiments.jsonl` (evaluator-stamped). Budget used 10/40.

## Independence statement

The signal design (BTC/market-beta-residual cross-sectional momentum, EW eligible-mean
factor, rolling-cov beta, t-stat formation score, centered-rank weights, EMA smoothing) was
derived from the family registration and public quantitative-finance concepts (Blitz-style
residual momentum) applied to crypto-native reasoning (narrative-rotation persistence,
retail herding). I had no visibility into any other team's work, the production book's code,
the holdout window, or any data beyond the frozen IS snapshot. All parameter choices follow
the selection rule pre-registered in `research_brief.md` §7 BEFORE the corresponding sweeps
were run; deviations: none (two cases where a non-selected variant scored higher — g=0,
L=168 — are disclosed in §9 and were NOT adopted, per the pre-registered rules).

## QE phase (added at finalization)

The QE implemented `strategy.py` and `test_strategy.py` strictly from research_brief.md §10
(the QE SPEC), consuming only that spec, the charter-authorized documents, and the evaluator
interface; the QE performed no research and changed no parameters. `cli.py team-run` output
(`out/is_metrics.json`, `out/net_is.csv`) reproduced the QR's scratch headline exactly
(Sharpe 1.3040 @1× / 0.9273 @2×), `cli.py audit` passed all six harness checks, and
`test_strategy.py` passed 9/9. One informational harness note (widening shifts the rank
centering mean by ≤ 1 ULP — numpy summation-order noise, junk-value-independent, junk
columns exactly flat) required no spec or code change. For `is_report.md` the QR read
`out/is_metrics.json` (team-run artifact) — the only additional file read in this phase.
The QR did not modify `strategy.py` or `test_strategy.py` at any point.

## Independence statement (reaffirmed at finalization)

The statement above stands for the full engagement, QE phase included: no other team's work,
no production-book code, no holdout data, no network, no data beyond the frozen IS snapshot.

## Timeline integrity

`research_brief.md` sections 1–8 (mechanism, regime expectations, falsifiers F1–F4,
parameter grid, selection rule) were written and saved BEFORE experiment e01 was logged.
Sections 9–10 were filled afterwards by applying §7 verbatim. The final QE-SPEC code was
verified bit-identical to the scratch implementation that produced the e09 numbers, and
causal under a future-corruption spot check (documented in §10 validation targets).
