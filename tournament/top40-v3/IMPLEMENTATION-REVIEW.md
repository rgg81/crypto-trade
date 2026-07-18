# Top40 V3 implementation review record

Review date: 2026-07-18
Scope: activated V3 training laboratory, Phase-0 authority, runner/worker boundary, pure-crypto
binding, journal transaction, candidate identity, coaching packet, and restart recovery.

## Independent review passes

Two read-only review passes were performed independently of the implementation tasks:

- `phase0_coherence_review` audited activation, configuration semantics, Phase-0 scope and crash
  recovery, authority paths, transitive dependencies, and policy/implementation consistency.
- `runner_static_review` audited runner/worker isolation, source reproducibility, artifact
  durability, coaching integration, restart behavior, and first-real-run environmental risks.

The reviewers did not execute tests, strategies, or evaluators and did not modify files. Their
findings were resolved prospectively before Phase 0; the canonical targeted suite and A6 audit
remain the executable acceptance evidence in `phase0-freeze.json`.

## Resolved findings

- Activated config, V3-only entrypoint, schedule authority, and semantic contract are mutually
  consistent; sealed validation, private, and final commands remain absent.
- Phase 0 freezes shared infrastructure and policy, not mutable team research lanes. Each trial
  independently binds its exact candidate source, config, risk, dependencies, evaluator, and data.
- Candidate trees are captured in durable content-addressed source archives. Top-level candidates
  exclude nested sibling candidates from their identity; nested candidates own their recursive
  directory. The worker-staged manifest must exactly match the archive.
- A real synthetic worker canary exercises namespaces, mounts, staged venv, Landlock, seccomp,
  protocol initialization, one decision, and clean shutdown before any team trial is accepted.
- A request is fsynced before execution and its success, failure, abort, artifacts, and resources
  are terminally journaled before disclosure. A restart-pending request is attributable and
  recoverable without resetting its trial count or reusing its run ID.
- Phase-0 publication uses its record as the final commit marker and recognizes only verified
  crash prefixes. Runner report files and directory promotions are fsynced before publication.
- Journal field names match the actual request/terminal schemas. The coaching packet matches the
  active train policy and reports RED/AMBER/GREEN gaps without claiming validation or nomination.
- V3 layout paths, `.python-version`, dependency lock, evaluator modules, and the A6 transitive V2
  contract dependency are frozen explicitly. The A6 snapshot remains read-only and V2 state is
  never inherited.

## Deliberate activation boundaries

- The active train CLI treats every invocation, including identical bytes, as a material trial.
  No special train replay mode is active.
- Diagnostic scoring is frozen as public-stage policy but is not a hidden train gate. Public,
  validation, private, and final command surfaces require their own prospective implementation
  review before activation.
- Candidate quality is not guaranteed by static review. It is established through serialized,
  fully logged IS work, scarce sealed probes, fixed public core floors, and uncompromised OOS.

Review disposition: **accepted for Phase 0 conditional on the exact targeted suite and A6 audit
passing without skip, fallback, or authority drift.**
