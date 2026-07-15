# team-02 research brief

## Preregistration identity

- Family: `team-02-causal-crowding-residual-persistence-v1`
- Short name: Causal Crowding-Conditioned Residual Persistence (`C3RP`)
- Status: research formation only; no market window, evaluator, snapshot, or trial result has been
  accessed.
- Independent origin: mechanism derived from the permitted Top-40 V2 charter, configuration,
  methodology, playbook, Phase-0 policy, and neutral strategy/risk interfaces on 2026-07-15.
- Canonical runtime strategy seed: `20260801`, the frozen config value. This is the only seed that
  may be passed to the worker or used to generate production target weights.
- Team trial/search/tie-test namespace: `2026080102`. It may label team-scoped research records or
  deterministic tie-test cases, but it is never the worker seed or a production target seed.

## Falsifiable causal claim

Top-40 perpetual returns contain two conditional, economically distinct responses to capital
flows. When the common market path is directional and breadth is coherent, gradual information
diffusion and slow mandate/inventory adjustment make risk-adjusted idiosyncratic moves persist.
When the common path is inefficient and breadth is fragmented, forced liquidity demand and
temporary inventory imbalances make short-horizon idiosyncratic extremes revert. Realized
perpetual funding identifies the expensive/crowded side of either trade: low or negative funding
improves a long candidate, and high positive funding improves a short candidate.

The claim is not simply that a composite score earns money. Before portfolio construction, its
state interaction must have the predicted sign: residual-trend rank efficacy must be higher in
high-persistence observations than in low-persistence observations, while residual-reversal rank
efficacy must be higher in low-persistence observations than in high-persistence observations.
Funding tilt must also improve realized net carry in the predicted direction. Failure of that
interaction in at least four of six chronological folds falsifies the causal explanation. Failure
of the complete economic viability rule below rejects the family even if the interaction exists.

### Mechanism-identity guardrail

The causal persistence-versus-reversal state interaction is mandatory family identity. Every
deployable candidate in this family must retain both the residual-persistence and residual-reversal
legs and must let causal `P` vary their relative weight. Trend-only, reversal-only, and fixed-blend
arms are falsification diagnostics only; they are never eligible to become this family's champion.
Fixing `P`, collapsing to unconditional residual continuation, or removing the reversal
interaction constitutes a different mechanism and requires a formally registered pivot before any
such candidate is run. This collision-control guardrail is independent of performance.

## Information and execution clock

At an 8-hour decision boundary `t`, define the conservative feature cutoff `c(t) = t - 8h`.

- Transaction-bar fields are used only when `close_time <= c(t)`. Their event and availability
  timestamp is `close_time`; the extra 8-hour lag is deliberate.
- Funding rows are used only when `funding_time <= c(t)`, even though the neutral worker already
  guarantees that all supplied funding is strictly earlier than `t`.
- The organizer-supplied `eligible_symbols` at `t` is the only universe. It is the point-in-time
  weekly Top-40 set intersected with executable symbols; no current or future execution open is
  exposed to the strategy.
- Give every exact 8-hour UTC boundary an integer index
  `j = (t - 1970-01-01T00:00:00Z) / 8h`. Target weights are recomputed iff
  `j mod rebalance_bars == 0`; the baseline `rebalance_bars=3` is therefore daily at 00:00 UTC.
  The strategy returns `None` at other valid boundaries to hold. A scheduled decision with
  insufficient valid state, or a timestamp off the exact grid, returns `{}` and requests flat.
- Every order is a target request. The central evaluator alone performs next-open fills, funding,
  fee/slippage, participation, delisting, exposure, risk actions, and PnL accounting.

No mark price, future bar, predicted funding rate, full-period statistic, evaluator state, or
timestamp-to-target table is an input.

## Signal definition

All day counts below mean three completed 8-hour bars per day. At `c(t)`, compute log returns
`r[i,s]` for each currently eligible symbol with valid history. The common return `m[s]` is the
cross-sectional median of valid `r[i,s]` at each historical bar. Using the current point-in-time
constituent set to form its past median is causal because both the set and all included past bars
are known at `t`.

For each symbol, estimate a trailing beta using only the latest `L_beta` days:

