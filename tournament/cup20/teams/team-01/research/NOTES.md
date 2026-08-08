# Team-01 research notes

Scope of everything in `research/`: **no tournament metric is computed here.** These scripts apply
no fee, no slippage, no funding-inclusive cost model, no exposure cap, no common risk unit, no
declared risk policy, and none of the charter's floors. They compute signal statistics — rank
information coefficients, signal-weighted mean forward returns per unit of own risk, hit rates,
sign-flip rates, gross information ratios in risk units, and the annualised absolute change of the
strategy's own target weights. They exist to choose which questions are worth a trial. Every number
that gates anything, and every number quoted as a metric in `RESEARCH-CERTIFICATE.md`, comes from
`scripts/cup20_evaluate.py`.

The one place that line is deliberately crossed toward realism is that step 8 onward includes
**funding** in the gross diagnostics, because the charter's per-side floor is stated on
`price_pnl + funding_pnl` and because funding turned out to be the single largest term separating
the signal from a tradeable book. Fees, slippage, caps and the risk unit are still absent.

---

## Step 0 — the shape of the problem (`eda_00_universe.py`)

- IS window starts at the first weekly reconstitution that reaches 20 members; **4335** decision
  boundaries, **3.96 years**, 207 reconstitutions.
- The point-in-time universe is exactly 20 names at every reconstitution. Per boundary the eligible
  set (member *and* has an executable open) is 20 at the median and drops to 13 at worst.
- **62** distinct symbols are eligible at some point; **116** one-sided membership changes across
  the window, i.e. roughly 15 entries a year. 19 of the 62 have under 180 days of tenure.
- Only five names (BTC, ETH, LINK, BNB, ADA) are members for the whole window.

Consequence for design: with 20 names and a `0.20` per-symbol cap, a book that holds most of the
universe never binds the cap; a book that concentrates into fewer than five names is executed at
reduced gross. And any per-coin construction must tolerate a coin appearing with a short history.

## Step 1 — is there own-price persistence at all? (`eda_01_horizon.py`)

Volatility-standardised trend `z = log(P_t/P_{t-L}) / (sigma * sqrt(L))` against the coin's own
next-bar open-to-open return, over eligible cells only.

| L (bars) | days | Spearman IC | hit rate |
|---|---|---|---|
| 21 | 7 | −0.009 | 0.493 |
| 45 | 15 | −0.009 | 0.492 |
| 90 | 30 | +0.006 | 0.500 |
| 180 | 60 | +0.004 | 0.498 |
| 360 | 120 | +0.002 | 0.498 |

**The rank IC is zero and the hit rate is at or below one half at every horizon.** Taken alone that
reads as a dead mechanism. It is not: the same table's sign-only control shows a clearly positive
mean signed return at every horizon (e.g. at L=90, +15.1 / +6.4 / +0.3 / +7.4 bps per bar in folds
F1–F4). Momentum here pays by magnitude in the tail, not by frequency — the classic trend-follower
payoff signature — so rank correlation is the wrong statistic and the *mean* is the right one.
Recorded because it is the single most misleading number in this research and any reader who checks
only the IC will conclude the opposite of the truth.

## Step 2 — where the edge lives (`eda_02_edge.py`)

`E[ sign(z) * r_fwd / sigma ]`, in bps of own risk per 8h bar, pooled t-statistic, by fold.

| spec | mean | t | F1 | F2 | F3 | F4 |
|---|---:|---:|---:|---:|---:|---:|
| sign L=21 | 284 | 7.67 | 296 | 245 | 210 | 383 |
| sign L=45 | 201 | 5.44 | 95 | 345 | 66 | 286 |
| sign L=90 | 279 | 7.53 | 403 | 265 | 100 | 362 |
| sign L=180 | 179 | 4.76 | 487 | 97 | 26 | 168 |
| sign L=360 | 122 | 3.18 | 465 | −34 | −38 | 221 |
| ladder L=45 (15/45/90) | 242 | 7.94 | 277 | 255 | 94 | 348 |
| ladder L=90 (30/90/180) | 238 | 7.87 | 436 | 205 | 95 | 258 |

Three findings that shaped everything after:

1. **The slow end of the lane is the weak end.** Beyond ~45 days of formation the edge is negative
   in F2 and F3. "Weeks", not "months", is where own-price persistence pays in this window.
