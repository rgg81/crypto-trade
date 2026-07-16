# Top-40 V2 Amendment 0005 — prospective declared-score diagnostics

Status: **DRAFT — INDEPENDENT REVIEW AND FREEZE REQUIRED**

This additive draft applies only to prospective, explicitly opted-in Team04–Team10 development
candidates registered after activation. Team03, preactivation registrations, private/final data,
and candidates without the exact opt-in are excluded. It changes no frozen tournament rule,
budget, evaluator, cost, target, journal, state, or active entrypoint.

The diagnostic is deliberately named a **declared-score diagnostic**. Runtime proves the exact
captured bytes, manifest schedule, deterministic replay, archived-target equivalence, labeling,
and statistic. Runtime does not prove that the captured dictionary is the model's operative
ranking signal, is economically meaningful, or is semantically before selection/weighting/risk.
A decoy or transient score can satisfy runtime checks. Semantic coupling therefore requires a
candidate-specific static source review whose exact SHA-256 is in the preregistered manifest. The
review binds an acyclic executable-source manifest listing every registered `.py`, staged strategy
configuration, and `risk_policy.json`; those bytes are proved at review, manifest, and registration
commits. The review attests that the direct hook receives the declared ranking signal at the declared boundary;
it remains nonautomatic evidence, not runtime proof or a qualification gate.

The registration opt-in at `parameters._top40_v2_score_adapter` binds adapter ID
`top40-v2-declared-score-boundary-v1` and the manifest SHA-256. Derived, immutable paths bind the
manifest, `<candidate>.executable-source-manifest.json`, and
`<candidate>.semantic-coupling-review.json`; all exact files must be in the manifest and
registration trees. Source, strategy, risk, seed, config, shared development snapshot,
archived targets, runner record, registration event, and result event are hash-bound. Registration
commit/event and result event must be strictly after the activation boundary.

Two fresh sandbox replays capture the candidate-declared dictionary and targets. Captured bytes and
targets must be exact across replays, and both targets must exactly equal archived development
targets. The snapshot manifest is reread after replay, snapshot hashes are rechecked, and every
captured Amendment 0001 helper identity is checked. The fixed statistic is pooled Pearson on
manifest-horizon executable open-to-open returns, globally and in each frozen fold, with fold-end
purging and the preregistered minimum-pair count.

Reservation and execution derive every stage, source, target, review, staging, result, and evidence
path; callers supply only team and candidate. The engine stages bounded single-link artifacts in a
mode-0700 directory behind an internally generated capability. After replay, the canonical state
lock is acquired and exact config, research phase, state bytes, journal head/count, and candidate
authority are reverified. Artifacts plus `terminal-result.json` are then published by one atomic
dirfd-based Linux `RENAME_NOREPLACE`. The frozen A2 facade receives only its exact four-field
outcome; the staging capability crosses through a trusted closure and is removed after any A2 or
final-state rejection. A retry validates and returns an exact complete transaction; partial or extra
canonical files fail closed. Failed runs publish only a terminal result in the same transaction.

Amendment freeze authority requires a strict implementation → independent-review → freeze commit
order, unique immutable review/freeze first-adds, and exact reviewed implementation and review
bytes in the freeze tree. That freeze alone is deliberately **frozen-pending-integration** and
cannot authorize reservation or execution. A separate integration authority requires a strict
amendment-freeze → integration-draft → independent-integration-review → integration-freeze commit
order with unique first-adds and exact authority bytes in every applicable tree. Only the
integration freeze records the activation journal count/head, validated with canonical zero-based
sequences; it is the sole prospective registration boundary. The draft SHA-pins parent
modules/entrypoint and checks callable identities before and after execution. It also pins the
active Amendment 0006 implementation, pure-crypto audit module, entrypoint, freeze,
integration-freeze, strict ancestry, and activation journal, and requires the exact canonical A6
pure-crypto audit before and after every A5 lifecycle operation.

The integration candidate is a prospective superset dispatcher at
`scripts/top40_v2_tournament_score_diagnostics_v5.py`. Its three non-conflicting commands are
`amendment-0005-status`, `amendment-0005-reserve-development-score-diagnostic`, and
`amendment-0005-run-development-score-diagnostic`; every other argument vector is delegated
unchanged to the exact frozen Amendment 0006 runner. Integration draft, review, and freeze must pin
the new entrypoint/module bytes and the Amendment 0006 integration freeze, while recording the
Amendment 0006 entrypoint as `superseded-unchanged`. A private identity capability held by that
dispatcher is mandatory for reservation and execution, and exact active integration plus A6 audit
authority is checked before and after each result-bearing call.

Publication assumes the tournament process controls its own Unix UID. A hostile process running as
the same UID can mutate files outside the lifecycle lock; such writers are out of scope. Even then,
`RENAME_NOREPLACE` prevents this lifecycle from silently replacing a raced destination, and every
existing transaction is fully revalidated before it can be returned.

The draft sidecar remains `scripts/top40_v2_amendment_0005_draft.py`. Its `status` command is
read-only; its mutating commands intentionally lack the private integration capability and fail
closed. Execution remains disabled until both independent amendment review/freeze and independent
integration draft/review/freeze authorities exist. No integration authority JSON is supplied by
this implementation draft.
