# Pivot 1 research brief: Directional Auction Absorption

## Identity and status

- Proposed family: `team-02-directional-auction-absorption-v1`
- Short name: Directional Auction Absorption (`DAA`)
- Parent: `team-02-causal-crowding-residual-persistence-v1`
- Exact reference candidate: `team-02-daa-reference-001`
- Status: pre-data proposal for organizer collision review; not registered, implemented, or run.
- Canonical runtime seed: `20260801`; team search/test namespace: `2026080102`.

## Genuine pivot boundary

DAA is not a C3RP parameter variant. It uses no common-market median, rolling beta, residual return,
funding, persistence/reversal state, sigmoid, directional sleeve tilt, or conditional blend of
continuation and reversal. Its raw mechanism is per-symbol auction behavior: a fixed directional
trend-efficiency rank is combined with a fixed taker-flow/closing-location absorption rank.

Every deployable DAA candidate must retain both the price-path and auction-absorption components.
Trend-only, absorption-only, flow-only, close-location-only, and sign-flipped controls are
diagnostic and cannot become champion. Removing either core component requires another formal
mechanism pivot.

## Causal economic thesis

Aggressive taker flow is not equivalent to informed price pressure. During a directional auction,
counterparty liquidity can absorb aggressive orders: a bar that closes stronger than its taker-buy
share implies latent demand, while a bar that closes weaker implies latent supply. Across a
multi-bar window, this price-response/flow gap should distinguish durable directional auctions from
fragile moves.

DAA therefore favors contracts whose own price path is directionally efficient and whose recent
closing location confirms hidden liquidity in the same direction. Longs are efficient relative
leaders with positive absorption gaps; shorts are efficient relative laggards with negative gaps.
The mechanism is fixed continuation after absorption, not a regime-dependent choice between trend
and reversal.

The cross-sectional long/short structure is intended to harvest differences in auction quality
rather than a common market forecast. Equal side budgets, broad selection, equal name weights, and
a conservative symbol cap are structural portfolio choices; the no-control signal must demonstrate
positive bull, bear, and chop evidence before any drawdown overlay is considered.

## Information and decision clock

At an exact 8-hour UTC decision boundary `t`, set `c(t)=t-8h`. The extra completed-bar lag is
mandatory. Give each boundary index
`j=(t-1970-01-01T00:00:00Z)/8h`; the baseline rebalances iff `j mod 3=0`, which is daily at 00:00
UTC. Valid non-rebalance boundaries return `None` to hold. Off-grid or insufficient scheduled
states return `{}` and request flat.

Use only the organizer's current point-in-time `eligible_symbols`. For every feature bar require
`close_time<=c(t)` and the exact expected `open_time`; a missing newer bar is never replaced with an
older anchor. The strategy sees no execution open, mark price, funding, evaluator state, position,
fill, cost, or PnL. All target requests fill, if possible, only through the central next-open
execution contract.

## Raw fields

DAA uses only completed 8-hour Binance USD-M transaction-kline fields:

- `open_time`, `close_time` for alignment and availability;
- `open`, `high`, `low`, `close` for returns and closing location;
- `quote_volume` and `taker_buy_quote_volume` for normalized aggressive flow;
- organizer-supplied point-in-time eligibility.

All fields have event timestamp `close_time` and are available only when the bar closes. No volume
or price value is forward-filled, interpolated, or learned from the full period.

## Exact reference signal

All arithmetic is finite IEEE-754 binary64. Time reductions are ascending; cross-sectional
reductions and final tie order use ascending ASCII symbol. Accurate deterministic float64 sums use
`math.fsum` semantics. Natural log is used. Freeze `epsilon=1e-12` and absolute numeric/weight
tolerance `tau=1e-12`.

### 1. Directional price-path efficiency

For each exact 8-hour return slot ending no later than `c(t)`, calculate
`r[i,s]=log(close[i,s]/close[i,s-1])`. The baseline trend horizon is `L_trend=12` days, or
`W_trend=36` complete returns requiring 37 consecutive valid closes.

`E[i] = fsum(r[i]) / (fsum(abs(r[i])) + epsilon)`.

`E` lies in `[-1,1]`: positive efficient paths rise with little backtracking, negative efficient
paths fall, and choppy paths approach zero. Every expected return must exist; there is no partial
horizon or history-fraction relaxation.

### 2. Auction absorption gap

For each of the most recent `L_abs=3` exact bars:

- require finite positive OHLC, `low <= open,close <= high`, and
  `high-low > epsilon*max(1,abs(high),abs(low))`;
- require finite `quote_volume > epsilon` and
  `0 <= taker_buy_quote_volume <= quote_volume`;
- aggressive-flow imbalance is
  `flow = 2*taker_buy_quote_volume/quote_volume - 1`;
- closing location is
  `clv = clip((2*close-high-low)/(high-low),-1,1)`;
- bar absorption gap is `gap=(clv-flow)/2`.

