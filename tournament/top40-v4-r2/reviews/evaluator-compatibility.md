# Adversarial evaluator, data, activation, and compatibility re-review

Review date: 2026-08-20
Scope: exact current Top-40 V4-R2 bytes and pretrial runtime state after launcher-v8 and incident-
recovery remediation. This independent review inspected activation supersession, crash durability,
model/result admission, frozen-scope binding, July-inclusive data, A6, evaluator/scoring/source
boundaries, and R1 external behavior. It did not modify implementation/runtime artifacts and did
not perform a broad snapshot replay or strategy backtest.

## Gate status

**PASSED. Unresolved findings: 0.**

The implementation is ready for the controlled pretrial recovery, fresh committed v8 activation,
and one Team-01 discovery retry. The old activation remains intentionally invalid until that
procedure is executed; no model or evaluator can run under it. No team trial has been accepted.

## Pretrial activation recovery

The previously blocking v7 authority state now has a narrow, evidence-preserving transition:

- Recovery requires the exact superseded activation file
  `d1b4aa7242b2085e9455ac7628672e7f6bc9826e3e4559f87f8d88a87db53aef`, activation record
  `c2777fbe3aa1ea80e86e35f346e771bccf0dfdb892c2c2bb8b3d0aaf3355d654`, activation-test output
  `66d244083e4c8b9ddf35c9c3c583ad96c58f37bd5073d60b3fed9596dc4843bb`, and Team-01 v7 launch
  authority `726ed7f538e4c49c5c98a3a35a80f7948631cf47091c99b791202d72dcdf2bc5`.
- Before the first mutation, it preflights all four old authorities, including the embedded old
  activation record identity. Evidence reads are bounded, non-following descriptor reads with
  regular-file, link-count, repeated-`fstat`, and final lexical-identity checks. JSON identities
  are parsed from those exact captured bytes with duplicate-key and nonfinite-value rejection. A
  lone active or staged candidate must have exactly one link; an nlink-2 candidate is accepted only
  when both names exist, both have two links, and their device/inode identities match. Regressions
  cover unrelated duplicates for each authority and a staged-only external alias, and require
  rejection before any earlier authority moves.
- It also requires a byte-empty valid journal; all 15 lanes in their exact seed-only state; no
  nomination, selection, certificate, IS report, source archive, historical output, candidate,
  outbox, or feedback; and a research-session tree containing only the known v7 launch path and
  its empty parent directories. Unexpected or mismatched evidence fails before an authority moves.
- Stage one durably creates each missing incident directory and parent, archives and verifies the
  old activation/test bytes, and publishes a self-hashed prepared receipt. The stale immutable v7
  launch remains active and incompatible with launcher v8, so it continues to fail closed.
- Canonical restart recognizes the exact prepared receipt before interpreting a fresh activation
  as superseded evidence. A committed successor must validate and bind its exact successful test
  output; an output-only activation crash is treated as non-authoritative scratch and is safely
  replaced by the activation rerun. Restart is covered with both one-name and same-inode two-name
  stale-launch states.
- A fresh activation may then be published only from clean committed v8 frozen scope, three passed
  exact-byte review reports, the aggregate review record, focused tests, A6, and the full July-
  inclusive snapshot. Completion validates that new activation before moving the stale launch.
- Authority moves persist the exact regular destination file, then its directory, before the
  source directory removal. If a crash exposes both names, identical expected bytes resume by
  retaining the verified archive and durably removing only the redundant source. An nlink-2
  duplicate is accepted only when both names resolve to the same device/inode; unrelated hard-link
  topology, differing bytes, and unsafe nodes reject before source mutation. Full prepare and
  completion regressions exercise activation and launch same-inode crash recovery.
- The final atomic directory rename publishes an exact five-file archive surface: the three
  superseded authorities, prepared receipt, and completed incident manifest. Admission rechecks
  the archived hashes, both self-hashes, exact tracked model-smoke receipt, expected v7/v8 identity,
  the exact incident reason, and the current validated activation file/record/implementation-commit
  binding from the same stable activation payload. Missing, extra, symlinked, hard-linked,
  corrupted, self-consistently rewritten, or mismatched evidence fails closed.
- Every R2 model launch and every result-bearing entrypoint requires the completed incident
  authority. Result commands check it before broker acquisition and repeat it under broker/result
  locks, alongside activation validation. Therefore recovery cannot race an accepted trial and
  deletion/corruption of incident evidence later blocks both model and evaluator progress.

