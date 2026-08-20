# Top-40 V4-R2 second-restart leakage and clean-room re-review

Review date: 2026-08-20
Reviewer: independent leakage/clean-room adversarial agent
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and evidence

This review inspected the exact second clean-restart patch in the nested `top40-v4-r4` worktree:
the expanded fresh-restart authority, isolation from both predecessor worktrees, physical genesis
admission, exact current-v8 discovery authority, activation and lock substitution boundaries,
mechanism-family semantics, broker failures, team-facing disclosures, candidate receipts, and all
previously reviewed R2 clean-room controls. It did not activate the edition or launch a team.

Executed evidence:

- Exact-current R2 contract/security/recovery suite: **109 passed**.
- R1 compatibility suite: **24 passed**.
- Ruff on the changed activation, isolation/layout, research-runtime, and test code: **passed**.
- `git diff --check`: **passed**.
- Organizer isolation audit: **passed**, exactly 15 lanes.
- Physical inspection found all 15 successor lanes seed-only, exactly 45 tracked one-byte newline
  lane markers, no journal, activation, activation-test, candidate, outbox, feedback, research
  session, nomination, source archive, selection, or competitive result artifact, and no symlink,
  FIFO, device, socket, or multiply-linked regular file in the successor tournament surface.
- The real Team-01 Codex 0.148 profile passed all six standard OS controls: sanitized reads and
  own-lane writes allowed; organizer/holdout/peer reads, peer writes, network, and host-process
  visibility denied. A separate direct profile probe denied the successor restart authority, the
  stopped first-restart activation and Team-01 outbox, and the original predecessor journal and
  Team-01 result summary.
- Fresh authority SHA-256
  `f33d4ac0fdbea88a75b8c8d8cd6f4bbbd799a4095dfbb3e9147c1c1a483d3f0b`
  is exact. Its expanded `restart_attempt` independently binds the stopped first-restart activation
  file and record, frozen implementation commit, empty journal, current-v8 discovery launch receipt,
  rejected Team-01 outbox, and eight research receipts. Those hashes matched the preserved physical
  artifacts. The receipt accurately distinguishes exact stopped runtime/model preservation from the
  first-restart tracked branch advancing after the stop.

## LC-01 — both predecessors and organizer access: closed

The effective profile is deny-by-default and exposes only the selected lane, sanitized kit, and
minimal Codex runtime. The real OS checks denied the organizer-only successor authority and private
paths in both predecessors despite their ancestor relationship. Current-root organizer, config,
holdout, Git, cross-lane, network, host-process, web, apps, plugins, and subagent boundaries remain
closed. Codex execution retains approval `never` and the frozen security-option ordering.

The authority and incident narrative are outside every readable team surface. Team-facing
mechanism documentation contains no predecessor candidate, score, result, strategy, or progress
information. Candidate attestations and prohibited-marker checks still reject legacy references.

## LC-02 — expanded authority and physical genesis: closed

The alternative authority is a bounded, no-follow, single-link, exact-hash JSON receipt in frozen
activation scope. It records no feedback disclosure and no predecessor candidate/result reuse. Its
second-attempt binding covers the original incident plus the stopped first-restart authority and
model/runtime artifacts. Missing, changed, unsafe, incomplete, arbitrary, or stale-v7 authority
blocks launch.

Activation independently proves the claim. Canonical activation creates the empty journal while
holding the hardened result lock, then exact-enumerates the entire successor tournament and reports
surfaces. Every expected file is regular, owner-controlled, single-linked, and stably read; every
intermediate directory is non-symlinked; any unlisted node rejects. The admitted surface is limited
to frozen tournament files, two frozen common reports, all 15 exact lane seeds and their committed
one-byte newline `.keep` markers, the byte-empty journal, and safe optional runtime locks.
Candidate, outbox, feedback, work, research-session, old-launch, report, source-archive,
nomination, selection, historical release, extra-file, symlink, hard-link, FIFO, and unsafe-node
residue fails before tests or freeze.