`beta[i] = clip(Cov(r[i], m) / Var(m), -1, 3)`.

For a horizon `h`, define risk-adjusted residual displacement:

`z[i,h] = (sum_h(r[i]) - beta[i] * sum_h(m)) / (sigma[i] * sqrt(3h) + epsilon)`,

where `sigma[i]` is trailing per-bar volatility estimated over `L_vol` days. Cross-sectional ranks
use deterministic average ranks, mapped to `[-1, 1]`; symbol order resolves only membership ties
after equal numeric ranks. There is no fitted cross-time scaler or winsorizer.

The three score legs are:

- Residual persistence: `T[i] = rank(0.65*z[i,L_slow] + 0.35*z[i,L_fast])`.
- Residual reversal: `R[i] = rank(-z[i,L_rev])`.
- Funding carry: for rows in the trailing `L_funding` days, calculate
  `cumulative_funding[i] = fsum(funding_rate)`, then
  `F[i] = rank(-cumulative_funding[i])`. Thus low/negative cumulative realized funding raises a
  long rank and high positive cumulative realized funding lowers a rank, making it a better short.
  A symbol without enough funding observations receives neutral `F=0`, never a cross-sectional
  extreme.

### Pre-trial funding-interface correction

The neutral V2 worker supplies normalized realized funding rows with `funding_time`, `symbol`,
`funding_rate`, and `mark_price`; it does not supply interval metadata. Therefore the executable
funding statistic is the raw cumulative actual funding rate above, using only `funding_time`,
`symbol`, and `funding_rate`. The fixed wall-time window already makes observations comparable and
the event-rate sum represents the per-notional funding actually accrued across supplied events.
Dividing by `L_funding`, 24 hours, or any other fixed positive constant would not change the
cross-sectional rank, so no scaling is applied. `mark_price` is intentionally unused: it neither
enters validity nor rescales the signal, and the central evaluator remains solely responsible for
funding cashflows.

This clarification corrects a pre-trial interface mismatch inside the already-registered realized-
funding carry mechanism. It was made without data, performance, evaluator output, or a trial; it is
not a thesis change, new domain, or mechanism pivot.

The market persistence state is known at `c(t)`:

- `ER = abs(sum(m)) / (sum(abs(m)) + epsilon)` over `L_slow` days.
- `BR = abs(2 * fraction_i(sum_L_slow(r[i]) > 0) - 1)`.
- `P = sigmoid((ER-theta_ER)/width + (BR-theta_BR)/width)`.

`P` is common to all symbols and changes the behavioral mechanism smoothly rather than switching
on an evaluator regime label. The final alpha rank is:

`A[i] = rank((1-w_funding) * (P*T[i] + (1-P)*R[i]) + w_funding*F[i])`.

## Portfolio construction and sleeve roles

Select the highest `q` fraction of valid `A` ranks for the long sleeve and the lowest `q` fraction
for the short sleeve. The sets are disjoint. Within each sleeve, allocate proportional to inverse
trailing volatility, with volatility clipped at that boundary's 10th and 90th cross-sectional
percentiles. Normalize each sleeve separately.

Let
`Z_m = sum_L_slow(m)/(sd(m)*sqrt(3*L_slow)+epsilon)` and
`D = tanh(Z_m/k_direction)`. For total requested gross `G` and maximum side tilt `d`, budgets are:

- long gross `G_long = G/2 + d*D`;
- short gross `G_short = G/2 - d*D` (submitted as negative weights).

At the baseline `G=0.90` and `d=0.075`, pre-cap requested gross is 0.90, absolute requested net is
below 0.15, and each pre-cap sleeve budget is at least 0.375 even at an extreme state. A
deterministic iterative 0.095 per-symbol precap redistributes excess within a sleeve; if too few
selected names make the requested sleeve budget infeasible, the unallocatable amount remains cash
rather than violating the cap. The central evaluator's stricter limits remain authoritative.

## Frozen executable numerical conventions

These conventions remove implementation discretion. Changing any one after a result is observed is
a material parameter change; the mechanism-identity guardrail still governs every deployable arm.

### Arithmetic, epsilon, and moments