The current incident boundary matches those predicates: the journal is zero bytes; no candidate,
outbox, feedback, receipt, archive, score, nomination, selection, or release exists. The recorded
model smoke is a tracked frozen-scope receipt with SHA-256
`3d6d524c9420ff2019a2176f74845d3fd13852700d18214bc3d02b15ee863136`; its canonical record hash
is valid and binds Codex 0.148, launcher v8, the exact permission profile, approval `never`, denied
network, successful lane-local sentinel creation, and zero durable lane delta after cleanup.

## Launcher, activation, and source authority

- Launcher v8 constructs `codex exec --strict-config --ignore-user-config` before every `-c`
  security override and disabled-capability flag. It supplies no legacy `--sandbox`, explicitly
  sets approval policy `never`, and retains specific candidate/outbox/work write grants beneath a
  read-only lane. Codex 0.148 reports these as valid `exec` options; the exact prefix/ordering
  regression passes.
- The effective profile probe now requires a successful create/verify/remove operation inside the
  team's work root in addition to allowed sanitized reads, denied organizer/peer reads, denied
  cross-lane writes, denied network, and hidden host processes. Probe failure precedes launch-
  authority creation.
- Activation still binds a clean committed explicit scope, branch, current review-scope head,
  exact report hashes, focused test output, config, A6 report, full snapshot manifest, and
  implementation commit. The old activation correctly rejects the new frozen scope with
  `adversarial review does not bind the activation implementation`.
- Candidate capture remains descriptor-relative through every candidate-directory component and
  rejects symlink, FIFO, hard-link, non-regular, oversize, lexical-substitution, and parent-
  directory-substitution inputs. Pinned captured bytes become the content-addressed source archive;
  official worker staging re-verifies those archive bytes and mounts Python source only.

## July 2026, A6, and evaluator semantics

- Config, holdout, and manifest end exclusively at `2026-08-01T00:00:00Z`. The manifest SHA-256
  remains `c21fdcefc39961cd4408277e6cbb4833c31178cf86fa5d166499a3df6a8e7af7`.
- Direct column scans found 59,605 July transaction-bar rows, 42,138 July funding rows, 28,494 July
  mark rows, and 160 July membership rows, with zero rows at or after August 1. Maximum timestamps
  are July 31 16:00 for transaction bars/marks, July 31 23:00 for funding, and July 27 for weekly
  membership.
- A6 module, dependency, manifest, and membership hashes match config. Deterministic report
  regeneration remains
  `a1f9175b7728efde33d9d421b08c6cbcfe904783ba0f856b52504a28a453776e`, status `passed`, zero
  violations, 670 metadata symbols, 328 membership symbols, and 13,026 membership rows.
- Past-only context exposes only completed bars, strictly earlier funding, and current-universe
  rows. Next-executable-open fills, boundary funding on carried positions, interior funding,
  mark-based sizing, transaction-open execution, participation limits, membership/forced exits,
  policy actions, and 2x/3x cost reruns retain their tested semantics.
- Exact sign inversion remains bound to a cited baseline, matching metadata/policy/grid, and exact
  numerical target negation. Accepted failures consume multiplicity; team Bonferroni and field-
  wide adjustment remain recomputed over accepted trials before the frozen floor and deterministic
  ranking. July 2024 through July 2026 continues to supply nine calendar quarters and the frozen
  five-positive-quarter winner gate.

## R1 compatibility

The clean default-edition external-contract suite passes 24/24. R1 remains 12 teams, advances five,
uses its original paths/schema identities, and preserves its worker-visible bundle behavior. The
new in-lock incident check is explicitly R2-conditional; R1 decorated orchestrator operations no
longer inherit an R2 incident prerequisite. Launcher-v8 and pretrial recovery files are R2-specific
and do not change the shared evaluator's external behavior.

## Focused evidence

```text
R2 exact-current contract/security/recovery suite                     85 passed
Focused evaluator/risk/past-only set                                  14 passed
Source-archive boundary suite                                          5 passed
R1 clean external-contract suite                                      24 passed
Ruff on changed CLI/runtime/orchestrator/activation/test modules         passed
git diff --check                                                         passed
July rows / rows at or after 2026-08-01                    present / zero
A6 deterministic report                                      passed / zero violations
old activation under current v8 frozen scope                         rejected
R2 journal bytes / accepted trials                                      0 / 0
R2 candidate/result/disclosure artifacts                                  none
```

**Final result: PASSED, zero unresolved findings.**