2. **Averaging horizons beats picking one** — the two ladders have the highest pooled
   t-statistics of anything tested and are positive in all four folds.
3. **The short sleeve is the fragile one.** Split by side, LONG is +484 bps (t=8.8) at L=21 and
   +504 (t=8.8) at L=90; SHORT is +94 (t=1.9) and +85 (t=1.8), and is *negative* at L=63, 135, 270
   and 360. The short sleeve is strongly negative in F1 at every horizon — shorting the 2020-21
   bull is punished — and only F2/F3 pay for it.

## Steps 3–5 — conviction shape, overlap, threshold (`eda_03`, `eda_04`, `eda_05`)

Gross information ratio of the unit-gross book (price only at this stage), with `dW` = annualised
sum of absolute target-weight changes at unit gross.

- A **hard sign** flips the whole position for an arbitrarily small change in the trend. At L=90,
  ladder, no overlap: IR 1.46 at `dW` 234. A **bounded conviction** (clip or tanh of `z`) gives IR
  1.42 at `dW` 169 — the same edge for 28% less churn, because the position passes through zero
  continuously.
- **Overlap systematically costs fold F3 and buys everything else.** For the L=90 ladder: F3 is
  +0.28 at h=1, −0.31 at h=9, −0.70 at h=90, while F1 improves from 2.68 to 2.44 and `dW` falls
  from 234 to 21.
- A **soft threshold** `max(|z| − thr, 0)` recovers part of F3 without the churn a hard deadband
  costs. At L=45 ladder h=6: F3 is −0.18 at thr=0, −0.06 at thr=0.35, −0.07 at thr=0.50.
- `tanh` and `clip` are indistinguishable (IR within 0.02 everywhere tested); `clip` is kept for
  being the simpler statement.
- A **skip period** (excluding the most recent k bars from the formation window, the equities
  12-1 convention) is uniformly harmful here: at L=90 ladder, F3 goes from +0.28 at skip=0 to
  −0.36 at skip=3 and −0.63 at skip=6. The most recent week is not contaminated by reversal at
  this frequency; it is the most informative part of the window. **Abandoned.**

## Step 6–7 — the formation surface is a spike, not a plateau (`eda_06`, `eda_07`)

On a fine grid at H=6, thr=0.35 (price only), the three-rung ladder reads:

| F | 30 | 36 | 40 | **45** | 50 | 54 | 60 | 72 | 90 | 110 |
|---|---|---|---|---|---|---|---|---|---|---|
| 3-rung | 0.91 | 1.13 | 1.32 | **1.44** | 1.32 | 1.21 | 1.07 | 1.07 | 1.22 | 0.99 |
| 4-rung | 0.89 | 1.03 | 1.24 | **1.36** | 1.30 | 1.26 | 1.14 | 1.08 | 1.24 | 1.06 |
| 5-rung | 1.23 | 1.20 | 1.26 | 1.24 | 1.08 | 1.09 | 1.08 | 1.08 | 1.07 | 0.92 |
| 1-rung | 0.76 | 0.91 | 0.86 | 0.99 | 0.83 | 0.87 | 0.91 | 1.07 | 1.45 | 0.95 |

Read honestly: **45 is a local maximum, and the level at 45 is partly luck.** The standard error of
an information ratio estimated over 3.96 years is about 0.50, so the 1.44-versus-1.21 gap between
F=45 and F=54 is not a fact about the world. What the table does establish is that averaging rungs
raises the *floor* of the surface — the 1-rung row is the worst row at almost every column — which
is the estimator-variance argument, and it is why the candidate uses a ladder at all. The 4-rung
ladder is chosen over the 3-rung because its surface is flatter on both sides of the anchor
(1.24/1.36/1.30/1.26 across F=40..54 versus 1.32/1.44/1.32/1.21), not because it scores higher.

## Step 8 — funding is the largest single term (`eda_08_sides.py`)

The book pays **≈ 1.15 bps of unit gross every 8h bar, ≈ 12.4% a year**, and it pays it almost
entirely on the long sleeve (−0.46 of cumulative unit-gross return over the window on longs,
+0.01 on shorts). Its average net exposure is −0.02, i.e. essentially zero, so this is not a
directional artifact: **a perpetual-futures trend follower is structurally on the crowded side of
funding.** It goes long after the price has risen, which is when the perpetual trades above spot
and longs pay; it goes short after the price has fallen, which is when shorts pay. The drag is
about 0.17 of information ratio and it is not avoidable without using funding as an input, which
is another team's lane.

