# Team 03 provenance

The residual-liquidity-shock-absorption family was developed independently for Team 03 inside the
Top-40 V2 visible-development boundary. No other team's V2 implementation, ledger, ballot,
leaderboard, private result, final result, or prior-tournament strategy was used to construct this
candidate.

Authorized inputs are the protocol-supplied closed 8-hour bar fields (`open_time`, `close`, and
`quote_volume`), eligible-symbol membership, and past funding fields (`funding_time`, `symbol`, and
`funding_rate`). BTCUSDT is used only as a factor anchor. The strategy does not use current fill
prices, future rows, private data, learned external artifacts, random selection, network data, or
manual overrides.

The implementation is contained in `strategy.py`; the exact candidate and no-control policy are
described by `candidate_spec.json`, `frozen_config.json`, and `risk_policy.json`. Runtime numerical
dependencies are NumPy, pandas, and the local tournament `DecisionContext` protocol. The synthetic
checks are contained in `test_strategy.py`.

No evaluator, tournament registration, development window, parameter neighbor, or risk ablation
was run while preparing this provenance record. An organizer reported a prior synthetic result of
four passes and one failed sleeve assertion. That failure led to a causal correction: beta and
residual-volatility baselines now end before the shock horizon, and raw finite scores retain their
ordering instead of collapsing at arbitrary clipping bounds. The amended suite has not yet been
rerun, so this record makes no claim that current tests pass.

All executable-source and configuration hashes must be computed only after the current synthetic
and policy checks pass and no further source edit is planned. The registration serializer remains
the authority for the strategy, source-bundle, risk-policy, and tournament-config hash bindings.
