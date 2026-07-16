# Team 03 research decision after insolvency

Decision: consume one bounded mechanism pivot. If this pivot fails any base or stability stop rule,
Team 03 finishes DNF; no second pivot or risk-control rescue will be pursued.

This document is a research decision, not a family/trial registration and not permission to run an
evaluator.

## Pivot identity

- Proposed family: `t03-confirmed-residual-shock-absorption-v1`
- Parent family: `t03-residual-liquidity-shock-absorption-v1`
- Proposed initial candidate: `t03-crsa-base-i3-c1-b30-v21`
- Pivot count after registration: one of two allowed
- Initial policy: no controls enabled

## Changed economic hypothesis

The failed family assumed that a large, high-volume beta-residual shock was immediately
mean-reverting. The child hypothesis is narrower: forced-flow impact is tradable only after one
subsequent closed 8-hour residual has reversed sign, providing observable evidence that marginal
flow has been absorbed.

This is an alpha-timing and state-definition change. It does not inspect entry P&L, equity,
drawdown, position age, or prior losses; does not add a stop, brake, cooldown, volatility target,
or turnover limit; and does not reduce the frozen 80% gross target. It therefore cannot conceal the
failed mechanism behind a risk overlay.

## Causal base specification

At each daily `00:00 UTC` decision, using only bars fully closed by that boundary:

1. For each eligible non-BTC contract, align its 8-hour log returns with BTCUSDT.
2. Reserve the latest closed bar as the confirmation bar. The three closed bars immediately before
   it form the impulse window.
3. Estimate BTC beta from 30 days of aligned returns ending before the impulse window. Estimate
   residual volatility from 21 days ending at the same boundary. Omit insufficient or degenerate
   symbols under the existing `1e-8` floor.
4. Compute the three-bar residual impulse. Compute quote-volume surprise on that impulse against a
   30-day pre-impulse median. Use only funding events strictly before the decision, with the same
   3-day/30-day scaling and `0.25` weight.
5. A long is eligible only when the impulse residual is negative and the confirmation residual is
   strictly positive. A short is eligible only when the impulse residual is positive and the
   confirmation residual is strictly negative. Zero or non-finite confirmations are ineligible.
6. Rank eligible longs and shorts by the raw finite impulse-exhaustion score without clipping.
   Symbol order breaks exact numerical ties only.
7. Let the per-side count be the larger of six and 25% of the valid non-BTC universe, rounded down.
   Trade only when both sides contain that many confirmed candidates; otherwise request a flat
   book. BTC remains an untraded anchor.
8. Keep the original 80% gross target, 8% name cap, and 60-day BTC trend tilt of five gross
   percentage points. No risk control is enabled.

The confirmation horizon is fixed at one bar and is not tunable in this pivot. There is no
confirmation-size threshold to optimize: only the preregistered sign change is used.

## Bounded neighborhood

Only the base may run initially. The neighborhood activates only after the no-control base passes
every hard, development, fold, regime, sleeve, cost, and concentration rule below. It contains
exactly four one-axis neighbors:

- impulse horizon 1 bar;
- impulse horizon 6 bars;
- BTC-beta lookback 21 days; and
- BTC-beta lookback 45 days.

All other parameters, including the one-bar confirmation, remain frozen. No manual variant,
threshold search, risk-control variant, or replacement neighbor is allowed. The pivot consumes at
most five material configurations: one base plus four neighbors.

## Immediate base stop rules

Stop the child family and declare Team 03 DNF if the base is causal-test invalid,
nondeterministic, execution-invalid, interrupted without a valid terminal artifact, or insolvent.
No failed or missing fold may be removed, rerun, or substituted.

The complete no-control development evidence must also satisfy all of the following:

- net Sharpe at least `0.75`;
- strictly positive annualized net return;
- Calmar at least `0.40` and maximum drawdown no greater than `0.30`;
- doubled-cost Sharpe at least `0.35`;
- at least four of six chronological folds with positive net return;
- positive-quarter fraction at least `0.55`;
- trial-adjusted probability of positive performance at least `0.90`; and
- positive-PnL concentration no greater than `0.40`.

Any failure stops the pivot. Risk controls do not get an activation opportunity.

## Regime stop rules

Bull, bear, and chop must each have strictly positive net return. At least three labeled regimes
must have positive Sharpe, and the worst regime Sharpe must be at least `-0.25`. Failure in any one
of bull, bear, or chop stops the pivot even if aggregate statistics pass.

## Sleeve stop rules

The long sleeve in bull, short sleeve in bear, and combined portfolio in chop must each contribute
strictly positive net return. Both sides must independently meet every public activity floor:

- instantaneous side exposure at least `0.01` when active;
- active-bar fraction at least `0.10`;
- mean side exposure at least `0.01`; and
- executed notional at least `1000 USDT`.

Failure or inactivity on either side stops the pivot. One sleeve cannot compensate for the other.

## Neighborhood stop rules

After base activation, all four neighbors must complete causally and solvently. At least 70% must
be profitable, their median Sharpe must be at least `0.50`, and positive-PnL concentration must not
exceed `0.40`. With four declared neighbors, the profitability fraction requires at least three to
be profitable. Any stability failure ends Team 03 as DNF.

## Process boundary

Before any implementation or measurement, the child family must receive a new research brief,
feature lineage, family registration with its parent ID, frozen candidate config, causal synthetic
tests, no-control risk policy, and trial registration. The previous result supplies no reusable
performance artifact. Registration must precede the only base evaluation, and the old family must
remain untouched.
