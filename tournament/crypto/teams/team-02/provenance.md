# team-02 — Provenance (t02-oi-crowding-fade-v1 negative result + t02-breakout-channel-v2 pivot)

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-02/BOOTSTRAP.md` (own team dir only)

Authorized evaluator source (`analysis/portfolio_tournament/`, holdout.py NEVER opened):
- `constants.py`, `engine.py` (full), `cli.py` (header/help + command definitions only),
  `teamlib.py`

Market data: reached EXCLUSIVELY through
`portfolio_tournament.engine.load_is_panels()` from scratch scripts inside
`tournament/crypto/teams/team-02/out/scratch/` (manifest-verified frozen IS snapshot).
No file under `tournament/crypto/data_is/` was opened directly.

## What I did NOT read

No access to: `data/`, `pf_data/`, `data/funding_rates/`, `data/open_interest/`,
`analysis/portfolio/`, `analysis/portfolio_v2/`, `analysis/portfolio_tournament/holdout.py`,
`src/crypto_trade/`, `diary-portfolio*`, `briefs-*`, `reports-*`, `BASELINE_*.md`,
`iter_*.py`, `features_*`, `tournament/crypto/MANIFEST.sha256.json`,
`tournament/crypto/results/`, `tournament/crypto/critic/`, `tournament/crypto/_build/`,
any other team's directory. No network access of any kind (no such tools in this
environment; none attempted). The sealed holdout was never inferred, probed, or requested.

## What I imported

- Scratch analysis (`out/scratch/*.py` only; out/ is excluded from the harness scan and the
  frozen bundle per the orchestrator's process note): `portfolio_tournament.engine`,
  `portfolio_tournament.constants`, numpy, pandas, stdlib.
- Team strategy code (QE phase): `strategy.py` implements the §II.8 QE SPEC verbatim from
  the normative `out/scratch/e12_final.py` reference, importing numpy/pandas only; no aux
  usage, no file I/O, no network, no randomness. `team-run` reproduced the spec's
  verification targets exactly (see `out/is_metrics.json`); `cli.py audit` = PASS on all
  six harness checks; `test_strategy.py` 8 passed. The QE's two static-scan token fixes
  were docstring/import wording only (no logic change). The QR did not modify
  `strategy.py` or `test_strategy.py` after QE delivery.

## Experiment ledger

All material experiments were logged via `cli.py log-experiment` BEFORE their results were
computed/read. Part I (OI-crowding fade): e01, e01b, e02, e03, e04, e05, e06 — 7 entries.
Part II (breakout/channel pivot, orchestrator-approved and journaled at choice time): e07,
e08, e09, e10, e11, e12 — 6 entries. **Budget used: 13 of 40.** Scratch scripts that
produced each result are retained under `out/scratch/` (`common.py`, `e01_eda.py`,
`e01b_ic.py`, `e02_e03_grids.py`, `e04_decomp.py`, `e05_formC.py`, `e06_postmortem.py`,
`breakout.py`, `e07_e08_grids.py`, `e09_e10_refine.py`, `e11_robust.py`, `e12_final.py`).
Part II's §II.1-§II.6 (mechanism, forms, grid, falsifier, selection rule) were written into
`research_brief.md` BEFORE e07 was logged; the selection in §II.7 follows those rules
mechanically, including one documented rejection (inverse-vol, e09) and one documented
non-override (N=60 kept over the post-hoc-better N=90, rule II.6.2).

## Independence statement

All signal definitions, formulas, grids, the falsifier, and the selection rule in
`research_brief.md` were designed inside this clean room from the charter-listed data menu
and general market-microstructure reasoning. No production-book code, no other team's work,
and no out-of-snapshot data informed any choice. The registered mechanism
(`t02-oi-crowding-fade-v1`) was researched exactly as approved; its falsifier fired and the
negative result is reported with the same precision a positive would have received. The
reverse-sign diagnostic in e06 was labeled DIAGNOSTIC in the ledger BEFORE its result was
read and is not proposed as a submission (it would misrepresent the registered family).

The same applies to Part II: the breakout/channel family (`t02-breakout-channel-v2`,
approved pivot) was designed from the charter data menu, classic public-domain channel
constructions (Donchian-style state, channel position), and the transferable process lessons
of Part I (turnover cost discipline; the same-bar IC horizon correction) — no production
code, no other team's work, no out-of-snapshot data. The final spec uses ONLY `pn["close"]`;
funding, OI, LS-ratio, taker-flow, and volume panels are deliberately untouched to respect
other teams' registered families.
