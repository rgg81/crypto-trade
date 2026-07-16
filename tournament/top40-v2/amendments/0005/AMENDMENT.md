# Top-40 V2 Amendment 0005 — prospective development score adapters

Status: **DRAFT — INDEPENDENT REVIEW AND FREEZE REQUIRED**

This additive amendment introduces a generic organizer-owned score boundary for prospective,
explicitly opted-in candidates from Team04 through Team10. It does not cover Team03, any
registration present before activation, or any registration lacking the exact opt-in object.
Completed preactivation candidates remain unchanged. Nothing in this draft changes the frozen
Phase-0 contract, Amendments 0001–0004, active tournament entrypoint, run state, organizer
research journal, research budgets, qualification rules, evaluator, costs, or targets.

The opt-in is preregistered at
`parameters._top40_v2_score_adapter`. It binds adapter ID
`top40-v2-preconstruction-score-boundary-v1` and the SHA-256 of the candidate's derived manifest
at `tournament/top40-v2/teams/<team>/score-adapters/<candidate>.json`. The manifest and trial
registration must each be uniquely first-added and immutable. The exact manifest must already be
present in the registration commit, and the manifest commit must be an ancestor of that commit.
The registration commit and organizer-journal registration event must both be after the future
Amendment 0005 activation boundary.

Candidate code directly imports `score_boundary` from the organizer protocol and calls it once at
each manifest-scheduled decision after score transformation and before selection, weighting,
caps, or risk controls. In ordinary execution it is an identity function. Diagnostic replay
temporarily replaces only `strategy.py`'s direct binding, captures an exact built-in dictionary
of finite non-Boolean scores, delegates identity, detects mutation, limits capture to one call per
decision, enforces the UTC schedule, and restores the original binding in `finally`.

The organizer reconstructs the exact registration source tree and verifies registered strategy,
risk, and complete source-bundle hashes. It performs two fresh sandbox replays through the frozen
V2 worker boundary. Scores and targets must be bit-exact across replays; both target replays must
equal the archived targets of the completed development run. The runner record, shared snapshot,
seed, config, and development artifacts are all hash-bound.

The label is the manifest-fixed simple return from the executable open at the score timestamp to
the executable open after the declared holding horizon. The horizon is a multiple of eight hours
from 8 through 168; 48 hours is supported. Opens must be finite and positive. Labels whose end
crosses or touches a fold boundary are purged. The statistic is one globally pooled Pearson
correlation for the full development set and separately within each of the frozen six folds. The
manifest fixes a minimum pair count. These numbers are public candidate-declared diagnostic
evidence, not a universal automatic qualification gate.

Only two result-bearing commands exist:

- `reserve-development-score-diagnostic TEAM CANDIDATE`
- `run-development-score-diagnostic TEAM CANDIDATE`

The caller supplies neither a stage nor a data or output path. Both APIs derive literal
development paths and reject any state after research/private/final sealing. Each candidate has
one reservation and one terminal result. The reservation must be committed as a unique immutable
first-add before execution. The diagnostic is non-material and charges no team trial, CPU, or
wall-clock budget. Public evidence is written only beneath
`reports-top40-v2/<team>/development-score-diagnostics/<candidate>`.

The new draft entrypoint is `scripts/top40_v2_amendment_0005_draft.py`. It is deliberately not
wired into `scripts/top40_v2_tournament_active.py`. Reservation and execution remain disabled
until an independently approved `REVIEW.json` and immutable `freeze.json` bind the final
implementation bytes and activation journal prefix. Neither approval nor freeze is present in
this draft.

The gate SHA-pins and captures the Amendment 0001 scientific helpers, Amendment 0002 schema-3
facade, Amendment 0004 active runner, and Amendment 0004 active entrypoint. Parent authority is
checked before and after diagnostic execution.
