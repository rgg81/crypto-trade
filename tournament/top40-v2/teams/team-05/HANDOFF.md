# Team 05 handoff

Outcome: one independent, performance-blind family is remediated for QR/QE review, not registration
or execution. The remaining external blocker is the organizer freeze of Amendment 0005 and
`score_adapter_protocol_v5`.
`strategy.py` implements a deterministic long/short 20d/60d residual-trend signal with a causal
3d reversal term that strengthens in chop, 0.60 requested gross, ±0.08 maximum net tilt, and 0.04
symbol caps. `risk_policy.json` is the required initial no-control policy;
`risk_ablations/combined.json` immutably declares conservative volatility, drawdown, stop,
cooldown, and turnover controls for gated promotion.

Review in this order:

1. `research_brief.md`, `SCORE-ADAPTER-CONTRACT.md`, `candidate_score_contract.json`, and
   `feature_lineage.json`.
2. `strategy.py`, then the unexecuted `test_strategy.py` and `test_risk_policy_contract.py`.
3. `frozen_config.json`, `risk_policy.json`, `ablations.json`, `trial_plan.json`,
   `walk_forward_plan.json`, and `parameter_neighborhood.json`.
4. `provenance.md`, `source_bindings.draft.json`, and the registration/manifest templates.

Required organizer actions, in order:

1. Resolve review comments without using performance evidence; any material change requires
   updating all mirrored declarations before registration.
2. Verify JSON/schema validity, source/config parity, synthetic tests, and the central integration
   checklist in `qe_test_plan.md`. None has been executed here.
3. Replace every `REPLACE_WITH...` placeholder; compute exact source, config, risk, dependency,
   fold-model, target, return, and manifest hashes.
4. Freeze Amendment 0005 and its v5 protocol, then hash-bind the first-candidate score manifest,
   simple executable-open-to-open label/IC contract, and byte-invariance evidence. Registration is
   forbidden before this step.
5. Set the actual family registration time and register
   `family_registration.template.json` through the organizer lifecycle. Do not hand-edit
   `families.jsonl`.
6. Register and run the no-control core first. Only if every preregistered broad positive alpha
   minimum passes may the single-control and combined policies activate. Each policy run produces
   base and doubled costs and is one material configuration.
7. Require every non-neighborhood official hard gate plus Team-05's stricter 25% drawdown, 5/6
   fold, and 35% PnL concentration gates for a provisional combined-policy base pass.
8. Only after that provisional base pass, activate the eight immutable one-axis neighbors. Require
   at least 6/8 profitable and median Sharpe ≥ 0.55; failed or interrupted neighbors stay in the
   denominator.
9. Freeze/consume the private ticket only after complete passing evidence and hash-bound manifests.
   A development or private failure is not a submission.

The missing charter was reported and acknowledged. The exact V2 README was separately authorized;
no search for a substitute occurred. No performance data was inspected.
