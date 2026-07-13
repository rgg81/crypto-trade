# Team-07 Negative Research Dossier

**Disposition:** PES and PEES are terminated. SRM-B failed its self-imposed 90% fill falsifier and is not QR-accepted, but that research threshold is not a charter DQ. At organizer direction, unchanged `T07-SRMB-118` is **organizer-advanced despite QR falsifier** as the mechanically valid QE/tournament submission nominee. All 120 material configurations are spent (73+47), public-OOS views are zero, and no further tuning is allowed.

## Negative history

PES predicted continuation after smooth seven-day displacement; its 72-point proxy grid had no survivor. The fixed point `(L=21,H=63,gamma=1,K=6,gross=.90)` had proxy Sharpe -1.917, MDD .960, and 1/6 positive half-years; exact evaluation became insolvent at `2022-05-13T00:00:00Z`. PEES (trial 73) reversed the sign at gross .60 and became insolvent at the same timestamp. No path-family rescue is permitted.

## SRM-B hypothesis and final tested specification

The replacement predicted slow continuation of each contract's BTC-adjusted relative performance after a fixed one-week skip; breadth could only reduce exposure. At Monday 00:00 UTC decision `t`, a bar opened at `u` is usable only when `u+8h<=t`. For each executable PIT member except BTC, require BTC and asset closes producing `W+S=210` exactly adjacent returns, with `W=189`, skip `S=21`, and formation `F=63`. On the oldest 189 returns before the skip, fit an intercept:

`beta=sum((x-xbar)(y-ybar))/sum((x-xbar)^2)`, `alpha=ybar-beta*xbar`, `e=y-alpha-beta*x`, and `s=sqrt(sum(e^2)/(W-2))`, where `x=r_BTC`, `y=r_i`. Require denominator `>1e-12` and `s>1e-8`. Score `z=sum(last F e)/(s*sqrt(F))`. This is a first-moment continuation score, not a path, tail, funding, flow, or lead-lag statistic.

Among the same scorable non-BTC members, breadth `B` is the fraction whose summed 21 skipped/recent returns is positive. The fixed gross multiplier is 1 when `.20<=B<=.80`, otherwise 0; breadth never selects, ranks, or reverses. Rank by `(z descending,symbol ascending)` for six longs and `(z ascending,symbol ascending)` for six disjoint shorts. With at least 12 names, weights are `+.05` and `-.05` (gross .60, net zero); otherwise return `{}`. Monday emits an explicit mapping (`{}` when braked); 08:00/16:00 and non-Monday boundaries return `None`. BTC is factor-only and never targeted. State is only the deterministic rolling history; OLS is refit from past rows at each Monday. Any gap, nonpositive/missing close, missing BTC row, or insufficient history makes that asset unscorable.

The evaluator charges actual funding `-signed_notional*rate` to carried positions before a same-boundary rebalance; signal code never uses funding. Orders fill at the next transaction open, pay 5bp taker fee plus 2.5bp slippage per side, and face the 0.10% prior-24h quote-volume cap. Unfilled gaps carry; central exposure reductions use remaining capacity and normal costs. Membership exits and last-bar delist exits are capped; an unfilled delist residual receives the common adverse full-notional settlement. Base and independent 2x fee/slippage runs use both sleeves.

## IS-only validation and falsifier

Trials 74-115 were seven `(W,F)` pairs `{(126,42),(126,63),(189,42),(189,63),(189,126),(252,63),(252,126)}` x RMS standardization on/off x `K in {4,6,8}`, with `S=21`, gross .60, breadth `[.20,.80]`, outside multiplier .50. Trials 116-120 fixed `(189,63,on,6)` and respectively tested gross .40, gross .80, outside multiplier 0, bounds `[.25,.75]`, and no brake. Seeds were strategy `20260713` and search `2026071307`.

Nested IS used six Monday-aligned half-year outer folds from 2021-07-05 through 2024-06-30. Each origin selected by median Sharpe across three prior 90-day inner blocks, with a seven-day overlap purge subsumed by a 14-day embargo; ties used median 2x-cost proxy Sharpe, lower turnover, then trial ID. The proxy included next-open returns and costs but not funding/participation; every chosen outer fold and the final selection used exact common evaluation from flat. Outer selections were `91,77,81,85,85,74`.

Exact nested OOF passed performance gates: Sharpe .798, 2x .621, MDD .132, 4/6 positive folds, fill .967, and regime Sharpes bear 3.039, bull -.160, chop .160, stress 2.228; both sleeves exceeded charter floors. Final inner selection was trial 118. Its full IS exact result was Sharpe .400, 2x .270, MDD .124, terminal equity 121,068 USDT, with charter-material long/short sleeves, but fill fraction was only .669. The fixed QR falsifier required at least .90 both nested and full IS, so SRM-B is not QR-validated. Tournament policy prevents a research/performance threshold from becoming a DQ; the organizer therefore advances the unchanged specification above. QE must implement it exactly with seeds `20260713`/`2026071307`, disclose the failed fill gate, and make no alternate selection, rescue, or OOS access.
