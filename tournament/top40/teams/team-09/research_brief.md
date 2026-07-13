# Funding-Price Elasticity Gap (FPEG)

Bindings: Phase-0 `012727865acecad6ea0c3327745359820b8e45c6`; common freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`; strategy seed `20260713`; trial namespace `2026071309`.

## QR disposition

**No preregistered cell passes the final IS selector gate or the aggregate outer-OOF acceptance gate. QR therefore rejects FPEG.** Because performance is not a charter disqualification, the mechanically organizer-advanced cell is exactly `q=0.30`, `Gmax=0.60`, `V=45 days`, `L=180`, with `D_t` excluded from its own threshold history. This is a reproducible fallback for tournament completion, not QR acceptance and not evidence that the strategy is ready for capital. Public OOS was not accessed.

## Hypothesis and mechanism

**Hypothesis:** within the point-in-time Top-40, a contract whose fast funding innovation is high relative to its contemporaneous volatility-scaled price displacement is levered-long crowded without matching price impact and subsequently unwinds; a low residual identifies crowded shorts and a rebound.

This is neither settlement-event response nor slow carry: it has no event-time window and removes each symbol's funding level. It computes no return-tail statistic.

At daily decision `t=00:00 UTC`, let `C_i(s)` be the close of the 8h transaction bar ending at `s`; `H=72h`. Require the exact ten-close grid `s=t-H,t-H+8h,...,t`; never bridge a gap. With nine adjacent log returns `r_i(s)`, define

`P_i(t)=log(C_i(t)/C_i(t-H))/max(sqrt(sum r_i(s)^2),1e-6)`.

Define `F_i(t)=sum funding_rate_i(tau)` for every actual Binance event with `t-H <= tau < t`; no 8h schedule is assumed. An empty event window is zero only after the symbol's first observed funding event; before that it is missing. Funding at `tau=t` is unavailable to the signal.

For the prior 60 daily decisions, recompute `P,F` using only then-available information. A price gap invalidates that pair; a post-first-event no-funding window remains zero. Require 48 valid pairs. Using prior pairs only,

`zX=clip((X-median(X_history))/max(1.4826*MAD(X_history), floor_X),-4,4)`, with `floor_F=1e-7` and `floor_P=0.10`.

The executable cross-section also requires current PIT eligibility and 80% of exact adjacent 8h returns over volatility window `V`. Returns spanning gaps are discarded. Set `sigma_i=max(sample_SD(valid returns,ddof=1),1e-6)` and require `n>=20`. For all pairs `i<j` with `|zP_j-zP_i|>1e-12`, calculate `(zF_j-zF_i)/(zP_j-zP_i)`. Require 20 slopes and five distinct `zP` values; otherwise request flat. The deterministic Theil-Sen slope is their median, `b_t`; intercept `a_t=median_i(zF_i-b_t*zP_i)`. Residual `e_i=zF_i-a_t-b_t*zP_i`; alpha is `-e_i`.

## State and portfolio, including the resolved `D_t` order

Unexplained funding dispersion is `D_t=1.4826*median_i(|e_i-median(e)|)`. The conservative past-only semantics are binding:

1. At decision `t`, let `H_t` contain valid `D_s` values from completed prior daily decisions only, `s<t`.
2. If `len(H_t)<60`, use gross `0.5*Gmax`. Otherwise truncate to the most recent `L` values and compute nearest-rank `Q33=sorted(H_t)[ceil(.33*m)-1]` and `Q67=sorted(H_t)[ceil(.67*m)-1]`.
3. Compare current `D_t` with those prior-only thresholds: gross is `0.5*Gmax` below `Q33`, `0.75*Gmax` from `Q33` inclusive to `Q67` exclusive, and `Gmax` at or above `Q67`.
4. Only after gross has been chosen, append `D_t` to history. A valid `D_t` is appended even if a later allocation-feasibility gate requests flat. An invalid cross-sectional fit produces `{}` and appends nothing.

Thus `D_t` never participates in `Q33/Q67` used to size itself. QE must set `dispersion_history_includes_current=false`; including it is neither an alternative cell nor an allowed tuning dimension.

Set `k=max(5,floor(q*n))`; require `2k<=n`. Sort `(e,symbol)` ascending: long first `k`, short last `k`; symbol breaks ties. Each sleeve receives `G/2`. Allocate proportional to `1/sigma_i`, iteratively fixing weights above 8% and redistributing remaining gross pro rata. Targets are symmetric, net zero, gross at most `Gmax<=0.60` for the fallback. Nonselected and newly ineligible names get zero on rebalance.

At 00:00 return the complete target mapping; at 08:00 and 16:00 return `None` (hold quantities). If any cross-sectional minimum or allocation rule fails, return `{}`. Context includes only bars closed by `t` and funding strictly before `t`; targets fill at the unseen transaction open stamped `t`. Boundary funding is charged to the carried position before that fill.

The common evaluator applies actual `-signed_mark_notional*funding_rate`, 5 bp taker fee plus 2.5 bp slippage per executed side, 0.10% of prior-24h quote-volume participation, carried unfilled gaps, cap reductions, membership exits, and adverse residual delist settlement. Funding is unchanged and fees/slippage are doubled in the independent cost stress.

## Forecast, nested validation, and deterministic selection

The research label is next-open 24h log return `Y_i(t)=log(O_i(t+24h)/O_i(t))`, information interval `[t,t+24h]`; opens are labels/fills, never features. Outer expanding IS validations are the six half-years from `[2021-07-01,2022-01-01)` through `[2024-01-01,2024-07-01)`. For every outer start, the selector uses the last three contiguous 90-day validation blocks ending 72h before that start. The deployable selector applies the same construction at the IS cutoff: `[2023-10-02,2023-12-31)`, `[2023-12-31,2024-03-30)`, and `[2024-03-30,2024-06-28)`.

At every boundary, training decisions whose label end is later than `validation_start-72h` are removed (24h label purge plus 72h embargo). Fold state is rebuilt chronologically from information available before the fold; no fitted state crosses from a later fold. Only genuine outer-fold predictions are aggregated.

The frozen grid is `q in {0.25,0.30}`, `Gmax in {0.60,0.80}`, `V in {15,30,45} days`, `L in {90,180,270}`: exactly 36 cells. The selector ranks passing cells by highest median inner base-cost Sharpe subject to positive Sharpe in at least two blocks, positive aggregate inner 2x-cost Sharpe, and both realized sleeves meeting charter floors. Ties are higher 2x-cost Sharpe, lower turnover, then lexicographic `(q,Gmax,V,L)`. No cell passed at the final anchor. Per the organizer instruction, the same primary/tie ordering over the failed cells mechanically advanced `(0.30,0.60,45,180)`; the grid was not extended.

The 36-cell deterministic proxy used ideal daily next-open quantities, actual event funding, and 7.5 bp per executed notional (15 bp stressed) to screen. Its finalist block Sharpes were `0.489892, 0.603315, -0.217215` (median `0.489892`), with aggregate stressed Sharpe `-0.751807`; all sleeve materiality checks passed. The formula was then replayed through the actual team target class and the common execution engine. Exact fresh-capital block Sharpes were `0.627187, 0.747580, -0.297995` (median `0.627187`), while aggregate exact stressed Sharpe was `-0.678793`. It still fails the frozen gate.

## Actual IS and internal OOF evidence

The mechanical finalist's exact full-IS central-engine result over `[2020-02-03,2024-07-01)` is contextual evidence, not a selector pass:

| Metric | Base cost | 2x cost |
|---|---:|---:|
| Net Sharpe | 1.183327 | 0.271870 |
| Annualized return | 9.3704% | 1.8383% |
| Max drawdown | 12.4205% | 22.6603% |
| Calmar | 0.754429 | 0.081123 |
| Positive-quarter fraction | 0.666667 | 0.444444 |

Its deterministic base-cost Sharpe 95% circular-block interval is `[0.179562, 2.196410]`. Full-IS common-regime Sharpes are bear `-0.208148`, bull `1.078359`, chop `0.935267`, and stress `2.762752`.

The nested path had passing inner selectors only for the first two folds. In the last four folds zero cells passed, so those rows are explicitly organizer fallback diagnostics:

| Outer fold | Cell `(q,G,V,L)` | Disposition | Base Sharpe | 2x Sharpe | mean daily Spearman `corr(e,Y)` |
|---|---|---|---:|---:|---:|
| 2021-07-01 to 2022-01-01 | `.25,.60,15,90` | QR-selected | 2.230442 | 1.345283 | -0.055622 |
| 2022-01-01 to 2022-07-01 | `.25,.80,30,270` | QR-selected | -0.559244 | -1.489977 | -0.015696 |
| 2022-07-01 to 2023-01-01 | `.25,.80,30,90` | organizer fallback | -2.754749 | -3.981025 | 0.028869 |
| 2023-01-01 to 2023-07-01 | `.25,.80,15,180` | organizer fallback | 0.946595 | -0.370907 | -0.005551 |
| 2023-07-01 to 2024-01-01 | `.25,.60,15,180` | organizer fallback | 0.885913 | -0.363126 | -0.002937 |
| 2024-01-01 to 2024-07-01 | `.25,.60,45,90` | organizer fallback | -0.598092 | -1.544346 | -0.006469 |

Aggregate outer-OOF base Sharpe is `-0.032341` with 95% interval `[-1.140588,1.104513]`; 2x-cost Sharpe is `-1.094736`, max drawdown is `18.4679%` base and `33.1754%` stressed, and three of six folds are positive. Common-regime Sharpes are bear `-0.848624`, bull `0.515561`, chop `0.460278`, and stress `-0.913471`.

### Frozen acceptance gates

| Gate | Required | Actual | Result |
|---|---:|---:|---|
| Aggregate outer-OOF net Sharpe | `>=0.75` | `-0.032341` | fail |
| Positive outer folds | `>=4/6` | `3/6` | fail |
| Aggregate 2x-cost Sharpe | `>0` | `-1.094736` | fail |
| Both sleeves material | charter floors | both pass | pass |
| Positive common regimes | `>=3/4` | `2/4` | fail |
| Worst-regime Sharpe | `>-0.50` | `-0.913471` | fail |
| Price PnL less fees/slippage, funding excluded | `>0` | `-0.111019` component-sum return | fail |
| Negative mean `corr(e,Y)` | `>=4/6` folds | `5/6` | pass |
| Joint Sharpe minus price-only | `>=0.10` | `+2.774555` proxy | pass |
| Joint Sharpe minus funding-only | `>=0.10` | `+0.046468` proxy | fail |

The ablation comparison is explicitly proxy evidence on identical ideal daily settings. Equal weight and no demeaning both outperform the joint baseline, which is additional negative mechanism evidence. Exact ablation values and all 36 final-anchor cells are in `ablations.json`.

## Sleeve, turnover, cost, funding, and fill evidence

Full-IS realized mean long/short gross exposures are `20.7062%/20.7017%`; each exceeds 1% on `94.3478%` of 8h bars. Executed buy/sell notionals are `29.118m/29.191m USDT`. Internal OOF mean exposures are `26.8345%/26.8355%`, both above 1% on `100%` of bars, with `19.929m/19.948m USDT` buy/sell notional. Both sleeves are economically material.

Arithmetic evaluator component sums for full IS are price `+0.582616`, funding `+0.138893`, fees `-0.209850`, slippage `-0.104925`, and net `+0.406734`. Long/short price components are `+0.829549/-0.246933`; long/short funding components are `-0.028727/+0.167619`. Total turnover is `419.700x` equity, executed notional `58.309m USDT`, unfilled requested notional `53,292 USDT`, forced-exit turnover `0.8788x`, no risk-reduction turnover, and no conservative settlement loss.

Internal OOF component sums are price `+0.188959`, funding `+0.100953`, fees `-0.199985`, slippage `-0.099993`, and net `-0.010066`. Long/short price components are `-0.012141/+0.201100`; long/short funding components are `+0.042697/+0.058256`. Turnover is `399.971x`, executed notional `39.876m USDT`, and unfilled requested notional `111 USDT`. Funding helps, but cannot overcome turnover costs out of fold; this is the central failure mode.

## Configuration accounting, risks, and QE handoff

The research account is 36 grid cells plus six preregistered ablations = **42 material configurations**, below the 120 limit. Re-evaluation across folds and base/stressed execution does not create a new configuration. No implementation/robustness variant was promoted, no parameter outside the grid was tried, and public-OOS views remain **0**. Timed successful stages consumed `1180.80s` wall and `1189.12s` CPU (user plus system), about `0.3303 CPUh`; diagnostic preprocessing failures occurred before any cell was scored and are disclosed in `provenance.md`.

QE's only mechanically valid organizer-fallback handoff is:

- `q=0.30`, `gross_max=0.60`, `volatility_days=45`, `dispersion_lookback=180`;
- `dispersion_history_includes_current=false` with the update order specified above;
- daily 00:00 UTC explicit rebalance, 08:00/16:00 `None`, `{}` on a failed gate;
- fixed feature order `(P,F,sigma)`, 60-day prior-only robust histories, 48-pair minimum, all other constants/formulas in this brief;
- seed `20260713`, no stochastic estimator, no pre-fitted state or timestamp lookup;
- maximum research accounting remains 42 material configurations and zero public-OOS views.

Expected strength was high-dispersion squeeze/unwind transitions; measured OOF weakness is broad, especially bear/stress and stressed costs. Failure modes are funding-rule change, carry masquerading as price alpha, turnover, sparse listings, capped exits, and delists. The observed main failure is turnover/cost fragility plus insufficient incremental value over funding-only. This handoff must retain the label **organizer-advanced after QR rejection**.
