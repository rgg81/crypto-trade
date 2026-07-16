# Pivot 2 research brief: Funding Inventory Relaxation

## Identity and stop boundary

- Family: `team-02-funding-inventory-relaxation-v1` (`FIR`).
- Parent: `team-02-directional-auction-absorption-v1`.
- Exact reference: `team-02-fir-reference-001`.
- Runtime seed: `20260801`; test/search namespace: `2026080102`.
- Status: implemented, synthetic tests written, not registered or evaluated.

This is Team 02's second and final mechanism pivot. C3RP is stopped after one insolvent reference
and one deeply negative all-regime diagnostic. DAA is stopped because its exact reference was
insolvent and incomplete. FIR cannot revive either family: it contains no market residual, price
trend/reversal score, state switch, direction tilt, auction location, taker flow, or absorption.

C3RP treated funding as a small penalty attached to a price-return forecast. FIR instead treats
funding as the source of expected return: a known realized transfer paid by crowded long inventory
to shorts when the rate is positive and by shorts to longs when it is negative. Price history is
used only to exclude the highest-volatility fifth before funding ranks are formed.

## Causal clock and raw inputs

At an exact 8-hour decision `t`, funding rows must have `funding_time<t`. The price-risk cutoff is
`c(t)=t-8h`; its newest permitted transaction bar opens at `c(t)-8h` and closes no later than
`c(t)`. Decisions rebalance when the integer 8-hour epoch index is divisible by nine, giving a
fixed three-day schedule. Other valid boundaries return `None`; off-grid or insufficient scheduled
states return `{}`.

Only these inputs are used:

- `funding_time`, `symbol`, and `funding_rate` from realized funding settlements;
- `open_time`, `close_time`, and positive `close` from completed 8-hour transaction bars; and
- organizer-supplied current `eligible_symbols`.

No future/unsettled funding, mark price, execution open, OHLC shape, volume, taker flow, common
factor, regime label, position, fill, equity, cost, drawdown, PnL, private data, or fitted state is
available to the strategy. Missing events or bars are never filled or replaced.

## Exact reference feature

All reductions use finite binary64 and `math.fsum`; time sorts ascending and symbol ties use ASCII.
Freeze `epsilon=tolerance=1e-12`.

For each current symbol, take the end-exclusive 21-day funding window `[t-21d,t)`, split into prior
`[t-21d,t-3d)` and recent `[t-3d,t)`, and require at least 18 and 3 unique events respectively.
The last event must be no more than 16 hours old and every absolute rate at most `0.05`.

Let:

```text
L = fsum(all 21-day rates) / 21
P = fsum(prior rates) / 18
R = fsum(recent rates) / 3
D = R - P
```

`L` is realized funding per calendar day. `D>0` means funding is relaxing upward; `D<0` means it
is relaxing downward. Dividing by calendar days deliberately retains changes in settlement
frequency because the feature estimates realized cash-flow intensity rather than an event mean.

Independently require 90 exact 8-hour log returns from 91 closes through `c(t)`. Realized
volatility is the population standard deviation of those returns. Among symbols with both funding
and volatility features, require at least 30 and retain exactly the lowest-volatility
`floor(4N/5)`, ordered by `(volatility, ASCII symbol)`; at least 24 must remain. Volatility never
enters the score or name weights.

Within the retained set, average-rank `L` and `D`, map each rank to `[-1,1]`, and set:

```text
S = -0.75 * rank(L) + 0.25 * rank(D)
```

Thus a long candidate has low funding and funding moving upward toward normalization; a short has
high funding and funding moving downward. Numeric ties receive their exact average rank. Sort the
final score by `(S, ASCII symbol)`.

## Exact portfolio

For retained count `N`, set `K=max(6,floor(N/4))` and require `2K<=N`. Short the first `K` scores
and long the last `K`. Require mean short funding `L` to exceed mean long funding `L` by more than
`1e-12` per day, so the selected equal-budget book has a strictly positive ex-ante carry spread.

Each side requests `0.20`; each name is capped at `0.03`. Effective side budget is
`min(0.20,K*0.03)`, with unallocatable capacity left as cash. Names are equal-weighted and the
binary64 residual is reconciled in ASCII order within cap. Requested gross is at most `0.40`, net
is zero within tolerance, and both sleeves are mandatory. No post-allocation renormalization,
inverse-volatility sizing, directional tilt, or risk-state logic is used.

## Regime thesis and hard falsifier

- Bull: low/negative-funding longs participate in broad appreciation; high-volatility crowded
  squeezes are excluded. Long-bull attribution must be positive.
- Bear: high-positive-funding shorts receive carry and should benefit from inventory liquidation.
  Short-bear attribution must be positive.
- Chop: equal direction budgets leave the realized funding spread as the main expected return.
- Stress: 0.40 gross, 0.03 cap, broad sleeves, and the volatility exclusion limit—not eliminate—
  tail exposure. Stress, solvency, and drawdown remain empirical.

Stop FIR before any parameter or control study if the reference is incomplete/insolvent, has
nonpositive annual return, net Sharpe, doubled-cost Sharpe, or realized funding PnL, exceeds 30%
drawdown, has fewer than four profitable folds, has nonpositive bull/bear/chop return, or fails the
long-bull/short-bear roles. A positive point estimate is not qualification: any champion must also
clear Sharpe 0.75, Calmar 0.40, doubled-cost 0.35, quarter, multiplicity, concentration, sleeve,
regime, six-fold, and neighborhood gates.

## Search, neighborhood, and remaining budget

Three material configurations and one pivot are consumed. FIR is the final pivot and caps its plan
at 29 additional configurations:

- 1 exact reference;
- 4 nondeployable diagnostics: level-only, relaxation-only, no-volatility-filter, and exact
  relaxation-sign flip;
- 8 additional coarse candidates across preregistered funding window, recent window, level weight,
  volatility lookback, selection fraction, and rebalance schedule—sequential, never Cartesian;
- 8 one-coordinate neighbors around the selected center; and
- 8 risk/cost observations only after a no-control core passes: none, volatility target, drawdown
  brake, and combined, each at base and doubled costs.

The plan leaves 48 of the current 77 configurations unused rather than spending the final-pivot
budget automatically.

The center plus eight neighbors are frozen in `parameter_neighborhood.json`; at least 7/9 must be
profitable and neighbor median Sharpe at least 0.50. Selection is non-compensatory gates first,
then positive folds, worst regime, worst fold, doubled-cost Sharpe, median-fold Sharpe, aggregate
Sharpe, Calmar, lower drawdown, lower turnover, and bytewise candidate ID. Every observation counts
before its result is read and every stage stops on its falsifier.

## Risk plan

The reference policy disables every organizer risk control. Only after a positive solvent core may
a 30-day 25% volatility target with scale `[0.25,1]` and drawdown brakes at 10%/0.75,
20%/0.40, and 27.5%/0 be tested in the full none/individual/combined, base/doubled-cost matrix.
Position stops, time stops, turnover limits, side scaling, and same-boundary reentry remain disabled.
