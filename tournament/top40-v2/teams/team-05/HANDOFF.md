# Team 05 handoff

Outcome: one independent, performance-blind family is rebound to the active A5/A6 authority for
QR/QE review, not registration or execution. The former Amendment 0005 freeze blocker is resolved.
The active entrypoint is `scripts/top40_v2_tournament_score_diagnostics_v5.py` at
`0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`; the controlling A5
integration freeze is commit `d2b95f610722aab65b4e67466b34efeaa3554101` with SHA-256
`b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.
`strategy.py` implements a deterministic long/short 20d/60d residual-trend signal with a causal
3d reversal term that strengthens in chop, 0.60 requested gross, ±0.08 maximum net tilt, and 0.04
symbol caps. `risk_policy.json` is the required initial no-control policy;
`risk_ablations/combined.json` immutably declares conservative volatility, drawdown, stop,
cooldown, and turnover controls for gated promotion.

Review in this order:

1. `research_brief.md`, `SCORE-ADAPTER-CONTRACT.md`, `candidate_score_contract.json`, and
   `feature_lineage.json`.
2. `candidate_variant.py`, `strategy.py`, then the unexecuted `test_strategy.py` and
   `test_risk_policy_contract.py`.
3. `frozen_config.json`, `risk_policy.json`, `ablations.json`, `trial_plan.json`,
   `walk_forward_plan.json`, and `parameter_neighborhood.json`.
4. `provenance.md`, `source_bindings.draft.json`, and the registration/manifest templates,
   especially the three A5 templates for the core candidate.

Required organizer actions, in order:

1. Resolve review comments without using performance evidence; any material change requires
   updating all mirrored declarations before registration.
2. Reverify the exact active A5 integration-freeze bytes/commit, active entrypoint bytes, delegated
   A6 integration authority, and zero-violation pure-crypto report before every result-bearing
   command. Use only the active A5 entrypoint; it delegates ordinary tournament commands through
   A6's pure-crypto enforcement.
3. Verify JSON/schema validity, source/config parity, synthetic tests, and the central integration
   checklist in `qe_test_plan.md`. This authority-rebind edit executed none of them.
4. Set the actual family registration time and register
   `family_registration.template.json` through the organizer lifecycle. Do not hand-edit
   `families.jsonl`. This must happen before the final source-bundle fingerprint because the
   canonical family projection participates in that fingerprint.
5. Freeze the final core candidate tree, then materialize its A5 files in this strict ancestry
   order: complete executable-source manifest; independent semantic-coupling review; score-adapter
   manifest. Each file must be a canonical immutable first-add, and the executable dependency
   bytes must remain exact at the semantic-review, score-manifest, and later registration commits.
   The complete core set currently contains `candidate_variant.py`, `frozen_config.json`,
   `risk_policy.json`, `strategy.py`, `test_risk_policy_contract.py`, and `test_strategy.py`.
6. After the family projection and all three A5 artifacts are present, replace every
   `REPLACE_WITH...`/`RECOMPUTE...` placeholder and compute the final source-bundle, source,
   config, risk, dependency, fold-model, target, return, and manifest hashes. Do not invent or
   prefill material evidence. Then register the core with the exact
   `_top40_v2_score_adapter` opt-in bound to the materialized score-manifest SHA-256.
7. Run the registered no-control core first. Only if every preregistered broad positive alpha
   minimum passes may the single-control and combined policies activate. Each policy run produces
   base and doubled costs and is one material configuration.
   For each later material candidate, first replace `candidate_variant.py` with that candidate's
   exact predeclared ID, overrides, and risk-template declaration, then copy those template bytes to the canonical
   top-level `risk_policy.json`; commit, rederive the complete source set, and bind fresh hashes
   before registration. The frozen lifecycle selects neither nested strategy entrypoints nor
   `risk_ablations/` paths.
8. Require every non-neighborhood official hard gate plus Team-05's stricter 25% drawdown, 5/6
   fold, and 35% PnL concentration gates for a provisional combined-policy base pass.
9. Only after that provisional base pass, activate the eight immutable one-axis neighbors. Require
   at least 6/8 profitable and median Sharpe ≥ 0.55; failed or interrupted neighbors stay in the
   denominator.
10. Freeze/consume the private ticket only after complete passing evidence and hash-bound manifests.
   A development or private failure is not a submission.

The A6 canonical report bound by the active chain is 73,777 bytes with SHA-256
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, policy SHA-256
`2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`, and zero
violations. Team05 consumes only `DecisionContext.eligible_symbols` and has no local universe
expansion or symbol override.

The missing charter was reported and acknowledged. The exact V2 README was separately authorized;
no search for a substitute occurred. No performance data was inspected.
