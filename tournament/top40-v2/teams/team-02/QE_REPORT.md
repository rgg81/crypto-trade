# team-02 Directional Auction Absorption engineering report

## Outcome

Exact reference candidate `team-02-daa-reference-001` is implemented for active family
`team-02-directional-auction-absorption-v1`. Commit `e563a80a` and the frozen files under
`pivot-01/` were treated as authoritative and were not edited. No specification ambiguity remains.

The strategy applies the mandatory `t-8h` feature cutoff and exact 8-hour grid. It computes the
complete 36-return signed path-efficiency statistic and the complete three-bar, half-life-two
auction-absorption statistic from validated OHLC, quote volume, and taker-buy quote volume. It
independently average-ranks both features, blends them at fixed `0.60/0.40`, and resolves final set
ties by ASCII symbol.

The portfolio requires 24 scoreable names, selects `K=max(6,floor(N/4))` on both sides, requests
equal `0.40/0.40` budgets, leaves cap-constrained capacity in cash, and uses equal name magnitudes
under the 6% cap. There is no common-market factor, beta, residual, funding feature, market state,
directional side tilt, inverse-volatility weighting, fill logic, or risk-state logic.

`build_strategy()` returns a fresh object and accepts only canonical runtime seed `20260801`.
Off-grid or insufficient scheduled inputs request flat `{}`; valid non-rebalance boundaries return
`None` to hold. `risk_policy.json` is the exact disabled no-control policy identified as
`team-02-daa-reference-no-control`.

## Verification

The synthetic suite passes `19/19` cases under the official `.venv`. Coverage includes causal
append/corrupt/truncate invariance, exact timing, closed-bar availability, feature formulas,
field validation, smoothing, ranks, numeric and membership ties, selection, capacity cash, equal
allocation, cap/gross/net invariants, invalid and duplicate rows, membership, seed enforcement,
context immutability, and clean-process determinism.

An isolated official V2 worker smoke also passed using only synthetic transaction bars, empty
funding, synthetic point-in-time membership, and one scheduled decision. Its target bytes exactly
matched the direct clean-process target.

- strategy SHA-256:
  `d1d031e717031455ef93decbc990f1f55e0703abee26dd885763a2ec4191ffd4`
- frozen config SHA-256:
  `f5b2a316b74c43323a6d38cf674c05422f6161e150bb3d624095267baa224e5b`
- no-control risk policy SHA-256:
  `0c90e21388df81f4a4a045c8d8a86ac61d178f14779987cc53883f5531556a52`
- synthetic target SHA-256:
  `8f3f92958586e57d96019abee2c65a36e88d5996bb428feb82fe0a689ea9ac89`
- synthetic target: seven longs, seven shorts, gross `0.8`, net `0.0`

Ruff lint/format, JSON parsing, neutral risk-policy parsing, source-tree validation, and diff checks
pass. Detailed test coverage and file hashes are recorded in `test_evidence.json`.

## Scope

Changed executable/test artifacts are `strategy.py`, `frozen_config.json`, `risk_policy.json`,
`test_strategy.py`, `test_evidence.json`, and this report. Reviews, ledgers, experiment history,
family records, top-level research artifacts, and every `pivot-01/` file were preserved.

No market snapshot, development result, private/final data, evaluator, trial registration,
lifecycle mutation, another team, or external research artifact was accessed. No performance claim
is made and the candidate has not been run or registered by QE.
