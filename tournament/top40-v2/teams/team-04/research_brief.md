# Team 04 research brief: Uncrowded Trend Carry

## Identity and status

- Family: `team-04-uncrowded-trend-carry-v1` (`UTC`).
- Exact reference: `team-04-utc-reference-001`.
- Parent family: none; this is the initial mechanism.
- Runtime seed: `20260801`; Team 04 test/search namespace: `2026080104`.
- Status: specified and implemented; synthetic tests written; not registered or evaluated.

## Economic thesis

Information, collateral, and inventory adjust at different speeds across perpetual contracts.
Relative leaders and laggards should therefore continue over several weeks. Continuation is less
credible when holding the position pays unusually expensive funding: high positive funding makes
an apparent long leader crowded, while low or negative funding makes a short laggard crowded.

UTC combines two fixed per-symbol trend horizons and a realized-funding rank. Medium trend captures
slow diffusion; faster trend requires the ordering to remain current; funding favors uncrowded
inventory. The latest one or two days are excluded from the trend horizons to avoid treating a
single transient liquidity shock as durable information. A 30-day volatility measure is used only
to exclude the highest-volatility fifth, not as alpha or a fitted scaler.

## Causal decision clock

At an exact 8-hour boundary `t`, set price cutoff `c(t)=t-8h`. The newest feature bar opens at
`c(t)-8h` and closes no later than `c(t)`. Funding must satisfy `funding_time<t`. Rebalance iff the
integer 8-hour epoch index is divisible by nine, a fixed three-day schedule. Other valid boundaries
return `None` to hold. Off-grid, malformed, or insufficient scheduled states return `{}` to request
flat.

The strategy sees only current organizer eligibility, completed transaction closes, and realized
funding. It does not see the execution open, future funding, mark price as a feature, OHLC shape,
volume, order flow, a common-market factor, organizer regimes, positions, fills, costs, equity,
drawdown, or PnL. Nothing is filled, interpolated, or substituted.

## Exact reference feature

All values are finite binary64. Time reductions use `math.fsum` in ascending order; symbol ordering
is ASCII; `epsilon=tolerance=1e-12`.

Require 132 exact 8-hour log returns from 133 closes through `c(t)`:

- medium trend `M` is the sum of 126 returns (42 days) ending two days before `c(t)`;
- fast trend `F` is the sum of 42 returns (14 days) ending one day before `c(t)`; and
- realized volatility `V` is the population standard deviation of the latest 90 returns (30 days).

For funding use `[t-7d,t)`, require at least seven unique events, last-event age at most 16 hours,
and `abs(funding_rate)<=0.05`. Define realized daily funding intensity
`C=fsum(funding_rate)/7`. Dividing by days rather than event count preserves the direct cash-flow
effect of settlement frequency.

Require at least 30 current symbols with all features. Sort by `(V,ASCII symbol)` and retain exactly
the lowest `floor(4N/5)`; at least 24 must remain. Within this set, independently average-rank `M`,
`F`, and `C`, mapping one-based rank to `[-1,1]`. Numeric ties get the exact average rank. Freeze:

```text
S = 0.50 * rank(M) + 0.30 * rank(F) - 0.20 * rank(C)
```

No fold, date, market state, or outcome changes these weights.

## Exact reference portfolio

Sort by `(S,ASCII symbol)`. Set `K=max(6,floor(N/4))`; require disjoint top/bottom sleeves. Long
the top `K`, short the bottom `K`. The selected long sleeve must have higher mean `M` and lower mean
`C` than the short sleeve by more than `1e-12`, otherwise request flat.

Each side requests `0.30`; cap each symbol at `0.04`. Effective side budget is
`min(0.30,K*0.04)` and unallocatable capacity remains cash. Give equal magnitudes and reconcile only
the floating residual in ASCII order within cap. Requested gross is at most `0.60`, net is zero
within tolerance, and both sleeves are mandatory. There is no inverse-volatility weighting,
direction tilt, regime switch, or strategy-owned risk state.

