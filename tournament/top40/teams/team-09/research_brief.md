# Funding-Price Elasticity Gap (FPEG)

Bindings: Phase-0 `012727865acecad6ea0c3327745359820b8e45c6`; common freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`.

## Hypothesis and mechanism

**Hypothesis:** within the point-in-time Top-40, a contract whose fast funding innovation is high relative to its contemporaneous volatility-scaled price displacement is levered-long crowded without matching price impact and subsequently unwinds; a low residual identifies crowded shorts and a rebound.

This is neither settlement-event response nor slow carry: it has no event-time window and removes each symbol's funding level. It computes no return-tail statistic.

At daily decision `t=00:00 UTC`, let `C_i(s)` be the close of the 8h transaction bar ending at `s`; `H=72h`. Require the exact ten-close grid `s=t-H,t-H+8h,...,t`; never bridge a gap. With nine adjacent log returns `r_i(s)`, define

`P_i(t)=log(C_i(t)/C_i(t-H))/max(sqrt(sum r_i(s)^2),1e-6)`.

Define `F_i(t)=sum funding_rate_i(tau)` for every actual Binance event with `t-H <= tau < t`; no 8h schedule is assumed. An empty event window is zero only after the symbol's first observed funding event; before that it is missing. Funding at `tau=t` is unavailable to the signal.

For the prior 60 daily decisions, recompute `P,F` using only then-available information. A price gap invalidates that pair; a post-first-event no-funding window remains zero. Require 48 valid pairs. Using prior pairs only,

`zX=clip((X-median(X_history))/max(1.4826*MAD(X_history), floor_X),-4,4)`, with `floor_F=1e-7` and `floor_P=0.10`.

The executable cross-section also requires current PIT eligibility and 80% of exact adjacent 8h returns over volatility window `V`; returns spanning gaps are discarded. Set `sigma_i=max(sample_SD(valid returns,ddof=1),1e-6)`. Require `n>=20`. For all pairs `i<j` with `|zP_j-zP_i|>1e-12`, calculate `(zF_j-zF_i)/(zP_j-zP_i)`. Require 20 slopes and five distinct `zP` values; otherwise request flat. The deterministic Theil-Sen slope is their median, `b_t`; intercept `a_t=median_i(zF_i-b_t*zP_i)`. Residual `e_i=zF_i-a_t-b_t*zP_i`; alpha is `-e_i`.

## State and portfolio

Unexplained funding dispersion is `D_t=1.4826*median_i(|e_i-median(e)|)`. Store valid daily `D` online. From the most recent `L`, use nearest-rank 33rd/67th percentiles (`sorted[ceil(p*m)-1]`). Until 60 exist, gross is `0.5*Gmax`; thereafter use `0.5*Gmax` if `D<Q33`, `0.75*Gmax` if `Q33<=D<Q67`, else `Gmax`. This past-only state does not replace scoring regimes.

Set `k=max(5,floor(q*n))`; require `2k<=n`. Sort `(e,symbol)` ascending: long first `k`, short last `k`; symbol breaks ties. Each sleeve receives `G/2`. Allocate proportional `1/sigma_i`, iteratively fixing weights above 8% and redistributing remaining gross pro rata. Targets are symmetric, net zero, gross at most 0.80. Nonselected and newly ineligible names get zero on rebalance.

At 00:00 return the complete target mapping; at 08:00 and 16:00 return `None` (hold quantities). If any cross-sectional minimum or allocation feasibility rule fails, return `{}`. Context includes only bars closed by `t` and funding strictly before `t`; targets fill at the unseen transaction open stamped `t`. Boundary funding is charged to the carried position before that fill.

The common evaluator applies actual `-signed_mark_notional*funding_rate`, 5 bp taker fee plus 2.5 bp slippage per executed side, 0.10% of prior-24h quote-volume participation, carried unfilled gaps, cap reductions, membership exits, and adverse residual delist settlement. Funding is unchanged and fees/slippage doubled in the independent cost stress.

## Forecast, validation, and budget

The research label is next-open 24h log return `Y_i(t)=log(O_i(t+24h)/O_i(t))`, information interval `[t,t+24h]`; opens are labels/fills, never features. Outer expanding IS validations are the six half-years from `[2021-07-01,2022-01-01)` through `[2024-01-01,2024-07-01)`. For each outer fold, select configuration on the last three contiguous 90-day inner validation blocks ending 72h before the outer start. At every boundary, remove training decisions whose label end is later than `validation_start-72h` (24h purge plus 72h embargo). Preprocessing, state, and selection restart within each fold; only genuine OOF predictions are aggregated.

Grid: `q in {0.25,0.30}`, `Gmax in {0.60,0.80}`, `V in {15,30,45} days`, `L in {90,180,270}`: 36 configurations. Select highest median inner net Sharpe subject to positive Sharpe in at least two blocks, positive aggregate double-cost Sharpe, and both realized sleeves meeting charter exposure/notional floors. Ties: higher double-cost Sharpe, lower turnover, then lexicographic `(q,Gmax,V,L)`. Apply the same rule to full IS after nested assessment. Six registered ablations plus at most 18 implementation/robustness variants give a hard ceiling of 60 material configurations, below 120. Strategy/bootstrap seed is `20260713`; trial namespace seed is `2026071309`; no stochastic estimator is used.

Acceptance requires aggregate outer-OOF net Sharpe >=0.75, positive Sharpe in at least four outer folds, double-cost Sharpe >0, both sleeves material, at least three positive common regimes and worst-regime Sharpe >-0.50. Price PnL less fees/slippage but excluding funding must be positive. Mean daily cross-sectional Spearman `corr(e,Y)` must be negative in at least four folds. Joint Sharpe must exceed both price-only (`alpha=b_t*zP`) and funding-only (`alpha=-zF`) versions by 0.10. Every failure and hostile fold/regime is negative evidence, not silently dropped.

Expected strength is high-dispersion squeeze/unwind transitions; low-dispersion chop should be weakest. Failure modes are funding-rule change, carry masquerading as price alpha, turnover, sparse listings, capped exits, and delists. No performance is claimed; public OOS was not accessed.
