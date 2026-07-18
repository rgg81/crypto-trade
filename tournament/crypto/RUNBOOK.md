# crypto-cup-01 — Orchestrator Runbook

Phase checklist. Every state change journals to `journal.jsonl`; commit at each phase gate.
`CLI = uv run python analysis/portfolio_tournament/cli.py`

## Phase 0 — substrate + freeze commit
- [ ] Funding fetched for the full 430-symbol union (REST + archive fallback); OI top-up done
- [ ] `CLI build-universe` → pool/union counts sane (~515 / 209 IS / 430 full)
- [ ] `CLI data-report --window is` → 0 FAIL (WARNs reviewed + journaled)
- [ ] `CLI build-snapshot` then `CLI verify-snapshot`
- [ ] Snapshot sanity: max open_time = 2024-06-30 16:00 UTC; ~209 symbol dirs; per-candle
      top-40 count = 40 post-warmup
- [ ] `uv run pytest tests/test_crypto_tournament.py -q` green
- [ ] Dry-run gate: scratch reference strategy scores plausibly @1x/2x; deliberately-leaky
      scratch strategy FAILS the harness on the right checks; tamper test trips the manifest;
      holdout gate refuses without flag+env
- [ ] `CLI init-teams`
- [ ] FREEZE COMMIT — `git add -f analysis/portfolio_tournament tests/test_crypto_tournament.py`
      (analysis/ is gitignored!) + `tournament/crypto/` docs + `.claude/agents/crypto-tournament-*`;
      verify with `git ls-files analysis/portfolio_tournament/ | wc -l` (≥ 12 files)

## Phase 1 — family registration (two-pass FCFS)
- [ ] Dispatch 10 QRs registration-only (primary + 2 backups each, one-line mechanisms)
- [ ] Resolve pass 1 (primaries FCFS by dispatch order), pass 2 (backups), ≤2 redraw rounds
- [ ] `CLI register-family` one line per decision (approve/veto + reason); commit registry

## Phase 2 — research waves (3/3/3/1)
Per team, sequentially inside a wave:
- [ ] QR: research_brief.md (mechanism, falsifier, parameter plan) + experiments via
      `CLI log-experiment` + is_report.md + provenance.md
- [ ] QE: strategy.py + test_strategy.py; iterate `CLI team-run` / `CLI audit` to PASS
- [ ] Orchestrator: `CLI freeze --team NN --family-id <id>` (validates registry approval)
- [ ] Commit per wave. Approval lines for any pivot are journaled AT choice time

## Phase 3 — Critic audit (batches of 5)
- [ ] Critic audits each frozen team (harness rerun, greps, SHAs, ledger, family fidelity,
      artifact consistency); orchestrator writes `critic/audit-team-NN.md` verbatim
- [ ] ONE BLOCK-PENDING-FIX round where verdicted; re-freeze + re-audit; commit

## Phase 4 — Stage-1 leaderboard
- [ ] `CLI leaderboard --teams <critic-passed>` — byte-identical reproduction gate; top 4
      advance; noise floor printed; commit results/

## Phase 5 — sealed holdout
- [ ] Refresh klines through ≥ 2026-07-01 AND funding/OI for the FULL 430-symbol union
- [ ] `CLI data-report --window full` → 0 FAIL
- [ ] Journal the store state (kline max timestamps) for provenance
- [ ] `export CRYPTO_TOURNAMENT_ALLOW_HOLDOUT=1`
- [ ] Per finalist: `CLI run-holdout --team NN --confirm-holdout` (canonical; mask-replay +
      IS-replay must pass), then `--no-funding`, `--cost-mult 2`, `--slip-mult 2`
- [ ] `CLI final-report`; write `results/FINAL_REPORT.md` (winner, noise floor, regime
      caveats, per-team post-mortems); commit; `unset CRYPTO_TOURNAMENT_ALLOW_HOLDOUT`

## Phase 6 — winner paper desk (6 months)
- [ ] `src/crypto_trade/portfolio/strategy_tournament.py` (frozen-submission book via the
      Stage-2 path; `check_submission_shas` at startup + every recompute)
- [ ] `run_portfolio_tournament_paper.py` — dry-run PortfolioEngine, own DB
      `data/portfolio_tournament_paper.db`, log `logs/portfolio_tournament_paper.log`
- [ ] Healthcheck script + monitor cron per the portfolio-monitor parallel-track recipe
- [ ] Hands-off 6 months; compare realized Sharpe to IS (holdout was one regime — expect
      paper nearer IS levels)
