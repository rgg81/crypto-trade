# tradfi-cup-01 — Critic Phase-3 cohort report (verbatim summary of record)

Auditor: tradfi-tournament-critic (Fable, read-only). Date: 2026-07-17.
Evidence base: harness reruns via cli.py audit for all nine frozen teams (all bit-identical to
frozen out/harness.json), independent SHA re-hash, denylist/obfuscation greps over full team
trees INCLUDING out/scratch (outside the static scan's coverage), ledger/artifact forensics
with filesystem-mtime reconstruction, all nine team pytest suites green, snapshot manifest
re-verified (66 files, IS end 2024-06-30). Holdout side untouched.

## Verdicts
- PASS: team-01, team-02, team-03, team-04, team-05, team-07, team-09, team-10
- PASS after amendment #1 (orchestrator-side registry fix, no team-tree change): team-06
- PASS as accepted DNF (negative-result bundle audited): team-08
- FAILs / integrity DQs: NONE

## Cross-team sweep
- No code or mechanism plagiarism; all nine implementations independently written.
- team-01 vs team-04 mechanically distinct (real residualization vs none).
- team-03 (scalar VIX gate) vs team-06 (true VIX book-switch) resolved as distinct; team-06's
  switch proven load-bearing (+0.74 composite vs +0.49 best unconditional ingredient).
- No prohibited-path, network, file-I/O, obfuscation, or cross-team references anywhere,
  including scratch code. All scratch data access via tournament.engine.load_is_panels().
- No post-freeze mutation anywhere (all source SHAs + net_is.csv SHAs match).

## Sign-flip pivot provenance (registry-flagged)
- team-02: chain intact in ledger (falsification -> single 7-cell diagnostic labeled
  "NOT a submission candidate" -> approval -> post-approval refinement of load-bearing params).
- team-09: chain verified by artifact-clock forensics — exp-008 diagnostic written ONCE
  (02:07:20 UTC), never refined; first new-family artifact reproduces it exactly per the
  pre-registered tripwire.

## Systemic observations (informational, for orchestrator + user)
1. Registry hygiene: one missing approval line (team-06 — fixed by amendment #1) and one
   harmless team-ledger registration gap (team-10). RECOMMENDATION: cli.py freeze should
   validate --family-id against an approved registry entry in future rounds.
2. Registry as an information channel: pivot-approval reason texts are team-readable and,
   with the disclosed team-09 dispatch prior, plausibly seeded the sign-flip clustering
   (02 -> 09). Authorized + disclosed; no DQ. Stage-2 reader should know that two books
   (02, 09) embed direction choices made after observing IS diagnostics and two more (03, 06)
   embed state-conditioning found after unconditional books failed — a cohort-level
   selection-on-IS effect concentrated at the top of the IS board.
3. Ledger clocks: teams 06 and 09 hand-stamped approximate times (orders verified via mtimes;
   both check out). RECOMMENDATION: evaluator-stamped ledger appends next round.
4. With 174 monthly IS points the Sharpe SE is ~0.26 — most Stage-1 gaps are inside noise;
   the locked rank metric decides, but the noise floor belongs next to the board.

## Cleared for Stage-1 ranking
team-01, team-02, team-03, team-04, team-05, team-06 (post-amendment), team-07, team-09, team-10.
Not ranked: team-08 (DNF).