- All calculations use finite IEEE-754 binary64 values. Symbols are traversed in ascending ASCII
  symbol order and time rows in ascending `open_time`/event-time order. Scalar sums use an
  accurate deterministic float64 sum (`math.fsum` semantics). `log` is the natural logarithm.
- The single return-scale constant is `epsilon = 1e-12`. It is added only to the three explicitly
  shown denominators: residual `z` (`sigma_i*sqrt(W_h)+epsilon`), `ER`
  (`sum(abs(m))+epsilon`), and market-direction `Z_m`
  (`sigma_m*sqrt(W_slow)+epsilon`). It is not added to prices, returns, covariance, beta variance,
  ranks, quantiles, funding, or budget normalization.
- Beta uses paired valid observations, arithmetic means, and population moments:
  `Cov_0(x,m)=sum((x-mean(x))*(m-mean(m)))/n` and
  `Var_0(m)=sum((m-mean(m))^2)/n` (`ddof=0`). If `Var_0(m) <= epsilon`, beta is invalid rather
  than regularized. A valid beta is clipped exactly to `[-1, 3]`.
- Symbol volatility `sigma_i` is the population standard deviation (`ddof=0`) of valid 8-hour log
  returns in the fixed `L_vol` window. The same `sigma_i` is used in residual `z`, the cross-section
  quantiles, and inverse-volatility weights. `sigma_i <= epsilon` is invalid.
- Residual displacement uses complete horizon returns and
  `W_h=3*h`: `(fsum(r_i)-beta_i*fsum(m))/(sigma_i*sqrt(W_h)+epsilon)`. It does not estimate a
  second residual standard deviation.
- Market-direction volatility `sigma_m` is the population standard deviation (`ddof=0`) of the
  complete `W_slow` common-return window. `ER` uses no variance. Thus every beta, residual-z,
  volatility-weight, ER, and direction convention is explicitly population-based where a moment
  is present.

### Bar, return, and funding windows

- At scheduled `t`, `c=t-8h`. The anchor is the bar with `open_time=c-8h` and
  `close_time<=c`; a different or missing anchor is not silently replaced with an older row.
- For a `W=3*h` return window, expected return-end bars have `open_time` in the exact grid
  `{c-8h, c-16h, ..., c-W*8h}`. Each return is
  `log(close_later/close_prior)` and additionally requires the immediately preceding bar at an
  `open_time` exactly 8 hours earlier. Therefore the rightmost usable end bar is included, the
  price at the left boundary is denominator-only, and `W+1` consecutive price bars are needed for
  a complete horizon. Duplicates, non-grid gaps, non-finite closes, and closes `<=0` make the
  affected return slot invalid; there is no forward fill.
- A fixed beta or volatility estimation window always contains exactly its `W` expected slots.
  With `f_min` represented as the exact rational `4/5` or `9/10`, validity requires
  `n_valid >= ceil(f_min*W)`; beta counts paired `(r_i,m)` slots and volatility counts symbol-return
  slots. At least two observations are also required. The numerator is not rescaled for missing
  slots. Fast, slow, and reversal cumulative-displacement horizons require all of their expected
  slots, so their economic horizon never shortens.
- A common return exists at a slot only with at least 12 valid current-constituent returns. It is
  their exact median: the central ordered value for odd `n`, or the arithmetic mean of the two
  central values for even `n`. `ER`, `D`, and each cumulative common displacement require a complete
  common-return horizon. Breadth uses only symbols with a complete slow horizon, requires at least
  12, and counts a zero cumulative return as non-positive.
- A trailing funding window is left-open/right-closed:
  `c-L_funding*24h < funding_time <= c`. Rows are ordered by `(funding_time,symbol)`, must have a
  finite `funding_rate`, and are never filled or interpolated. The event key is
  `(symbol,funding_time)`. Any repeated key in the window invalidates that symbol's entire funding
  statistic for the decision, regardless of whether the repeated values agree, preventing silent
  double counting or an arbitrary first/last choice. A symbol needs at least two unique valid
  events for `cumulative_funding`; this already-frozen minimum prevents a single event from defining
  a multi-day carry rank. A non-finite in-window rate or duplicate key makes that symbol neutral.
  Funding ranks are computed only if at least four symbols have valid `cumulative_funding`; all
  other symbols receive `F=0`. If fewer than four are valid, every symbol receives `F=0` for that
  decision.