Positive `gap` means price closed stronger than aggressive buy share alone implies (latent demand);
negative `gap` means price closed weaker (latent supply). `gap` is bounded in `[-1,1]`.

Smooth the exact last `L_abs` gaps with half-life `h_abs=2` bars. For age `a=0` on the newest bar
through `L_abs-1`, raw weight is `2^(-a/h_abs)`; normalize the weights with `fsum` and calculate
`G[i]=fsum(weight[a]*gap[i,a])`. All bars must be valid.

### 3. Cross-sectional auction score

Among all scoreable current constituents, independently average-rank `E` and `G`. For `N>=2`, an
exact numeric tie receives the average of its one-based ascending positions; map rank `r` to
`2*(r-1)/(N-1)-1`. Symbols do not break a numeric rank tie.

With baseline `w_trend=0.60`:

`S[i] = 0.60*rank(E[i]) + 0.40*rank(G[i])`.

No nonlinear state or regime label changes these weights. Sort once by `(S ascending, symbol ASCII
ascending)` for deterministic sleeve membership.

## Exact reference portfolio

Require at least `N=24` scoreable symbols. Interpret `q=0.25` as exact rational `1/4` and set
`K=max(6,floor(N/4))`; require `2K<=N`. The first `K` sorted symbols are shorts and the last `K`
are longs. Both sleeves are mandatory and disjoint.

Total requested gross is fixed at `0.80`, split into requested long and short budgets `B=0.40`
each. The per-symbol cap is `C=0.06`. For each sleeve set
`B_eff=min(0.40,K*C)`; unallocatable capacity remains cash. Give every selected name equal magnitude
`B_eff/K`. Assign the float residual `B_eff-fsum(weights)` within cap to names in ASCII order;
positive residual uses available headroom and negative residual subtracts no more than current
weight. Final magnitudes must lie in `[0,C]` and sum to `B_eff` within `tau`; otherwise the whole
scheduled request is flat. Apply positive signs to longs and negative signs to shorts. No
post-allocation gross renormalization, inverse-volatility weighting, or directional side tilt is
used.

Reference parameters are frozen in `reference_candidate.json`. Any change to field validation,
window sides, rank mapping, smoothing weights, score weights, set rounding, capacity behavior,
seed, or clock is material.

## Expected regime and sleeve roles

- **Bull:** efficient relative leaders with positive absorption gaps populate the long sleeve;
  long attribution is expected positive. The short sleeve targets weak auctions where aggressive
  buying fails to hold the close, not the broad market merely because it rose.
- **Bear:** efficient relative laggards with negative absorption gaps populate the short sleeve;
  short attribution is expected positive. Longs are confined to relatively resilient auctions
  with latent demand.
- **Chop:** raw price efficiency weakens, so the independent absorption rank differentiates
  temporary demand/supply imbalances. Equal side budgets make the combined cross-sectional book,
  rather than a directional forecast, responsible for positive return.
- **Stress:** large taker flow and closing-location disagreement can expose liquidity absorption or
  failure. Broad equal weights and a 6% name cap limit idiosyncratic dominance, but the no-control
  reference must empirically respect the tournament tail and worst-regime gates.
- **Long sleeve:** always selected from the top composite auction scores and held at positive equal
  magnitudes; it must be materially active and positive in bull.
- **Short sleeve:** always selected from the bottom composite auction scores and held at negative
  equal magnitudes; it must be materially active and positive in bear.

No regime label is an input, and no sleeve is disabled by a market-state switch.

## Causal diagnostic and falsifier

For diagnostics only, define the next scheduled 24-hour symbol return strictly after a decision;
it is never a strategy input. Within each chronological fold, partition the price-efficiency rank
into top and bottom terciles and the absorption rank into top and bottom terciles. Define:

- `U_long = mean(next_return | E_top,G_top) - mean(next_return | E_top,G_bottom)`;
- `U_short = mean(next_return | E_bottom,G_top) - mean(next_return | E_bottom,G_bottom)`;
- `U = (U_long+U_short)/2`.

The absorption thesis requires `U>0` in at least four of six folds and pooled `U>0`; the composite
score rank IC with next return must also be positive in at least four folds. These tests ask whether
auction absorption adds directional information inside both strong and weak price paths.

The exact no-control reference is a hard first gate. Stop DAA without parameter or risk rescue if it
is insolvent, artifact-incomplete, has nonpositive annualized return, net Sharpe `<=0`, doubled-cost
Sharpe `<=0`, fewer than four profitable folds, nonpositive bull/bear/chop return, a failed long-bull
or short-bear role, or failed `U`/IC sign tests. Mere drawdown improvement is not mechanism evidence.

If the reference passes this core gate, later candidates still must satisfy every frozen tournament
qualification threshold, including Sharpe `>=0.75`, Calmar `>=0.40`, maximum drawdown `<=0.30`,
doubled-cost Sharpe `>=0.35`, quarter, multiplicity, concentration, sleeve, regime, and neighborhood
requirements. No metric compensates for a failed gate.

