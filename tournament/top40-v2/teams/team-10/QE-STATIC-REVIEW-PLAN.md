# Team 10 QE static review plan

This is a prospective checklist, not evidence that review has passed.

1. Confirm `strategy.py` imports only standard-library, NumPy, and pandas dependencies available to
   the canonical worker; bind every executable source byte in the source-bundle manifest.
2. Verify all `StrategyConfig` fields appear identically in the frozen config, family ranges, trial
   template, ablations, and every parameter neighbor.
3. Trace close availability: `open_time + 8h <= decision_time`; ensure appended or corrupted future
   values cannot affect a target and exact 8-hour gaps cannot be compressed.
4. Confirm only Amendment-0006-supplied eligible symbols can be returned. Do not add a team-owned
   ticker denylist or accept a raw Binance listing as eligibility evidence.
5. Prove that funding, auxiliary frames, transaction opens, marks, fills, positions, equity, and
   evaluator results do not enter the signal.
6. Verify deterministic ordering, finite outputs, disjoint sleeves, 0.80 maximum gross, zero requested
   net, and 0.08 maximum weight for the five-per-side reference configuration.
7. Exercise insufficient breadth, under-history listings, stale histories, missing candles, constant
   prices, duplicate past bars, malformed past prices, reversed input order, and seed invariance.
8. Review all six declarative risk policies against the public schema and verify next-open execution,
   ordinary costs, shared participation, and same-boundary reentry prevention remain organizer-owned.
9. Confirm the risk plan counts six policies, with base and doubled costs emitted together for each;
   reject any accounting that calls those twelve material choices.
   Require root `risk_policy.json` to be byte-identical to `risk_policies/no-control.json` for the
   first material candidate. Run that core first and require positive ordinary/doubled return and
   Sharpe, at least four positive folds, positive bull/bear/chop returns, positive
   long-bull/short-bear/combined-chop attribution, and active sleeves before any control. Controls
   cannot rescue failure. For a later policy, copy its immutable template byte-for-byte to root
   before commit, registration, and run, then recompute all bindings.
10. Confirm `families.jsonl` and `experiments.jsonl` are still empty and that every generated evidence
    hash, result path, and performance field remains absent before registration/evaluation.

Any material correction after family registration requires a new prospective registration and trial
count. No result-bearing command may use the superseded historical entrypoint.