After funding, both sleeves still clear zero at the chosen anchor: long +2.75, short +0.55 of
cumulative unit-gross return.

## Step 9 — the neighbourhood, declared before it was measured (`eda_09_neighbourhood.py`)

Rule fixed before any of these numbers were seen: vary each coordinate one at a time by **±20%** of
the nominee's value. Four times the charter's 5% materiality minimum, applied uniformly so it
cannot be tuned per coordinate.

4-rung ladder, nominee F=45 H=9 thr=0.35, gross of price and funding:

| point | F | H | thr | IR | F1 | F2 | F3 | F4 | dW |
|---|---|---|---|---|---|---|---|---|---|
| nominee | 45 | 9 | 0.35 | 1.19 | 1.98 | 0.98 | −0.01 | 1.77 | 89 |
| F− | 36 | 9 | 0.35 | 0.99 | 1.55 | 0.95 | −0.15 | 1.60 | 103 |
| F+ | 54 | 9 | 0.35 | 1.01 | 1.84 | 0.73 | −0.11 | 1.57 | 81 |
| H− | 45 | 7 | 0.35 | 1.20 | 1.99 | 1.06 | −0.13 | 1.83 | 101 |
| H+ | 45 | 11 | 0.35 | 1.11 | 1.94 | 0.90 | −0.10 | 1.66 | 81 |
| T− | 45 | 9 | 0.28 | 1.18 | 1.96 | 0.98 | −0.02 | 1.77 | 87 |
| T+ | 45 | 9 | 0.42 | 1.19 | 2.00 | 0.99 | −0.02 | 1.78 | 91 |
| **median** | | | | **1.18** | **1.96** | **0.98** | **−0.10** | **1.77** | **89** |

H=9 is preferred over H=6 (median IR 1.18 vs 1.19, indistinguishable) on churn: `dW` 89 versus 109
at unit gross, which is the difference between a comfortable and a marginal turnover floor. F=45
H=12 medians to 1.06 and F=54 H=9 to 1.01, so the anchor is not arbitrary within the family even
if its own level is optimistic.

## Step 10 — a better volatility estimator does not help (`eda_10_volest.py`)

Own volatility enters twice (standardising the trend, and sizing the position), so a lower-variance
estimator should pay twice. The Parkinson range estimator, which uses each bar's high and low
instead of discarding them, moves the neighbourhood median IR from **1.18 to 1.16** at F=45 H=9 and
leaves the fold profile unchanged; a 50/50 blend gives 1.17. **Rejected** — the specification is
insensitive to it, and the simpler close-to-close estimator is the one a reader can check.

---

## Post-nomination exploration (steps 11–14) — no trials spent

After `slow-tsmom` was frozen at 8 accepted trials the organiser asked for further improvement with
four trials remaining. Superseding costs two of them (a fresh sweep and a fresh battery are bound to
the source digest and do not transfer), leaving two for research — so the search below was run
entirely on the free team-side diagnostics, and **no trial was spent on any of it.**

### The target, and the three constraints that define it

Decomposing the charter's ranking score on the frozen nominee's own sweep medians shows where the
points are:

| G term | earned | available | what moves it |
|---|---:|---:|---|
| worst fold 2× | 4.74 | 30 | fold F3, currently −0.092 |
| max drawdown 2× | 10.67 | 20 | drawdown, currently 0.120 |
| positive quarters 2× | 3.14 | 8 | currently 11 of 17 |
| median fold 2× | 20.00 | 20 | maxed |
| Calmar 2× | 15.00 | 15 | maxed |
| trial-adjusted confidence | 3.36 (T=8) | 7 | falls as trials are spent |

**Almost the whole prize is fold F3**, and trial #7 already had it: the four-rung ladder at H=9
scored a worst fold of **+0.122** and would rank at **G = 61.05 at T=11** against the frozen
nominee's **55.55** at the same count. It failed one floor, turnover, at 27.80 against 25.

So a replacement has to satisfy three conditions at once, all fixed before the search ran:

1. **`dW ≤ 66`** — turnover. Fitted on trials #6/#7/#8 as `gross × (24 + 1.394·dW)`, which predicts
   28.1 against #7's actual 27.80 and 19.4 against #8's actual 19.52. The floor applies to the
   neighbourhood median, so 66 leaves room for the points either side.
2. **`IR ≥ 1.10`** — the confidence floor, and this is the one that is easy to miss. Confidence is
   `1 − T·(1−B)` on the *complete* trial count, so re-freezing at T=11 needs `B ≥ 0.99091` and at
   T=12 `B ≥ 0.99167`. Across six scored runs the bootstrap fraction maps to a net Sharpe of about
   1.19 at that level. **A slower, lower-Sharpe, better-behaved candidate is not the safe choice —
   it is the disqualified one.**
3. **`F3 ≥ −0.05`** — the prize, mapping to roughly +0.08 scored on the measured +0.13 offset.

### Step 13 — a no-trade band, and why it was abandoned

The idea was to attack the 40% of turnover that is not signal churn: emit a target only when the
book has moved more than a band in L1 since the last emission, and otherwise return `None`. Held on
the team-side panel with positions drifting properly, the four-rung H=9 signal at a 0.24 band gives
IR 1.24, F3 +0.08 and dW 78 at an emission rate of 0.24 — apparently exactly what was needed.

**It was abandoned on a reading of the evaluator, not on a number.** With a volatility target
declared, `boundary_risk_decision` puts `"volatility_target"` in `reasons` at every boundary the
scale is below 1 — which for this book is every boundary, since it realises 16.6% against a 10%
target. That makes `scale_reasons` non-empty, so `_reduction_only_policy_target` runs on *skipped*
boundaries too and fills against them. Two consequences, both bad: the fills the band was meant to
suppress do not go away, and the reduction-only rule trims a position only when it has drifted *up*
— it cuts winners and never adds to losers, which is precisely backwards for a trend follower. The
band would have bought less turnover than modelled and paid for it in the mechanism.

### Step 14 — the exhaustive search, and the exhaustion

Eighty specifications across ten ladder families — diluting the fast rung by adding slower rungs,
unequal rung weights from 1/8 to 1/4 on the fast rung, formation 45 and 54, holding 9 to 18 —
scored against all three thresholds simultaneously.

**Zero clear all three. 49 fail IR, 30 fail dW, 1 fails F3.**

The failure mode is not scattered, it is monotone: `dW` and `IR` move together along the speed axis,
and `F3` moves with `dW`. Every specification that gets F3 to −0.10 or better inside the turnover
budget has an information ratio between 0.87 and 1.03 — a scored Sharpe around 0.98 to 1.14, which
is under the bootstrap floor a re-freeze would have to clear. The single specification with both a
good F3 and IR ≥ 1.10 is the four-rung ladder at H=9, `dW` 89, which *is* trial #7.

The closest near-misses, all failing on IR alone: `5rung +3/2` F=54 H=15 (IR 1.02, F3 −0.05, dW 58);
`4rung 1/3,1,3/2,2` F=54 H=15 (IR 1.02, F3 −0.03, dW 59) and H=18 (IR 1.00, F3 −0.00, dW 54);
`fast-lite w=1/5 +3/2` F=54 H=15 (IR 1.04, F3 −0.02, dW 56). Every one of them would trade a
comfortably qualifying nomination for a coin flip on a **disqualifying** gate in exchange for
perhaps +2 G.

### One lever considered and rejected without a trial

Lengthening the declared volatility target's `lookback_days` from 30 is *not* the forbidden lever —
it does not shrink the book, since the realised-volatility fixed point `sqrt(target × v)` does not
depend on the lookback; it only makes the gross scale move more slowly, which is genuinely trading
less. But the arithmetic does not reach: the scale's contribution is about 25 of trial #7's 148
turnover units (the gap between #6 without a policy and #7 with one at identical `dW`), so even
tripling the lookback to 90 days leaves turnover near 24.9 against a floor of 25 that applies to the
median. And it would blunt the volatility target exactly where it earns its keep — the fast reaction
during the risk unit's 90-day warm-up, which is where trial #6 → #7 found almost all of its gain.

### Conclusion

The lane is exhausted at 8 trials. The nominee stands.
