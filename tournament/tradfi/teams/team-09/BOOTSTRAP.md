# team-09 — tradfi-cup-01 boot card

You are one of ten independent teams. Read, in order:
1. `tournament/tradfi/CHARTER.md`  — the rules. Binding.
2. `tournament/tradfi/config.toml` — machine-readable parameters.
3. `tournament/tradfi/FAMILY-MENU.md` — seeded mechanism families (yours must be registered
   and approved in `tournament/tradfi/registry.jsonl` before you build).

Workspace: this directory ONLY. Data: the frozen IS snapshot `tournament/tradfi/data_is/`
reached exclusively through the evaluator (`cli.py team-run` / `tournament.engine`).

Deliverables checklist (all required to freeze):
- [ ] research_brief.md   — mechanism, economic rationale, falsifier, parameter plan
- [ ] strategy.py         — `build_raw_weights(pn, aux)` (+ optional helper .py files)
- [ ] test_strategy.py    — team-owned tests incl. a future-corruption self-check
- [ ] experiments.jsonl   — append-only: one line per material experiment, BEFORE reading
                            its result
- [ ] is_report.md        — numbers ONLY from `team-run` output (out/is_metrics.json)
- [ ] provenance.md       — what you read, what you imported, independence statement
- [ ] PASS from `cli.py audit --team team-09`
Then the orchestrator freezes: `cli.py freeze --team team-09 --family-id <id>`.
