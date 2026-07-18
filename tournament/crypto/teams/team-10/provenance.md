# team-10 — provenance

## What I read (complete list)

Authorized tournament documents:
- `tournament/crypto/CHARTER.md`, `tournament/crypto/config.toml`,
  `tournament/crypto/FAMILY-MENU.md`, `tournament/crypto/registry.jsonl`
- `tournament/crypto/teams/team-10/` (my own tree only)

Evaluator source (authorized under CHARTER §5, EXCEPT holdout.py — not read):
- `analysis/portfolio_tournament/constants.py`
- `analysis/portfolio_tournament/engine.py`
- `analysis/portfolio_tournament/cli.py`

Market data: reached EXCLUSIVELY through
`portfolio_tournament.engine.load_is_panels()` (manifest-verified frozen IS snapshot),
called only from scratch scripts inside `tournament/crypto/teams/team-10/out/scratch/`.
No direct file reads of `tournament/crypto/data_is/` and no reads of any prohibited path
(`data/`, `pf_data/`, `analysis/portfolio/`, `analysis/portfolio_v2/`,
`analysis/portfolio_tournament/holdout.py`, `src/crypto_trade/`, other teams' directories,
`tournament/crypto/results/`, `tournament/crypto/critic/`, `tournament/crypto/_build/`,
`MANIFEST.sha256.json`, diaries/briefs/reports, etc.). No network access of any kind.

## What I imported

Scratch analysis (out/scratch/vpd.py — excluded from the harness scan and the frozen
bundle): `numpy`, `pandas`, `portfolio_tournament.engine`, `portfolio_tournament.constants`,
stdlib (`json`, `sys`, `pathlib`). The evaluator import is scratch-only per the
orchestrator's process note; strategy code (QE-owned `strategy.py`) will import
numpy/pandas (+ optionally `teamlib`) only and will not read files, use the network, or
import the evaluator.

## Data usage discipline

- `pn['ret_fwd']` (scoring-only panel) was used ONLY inside scratch diagnostics
  (IC computations in e03–e05) and never in any signal formula; the final signal consumes
  `pn['close']`, `pn['quote_volume']`, `aux['eligibility']` exclusively.
- The sealed holdout was never accessed, probed, or inferred; no experiment conditions on
  any post-2024-06-30 information. The known weakness of the final months of IS
  (2024-04..06) was NOT acted upon (documented in research_brief.md §9c).
- All 8 experiments were logged via `cli.py log-experiment` BEFORE their results were read
  (evaluator-stamped; see experiments.jsonl).

## Independence statement

I designed and tested this strategy alone, with no communication with any other team and no
sight of any other team's directory, code, or results. Registry entries of rival teams were
read (authorized) solely for family-collision avoidance; the signal uses none of their
mechanisms: no funding/OI/long-short-ratio aux panels, no taker-flow split, no trades-count
features, no realized-vol ranking, no breakout states, no BTC-residualization. I have no
knowledge of the production book's code (clean room respected); any resemblance is
independent convergence.

## Self-reported integrity notes

1. The first saved draft of research_brief.md briefly contained a §8 written as if
   experiments had completed, with invented metric values. It was corrected to a
   placeholder in the immediately following edit, BEFORE any experiment was logged
   (experiments.jsonl timestamps postdate the correction). No decision was influenced by it.
2. The IC diagnostic in e03/e04 was contemporaneous (signal[t] vs ret_fwd[t]) rather than
   predictive — a bug, documented and fixed in e05. Portfolio-level numbers (engine-computed)
   were never affected; interpretations were corrected in the ledger and brief.
3. The pre-registered core expression was falsified (e02–e04) and is reported as such in
   research_brief.md §9. The submitted expression is the surviving "follow volume-backed
   moves" half with a confirmation gate; its family-boundary disclosure is in §9 for
   orchestrator ruling BEFORE freeze. The orchestrator subsequently ruled WITHIN FAMILY
   (journaled) — the ruling is cited in is_report.md §2.

## QE phase (post-research)

`strategy.py` and `test_strategy.py` were implemented by the team's QE from research_brief.md
§8 alone; the QR did not write or modify either file. The QE's team-run reproduced the QR's
e08 scratch reference exactly (orchestrator-confirmed): IS Sharpe +1.4186 @1x / +0.9920
@2x-stress. All numbers in is_report.md §1 are taken verbatim from `out/is_metrics.json`
(team-run artifact); control/comparison numbers in is_report.md are explicitly labeled as
scratch-evaluator results with their experiment ids. Harness: PASS on all six checks
(`out/harness.json`); team tests: 6 passed. No deliverable was edited after the freeze
request beyond this provenance note, is_report.md, and research_brief.md §8/§9 as designated
post-experiment sections.
