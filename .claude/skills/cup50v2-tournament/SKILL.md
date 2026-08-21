---
name: cup50v2-tournament
description: Run the CUP-50 v2 twelve-lane Binance Top-50 tournament end to end — build, activation, team research, field close, one-shot sealed observation, release, and the four forward paper desks. Use when asked to run, continue, or check CUP-50 v2.
---

# CUP-50 v2 — organizer runbook

Worktree `quant-portfolio-blind-top50-v2`. Human policy:
`TOURNAMENT-CHARTER-CUP50-V2.md`. Machine policy: `tournament/cup50v2/config.toml`, which is the
only place a tunable lives — never restate a cap, a cost or a score weight anywhere else.

**Never edit `src/crypto_trade/cup50/` or `cup50_desk/`.** CUP-50 is hash-bound by its own
activation record and its paper desk is live in a sibling worktree.

## Order of operations

```
acquire-reuse → build → readiness → export-protocol → export-evaluator → docker build →
quarantine → activate → [research] → field-close → observe → integrity-review →
leaderboard → release → paper
```

Everything before `activate` is repeatable. Everything after is one-shot: `activate`, `nominate`,
`field-close`, `observe start`, and `release` all refuse to run twice, on purpose.

## Phase 1 — data and activation

```bash
uv run python -m crypto_trade.cup50v2.cli build \
  --acquisition data/cup50v2/acquisition \
  --acquisition-manifest data/cup50v2/acquisition/manifest.json \
  --classification-audit tournament/cup50v2/historical-asset-classification.json \
  --pure-crypto-audit-output data/cup50v2/pure-crypto-audit.json \
  --is-root data/cup50v2/is --sealed-root data/cup50v2/sealed \
  --team-is-root data/cup50v2/team-is

uv run python -m crypto_trade.cup50v2.cli readiness \
  --is-root data/cup50v2/is --sealed-root data/cup50v2/sealed \
  --seed-root tournament/cup50v2/seeds \
  --unavailability-audit tournament/cup50v2/historical-unavailability.json
```

Readiness replays all twelve seeds and takes tens of minutes; run it detached. It fails closed if
fewer than nine lanes deploy — a field that does not trade has not tested execution.

Activation requires every preflight check to pass, a clean git tree, and a digest-pinned sandbox
image. Build the image from `tournament/cup50v2/sandbox` and **never from the repository root**:
the root would hand the daemon the sealed snapshot and the acquisition tree.

## Phase 2 — research

Twelve `cup50v2-team-researcher` agents, one per lane, workspaces at
`/home/roberto/cup50v2-teams/team-NN/` — outside the repository, so no team's scan can ever see
another's. Results go to a sibling `team-NN-results/`, because the clean-room scan rejects a cached
frame inside a research root.

Dispatch three or four at a time. Answer protocol questions; refuse strategy questions, and never
relay one team's facts to another, including aggregates.

At each nomination: `critic-pack` → `cup50v2-critic` → confirm any recommended code independently
before acting on it. Run `scripts/cup50v2_transcript_audit.py` for every team before field close.

## Phase 3 — observation

`field-close` freezes dispositions, qualification verdicts and the observation order together, while
the sealed window is still shut. Then `observe start`, then one `observe point` per point of every
nominated lane — about 143 points at a few minutes each.

Observation is silent. Do not report a partial standing, do not compare lanes mid-batch, and do not
retry a terminal: an interrupted candidate point is a terminal zero and that is the rule working. An
*organizer* failure pauses instead, and resumes from its own record.

## Phase 4 — release and desks

`integrity-review` → `leaderboard` → `release` publishes atomically. Then four desks: the winner,
two next-ranked eligible lanes, and the equal-risk ensemble. Minimum 183 official days before the
capital rule is even evaluated.

## Before you scan a workspace

Remove tool droppings first — `__pycache__`, `.pytest_cache`, `.ruff_cache`. The scan flags them
and it is right to: a research root should carry source, not caches. But they reappear whenever
anyone runs Python in the workspace, so a scan that fails on them is telling you to tidy up, not
that a team leaked anything. Clean, then scan, then judge what is left.

## Things that will bite

- A held decision is an all-NaN row in `raw_targets`. Reduce with `np.nanmax`.
- The per-symbol 0.20 cap binds before the gross 1.0 cap on a book with few names.
- The risk unit can only shrink a book onto the target; a calm book is held at its ceiling.
- `PRIOR_NAMESPACE` matches digits possessively, and exempts this edition's own worktree name.
  Relax the first and every source importing this tournament's toolkit is rejected; drop the
  second and every source that writes down where the repository lives is rejected. Both were
  found by teams, not by tests.
- The event lane is legitimately flat between events. Judge it on the field-level floor, not a
  per-lane turnover assertion.

## If something is wrong after the first sealed read

Stop. The charter voids the edition rather than correcting it retrospectively. CUP-50 corrected in
place, changed its winner, reclassified nine lanes after their evidence had been read, and its own
incident record concedes the correction cannot recreate the blindness it spent. A new version is
cheaper than a result nobody can trust.
