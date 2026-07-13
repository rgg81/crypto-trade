# HWDS — Hierarchical Weekday Differential Seasonality

**Candidate:** `T06-HWDS-001`; strategy seed `20260713`, trial seed `2026071306`. **Hypothesis:** recurring UTC-weekday participation cycles create contract-specific, beta-independent 24-hour return seasonality that survives partial pooling, costs, and weekly universe changes.

## Signal and clock

Use only PIT Top-40 members executable at decision (t). Let (c_{i,u}) be the close of the 8h transaction candle `[u-8h,u)`, available at (u). Define (r_{i,d}=\log(c_{i,d+1d}/c_{i,d})), event interval `[d,d+1d]`, available at (d+1d). At daily `00:00 UTC` (t), all inputs satisfy endpoint `<=t`; the unseen transaction open at (t) is the evaluator fill. At `08:00/16:00`, return `None` (hold).

Estimate βᵢ from paired (r_i,r_{BTC}) with start dates `[t-60d,t)`, minimum 45, and set (e_{i,d}=r_{i,d}-\beta_i r_{BTC,d}). For weekday (w(t)), take observations with (d\in[t-52w,t-1d]), `weekday(d)=w(t)`, minimum 26. Ordered oldest-to-newest, age (a=0) for newest, (q_a=2^{-a/13}):

`m_i=Σq e/Σq`; `n_eff=(Σq)^2/Σq^2`; `s_i^2=Σq(e-m_i)^2/(Σq-Σq^2/Σq)`; `v_i=s_i^2/n_eff`.

Across valid names, `mu=mean(m_i)`, `tau2=max(popvar(m_i)-mean(v_i),0)`, `lambda_i=tau2/(tau2+v_i)` (zero if denominator zero), and `p_i=mu+lambda_i(m_i-mu)`. A listing/history failure receives audit forecast `mu`, reliability zero, and is excluded from ranking. Flat if fewer than 10 valid names.

At (t), also compute over start dates `[t-20d,t)`: momentum `M=sum(r_i)`, daily sample volatility `sigma=sd(r_i)`, and `L=log(median(daily quote_volume))`; require 18 returns and 18 positive-volume completed dates. Cross-sectionally transform β, M, σ, L by `(x-median)/(1.4826*MAD)`, clipped to `[-5,5]`; if MAD is zero use population SD, and if that is zero use a zero column. Ridge-regress (p) on intercept plus those four columns, minimizing `sum(residual^2)+sum(slope^2)` with unpenalized intercept. The signal (z_i) is the residual.

## Portfolio and execution

Sort by `(z,symbol)`. With (N) valid names, `K=min(8,max(5,floor(.20*N)))`; short bottom K and long top K (top ties also alphabetical). Let `S=median(z_top)-median(z_bottom)`, dispersion haircut `h=clip((S-0.003)/0.003,0,1)`, volatility throttle `v= min(1,0.04/median(sigma))`, and gross `G=0.80*h*v`. Allocate exactly `G/2` per sleeve proportional to `1/max(sigma,0.01)`, iteratively cap each absolute weight at `0.09` and redistribute within that sleeve. Net is zero; `{}` is returned when `G=0`.

The central evaluator alone applies next-open transaction fills, 0.10% of prior-24h quote-volume participation, partial fills, 5bp fee plus 2.5bp slippage per executed side, and the independent 2x fee/slippage run. It applies each actual funding event as `-signed_position_notional*funding_rate` to the carried position, before a coincident rebalance; funding is not a feature or doubled. Targets never include nonmembers. Weekly removals and delists use capped exits; any residual receives the common adverse 100% settlement. Both sleeves must meet the charter exposure/notional floors in IS. Common bull/bear/chop/stress labels are reporting-only: expect low-beta behavior in bull/bear/chop and weaker stress results, partly reduced by `v`.

## Validation, budget, and falsifier

IS-only expanding prequential folds score `2021-01-08..2021-12-31`, `2022-01-08..2022-12-31`, `2023-01-08..2023-12-31`, and `2024-01-08..2024-06-30`. At each January boundary purge every training label whose `[d,d+1d]` overlaps the new year and embargo January 1–7; daily online refits may thereafter consume only labels whose endpoints have passed. No OOS row is read.

Frozen tuple: `(52w, half-life=13 weekday observations, min=26, beta=60/45, covariates=20/18, ridge=1, K-cap=8, gross-cap=.80, symbol-cap=.09, vol-floor=.01, throttle=.04, spread ramp=.003→.006)`. Any search is capped at 72 configurations: lookback `{26,52,78}` × half-life `{8,13,26}` × minimum `{13,26}` × K-cap `{6,8}` × gross `{.60,.80}`; five registered ablations make 77 total, below 120.

QE accepts only if two clean runs are byte-identical; truncation, corrupt-future, and append tests preserve every target through the cut; funding/cost reconciliation is within `1e-12`; caps and both-sleeve floors pass; pooled fold base- and 2x-cost Sharpe are each `>0`; at least three folds have positive net return; and pooled long and short price-plus-funding PnL are each positive. Otherwise the hypothesis is falsified, not retuned.
