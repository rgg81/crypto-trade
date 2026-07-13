---
name: top40-tournament
description: "Orchestrate the fresh ten-team QR+QE Binance USD-M perpetual Top-40 tournament from common-data freeze through independent research, frozen canonical reruns, comparative Critic review, user ballot, final leaderboard, and forward-paper handoff. Use for quant-portfolio-blind-top40 tournament execution or continuation."
---

# Top-40 Tournament Orchestration

Read `TOURNAMENT-CHARTER-TOP40.md`, `tournament/top40/config.toml`, and
`tournament/top40/METHODOLOGY-DISTILLATION.md` first. They override old portfolio workflows. The
distillation carries controls from all three local quantitative skill files while excluding their
illustrative signals and trade mappings. Do not load old trade ideas or results.

## Orchestrator scope

You own common infrastructure, data/config hashes, team scheduling, frozen reruns, score
aggregation, and commits. You do not invent team strategies. Teams own only their namespaces.

## Phase 0 — freeze the playing field

1. Verify branch/worktree is `quant-portfolio-blind-top40`.
2. Build one Binance public-data snapshot and SHA-256 manifest. Include current/delisted archive
   coverage, actual funding timestamps/rates, and current exchange metadata. Record limitations.
3. Run shared evaluator/unit tests and freeze evaluator/config/data SHAs.
4. Publish compute budget, deadline, seeds policy, public-OOS access logging, and regime labels.
5. Create `team-01` through `team-10` namespaces from the submission template.

No team starts before shared SHAs are fixed.

Executable Phase-0 path:

```bash
uv run python scripts/top40_tournament.py init-teams
uv run python scripts/top40_tournament.py build-snapshot
uv run python scripts/top40_tournament.py verify-snapshot
uv run pytest tests/tournament -q
uv run ruff check src/crypto_trade/tournament tests/tournament scripts/top40_tournament.py
```

Commit the common infrastructure, manifest, common BTC artifacts, and team scaffolds. From that
clean commit run `uv run python scripts/top40_tournament.py freeze-phase0`, then commit the freeze
record before dispatch. Freeze is single-shot; verification derives the later record commit and
requires its exact bytes to stay clean. The common commit must already contain the canonical
genesis-only `organizer_research_journal.jsonl` and its `run_state.json` anchor. The resulting
lifecycle phase is `research`.

## Phase 1 — dispatch ten isolated pairs

For each team, dispatch one `top40-quant-researcher`, then its paired
`top40-quant-engineer`. Run pairs in concurrency waves as capacity allows. Pass only `TEAM_ID`,
shared SHAs, compute budget, and deadline—never another team's context or a prior idea.

QR handshake: `RESEARCH_SPEC_READY team-NN <brief-sha> <trial-budget>`.

QE handshake: `ENGINEERING_READY team-NN <strategy-sha> <tests-sha> <reproduce-command>`.

Before each deliberate full public-OOS view, append an OOS-requesting registration and run:

```bash
uv run python scripts/top40_tournament.py run-team team-NN --candidate-id CANDIDATE
```

Commit the candidate source and pending registration before invoking the gate. The command adds a
hash-chained organizer reservation before evaluation, then automatically appends measured
CPU/wall time, status, metrics, and artifact hashes to the organizer journal and the matching team
result event. Failed/interrupted attempts count. After every attempt, commit the strict append of
`organizer_research_journal.jsonl`, `run_state.json`, the affected `experiments.jsonl`, and its run
outputs before registering another candidate.

If `run-team` is interrupted, recover the write-ahead journal before doing anything else:

```bash
uv run python scripts/top40_tournament.py recover-research-accounting
```

Recovery may finish an already-journaled result or may expose a still-open reservation. In the
latter case, explicitly consume it as a failed attempt—never rerun or delete it—then commit the
three accounting files:

```bash
uv run python scripts/top40_tournament.py close-interrupted-run team-NN CANDIDATE
git add tournament/top40/organizer_research_journal.jsonl \
  tournament/top40/run_state.json tournament/top40/teams/team-NN/experiments.jsonl
git commit -m "Recover team-NN research accounting"
```

