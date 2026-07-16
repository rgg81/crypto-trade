# Team 06 handoff

Status: rebound to the active A5/A6 authority but **prospective, unregistered, unevaluated, and
unqualified**. There are no candidate evidence hashes or performance results.

## Active authority

- Entrypoint: `scripts/top40_v2_tournament_score_diagnostics_v5.py`, SHA-256
  `0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`.
- A5 integration freeze: commit `d2b95f610722aab65b4e67466b34efeaa3554101`, SHA-256
  `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.
- Delegated A6 integration freeze: commit `ed3af1398543dfee4a50150915dc2e37b3631fc9`,
  SHA-256 `3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34`.
- Pure-crypto audit: SHA-256
  `b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, 73,777 bytes,
  zero violations. The organizer supplies only certified native crypto coin/token membership;
  stablecoins, TradFi/equities, commodities/metals, and indexes are excluded.

## Frozen design

- Family: `t06-balanced-trend-reversal-v1`; seed: `20260801`.
- The frozen lifecycle always invokes zero-argument root `strategy.py:build_strategy`. That factory
  validates and consumes the exact ID/overrides committed in root `candidate_variant.py`; nested
  neighbor entrypoints are neither required nor supported.
- Canonical bars: `RangeIndex` with `open_time` and `close`; only
  `open_time + 8h <= decision_time` is admitted.
- Direct score boundary: one call to
  `crypto_trade.tournament.score_adapter_protocol_v5.score_boundary` on a finite built-in score
  dictionary after transforms and before selection; returned scores drive construction.
- Exposure: gross <= 0.48, absolute net <= 0.04, symbol <= 0.07.
- Runtime policy: always top-level `risk_policy.json`. The files under `risk_policies/` are inert
  source templates until the selected one is copied byte-for-byte to that root path and committed.
- Initial template: `risk_policies/no-control.json`; conditional combined template:
  `risk_policies/combined.json`.
- Declared-score diagnostic: adapter `top40-v2-declared-score-boundary-v1`, daily UTC schedule,
  24-hour executable-open label, pooled Pearson, and exact frozen A5 folds F1–F6.

## Required organizer sequence

1. For the initial candidate, write ID `t06-balanced-trend-reversal-v1-base` and `{}` overrides to
   root `candidate_variant.py`; copy `risk_policies/no-control.json` byte-for-byte to root
   `risk_policy.json`; commit those exact bytes. The root zero-argument factory and root risk path
   are the only lifecycle runtime surfaces.
2. From that historical candidate commit, finalize all executable bytes, including
   `candidate_variant.py`. Materialize the complete acyclic executable-source manifest at the
   exact canonical A5 path. Do not use hashes from these templates as evidence.
3. Have an independent reviewer inspect the complete manifest-bound source set and materialize the
   exact semantic-coupling review. Only an actual review may set its decision/findings to approval.
4. Hash that review, materialize the exact score-adapter manifest, and place its SHA-256 in the
   exact `_top40_v2_score_adapter` object nested in the trial registration `parameters`.
5. Commit the three immutable A5 control files in required order: executable-source manifest,
   semantic review, score manifest. Then fill and register the family and initial trial through the
   active A5 entrypoint. The initial trial uses the top-level no-control policy and emits 1x/2x
   cost views from one run.
6. Apply every positive no-control core minimum in `trial_plan.json`. Any failure rejects this
   family; controls cannot rescue negative alpha.
7. Only after core pass, materialize each of the three single controls and combined control exactly
   as declared in `trial_plan.json`: write its ID with `{}` overrides to `candidate_variant.py`,
   copy its policy template to root `risk_policy.json`, commit, rederive its hashes/A5 controls,
   and register its historical commit. Register all four before running any; read results only
   after the batch is terminal. Each material run has 1x/2x views. Do not select among policies.
8. Apply every full qualification and attribution gate to the combined candidate.
9. Only after combined full-gate pass, materialize each neighbor's exact one-axis override in
   root `candidate_variant.py` and the combined template at root `risk_policy.json`, then commit,
   rehash, and register all four historical commits before running any. Run them as a batch and
   require >=3/4 profitable and median Sharpe >=0.50; neighbors cannot replace the base.
10. After the completed material trial, reserve and run the A5 non-material declared-score
   diagnostic. A5 owns the F1–F6 fold assignment, fold-end purge, replay artifacts, terminal result,
   and statistics. The diagnostic is never an automatic qualification gate.
11. Run the integration contract in `synthetic_test_plan.md` and require two clean-worker byte and
    output reproductions before any private ticket.

The plan consumes at most nine material configurations: one no-control core, three single
controls, one combined control, and four neighbors. Doubled cost is always a view, never a trial.
Template angle-bracket values are deliberately invalid sentinels. No canonical A5 control file,
registration, reservation, result, or performance claim has been materialized by this handoff.