The exact seed scan repeats after focused tests. Pre-freeze `activation-tests.out` is bounded,
single-link, non-authoritative scratch, excluded from the competitive digest, and always replaced
by a complete rerun. A failing test writes no freeze. All 45 marker paths are themselves in
`FROZEN_SCOPE`; their committed size and SHA-256 feed the seed chain rather than being synthesized
as empty runtime rows. Only the journal is deliberately modeled as synthetic empty genesis.
Current bytes recompute a 94-file seed surface with chained head
`fb34ad31d82422ce8680d3dc7285978ff1d51ea2ac00dce8c826c4e459dc2e8f`.
Activation freezes mode, authority hash, empty-journal hash, lane count, file count, and that head;
runtime validation reconstructs the binding from frozen scope while allowing legitimate post-start
journal progress.

Regressions cover clean canonical activation, dirty pre-test rejection, nonempty journal, lane and
research residue, result/selection/archive residue, linked seed files, scratch retry, malformed
binding, and post-freeze validation.

## LC-03 — exact launch authority, substitution, overlap, and oracles: closed

The historically reused Team-01 discovery receipt path is not a bypass. Activation stably reads it
once, rejects the exact known v7 receipt hash, and passes those same captured bytes to the current
validator without reopening the path. Recorder and validator share one canonical payload builder;
accepted bytes must exactly encode Team-01, phase `discovery`, launcher v8, the current successor
profile and team-kit hashes, tournament identity, schema, and status. Compact, reordered,
duplicate-key, arbitrary-residue, and old-v7 encodings reject. Regression coverage substitutes the
path after stable capture and proves validation remains bound to the captured bytes.

The result lock opens parent and node descriptor-relatively with `O_NOFOLLOW`, validates owner,
regular-file and single-link identity before mutation, blocks on the kernel lock, then compares the
locked descriptor with the non-following lexical inode before truncating or writing its PID marker.
Symlink and hard-link substitutions reject without changing their target. The broker lease retains
its descriptor, identity, ownership, single-link, post-lock, and process-reentrant checks.

Activation remains the broker-lease bootstrap exception so its test child cannot deadlock, but is
result-lock serialized. Every later model/evaluator entrypoint validates activation and restart
authority before broker acquisition and repeats validation under the ordinary locks. Models exit
before evaluation, teams run serially, and pre-selection status/validate keep the constant genesis
projection rather than exposing lane or predecessor progress.

## LC-04 — mechanism and broker behavior: closed

Rules, strategy APIs, templates, and the discovery prompt agree. The first accepted mechanism prose
establishes the family epoch; ordinary variants repeat it. A `control-ablation` or `role-check` may
use more specific prose only with an accepted current-epoch parent. One genuine `mechanism-pivot`
starts the only new epoch; first-trial, no-op, and second pivots reject before acceptance. Code
orders history by durable trial number and enforces those exact parent/tag/epoch rules. Regressions
cover accepted and rejected cases.

The broker preserves the original admission exception when no accepted authority exists, re-raises
an infrastructure exception when acceptance lacks a terminal record, and normalizes only a durable
terminal candidate failure. The team process has already exited and feedback is atomic after the
whole batch, so organizer errors expose no team score/progress and fabricate no trial evidence.

## LC-05 — source receipts and prior controls: closed

No predecessor candidate or result byte is reused. Every new phase still uses the sole authorized
offline launcher, exact effective profile and kit hash, passed OS probes, and a candidate receipt
bound to the exact captured source-bundle SHA-256. Admission revalidates that receipt before
journaling. Descriptor-relative capture rejects links, FIFOs, hard links and substitution races;
the same bounded bytes become the content-addressed archive; workers execute only archived
`strategy.py`.

The compact stateless causal AST gate and exact archived-source three-scenario future
append/corruption invariance remain intact. Hidden markdown/text/encoded payloads, persistent state,
ordinal/decision-time branches, opaque literals, dynamic loading, RNG/operator substitutes, and
alternate executable files remain rejected by exact-byte gates and passing regressions.

## Gate decision

**PASSED — zero unresolved leakage or clean-room findings.** The expanded receipt exactly binds the
two stopped attempts, the successor profile denies both predecessor trees and organizer bytes, the
current-v8 discovery authority cannot be replaced by arbitrary residue or the old v7 receipt,
activation proves and freezes score-blind genesis, and substitution-sensitive locks and source
receipts fail closed before any of the 15 fresh lanes starts.