### Ranks, state transforms, and startup

- For `n>=2` finite values, numeric ties are exact-equality groups, assigned the average of their
  one-based ascending positions. Map average rank `r` to `2*(r-1)/(n-1)-1`. No tolerance or symbol
  key breaks a numeric rank tie. A one-element rank cross-section is invalid.
- The persistence input is
  `x=(ER-theta_ER)/width+(BR-theta_BR)/width`; freeze
  `sigmoid(x)=1/(1+exp(-clip(x,-40,40)))`. The clipping prevents overflow but leaves both trend and
  reversal weights strictly nonzero. Direction is
  `D=tanh(clip(Z_m/k_direction,-20,20))`.
- The funding rank applies the same average-rank map to `-cumulative_funding`; exact equal funding
  maps to the same value. Missing, invalid, duplicate, or insufficient funding is assigned neutral
  zero only after ranking valid symbols, never inserted into the rank distribution.
- A symbol is scoreable only when beta, `sigma_i`, every required complete displacement, trend,
  reversal, and composite alpha are finite. Funding may be neutral. No shorter startup window or
  padded history is allowed. A scheduled decision needs at least `N=12` scoreable symbols and a
  feasible allocation on both sides; otherwise the whole portfolio requests flat `{}` rather than
  running one-sided.

### Sleeve count, quantiles, and deterministic capped allocation

- `N` is the number of scoreable current constituents before sleeve selection. Interpret the three
  allowed `q` values as exact rationals: `0.20=1/5`, `0.25=1/4`, and `0.30=3/10`. Set
  `K=max(4,floor(q*N))` for each sleeve. If `2*K>N`, request flat. Sort once by
  `(A_i ascending, symbol ASCII ascending)`; the first `K` are shorts and the last `K` are longs,
  guaranteeing disjoint sets even when all alphas tie.
- Compute volatility quantiles from all `N` finite positive `sigma_i` values before selecting a
  sleeve. Freeze Hyndman-Fan type 7 linear interpolation: sort `s[0..N-1]`, let
  `u=(N-1)*p`, `j=floor(u)`, `g=u-j`, and
  `Q_p=(1-g)*s[j]+g*s[min(j+1,N-1)]`, for `p=0.10` and `0.90`. Each selected volatility becomes
  `v_i=min(max(sigma_i,Q_0.10),Q_0.90)` and raw allocation score is `a_i=1/v_i`.
- Freeze symbol cap `C=0.095` and absolute weight tolerance `tau_w=1e-12`. For requested side
  budget `B`, first set `B_eff=min(B,K*C)`; `B-B_eff` remains cash and no extra symbol is added.
  Initialize all selected symbols active, all weights zero, and remaining budget `b=B_eff`.
  Repeatedly sum active `a_i` in ASCII order, propose `u_i=b*a_i/sum(a)`, simultaneously set every
  symbol with `u_i>=C-tau_w` to `C`, subtract those caps from `b`, remove them, and repeat. When no
  symbol meets that condition, assign every active symbol its proposed `u_i` and stop. If a cap
  round leaves `b<=tau_w`, leave all still-active weights at zero and stop to reconcile. If it
  removes the final active symbol, also stop and reconcile; an empty active set is not itself a
  failure. A nonempty active set with `b>tau_w` and a non-finite or non-positive score sum makes the
  side infeasible.
- Before reconciliation, fail if a weight is outside `[-tau_w,C+tau_w]`; otherwise project only
  boundary roundoff with `w_i=min(C,max(0,w_i))`. Then let `delta=B_eff-fsum(w)`. If `delta>0`, add
  up to available
  headroom in descending-headroom then ASCII-symbol order; if `delta<0`, subtract in
  descending-weight then ASCII-symbol order, never subtracting more than the current weight. Stop
  when `abs(delta)<=tau_w`. If reconciliation is
  impossible, any final weight lies outside `[0,C]`, or the final magnitude sum differs from
  `B_eff` by more than `tau_w`, the whole scheduled target is `{}`. Otherwise apply positive signs
  to longs and negative signs to shorts and do not renormalize away deliberately unallocated cash.

