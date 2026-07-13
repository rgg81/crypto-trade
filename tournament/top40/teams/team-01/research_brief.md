# Team-01: Asymmetric Liquidity Replenishment

Candidate `t01-alr-002`; seed `20260713`. Hypothesis: among weekly PIT Top-40 Binance USD-M perpetuals, latent demand appears as idiosyncratic continuation after abnormal aggressive-buy flow and recovery after aggressive-sell flow; that cross-section should beat its latent-supply mirror after carry and costs.

## Candidate history and c002 delta

`t01-alr-001` is retained as falsified: an organizer IS-only audit found 26/26 sampled Mondays flat because its unscaled per-side `sum(omega*x^2)>.25` gate eliminated all features; zero OOS views occurred. C002 changes only flow scaling: remove the arbitrary `|q|>=.05` cutoff and divide each side's nonzero `x` by its own past weighted RMS before regression. All other signal, portfolio, validation, and risk choices remain fixed. A separate IS-only every-eight-weeks sample (23 Mondays, 2021-01-04 onward) produced 18 nonflat targets; no return/PnL was viewed.

## Exact signal

At Monday 00:00 UTC decision `t`, use only 8h transaction bars with `open_time+8h<=t`; the last bar closes at `t`, then the evaluator fills at the hidden transaction open timestamped `t` (next open). Other 8h calls return `None`; insufficient Monday data returns `{}`.

For adjacent bars, `r_i,k=log(C_i,k/C_i,k-1)`. From 126 strictly earlier paired returns (minimum 84), `beta_i,k=clip(Cov(r_i,r_BTC)/Var(r_BTC),-3,3)` (`ddof=1`, BTC variance `>1e-12`), and `e_i,k=r_i,k-beta_i,k*r_BTC,k`.

Using 63 preceding log quote volumes (minimum 42), let `v=clip((log QV-median)/max(1.4826*MAD,0.10),-4,4)` and `q=clip(2*taker_buy_quote_volume/QV-1,-1,1)`. Define `x=q*max(v-theta,0)`; exact zero is not an event. For event `k`, `y_H=sum(e_i,k+h,h=1..H)`, available only at `c_k+8H`; require that time `<=t`. Over the latest `W` bars weight events by `omega=2^(-(t-c_k)/(8h*W/2))`. Within each sign `s`, set `rms_s=sqrt(sum(omega*x^2)/sum(omega))` and `z=x/rms_s`; nonfinite or nonpositive sums/RMS invalidate that side. Then

`b_s=sum(omega*z*y)/[sum(omega*z^2)+0.10]`.

Each side needs six events and normalized unregularized denominator `sum(omega*z^2)>.25`. For deterministic centered rank `R(z)=2(rank-1)/(n-1)-1`, ties by symbol, set `a=.5[R(b_plus)-R(b_minus)]`.

Neutralize `a` against ranks of latest beta, 60-return idiosyncratic momentum ending 24h ago, 63-return volatility (minimum 42), and log median 63-bar QV: with `X=[1,controls]`, `u=a-X inverse(X'X+diag(0,1,1,1,1))X'a`. Let `F` sum actual funding rates in `[t-21d,t)` (strictly earlier than `t`; minimum 14 events spanning 14 days; never assume 8h funding). Final `s=R(u)-lambda_f*R(F)`. Missing/nonfinite data excludes the affected computation; no imputation. BTC is never an alpha target.

### Binding endpoint conventions

