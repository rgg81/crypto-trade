# team-03 provenance — QR design phase

## What was read (complete list)

Tournament governance: `tournament/tradfi/CHARTER.md`, `tournament/tradfi/config.toml`,
`tournament/tradfi/FAMILY-MENU.md`, `tournament/tradfi/registry.jsonl`,
`tournament/tradfi/teams/team-03/BOOTSTRAP.md`, `.claude/agents/tradfi-tournament-qr.md`
(role definition).

Evaluator source (charter-authorized): `analysis/portfolio/tradfi/tournament/engine.py`,
`analysis/portfolio/tradfi/tournament/constants.py`. NOT read: `holdout.py` (prohibited),
`snapshot.py`, `harness.py`, `cli.py`, `leaderboard.py`, `protocol.py`.

Approved substrate modules (charter §5): `analysis/portfolio/tradfi/core_tradfi.py`
(read for `ret_fwd` convention, metric estimators, vol-target mechanics, regime tags),
`analysis/portfolio/tradfi/universe_tradfi.py` (SECTOR_MAP grep + size/sector counts only).

## Data access

Market data was touched EXCLUSIVELY through `tournament.engine.load_is_panels()` /
`team_view()` / `run_is()` from scratch scripts inside this team directory
(`scratch_lib.py`, `scratch_run.py`), i.e. the manifest-verified frozen IS snapshot,
boundary-enforced at 2024-06-30. `pn['ret_fwd']` was never used in signal construction —
signals consume `team_view` close prices plus `aux['vix']` / `aux['sector_map']` only
(volume, open, high, low unused in the final spec; high/low were used transiently by the
rejected exp-007 exhaustion variant through the same team_view interface).

No files under `data/`, `data_live_tradfi/`, `reports-tradfi/`, `diary-portfolio-tradfi/`,
other teams' directories, `tournament/tradfi/critic/`, `tournament/tradfi/results/`, or any
other prohibited path were read. No network access of any kind. No holdout information of
any kind was seen, inferred, or probed; no post-2024-06-30 market knowledge was used in any
design decision (regime-robustness arguments in the brief are generic, not event-based).

## Imports in team code

`numpy`, `pandas`, stdlib (`json`, `sys`, `pathlib`), `tournament.engine`,
`core_tradfi` (metric helpers only, inside scratch_run.py diagnostics). The deliverable
`strategy.py` (QE-owned) requires only numpy/pandas.

## Experiment ledger integrity

`experiments.jsonl`: 14 lines — reg-001 (registration) + exp-002 … exp-014 (13 material
experiments). Every line was appended BEFORE reading the corresponding result (ledger
timestamps monotone). Budget: 13/40 used; no pivot used; one family throughout.

## Independence statement

All design decisions were made solely by the team-03 QR from the sources listed above.
No communication with any other team occurred; no other team's directory, registration
rationale (beyond the public registry.jsonl status lines), code, or results informed this
work. The registry was read only to verify family approval status and avoid collisions.

## QE implementation notes (Phase 2)

QE read: `CHARTER.md`, `config.toml`, `teams/team-03/BOOTSTRAP.md`, `research_brief.md`
(§2 binding spec), and the evaluator interfaces it implements against —
`analysis/portfolio/tradfi/tournament/{engine,harness,protocol,cli,leaderboard,constants}.py`.
Reference-only (not spec): `scratch_lib.py`. No prohibited path was read, imported, grepped,
or referenced; no network, subprocess, file I/O, or holdout access. Clean-room maintained.

`strategy.py` is a direct transcription of `scratch_lib.build_raw` at the frozen exp-014
parameters (`L=5, skip=0, vol_std=True, vol_win=63, transform="blend", winsor=3.0,
ema_span=5, z_in=0.0, exhaust=False, vix_mode="pct", vix_thr=0.85, sector_demean=False,
inv_vol=False, peers_min=2, min_hist=63`). Dead branches (skip / z_in / exhaust / level-VIX
/ sector-demean / inverse-vol) were removed per the §6 QE checklist; the numerics and step
order of the live branches (residual → vol-standardised L-day sum → −core → 50/50 z-rank
blend → VIX-percentile gate BEFORE EMA → EMA(5) → active mask) are preserved bit-for-bit.
No parameter was re-tuned; no research choice was made by the QE. The spec left nothing
ambiguous — every lookback, missing-data rule, transform order, and parameter was pinned in
§2 plus the exp-014 invocation, so nothing was bounced to the QR.

Imports in `strategy.py`: `numpy`, `pandas` only (+ `from __future__ import annotations`).
Consumes ONLY `pn['close']`, `aux['vix']`, `aux['sector_map']`; `aux['seed']` unused (no
randomness). Tickers derived from `pn['close'].columns` at runtime.

Bundle hygiene: `scratch_run.py` (QR reference-only runner) was removed from the team dir —
it imports `json`/`sys`/`pathlib`/`tournament`, which the mandatory `cli.py audit` static
scan (import whitelist) rejects, and it is not a deliverable. `scratch_lib.py` is retained
(numpy/pandas only → scan-clean) as the transcription reference. `test_strategy.py` imports
the sibling `strategy` module directly (pytest prepend mode) to stay within the scan
whitelist.

Verification (all on the frozen IS snapshot via the evaluator):
- `uv run pytest teams/team-03/test_strategy.py -q` → 7 passed (determinism, future-corruption,
  truncated-replay, same-bar, no-hardcoded-tickers, ragged-starts, grid-conformance).
- `cli.py team-run --team team-03` → Sharpe +0.568 @1x / +0.439 @2x, maxDD −32.5%,
  breadth 25/23, ann. turnover 15.5 — reproduces exp-014 (`is_report.md` §4).
- `cli.py audit --team team-03` → PASS (scan, determinism, truncated-replay, future-corruption,
  same-bar all green; 11 truncation cuts). The VIX gate uses `aux['vix']`, which the harness
  truncates/corrupts too; the gate is a causal rolling-252d percentile, so it passes.
