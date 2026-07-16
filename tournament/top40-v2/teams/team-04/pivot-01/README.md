# Team 04 pivot 01 package

Status: `PROMOTED_VALIDATED_NOT_REGISTERED_NOT_EVALUATED`

The prospective authority is now active. Every future tournament command must use
`scripts/top40_v2_tournament_score_diagnostics_v5.py`, exact SHA-256
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`. Its Amendment 0005
integration freeze is commit `d2b95f610722aab65b4e67466b34efeaa3554101`, file SHA-256
`b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.

That dispatcher delegates ordinary tournament operations through active Amendment 0006. The
universe therefore remains the audited pure-crypto-only universe: no stablecoins, direct TradFi,
equities, indexes, metals, commodities, or other direct non-crypto exposures. The A6 integration
freeze is commit `ed3af1398543dfee4a50150915dc2e37b3631fc9`, SHA-256
`3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34`; its canonical passing
report SHA-256 is `b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`.

Canonical proposed bytes are local to this directory:

- `strategy.py`: BER strategy with the prospective organizer-owned A5 `score_boundary` hook at the
  exact post-rank/pre-selection boundary.
- `organizer_score_adapter.py`: deprecated noncanonical audit serializer retained for byte-level
  tests only; it is not promoted, registered, or executed for official score IC.
- `test_strategy.py`: synthetic tests, passed from both pivot-local and promoted-root layouts.
- `frozen_config.json` and `risk_policy.json`: exact candidate and disabled control policy.
- `family-registration-input.json` and `trial-registration-input.template.json`: exact active
  family/trial schema shapes with event-time/zero sentinels that the organizer must replace only
  in materialized organizer-input copies outside the candidate tree.
- `executable-source-manifest.template.json`: exact A5 executable-source schema shape and the
  anticipated complete executable path set after canonical promotion; all sizes and hashes are
  zero sentinels.
- `semantic-coupling-review.template.json`: exact A5 review schema shape only. Its forced approval
  constants, placeholder reviewer/event time, and zero hashes are not a review or evidence.
- `score-adapter-manifest.template.json`: exact A5 score-manifest schema shape for the 48-hour BER
  schedule/label; its semantic-review digest is a zero sentinel. Its literal
  `1970-01-01T00:00:00Z` schedule anchor is real immutable authority, not a sentinel.
- `prospective-a5-score-opt-in.template.json`: the exact three-field A5 registration parameter
  shape; its manifest digest is a zero sentinel.
- `research_brief.md`, `feature_lineage.json`, `ablations.json`,
  `parameter_neighborhood.json`, and `provenance.md`: preregistered research record.
- `test_evidence.json` and `validation_commands.json`: accurate serialized validation evidence.

The historical top-level UTC bytes remain preserved in Git history. The working top-level runtime
files now contain the reviewed byte-identical BER promotion. `../active-pivot.json` is metadata
only. One material Team 04 trial was already consumed by the stopped UTC reference; registering
BER would be material trial 2. This promotion did not edit either organizer ledger.

The organizer must complete the following immutable order through material trial registration:

1. **Completed.** Promote byte-identical reviewed `strategy.py`, `frozen_config.json`, `test_strategy.py`, and
   `risk_policy.json` to the canonical Team 04 top-level paths required by ordinary `run-window`.
   A nested `pivot-01/strategy.py` is not a lifecycle entrypoint. The test is deliberately
   layout-aware: from the promoted path it loads root `strategy.py`, `frozen_config.json`, and
   `risk_policy.json`, while resolving template/audit support under `pivot-01`. Do not promote
   `organizer_score_adapter.py`, and validate the canonical top-level test path serially before
   hashing. Both pivot-local and promoted-root suites passed 14 tests, and both risk paths passed
   the organizer validator.
2. Derive every staged `.py`/strategy-config file plus top-level `risk_policy.json`, materialize
   the executable-source template with exact sizes/hashes, and first-add it at
   `score-adapters/team-04-ber-reference-001.executable-source-manifest.json`. Frozen A5 treats
   every `.py` under the Team 04 tree as staged, so the unpromoted pivot audit serializer remains
   hash-bound in this complete set even though the worker never imports it as an official adapter.
3. Obtain an independent static review of that exact complete executable set and first-add the
   truthful review at the derived A5 semantic-review path. The template is never that review.
4. Hash the review, materialize and first-add the canonical score-adapter manifest, preserving its
   literal epoch anchor exactly, and prepare its SHA-256 for the trial opt-in.
5. Materialize `family-registration-input.json` outside the Team 04 tree, replacing only its
   `registered_at_utc` event placeholder, and explicitly run `pivot-team team-04` through the
   active A5 dispatcher. BER must exist in `families.jsonl` before trial registration. This family
   append changes the complete Team 04 source tree and therefore must precede its final hash.
6. After promotion, all canonical A5 control first-adds, and BER family registration, run the
   serialized canonical validations and then compute the final complete Team 04 source-tree
   fingerprint plus canonical strategy, config, and risk hashes. Do not edit any candidate-tree
   byte afterward.
7. Materialize the trial input outside the Team 04 tree from
   `trial-registration-input.template.json`; replace its trial event timestamp and zero digests,
   including the exact score-manifest opt-in digest and final post-family source fingerprint. Then,
   and only then, register BER as Team 04 material trial 2 through the active A5 dispatcher.

The epoch values in `registered_at_utc`, `timestamp_utc`, and `reviewed_at_utc` are template event
placeholders. The epoch value in `schedule_utc.anchor_timestamp_utc` is not replaced. No placeholder
file, zero digest, family/trial template, or review-shaped template is registration evidence. No
registration, evaluation, diagnostic result, or performance claim is made here.