## Expected regime and sleeve roles

- Bull: positive uncrowded leaders populate longs; long-bull attribution must be positive.
- Bear: negative crowded laggards populate shorts; short-bear attribution must be positive.
- Chop: trend components weaken or disagree, so funding de-crowding and equal side budgets must
  keep combined return positive without suppressing either sleeve.
- Stress: the volatility exclusion, broad sleeves, 0.60 gross, and 0.04 cap reduce concentration;
  stress return, tails, solvency, and drawdown remain empirical hard gates.
- Long sleeve: always the top composite ranks and materially active when the book is active.
- Short sleeve: always the bottom composite ranks and materially active when the book is active.

## Falsifier

Stop UTC before parameter, neighbor, or risk study if the exact no-control reference is insolvent or
incomplete; has nonpositive annualized return, net Sharpe, or doubled-cost Sharpe; fewer than four
profitable folds; nonpositive bull/bear/chop return; failed long-bull or short-bear attribution; or
nonpositive pooled and four-of-six-fold composite score IC against the next scheduled three-day
symbol return. Controls cannot rescue failed alpha, regimes, sleeves, folds, or causal score signs.

A positive reference is not qualification. A champion must clear every frozen gate: Sharpe 0.75,
Calmar 0.40, maximum drawdown 0.30, doubled-cost Sharpe 0.35, positive folds and quarters,
trial-adjusted probability, three regime Sharpes, worst-regime floor, sleeve activity, PnL
concentration, and neighborhood stability.

## Walk-forward and diagnostics

The reference has no learned parameter, scaler, selector, or fitted state. It is frozen before all
outcomes, so its predictions in each fold are generated by the same preregistered source hash using
only rolling past inputs. Six contiguous end-exclusive folds cover development:

1. `[2020-02-03,2020-09-01)`
2. `[2020-09-01,2021-04-01)`
3. `[2021-04-01,2021-11-01)`
4. `[2021-11-01,2022-06-01)`
5. `[2022-06-01,2023-01-01)`
6. `[2023-01-01,2023-07-01)`

Warmup before the first fold initializes windows but is not scored. The diagnostic forward label
begins at the next executable open and ends at the following scheduled three-day rebalance. Labels
do not overlap; any malformed overlap is purged. Any later outcome-selected parameter must be chosen
using expanding training data ending at least 30 calendar days before the scored fold, and its
source/config hash must be declared separately. Fold 1 always uses the fixed reference.

## Search, neighborhood, and budget

The family caps its total initial plan at 36 configurations from the cumulative 80:

- 1 exact no-control reference;
- 5 nondeployable diagnostics: medium-only, fast-only, funding-only, no-volatility-filter, and
  funding-sign-flip;
- 10 additional coarse cells chosen sequentially from the registered ranges, never a full grid;
- 4 portfolio/schedule cells for selection fraction and rebalance frequency;
- 8 one-coordinate neighbors around the chosen center; and
- 8 risk/cost observations after a core passes: none, volatility target, drawdown brake, and
  combined, each at base and doubled costs.

Unused observations are not automatically reallocated. The center plus eight neighbors are frozen
in `parameter_neighborhood.json`; at least 7/9 must be profitable and median Sharpe at least 0.50.
Selection is gates first, then positive folds, worst regime, worst fold, doubled-cost Sharpe,
median-fold Sharpe, aggregate Sharpe, Calmar, lower drawdown, lower turnover, and candidate ID.

## Risk-control ablations

The reference policy disables every control. Only after a solvent positive core may two organizer
controls be tested: a 30-day 25% annualized volatility target with scale `[0.25,1]`, and drawdown
scales 0.75 at 10%, 0.40 at 18%, and 0 at 25%. Evaluate none, each alone, and combined under base
and doubled costs. Position/time stops, turnover limits, side scaling, and same-boundary reentry
remain disabled.

