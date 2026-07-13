# Print-Fragmentation Attention Premium — QR no-go dossier

**Status:** the mechanism is terminated, not team-10. Final Phase-0 record `012727865acecad6ea0c3327745359820b8e45c6`, common freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`. Twenty-one configurations were consumed; public-OOS views: zero; 99 configurations and all three views remain for a separately originated hypothesis.

## Hypothesis and mechanism

**Hypothesis:** unusually many transaction prints per quote dollar proxy broad retail/algorithmic attention and order splitting, temporarily overpricing attention-rich USD-M perpetuals; therefore, among the point-in-time Top-40, long the lowest fragmentation shocks and short the highest for a 72-hour unwind.

This is direction-free transaction fragmentation, not signed taker flow, depth, replenishment, price impact, lead-lag, return-tail asymmetry, funding response/carry, wick rejection, calendar seasonality, or path persistence. The economic falsifier was an exact common-evaluator IS net Sharpe at or below zero, or a spread that came only from liquidity, raw count, or quote volume. The first condition fired.

## Frozen candidate specification

At each eligible 00:00 UTC decision `t`, aggregate the three transaction klines opened at `t-24h`, `t-16h`, and `t-8h`; all close by `t`. For symbol `i`, let `N_it=sum(trade_count)`, `Q_it=sum(quote_volume)`, and

`x_it = ln(N_it) - ln(Q_it)`.

A day is missing unless exactly three bars exist, `N_it >= 10`, and `Q_it >= 100,000 USDT`; no pseudocount is used. From the prior 120 valid daily observations, excluding `t`, require 60 and compute median `m_it` and MAD. Then

`f_it = clip((x_it-m_it)/max(1.4826*MAD_it,0.05),-5,5)`.

Remove nuisance exposure decision-locally. Available through `t`, compute `L_it=ln(median(Q,30d))` (20-day minimum), annualized close-return volatility `V_it=sqrt(365)*sd(r,30d)` (20-day minimum), and 90-day BTC beta `B_it=(E[r_i r_B]-E[r_i]E[r_B])/(E[r_B^2]-E[r_B]^2)` (60 paired days; nonpositive denominator is missing). For each nuisance, average-rank the valid cross-section, divide rank by `n`, subtract `0.5`, and divide by its population standard deviation. With `A=[1,z(L),z(V),z(B)]`, set `u=f-A(A^+f)`, using unweighted least squares and Moore-Penrose tolerance `1e-12`.

Only current PIT members with an executable decision-time open (its price remains hidden) enter. Require ten valid names. Sort `(u,symbol)` ascending: long the first five at `+0.08` each and short the last five at `-0.08` each; ties resolve lexicographically. Gross target is 0.80, net zero, symbol maximum 0.08. If fewer than ten names qualify, return `{}`. Emit that mapping at 00:00 when integer UTC days since `2020-02-03` are divisible by three. At all other 8h decisions return `None`, holding quantities; central membership/risk/delist exits remain active. State is rolling raw history only, with fixed feature order and seed `20260713` (trial namespace `2026071310`); there is no fitted artifact or randomness.

Pre-admission transaction history may warm a baseline, but a name is never targeted before membership. A new/returning listing remains excluded until all minima are met. Missing one symbol never imputes it or changes another symbol's history. Truncation, corrupt-future, and append invariance were required QE tests had the mechanism advanced.

## Execution, funding, and risk contract

The decision uses candles closed by `t` and fills at the transaction open at `t`, the next open after the final observed close. The common evaluator charges 5 bp VIP-0 taker fee plus 2.5 bp slippage per executed side (and an independent 2x-cost replay), caps each fill at 0.10% of prior-24h quote volume, carries unfilled gaps, and applies actual funding events as `-signed_notional*funding_rate`. Funding at a rebalance boundary is charged to the carried position before trading. Mark prices govern exposure only. Weekly removals and disappearing contracts receive participation-capped normal-cost exits; any delist residual gets the common adverse full-notional settlement. Common caps remain gross 1.0, absolute net 0.25, symbol 0.10, capital 100,000 USDT.

## IS feasibility and negative evidence

All reads were predicate-limited to `<2024-07-01`. PIT coverage after warm-up averaged about 32 valid names per day; only 18 PIT-member days had zero/near-zero activity, so data scarcity did not explain failure. A bounded 15-cell proxy screen (holding 1/2/3/5/7 days by 4/5/6 names per sleeve) favored 72h, but this was selection evidence, not validation. Daily primary, no-nuisance, quote-only, raw-count, and reversed-sign controls were also recorded.

The fixed 72h/5+5 candidate then failed the exact common evaluator over IS: net Sharpe `-0.2513`, annualized return `-8.18%`, maximum drawdown `61.74%`, positive quarters `27.78%`. Long price contribution was `+1.0556`, short price `-1.1819`, funding `+0.1692`, fees `-0.2074`, and slippage `-0.1037` (return-sum units). IS Sharpes by year were 2020 `1.295`, 2021 `0.447`, 2022 `-2.030`, 2023 `-0.084`, 2024H1 `-2.140`; common bull/bear/chop/stress buckets were all negative. At 2x costs Sharpe fell to `-0.5549`, annualized return to `-14.45%`, and drawdown rose to `69.91%`.

Both sleeves were real (mean long/short exposure `36.78%/36.59%`; each above 1% on `93.29%` of bars; buy/sell notional above 21.4m USDT). Unfilled requested notional was 237,218 USDT, no material delist haircut occurred, and 53 post-trade drift breaches invoked central risk handling. Thus fillability did not rescue or cause the core short-sleeve loss.

## Validation gate and disposition

Had exact feasibility passed, selection would have used six chronological 6-month outer IS folds from 2021H2 through 2024H1, expanding inner folds, 72h label purging, six-day embargo, fold-local transforms, and a requirement of positive median outer Sharpe with at least four positive folds, both sleeves meeting exposure floors, and positive 2x-cost Sharpe. DSR/PBO and block-bootstrap intervals would be diagnostics, not vetoes. That nested stage and every OOS access were correctly skipped after the preliminary hard gate failed.

Expected failure mode was that small-print intensity reflects informed diffusion rather than temporary overpricing and that 72h re-ranking cannot amortize taker costs. The observed short-sleeve and 2022/2024 losses match it. **Do not implement, submit, or tune this mechanism; originate a distinct replacement under the remaining budget.**
