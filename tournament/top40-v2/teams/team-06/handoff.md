# Team 06 handoff

Status: remediated but **blocked pending organizer A5 freeze; not registered, run, or qualified**.
There are no performance results or evidence hashes.

## Frozen design

- Family: `t06-balanced-trend-reversal-v1`; seed: `20260801`.
- Canonical bars: `RangeIndex` with `open_time` and `close`; only
  `open_time + 8h <= decision_time` is admitted.
- Direct score boundary: one call to
  `crypto_trade.tournament.score_adapter_protocol_v5.score_boundary` on a finite built-in score
  dictionary after transforms and before selection; returned scores drive construction.
- Exposure: gross <= 0.48, absolute net <= 0.04, symbol <= 0.07.
- Initial policy: top-level `risk_policy.json` (no control).
- Conditional combined policy: `risk_policies/combined.json`.
- Evidence folds: six organizer-derived equal chronological slices; no Team06 dates or hashes.

## Required organizer sequence

1. Complete `candidate_contract.template.json` and `candidate_manifest.template.json` from final
   authoritative bytes. Run the A5 capture replay, prove before/after bytes identical, and freeze
   those records. **Do not register anything before this is complete.**
2. Fill and register the family and initial trial templates from frozen bytes. The initial trial
   uses the top-level no-control policy and emits 1x/2x cost views from one run.
3. Apply every positive no-control core minimum in `trial_plan.json`. Any failure rejects this
   family; controls cannot rescue negative alpha.
4. Only after core pass, register all three single controls and combined control before reading
   any result. Run as one batch; each material run has 1x/2x views. Do not select among policies.
5. Apply every full qualification and attribution gate to the combined candidate.
6. Only after combined full-gate pass, register/run all four neighbors under combined policy as a
   batch. Require >=3/4 profitable and median Sharpe >=0.50; neighbors cannot replace the base.
7. Have the organizer derive the six equal chronological slices, fill only produced fold paths and
   hashes in a copy of `walk_forward_manifest.template.json`, and stitch each observation once.
8. Run the integration contract in `synthetic_test_plan.md` and require two clean-worker byte and
   output reproductions before any private ticket.

The plan consumes at most nine material configurations: one no-control core, three single
controls, one combined control, and four neighbors. Doubled cost is always a view, never a trial.
Template angle-bracket values are deliberately unfilled and are not evidence.
