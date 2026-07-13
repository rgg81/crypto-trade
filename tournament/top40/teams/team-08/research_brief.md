# Team-08 — Persistent Carry Dispersion Harvest

**Hypothesis.** Sticky leveraged demand makes actual USD-M funding disperse persistently; long-low/short-high carry earns the transfer after symmetric adverse-selection controls.

## Signal and clock

Let `E_x(t)={j:t-x days<=funding_time_j<t}`. Canonical `d_j=funding_interval_hours` is hours since that symbol's immediate prior actual Binance event, derived on the complete source sequence before membership, warm-up, or window filters; its predecessor may be outside `E_84`. Never substitute the first in-window row; absent/nonfinite `d_j` invalidates the symbol. With rate `f_j`, define `w_H=2^-((t-funding_time_j)/(24H))` and

`c_H(t)=24 sum(w_H f_j)/sum(w_H d_j)`, `H in {7,28}`, both over `E_84`.

On `E_28`, require >=42 events, `sum(d_j)>=504h`, oldest age >=21d, newest age <=24h, and every `0<d_j<=24h`; failure is missing. On exactly `E_28`, let `pi=sum(w_28 d_j sign(f_j))/sum(w_28 d_j)`. Score

`C*=1[c_7*c_28>0] sign(c_28) min(|c_7|,|c_28|) max(0,(|pi|-0.25)/0.75)`.

Let `C_i(u)` close bar `[u-8h,u]` and `r_i(u)=log(C_i(u)/C_i(u-8h))`; “last `L`” ends at `u=t` and starts `t-(L-1)8h`. Require finite positive closes and 168 contiguous returns. All `sd/Cov/Var` are sample (`ddof=1`); every used `sd>1e-12`. Beta uses all finite aligned pairs among 252 scheduled endpoints through `t`, requires >=189 and BTC `Var>1e-16`, and clips `Cov/Var` to `[-0.5,3]`. Veto if `|sum(last42 r)|/(sd(last168 r)*sqrt(42))>=2.5` or `sd(last21 r)/sd(last84 r)>=2.0`.

Scheduled decisions are `2020-02-03T00:00Z + 72h*k`; this rotating weekday anchor encodes no weekday effect. Other 8h calls return `None`. Funding exactly at `t` is unseen and is charged to the carried position before the next-open rebalance.

## State and portfolio

Rank valid PIT members by `C*` ascending (one-based; symbol tie-break). With `B=min(4,max(0,floor(N/2)-10))`, retain prior longs at rank <=`10+B` and shorts at rank >=`N-10-B+1`; fill disjointly to ten from rank tails. `N<20` requests `{}`; every `{}` clears state.

For sleeve `S`, `sigma_i=sd(last84 r)` and `a_i=(1/sigma_i)/sum_S(1/sigma)`. With cap `u=.1875`, form `p^-`/`p^+` by allocating `u`, then remainder, in beta ascending/descending order, both with symbol-ascending ties. `I_S=[p^- beta,p^+ beta]`; set `L=max(I_L.low,I_S.low)`, `U=min(I_L.high,I_S.high)`. If `L<=U`, `b0=(a_L beta_L+a_S beta_S)/2` and `b*=clip(b0,L,U)`.

Solve each sleeve's `min .5*sum((p-a)^2)` subject to `sum(p)=1`, `p beta=b*`, `0<=p<=u`. Use float64 SciPy SLSQP, lexical symbols, analytic Jacobians, `ftol=1e-12`, `maxiter=500`, and feasible start `(1-lambda)p^-+lambda*p^+`, `lambda=(b*-p^- beta)/(p^+ beta-p^- beta)`; zero width uses `p^-`. Require success, bound violation <=`1e-10`, equality residuals <=`1e-9`; never postprocess.

On failure, `M=min(15,floor(N/2))`. For each `k=11,...,M`, add one pair: next lowest-ranked name unused by either sleeve to long, then next highest unused to short. Never add asymmetrically. Recompute `a,I,b*` and QPs; first success wins. No pair or failure at `M` requests `{}`. Weights `+0.40p/-0.40p` give gross .80, net/beta zero, symbol <=7.5%.

On scheduled calls, duplicate/nonmonotone/malformed/gapped data excludes only that non-BTC symbol at `t`, without imputation; recompute `N`, with re-entry after a clean lookback. BTC failure invalidates all betas and requests `{}`. Symbol faults otherwise flatten only via `N<20` or construction failure.

## Evaluation contract and expectations

Mappings rebalance at hidden opens. Evaluation uses 5bp fee +2.5bp slippage per side, 0.10% prior-24h-volume participation, exact `funding_pnl=-signed_notional*actual_rate`, charter exits/delist settlement, and 2x costs. No schedule is forecast. Funding PnL should be positive, price PnL near zero. Chop is home; stress worst. Lagged-BTC regimes only report.

## IS-only validation, budget, and falsifier

Labels `[t,t+72h)` are actual funding sum for IC and next-open total return for portfolio validation. Use eight rolling outer folds (504d/126d/126d train/test/step), inner 252d/63d/63d. Purge overlapping labels plus 72h embargo; transforms/selection stay within folds.

The 40-config ceiling includes 12 consumed diagnostics (one interrupted IS evaluator; zero public-OOS views): 24 displacement/acceleration/persistence/buffer combinations, six ablations, ten stresses. Seeds `20260713`; namespace `2026071308`.

Strict-pre-2024-07-01 IS: 17,925 symbol-decisions/518 anchors; score versus future-72h funding had median rank IC .553, positive on 99.2% of 507 usable anchors, and 17.25bp median tail spread. `N>=20` on 91.2%, first 2020-05-09. Negative evidence: 7d-only IC was .611; `2.0/1.75` vetoes reduced carry and raised churn, favoring the slower mechanism/loose vetoes.

Advance only if pooled outer OOF net Sharpe >=0.75, 2x-cost Sharpe >0, at least six outer folds have positive net return and carry PnL, drawdown <=30%, and both sleeves meet the charter exposure/trade floors. **Falsifier:** reject if outer median carry IC is non-positive or reversed-sign carry does not underperform after identical costs/funding. Failure modes are rapid funding-sign flips, informed squeezes, sparse new listings, and stress-driven correlation/beta breaks.
