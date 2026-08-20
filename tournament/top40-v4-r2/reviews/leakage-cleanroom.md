# Top-40 V4-R2 clean-restart leakage and clean-room re-review

Review date: 2026-08-20
Reviewer: independent leakage/clean-room adversarial agent
Gate status: **PASSED**
Unresolved findings: **0**

## Scope and evidence

This review inspected the exact clean-restart patch in the nested restart worktree: the frozen
fresh-restart authority, predecessor separation, physical genesis admission, activation and lock
substitution boundaries, mechanism-family semantics, broker failures, team-facing disclosures,
candidate receipts, and all previously reviewed R2 clean-room controls. It did not activate the
edition or launch a team.

Executed evidence:

- R2 contract/security/recovery suite: **106 passed**.
- R1 compatibility suite: **24 passed**.
- Ruff on the R2 broker, CLI, activation, isolation, layout, orchestrator, research runtime,
  runner, and tests: **passed**.
- `git diff --check`: **passed**.
- Organizer isolation audit: **passed**, exactly 15 lanes.
- Physical inspection found all 15 lanes seed-only, exactly 45 tracked one-byte newline lane
  markers, no competitive restart residue, and no symlink, FIFO, device, socket, or
  multiply-linked regular file in the R2 tournament surface.
- The real Team-01 Codex 0.148 profile passed all six standard OS controls: sanitized reads and
  own-lane writes allowed; organizer/holdout/peer reads, peer writes, network, and host-process
  visibility denied. Direct profile probes also denied the restart authority and the nested
  predecessor's journal, summary, Team-01 candidate, and Git metadata.
- Fresh authority SHA-256
  `bae6aa65e9689c6c19b302bd3284cdda118449187705b05314392ae5853b5431`
  is exact. Its predecessor activation, journal, journal head/count, two summary hashes,
  rejected-candidate outbox, research receipt, source archive, branch, and implementation commit
  independently matched the preserved predecessor.

## LC-01 — nested predecessor and organizer access: closed

The effective profile is deny-by-default and exposes only the selected lane, sanitized kit, and
minimal Codex runtime. The real OS checks denied both the organizer-only restart receipt and
predecessor paths despite their ancestor relationship. Current-root organizer, config, holdout,
Git, cross-lane, network, host-process, web, apps, plugins, and subagent boundaries remain closed.
Codex execution retains approval `never` and the frozen security-option ordering.

The authority and incident narrative are outside every readable team surface. Team-facing
mechanism documentation contains no predecessor candidate, score, result, strategy, or progress
information. Candidate attestations and prohibited-marker checks still reject legacy references.

## LC-02 — authority and physical genesis: closed

The alternative authority is a bounded, no-follow, single-link, exact-hash JSON receipt in frozen
activation scope. It records no feedback disclosure and no predecessor candidate/result reuse.
Missing, changed, unsafe, staged, or stale-v7 authority blocks launch.

Activation independently proves the claim. Canonical activation creates the empty journal while
holding the hardened result lock, then exact-enumerates the entire R2 tournament and reports
surfaces. Every expected file is regular, owner-controlled, single-linked, and stably read; every
intermediate directory is non-symlinked; any unlisted node rejects. The admitted surface is limited
to frozen tournament files, two frozen common reports, all 15 exact lane seeds and their committed
one-byte newline `.keep` markers, the byte-empty journal, and safe optional runtime locks.
Candidate, outbox, feedback, work, research-session, old-launch, report, source-archive,
nomination, selection, historical
release, extra-file, symlink, hard-link, FIFO, and unsafe-node residue fails before tests or freeze.

The exact seed scan repeats after focused tests. Pre-freeze `activation-tests.out` is bounded,
single-link, non-authoritative scratch, excluded from the competitive digest, and always replaced
by a complete rerun. A failing test writes no freeze. All 45 marker paths are themselves in
`FROZEN_SCOPE`; their committed size and SHA-256 feed the seed chain rather than being synthesized
as empty runtime rows. Only the journal is deliberately modeled as synthetic empty genesis.
Activation freezes mode, authority hash, empty-journal hash, lane count 15, seed-file count 94,
and chained surface head
`ad0594a4222679cd4ccf4abc54afb12381f8789aef3ab9b00361ddfd8bdaf9e0`. Runtime validation
reconstructs this binding from frozen scope while allowing legitimate post-start journal progress.

Regressions cover clean canonical activation, dirty pre-test rejection, nonempty journal, lane and
research residue, result/selection/archive residue, linked seed files, scratch retry, malformed
binding, and post-freeze validation.

## LC-03 — substitution, overlap, and progress oracles: closed

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

Rules, strategy APIs, templates, and the discovery prompt now agree. The first accepted mechanism
prose establishes the family epoch; ordinary variants repeat it. A `control-ablation` or
`role-check` may use more specific prose only with an accepted current-epoch parent. One genuine
`mechanism-pivot` starts the only new epoch; first-trial, no-op, and second pivots reject before
acceptance. Code orders history by durable trial number and enforces those exact parent/tag/epoch
rules. Regressions cover accepted and rejected cases.

The broker preserves the original admission exception when no accepted authority exists, re-raises
an infrastructure exception when acceptance lacks a terminal record, and normalizes only a durable
terminal candidate failure. The team process has already exited and feedback is atomic after the
whole batch, so organizer errors expose no team score/progress and fabricate no trial evidence.

## LC-05 — receipts and prior controls: closed

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

**PASSED — zero unresolved leakage or clean-room findings.** The restart receipt matches the
privately preserved predecessor, the nested team boundary denies predecessor and organizer bytes,
activation proves and freezes score-blind genesis, substitution-sensitive locks and receipts fail
closed, and the clarified mechanism/broker contract is uniform before any of 15 fresh lanes starts.