## Chronological folds and selection

The six contiguous end-exclusive folds score the full visible-development interval exactly once:

1. `[2020-02-03, 2020-09-01)`
2. `[2020-09-01, 2021-04-01)`
3. `[2021-04-01, 2021-11-01)`
4. `[2021-11-01, 2022-06-01)`
5. `[2022-06-01, 2023-01-01)`
6. `[2023-01-01, 2023-07-01)`

Authorized `[2020-01-01,2020-02-03)` observations initialize feature windows but are not scored.
All transforms are rolling and past-only; there is no fitted scaler or supervised model. Any
outcome-based fold-local choice must end strictly before `fold_start-30d`. Embargoed raw bars may
initialize a frozen candidate, but their outcomes cannot select it. Fold 1 uses only fixed
preregistered definitions. Forward diagnostic labels do not overlap because decisions are daily;
purge any malformed overlap and preserve the 30-day selection embargo.

Only candidates clearing the reference gate are compared. Selection is lexicographic: all
non-compensatory gates, positive-fold count, worst-regime Sharpe, worst-fold Sharpe, doubled-cost
Sharpe, median-fold Sharpe, aggregate Sharpe, Calmar, lower drawdown, lower turnover, then bytewise
candidate ID. Every candidate and diagnostic counts before its result is read.

## Parameter ranges and neighborhood

The search is structured, never a Cartesian sweep of all values:

| Parameter | Reference | Allowed values |
| --- | ---: | --- |
| feature lag | 1 bar | 1 only |
| `L_trend` | 12 days | 8, 12, 16, 18 |
| `L_abs` | 3 bars | 2, 3, 6 |
| `h_abs` | 2 bars | 2 only |
| `w_trend` | 0.60 | 0.50, 0.60, 0.70 |
| selected fraction `q` | 1/4 | 1/5, 1/4, 3/10 |
| minimum names per side | 6 | 6 only |
| rebalance bars | 3 | 3, 6 |
| gross | 0.80 | 0.80 only |
| side budget | 0.40 | 0.40 only |
| symbol cap | 0.06 | 0.06 only |

The declared nine-cell neighborhood is the selected center plus eight one-coordinate neighbors:
previous/next allowed `L_trend`, previous/next `L_abs`, `w_trend +/-0.10`, and previous/next `q`.
Use the frozen ordered lists. If the center is at an endpoint, use the nearest and second-nearest
inward values so both neighbors remain byte-distinct; a center without two distinct alternatives
on every axis is ineligible. Never invent a post-result value. At least 7/9 must be profitable,
neighbor median Sharpe must be `>=0.50`, and positive PnL concentration must satisfy the tournament
limit.

## Trial allocation and risk plan

Two team configurations are already consumed, leaving 78 cumulative configurations before formal
pivot registration. Pivot 1 allocates at most 37:

- 1 exact no-control reference;
- 5 nondeployable causal diagnostics (trend-only, absorption-only, no-flow, no-close-location, and
  sign-flipped absorption negative control);
- 11 additional coarse cells, completing a 12-cell grid including the reference
  (`3` trend horizons x `2` absorption windows x `2` trend weights);
- 4 portfolio/schedule cells (`q` in `1/5,3/10` x rebalance in `3,6`), with gross/cap unchanged;
- 8 additional one-coordinate neighbors around the already-tested center;
- 8 risk/cost observations only after a no-control signal passes: none, volatility target,
  drawdown brake, and combined, each at base and doubled cost.

This leaves at least 41 configurations for an honest second pivot or unanticipated preregistered
audit needs. Stages stop immediately on their falsifier; unused allocations are not automatically
reassigned.

The reference risk policy is no-control: volatility target, drawdown brakes, position/time stops,
turnover limit, and side scaling are disabled; same-boundary reentry is false. Only after a complete
positive no-control core may two organizer controls be tested: a 20-day 35% annualized volatility
target with scale `[0.25,1]`, and drawdown scales `0.75` at 10%, `0.40` at 20%, and `0` at 27.5%.
Position/time stops and turnover limits remain outside DAA. Full none/individual/combined and
base/doubled-cost evidence is mandatory. A control cannot rescue nonpositive alpha, a failed regime,
or a failed sleeve role.

## Limitations

- Taker-buy share is an aggressor classification, not trader identity or intent.
- Closing location can reflect late-bar noise; the multi-bar fixed smoother is the causal defense,
  not an empirical guarantee.
- Equal weights ignore covariance and volatility differences by design; broad selection and the
  6% cap, not an optimized risk model, control concentration.
- Directional continuation can whipsaw in chop; the absorption component must demonstrate its
  incremental uplift rather than receiving credit from the thesis.
- No-control short positions retain unbounded price-loss risk and next-open/participation limits;
  solvency and drawdown remain empirical hard gates.
