# Artifact template notes

Files ending in `.template.json` are inputs for the organizer to materialize; they are not frozen
evidence. Uppercase `REPLACE_WITH...` values intentionally fail the official SHA/timestamp/number
schemas so an incomplete draft cannot be mistaken for a valid artifact.

- Preserve and verify the family registration accepted at `2026-07-16T16:32:53Z` before the final
  source-bundle fingerprint, any trial registration, or any run. `families.jsonl` changes the
  canonical team-tree fingerprint even though it is not an executable-source-manifest entry; do
  not register or append the family again.
- Each activated risk policy and neighbor gets one trial registration and candidate ID; every
  evaluator run emits both base- and doubled-cost evidence.
- `walk_forward_manifest.template.json`, `fold_declaration.template.json`, and
  `model_artifact.template.json` are candidate-generic source templates, never base-candidate
  evidence. Materialize one complete candidate-specific set for the no-control
  `team05-crtr-core-v2`/`risk_policy.json` run and a separate complete set for the eventual
  combined `team05-crtr-base-v1` run after `risk_ablations/combined.json` is materialized at root
  `risk_policy.json`.
- A fold declaration is materialized only after the organizer derives its exact equal
  chronological boundaries. Each matching model artifact then binds that candidate's accepted
  registration, source/config/risk/seed/cutoff bytes, fold declaration, and target artifact.
  Sharing a derivation manifest does not permit either candidate to reuse the other's manifest,
  fold/model declaration, target/return path, or artifact hash.
- Amendment 0005 is active. The three root A5 files remain prospective source templates, not
  canonical artifacts or evidence. Freeze the final Team05 executable tree and rederive the
  complete source set before replacing any placeholder.
- Materialize `executable_source_manifest.template.json` first at
  `score-adapters/team05-crtr-core-v2.executable-source-manifest.json`. Its sorted list must equal
  every registered Team05 `.py`, staged strategy configuration, and `risk_policy.json` in the
  historical tree; currently that prospective set is `candidate_variant.py`,
  `frozen_config.json`, `risk_policy.json`, `strategy.py`, `test_risk_policy_contract.py`, and
  `test_strategy.py`.
- An independent reviewer then materializes `semantic_coupling_review.template.json` at
  `score-adapters/team05-crtr-core-v2.semantic-coupling-review.json`, binding the exact complete
  source-manifest and strategy hashes. The template's fixed `approve` shape is not a present
  approval; reviewer identity, timestamp, and all five findings must be established independently.
- Only after the review first-add may the organizer materialize
  `candidate_score_manifest.template.json` at `score-adapters/team05-crtr-core-v2.json`, binding the
  review SHA. Only after that score-manifest first-add may the core registration bind its SHA under
  `parameters._top40_v2_score_adapter`. Any executable-byte change restarts the sequence.
- `trial_registration.template.json` is now intentionally candidate-specific to the first
  no-control core and carries that exact A5 opt-in. Controlled and neighbor candidates require
  separate registrations derived from `trial_plan.json`; they must not reuse the core candidate's
  manifest hash or candidate-specific opt-in.
- The lifecycle runs only root `strategy.py` and root `risk_policy.json`. For every later material
  candidate, first materialize its exact declared ID, overrides, and risk-template declaration
  into `candidate_variant.py`, then copy those template bytes to root `risk_policy.json`; commit and recompute every
  source/config/risk binding. References to `risk_ablations/*.json` identify immutable source
  declarations, not alternate runtime paths.
- The declared-score diagnostic uses exact 72-hour executable-open endpoints and globally pooled
  Pearson, with fold-end purging. Its eventual artifacts are A5-produced non-material evidence,
  not fields in the preregistered score manifest and not an automatic qualification gate.
- Each candidate-specific final walk-forward manifest uses six fold-declaration hashes, six
  model-artifact hashes, and its own stitched OOF return path/hash.
- The neighborhood manifest uses the eight prewritten parameter artifacts and eight distinct
  organizer-produced daily-return artifacts. Neighbors remain dormant until provisional base pass.
- Trial result input records failure/interruption honestly; it never substitutes private numerical
  information for the permitted pass/fail boundary.
- All result-bearing commands must use active entrypoint
  `scripts/top40_v2_tournament_score_diagnostics_v5.py` at
  `0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`. Its delegated A6
  authority permits only certified native crypto coins/tokens and rejects stablecoins,
  equities/TradFi, indexes, metals, commodities, and all other non-crypto contracts.
