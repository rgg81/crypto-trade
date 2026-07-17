# tradfi-cup-01 — Orchestrator Runbook

All commands from the worktree root. CLI = `uv run python analysis/portfolio/tradfi/tournament/cli.py`.

## Phase 0 — substrate + freeze
```
uv run python analysis/portfolio/tradfi/ingest_yahoo.py            # 69 names + VIX, 2010 -> now
uv run python analysis/portfolio/tradfi/ingest_perp_tradfi.py      # perp klines + funding
uv run pytest tests/test_tradfi_tournament.py tests/test_portfolio_tradfi_foundation.py tests/test_tradfi_splice.py -q
<CLI> build-snapshot
<CLI> verify-snapshot
<CLI> init-teams
git add -A tournament/ analysis/portfolio/tradfi/tournament/ .claude/agents/tradfi-tournament-*.md tests/test_tradfi_tournament.py
git commit    # THE FREEZE COMMIT
```
Sanity gates before freeze: every SECTOR_MAP name with pre-2024-07 history present; AAPL/MSFT/JPM
start ≈2010-01; snapshot max bar = 2024-06-28; VIX present. Dry-run: scratch team with the
reference xsmom → team-run → audit (PASS) → freeze → leaderboard reproduces; a deliberately
leaky scratch strategy must FAIL the audit. Delete scratch dirs after; journal notes the dry-run.

## Phase 1 — family registration
Dispatch each QR with a REGISTRATION-ONLY task (family_registration.json + brief §1 in its team
dir). Resolve collisions FCFS; `register-family` each approval/veto; vetoed teams redraw
(≤2 rounds). Commit `registry.jsonl`.

## Phase 2 — research waves
Waves of 3 teams (disjoint dirs). Per team, sequential: QR finalizes `research_brief.md` +
experiment plan → QE implements `strategy.py` + `test_strategy.py`, iterates INSIDE the team
dir, runs `team-run` then `audit` until PASS → orchestrator runs `freeze --team NN --family-id ID`.
Commit after each wave.

## Phase 3 — Critic audit
Dispatch the tournament Critic once per team (batch 5+5). BLOCK-PENDING-FIX → one QE fix round →
re-audit. Verdicts to `critic/audit-team-NN.md`. Commit.

## Phase 4 — Stage-1 leaderboard
```
<CLI> leaderboard --teams <comma-list-of-critic-PASSED-teams>
```
Byte-identical reproduction required; failures are FAILs, not negotiations. Top 4 advance. Commit.

## Phase 5 — sealed holdout
```
uv run python analysis/portfolio/tradfi/ingest_yahoo.py && uv run python analysis/portfolio/tradfi/ingest_perp_tradfi.py
export TRADFI_TOURNAMENT_ALLOW_HOLDOUT=1
<CLI> run-holdout --team team-0X --confirm-holdout                      # x4 canonical
<CLI> run-holdout --team team-0X --confirm-holdout --no-funding         # sensitivities
<CLI> run-holdout --team team-0X --confirm-holdout --cost-mult 2
<CLI> run-holdout --team team-0X --confirm-holdout --exclude PAYPUSDT
<CLI> final-report
unset TRADFI_TOURNAMENT_ALLOW_HOLDOUT
```
Winner = best canonical net holdout Sharpe. Write FINAL_REPORT.md (add Sharpe noise floor +
narrative around the mechanical stage2 report). Commit.

## Phase 6 — winner paper desk
Build `run_tradfi_tournament_paper.py` (second TradfiPaperEngine instance; DB
`data/tradfi_tournament_paper.db`; weight source = winner's frozen `build_raw_weights` through
`normalize_and_cap`; refresh cadence staggered vs the incumbent desk). Never touch the
incumbent desk's DB/log.
