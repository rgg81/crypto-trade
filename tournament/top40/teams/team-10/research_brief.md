# Team-10 QR organizer-advance — Perpetual Listing-Maturation Premium

**Status:** field exact candidate `T10-PLMP-270-540-C14` with `qr_accepted=false`. Final Phase-0 record `012727865acecad6ea0c3327745359820b8e45c6`; common freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`. Thirty-seven material configurations are consumed, 83 remain, and public-OOS views remain zero.

## Independent hypothesis

New USD-M perpetuals can have one-sided speculative price discovery before a natural hedge/arbitrage base matures. A launch premium should decay after Top-40 seasoning, so the portfolio is long mature contracts and short young contracts. The only alpha input is contract lifecycle age derived from the first transaction-bar `open_time` visible by the decision. It uses no price value, return, volume, trade count, VWAP, funding, wick/path statistic, flow/book/OI/liquidation field, network, tail, calendar, sector, or vendor data.

This is independent of team-10's terminated Print-Fragmentation and Transaction Cost-Basis mechanisms. Their exact primary IS Sharpes were `-0.2513` and `-1.5150` (`-0.5549` and `-2.8116` at 2x costs). Their 21 and five configurations remain charged; no result was rescued or sent to OOS.

## Frozen candidate

At decision time `t`, derive `f_i(t)=min(open_time)` from transaction bars present in past context and set age `a_i(t)=(t-f_i(t))/1 day`. No price or other bar value is read. An exact first open equal to snapshot start `2020-01-01T00:00:00Z` is left-censored and treated as mature; no other first open is censored. Missing first-open history makes a symbol ineligible. Runtime state is only the past-derived first-open map; there is no pretrained artifact, timestamp answer table, or randomness. Seed is `20260713`, trial namespace `2026071310`.

The anchor is `2020-02-03T00:00:00Z`. Rebalance only at 00:00 UTC when the nonnegative integer day distance from the anchor is divisible by 14. Those scheduled calls always return an explicit mapping (possibly `{}`); 08:00, 16:00, and every other boundary return `None` and hold quantities while central exits and risk controls remain live.

Intersect current point-in-time membership with contracts having a decision-time executable transaction open, whose price is hidden from the strategy. Young means not left-censored and `30 <= age <= 270` days; mature means left-censored or `age >= 540` days. Require at least five in each sleeve or return `{}`. Sort young `(age ASC, symbol ASC)` and short the five youngest at `-0.08`; sort mature `(age DESC, symbol ASC)` and long the five oldest at `+0.08`. The selected ten alone appear in the mapping: gross `0.80`, net zero, symbol weight `0.08`.

All alpha bars are available by `t`. The common evaluator fills at the transaction open at `t`—the next open after the held period—and charges 5 bp taker fee plus 2.5 bp slippage per executed side, with an independent 2x-cost replay. Fills are capped at 0.10% of prior-24h quote volume and unfilled gaps carry. Actual funding is applied as `funding_pnl=-signed_notional*funding_rate`, with boundary funding before rebalance. Weekly removals and disappearing contracts receive participation-capped, normal-cost exits; residual delist notional receives the common adverse full-notional settlement. Common limits remain gross `1.0`, absolute net `0.25`, symbol `0.10`, and capital 100,000 USDT.

## In-sample evidence and gates

Every read was predicate-limited to `<2024-07-01`; loaded maxima were bars/marks `2024-06-30T16:00:00Z`, funding `2024-06-30T20:00:00.004Z`, and membership `2024-06-24T00:00:00Z`. Of 115 scheduled decisions, 58 were active (`50.43%`), from 2021-07-05 through 2024-06-17. Mean available young/mature counts were 11.56/17.72.

The exact primary returned net Sharpe `0.3670`, annualized return `5.03%`, drawdown `30.89%`, and positive-quarter fraction `44.44%`; 2x-cost Sharpe was `0.3262`, return `4.28%`, and drawdown `31.59%`. Price PnL sum was `+0.2926` (long `-0.0658`, short `+0.3584`); actual funding was `+0.0216` (long `-0.0736`, short `+0.0952`), fees `0.0200`, and slippage `0.0100`. Mean long/short exposure was `18.26%/18.92%`, active on `50.43%/52.17%` of bars; buy/sell notional was `2.237m/2.279m` USDT. The preliminary gate passed: both sleeves were material, base and 2x Sharpe were positive, and only two of five calendar buckets were negative.

Important weaknesses remain. Requested unfilled notional was `9.733m` USDT, 21 risk-cap breaches occurred, and conservative delist settlement loss was `0.0740` return-sum units; terminal unresolved notional was zero. Bear/bull/chop/stress Sharpes were `0.642/0.037/1.373/-0.830`, so the edge failed in stress and was nearly absent in bull markets.

The predeclared `young_max={180,270,360}` by cadence `{7,14,28}` basin had six of nine positive cells at both cost levels; median base/2x Sharpe was `0.0936/0.0582`. Reverse-primary Sharpe was `-0.5798`; an all-age rank control was `-0.0471`. This supports direction and thresholding but was diagnostic only: no neighbor replaced the fixed primary.

Nested expanding validation kept the fixed cell, past-only lifecycle state, 14-day label purge, and 28-day embargo. Six half-year outer base Sharpes were `-0.433, 0.066, 1.804, 3.125, -0.195, -0.381`; 2x values were `-0.479, 0.005, 1.754, 3.095, -0.256, -0.433`. Only three folds were positive and median base/2x Sharpe was `-0.064/-0.125`, so the nested gate failed. Per the organizer's anti-veto instruction, field the unchanged fixed cell with `qr_accepted=false`; do not treat it as QR endorsement and do not open public OOS.