Expected roles are preregistered as follows:

- Bull: high positive `D` increases long budget; high `P` emphasizes uncrowded residual winners.
  Long attribution should be positive. The still-material short sleeve hedges relative laggards
  and collects expensive funding where available.
- Bear: negative `D` increases short budget; high `P` emphasizes persistent residual losers, with
  high positive funding improving short carry. Short attribution should be positive. The long
  sleeve remains active in resilient/negative-funding contracts.
- Chop: `D` is near zero and `P` tends lower; residual reversal plus funding carry is expected to
  make the combined near-neutral portfolio positive.
- Stress: cross-sectional residualization and inverse-volatility weights limit common-beta
  concentration. The volatility target and drawdown brake are intended to suppress tail exposure.
  The prior expectation is approximately flat to modestly positive, not a claim of crisis alpha.

## Parameters and baseline

The search is structured and is not the Cartesian product of all ranges.

| Parameter | Baseline | Preregistered values/range |
| --- | ---: | --- |
| `L_beta_days` | 20 | 15, 20, 25 |
| `L_slow_days` | 20 | 15, 20, 25 |
| `L_fast_days` | 10 | 7, 10 |
| `L_rev_days` | 2 | 1, 2, 3 |
| `L_vol_days` | 20 | 15, 20, 25 |
| `L_funding_days` | 7 | 3, 7, 14 |
| slow/fast trend weights | 0.65/0.35 | 0.50/0.50 to 0.80/0.20 |
| `w_funding` | 0.20 | 0.10, 0.20, 0.30 |
| `theta_ER` | 0.30 | 0.20, 0.30, 0.40 |
| `theta_BR` | 0.30 | 0.20, 0.30, 0.40 |
| transition `width` | 0.15 | 0.10, 0.15 |
| selected fraction `q` | 0.25 | 0.20, 0.25, 0.30 |
| gross `G` | 0.90 | 0.80, 0.90, 1.00 |
| maximum side tilt `d` | 0.075 | 0.05, 0.075, 0.10 |
| direction scale `k_direction` | 1.5 | 1.0, 1.5, 2.0 |
| rebalance interval | 3 bars | 3 or 6 bars |
| minimum valid history fraction | 0.80 | 0.80 or 0.90 |

All fixed clipping constants, tie rules, epsilon handling, startup behavior, and missingness rules
are parameters for trial-accounting purposes if changed.

## Chronological training and selection

There is no supervised forward-return label and no global model fit. Rolling betas, volatility,
cross-sectional ranks, and persistence state are re-estimated at every scheduled decision using
only data through `c(t)`. Nevertheless, candidate selection is treated as learning and is strictly
chronological.

The six contiguous, end-exclusive outer validation folds cover the entire canonical visible
development window exactly once and are fixed before results:

1. `[2020-02-03, 2020-09-01)`
2. `[2020-09-01, 2021-04-01)`
3. `[2021-04-01, 2021-11-01)`
4. `[2021-11-01, 2022-06-01)`
5. `[2022-06-01, 2023-01-01)`
6. `[2023-01-01, 2023-07-01)`

Authorized history from `[2020-01-01, 2020-02-03)` initializes rolling feature state for fold 1 but
is not scored and supplies no visible-development selection outcome. Later folds replay all causal
past raw observations for rolling state. Every canonical visible-development date is nevertheless
scored in exactly one fold; neither warmup nor embargo removes a scored date.

A 30-calendar-day selection embargo applies before each fold: any outcome used for fold-local
manual or algorithmic parameter choice must be strictly earlier than `fold_start - 30d`. Raw
observations in that embargo may be replayed as past-only feature state once a candidate is frozen,
but their outcomes cannot choose that candidate. Fold 1 has no earlier visible-development outcome,
so it permits no fold-local performance selection and runs preregistered fixed candidate
definitions. Because there is no forward label, label-overlap purge is vacuous. Fold predictions,
model/parameter declarations, and return series must be independently hash-bound; slices of one
full-period fitted object are forbidden.

