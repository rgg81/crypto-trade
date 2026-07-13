# Funding Receiver Aftershock (`t04-fps-001`)

**Hypothesis.** An unusually large perpetual-funding payment is a discrete balance-sheet shock; when the first completed post-settlement 8h bar moves toward the receiver, payer deleveraging continues for one more 8h bar.

## Frozen handoff

At every UTC 8h decision `t`, use only `E_t=context.eligible_symbols`. For symbol `i`, let `tau` be its latest actual funding row with `funding_time < t`, `s=floor_hour(tau)` (the evaluator convention), and `b=ceil_8h_UTC(s)`, equality allowed. The event is usable iff `b+8h=t` and the transaction bar `[b,t]` exists. Thus an off-grid event waits for the first wholly subsequent bar; a newer unfinished event supersedes it. Any no-match/missing/minimum failure gives zero signal, never a stale value.

For funding rows in `[tau-180d,tau)` at the same settlement UTC hour, require 20 observations; fall back to all hours with 60, else invalidate. With `MAD(x)=median(|x-median(x)|)`:

`Z_i=clip((f_i-median(f_hist))/max(1.4826*MAD(f_hist),1e-5),-6,6)` and `F_i=Z_i-median_j(Z_j)` across at least eight valid matched names.

Let `x_i,u=log(close_i,u/open_i,u)`. Using bars in `[b-180d,b)`, subtract the same bar-open UTC-hour median (minimum 30; all-hour fallback minimum 90) to obtain `d_i,u`. Primary market is identically transformed `BTCUSDT`. Estimate `beta_i=clip(cov(d_i,d_m)/var(d_m),-3,3)` on the last 270 pre-`b` paired bars, minimum 120 and variance at least `1e-8`. If BTC is unavailable, use at each bar the median `d` of at least ten current-`E_t` names; require 120 pairs. Otherwise invalidate. Set `e_i=d_i,b-beta_i*d_m,b`. Its scale is `sigma_i=max(1.4826*MAD(e_i,u),5e-4)` over the last 90 pre-`b` paired residuals, minimum 60. Across at least eight valid names, `R_i=clip((e_i-median_j(e_j))/sigma_i,-6,6)`.

Activate iff `sign(F_i)=sign(f_i)`, `|F_i|>=1.5`, `|R_i|>=0.25`, and `F_i*R_i<0`. Direction is exactly `a_i=-sign(f_i)` (positive funding -> short; negative -> long); strength is `q_i=sqrt(|F_i R_i|)`. Alpha uses only past funding, closed transaction prices, and deterministic calendar transforms.

Form all opposite-direction pairs with `|beta_L-beta_S|<=0.25`. Greedily choose at most five disjoint pairs by descending `min(q_L,q_S)/(1+|beta_L-beta_S|)`, then ascending beta gap, then `(long_symbol,short_symbol)` lexicographically. Require two pairs; otherwise return `{}`. For `K>=2`, each long is `+w`, each short `-w`, where `w=min(0.08,0.40/K)`. Hence gross is at most 0.80, net zero, symbol exposure at most 0.08, and absolute matched-beta exposure at most 0.10. Emit an explicit mapping every `t`; it replaces or closes the prior one-bar position. Fill is hidden open `t`. Funding at `t` is charged to the carried position before rebalance; all later actual events, 7.5 bp/side base taker-plus-slippage, 15 bp/side stress cost, 0.10% prior-24h participation caps, membership exits, and delist residual loss are evaluator-owned. Future funding is never assumed.

Frozen tuple is `(180d,20/60,1.5,180d,30/90,90d beta/120,30d residual/60,0.25,0.25 beta-gap,5 pairs,0.08 cap)`, seed `20260713`; trial seed namespace is `2026071304`. Rolling state is rebuilt chronologically; no fitted artifact is shipped.

## Validation, falsifier, and acceptance

The price label is `log(open[t+8h]/open[t])`, interval `[t,t+8h]`; canonical selection uses portfolio returns net of actual funding/fills/costs. Outer IS validations are `[2022-01-01,07-01)`, `[2022-07-01,2023-01-01)`, and each following half-year through `[2024-01-01,07-01)`, with expanding history from `2020-02-03`. Within each outer history, inner expanding validation blocks are 270 bars after a minimum 1,095-bar train, stepping 270 bars. Purge any train label intersecting validation and exclude the final 24h before validation (three-bar embargo). All transforms refit inside each split.

The predeclared grid has 48 tuples: funding lookback `{90,180}d`, `|F|` `{1.0,1.5}`, `|R|` `{0,0.25,0.5}`, beta gap `{0.25,0.50}`, max pairs `{3,5}`; five ablations bring the hard maximum to 53 configurations, below 120. Selection is median inner-fold net Sharpe, then double-cost Sharpe, then lower turnover, then lexicographic tuple.

Reject the mechanism if concatenated outer-OOF net Sharpe is below 0.50, its double-cost Sharpe is nonpositive, fewer than three outer folds have positive net Sharpe, or reversed-direction/placebo funding has at least the candidate's base-cost net Sharpe in three folds. QE acceptance additionally requires byte-identical reruns; truncation, corrupt-future, and append invariance; exact sign/alignment unit tests; and, for each sleeve, at least 1% realized gross on 5% of bars, 0.5% mean gross, and 1,000 USDT executed buy/sell notional. Actual funding, fees, slippage, capped/unfilled orders, forced exits, and 2x-cost output must reconcile exactly.

An IS-only coverage audit (no forward label) found 175,642 matched PIT symbol-events and 1,643/4,830 decisions with at least two raw confirmations each way. No OOS row was read. Expected strength is stress/bear payer unwind; bull dips may reverse, chop may not clear costs, negative-funding longs may be sparse, and irregular funding or delists can force flat/adverse exits. These are disclosed failure modes, not regime filters.
