# Team 06 research brief — balanced trend/reversal v1

Status: active-A5/A6-bound, prospective, unregistered, and unevaluated. This document makes no
performance claim.

## Mechanism and causal contract

The family combines lagged 7-day and 30-day cross-sectional trend with 2-day reversal, a fixed
low-volatility penalty, a past-only market-direction mix, and a bounded directional tilt. At most
0.48 gross, 0.04 absolute net, and 0.07 per symbol is requested. The seed is exactly `20260801`.

At 00:00 UTC the strategy intersects the organizer's Amendment 0006-certified point-in-time pure-
crypto eligible universe with canonical worker bar frames. The organizer excludes stablecoins,
TradFi/equities, commodities/metals, and indexes even when Binance lists a perpetual contract. The
strategy deliberately does not guess asset class from symbol text. A frame is admitted only with a
`RangeIndex` and `open_time` / `close` columns. A close is available only when
`open_time + 8h <= decision_time`; a future or incomplete bar is truncated before features.
Histories are then sorted and deduplicated by `open_time`.

After every valid candidate has a finite built-in `float` score, `strategy.py` calls the directly
imported `crypto_trade.tournament.score_adapter_protocol_v5.score_boundary` exactly once with a
built-in `dict[str, float]`. This is post-transform and pre-selection, weight-cap, and risk. The
returned values drive ordering and construction. The evaluator alone owns next-open fills,
funding, costs, capacity, positions, risk state, and PnL.

The evaluator always calls zero-argument root `strategy.py:build_strategy`. Before each material
registration, the organizer commits the candidate's exact ID and declared override dictionary in
root `candidate_variant.py`; the factory rejects an unknown ID or mismatched override. Dormant
neighbor declarations do not depend on nested wrapper entrypoints.

## Frozen A5 declared-score diagnostic

The prospective score manifest declares a 24-hour schedule anchored at
`2020-02-03T00:00:00Z`, a 24-hour executable-open-to-open label, higher-score/higher-return
direction, globally pooled Pearson, and 100 minimum pairs. A5 assigns observations to its exact
half-open folds F1 `[2020-02-03, 2020-09-01)`, F2 `[2020-09-01, 2021-04-01)`, F3
`[2021-04-01, 2021-11-01)`, F4 `[2021-11-01, 2022-06-01)`, F5
`[2022-06-01, 2023-01-01)`, and F6 `[2023-01-01, 2023-07-01)`, all UTC. Labels touching or
crossing a fold end are purged. These fixed diagnostic folds do not introduce fitting: the
strategy has no learned state. A5 reports pooled and per-fold correlation as non-material evidence,
never as an automatic qualification gate.

## Noncompensatory trial sequence

Registration is prohibited until the organizer materializes the exact A5 executable-source
manifest, obtains an independent semantic-coupling review, materializes the score manifest, and
places its exact SHA-256 in the trial's registration opt-in. The active A5 entrypoint and delegated
A6 pure-crypto audit must remain exact throughout.

1. Materialize the base ID and `{}` overrides in `candidate_variant.py`, copy
   `risk_policies/no-control.json` byte-for-byte to top-level `risk_policy.json`, commit and bind
   those exact bytes, then run the no-control core first. One material run produces both 1x and 2x
   central-cost views; doubled cost is never a duplicate trial.
2. Require all broad alpha minima: aggregate net return and Sharpe strictly positive; doubled-cost
   net return and Sharpe strictly positive; bull, bear, and chop returns strictly positive;
   long/bull, short/bear, and combined/chop returns strictly positive; at least four of six frozen
   A5 folds
   positive; positive-quarter fraction at least 0.55; both sleeves clear the frozen exposure,
   activity, mean-exposure, and notional minima; positive-PnL concentration at most 0.40.
3. If any no-control minimum fails, reject the family. A single or combined control cannot rescue
   negative core alpha.
4. Only after core pass, materialize, commit, rehash, and preregister volatility-only,
   drawdown-only, turnover-only, and combined as separate historical candidate commits. Every
   candidate uses `{}` strategy overrides and copies its named template to root `risk_policy.json`.
   Run them as one fixed batch and read them together for attribution, not policy selection. Each
   run emits 1x and 2x views.
5. Apply every full development gate to the already-run combined candidate: Sharpe >= 0.75,
   annualized return >= 0, Calmar >= 0.40, drawdown <= 0.30, doubled-cost Sharpe >= 0.35,
   positive-quarter fraction >= 0.55, trial-adjusted probability positive >= 0.90, at least four
   positive folds, all frozen regime/role/sleeve gates, and concentration <= 0.40. The combined
   policy must also improve at least one declared risk failure mode without worsening maximum
   drawdown versus no-control.
6. Only after combined full-gate pass, commit each neighbor artifact's exact ID/one-axis override
   in root `candidate_variant.py`, copy the combined template to root `risk_policy.json`, rehash and
   preregister, then run all four historical commits as a batch. Require at least 3/4 profitable
   and median Sharpe >= 0.50. A neighbor cannot replace the combined base.

The maximum is nine material configurations: one no-control core, three single controls, one
combined control, and four conditional neighbors. A failed noncompensatory stage records negative
evidence and leads only to a documented pivot or DNF.

## Fixed risk policies

The evaluator reads only root `risk_policy.json`. Files under `risk_policies/` are byte templates:
the selected template must be copied to the root path before the candidate commit, registration,
and run. `risk_policies/combined.json` freezes the 18% annualized volatility target (30-day
lookback, scale 0.30–1.00), gross scales
0.75/0.45/0.25 at 10%/18%/25% drawdown, and 0.18 maximum one-way turnover. Position and time stops
are disabled, side scales are 1.0, and same-boundary reentry is false in every variant.
