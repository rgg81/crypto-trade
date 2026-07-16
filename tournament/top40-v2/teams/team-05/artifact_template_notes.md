# Artifact template notes

Files ending in `.template.json` are inputs for the organizer to materialize; they are not frozen
evidence. Uppercase `REPLACE_WITH...` values intentionally fail the official SHA/timestamp/number
schemas so an incomplete draft cannot be mistaken for a valid artifact.

- Set the family timestamp at actual organizer registration and journal the family before any run.
- Each activated risk policy and neighbor gets one trial registration and candidate ID; every
  evaluator run emits both base- and doubled-cost evidence.
- `walk_forward_manifest.template.json`, `fold_declaration.template.json`, and
  `model_artifact.template.json` are candidate-generic source templates, never base-candidate
  evidence. Materialize one complete candidate-specific set for the no-control
  `team05-crtr-core-v1`/`risk_policy.json` run and a separate complete set for the eventual
  combined `team05-crtr-base-v1`/`risk_ablations/combined.json` run.
- A fold declaration is materialized only after the organizer derives its exact equal
  chronological boundaries. Each matching model artifact then binds that candidate's accepted
  registration, source/config/risk/seed/cutoff bytes, fold declaration, and target artifact.
  Sharing a derivation manifest does not permit either candidate to reuse the other's manifest,
  fold/model declaration, target/return path, or artifact hash.
- The first candidate score manifest remains a placeholder until Amendment 0005 is frozen and the
  score protocol, open-to-open labels, IC artifact, and byte-invariance evidence are hash-bound.
- Each candidate-specific final walk-forward manifest uses six fold-declaration hashes, six
  model-artifact hashes, and its own stitched OOF return path/hash.
- The neighborhood manifest uses the eight prewritten parameter artifacts and eight distinct
  organizer-produced daily-return artifacts. Neighbors remain dormant until provisional base pass.
- Trial result input records failure/interruption honestly; it never substitutes private numerical
  information for the permitted pass/fail boundary.
