# Team 04 pivot 01 package

Status: `IMPLEMENTED_NOT_REGISTERED_TESTS_NOT_RUN_NOT_EVALUATED_BLOCKED_AWAITING_A5_FREEZE`

Canonical proposed bytes are local to this directory:

- `strategy.py`: BER strategy with the prospective organizer-owned A5 `score_boundary` hook at the
  exact post-rank/pre-selection boundary.
- `organizer_score_adapter.py`: deprecated noncanonical audit serializer retained for byte-level
  tests only; it is not promoted, registered, or executed for official score IC.
- `test_strategy.py`: synthetic tests, written but not executed.
- `frozen_config.json` and `risk_policy.json`: exact candidate and disabled control policy.
- `family-registration-input.json` and `trial-registration-input.template.json`: root-owned
  registration inputs with explicit timestamp/hash placeholders.
- `source-bundle-manifest.template.json`: exact canonical and audit-only bundle membership plus
  root-owned hash placeholders.
- `prospective-a5-score-opt-in.template.json`: deliberately invalid prospective A5 opt-in; it must
  be replaced under a later frozen A5 authority before registration.
- `research_brief.md`, `feature_lineage.json`, `ablations.json`,
  `parameter_neighborhood.json`, and `provenance.md`: preregistered research record.
- `test_evidence.json` and `validation_commands.json`: accurate unrun evidence.

The historical top-level UTC files remain unchanged. `../active-pivot.json` is metadata only. An
authorized root promotion must separately copy reviewed `strategy.py`, `frozen_config.json`,
`test_strategy.py`, and `risk_policy.json` to canonical top-level paths before hashing. The audit
adapter must remain unpromoted. Registration must not begin until A5 exists, is frozen, the
prospective template is replaced by an authority-valid opt-in manifest, bundle membership is
verified, and serialized validation is complete.
