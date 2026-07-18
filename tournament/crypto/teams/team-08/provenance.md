# team-08 — provenance

## What I read (authorized paths only)

- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-08/` (my own tree: BOOTSTRAP.md, my own deliverables)
- Evaluator source (authorized, holdout.py EXCLUDED — never opened):
  `analysis/portfolio_tournament/constants.py`, `engine.py`, `cli.py`, `protocol.py`,
  `snapshot.py`, `teamlib.py`
- Orchestrator messages (registration, redraw, research-phase dispatch, pivot grant/approval).

## What I did NOT read

- `data/` (full store), `pf_data/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
  `analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, any other team's
  directory, `tournament/crypto/critic/`, `tournament/crypto/results/`,
  `tournament/crypto/_build/`, `MANIFEST.sha256.json`, any diary/briefs/reports/baseline/
  iteration files of the production tracks. No network access of any kind.

## Data access

Market data reached exclusively through the evaluator:
`portfolio_tournament.engine.load_is_panels()` from scratch scripts under
`tournament/crypto/teams/team-08/out/scratch/` (out/ is harness-excluded). The frozen IS
snapshot was never opened directly; `ret_fwd` was used only inside the evaluator's own
`net_series` scoring path, never as a signal input.

## What I imported (scratch code)

numpy, pandas, stdlib (argparse/json/sys/pathlib), and `portfolio_tournament.{engine,constants}`
— scratch-only, permitted (out/scratch is harness-excluded).

## QE phase

The QE implemented `strategy.py` + `test_strategy.py` exactly from `research_brief.md` §A8
(imports: numpy/pandas only in team code), ran `team-run` (metrics land on the §A8 scratch
cross-check row) and `audit` (harness PASS 6/6; tests 7 passed). The QR did not modify
`strategy.py` or `test_strategy.py` at any point. `is_report.md` was written by the QR with
board numbers exclusively from `out/is_metrics.json`; active-window/V2 numbers are labeled
SCRATCH with ledger ids (e04–e08) per the orchestrator's finalization instruction.

## Experiments

`experiments.jsonl` entries e01–e08, each logged via `cli.py log-experiment`
(evaluator-stamped) BEFORE its result was computed or read. 8 of 40 budget used.
- e01–e03: family 1 (`t08-short-horizon-reversal-v2`) — falsifier F1 fired; its pre-registered
  smoothing/plateau stages were NOT run (smoothing cannot alter the sign of a gross edge).
- e04–e08: family 2 (`t08-oi-price-confirmation-v3`, approved pivot) — census/artifact scan,
  Stage A structure, Stage B plateau, Stage C ΔOI window, Stage D integrity + verdict.
  Falsifier did not fire; selected config S1γ0 / σ-scaled / L=18 / M=18 / H=2 per the
  pre-registered selection rule (research_brief.md §A6–A8).

## Independence statement

All research decisions here derive from: the charter/menu/config, the evaluator source
listed above, the frozen IS snapshot via the evaluator, and general public-domain knowledge
of crypto perp microstructure. No production-book code, data, diaries, or results were read
or referenced. No other team's work was seen. The negative result reported in
`research_brief.md` §6 is stated with the same precision as a positive one would have been.