After all research, commit the required QR evidence, run `mark-review team-NN qr`, and commit the
resulting `run_state.json`. Once every team source/evidence file is final, build and commit the
complete source manifest, then record and commit the QE review:

```bash
uv run python scripts/top40_tournament.py build-team-source-manifest team-NN
git add tournament/top40/teams/team-NN
git commit -m "Freeze team-NN source evidence"
uv run python scripts/top40_tournament.py mark-review team-NN qe
git add tournament/top40/run_state.json
git commit -m "Record team-NN QE review"
```

The QE review includes `team_source_manifest.json`; any later team-file change requires rebuilding
and re-reviewing before champion freeze. Review records are commit- and evidence-hash-bound.

If two proposals collide, use only pre-experiment mechanism fingerprints to request that the later
proposal broaden or pivot. Do not reveal the first team's implementation or results.

## Phase 2 — technical validation and freeze

Validate schema, paths, hashes, entrypoint, dependency lock, deterministic seeds, and dry-run
execution. A formatting/path repair requires rebuilding the source manifest and repeating the
affected review; no team file changes after that reviewed freeze commit. Then freeze one commit per
team and close strategy mutation. Record all ten freeze SHAs before any canonical score is computed.

```bash
uv run python scripts/top40_tournament.py freeze-team team-NN \
  --strategy-name NAME --freeze-commit COMMIT
git add tournament/top40/run_state.json
git commit -m "Freeze team-NN champion"
```

Commit the state change before freezing the next team. The journal, state, and affected team
ledger must already be clean, committed, and strict append-only; on the tenth freeze this audit
covers all ten ledgers. Only the tenth recorded champion changes `research` to `cohort_frozen`.

The whole allowed UTF-8 team text tree is Git-bound and fingerprinted (2 MiB per file, 10 MiB
total), but the worker stages only `.py` plus the fixed small `frozen_config.json`/
`strategy_config.{json,toml,yaml,yml}` names. Opaque prefit state and timestamp→target lookups are
forbidden. Canonical execution requires the implemented Linux namespace/Landlock/seccomp sandbox,
a minimal non-inherited environment, resource limits, a 900-second CPU cap, and a 1,800-second wall
cap; it fails closed if those host controls are unavailable.

## Phase 3 — canonical rerun

For each frozen team, in a clean process:

1. Regenerate targets only through the narrow strategy protocol.
2. Run common base evaluator and independent 2×-cost evaluator.
3. Run corrupt-future, append-invariance, point-in-time membership, funding-sign/timestamp,
   next-open, forced-exit, and deterministic-rerun audits.
4. Generate daily returns, targets, fills, positions, funding, long/short attribution, quarterly,
   annual, regime, worst-window, tail-risk, and raw metric artifacts.
5. Populate canonical `submission.json`; team self-reported metrics never override it.
6. Use `finalize-team TEAM_ID` to read the recorded champion. It runs the champion twice in
   independent clean workers and requires byte-identical canonical artifacts and scalar fields
   before assembling/validating the submission. The command is unavailable before the
   ten-champion barrier.
7. Validate the cohort:

```bash
uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-*/submission.json
```

A common evaluator defect triggers one shared correction and full affected-cohort rerun. Commit
each of the first nine teams' tracked submission/artifact manifest and updated state before
finalizing another team. Reproducible report files under `reports-top40/team-*` remain local and
are hash-bound; do not force-add the ignored output directories. The tenth `finalize-team` also
creates `objective_lock.json` with all ten artifact/output hashes and objective scores/ranks and
changes the phase to `objective_locked`. Commit its tracked submission, artifact manifest,
`objective_lock.json`, and `run_state.json` in one commit. It must be the objective lock's unique
first-add commit and have the command's recorded pre-lock HEAD as its sole parent; do not insert an
intermediate commit.

## Phase 4 — objective score, Critic, user vote

The tenth finalization has already locked objective metrics. Commit that record, then invoke one
`top40-tournament-critic` over all submissions with blinded team labels. Persist
`critic_scores.json` (0–15 each), the comparative review, and strict
`critic_adjudications.json` copied from its template and bound to the cohort/team/artifact hashes.
Every integrity finding cites one hashed artifact and uses only the charter allowlist; use an empty
findings array when no breach is alleged. Seal those files before confirmations or any user ballot:

```bash
uv run python scripts/top40_tournament.py lock-critic \
  --critic-scores tournament/top40/critic_scores.json \
  --critic-adjudications tournament/top40/critic_adjudications.json
git add tournament/top40/critic_scores.json \
  tournament/top40/critic_adjudications.json \
  tournament/top40/critic_lock.json tournament/top40/run_state.json
git commit -m "Lock Top40 Critic ballot"
```

That commit must be the unique first-add commit for all three Critic files and its sole parent must
be the objective-lock record commit. Do not create `critic_confirmations.json` or
`user_scores.json` earlier.

Next, the organizer independently verifies each cited integrity finding and records, for all ten
teams, only the exact Critic codes that are confirmed. Unconfirmed findings remain Critic
commentary and never disqualify. Lock and commit the confirmation before asking for user scores:

```bash
uv run python scripts/top40_tournament.py lock-critic-confirmations \
  --confirmations tournament/top40/critic_confirmations.json
git add tournament/top40/critic_confirmations.json \
  tournament/top40/critic_confirmation_lock.json tournament/top40/run_state.json
git commit -m "Lock Top40 Critic confirmations"
```

The confirmation commit must directly follow the Critic-lock commit. The command aborts if the
confirmed findings would eliminate every mechanically valid team; resolve a common integrity
defect uniformly rather than weakening one team's proof.

Only now ask the user for the canonical `user_scores.json` (0–15 each). Never infer a missing vote
or substitute the Critic for the user's ballot. Lock and commit it as the direct child of the
confirmation-lock commit:

```bash
uv run python scripts/top40_tournament.py lock-user-ballot \
  --user-scores tournament/top40/user_scores.json
git add tournament/top40/user_scores.json \
  tournament/top40/user_ballot_lock.json tournament/top40/run_state.json
git commit -m "Lock Top40 user ballot"
```

Final scoring:

```bash
uv run python scripts/top40_tournament.py score \
  --critic-scores tournament/top40/critic_scores.json \
  --critic-adjudications tournament/top40/critic_adjudications.json \
  --user-scores tournament/top40/user_scores.json \
  --json-out tournament/top40/leaderboard.json \
  --csv-out tournament/top40/leaderboard.csv \
  tournament/top40/teams/team-*/submission.json
git add tournament/top40/leaderboard.json tournament/top40/leaderboard.csv
git commit -m "Publish final Top40 leaderboard"
```

Non-provisional scoring accepts only those ten canonical submission paths and reloads their exact
objective-locked bytes; alternate copies are rejected even if their schema is valid.

Publish raw metrics alongside ranks. The highest total valid team wins. Separately publish
`paper_eligible`; never rewrite “not eligible” into “no tournament winner.”

## Phase 5 — forward paper

Commit the final leaderboard and every selection input first, then freeze the unique rank-one
winner unchanged:

```bash
uv run python scripts/top40_tournament.py freeze-winner
git add tournament/top40/winner_freeze.json tournament/top40/run_state.json
git commit -m "Freeze Top40 forward-paper winner"
uv run python scripts/top40_tournament.py verify-winner-freeze
```

The winner-freeze commit must add the record exactly once, contain the matching paper-frozen
`run_state.json`, and have the committed final-selection HEAD as its sole parent.

The prospective clock begins at the strictly next 00:00, 08:00, or 16:00 UTC boundary after the
winner-freeze timestamp. Quarantine 2026-07-01 through that boundary rather than backfilling it as
untouched evidence. The handoff is paper-only and initializes a hash-chain genesis; it does not
route orders or yet append live observations. A later ingester must apply data freshness, current
exchange filters, order rounding, mark-price risk, actual funding, reconciliation, and kill-switch
checks. Forward results affect deployability only; do not retroactively alter the tournament score.

## Required checks before handoff

```bash
uv run pytest tests/tournament -q
uv run ruff check src/crypto_trade/tournament tests/tournament scripts/top40_tournament.py
git diff --check
```
