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
review attests that the direct hook receives the declared ranking signal at the declared boundary;
it remains nonautomatic evidence, not runtime proof or a qualification gate.

The registration opt-in at `parameters._top40_v2_score_adapter` binds adapter ID
`top40-v2-declared-score-boundary-v1` and the manifest SHA-256. Derived, immutable paths bind the
manifest and `<candidate>.semantic-coupling-review.json`; both exact files must be in the manifest
and registration trees. Source, strategy, risk, seed, config, shared development snapshot,
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
directory rename. A retry validates and returns an exact complete transaction; partial or extra
canonical files fail closed. Failed runs publish only a terminal result in the same transaction.

Freeze authority requires a strict implementation → independent-review → freeze commit order,
unique immutable review/freeze first-adds, exact reviewed implementation and review bytes in the
freeze tree, and the exact activation journal count/head in that tree. The draft SHA-pins parent
modules/entrypoint and checks callable identities before and after execution.

The draft entrypoint is `scripts/top40_v2_amendment_0005_draft.py`. It is not wired into the active
runner. Execution remains disabled until a new independent approval and immutable freeze exist.
