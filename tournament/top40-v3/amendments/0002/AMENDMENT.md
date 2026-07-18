# Top40 V3 Amendment 0002: sealed validation activation

Status: prospective until the unique integration-freeze commit is verified.

This amendment opens exactly one validation observation for each candidate in the committed
four-team GREEN IS cohort. It does not change any split, floor, cost, seed, evaluator, universe,
or candidate identity.

## Immutable cohort

The only authorized candidates are the exact identities in
`tournament/top40-v3/is-cohort-freeze.json`. Their training metric packets, successful train
journal records, and content-addressed source archives must all agree. A mutable team working tree
is never a validation authority.

## Archive rehydration

The organizer mechanically rehydrates the original train archive into a candidate-specific
staging directory below the same team namespace. A derived content-addressed archive binds the new
staging root while retaining the exact original file manifest and source-bundle hash. Both archive
authorities are recorded before the runner may access snapshot data. Staging never overwrites the
team's live candidate and is removed after the terminal transaction.

## Probe and replay transaction

One canonical global result lock serializes validation. The accepted request embeds the exact
`lab_v3` opening-probe authorization and is appended, flushed, and fsynced before the runner is
called. Success, failure, abort, and restart all consume the probe. Every successful primary run is
followed serially by an exact private replay; logical metrics and artifact hashes must match.

## Disclosure

Runner artifacts remain under `tournament/top40-v3/private/validation` and are permission-reduced.
Per-probe commands disclose only a packet hash. The fixed aggregate packets omit raw paths, rows,
returns series, targets, positions, events, and trades. The four packets are released together only
after all four candidates have terminal records and a canonical `packet_released` event has been
fsynced. Failed candidates disclose only `validation_dnf`.

The packet contains validation-window risk and return aggregates, doubled-cost results, quarterly
aggregate returns, validation-only trade count, aggregate regime Sharpes, confidence intervals,
hard-gate status, and immutable provenance commitments. A later prospective stage may construct
the stitched train-plus-validation public assessment and nomination locks; this amendment does not
open private or final OOS data.

## Prospective evidence suite

The activation freeze reruns the current Phase-0 base suite except the historical
`test_v3_team_bundles.py` file, whose pre-tournament assertion requires all top-level candidates to
remain labeled “baseline not yet evaluated” and is no longer true after logged IS revisions. The
frozen Phase-0 evidence retains that historical test. Amendment 0002 replaces its live relevance
with exact reconstruction of the selected cohort from train journals, metric packets, and source
archives. The freeze also reruns Amendment 0001's UTC evaluator suite and the focused Amendment
0002 suite, serially, before writing its prospective record. Amendment 0001's frozen evidence
retains its original integration suite; the one live integration test that appends a hard-coded
17:00 UTC request is now historically stale because the real train journal correctly progressed
past that time. Amendment 0002 exercises the live parent verifier directly instead of weakening the
journal's monotonic-time rule.
