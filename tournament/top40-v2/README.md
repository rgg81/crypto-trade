# Top-40 V2

Top-40 V2 is a qualification tournament for ten independent crypto-futures research teams. It
reuses the immutable V1 Binance snapshot and proven execution infrastructure by hash, while its
rules, lifecycle, team namespaces, reports, locks, and evaluator extensions are separate.

The tournament starts with ten teams but does not require ten finalists. A failed hypothesis is
recorded as research evidence; it cannot be frozen as a tournament submission. A team must
continue, pivot within its cumulative budget, or finish with an auditable DNF.

## Lifecycle

```text
phase0
  -> research
  -> qualification_closed
  -> finalist_cohort_frozen
  -> oos_revealed
  -> objective_locked
  -> critic_locked
  -> dq_confirmed | integrity_review_required
  -> user_locked
  -> selection_locked
  -> paper_frozen

phase0 -> research -> qualification_closed -> no_qualified_model
```

Team lifecycle:

```text
researching
  -> qualifier_candidate_frozen
  -> qualified | dnf
  -> finalist_frozen
  -> canonical_running
  -> canonical_complete | canonical_failed
```

The intended organizer CLI is `scripts/top40_v2_tournament.py`. Phase 0 must not be frozen until
the proposed deadline, numerical gates, risk-policy contract, and sealed-window isolation have
all been reviewed and accepted.

## Non-negotiable rules

- Development qualification uses chronological, stitched out-of-fold evidence.
- A team that fails qualification cannot submit its least-bad candidate.
- The private qualifier is one-shot and returns pass/fail only before the finalist cohort lock.
- No team may inspect final-OOS metrics before every team is terminal and the finalist cohort is
  committed.
- DNF teams remain in the final report but receive no fabricated scores or OOS metrics.
- With zero qualified finalists the correct terminal result is `no_qualified_model`.
- Risk controls use authoritative evaluator state, execute no earlier than the next open, pay
  ordinary costs, and share participation capacity with strategy orders.
- V1 files and records remain immutable and out of bounds to V2 competitors.

## Snapshot reuse

V2 deliberately references the exact V1 canonical snapshot rather than duplicating large data
files. Its Phase-0 record must bind the shared manifest and every canonical file SHA-256, plus the
V2 config, V2 evaluator, and V2 methodology. Reuse does not make the 2024-2026 interval globally
untouched; it is only sealed from fresh V2 teams. Prospective paper data remains the first truly
untouched temporal evidence.
