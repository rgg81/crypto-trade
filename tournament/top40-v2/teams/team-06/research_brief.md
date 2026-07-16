# Team 06 research brief — balanced trend/reversal v1

Status: design-remediated, unregistered, unevaluated, and blocked pending the organizer A5 freeze.
This document makes no performance claim.

## Mechanism and causal contract

The family combines lagged 7-day and 30-day cross-sectional trend with 2-day reversal, a fixed
low-volatility penalty, a past-only market-direction mix, and a bounded directional tilt. At most
0.48 gross, 0.04 absolute net, and 0.07 per symbol is requested. The seed is exactly `20260801`.

At 00:00 UTC the strategy intersects the organizer's point-in-time eligible universe with
canonical worker bar frames. A frame is admitted only with a `RangeIndex` and `open_time` / `close`
columns. A close is available only when `open_time + 8h <= decision_time`; a future or incomplete
bar is truncated before features. Histories are then sorted and deduplicated by `open_time`.

After every valid candidate has a finite built-in `float` score, `strategy.py` calls the directly
imported `crypto_trade.tournament.score_adapter_protocol_v5.score_boundary` exactly once with a
built-in `dict[str, float]`. This is post-transform and pre-selection, weight-cap, and risk. The
returned values drive ordering and construction. The evaluator alone owns next-open fills,
funding, costs, capacity, positions, risk state, and PnL.

## Organizer-derived folds

Team06 does not hand-date folds. `folds/fold_declaration.template.json` tells the organizer to
enumerate its canonical visible-development observation boundaries and divide them into six
contiguous chronological slices of equal size (lengths differ by at most one; earlier folds take
the remainder). All starts, ends, training cutoffs, produced artifact paths, and hashes remain
explicit organizer placeholders. No Team06-authored hash is evidence.

## Noncompensatory trial sequence

Registration is prohibited until the organizer completes the A5 candidate-manifest / candidate-
contract freeze, fills authoritative hashes, and proves candidate bytes are invariant across the
capture replay.

1. Run the top-level `risk_policy.json` no-control core first. One material run produces both 1x
   and 2x central-cost views; doubled cost is never a duplicate trial.
2. Require all broad alpha minima: aggregate net return and Sharpe strictly positive; doubled-cost
   net return and Sharpe strictly positive; bull, bear, and chop returns strictly positive;
   long/bull, short/bear, and combined/chop returns strictly positive; at least four of six folds
   positive; positive-quarter fraction at least 0.55; both sleeves clear the frozen exposure,
   activity, mean-exposure, and notional minima; positive-PnL concentration at most 0.40.
3. If any no-control minimum fails, reject the family. A single or combined control cannot rescue
   negative core alpha.
4. Only after core pass, preregister and run volatility-only, drawdown-only, turnover-only, and the
   separately frozen combined policy as one fixed batch. Read them together for attribution, not
   policy selection. Each run emits 1x and 2x views.
5. Apply every full development gate to the already-run combined candidate: Sharpe >= 0.75,
   annualized return >= 0, Calmar >= 0.40, drawdown <= 0.30, doubled-cost Sharpe >= 0.35,
   positive-quarter fraction >= 0.55, trial-adjusted probability positive >= 0.90, at least four
   positive folds, all frozen regime/role/sleeve gates, and concentration <= 0.40. The combined
   policy must also improve at least one declared risk failure mode without worsening maximum
   drawdown versus no-control.
6. Only after combined full-gate pass, run all four preregistered one-axis neighbors under the
   combined policy. Require at least 3/4 profitable and median Sharpe >= 0.50. A neighbor cannot
   replace the combined base.

The maximum is nine material configurations: one no-control core, three single controls, one
combined control, and four conditional neighbors. A failed noncompensatory stage records negative
evidence and leads only to a documented pivot or DNF.

## Fixed risk policies

`risk_policy.json` is the initial no-control policy. `risk_policies/combined.json` separately
freezes the 18% annualized volatility target (30-day lookback, scale 0.30–1.00), gross scales
0.75/0.45/0.25 at 10%/18%/25% drawdown, and 0.18 maximum one-way turnover. Position and time stops
are disabled, side scales are 1.0, and same-boundary reentry is false in every variant.
