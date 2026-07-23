# Team 09 monitor

Use the `team09-monitor` skill in `.claude/skills/team09-monitor/SKILL.md`.

Run the read-only healthcheck and observational digest serially:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1
uv run python scripts/team09_paper_healthcheck.py
uv run python scripts/team09_paper_digest.py
```

Alert only on experiment-integrity failures. Never intervene because of PnL, drawdown, Sharpe,
turnover, exposure, or a losing streak. Preserve all append-invariant artifacts and keep the engine
paper-only.
