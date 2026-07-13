# Team-03 QR brief: Residual Tail Asymmetry

**Intended candidate:** `t03-idtail-v1`; seed `20260713`; frozen intended tuple `(a=2, blend=.75, windows={84,168,336}, K=6, annualized volatility target=.30)`. **Hypothesis:** persistent idiosyncratic positive-tail concentration reflects lottery demand and predicts relative underperformance, while matched low/negative-tail contracts earn the opposite premium.

## Frozen signal

At each 8h boundary `t`, return `None` except Monday 00:00 UTC. A Monday mapping fills at that transaction open, which is hidden at decision time. Let `E_t` be current weekly PIT Top-40 executable membership. Index each 8h close by its close time `s`; use `r_i,s=log(C_i,s/C_i,s-8h)` only when both bars are exactly adjacent and closed (`s<=t`); never bridge gaps.

Use BTC returns as factor when BTCUSDT is in `E_t` with at least 252 of the last 336 returns. Otherwise use, at each `s`, the median return across `E_t`, requiring `max(5,ceil(|E_t|/2))` observations and 252 factor observations overall. For each symbol, on paired observations in `(t-112d,t]` (maximum 336; minimum 252), clip asset and factor separately to median +/- `6*max(1.4826*MAD,1e-6)`, then OLS-fit `r=alpha+beta*f`; invalidate factor variance below `1e-10`. Apply fitted coefficients to *unclipped* returns: `u=r-alpha-beta*f`. Set `m=median(u)`, `d=max(1.4826*MAD(u),1e-6)`, `z=clip((u-m)/d,-8,8)`.

For each baseline window `W in {84,168,336}` returns, require `ceil(.8W)` observations in its exact calendar span. With `a=2`, define `P=mean(max(z-a,0)^2)`, `N=mean(max(-z-a,0)^2)`, `A=(P-N)/(P+N+.05)`, and `F=(count(z>a)-count(z<-a))/(count(|z|>a)+2)`. Tail score is `L=-mean_W(.75*A+.25*F)` (high is long). Nuisances are fitted `beta`, 28d log return, and `log(d)`. Momentum requires all 84 exact-span adjacent returns in `(t-28d,t]`; one missing return invalidates that symbol.

Cross-sectionally map any vector to average-tie ranks in `[-1,1]` (constant maps to zero). Regress `rank(L)` on `[1,rank(beta),rank(momentum),rank(log(d))]` using ridge penalty `diag(0,1,1,1)`; final score is the rank of the residual. A failed solve or fewer than `2*(K+3)` valid alpha names returns `{}`.

## Portfolio and risk

BTC is excluded from alpha and is factor hedge. Under median-factor fallback, use the highest-beta valid symbol (symbol tie-break), requiring beta at least .5; otherwise flatten. That fallback hedge remains in the median-factor and cross-sectional nuisance fits but is excluded from both alpha sleeves. Baseline `K=6`: retain eligible sleeve incumbents inside rank `K+3`, then fill longs from highest and shorts from lowest score, deterministic symbol tie-break. Each sleeve starts at 0.42 gross, proportional to `1/d` clipped to `[.5M,2M]`, where `M` is the median `1/d` across every valid alpha-candidate name after hedge exclusion and before sleeve selection. Redistribute by deterministic water-filling with 0.08 symbol cap.

Let alpha factor exposure be `B=sum(w_i*beta_i)` and hedge beta `beta_h`; `beta_h=1` exactly when BTC is the hedge. Scale alpha by `c=min(1,.08*|beta_h|/|B|)` (`c=1` if `B=0`) and set hedge `h=-cB/beta_h`. Thus gross is at most .92, absolute net at most .08, and factor beta is zero algebraically. From the last 84 raw-return timestamps require 68 complete rows; winsorize each column at median +/-8 MAD, let `S` be sample covariance with `ddof=1`, use `Sigma=.5*S+.5*diag(S)`, and scale all weights by `min(1,.30/sqrt(1095*w'Sigma*w))`; invalid covariance flattens. Non-Monday `None` holds quantities. Membership exits, 0.10% participation, delists/adverse residual settlement, 5bp fee plus 2.5bp slippage, 2x costs, exposure controls, and actual funding (`-signed_notional*rate`, carried position first) remain evaluator-owned. Funding is not a predictor.

## Validation, search, and falsifier

Research label is next-open-to-open seven-day return, interval `[t,t+7d]`; it never enters runtime. Outer expanding folds are train through 2021-06-21 / validate 2021-07-12--2022-06-27; train through 2022-06-20 / validate 2022-07-11--2023-06-26; train through 2023-06-19 / validate 2023-07-10--2024-06-17. Purge every overlapping label and embargo 14 days after the last training label end. Inner folds use expanding minimum 52 Mondays, successive 26-Monday validations, identical purge/embargo, ending inside each outer train. All transforms refit at each decision.

Search at most 48 configurations: `a={1.75,2,2.25}`, tail blend `{.5,.75}`, windows `{{84,168},{84,168,336}}`, `K={6,8}`, volatility target `{.20,.30}`. Select highest median inner base-cost Sharpe, then worst-fold Sharpe, then lower turnover, then lexicographic parameters. Ablations count separately; total planned material configurations <=56, below 120. After IS-only selection freezes one candidate, exactly one organizer-gated public-OOS view is authorized for that candidate; it must be preregistered and ledger-accounted and cannot alter the frozen tuple.

Falsify before OOS if weekly cross-sectional residual-return IC is nonpositive in at least two outer folds or median IC <=0, aggregate outer base-cost Sharpe <=.25, or either sleeve's pre-cost factor-residual PnL is nonpositive. Report each common regime and sleeve: price, funding, costs, Sharpe, exposure, turnover, drawdown, fill ratio, and delist loss.

## Immutable QE acceptance

Only closed `close` prices, PIT membership, and calendar enter alpha; impact, flow/volume shocks, liquidity recovery, funding/crowding signals, highs/lows, and future rows are forbidden. Required tests: exact equations/minima/fallbacks; Monday explicit mapping and other-boundary `None`; next-open blindness; truncation, corrupt-future, append and deterministic invariance; both realized sleeves meet charter floors; target caps/beta identity; actual funding and both cost runs reconcile; no prefitted state or target table.
