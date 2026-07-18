# Team 05 handoff

Outcome: one independent, performance-blind family remains registered at
`2026-07-16T16:32:53Z`. Its `team05-crtr-core-v2` trial terminated before strategy initialization
because the frozen worker could not import the A5 score protocol; it produced no model metric or
artifact and remains immutable material trial 1. Frozen Amendment 0008 authorizes exactly one
scientifically unchanged replacement, `team05-crtr-core-v2-infra-r1`, as material trial 2 under
the same family. No family registration or pivot is authorized.

The active runtime entrypoint is `scripts/top40_v2_tournament_runtime_preload_v7.py` at
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`; its integration freeze is
commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, SHA-256
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`. The A8 one-shot freeze is
commit `f6003ae687d5a6bf665abb001715b01ea8b10abb`, SHA-256
`08bf194c9ade1f66bf38012210ad8604df61ca467cdad00bd3957aa679ea9bdd`.
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
2. Reverify exact A5, A6, A7, and A8 freeze/entrypoint bytes before every result-bearing command.
   Use only the active A7 entrypoint; it delegates through unchanged A5 and A6 enforcement.
3. Verify JSON/schema validity, source/config parity, synthetic tests, and the central integration
   checklist in `qe_test_plan.md`. This authority-rebind edit executed none of them.
4. Verify the already accepted family registration and its one-row canonical `families.jsonl`
   projection from commit `742aa655`; never append or register it again. Preserve that projection
   before the final source-bundle fingerprint because it participates in the fingerprint.
5. Freeze the final infra-r1 candidate tree, then materialize its fresh A5 files in this strict ancestry
   order: complete executable-source manifest; independent semantic-coupling review; score-adapter
   manifest. Each file must be a canonical immutable first-add, and the executable dependency
   bytes must remain exact at the semantic-review, score-manifest, and later registration commits.
   The complete core set currently contains `candidate_variant.py`, `frozen_config.json`,
   `risk_policy.json`, `strategy.py`, `test_risk_policy_contract.py`, and `test_strategy.py`.
6. After the family projection and all three candidate-bound A5 artifacts are present, replace every
   `REPLACE_WITH...`/`RECOMPUTE...` placeholder and compute the final source-bundle, source,
   config, risk, dependency, fold-model, target, return, and manifest hashes. Do not invent or
   prefill material evidence. Then register `team05-crtr-core-v2-infra-r1` with the exact
   `_top40_v2_score_adapter` opt-in and the exact A7/A8 authority bindings in
   `trial_registration.template.json`.
7. Run the registered no-control replacement exactly once. Only if every preregistered broad positive alpha
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
