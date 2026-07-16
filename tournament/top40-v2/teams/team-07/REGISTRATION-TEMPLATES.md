# Registration template use

The family and trial templates contain exactly the keys accepted by the frozen public schemas.
They are drafts, not registrations. Before submission, replace the epoch timestamp with the actual
UTC registration time and replace every all-zero SHA-256 sentinel with a hash computed from the
final frozen bytes. Do not add notes or status fields to either JSON object. Validate the
materialized objects, then use `scripts/top40_v2_tournament_score_diagnostics_v5.py`, the active
A5 superset entrypoint that preserves the A6 pure-crypto preflight. The organizer, not Team07,
appends families.jsonl and experiments.jsonl.
