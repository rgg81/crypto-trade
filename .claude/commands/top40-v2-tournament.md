---
description: Run the hash-bound Top-40 V2 qualification and finalist lifecycle
---

# Top-40 V2 tournament

Use `uv run python scripts/top40_v2_tournament.py COMMAND ...` from the repository root. Never
call the evaluator or runner module directly. Phase 0 is deliberately single-shot: validate the
deadline and every frozen threshold with the user before `freeze-phase0`.

## Bootstrap and research

1. `validate-config`
2. `init-teams`
3. Commit the pristine V2 namespace and common inputs.
4. `freeze-phase0`, then commit the Phase-0 record as the direct child of the common commit.
5. For each team, `register-family TEAM REGISTRATION.json` before its first family, and
   `pivot-team` for at most two documented mechanism changes.
6. Before every material result, `register-trial TEAM REGISTRATION.json`.
7. Prefer `run-window development TEAM CANDIDATE`: it measures resources, executes the cutoff-safe
   worker, archives artifacts, and closes the journal result. External experiments must use
   `record-trial-result` and bind real repository artifacts.
8. Use `research-status [TEAM]` to validate the organizer journal, repair only exact ledger
   prefixes, and report cumulative trials/CPU/wall time.

## Qualification

For a completed candidate, prepare the hash-bound six-fold retraining and parameter-neighborhood
manifests, then run:

```text
record-development-assessment TEAM RUNNER_RECORD.json \
  --candidate-id CANDIDATE \
  --walk-forward-manifest WALK_FORWARD.json \
  --parameter-neighborhood-manifest NEIGHBORHOOD.json
```

The organizer recomputes every statistic from canonical artifacts. A failure leaves the team in
research; it is not a submission. A pass freezes the complete candidate. `run-window private TEAM
CANDIDATE` consumes the one private ticket and publishes pass/fail-only feedback. A failed or
interrupted private run is terminal DNF.

At the deadline, terminate every pending trial result, use `withdraw-team` where appropriate, then
run `close-qualification` and `lock-finalist-cohort`. Zero finalists ends as
`no_qualified_model`; no fake submissions or ballots are created.

## Finalists and selection

1. `run-finalist TEAM` once for each locked finalist. One organizer reveal performs two internal
   deterministic replays, requires identical metrics and artifact hashes, and promotes one
   canonical result.
2. `lock-final-oos` after every finalist is complete.
3. `lock-objective` to freeze the 50 absolute + 20 relative score before jury input.
4. `lock-critic CRITIC_BALLOT.json`. The ballot must score all five 0–3 categories for every
   finalist. Any DQ allegation uses a frozen code and an exact evidence path/SHA.
5. `lock-critic-confirmations CONFIRMATION.json`. Only independently confirmed proposed codes
   disqualify. If every finalist is confirmed DQ, stop at `integrity_review_required`.
6. `lock-user-ballot USER_BALLOT.json`; every original finalist must receive an explicit 0–15
   score, including a later-DQed finalist.
7. `lock-selection` combines locked automatic scores and ballots without rescoring, appends DNF
   dispositions, and computes separate paper eligibility.
8. `freeze-winner`, then `verify-winner-freeze`. The freeze creates a prospective paper-journal
   genesis, starts at the next 8h boundary, and explicitly keeps live orders disabled.

Immutable locks must be committed before their downstream command. Never rewrite a lock, sealed
private record, reservation, canonical runner record, or paper genesis.