- Slope candidates are closes `c_k in [t-W*8h,t)`, not the latest `W` events; then require label end `<=t`. `b_plus` uses only `x>0`, `b_minus` only `x<0`; zero is ignored and never counted. RMS is fitted separately after this sign split from those same past events.
- Each historical `e_i,k` keeps its own beta from the 126 returns immediately preceding `k`, never today's beta. At `t`, `beta_ctl` is attached to the return closing at `t`. Momentum is the 60 returns closing `t-24h,t-32h,...,t-496h`, excluding `t,t-8h,t-16h`. Volatility is sample standard deviation (`ddof=1`) of the latest 63 returns including `t`. Liquidity QV uses the latest 63 bars including `t`; capacity includes closes `t,t-8h,t-16h`. Only an event's abnormal-volume baseline excludes that event.
- Tail risk uses each observation's historical rolling-beta residual. `q05/q95` use Hyndman-Fan type 7 (`method="linear"`); arithmetic tail means include values equal to the threshold.
- Funding requires at least 14 rows and `max(funding_time)-min(funding_time)>=14*24h` inside `[t-21d,t)`. Sum each once. A duplicate `(symbol,funding_time)` fails closed; never deduplicate.
- Exact 8h contiguity applies to each primitive return, beta, volume, control, tail, capacity, and event-label window, with BTC matched at identical closes. A gap invalidates only computations whose interval crosses it; valid events on either side may coexist in the calendar slope window. Irregular funding is exempt.
- Every `R` is ordinal ascending by exact `(value,symbol)`; equal values receive distinct symbol-ordered ranks, never averages. Exclude nonfinite values before ranking.

## Portfolio and realism

Require current `context.eligible_symbols`, three complete prior bars totaling at least 15m USDT QV, and 16 valid non-BTC names. Select top eight/bottom eight by `(s,symbol)`. From 126 `e` (minimum 84), long risk is `-mean(e<=q05)` and short risk `mean(e>=q95)`; floor each at `max(raw,.005,.5*sleeve_median)`. Inverse-risk water-fill each sleeve to 0.40 gross, cap 0.075/name. Targets are exactly 0.80 gross and zero net.

The central evaluator alone applies exact funding `-signed_notional*rate`, 5bp taker fee plus 2.5bp slippage/side, 0.10% prior-24h-QV participation, mark-based caps, and an independent 2x fee/slippage rerun (funding unchanged). Weekly removals target zero; between decisions central membership/delist exits still occur. Last-close exits remain capacity-capped and residual delists take the adverse full-notional settlement.

Same two-sided rule runs in bull, bear, chop, stress. Expect best balance in chop, long strength in bull, short strength in bear, weakest results in stress. Report regime and sleeve return/Sharpe/exposure, price/funding PnL, turnover, fills/unfilled, forced settlements, and verify both charter side-exposure/notional floors in IS and public OOS.

## Preregistered research

Frozen c002 values remain `H=6,W=189,theta=1,lambda_f=.25`. The 53 unused c001 grid alternatives are retired. C001 plus c002 and at most eight registered ablations total at most 10/120 material configurations. Seed for placebo only: `2026071301`. Exactly one public-OOS view is authorized, for `t01-alr-002`; no other candidate may request one.

Validation blocks (end-exclusive): `2021-01-04/07-05`, `2021-07-05/2022-01-03`, `2022-01-03/07-04`, `2022-07-04/2023-01-02`, `2023-01-02/07-03`, `2023-07-03/2024-01-01`, `2024-01-01/07-01`. Outer blocks 4–7 select only on preceding blocks; final selection uses all seven. Purge weekly labels `[t,t+7d)` and event labels overlapping validation; embargo seven days on both boundary sides. Maximize median-fold `min(base,2x Sharpe)-.25*IQR(base Sharpe)-.5*max(0,median DD-.30)`; ties within .02: lower turnover, then smaller `W,H`, larger `theta,lambda_f`.

Falsify before OOS if purged top-minus-bottom next-week residual spread is nonpositive overall or positive in fewer than four blocks, or unsigned-volume ablation retains >=90% of it. No regime rescue.

QE acceptance is immutable: equations/constants/cadence match; label ends and funding precede decisions; only PIT eligible names trade; valid targets meet counts/gross/net/cap; no prefitted state; truncation, corrupt-future, append, and deterministic-rerun targets are identical; tests prove next-open timing, funding sign/order, costs/2x, both sides, membership holds, participation, and delist settlement.
