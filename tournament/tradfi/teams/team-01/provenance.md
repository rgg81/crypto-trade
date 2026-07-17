# team-01 provenance — t01-residual-momentum-v1 (QR phase)

## What was read (complete list)

Tournament documents (authorized):
- `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
  `tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl`,
  `tournament/tradfi/teams/team-01/BOOTSTRAP.md`, `.claude/agents/tradfi-tournament-qr.md`.

Evaluator / substrate source (authorized; `holdout.py` NOT opened):
- `analysis/portfolio/tradfi/tournament/engine.py`
- `analysis/portfolio/tradfi/tournament/constants.py`
- `analysis/portfolio/tradfi/core_tradfi.py` — metric helpers only (lines ~20–165:
  COST_SIDE, vol_target, msharpe, turnover, maxdd, `_REGIMES`, regime_sharpe)
- `analysis/portfolio/tradfi/neutralize.py` (approved substrate, `dollar_neutralize` used)

Market data: ONLY via `tournament.engine.load_is_panels()` (manifest-verified frozen IS
snapshot, 2010-01-04 → 2024-06-28), inside scratch scripts in this directory.

## What was NOT touched (clean-room statement)

No reads/greps/imports of: `data/`, `data_live_tradfi/`, `data/funding_rates/`,
`diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`, `reports-tradfi/`,
`analysis/portfolio/tradfi/iter_*.py`, `oos_forensic.py`, `splice_loader.py`,
`reconcile_basis_tradfi.py`, `live_tradfi.py`, `live_weights_tradfi.py`,
`analysis/portfolio/tradfi/tournament/holdout.py`, `tournament/tradfi/MANIFEST.sha256.json`
(path passed to the loader as a constant; contents never read), `tournament/tradfi/results/`,
`tournament/tradfi/critic/`, any other team's directory. No network access of any kind.
No holdout bar (post 2024-06-30) was seen; the loader's ISBoundaryError guard was active on
every load. `pn['ret_fwd']` was never used in signal construction — it stays inside
`te.run_is` (scoring only).

## What was imported by scratch code

`numpy`, `pandas`, stdlib (`sys`, `json`, `pathlib`), `tournament.engine`,
`neutralize.dollar_neutralize`. Nothing else. `strategy.py` (QE-owned) is specified to
import only numpy/pandas/stdlib-math/`neutralize`.

## Independence statement

All design decisions were made from the frozen IS snapshot via the evaluator, the
authorized tournament documents, and public-domain finance literature knowledge
(residual/idiosyncratic momentum, e.g. Blitz–Huij–Martens-style constructions), with no
access to any other team's work, the incumbent production book's research, or any data
past 2024-06-30. Ledger discipline: every experiments.jsonl line was appended BEFORE its
batch result was read; judgment calls that deviated from or refined pre-registered
adoption rules are recorded as `decision_note` fields in the immediately following line.

## Files produced (this directory only)

`family_registration.json`, `experiments.jsonl`, `scratch_common.py`, `scratch_00_eda.py`,
`scratch_run.py`, `out/exp-*.json` results, `research_brief.md`, `is_report.md` (draft),
`provenance.md`. `strategy.py` deliberately NOT written — QE-owned.

---

# team-01 provenance — QE (implementation) phase

## What the QE read (clean-room, identical constraints to QR)

Boot sequence only: `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
`teams/team-01/BOOTSTRAP.md`, `teams/team-01/research_brief.md` (the binding spec), and the
QR's reference material `scratch_common.py` / `scratch_run.py` / `scratch_00_eda.py` /
`out/exp-*.json`. Evaluator interfaces implemented against (authorized): `tournament/engine.py`,
`tournament/harness.py`, `tournament/protocol.py`, `tournament/cli.py`, `tournament/leaderboard.py`,
`tournament/constants.py`, `neutralize.py`. Market data reached ONLY via `cli.py team-run`
/ `cli.py audit` (evaluator, manifest-verified frozen IS snapshot). NONE of the prohibited
paths (charter §5 denylist, `holdout.py`, other teams) were read, imported, or grepped. No
network, no holdout bars.

## What the QE built

- `strategy.py` — `build_raw_weights(pn, aux)`, a pure/deterministic/past-only implementation
  of research_brief §3 with every parameter frozen (beta/gamma win 63, form 252, skip 21,
  L=231, min_periods 208, blend 50/50 IR+sum pct-ranks, dollar-neutral rank book, EMA
  halflife 10). Imports: `numpy`, `pandas`, `neutralize.dollar_neutralize` (charter-approved).
  Reads ONLY `pn['close']` and `aux['sector_map']`; `aux['vix']`/`aux['seed']` unused (no
  randomness). It was verified BIT-IDENTICAL (`pd.testing.assert_frame_equal(check_exact=True)`,
  3646×65 grid) to `scratch_common.build()` with the exp-013 `CHOSEN` config; team-run
  reproduces `out/exp-013_results.json` to full float64 precision.
- `test_strategy.py` — six leak-proofing self-checks on a deterministic synthetic panel
  (450 bars × 12 names × 3 sectors, past the ~294-bar burn-in): determinism, future-bar
  corruption (mangle bars after a cut → weights ≤ cut unchanged), truncated-replay,
  same-bar perturbation, close-only dependence, and per-row dollar-neutrality. Imports only
  `numpy`/`pandas`/local `strategy` (scan-clean).
- `pytest.ini` — local test config (NOT a `.py`; excluded from the audit static scan and the
  freeze SHA-bind). Sets `pythonpath` to `analysis/portfolio/tradfi` so standalone
  `uv run pytest` can resolve the `neutralize` substrate import (the evaluator supplies that
  path in the tournament runtime; `strategy.py` may not add it because the scan bans `import sys`).

## Bundle hygiene (root-cause fix, not a route-around)

The QR's research scaffolding (`scratch_common.py`, `scratch_run.py`, `scratch_00_eda.py`)
imports `sys`/`json`/`pathlib`/`tournament` and reads the frozen snapshot offline — legitimate
for research but not leak-safe submission code, so the audit static scan (which scans every
`.py` under the team dir) flagged them. They were relocated verbatim into `out/scratch/`
(the `out/` subtree is excluded from BOTH the static scan and the freeze SHA-bind), preserving
them as reference while leaving the frozen submission bundle = `strategy.py` + `test_strategy.py`
only. No scan rule was weakened and no evaluator/shared file was touched.

## Canonical results (from `cli.py team-run --team team-01`, `out/is_metrics.json`)

Net IS Sharpe (monthly √12): **+0.4546 @1×**, **+0.4183 @2×** (Δ = 0.0363). maxDD −28.34%
(1×) / −28.79% (2×). Ann. gross turnover 4.034×. 174 months. Median names long/short 24/24
(~5× the breadth floor). Mean gross 1.0, mean net 5.3e-17. Regime Sharpe (1×): bull +0.444,
bear −0.240, chop +0.732. Audit (`cli.py audit --team team-01`): PASS on all five checks
(scan, determinism, truncated-replay×11, future-corruption, same-bar). `pytest`: 6/6 green.

## QE independence statement

The QE implemented the QR's frozen specification exactly and made NO research choices — no
lookback, transform-order, missing-data-rule, or parameter was invented or altered; every
value traces to research_brief §2/§3. The only judgment calls were mechanical bundle hygiene
(relocating non-submission scratch scripts to `out/scratch/`) and standalone-test plumbing
(`pytest.ini` pythonpath), neither of which changes any number. No other team's work, the
incumbent book, or any holdout/prohibited path was accessed.