Every candidate is preregistered before execution. The stitched OOF series is the concatenation of
the six scored intervals, including transition costs. A champion is eligible only if it passes all
non-compensatory aggregate, doubled-cost, fold, quarter, multiplicity, concentration, regime,
sleeve, exposure, notional, and neighborhood gates. Among eligible candidates, selection is
lexicographic: positive-fold count, worst-fold net Sharpe, median-fold net Sharpe, doubled-cost
Sharpe, Calmar, lower maximum drawdown, lower turnover, then bytewise candidate ID. If no candidate
is eligible, there is no champion to advance.

## Falsifiers and stop rules

The family is rejected or pivoted without cosmetic rescue when either condition holds:

1. **Mechanism falsifier:** in fewer than four of six folds,
   `(IC_trend_highP - IC_trend_lowP) + (IC_reversal_lowP - IC_reversal_highP) > 0`, where IC is
   the Spearman rank correlation between the component score at a scheduled decision and the
   next scheduled-period residual return. The funding tilt must additionally reduce realized net
   funding paid relative to the otherwise identical `w_funding=0` arm in at least four folds.
2. **Economic falsifier:** fewer than four folds are profitable after base costs, required
   bull/bear/chop and sleeve-role signs fail, doubled-cost viability fails, or fewer than 70% of
   the declared local neighbors are profitable. Tournament gate failure is not offset by a strong
   aggregate point estimate.

No threshold is relaxed after seeing a result. An isolated optimum is rejected.

## Risk policy and causal ablations

Signal configuration is frozen before risk-control comparison. Three organizer-owned controls
address distinct failure modes:

- Volatility target: 20-day realized portfolio volatility, 35% annualized target, scale in
  `[0.25, 1.00]`; intended to attenuate volatility clustering without leverage.
- Drawdown brake: gross scales 0.70 at 10% drawdown, 0.35 at 20%, and 0.00 at 27.5%; intended to
  stop portfolio-level loss cascades.
- Turnover limit: maximum one-way turnover 0.25 per boundary; intended to reduce costly rank
  churn and participation pressure.

Position and time stops remain disabled because they confound the persistence/reversal holding
horizon. Side scales remain 1.0 and same-boundary reentry remains disabled. Funding is charged to
the carried position first; all triggered reductions execute only at the next open, pay normal
costs, and share participation capacity.

The complete `2^3` control factorial (none, each individual, all pairs, all three) is evaluated at
base and doubled costs. The combined policy is retained only if it improves maximum drawdown or
5% tail loss by at least 10% relative to no-control, does not reduce net Sharpe by more than 0.10,
and still clears every regime and sleeve gate. Otherwise the simplest gate-passing subset wins;
if no control addresses its stated failure mode, no-control remains frozen.

## Trial allocation

The initial family receives at most 52 of the cumulative 80 material configurations:

- 8 causal component configurations: baseline plus seven prespecified removals/sensitivities;
- 12 coarse horizon/state configurations (`3` horizon bundles x `2` reversal horizons x `2`
  persistence-threshold pairs);
- 8 carry/portfolio refinements (`2` funding weights x `2` selection fractions x `2` rebalance
  intervals);
- 8 additional one-coordinate local neighbors around the provisional center, yielding a
  nine-member neighborhood including the already-tested center;
- 16 risk observations: eight control subsets at base and doubled costs.

The remaining 28 configurations are unspent reserve for at most two documented pivots. They are
not permission to expand this family after an answer is seen. Failed, interrupted, manual,
feature, parameter, neighbor, and risk variants all consume budget and must be registered before
their result is read.

## Assumptions and limitations

- The public Binance USD-M snapshot and central eligibility/fill contracts are taken as frozen;
  no snapshot data were inspected during formation.
- Funding is realized carry/crowding evidence, not a forecast. Missing funding is neutral and may
  weaken the family for newly listed contracts.
- Residual beta estimated from 15--25 days is noisy; clipping and cross-sectional ranking bound
  but do not eliminate that estimation error.
- The persistence state is endogenous and causal but is not the organizer's BTC regime label.
  Regime success therefore remains an empirical gate, not guaranteed by construction.
- Daily target refresh may miss sub-day reversals. Faster refresh is outside the initial family
  unless separately registered as a material change.
- Risk controls can reduce exposure after losses but cannot guarantee a fill or a 30% drawdown
  ceiling in a gap or participation-constrained market.
