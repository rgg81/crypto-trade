# desk-closed-share

## What this is

A cross-sectional long/short book on twenty crypto perpetuals whose only input is **when in the
week a coin trades** — never how much it returned, never its funding rate, never its volatility.

For each coin the strategy measures its **desk-closed share**: the fraction of its trading activity
(bar trade count) over the past `ACTIVITY_WINDOW_BARS` closed 8h bars that landed in the calendar
cells where professional desks are shut —

* the **00:00–08:00 UTC settlement session**, the thinnest window of the crypto day (27.4% of
  in-sample quote volume, against 39.4% for 08:00–16:00 and 33.2% for 16:00–24:00), and
* the **weekend** (Saturday and Sunday UTC), when institutional participation withdraws.

The book is **short** coins with a high desk-closed share and **long** coins with a low one,
dollar-neutral, rank-weighted, rebalanced once a week at a declared phase.

## Why this should work

The 8h decision grid is not an arbitrary sampling frequency — it is the funding settlement clock,
and it cuts the day at the boundaries the market's own accounting uses. Around that clock sit
participants who keep human schedules, and the schedule they keep says who they are.

A coin whose activity concentrates in the desk-closed cells is being priced predominantly by
leveraged retail perpetual flow: the hours when spot desks, market-making desks and CME are quiet
are the hours when the marginal buyer is a retail account with leverage on. A coin whose activity
concentrates in the weekday European and US sessions is being priced alongside spot and
institutional participation. The measure is therefore a **clientele characteristic** — it says who
is left holding the coin — and the claim is that the desk-closed clientele is the one that pays.

It is a slow characteristic rather than a fast signal, which is what makes it affordable: the book
turns over about 9× a year against a 25× limit and earns roughly 86 bp of gross edge per unit of
one-way turnover against a 40 bp floor.

## Why the claim is about the clock and was tested as one

Against a **shape-matched scrambled clock** — each day independently permuting its own three
settlement slots, each week independently nominating its own two "weekend" days, so cell sizes,
coin mix and volatility mix are all held exactly and only the alignment with the real clock is
destroyed — the true partition's rank IC is −0.0227 against a null centred at +0.0004 with
standard deviation 0.0051 (z = −4.5; 0 of 300 draws as extreme). The scrambled twin is a scored
ablation, not only an offline statistic.

## Parameters

| Constant | Value | What moves when it moves |
|---|---|---|
| `ACTIVITY_WINDOW_BARS` | 378 | the measurement window (378 bars = 126 days) |
| `REBALANCE_CADENCE_BARS` | 21 | bars between rebalances; 21 is exactly one week |
| `REBALANCE_PHASE_BARS` | 6 | the (weekday, settlement slot) the book is reset at, counted from Monday 00:00 UTC — phase 6 is Wednesday 00:00 |
| `WEIGHT_POWER` | 1.0 | the exponent on the centred cross-sectional rank; continuous, so every declared variation moves every weight |

Phase is a first-order axis in this lane rather than a robustness detail, and the whole 21-point
weekly phase surface is reported in the research certificate.

## Causality

Every quantity is read from bars that have already closed at the decision. The share is a ratio of
sums over past closed bars only; the transaction open the evaluator fills at is never visible to
this code, and no fitted artifact is staged — the rolling accumulators are built from the rows the
`DecisionContext` streams during the run.

## Risk policy

`team-11-flat`: every declarable primitive disabled, `volatility_target.enabled` false as charter
amendment A3 requires. Shape is expressed entirely in the weights.
