# slow-tsmom — team-01's nominated candidate

Lane: `slow-per-coin-time-series-momentum`. Roles: long and short.

## What it is, in one paragraph

At every 8h decision boundary, and for each coin the runner declares eligible, the strategy reads
that coin's own closed bars and nothing else. It measures the coin's trailing log return over two
horizons — `FORMATION_BARS` bars and twice that, which at the nominated value is fifteen and thirty
days — divides each by that coin's own realised volatility times the square root of the horizon to
get a trend t-statistic, shrinks the magnitude of each t-statistic by `TREND_THRESHOLD` and clips it
into `[-1, +1]`, and averages the two rungs. It then averages that conviction over the last
`HOLDING_BARS` boundaries, which is its holding horizon, and sizes the position at conviction
divided by the coin's own volatility. The book is normalised to unit gross and returned. There is
no comparison between coins anywhere in it.

## Why it should work

A perpetual future has no expiry and no overnight gap, and its marginal buyer is leveraged.
Unrealised profit on an open perpetual is collateral, so a move that persists mechanically expands
the buying power of the side that is winning while liquidating the other side *into* the move rather
than out of it. The 24/7 tape gives that loop no nightly close in which positioning can be squared.
The only force pulling a perpetual back toward spot is the funding rate, which settles a few basis
points every eight hours — enough to tax the crowd riding a trend, nowhere near enough to stop it.
The claim under test is that the own-price persistence this produces, measured over weeks, is worth
more than the 7.5 bps a side it costs to harvest on the twenty most liquid names in the market.

The research found that funding is not a rounding error in that story. This book pays roughly 12%
of unit gross a year in funding, essentially all of it on the long sleeve, on a book whose average
net exposure is about zero — because a trend follower is structurally on the crowded side: it is
long after the price has risen, which is when longs pay, and short after it has fallen, which is
when shorts pay. That is the price of admission to the mechanism, and it is inside every number
reported for this candidate.

## The three declared coordinates

| constant | value | what it is |
|---|---|---|
| `FORMATION_BARS` | 45 | the near ladder rung, 15 days; the far rung is twice it, 30 days |
| `HOLDING_BARS` | 15 | boundaries of conviction overlap, 5 days — the holding horizon |
| `TREND_THRESHOLD` | 0.35 | the shrinkage subtracted from the magnitude of each trend t-statistic |

Everything else is a frozen structural choice, not a tuned parameter: the volatility window is
`2 × FORMATION_BARS` and moves with it, the ladder rungs are `1 ×` and `2 × FORMATION_BARS` and move
with it, and `MINIMUM_VOLATILITY` is a data-quality guard at 1e-4 per bar (under 0.2% annualised),
below which a feed is stale rather than quiet and would otherwise be handed the whole book by the
`1/sigma` sizing.

## The holding horizon has no phase

The overlap is a mean over the last `HOLDING_BARS` boundaries' convictions, not a rebalance clock.
That is deliberate. A clocked cadence longer than one bar has a phase offset, and a result obtained
at one offset is a result about that offset rather than about that cadence. This construction
decides at every boundary and there is no phase to choose, so the phase axis is void by
construction rather than unswept.

## The declared risk policy

`team-01-voltarget`: a 10% annualised volatility target on a 30-day lookback, scale bounded in
`[0.10, 1.0]`, and nothing else — no drawdown brake, no position stop, no time stop, no turnover
limit, no side scaling.

It is one control and it is load-bearing. The common risk unit's own scalar needs 90 days of the
reference book's history before it can be computed and sits at 1.0 until then, so for the first
three months of the window the tournament's leveller is not levelling anything, and a book at full
unlevered gross is a 70%-volatility book. Trial #6 ran this exact signal with no declared policy and
returned a 0.57 net Sharpe with a 0.238 maximum drawdown; trial #7 added only this volatility
target and returned 1.23 and 0.127. Almost all of that is fold F1, which contains the warm-up:
its 2×-cost Sharpe went from 0.18 to 1.43.

A two-step drawdown brake was tested on top of it (trial #9) and **rejected**: it made every number
worse, including the drawdown it was meant to control (0.110 → 0.145). A brake that cuts exposure
into a drawdown and restores it on recovery is backwards for a trend book, because the recovery is
where the mechanism pays.

## What it is not

It is not a cross-sectional strategy: no coin's signal, weight or eligibility depends on any other
coin's data. It is not a breakout or channel rule, it does not use funding, basis, open interest,
taker flow or volume as an input, and it has no regime classifier. The only inputs are each coin's
own closes.

## Trials behind it

Journal sequences #5 (transparent baseline), #6 (this signal, no controls), #7 (an earlier
four-rung, nine-boundary version with this policy), #8 (this exact frozen state), #9 (drawdown-brake
ablation), #10 (the same construction at the months end of the lane), #11 (declared neighbourhood
sweep), #12 (falsification battery). `RESEARCH-CERTIFICATE.md` carries the full record including
what failed.
