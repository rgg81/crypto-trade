# Team 06 research brief — balanced trend/reversal v1

Status: design-complete, unregistered, unevaluated. This document makes no performance claim.

## Mechanism and economic thesis

The initial family combines two distinct but fixed cross-sectional effects. Lagged 7-day and
30-day risk-adjusted returns capture gradual information diffusion and persistent relative trend;
a 2-day reversal term captures temporary liquidity pressure. A causal cross-sectional median
30-day return continuously changes the mix: reversal receives more weight when the market is
directionless, while trend receives more weight when the common market move is large. It also
permits only a small signed net tilt. The construction is otherwise balanced long/short.

The thesis is intentionally modest. In bull markets, stronger relative trends plus at most +4%
net exposure should make the long sleeve positive. In bear markets, weak relative trends plus at
most -4% net exposure should make the short sleeve positive. In chop, the near-neutral book and
short reversal component should provide the combined return. In stress, a low 48% requested gross,
low-volatility preference, central volatility scaling, and drawdown brakes should limit loss; no
claim is made that stress return must be positive.

## Causal decision rule

At 00:00 UTC each day, and only then:

1. Intersect bars with `context.eligible_symbols`; reject rows whose close timestamp is after the
   decision time. Exclude stale, nonpositive, nonfinite, or insufficient histories.
2. Compute fixed slow trend, fast trend, reversal, and trailing volatility from past closes.
3. Convert each feature to an average-tie cross-sectional rank in `[-1, 1]`. There is no fitted
   scaler, selector, coefficient, regime state, or forward label.
4. Publish every valid symbol's score through `preconstruction_snapshot` /
   `preconstruction_scores`. This is before top/bottom selection and sizing. An optional future
   organizer hook is identity-only and is rejected if it changes a key or value; no nonexistent
   shared hook is imported.
5. Long the highest-scoring quarter and short the lowest-scoring quarter, at least four names per
   side. Equal-weight each side. Requested gross is at most 0.48, requested absolute net at most
   0.04, and requested symbol exposure at most 0.07. Return `{}` if fewer than 12 histories are
   valid and `None` on non-rebalance boundaries.

The evaluator alone applies the request at a later transaction open and owns funding, costs,
capacity, membership/delisting exits, positions, risk state, and PnL.

## Expected regime and sleeve roles

| Cell | Preregistered role | Failure interpretation |
| --- | --- | --- |
| Bull | Positive combined return and Sharpe; positive long sleeve | Slow/fast trend and bounded long tilt do not capture broad upside |
| Bear | Positive combined return and Sharpe; positive short sleeve | Relative losers or bounded short tilt do not monetize downside |
| Chop | Positive combined return from reversal plus spread selection | Trading costs or false reversals dominate |
| Stress | Drawdown containment; Sharpe no worse than frozen floor | Risk controls react too late or cross-sectional crowding dominates |
| Long sleeve | Materially active; primary bull contributor | Low-risk/trend ranking selects weak upside names |
| Short sleeve | Materially active; primary bear contributor | Borrow-independent perpetual short signal fails after funding/costs |

## Six-fold chronological evidence plan

The visible interval is stitched once from six contiguous, nonoverlapping test slices:

| Fold | Training history available through | OOF test start | OOF test end |
| --- | --- | --- | --- |
| fold-1 | 2020-02-02 | 2020-02-03 | 2020-08-31 |
| fold-2 | 2020-08-31 | 2020-09-01 | 2021-03-31 |
| fold-3 | 2021-03-31 | 2021-04-01 | 2021-10-31 |
| fold-4 | 2021-10-31 | 2021-11-01 | 2022-05-31 |
| fold-5 | 2022-05-31 | 2022-06-01 | 2022-12-31 |
| fold-6 | 2022-12-31 | 2023-01-01 | 2023-06-30 |

The rule has no learned state, labels, or preprocessing. “Retraining” in each fold is therefore a
fresh clean instance bound to the frozen source/config, consuming only history then available.
There is no overlapping forward label to purge or embargo. Fold results may not change a later
fold, the base parameters, or the risk policy. The organizer must hash each fold declaration and
the final stitched return artifact before freeze.

## Hard, noncompensatory decision rule

The base receives a **base-core pass** only if every gate that does not require neighbors passes:

- net Sharpe >= 0.75, annualized return >= 0, Calmar >= 0.40, maximum drawdown <= 0.30;
- doubled-cost Sharpe >= 0.35, positive-quarter fraction >= 0.55, and trial-adjusted probability
  of positive performance >= 0.90;
- at least four of six folds have positive net return;
- bull, bear, and chop each have strictly positive net return; at least three regime Sharpes are
  positive; worst regime Sharpe >= -0.25;
- long/bull, short/bear, and combined/chop net returns are each strictly positive;
- both sleeves have exposure >= 0.01 when active, active-bar fraction >= 0.10, mean exposure >=
  0.01, and executed notional >= 1,000 USDT; and
- maximum positive-PnL concentration <= 0.40.

Nothing compensates for a failed item. The initial base is the only candidate. If base-core fails,
the four dormant neighbors are not registered or run. A mechanism review then records the failure
and either makes a documented budget-preserving pivot or ends DNF.

After base-core passes, all four already-declared one-axis neighbors are registered before any
neighbor result is read, then evaluated as a batch. The base qualifies on stability only if at
least three of four neighbors are profitable and their median Sharpe is >= 0.50. A better neighbor
does not replace the base. The fixed risk ablations then test mechanism and risk attribution; they
are not a policy-selection menu.

## Falsifier

Reject this family if any hard gate fails; if fewer than three neighbors are profitable; if the
neighbor median Sharpe is below 0.50; if profits rely on more than 40% concentration; if either
sleeve is immaterial; or if the combined frozen risk policy fails to reduce its stated volatility,
drawdown, or turnover failure mode without preserving the qualification gates. No least-bad
candidate advances.

## Fixed risk plan

The final policy is frozen before evidence: 18% annualized volatility target (30-day lookback,
scale 0.30–1.00), gross scales 0.75/0.45/0.25 at 10%/18%/25% drawdown, and maximum one-way turnover
0.18. Position and time stops are disabled because they would conflict with trend persistence and
add symbol-level path dependence. Same-boundary reentry remains false. Central execution must
charge carried funding, mark the book, evaluate controls, execute risk reductions next-open with
normal costs/capacity, gate the strategy request, execute the remainder, then enforce common
exposure/delisting controls.

## Research budget

The planned family uses at most nine material configurations: one base combined-policy candidate,
four conditional neighbors, and four conditional control ablations. Each policy/configuration is
evaluated at base and doubled costs centrally; cost views do not authorize parameter changes.
This is far below the cumulative limit of 80 and uses no pivot. Registration and consumed-resource
accounting remain organizer-owned.
